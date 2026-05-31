"""Build a blind native-speaker rating kit for Korean persona authenticity (paper §CAS / weakness: no human eval).

Samples 20 prompts shared across Vanilla-3B, Cultural-KR-3B, Cultural-KR-7B,
presents the three replies per prompt in a randomized blind order (A/B/C), and
writes:
  reports/human_eval/rating_sheet.md   <- give to a native Korean speaker
  reports/human_eval/blind_key.json    <- hidden mapping (do NOT look while rating)
The rater scores each reply 1-5 on cultural authenticity. Then
scripts/score_human_eval.py de-blinds and correlates with the LLM-judge CAS.
"""
import json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "results/cas_corpus"
OUT = ROOT / "reports/human_eval"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 461  # fixed for reproducible blinding
N = 20

MODELS = {
    "vanilla-3b_kr": "Vanilla-3B",
    "cultural-kr_kr": "Cultural-KR-3B",
    "cultural-kr-7b_kr": "Cultural-KR-7B",
}

def load(f):
    d = json.load(open(SRC / f"{f}.json"))
    return {g["prompt_id"]: g for g in d["generations"]}

gens = {m: load(m) for m in MODELS}
common = sorted(set.intersection(*[set(g.keys()) for g in gens.values()]))
rng = random.Random(SEED)
chosen = rng.sample(common, min(N, len(common)))

key = {}
lines = ["# Korean Persona Authenticity — Blind Rating Sheet",
         "",
         "For each prompt, three model replies are shown in random order (A/B/C).",
         "Rate **cultural authenticity** 1-5 (1 = generic/foreign-sounding, 5 = authentically Korean).",
         "Write your score next to each. Do not open blind_key.json until done.",
         ""]
for i, pid in enumerate(chosen, 1):
    prompt = gens["vanilla-3b_kr"][pid]["prompt"]
    slots = list(MODELS.keys())
    rng.shuffle(slots)
    key[str(pid)] = {lab: MODELS[m] for lab, m in zip("ABC", slots)}
    lines.append(f"## {i}. (prompt_id {pid})")
    lines.append(f"**Prompt:** {prompt}")
    lines.append("")
    for lab, m in zip("ABC", slots):
        reply = gens[m][pid]["reply"].strip().replace("\n", " ")
        if len(reply) > 600:
            reply = reply[:600] + " […]"
        lines.append(f"- **{lab}.** {reply}")
        lines.append(f"  - score (1-5): ____")
    lines.append("")

(OUT / "rating_sheet.md").write_text("\n".join(lines), encoding="utf-8")
json.dump(key, open(OUT / "blind_key.json", "w"), ensure_ascii=False, indent=2)
print(f"wrote {OUT/'rating_sheet.md'} ({len(chosen)} prompts) + blind_key.json")
