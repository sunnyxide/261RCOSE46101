"""Generate n=150 LaTeX table rows + significance flags for paper.tex.

Reads results/benchmarks/matrix_n150/cross_cultural_{label}_{culture}_FULL.json,
computes per-cell mean KS + bootstrap 95% CI (10K resamples on full per-question
KS), and emits:
  - Table 5 (cross-cultural) rows: mean +/- half-width CI
  - Table 6 (Hofstede ablation, KR target) rows (reads diagonal full_perq if present)
  - vanilla-vs-adapter CI-overlap verdicts (significance)
Pure stdlib; runs on Mac CPU.
"""
import json, glob, os, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
N_BOOT = 10000
SEED = 42

def boot(vals, seed=SEED):
    rng = random.Random(seed); n = len(vals); ms = []
    for _ in range(N_BOOT):
        ms.append(sum(vals[rng.randrange(n)] for _ in range(n)) / n)
    ms.sort()
    return {"mean": sum(vals)/n, "lo": ms[int(.025*N_BOOT)], "hi": ms[int(.975*N_BOOT)], "n": n}

def load_ks(path):
    d = json.load(open(path))
    go = d.get("global_opinion", {})
    return [q["ks"] for q in go.get("per_question", []) if isinstance(q.get("ks"), (int, float))]

def cell(label, culture, search_dirs):
    for sd in search_dirs:
        p = ROOT / sd / f"cross_cultural_{label}_{culture}_FULL.json"
        if p.exists():
            ks = load_ks(p)
            if ks:
                return boot(ks)
    return None

# label -> display name + base for Table 5 (order matters)
ROWS = [
    ("vanilla-3b",        "Vanilla-3B"),
    ("vanilla-7b",        "Vanilla-7B (unsloth)"),
    ("koalpaca-3b-runB",  "KoAlpaca-3B (Run-B)"),
    ("koalpaca-7b-runD",  "KoAlpaca-7B (Run-D)"),
    ("run-f-kr",          "Cultural-KR (3B, Run-F)"),
    ("run-g-jp",          "Cultural-JP (3B, Run-G)"),
    ("run-h-us",          "Cultural-US (3B, Run-H)"),
    ("run-i-cn",          "Cultural-CN (3B, Run-I)"),
    ("run-j-kr-7b",       "Cultural-KR (7B, Run-J)"),
    ("run-m-multi",       "Multi-cultural (Run-M)"),
]
DIAG = {"run-f-kr": "kr", "run-g-jp": "jp", "run-h-us": "us", "run-i-cn": "cn",
        "run-j-kr-7b": "kr"}  # bold cells (in-distribution)
SEARCH = ["results/benchmarks/matrix_n150", "results/benchmarks/full_perq"]

def fmt(b, bold=False):
    if b is None:
        return "--"
    half = (b["hi"] - b["lo"]) / 2
    s = f"{b['mean']:.3f}\\,$\\pm$\\,{half:.3f}"
    return f"\\textbf{{{s}}}" if bold else s

print("% ===== Table 5: cross-cultural KS (n=150) =====")
vanilla = {c: cell("vanilla-3b", c, SEARCH) for c in ["kr","jp","us","cn"]}
for label, disp in ROWS:
    cells = {c: cell(label, c, SEARCH) for c in ["kr","jp","us","cn"]}
    parts = []
    for c in ["kr","jp","us","cn"]:
        parts.append(fmt(cells[c], bold=(DIAG.get(label) == c)))
    print(f"{disp} & " + " & ".join(parts) + r" \\")

print("\n% ===== Significance vs Vanilla-3B (same target) =====")
for label, disp in ROWS:
    if label == "vanilla-3b": continue
    for c in ["kr","jp","us","cn"]:
        b = cell(label, c, SEARCH); v = vanilla[c]
        if b and v:
            overlap = not (b["hi"] < v["lo"] or b["lo"] > v["hi"])
            better = b["mean"] < v["mean"]
            tag = "SIG" if not overlap else "ns"
            print(f"  {disp:28s} {c}: {b['mean']:.3f} vs vanilla {v['mean']:.3f}  "
                  f"{'better' if better else 'worse '}  CI-overlap={overlap}  [{tag}]")

print("\n% ===== Table 6: Hofstede ablation (KR target, n=150) =====")
ABL = [("vanilla-3b","Vanilla Qwen2.5-3B (no Hofstede)"),
       ("abl-kr-idv-only","IDV-only (collectivism, KR=18)"),
       ("abl-kr-uai-only","UAI-only (uncertainty avoidance, KR=85)"),
       ("abl-kr-all6d","Full 6-D system prompt"),
       ("run-f-kr","Run-F: full 6-D + LoRA (Cultural-KR-3B)"),
       ("run-j-kr-7b","Run-J: full 6-D + LoRA (Cultural-KR-7B)")]
for label, disp in ABL:
    b = cell(label, "kr", SEARCH)
    print(f"{disp} & {fmt(b)} " + r"\\")
