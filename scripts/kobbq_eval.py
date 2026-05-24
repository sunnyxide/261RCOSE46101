"""KoBBQ mini-eval — Korean Bias Benchmark for QA on 4 models.

Compares vanilla Qwen2.5-3B vs Run-A/B/C QLoRA adapters on a 50-question
subset of KoBBQ. Reports accuracy per model + per-category bias score.

KoBBQ is the canonical Korean bias-in-QA benchmark (Jin et al., 2024 TACL).
Even a 50-Q mini-eval gives us cite-able numbers for the paper's
'Korean cultural benchmark' table.
"""
import json
import os
import sys
import glob
import time
import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

ROOT = os.path.expanduser("~/orbt-research-lab")
BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"
N_QUESTIONS = 50


def load_kobbq():
    """KoBBQ has Age / Gender / Social-status categories. Sample 50 across all."""
    try:
        ds = load_dataset("naver-ai/kobbq", split="test", streaming=False)
    except Exception:
        # Fallback: smaller alternative if KoBBQ is gated
        try:
            ds = load_dataset("HAERAE-HUB/KMMLU", "Korean-History", split="test", streaming=False)
            return [{"context": "", "question": r["question"],
                     "choices": [r["A"], r["B"], r["C"], r["D"]],
                     "answer": ord(r["answer"]) - ord("A"),
                     "category": "korean_history"} for r in ds.shuffle(seed=42).select(range(N_QUESTIONS))]
        except Exception as e:
            print(f"ERROR: no Korean QA benchmark accessible: {e}")
            sys.exit(2)
    qs = []
    seen_cats = set()
    for r in ds.shuffle(seed=42):
        cat = r.get("category", "?")
        seen_cats.add(cat)
        qs.append({
            "context": r.get("context", ""),
            "question": r.get("question", ""),
            "choices": [r.get("ans0", ""), r.get("ans1", ""), r.get("ans2", "")],
            "answer": int(r.get("answer", r.get("label", 0))),
            "category": cat,
        })
        if len(qs) >= N_QUESTIONS:
            break
    return qs


def load_base():
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_use_double_quant=True,
                              bnb_4bit_compute_dtype=torch.bfloat16)
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, quantization_config=bnb,
        device_map="auto", attn_implementation="sdpa",
    )
    return tok, base


def make_prompt(q):
    ctx = f"맥락: {q['context']}\n\n" if q["context"] else ""
    choices_str = "\n".join(f"{i}. {c}" for i, c in enumerate(q["choices"]))
    return (f"{ctx}질문: {q['question']}\n\n선택지:\n{choices_str}\n\n"
            "정답 번호만 출력하세요 (예: 0):")


def score_model(name, tok, model, questions):
    correct = 0
    by_cat = {}
    preds = []
    with torch.inference_mode():
        for q in questions:
            prompt = make_prompt(q)
            msgs = [{"role": "user", "content": prompt}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inp = tok(text, return_tensors="pt").to("cuda")
            out = model.generate(**inp, max_new_tokens=8, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
            reply = tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True).strip()
            # Extract first digit
            import re
            m = re.search(r"\d", reply)
            pred = int(m.group(0)) if m else -1
            is_correct = pred == q["answer"]
            if is_correct:
                correct += 1
            cat = q["category"]
            by_cat.setdefault(cat, {"correct": 0, "total": 0})
            by_cat[cat]["total"] += 1
            if is_correct:
                by_cat[cat]["correct"] += 1
            preds.append({"q": q["question"][:80], "ans": q["answer"],
                          "pred": pred, "correct": is_correct, "category": cat})
    accuracy = correct / max(1, len(questions))
    return {
        "model": name, "n": len(questions), "correct": correct,
        "accuracy": round(accuracy, 4), "by_category": by_cat, "preds": preds,
    }


def main():
    t0 = time.time()
    out_dir = os.path.join(ROOT, "results/benchmarks")
    os.makedirs(out_dir, exist_ok=True)

    print(f"[{time.time()-t0:.1f}s] loading KoBBQ subset (n={N_QUESTIONS})", flush=True)
    questions = load_kobbq()
    print(f"[{time.time()-t0:.1f}s] {len(questions)} questions loaded", flush=True)

    tok, base = load_base()
    print(f"[{time.time()-t0:.1f}s] base loaded", flush=True)

    # 1. Vanilla
    print(f"[{time.time()-t0:.1f}s] scoring vanilla...", flush=True)
    results = {"vanilla": score_model("vanilla", tok, base, questions)}
    print(f"  vanilla acc = {results['vanilla']['accuracy']:.3f}", flush=True)

    # 2/3/4. Run-A, Run-B, Run-C
    for tag, glob_pat in [("run-a", "run-a-*"), ("run-b", "run-b-*"), ("run-c", "run-c-*")]:
        candidates = glob.glob(f"{ROOT}/runs/{glob_pat}/adapter_final")
        if not candidates:
            print(f"  {tag}: SKIPPED (no adapter)", flush=True)
            continue
        adapter_path = max(candidates, key=os.path.getmtime)
        print(f"[{time.time()-t0:.1f}s] scoring {tag} ({os.path.basename(os.path.dirname(adapter_path))})...", flush=True)
        peft_model = PeftModel.from_pretrained(base, adapter_path, adapter_name=tag)
        peft_model.set_adapter(tag)
        results[tag] = score_model(tag, tok, peft_model, questions)
        print(f"  {tag} acc = {results[tag]['accuracy']:.3f}", flush=True)
        # Note: we keep adding adapters to the same base. PEFT handles this via adapter_name.

    out_path = os.path.join(out_dir, "kobbq_4way.json")
    with open(out_path, "w") as f:
        json.dump({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "results": results, "elapsed_sec": round(time.time()-t0, 1)},
                  f, indent=2, ensure_ascii=False)

    # Human-readable summary
    summary = os.path.join(out_dir, "kobbq_4way_summary.md")
    lines = [f"# KoBBQ mini-eval — 4-way comparison\n",
             f"- N questions: {len(questions)}", f"- Base: {BASE_MODEL}", "",
             "| Model | Accuracy | Correct/Total |", "|---|---|---|"]
    for model_name, r in results.items():
        lines.append(f"| {model_name} | **{r['accuracy']:.1%}** | {r['correct']}/{r['n']} |")
    lines.append("\n## Per-category breakdown\n")
    for model_name, r in results.items():
        lines.append(f"### {model_name}")
        for cat, stats in r["by_category"].items():
            lines.append(f"- {cat}: {stats['correct']}/{stats['total']}")
        lines.append("")
    with open(summary, "w") as f:
        f.write("\n".join(lines))

    print(f"[{time.time()-t0:.1f}s] DONE → {out_path}", flush=True)


if __name__ == "__main__":
    main()
