"""API-based baseline eval — adds frontier-model comparisons without disk constraint.

Tests OpenAI GPT-5, Anthropic Claude Opus 4.6, and (optionally) Naver HyperCLOVA X
on the same KoBBQ + KMMLU subset as our local models. Pure API inference;
no GPU, no disk. Runs on local Mac.

Why: paper Table 1 becomes much stronger with frontier-model points. Lets us
position our QLoRA result against "what could we have done with the best LLMs?"
without expensive training.

Cost estimate (60 prompts × 80 KoBBQ + 40 KMMLU = ~120 calls per model):
  GPT-5: ~$1-2 (mostly input tokens are short)
  Claude Opus 4.6: ~$2-3 (more expensive per token)
  HyperCLOVA X HCX-005: ~$0.50 (if key provisioned)

Auth: reads from local .env. Required keys (each optional):
  OPENAI_API_KEY
  ANTHROPIC_API_KEY
  NAVER_CLOUD_API_KEY + NAVER_CLOUD_APIGW_KEY
"""
import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _normalize_choices(raw):
    if isinstance(raw, list):
        return [str(c).strip() for c in raw]
    if not isinstance(raw, str):
        return []
    s = raw.strip().strip("[]").strip()
    import json as _json
    try:
        parsed = _json.loads("[" + s.replace("'", '"') + "]")
        if isinstance(parsed, list):
            return [str(c).strip() for c in parsed]
    except Exception:
        pass
    return [p.strip().strip("'\"") for p in s.split(",") if p.strip()]


def load_kobbq(n: int = 80):
    from datasets import load_dataset
    ds = load_dataset("naver-ai/kobbq", split="test", streaming=False)
    rows, by_cat = [], defaultdict(int)
    for r in ds.shuffle(seed=42):
        cat = r.get("bbq_category", "?")
        if by_cat[cat] >= max(2, n // 8):
            continue
        choices = _normalize_choices(r.get("choices", []))
        if len(choices) < 2:
            continue
        rows.append({"id": r.get("sample_id"), "category": cat,
                     "context": r.get("context", ""), "question": r.get("question", ""),
                     "choices": choices, "answer": str(r.get("answer", "")).strip(),
                     "biased_answer": str(r.get("biased_answer", "")).strip()})
        by_cat[cat] += 1
        if len(rows) >= n:
            break
    return rows


def load_kmmlu(n: int = 40):
    from datasets import load_dataset
    ds = load_dataset("HAERAE-HUB/KMMLU", "Korean-History", split="test", streaming=False)
    rows = []
    for r in ds.shuffle(seed=42).select(range(min(n, len(ds)))):
        rows.append({"question": r["question"],
                     "choices": [r["A"], r["B"], r["C"], r["D"]],
                     "answer_idx": int(r["answer"]) - 1})
    return rows


def kobbq_prompt(q):
    ctx = q["context"]
    cs = "\n".join(f"{i+1}. {c}" for i, c in enumerate(q["choices"]))
    return (f"맥락: {ctx}\n\n질문: {q['question']}\n\n선택지:\n{cs}\n\n정답 번호만 출력하세요 (예: 1).")


def kmmlu_prompt(q):
    cs = "\n".join(f"{chr(ord('A') + i)}. {c}" for i, c in enumerate(q["choices"]))
    return f"질문: {q['question']}\n\n{cs}\n\n정답 알파벳만 출력하세요 (예: A)."


def parse_choice(reply, n_choices, letter=False):
    if letter:
        m = re.search(r"[A-D]", reply)
        return ord(m.group(0)) - ord("A") if m else -1
    m = re.search(r"[1-9]", reply)
    if m:
        idx = int(m.group(0)) - 1
        return idx if 0 <= idx < n_choices else -1
    return -1


class OpenAIClient:
    def __init__(self, model="gpt-5"):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model
        # Pricing per config/models.yaml (Jan 2026 cutoff snapshot).
        # gpt-5: $5 / $15 per Mtoken in / out.
        self.cost_in = 5.0
        self.cost_out = 15.0

    def query(self, prompt: str, max_tokens=10) -> tuple[str, dict]:
        # gpt-5 family deprecated `max_tokens` in favor of `max_completion_tokens`
        # and requires default temperature (temperature=1). Earlier code used
        # `max_tokens=10, temperature=0` which 400s silently.
        try:
            r = self.client.chat.completions.create(
                model=self.model,
                max_completion_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            # Raise loudly — silent score=0 was a paper-grade hazard (review C2).
            raise RuntimeError(f"OpenAI API call failed for {self.model}: {e}") from e
        usage = r.usage
        cost = (usage.prompt_tokens * self.cost_in + usage.completion_tokens * self.cost_out) / 1e6
        return r.choices[0].message.content or "", {"cost_usd": cost, "tokens": usage.total_tokens}


class AnthropicClient:
    def __init__(self, model="claude-opus-4-6"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        # Default to the dated-snapshot alias to avoid 404 on bare model names.
        self.model = model if "-2026" in model else f"{model}-20260514"
        self.cost_in = 15.0
        self.cost_out = 75.0  # per Mtoken claude opus 4.6 list price

    def query(self, prompt: str, max_tokens=10) -> tuple[str, dict]:
        try:
            r = self.client.messages.create(
                model=self.model, max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            # Raise loudly — silent score=0 hazard (review C3).
            raise RuntimeError(f"Anthropic API call failed for {self.model}: {e}") from e
        usage = r.usage
        cost = (usage.input_tokens * self.cost_in + usage.output_tokens * self.cost_out) / 1e6
        text = r.content[0].text if r.content else ""
        return text, {"cost_usd": cost, "tokens": usage.input_tokens + usage.output_tokens}


class HyperCLOVAClient:
    """Stub — requires Naver Cloud key. If not configured, skipped."""
    def __init__(self, model="HCX-005"):
        self.api_key = os.environ.get("NAVER_CLOUD_API_KEY", "")
        self.apigw_key = os.environ.get("NAVER_CLOUD_APIGW_KEY", "")
        self.model = model

    def available(self) -> bool:
        return bool(self.api_key and self.apigw_key)

    def query(self, prompt: str, max_tokens=10) -> tuple[str, dict]:
        if not self.available():
            return "", {"error": "no NAVER_CLOUD_API_KEY"}
        # Real implementation TBD — Naver Cloud HyperCLOVA X endpoint
        return "", {"error": "HyperCLOVA X integration pending — needs endpoint setup"}


def score_kobbq(client, name, rows):
    correct, biased, by_cat, total_cost = 0, 0, defaultdict(lambda: {"correct": 0, "biased": 0, "total": 0}), 0.0
    preds = []
    for q in rows:
        reply, meta = client.query(kobbq_prompt(q))
        total_cost += meta.get("cost_usd", 0)
        idx = parse_choice(reply, len(q["choices"]))
        picked = q["choices"][idx] if 0 <= idx < len(q["choices"]) else None
        is_correct = picked == q["answer"]
        is_biased = picked == q["biased_answer"]
        by_cat[q["category"]]["total"] += 1
        if is_correct:
            correct += 1; by_cat[q["category"]]["correct"] += 1
        if is_biased:
            biased += 1; by_cat[q["category"]]["biased"] += 1
        preds.append({"id": q["id"], "reply": reply[:30], "picked": picked,
                      "correct": is_correct, "biased": is_biased})
    n = len(rows)
    return {"n": n, "correct_rate": round(correct / max(1, n), 4),
            "bias_rate": round(biased / max(1, n), 4),
            "total_cost_usd": round(total_cost, 4),
            "by_category": dict(by_cat), "preds_sample": preds[:3]}


def score_kmmlu(client, name, rows):
    correct = unparsed = 0
    total_cost = 0.0
    for q in rows:
        reply, meta = client.query(kmmlu_prompt(q))
        total_cost += meta.get("cost_usd", 0)
        idx = parse_choice(reply, 4, letter=True)
        if idx == q["answer_idx"]:
            correct += 1
        elif idx < 0:
            unparsed += 1
    return {"n": len(rows), "accuracy": round(correct / max(1, len(rows)), 4),
            "unparsed": unparsed, "total_cost_usd": round(total_cost, 4)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=f"{ROOT}/results/benchmarks/api_baseline.json")
    parser.add_argument("--n-kobbq", type=int, default=80)
    parser.add_argument("--n-kmmlu", type=int, default=40)
    parser.add_argument("--skip", nargs="*", default=[], help="Skip these: openai, anthropic, hyperclova")
    args = parser.parse_args()

    # Load .env
    env_path = os.path.join(ROOT, ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    t0 = time.time()
    kobbq_rows = load_kobbq(args.n_kobbq)
    kmmlu_rows = load_kmmlu(args.n_kmmlu)
    print(f"[{time.time()-t0:.1f}s] benchmarks loaded: kobbq={len(kobbq_rows)} kmmlu={len(kmmlu_rows)}",
          flush=True)

    results = {}
    clients = []
    if "openai" not in args.skip and os.environ.get("OPENAI_API_KEY", "").startswith("sk-"):
        clients.append(("GPT-5", OpenAIClient("gpt-5")))
    if "anthropic" not in args.skip and os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-ant-"):
        clients.append(("Claude-Opus-4.6", AnthropicClient("claude-opus-4-6")))
    if "hyperclova" not in args.skip:
        hcx = HyperCLOVAClient()
        if hcx.available():
            clients.append(("HyperCLOVA-X-HCX-005", hcx))

    if not clients:
        print("ERROR: no API clients configured. Set OPENAI_API_KEY / ANTHROPIC_API_KEY / NAVER_CLOUD_API_KEY in .env")
        sys.exit(2)

    for name, client in clients:
        print(f"\n[{time.time()-t0:.1f}s] scoring {name}", flush=True)
        try:
            kb = score_kobbq(client, name, kobbq_rows)
            km = score_kmmlu(client, name, kmmlu_rows)
            results[name] = {"kobbq": kb, "kmmlu": km,
                             "total_cost_usd": kb.get("total_cost_usd", 0) + km.get("total_cost_usd", 0)}
            print(f"  → kobbq corr={kb['correct_rate']:.3f} bias={kb['bias_rate']:.3f} | "
                  f"kmmlu acc={km['accuracy']:.3f} | cost=${results[name]['total_cost_usd']:.4f}",
                  flush=True)
        except Exception as e:
            results[name] = {"error": str(e)[:300]}
            print(f"  FAIL: {type(e).__name__}: {str(e)[:200]}", flush=True)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "results": results, "elapsed_sec": round(time.time() - t0, 1)},
                  f, indent=2, ensure_ascii=False)
    print(f"\nDONE → {args.out}", flush=True)


if __name__ == "__main__":
    main()
