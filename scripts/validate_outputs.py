"""Validation pipeline: gpt-5.5 reviews mimo drafts + overall project assessment.

For each mimo draft in reports/drafts_mimo/, ask gpt-5.5:
  1. Factual accuracy check (any claims unsupported by our actual results?)
  2. Citation validity (are referenced papers real and properly cited?)
  3. NeurIPS-template fit (does it match section conventions?)
  4. Tone / academic register / hallucination flag
  5. Concrete revisions needed

Plus an overall project assessment:
  "Is this remarkable enough for COSE461 final + workshop submission?"

Output: reports/validation/<draft_name>_validation.md per file +
        reports/validation/OVERALL_ASSESSMENT.md
"""
import json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "reports" / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_CONTEXT = """
This is a COSE461 NLP final project (Korea University, Spring 2026). Team 8 토큰해적단.

The project: Cultural-QLoRA fine-tuning of Qwen2.5-3B/7B with Hofstede-6D system-prompt conditioning, on cultural training data (CultureBank country-filtered + Nemotron-Personas-Korea). 4 per-culture adapters (KR/JP/US/CN) + 1 multi-cultural + 1 KR-7B. Eval: KoBBQ, KMMLU, HAE-RAE, CLIcK (in-distribution) + GlobalOpinionQA KS test + BLEnD MCQ (cross-cultural). Plus Hofstede dimension ablation (IDV-only / UAI-only / all-6D).

CONCRETE RESULTS WE HAVE (verified from results/benchmarks/):
- Phase 1 Korean baselines (5 models × 7 benchmarks): Vanilla-3B-Qwen, Run-A/B-KoAlpaca, Vanilla-7B-Qwen, Run-D-7B+KoAlpaca, with KoBBQ corr/bias, KMMLU, HAE-RAE, CLIcK
- 4 cultural adapter in-distribution scores (KoBBQ + KMMLU on each)
- CAS 3-judge panel (gpt-5.5 + claude-opus-4.7 + mimo-v2.5-pro):
    Cultural-CN: auth=3.10, consis=4.10, factual=3.49
    Cultural-KR: auth=2.86, consis=3.75, factual=2.86
    Cultural-US: auth=2.05, consis=3.55, factual=3.25
    Cultural-JP: auth=1.64, consis=2.68, factual=1.96
- Run-J-KR-7B persona corpus + scored CAS
- Cross-cultural KS + BLEnD: STILL RUNNING on AWS at submission time

KNOWN GAPS:
- Cross-cultural KS results being generated NOW (started 5/29)
- Hofstede ablation: 2 of 3 variants trained, eval not yet aggregated
- No human evaluation
- Single seed per run
- Limited model size (3B/7B)

DEADLINE: GitHub URL Google Form 2026-06-02 (4 days). PDF BlackBoard end of W8.
TEMPLATE: NeurIPS 2020, 8 page MAX (excl. references), sections required:
Abstract <300w / 1.Introduction / 2.Related Work / 3.Approach / 4.Experiments
(Data/Eval/Details/Results) / 5.Analysis (qualitative) / 6.Conclusion /
References (unsrt) / Appendix A Team contributions.
"""

REVIEW_PROMPT = """You are a senior NLP research reviewer evaluating a draft section for a Korea University COSE461 NLP final-project paper.

PROJECT CONTEXT:
{context}

DRAFT SECTION (file: {fname}):
---
{content}
---

Provide a structured review covering:

## 1. Hallucination check
List any factual claims, citations, or numerical statements in the draft that are NOT supported by the project context. Flag invented papers, false numbers, made-up methodology.

## 2. NeurIPS-template fit
Does the section match its template-required role (e.g., Section 4 has 4 subsections Data/Eval/Details/Results)? Note any structural problems.

## 3. Academic tone & register
Is it dense and technical (NeurIPS-style) or marketing/inflated? Specific examples.

## 4. Concrete revisions needed
3-5 actionable changes for the team to apply before submission.

## 5. Overall quality
Rate 1-5 (5 = ready as-is, 1 = needs major rewrite). One sentence.

Output as plain markdown. Be honest — flag weak spots. Do not be flattering.
"""

OVERALL_PROMPT = """You are evaluating whether a Korea University COSE461 NLP final-project is "remarkable" enough to:
(a) earn a strong grade in the course
(b) present publicly (e.g., team presentation)
(c) potentially be developed into a workshop submission (ACL/EACL/COLING)

PROJECT CONTEXT:
{context}

KEY ARTIFACTS we have produced:
- 6 cultural QLoRA adapters trained on Qwen2.5-3B / 7B
- CAS 3-judge LLM panel scoring of persona corpora across 4 cultures
- KoBBQ/KMMLU/HAE-RAE/CLIcK benchmark numbers for 5 baselines + 4 cultural adapters
- 20 paper section drafts (some need editing)
- Public GitHub repo with reproducibility scripts + decision log + AI-usage disclosure
- Cross-cultural KS being generated NOW; results expected within hours

Answer concisely:

## Course grading viability (COSE461)
Will this pass / get strong grade? What's the floor and ceiling?

## Presentation viability
Is the story clear and compelling? What's the strongest single finding to lead with?

## Workshop submission viability
What would a typical EACL/COLING reviewer flag as the strongest contribution? What's the weakest link that would block acceptance?

## Top-3 critical revisions (in priority order)
What should the team finish in the remaining 4 days before deadline?

## Bottom line
Single sentence: is this submission-ready right now, with completion of in-flight work, or is the story fundamentally too thin?

Be honest, not flattering. Specific.
"""

def call_gpt55(prompt, max_tokens=2500):
    from openai import OpenAI
    c = OpenAI()
    r = c.chat.completions.create(
        model="gpt-5.5",
        max_completion_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        reasoning_effort="medium",
    )
    return r.choices[0].message.content or ""

def review_draft(path):
    fname = path.name
    out_path = OUT_DIR / f"{path.stem}_validation.md"
    if out_path.exists() and out_path.stat().st_size > 500:
        print(f"[skip] {fname} (already reviewed)")
        return
    content = path.read_text()
    if len(content) > 12000:
        content = content[:12000] + "\n[... truncated ...]"
    prompt = REVIEW_PROMPT.format(context=PROJECT_CONTEXT, fname=fname, content=content)
    print(f"[review] {fname}")
    t0 = time.time()
    review = call_gpt55(prompt)
    out_path.write_text(f"# Validation review — {fname}\n\n_Reviewer: gpt-5.5, elapsed={time.time()-t0:.0f}s_\n\n{review}\n")
    print(f"  -> {out_path.name} ({len(review)} chars)")

def main():
    # Review each mimo draft
    drafts = sorted((ROOT / "reports/drafts_mimo").glob("*_draft_mimo.md"))
    print(f"[start] reviewing {len(drafts)} mimo drafts")
    for d in drafts:
        try:
            review_draft(d)
        except Exception as e:
            print(f"  [FAIL] {d.name}: {str(e)[:200]}")

    # Overall assessment
    print("[start] overall assessment")
    out_path = OUT_DIR / "OVERALL_ASSESSMENT.md"
    overall_prompt = OVERALL_PROMPT.format(context=PROJECT_CONTEXT)
    overall = call_gpt55(overall_prompt, max_tokens=3000)
    out_path.write_text(f"# Overall project assessment\n\n_Reviewer: gpt-5.5 (reasoning_effort=medium)_\n\n{overall}\n")
    print(f"  -> {out_path}")

if __name__ == "__main__":
    main()
    import os as _os; _os._exit(0)
