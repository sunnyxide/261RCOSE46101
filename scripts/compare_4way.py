"""Four-way comparison: vanilla / Run-A / Run-B / Run-C on 60 Korean prompts.

Extension of compare_3way.py to include Run-C (KULLM-v2 data ablation).
"""
import json
import os

ROOT = os.path.expanduser("~/orbt-research-lab")
BASELINES = os.path.join(ROOT, "results/baselines")


def load(name):
    p = os.path.join(BASELINES, name)
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    v = load("qwen2.5-3b-vanilla-corpus.json")
    a = load("qwen2.5-3b-qlora-run-a-corpus.json")
    b = load("qwen2.5-3b-qlora-run-b-corpus.json")
    c = load("qwen2.5-3b-qlora-run-c-corpus.json")
    if v is None:
        print("ERROR: no vanilla corpus"); return

    metrics = {"vanilla_tokens": 0, "run_a_tokens": 0, "run_b_tokens": 0, "run_c_tokens": 0,
               "vanilla_chars": 0, "run_a_chars": 0, "run_b_chars": 0, "run_c_chars": 0,
               "n_prompts": 0, "categories": {}}

    lines = ["# Four-way comparison — Vanilla vs Run-A vs Run-B vs Run-C", "",
             f"- Vanilla: `{v.get('model_id','?')}`",
             f"- Run-A (KoAlpaca 8k, rank 16): {(a or {}).get('adapter', '(missing)')}",
             f"- Run-B (KoAlpaca 15k, rank 32, 2ep): {(b or {}).get('adapter', '(missing)')}",
             f"- Run-C (KULLM-v2 10k, rank 16): {(c or {}).get('adapter', '(missing)')}", ""]

    gens = {x: {g["prompt_id"]: g for g in (corpus or {}).get("generations", [])}
            for x, corpus in [("v", v), ("a", a), ("b", b), ("c", c)]}

    for pid in sorted(gens["v"]):
        vg = gens["v"][pid]
        cat = vg["category"]
        metrics["categories"].setdefault(cat, 0); metrics["categories"][cat] += 1
        metrics["n_prompts"] += 1
        for key, suffix in [("v", "vanilla"), ("a", "run_a"), ("b", "run_b"), ("c", "run_c")]:
            g = gens[key].get(pid)
            if g:
                metrics[f"{suffix}_tokens"] += g["new_tokens"]
                metrics[f"{suffix}_chars"] += len(g["reply"])
        lines.append(f"\n## [{cat}] {vg['prompt'][:140]}\n")
        for tag, key in [("Vanilla", "v"), ("Run-A", "a"), ("Run-B", "b"), ("Run-C", "c")]:
            g = gens[key].get(pid)
            if g:
                lines.append(f"**{tag}** ({g['new_tokens']}t): {g['reply'][:400]}\n")

    diff_path = os.path.join(BASELINES, "four_way_diff.md")
    metrics_path = os.path.join(BASELINES, "four_way_metrics.json")
    with open(diff_path, "w") as f:
        f.write("\n".join(lines))
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"wrote {diff_path}")
    print(f"wrote {metrics_path}")
    print(f"vanilla={metrics['vanilla_tokens']} a={metrics['run_a_tokens']} b={metrics['run_b_tokens']} c={metrics['run_c_tokens']}")


if __name__ == "__main__":
    main()
