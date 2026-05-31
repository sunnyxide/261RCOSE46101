"""Temperature-sampling metric-sensitivity analysis (paper §5.6 / Table tab:temp).

For the temperature-0.7 re-eval cells, reports per cell: bootstrap mean KS,
mean output entropy of the sampled distribution, gold entropy, and an
entropy-independent mode-match accuracy (model's most-sampled option ==
gold's top option). Shows the KS advantage tracks output entropy, while
mode-match (entropy-free) is only directional.

Run after syncing results/benchmarks/temp_sampling/.
"""
import json, os, math, random

N_BOOT = 10000
SRC = "results/benchmarks/temp_sampling"
CELLS = [("vanilla-3b", "kr"), ("vanilla-7b", "kr"),
         ("run-f-kr", "kr"), ("run-j-kr-7b", "kr"),
         ("vanilla-3b", "us"), ("run-h-us", "us")]

def entropy(dist):
    s = sum(dist)
    if s <= 0:
        return 0.0
    return -sum((x/s) * math.log2(x/s) for x in dist if x > 0)

def boot(vals, seed=42):
    rng = random.Random(seed); n = len(vals)
    ms = sorted(sum(vals[rng.randrange(n)] for _ in range(n)) / n for _ in range(N_BOOT))
    return sum(vals)/n, ms[int(.025*N_BOOT)], ms[int(.975*N_BOOT)]

def analyze(label, culture):
    p = os.path.join(SRC, f"cross_cultural_{label}_{culture}_FULL.json".replace("_FULL", "_TEMP"))
    if not os.path.exists(p):
        return None
    pq = json.load(open(p))["global_opinion"]["per_question"]
    ks, me, ge, mode = [], [], [], []
    for q in pq:
        pred, gold = q.get("pred"), q.get("gold")
        if not pred or not gold:
            continue
        ks.append(q["ks"]); me.append(entropy(pred)); ge.append(entropy(gold))
        mode.append(1.0 if pred.index(max(pred)) == gold.index(max(gold)) else 0.0)
    n = len(ks)
    ks_m, ks_lo, ks_hi = boot(ks)
    md_m, md_lo, md_hi = boot(mode)
    return dict(n=n, ks=ks_m, ks_ci=(ks_lo, ks_hi), model_H=sum(me)/n,
                gold_H=sum(ge)/n, mode_acc=md_m, mode_ci=(md_lo, md_hi))

if __name__ == "__main__":
    print(f"{'cell':18s} {'KS [95% CI]':>22s} {'H_model':>8s} {'H_gold':>7s} {'mode-acc [95% CI]':>22s}")
    for lab, c in CELLS:
        r = analyze(lab, c)
        if not r:
            continue
        ks = f"{r['ks']:.3f} [{r['ks_ci'][0]:.3f},{r['ks_ci'][1]:.3f}]"
        md = f"{r['mode_acc']:.3f} [{r['mode_ci'][0]:.3f},{r['mode_ci'][1]:.3f}]"
        print(f"{lab+'@'+c:18s} {ks:>22s} {r['model_H']:8.3f} {r['gold_H']:7.3f} {md:>22s}")
