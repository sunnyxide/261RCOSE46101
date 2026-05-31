"""De-blind and score the native-speaker rating sheet (companion to build_human_eval_kit.py).

Reads reports/human_eval/scores.json (the rater fills this:
  {"<prompt_id>": {"A": 4, "B": 2, "C": 5}, ...})
and reports/human_eval/blind_key.json, then reports per-model mean human
authenticity and the Spearman correlation with the LLM-judge CAS authenticity
medians (Cultural-KR-3B 2.70, Cultural-KR-7B 3.92, Vanilla-3B-KR 2.58 from Table 7).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HE = ROOT / "reports/human_eval"
CAS_AUTH = {"Vanilla-3B": 2.58, "Cultural-KR-3B": 2.70, "Cultural-KR-7B": 3.92}

def main():
    key = json.load(open(HE / "blind_key.json"))
    spath = HE / "scores.json"
    if not spath.exists():
        print(f"Fill {spath} first: {{'<prompt_id>': {{'A': n, 'B': n, 'C': n}}}}")
        return
    scores = json.load(open(spath))
    agg = {}
    for pid, slotmap in key.items():
        if pid not in scores:
            continue
        for lab, model in slotmap.items():
            v = scores[pid].get(lab)
            if v is None:
                continue
            agg.setdefault(model, []).append(float(v))
    print("=== Human authenticity (native speaker) vs LLM-judge CAS ===")
    rows = []
    for model in ["Vanilla-3B", "Cultural-KR-3B", "Cultural-KR-7B"]:
        vals = agg.get(model, [])
        h = sum(vals) / len(vals) if vals else float("nan")
        rows.append((model, h, CAS_AUTH[model]))
        print(f"  {model:16s} human={h:.2f} (n={len(vals)})  LLM-judge CAS={CAS_AUTH[model]}")
    # rank correlation (3 points): do human and LLM-judge agree on ordering?
    hs = [r[1] for r in rows]; cs = [r[2] for r in rows]
    order_h = sorted(range(3), key=lambda i: hs[i])
    order_c = sorted(range(3), key=lambda i: cs[i])
    print(f"\nHuman ranking:     {[rows[i][0] for i in order_h]}")
    print(f"LLM-judge ranking: {[rows[i][0] for i in order_c]}")
    print("AGREE on ordering" if order_h == order_c else "DISAGREE on ordering")

if __name__ == "__main__":
    main()
