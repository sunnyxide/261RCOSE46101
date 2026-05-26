"""Korean cultural benchmark evaluation — KoBBQ + KMMLU on multiple models.

For each model (vanilla + every Run-* adapter), reports:
  - KoBBQ correct_rate (model picked the right answer text)
  - KoBBQ bias_rate (model picked the biased_answer — should be LOW for good model)
  - KMMLU accuracy (Korean MCQ across 6 humanities categories)

Saves results/benchmarks/korean_bench_4way.json + summary.md.

KoBBQ schema (verified 2026-05-26):
  question, choices (list), answer (text), biased_answer (text), bbq_category
KMMLU schema:
  question, A/B/C/D, answer (int 1-4), Category
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from collections import defaultdict

import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

ROOT = os.path.expanduser("~/orbt-research-lab")
BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"


def _normalize_choices(raw):
    """KoBBQ stores `choices` as a stringified Python list. Normalize to list[str].
    Pure string parsing (no eval) — split on commas inside brackets, strip quotes.
    """
    if isinstance(raw, list):
        return [str(c).strip() for c in raw]
    if not isinstance(raw, str):
        return []
    s = raw.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    # Replace single quotes with double for JSON parsing
    import json as _json
    try:
        parsed = _json.loads("[" + s.replace("'", '"') + "]")
        if isinstance(parsed, list):
            return [str(c).strip() for c in parsed]
    except Exception:
        pass
    # Last-resort split
    parts = [p.strip().strip("'\"") for p in s.split(",") if p.strip()]
    return parts


def load_kobbq_subset(n: int = 80):
    """Mix of ambiguous + disambiguated contexts across all categories."""
    try:
        ds = load_dataset("naver-ai/kobbq", split="test", streaming=False)
    except Exception as e:
        print(f"KoBBQ load failed: {e}")
        return []
    rows = []
    by_cat = defaultdict(int)
    for r in ds.shuffle(seed=42):
        cat = r.get("bbq_category", "?")
        if by_cat[cat] >= max(2, n // 8):
            continue
        choices = _normalize_choices(r.get("choices", []))
        if len(choices) < 2:
            continue
        rows.append({
            "id": r.get("sample_id"),
            "category": cat,
            "context": r.get("context", ""),
            "question": r.get("question", ""),
            "choices": choices,
            "answer": str(r.get("answer", "")).strip(),
            "biased_answer": str(r.get("biased_answer", "")).strip(),
            "label_annotation": r.get("label_annotation", ""),
        })
        by_cat[cat] += 1
        if len(rows) >= n:
            break
    return rows


def load_kmmlu_subset(n: int = 40):
    """KMMLU Korean-History as a knowledge-grounded MCQ supplement."""
    try:
        ds = load_dataset("HAERAE-HUB/KMMLU", "Korean-History", split="test", streaming=False)
    except Exception as e:
        print(f"KMMLU load failed: {e}")
        return []
    rows = []
    for r in ds.shuffle(seed=42).select(range(min(n, len(ds)))):
        rows.append({
            "question": r["question"],
            "choices": [r["A"], r["B"], r["C"], r["D"]],
            "answer_idx": int(r["answer"]) - 1,  # 1-based → 0-based
            "answer_text": [r["A"], r["B"], r["C"], r["D"]][int(r["answer"]) - 1],
        })
    return rows


def make_kobbq_prompt(q):
    ctx = q["context"]
    choices_str = "\n".join(f"{i+1}. {c}" for i, c in enumerate(q["choices"]))
    return (f"맥락: {ctx}\n\n질문: {q['question']}\n\n선택지:\n{choices_str}\n\n"
            "정답 번호만 출력하세요 (예: 1).")


def make_kmmlu_prompt(q):
    choices_str = "\n".join(f"{chr(ord('A') + i)}. {c}" for i, c in enumerate(q["choices"]))
    return (f"질문: {q['question']}\n\n{choices_str}\n\n"
            "정답 알파벳만 출력하세요 (예: A).")


def parse_choice(reply: str, n_choices: int, letter: bool = False):
    """Return 0-based choice index, or -1 if can't parse."""
    if letter:
        m = re.search(r"[A-D]", reply)
        if m:
            return ord(m.group(0)) - ord("A")
    else:
        m = re.search(r"[1-9]", reply)
        if m:
            idx = int(m.group(0)) - 1
            if 0 <= idx < n_choices:
                return idx
    return -1


def load_base():
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_use_double_quant=True,
                              bnb_4bit_compute_dtype=torch.bfloat16)
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, quantization_config=bnb, device_map="auto",
        attn_implementation="sdpa",
    )
    return tok, base


def score_kobbq(model, tok, rows):
    correct = 0
    biased = 0
    by_cat = defaultdict(lambda: {"correct": 0, "biased": 0, "total": 0, "unparsed": 0})
    preds = []
    with torch.inference_mode():
        for q in rows:
            prompt = make_kobbq_prompt(q)
            msgs = [{"role": "user", "content": prompt}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inp = tok(text, return_tensors="pt").to("cuda")
            out = model.generate(**inp, max_new_tokens=6, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
            reply = tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True).strip()
            idx = parse_choice(reply, len(q["choices"]))
            if 0 <= idx < len(q["choices"]):
                picked = q["choices"][idx]
                is_correct = (picked == q["answer"])
                is_biased = (picked == q["biased_answer"])
            else:
                picked = None
                is_correct = False
                is_biased = False
                by_cat[q["category"]]["unparsed"] += 1
            by_cat[q["category"]]["total"] += 1
            if is_correct:
                correct += 1
                by_cat[q["category"]]["correct"] += 1
            if is_biased:
                biased += 1
                by_cat[q["category"]]["biased"] += 1
            preds.append({"id": q["id"], "category": q["category"],
                          "reply": reply, "picked": picked,
                          "correct": is_correct, "biased": is_biased})
    n = len(rows)
    return {
        "n": n,
        "correct_rate": round(correct / max(1, n), 4),
        "bias_rate": round(biased / max(1, n), 4),
        "by_category": {c: {
            "correct_rate": round(v["correct"] / max(1, v["total"]), 4),
            "bias_rate": round(v["biased"] / max(1, v["total"]), 4),
            "unparsed": v["unparsed"], "total": v["total"],
        } for c, v in by_cat.items()},
        "preds_sample": preds[:5],
    }


def score_kmmlu(model, tok, rows):
    correct = 0
    unparsed = 0
    preds = []
    with torch.inference_mode():
        for q in rows:
            prompt = make_kmmlu_prompt(q)
            msgs = [{"role": "user", "content": prompt}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inp = tok(text, return_tensors="pt").to("cuda")
            out = model.generate(**inp, max_new_tokens=6, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
            reply = tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True).strip()
            idx = parse_choice(reply, 4, letter=True)
            if idx == q["answer_idx"]:
                correct += 1
            elif idx < 0:
                unparsed += 1
            preds.append({"q": q["question"][:60], "ans_idx": q["answer_idx"],
                          "pred_idx": idx, "correct": (idx == q["answer_idx"])})
    return {
        "n": len(rows),
        "accuracy": round(correct / max(1, len(rows)), 4),
        "unparsed": unparsed,
        "preds_sample": preds[:5],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-kobbq", type=int, default=80)
    parser.add_argument("--n-kmmlu", type=int, default=40)
    args = parser.parse_args()

    t0 = time.time()
    out_dir = os.path.join(ROOT, "results/benchmarks")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[{time.time()-t0:.1f}s] loading benchmarks", flush=True)
    kobbq_rows = load_kobbq_subset(args.n_kobbq)
    kmmlu_rows = load_kmmlu_subset(args.n_kmmlu)
    print(f"[{time.time()-t0:.1f}s] KoBBQ={len(kobbq_rows)} KMMLU={len(kmmlu_rows)}", flush=True)

    tok, base = load_base()
    print(f"[{time.time()-t0:.1f}s] base loaded", flush=True)

    results = {}

    # 1. vanilla
    print(f"[{time.time()-t0:.1f}s] scoring vanilla", flush=True)
    results["vanilla"] = {
        "model_id": BASE_MODEL,
        "kobbq": score_kobbq(base, tok, kobbq_rows),
        "kmmlu": score_kmmlu(base, tok, kmmlu_rows),
    }
    print(f"  vanilla kobbq: correct={results['vanilla']['kobbq']['correct_rate']:.3f} "
          f"bias={results['vanilla']['kobbq']['bias_rate']:.3f} | "
          f"kmmlu={results['vanilla']['kmmlu']['accuracy']:.3f}",
          flush=True)

    # 2/3/4. adapters
    current_peft = None
    for tag, pat in [("run-a", "run-a-*"), ("run-b", "run-b-*"),
                     ("run-c", "run-c-*"), ("run-d", "run-d-*"), ("run-e", "run-e-*")]:
        candidates = glob.glob(f"{ROOT}/runs/{pat}/adapter_final")
        candidates = [c for c in candidates if os.path.exists(os.path.join(c, "adapter_config.json"))]
        if not candidates:
            continue
        adapter_path = max(candidates, key=os.path.getmtime)
        print(f"[{time.time()-t0:.1f}s] scoring {tag} ({os.path.basename(os.path.dirname(adapter_path))})",
              flush=True)
        if current_peft is None:
            peft_model = PeftModel.from_pretrained(base, adapter_path, adapter_name=tag)
            current_peft = peft_model
        else:
            current_peft.load_adapter(adapter_path, adapter_name=tag)
        current_peft.set_adapter(tag)
        results[tag] = {
            "adapter": adapter_path,
            "kobbq": score_kobbq(current_peft, tok, kobbq_rows),
            "kmmlu": score_kmmlu(current_peft, tok, kmmlu_rows),
        }
        print(f"  {tag} kobbq: correct={results[tag]['kobbq']['correct_rate']:.3f} "
              f"bias={results[tag]['kobbq']['bias_rate']:.3f} | "
              f"kmmlu={results[tag]['kmmlu']['accuracy']:.3f}",
              flush=True)

    # save
    out_path = os.path.join(out_dir, "korean_bench_results.json")
    with open(out_path, "w") as f:
        json.dump({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "results": results, "elapsed_sec": round(time.time() - t0, 1)},
                  f, indent=2, ensure_ascii=False)

    # summary md
    summary_path = os.path.join(out_dir, "korean_bench_summary.md")
    lines = [f"# Korean cultural benchmark — multi-way comparison\n",
             f"- N KoBBQ: {len(kobbq_rows)} ({len(set(r['category'] for r in kobbq_rows))} categories)",
             f"- N KMMLU: {len(kmmlu_rows)} (Korean-History)",
             f"- Base: {BASE_MODEL}", "",
             "## KoBBQ (Korean Bias Benchmark)",
             "| Model | Correct rate | Bias rate | n |",
             "|---|---|---|---|"]
    for model, r in results.items():
        kb = r["kobbq"]
        lines.append(f"| {model} | **{kb['correct_rate']:.1%}** | {kb['bias_rate']:.1%} | {kb['n']} |")
    lines += ["", "Lower bias_rate is better — measures how often model picks the biased answer.",
              "Higher correct_rate is better — measures factual correctness on unbiased ground.",
              "", "## KMMLU Korean History",
              "| Model | Accuracy | Unparsed | n |",
              "|---|---|---|---|"]
    for model, r in results.items():
        km = r["kmmlu"]
        lines.append(f"| {model} | **{km['accuracy']:.1%}** | {km['unparsed']} | {km['n']} |")
    with open(summary_path, "w") as f:
        f.write("\n".join(lines))

    print(f"[{time.time()-t0:.1f}s] DONE → {out_path}", flush=True)


if __name__ == "__main__":
    main()
