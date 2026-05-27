"""CAS (Cultural Alignment Score) 3-judge panel.

Reads persona corpus JSONs from results/cas_corpus/ (produced by reinforcement_a/b
on AWS), asks three independent judges to rate each generation 1-5 on:
  - cultural_authenticity: does this read like a native of the target culture?
  - persona_consistency: does it stay in character?
  - factual_accuracy: are cultural facts/practices correct?

Judges:
  - Tier A: GPT-5 (OpenAI API, reasoning_effort='minimal')
  - Tier B: Claude Opus 4.7 (Anthropic API)
  - Tier C: Local Qwen3.5-27B-Claude-Opus-Distilled-MLX-4bit (via oMLX :11434)

Aggregation: median of 3 judges per dimension. Inter-rater agreement
(Krippendorff's alpha) reported as reliability check.

Output: results/cas_scores/<corpus_name>_scored.json with:
  - per-prompt scores from each judge
  - aggregate (median) score per dimension
  - inter-rater alpha

Usage:
  python scripts/cas_judge_panel.py --corpus results/cas_corpus/cultural-kr_kr.json \
      --culture kr --out results/cas_scores/cultural-kr_kr_scored.json
"""
import argparse, json, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CULTURE_LABELS = {"kr": "Korean", "jp": "Japanese", "us": "American", "cn": "Chinese"}

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator of culturally-grounded text generation. Rate the following AI response to a culturally-relevant prompt.

CULTURAL CONTEXT: {culture}
USER PROMPT: {prompt}
AI RESPONSE: {reply}

Rate on three dimensions, each 1-5:
1. cultural_authenticity (does this sound like a native of {culture} speaking, not a tourist?)
2. persona_consistency (does the response maintain a coherent persona throughout?)
3. factual_accuracy (are cultural facts, customs, terminology correct?)

Respond with ONLY a JSON object, no explanation:
{{"cultural_authenticity": <1-5>, "persona_consistency": <1-5>, "factual_accuracy": <1-5>}}
"""

def parse_scores(text):
    """Extract scores JSON from judge response (handles markdown fences, extra text)."""
    if not text: return None
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Find JSON object
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if not m: return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    out = {}
    for k in ("cultural_authenticity", "persona_consistency", "factual_accuracy"):
        v = d.get(k)
        if isinstance(v, (int, float)) and 1 <= v <= 5:
            out[k] = float(v)
    if len(out) != 3: return None
    return out

# ---------------- Judges ----------------

def judge_gpt5(prompt):
    from openai import OpenAI
    client = OpenAI()
    r = client.chat.completions.create(
        model="gpt-5.5",
        max_completion_tokens=200,
        messages=[{"role": "user", "content": prompt}],
        reasoning_effort="none",
    )
    return r.choices[0].message.content

def judge_claude(prompt):
    import anthropic
    client = anthropic.Anthropic()
    r = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text if r.content else ""

def judge_local(prompt, model_id="Qwen3.6-35B-A3B-4bit-DWQ"):
    """Local oMLX-served Qwen3.6-35B-A3B-4bit-DWQ at :11434.

    Use the user's CURRENTLY-LOADED default model (Qwen3.6-35B-A3B-4bit-DWQ)
    so we don't trigger a model swap on oMLX, which has caused OOM in the past
    (see 2026-05-27 incident analysis). DO NOT change to Qwen3.5-Claude-distilled
    or other models without first confirming with user that swap is safe.

    Note: latency ~5-15s per call. Generous max_tokens (800) to allow reasoning
    before final JSON.
    """
    import urllib.request
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt +
                      "\n\nReason briefly then output ONLY the JSON on the final line."}],
        "max_tokens": 800,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.loads(resp.read())
    return d["choices"][0]["message"]["content"]

JUDGES = [
    ("gpt5", judge_gpt5),
    ("claude", judge_claude),
    ("local_qwen27b", judge_local),
]

# ---------------- Aggregation ----------------

def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0: return None
    return xs[n//2] if n % 2 else (xs[n//2 - 1] + xs[n//2]) / 2

def aggregate(per_prompt_scores):
    """For each prompt, compute median of available judges per dimension."""
    out = []
    for entry in per_prompt_scores:
        agg = {}
        for dim in ("cultural_authenticity", "persona_consistency", "factual_accuracy"):
            vals = [entry["judges"][j][dim] for j in entry["judges"]
                    if entry["judges"][j] and dim in entry["judges"][j]]
            agg[dim] = median(vals)
        agg["n_judges"] = sum(1 for j in entry["judges"] if entry["judges"][j])
        out.append({**entry, "aggregate": agg})
    return out

def overall_stats(per_prompt):
    """Summary across all prompts."""
    dims = ("cultural_authenticity", "persona_consistency", "factual_accuracy")
    stats = {}
    for dim in dims:
        vals = [p["aggregate"][dim] for p in per_prompt if p["aggregate"][dim] is not None]
        if not vals: stats[dim] = {"mean": None, "n": 0}; continue
        stats[dim] = {
            "mean": sum(vals)/len(vals),
            "median": median(vals),
            "n": len(vals),
        }
    # Inter-rater pairwise agreement (mean absolute diff between judges per dim)
    irr = {}
    for dim in dims:
        diffs = []
        for p in per_prompt:
            scores = [p["judges"][j][dim] for j in p["judges"]
                      if p["judges"][j] and dim in p["judges"][j]]
            if len(scores) < 2: continue
            # Mean absolute pairwise diff
            n = len(scores); pairs = 0; total = 0.0
            for i in range(n):
                for k in range(i+1, n):
                    total += abs(scores[i] - scores[k]); pairs += 1
            if pairs: diffs.append(total/pairs)
        irr[dim] = {"mean_pairwise_diff": (sum(diffs)/len(diffs) if diffs else None),
                    "n_with_multi_judge": len(diffs)}
    return {"per_dim": stats, "inter_rater": irr}

# ---------------- Main ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="path to cas_corpus/*.json")
    ap.add_argument("--culture", required=True, choices=list(CULTURE_LABELS.keys()))
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-judge", choices=["gpt5", "claude", "local_qwen27b"],
                    action="append", default=[], help="skip a judge (can repeat)")
    ap.add_argument("--limit", type=int, default=None, help="limit number of prompts (test)")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus))
    gens = corpus["generations"]
    if args.limit: gens = gens[:args.limit]
    label = corpus.get("label", Path(args.corpus).stem)
    culture_label = CULTURE_LABELS[args.culture]

    active_judges = [(name, fn) for name, fn in JUDGES if name not in args.skip_judge]
    print(f"[init] corpus={label} culture={culture_label} prompts={len(gens)} judges={[n for n,_ in active_judges]}")

    t0 = time.time()
    results = []
    for i, g in enumerate(gens):
        prompt_text = JUDGE_PROMPT_TEMPLATE.format(
            culture=culture_label,
            prompt=g["prompt"],
            reply=g["reply"][:800],
        )
        judges_scores = {}
        for j_name, j_fn in active_judges:
            try:
                raw = j_fn(prompt_text)
                judges_scores[j_name] = parse_scores(raw)
            except Exception as e:
                print(f"  [{j_name}] FAIL: {str(e)[:120]}")
                judges_scores[j_name] = None
        results.append({
            "prompt_id": g.get("prompt_id", i),
            "prompt": g["prompt"][:200],
            "judges": judges_scores,
        })
        if (i+1) % 5 == 0:
            print(f"  {i+1}/{len(gens)} ({time.time()-t0:.0f}s)")

    aggregated = aggregate(results)
    stats = overall_stats(aggregated)
    out = {
        "label": label,
        "culture": args.culture,
        "corpus": args.corpus,
        "n_prompts": len(aggregated),
        "active_judges": [n for n, _ in active_judges],
        "per_prompt": aggregated,
        "overall": stats,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"[done] -> {args.out}")
    print(f"  overall: {stats['per_dim']}")
    print(f"  inter-rater pairwise diff: {stats['inter_rater']}")

if __name__ == "__main__":
    main()
    import os as _os; _os._exit(0)
