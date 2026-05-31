"""Transfer-matrix heatmap of cross-cultural KS (n=150) for the paper.

Rows = model variants, cols = target culture. Color = mean KS (lower=better,
green; higher=worse, red). In-distribution cells (adapter's own culture) are
boxed. Output: reports/overleaf/fig_transfer_matrix.pdf (vector).
"""
import json, os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "results/benchmarks/matrix_n150"
CULTURES = ["kr", "jp", "us", "cn"]
ROWS = [
    ("vanilla-3b",       "Vanilla-3B",            None),
    ("vanilla-7b",       "Vanilla-7B",            None),
    ("koalpaca-3b-runB", "KoAlpaca-3B (Run-B)",   None),
    ("koalpaca-7b-runD", "KoAlpaca-7B (Run-D)",   None),
    ("run-f-kr",         "Cultural-KR (Run-F)",   "kr"),
    ("run-g-jp",         "Cultural-JP (Run-G)",   "jp"),
    ("run-h-us",         "Cultural-US (Run-H)",   "us"),
    ("run-i-cn",         "Cultural-CN (Run-I)",   "cn"),
    ("run-j-kr-7b",      "Cultural-KR-7B (Run-J)","kr"),
    ("run-m-multi",      "Multi-cultural (Run-M)",None),
]

def mean_ks(label, culture):
    p = SRC / f"cross_cultural_{label}_{culture}_FULL.json"
    if not p.exists():
        return np.nan
    d = json.load(open(p))
    return d.get("global_opinion", {}).get("mean_ks", np.nan)

M = np.array([[mean_ks(lab, c) for c in CULTURES] for lab, _, _ in ROWS])

fig, ax = plt.subplots(figsize=(5.2, 6.0))
im = ax.imshow(M, cmap="RdYlGn_r", vmin=0.50, vmax=0.72, aspect="auto")

ax.set_xticks(range(len(CULTURES)))
ax.set_xticklabels([c.upper() for c in CULTURES])
ax.set_yticks(range(len(ROWS)))
ax.set_yticklabels([disp for _, disp, _ in ROWS])
ax.set_xlabel("Target culture (GlobalOpinionQA)")
ax.xaxis.set_label_position("top"); ax.xaxis.tick_top()

for i, (_, _, diag) in enumerate(ROWS):
    for j, c in enumerate(CULTURES):
        v = M[i, j]
        if np.isnan(v):
            continue
        ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=8,
                color="black")
        if diag == c:  # in-distribution: box it
            ax.add_patch(Rectangle((j-0.5, i-0.5), 1, 1, fill=False,
                                   edgecolor="black", lw=2.2))

cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("Mean KS distance (lower = better alignment)")
ax.set_title("Cross-cultural alignment ($n{=}150$)\nboxed = in-distribution",
             pad=28, fontsize=10)
plt.tight_layout()
out = ROOT / "reports/overleaf/fig_transfer_matrix.pdf"
plt.savefig(out, bbox_inches="tight")
print(f"wrote {out}")
