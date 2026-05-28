"""Bootstrap 95% CI on per-question KS distance in cross_cultural_*.json.

For each (adapter, target_culture) result, resamples the per_question KS values
with replacement N times (default 10,000), computes the mean each iter, reports
2.5th-97.5th percentile as 95% CI. Free (Mac CPU only, no GPU/API).

Output: reports/bootstrap_ci.md (paper-ready table) + JSON for paper.tex.
"""
import json, glob, random, os, re
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parent.parent
N_BOOT = 10000
SEED = 42

def bootstrap(values, n=N_BOOT, seed=SEED):
    rng = random.Random(seed)
    n_obs = len(values)
    if n_obs == 0:
        return {"n": 0, "mean": None, "ci_lo": None, "ci_hi": None}
    means = []
    for _ in range(n):
        sample = [values[rng.randrange(n_obs)] for _ in range(n_obs)]
        means.append(sum(sample) / n_obs)
    means.sort()
    return {
        "n": n_obs,
        "mean": sum(values) / n_obs,
        "median": sorted(values)[n_obs // 2],
        "ci_lo": means[int(0.025 * n)],
        "ci_hi": means[int(0.975 * n)],
        "n_bootstrap": n,
    }

def main():
    out = {}
    rows = []
    paths = sorted(glob.glob(str(ROOT / "results/benchmarks/cross_cultural_*.json")))
    print(f"[boot] processing {len(paths)} cross_cultural files")

    for p in paths:
        stem = Path(p).stem
        m = re.match(r"cross_cultural_(.+)_(kr|jp|us|cn)$", stem)
        if not m:
            continue
        adapter, culture = m.group(1), m.group(2)
        d = json.load(open(p))
        go = d.get("global_opinion") or {}
        per_q = go.get("per_question") or []
        ks_values = [q["ks"] for q in per_q if isinstance(q.get("ks"), (int, float))]
        if not ks_values:
            continue

        boot = bootstrap(ks_values)
        out[stem] = {"adapter": adapter, "culture": culture, **boot}
        rows.append((adapter, culture, boot))
        print(f"  {adapter}/{culture}: mean={boot['mean']:.3f} 95% CI [{boot['ci_lo']:.3f}, {boot['ci_hi']:.3f}] (n={boot['n']})")

    out_json = ROOT / "results/benchmarks/bootstrap_ci.json"
    with open(out_json, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[done] -> {out_json}")

    # Markdown table for paper appendix
    rows.sort(key=lambda x: (x[0], x[1]))
    md_lines = [
        "# Bootstrap 95% CI on cross-cultural KS distance",
        f"\n_Computed {N_BOOT:,} resamples with replacement, seed={SEED}._\n",
        "| Adapter | Culture | n | Mean KS | 95% CI |",
        "|---|---|---|---|---|",
    ]
    for adapter, culture, boot in rows:
        md_lines.append(
            f"| {adapter} | {culture} | {boot['n']} | "
            f"{boot['mean']:.3f} | [{boot['ci_lo']:.3f}, {boot['ci_hi']:.3f}] |"
        )
    md_path = ROOT / "reports/bootstrap_ci.md"
    md_path.write_text("\n".join(md_lines))
    print(f"[done] -> {md_path}")

if __name__ == "__main__":
    main()
    import os as _os; _os._exit(0)
