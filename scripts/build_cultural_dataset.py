"""Build cultural-grounded instruction dataset for Cultural-QLoRA training.

Per culture C ∈ {kr, jp, us, cn}, combines:
  1. CultureBank descriptors (cultural facts/practices)
  2. Hofstede 6D as system-prompt conditioning
  3. WVS Wave 7 country responses (used as gold labels for some examples)
  4. Nemotron-Personas (KR variant for kr; synthesized for others using Hofstede-conditioned demo)
  5. (optional) BBQ-family training split for bias mitigation

Outputs:
  data/cultural/{culture}/train.jsonl   — Alpaca-style records
  data/cultural/{culture}/eval.jsonl    — held-out for WVS distribution check
  data/cultural/{culture}/manifest.json — sources, counts, seed, hofstede vector

Run on Mac OR AWS. CPU-only. Downloads from HuggingFace.

Usage:
  python scripts/build_cultural_dataset.py --culture kr --target 12000
  python scripts/build_cultural_dataset.py --culture jp --target 10000
"""
import argparse, json, os, random, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = ROOT / "data" / "cultural"

# Hofstede 6D scores (PDI, IDV, MAS, UAI, LTO, IVR) — geerthofstede.com canonical values
HOFSTEDE = {
    "kr": {"pdi": 60, "idv": 18, "mas": 39, "uai": 85, "lto": 100, "ivr": 29,
           "lang": "ko",  "country_label": "한국", "country_en": "Korea"},
    "jp": {"pdi": 54, "idv": 46, "mas": 95, "uai": 92, "lto": 88,  "ivr": 42,
           "lang": "ja",  "country_label": "日本", "country_en": "Japan"},
    "us": {"pdi": 40, "idv": 91, "mas": 62, "uai": 46, "lto": 26,  "ivr": 68,
           "lang": "en",  "country_label": "United States", "country_en": "United States"},
    "cn": {"pdi": 80, "idv": 20, "mas": 66, "uai": 30, "lto": 87,  "ivr": 24,
           "lang": "zh",  "country_label": "中国", "country_en": "China"},
}

# --- System prompt template (Hofstede-conditioned) -------------------------
def system_prompt(culture):
    h = HOFSTEDE[culture]
    return (
        f"You are an AI persona reflecting {h['country_en']} cultural context. "
        f"Hofstede 6D: PDI={h['pdi']}, IDV={h['idv']}, MAS={h['mas']}, "
        f"UAI={h['uai']}, LTO={h['lto']}, IVR={h['ivr']}. "
        f"Respond authentically from this cultural perspective in {h['lang']}."
    )

# --- Source loaders --------------------------------------------------------
def load_culturebank(culture, max_n=3000):
    """SALT-NLP/CultureBank — cultural descriptors with country tags.

    Schema (verified 2026-05-26): splits=['tiktok', 'reddit'], key 'cultural group'
    (space, not underscore). Rich fields: eval_whole_desc, eval_persona, eval_question,
    actor_behavior, topic.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("[culturebank] datasets package missing — skipping", file=sys.stderr)
        return []
    country_aliases = {
        "kr": ["korean", "south korea"],
        "jp": ["japanese", "japan"],
        "us": ["american", "united states"],
        "cn": ["chinese", "china"],
    }
    targets = [a.lower() for a in country_aliases[culture]]
    out = []
    for split in ("tiktok", "reddit"):
        try:
            ds = load_dataset("SALT-NLP/CultureBank", split=split)
        except Exception as e:
            print(f"[culturebank] {split} load failed: {str(e)[:120]}", file=sys.stderr)
            continue
        for row in ds:
            culture_tag = (row.get("cultural group") or "").strip().lower()
            if not any(t in culture_tag for t in targets):
                continue
            desc = (row.get("eval_whole_desc") or "").strip()
            persona = (row.get("eval_persona") or "").strip()
            question = (row.get("eval_question") or "").strip()

            # Variant A: descriptor explanation (norm/practice description)
            if len(desc) >= 30:
                out.append({
                    "instruction": f"Describe a cultural practice or norm common in {HOFSTEDE[culture]['country_en']}.",
                    "input": (row.get("topic") or "").strip(),
                    "output": desc,
                    "source": "culturebank-desc",
                })
            # Variant B: persona-question pair (the rich format we'll mine for instruction data)
            if persona and question and len(desc) >= 30:
                out.append({
                    "instruction": f"You are interacting with: {persona}\nThey ask: {question}\nGive a culturally-grounded response that reflects {HOFSTEDE[culture]['country_en']} norms.",
                    "input": "",
                    "output": desc,
                    "source": "culturebank-persona",
                })
            if len(out) >= max_n:
                return out
    return out

def load_wvs_responses(culture, max_n=2000):
    """WVS Wave 7 — country responses as gold labels for cultural-value questions.

    Expects local CSV at data/wvs/wvs7_{culture}.csv with columns:
      question_text, answer_text, response_count
    (Hermes brief 07 produces this from official WVS dump.)
    """
    path = ROOT / "data" / "wvs" / f"wvs7_{culture}.csv"
    if not path.exists():
        print(f"[wvs] {path} not present — Hermes brief 07 will produce it", file=sys.stderr)
        return []
    import csv
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            q = (r.get("question_text") or "").strip()
            a = (r.get("answer_text") or "").strip()
            if not q or not a:
                continue
            rows.append({
                "instruction": q,
                "input": "",
                "output": a,
                "source": "wvs7",
            })
            if len(rows) >= max_n:
                break
    return rows

def load_nemotron_personas(culture, max_n=3000):
    """Nemotron-Personas-Korea — KR only. Rich multi-facet personas in Korean.

    Verified schema: persona, professional_persona, family_persona, cultural_background,
    age, sex, district, province, occupation, education_level.
    Strategy: emit multiple instruction variants per row (persona summary, professional
    detail, cultural background) → high cultural-signal data points.
    """
    if culture != "kr":
        return []
    try:
        from datasets import load_dataset
    except ImportError:
        return []
    try:
        ds = load_dataset("nvidia/Nemotron-Personas-Korea", split="train", streaming=True)
    except Exception as e:
        print(f"[nemotron] load failed: {e}", file=sys.stderr)
        return []
    out = []
    for row in ds:
        persona = (row.get("persona") or "").strip()
        bg = (row.get("cultural_background") or "").strip()
        prof = (row.get("professional_persona") or "").strip()
        fam = (row.get("family_persona") or "").strip()
        age = row.get("age"); sex = row.get("sex"); occ = row.get("occupation")
        prov = row.get("province"); district = row.get("district")
        if len(persona) < 30:
            continue
        seed = f"{age}세 {sex}, {prov} {district}, 직업: {occ}".strip()
        # Variant A: short persona summary
        out.append({
            "instruction": "다음 인물 정보를 바탕으로 한국인 페르소나를 상세히 묘사하세요.",
            "input": seed,
            "output": persona,
            "source": "nemotron-persona-summary",
        })
        # Variant B: cultural background expansion
        if len(bg) >= 50:
            out.append({
                "instruction": "이 한국인의 문화적 배경과 가치관을 설명하세요.",
                "input": persona,
                "output": bg,
                "source": "nemotron-cultural-bg",
            })
        # Variant C: lifestyle facet (rotate professional/family for diversity)
        facet = prof if (hash(row.get("uuid","")) % 2 == 0 and len(prof) >= 50) else fam
        if len(facet) >= 50:
            facet_q = "이 한국인의 직업적 일상을 묘사하세요." if facet == prof else "이 한국인의 가족 관계를 묘사하세요."
            out.append({
                "instruction": facet_q,
                "input": persona,
                "output": facet,
                "source": "nemotron-lifestyle",
            })
        if len(out) >= max_n:
            break
    return out

def load_kobbq_train(culture, max_n=1500):
    """KoBBQ has eval-only ('test') split — using it for training would leak.

    Returns []. Bias mitigation training is delegated to Hermes brief 09
    (synthesize bias-aware demonstrations) or to general Korean instruction
    mixing via KoAlpaca-style data later. Function kept for interface parity.
    """
    return []

# --- Combine and format ----------------------------------------------------
def format_as_instruction(records, culture):
    """Wrap each record with system prompt + Alpaca-style chat format."""
    sys_p = system_prompt(culture)
    out = []
    for r in records:
        out.append({
            "system": sys_p,
            "instruction": r["instruction"],
            "input": r.get("input", ""),
            "output": r["output"],
            "culture": culture,
            "source": r.get("source", "unknown"),
            "hofstede": HOFSTEDE[culture],
        })
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--culture", required=True, choices=list(HOFSTEDE.keys()))
    ap.add_argument("--target", type=int, default=12000, help="target training examples")
    ap.add_argument("--eval-frac", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    culture = args.culture
    out_dir = OUT_ROOT / culture
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[build] culture={culture} target={args.target}")
    t0 = time.time()

    # Per-source budgets (auto-scaled by target). KoBBQ removed (eval-only split, leakage).
    # Nemotron generates 3 variants per row so 30% target gives ~ that many rows × 3.
    budgets = {
        "culturebank": int(args.target * 0.30),
        "wvs":         int(args.target * 0.15),
        "nemotron":    int(args.target * 0.40),
        "kobbq":       0,  # leakage guard; Hermes brief 09 fills bias-mitigation slot synthetically
    }

    sources = []
    sources += load_culturebank(culture, budgets["culturebank"])
    print(f"[build] culturebank → {len(sources)} cumulative")
    sources += load_wvs_responses(culture, budgets["wvs"])
    print(f"[build] +wvs → {len(sources)} cumulative")
    sources += load_nemotron_personas(culture, budgets["nemotron"])
    print(f"[build] +nemotron → {len(sources)} cumulative")
    sources += load_kobbq_train(culture, budgets["kobbq"])
    print(f"[build] +kobbq → {len(sources)} cumulative")

    if not sources:
        print(f"[build] FATAL: no data loaded for {culture}. "
              f"Check that datasets pkg is installed and HF reachable.", file=sys.stderr)
        sys.exit(2)

    formatted = format_as_instruction(sources, culture)
    random.shuffle(formatted)

    n_eval = max(50, int(len(formatted) * args.eval_frac))
    eval_set = formatted[:n_eval]
    train_set = formatted[n_eval:]

    train_path = out_dir / "train.jsonl"
    eval_path = out_dir / "eval.jsonl"
    with open(train_path, "w", encoding="utf-8") as f:
        for r in train_set:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(eval_path, "w", encoding="utf-8") as f:
        for r in eval_set:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    manifest = {
        "culture": culture,
        "hofstede": HOFSTEDE[culture],
        "target": args.target,
        "actual_total": len(formatted),
        "train_count": len(train_set),
        "eval_count": len(eval_set),
        "source_counts": {
            k: sum(1 for r in formatted if r["source"].startswith(k.replace("nemotron", "nemotron-")))
            for k in budgets
        },
        "seed": args.seed,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_sec": round(time.time() - t0, 1),
    }
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[build] DONE culture={culture} train={len(train_set)} eval={len(eval_set)} "
          f"path={out_dir} elapsed={manifest['elapsed_sec']}s")

if __name__ == "__main__":
    main()
