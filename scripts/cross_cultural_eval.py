"""Cross-cultural alignment evaluation — paper's main contribution metric.

Two complementary benchmarks:

1. GlobalOpinionQA (Anthropic) — KS test against per-country response distributions
   - Multinational opinion questions with country-level gold distributions
   - Metric: KS statistic between model's response distribution (sampled N times) and
     the target country's empirical distribution. Lower = better cultural alignment.

2. BLEnD MCQ (Lee et al. 2024) — country-conditioned cultural common-sense MCQ
   - "What is a common snack for preschool kids in {country}?" with country-tagged choices.
   - Metric: accuracy when model is asked from the perspective of the target country.

Usage (per culture):
  python scripts/cross_cultural_eval.py \
      --base Qwen/Qwen2.5-3B-Instruct \
      --adapter ~/orbt-research-lab/runs/run-f-kr-*/adapter_final \
      --culture kr --n-globalopinion 200 --n-blend 100 \
      --out results/benchmarks/cross_cultural_kr_run-f.json

Country codes: kr->South_Korea, jp->Japan, us->United States, cn->China.
"""
import argparse, glob, json, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CULTURE_NAMES = {
    # GlobalOpinionQA uses abbreviations like "S. Korea" — match substring "Korea"
    "kr": {"globalopinion": "Korea", "blend": "South_Korea",   "label_en": "Korea"},
    "jp": {"globalopinion": "Japan", "blend": "Japan",         "label_en": "Japan"},
    "us": {"globalopinion": "United States","blend": "US",     "label_en": "United States"},
    "cn": {"globalopinion": "China", "blend": "China",         "label_en": "China"},
}

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # bug audit 2026-05-29: GO has up to 9 options

def build_mcq_prompt(question, choices, culture_label, culture_token=None):
    # Run-M (multi-cultural unified adapter) is trained with a `<<culture:xx>>`
    # token prepended to the user instruction; activate it at inference when
    # culture_token is set so the eval matches the §3.7 method description.
    q = f"<<culture:{culture_token}>> {question}" if culture_token else question
    lines = [f"Q (you are answering from a {culture_label} cultural perspective): {q}"]
    for i, c in enumerate(choices):
        lines.append(f"  {LETTERS[i]}. {c}")
    lines.append("\nA single letter only. Answer:")
    return "\n".join(lines)

def parse_letter(reply, n_choices):
    # Accept up to LETTERS[n_choices-1] dynamically
    if n_choices <= 0: return None
    max_letter = LETTERS[min(n_choices - 1, len(LETTERS) - 1)]
    m = re.search(f"[A-{max_letter}]", reply.strip().upper())
    if not m: return None
    idx = ord(m.group(0)) - ord("A")
    return idx if 0 <= idx < n_choices else None

def load_globalopinion(target_country_name, n=200):
    from datasets import load_dataset
    ds = load_dataset("Anthropic/llm_global_opinions", split="train")
    rows = []
    for r in ds:
        sel = r.get("selections") or {}
        # HF may return selections as a JSON string instead of dict — handle both.
        # Root cause of repeated 0-result cross-cultural eval runs on 5/26-5/28.
        if isinstance(sel, str):
            try:
                # The string format uses Python repr (defaultdict(...)) — try eval-safe parse first
                # Strip "defaultdict(<class 'list'>, {...})" wrapper if present
                if sel.startswith("defaultdict"):
                    import re as _re
                    m = _re.search(r"\{.*\}", sel, _re.DOTALL)
                    if m: sel = m.group(0)
                # Now try JSON-like — replace single quotes with double quotes
                sel = json.loads(sel.replace("'", '"'))
            except Exception:
                continue
        if not isinstance(sel, dict):
            continue
        match_key = None
        for k in sel.keys():
            if target_country_name.lower() in str(k).lower():
                match_key = k
                break
        if not match_key:
            continue
        dist = sel[match_key]
        if not isinstance(dist, list) or len(dist) < 2:
            continue
        options = r.get("options") or []
        # 3rd bug: `options` is ALSO serialized as JSON string in GlobalOpinionQA,
        # not list — len("[...]") gave char count not list length, so every Korea
        # match silently dropped via "options != dist length" check. Probe on AWS
        # found 790 Korea hits, 0 passed this gate; after parsing, 564 valid rows.
        if isinstance(options, str):
            try:
                options = json.loads(options.replace("'", '"'))
            except Exception:
                continue
        if not isinstance(options, list) or len(options) != len(dist):
            continue
        rows.append({
            "question": r["question"],
            "options": options,
            "gold_dist": list(dist),
        })
        if len(rows) >= n:
            break
    return rows

def ks_stat(p_emp, q_pred):
    """KS over a discrete distribution via max cumulative diff."""
    import numpy as np
    p = np.array(p_emp, dtype=float); q = np.array(q_pred, dtype=float)
    if p.sum() == 0 or q.sum() == 0: return 1.0
    p = p / p.sum(); q = q / q.sum()
    cp, cq = np.cumsum(p), np.cumsum(q)
    return float(np.max(np.abs(cp - cq)))

def score_globalopinion(model_fn, rows, n_samples=10, culture_token=None):
    """For each question, generate n_samples model responses, compare distribution."""
    results = []
    for row in rows:
        opts = row["options"]
        counts = [0] * len(opts)
        for _ in range(n_samples):
            prompt = build_mcq_prompt(row["question"], opts, "neutral", culture_token)
            reply = model_fn(prompt, max_new_tokens=4)
            idx = parse_letter(reply, len(opts))
            if idx is not None:
                counts[idx] += 1
        ks = ks_stat(row["gold_dist"], counts)
        results.append({"q": row["question"][:80], "ks": ks,
                        "gold": row["gold_dist"], "pred": counts})
    if not results:
        return {"n": 0, "mean_ks": None}
    return {
        "n": len(results),
        "n_samples_per_q": n_samples,
        "mean_ks": sum(r["ks"] for r in results) / len(results),
        "median_ks": sorted(r["ks"] for r in results)[len(results)//2],
        # Store ALL per-question results so bootstrap CI uses full sample
        # (audit 2026-05-29: prior :20 slice gave artificially wide CIs)
        "per_question": results,
    }

def load_blend(blend_country, n=100):
    from datasets import load_dataset
    ds = load_dataset("nayeon212/BLEnD", "multiple-choice-questions", split="test")
    rows = []
    for r in ds:
        if str(r.get("country", "")) != blend_country:
            continue
        choices_raw = r.get("choices") or {}
        if isinstance(choices_raw, str):
            choices_raw = json.loads(choices_raw)
        items = [choices_raw.get(L, "") for L in LETTERS[:4]]
        if any(not x for x in items):
            continue
        ans = str(r.get("answer_idx", "")).strip()
        m = re.search(r"[A-D]", ans)
        if not m: continue
        ans_idx = ord(m.group(0)) - ord("A")
        rows.append({
            "prompt": r["prompt"],
            "choices": items,
            "answer_idx": ans_idx,
        })
        if len(rows) >= n:
            break
    return rows

def score_blend(model_fn, rows, culture_label, culture_token=None):
    correct = 0; total = 0; unparsed = 0
    per_q = []
    for row in rows:
        prompt = build_mcq_prompt(row["prompt"], row["choices"], culture_label, culture_token)
        reply = model_fn(prompt, max_new_tokens=4)
        idx = parse_letter(reply, len(row["choices"]))
        if idx is None:
            unparsed += 1; total += 1; continue
        if idx == row["answer_idx"]:
            correct += 1
        total += 1
        per_q.append({"q": row["prompt"][:80], "pred": idx, "gold": row["answer_idx"]})
    return {"n": total, "correct": correct, "unparsed": unparsed,
            "accuracy": correct / max(total, 1),
            "per_q_sample": per_q[:10]}

def make_model_fn(base_model, adapter_path=None):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
    prequantized = ("-bnb-4bit" in base_model.lower()) or ("4bit" in base_model.lower())
    tok = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    kw = {"device_map": "auto", "attn_implementation": "sdpa", "trust_remote_code": True}
    if not prequantized:
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16,
        )
    else:
        kw["torch_dtype"] = torch.bfloat16
    model = AutoModelForCausalLM.from_pretrained(base_model, **kw)
    if adapter_path:
        if "*" in adapter_path:
            matches = glob.glob(os.path.expanduser(adapter_path))
            if not matches:
                raise FileNotFoundError(f"no adapter at {adapter_path}")
            adapter_path = matches[0]
        model = PeftModel.from_pretrained(model, adapter_path)
    model.train(False)  # inference mode
    def fn(prompt, max_new_tokens=4):
        msgs = [{"role": "user", "content": prompt}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inp = tok(text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=max_new_tokens,
                                  do_sample=False, pad_token_id=tok.eos_token_id)
        return tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)
    return fn

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--culture", required=True, choices=list(CULTURE_NAMES.keys()))
    ap.add_argument("--n-globalopinion", type=int, default=200)
    ap.add_argument("--n-blend", type=int, default=100)
    ap.add_argument("--n-samples-globalopinion", type=int, default=8)
    ap.add_argument("--culture-token", action="store_true",
                    help="prepend <<culture:{culture}>> token (Run-M multi-cultural adapter)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    culture_token = args.culture if args.culture_token else None

    cm = CULTURE_NAMES[args.culture]
    t0 = time.time()

    print(f"[init] loading {args.base} + adapter={args.adapter}", flush=True)
    model_fn = make_model_fn(args.base, args.adapter)
    print(f"[{time.time()-t0:.1f}s] model loaded", flush=True)

    print(f"[load] GlobalOpinionQA for '{cm['globalopinion']}' (n={args.n_globalopinion})", flush=True)
    go_rows = load_globalopinion(cm["globalopinion"], args.n_globalopinion)
    print(f"  -> {len(go_rows)} rows", flush=True)
    print(f"[load] BLEnD MCQ for '{cm['blend']}' (n={args.n_blend})", flush=True)
    blend_rows = load_blend(cm["blend"], args.n_blend)
    print(f"  -> {len(blend_rows)} rows", flush=True)

    print(f"[score] GlobalOpinionQA (n_samples={args.n_samples_globalopinion})", flush=True)
    go_results = score_globalopinion(model_fn, go_rows, args.n_samples_globalopinion, culture_token)
    print(f"  -> mean KS = {go_results.get('mean_ks')}", flush=True)
    print(f"[score] BLEnD", flush=True)
    blend_results = score_blend(model_fn, blend_rows, cm["label_en"], culture_token)
    print(f"  -> accuracy = {blend_results['accuracy']:.3f}", flush=True)

    out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base": args.base,
        "adapter": args.adapter,
        "culture": args.culture,
        "culture_token": culture_token,
        "global_opinion": go_results,
        "blend": blend_results,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"[done] -> {args.out} in {out['elapsed_sec']}s", flush=True)

if __name__ == "__main__":
    main()
