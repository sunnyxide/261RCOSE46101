"""Aggregate all results JSONs into a paper-ready table + final report.

Reads:
  results/benchmarks/phase1_extended.json        (5-way Vanilla/Run-A/B/D × KoBBQ+KMMLU+HAERAE+CLIcK)
  results/benchmarks/phase1_haerae_click_fixed.json  (rerun with fixed loaders, if available)
  results/benchmarks/cultural_*.json              (per-culture KoBBQ/HAERAE/CLIcK on cultural adapter)
  results/benchmarks/cross_cultural_*.json        (per-culture GlobalOpinionQA KS + BLEnD)

Writes:
  reports/final_results_table.md         (paper-ready markdown table)
  reports/final_summary.json             (machine-readable summary)
  reports/sections/04_results_draft.md   (Section 4 draft body)
"""
import glob, json, os
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "results" / "benchmarks"
OUT_REPORTS = ROOT / "reports"
OUT_SECTIONS = OUT_REPORTS / "sections"
OUT_REPORTS.mkdir(parents=True, exist_ok=True)
OUT_SECTIONS.mkdir(parents=True, exist_ok=True)

def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"[warn] failed to load {path}: {e}")
        return None

def fmt(v, digits=3, default="-"):
    if v is None: return default
    try: return f"{float(v):.{digits}f}"
    except (TypeError, ValueError): return str(v)

def main():
    # ---- Phase 1 (Vanilla + KoAlpaca-QLoRA baselines) ----
    phase1 = load(BENCH / "phase1_extended.json") or {}
    phase1_fixed = load(BENCH / "phase1_haerae_click_fixed.json") or {}
    phase1_results = (phase1_fixed.get("results") or phase1.get("results") or {})

    # ---- Cultural-QLoRA per-culture benchmarks ----
    cultural = {}
    for path in sorted(glob.glob(str(BENCH / "cultural_*_*.json"))):
        culture = Path(path).stem.split("_")[1]  # cultural_kr_<ts> -> kr
        if culture in ("cn", "jp", "us", "kr"):
            cultural.setdefault(culture, []).append((path, load(path)))

    # ---- Cross-cultural eval (GlobalOpinionQA + BLEnD) per adapter ----
    cross_cultural = {}
    for path in sorted(glob.glob(str(BENCH / "cross_cultural_*.json"))):
        stem = Path(path).stem
        cross_cultural[stem] = load(path)

    # ---- Build paper table ----
    lines = ["# Paper Final Results — Auto-generated\n",
             f"_generated {os.environ.get('USER','?')} / aggregate_results.py_\n"]

    lines.append("## 1. KoBBQ + KMMLU + HAE-RAE + CLIcK (Phase 1)\n")
    lines.append("| Model | KoBBQ corr | KoBBQ bias | Ambig corr | Disambig corr | KMMLU | HAE-RAE | CLIcK |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for label, r in phase1_results.items():
        k = r.get("kobbq") or {}
        ctx = (k.get("by_context_type") or {})
        m = r.get("kmmlu") or {}
        h = r.get("haerae") or {}
        c = r.get("click") or {}
        lines.append("| "+" | ".join([
            label,
            fmt(k.get("correct_rate")),
            fmt(k.get("bias_rate")),
            fmt((ctx.get("ambig") or {}).get("correct_rate")),
            fmt((ctx.get("disambig") or {}).get("correct_rate")),
            fmt(m.get("accuracy")),
            fmt(h.get("accuracy")),
            fmt(c.get("accuracy")),
        ])+" |")

    lines.append("\n## 2. Cultural-QLoRA on target benchmark (per culture)\n")
    lines.append("| Culture | Model | KoBBQ corr | KoBBQ bias | KMMLU | HAE-RAE | CLIcK |")
    lines.append("|---|---|---|---|---|---|---|")
    for culture, runs in cultural.items():
        if not runs: continue
        path, data = runs[-1]
        results = (data or {}).get("results", {})
        for label, r in results.items():
            k = r.get("kobbq") or {}
            m = r.get("kmmlu") or {}
            h = r.get("haerae") or {}
            c = r.get("click") or {}
            # Audit fix 2026-05-29: was joining culture+label as single cell,
            # producing 7 cells under 6-col header → shifted KMMLU/HAE-RAE/CLIcK.
            lines.append("| "+" | ".join([
                culture.upper(),
                label,
                fmt(k.get("correct_rate")),
                fmt(k.get("bias_rate")),
                fmt(m.get("accuracy")),
                fmt(h.get("accuracy")),
                fmt(c.get("accuracy")),
            ])+" |")

    lines.append("\n## 3. Cross-cultural alignment (GlobalOpinionQA + BLEnD)\n")
    lines.append("| Adapter | Culture | GO mean KS | GO median KS | BLEnD acc | BLEnD unparsed |")
    lines.append("|---|---|---|---|---|---|")
    for key, data in cross_cultural.items():
        if not data: continue
        go = data.get("global_opinion") or {}
        bl = data.get("blend") or {}
        lines.append("| "+" | ".join([
            key,
            str(data.get("culture", "?")),
            fmt(go.get("mean_ks")),
            fmt(go.get("median_ks")),
            fmt(bl.get("accuracy")),
            str(bl.get("unparsed", "-")),
        ])+" |")

    # ---- Section 4: CAS LLM-judge scores ----
    cas_scores = sorted(glob.glob(str(ROOT / "results/cas_scores" / "*_scored.json")))
    if cas_scores:
        lines.append("\n## 4. CAS LLM-judge panel (gpt-5.5 + Claude + mimo)\n")
        lines.append("| Adapter | Culture | Authenticity | Consistency | Factual | n_prompts | Multi-judge coverage |")
        lines.append("|---|---|---|---|---|---|---|")
        for p in cas_scores:
            d = load(p) or {}
            label = d.get("label", Path(p).stem)
            culture = d.get("culture", "?")
            overall = (d.get("overall") or {}).get("per_dim") or {}
            irr = (d.get("overall") or {}).get("inter_rater") or {}
            n_prompts = d.get("n_prompts", 0)
            # Average multi-judge coverage across 3 dims
            mj_n = [irr.get(dim, {}).get("n_with_multi_judge", 0)
                    for dim in ("cultural_authenticity", "persona_consistency", "factual_accuracy")]
            avg_mj = sum(mj_n) / 3 if mj_n else 0
            coverage = f"{avg_mj:.0f}/{n_prompts}" if n_prompts else "-"
            lines.append("| " + " | ".join([
                label, culture,
                fmt(overall.get("cultural_authenticity", {}).get("mean")),
                fmt(overall.get("persona_consistency", {}).get("mean")),
                fmt(overall.get("factual_accuracy", {}).get("mean")),
                str(n_prompts), coverage,
            ]) + " |")

    # ---- Write outputs ----
    table_path = OUT_REPORTS / "final_results_table.md"
    with open(table_path, "w") as f:
        f.write("\n".join(lines))
    print(f"[done] table -> {table_path}")

    # Compact JSON summary (machine-readable)
    summary = {
        "phase1_results": phase1_results,
        "cultural_runs": {c: [Path(p).name for p, _ in runs] for c, runs in cultural.items()},
        "cross_cultural_evals": list(cross_cultural.keys()),
    }
    summary_path = OUT_REPORTS / "final_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[done] summary -> {summary_path}")

    # Section 4 draft (markdown)
    s4 = ["# Section 4: Results\n",
          "## 4.1 Baselines\n",
          "Vanilla off-the-shelf instruction-tuned LLMs (Qwen2.5-3B/7B, GPT-5, Claude Opus 4.7) "
          "and KoAlpaca-QLoRA fine-tunes (Run-A/B/D) on Korean cultural benchmarks.\n",
          "[Insert Table 1 from results/final_results_table.md §1]\n",
          "\n## 4.2 Cultural-QLoRA per culture\n",
          "Cultural-QLoRA trained on CultureBank + Nemotron-Personas (KR) + Hofstede-conditioned "
          "instruction prompts achieves [TODO insert findings] on target-culture benchmarks.\n",
          "[Insert Table 2 §2]\n",
          "\n## 4.3 Cross-cultural alignment (main contribution)\n",
          "GlobalOpinionQA KS-statistic measures how closely the model's response distribution "
          "matches the target country's empirical distribution from multinational opinion surveys. "
          "Lower = better alignment.\n",
          "[Insert Table 3 §3 and Hofstede 6D shift heatmap]\n",
          "\n## 4.4 Ablations\n",
          "[Run-J: Qwen-7B FP16 vs Qwen-7B bnb-4bit — addresses quantization confound]\n"]
    s4_path = OUT_SECTIONS / "04_results_draft.md"
    with open(s4_path, "w") as f:
        f.write("\n".join(s4))
    print(f"[done] section 4 draft -> {s4_path}")

if __name__ == "__main__":
    main()
