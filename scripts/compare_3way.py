"""Three-way comparison: vanilla / Run-A / Run-B on same 60 Korean prompts.

Reads:
- results/baselines/qwen2.5-3b-vanilla-corpus.json
- results/baselines/qwen2.5-3b-qlora-run-a-corpus.json
- results/baselines/qwen2.5-3b-qlora-run-b-corpus.json

Writes:
- results/baselines/three_way_diff.md (side-by-side, all 60 prompts)
- results/baselines/three_way_metrics.json (token counts, length deltas)
"""
import json
import os

ROOT = os.path.expanduser("~/orbt-research-lab")
BASELINES = os.path.join(ROOT, "results/baselines")


def load(path):
    full = os.path.join(BASELINES, path)
    if not os.path.exists(full):
        return None
    return json.load(open(full))


def main():
    vanilla = load("qwen2.5-3b-vanilla-corpus.json")
    run_a = load("qwen2.5-3b-qlora-run-a-corpus.json")
    run_b = load("qwen2.5-3b-qlora-run-b-corpus.json")

    if vanilla is None:
        print("ERROR: no vanilla corpus")
        return

    metrics = {"vanilla_tokens": 0, "run_a_tokens": 0, "run_b_tokens": 0,
               "vanilla_len_chars": 0, "run_a_len_chars": 0, "run_b_len_chars": 0,
               "n_prompts": 0, "categories": {}}

    lines = ["# Three-way comparison — Vanilla vs Run-A vs Run-B", "",
             f"- Vanilla: `{vanilla.get('model_id', '?')}`",
             f"- Run-A: {(run_a or {}).get('adapter', '(missing)')}",
             f"- Run-B: {(run_b or {}).get('adapter', '(missing)')}", ""]

    vgens = {g["prompt_id"]: g for g in vanilla["generations"]} if vanilla else {}
    ag = {g["prompt_id"]: g for g in run_a["generations"]} if run_a else {}
    bg = {g["prompt_id"]: g for g in run_b["generations"]} if run_b else {}

    for pid in sorted(vgens):
        v = vgens[pid]
        a = ag.get(pid)
        b = bg.get(pid)
        cat = v["category"]
        metrics["categories"].setdefault(cat, 0)
        metrics["categories"][cat] += 1
        metrics["n_prompts"] += 1
        metrics["vanilla_tokens"] += v["new_tokens"]
        metrics["vanilla_len_chars"] += len(v["reply"])
        if a:
            metrics["run_a_tokens"] += a["new_tokens"]
            metrics["run_a_len_chars"] += len(a["reply"])
        if b:
            metrics["run_b_tokens"] += b["new_tokens"]
            metrics["run_b_len_chars"] += len(b["reply"])
        lines.append(f"\n## [{cat}] {v['prompt'][:120]}\n")
        lines.append(f"**Vanilla** ({v['new_tokens']}t): {v['reply'][:450]}\n")
        if a:
            lines.append(f"**Run-A** ({a['new_tokens']}t): {a['reply'][:450]}\n")
        if b:
            lines.append(f"**Run-B** ({b['new_tokens']}t): {b['reply'][:450]}\n")

    diff_path = os.path.join(BASELINES, "three_way_diff.md")
    with open(diff_path, "w") as f:
        f.write("\n".join(lines))

    metrics_path = os.path.join(BASELINES, "three_way_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print(f"wrote {diff_path}")
    print(f"wrote {metrics_path}")
    print(f"vanilla_tokens={metrics['vanilla_tokens']}")
    print(f"run_a_tokens={metrics['run_a_tokens']}")
    print(f"run_b_tokens={metrics['run_b_tokens']}")


if __name__ == "__main__":
    main()
