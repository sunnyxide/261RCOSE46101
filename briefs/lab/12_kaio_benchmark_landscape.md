# KAIO benchmark literature deep dive

**Origin**: KPI_FRAMEWORK.md and MOTIVATION_v2.md cite "KAIO 2026" as the
hard-Korean benchmark showing GPT-5 at 62.8 and Gemini-2.5-Pro at 52.3,
with Qwen3-235B and DeepSeek-R1 below 30. The bibkey is not in
bibliography.bib yet — Critic will fail any draft that uses "KAIO 2026"
without a proper citation.

**Goal**: produce `results/hermes_outputs/12_kaio_benchmark_landscape.md` — a
literature-grounded brief on KAIO and adjacent recent Korean benchmarks
(2024-2026 publication window), with citations ready to add to
`reports/bibliography.bib`.

---

## Required findings (5-slot format)

### Finding 1 — KAIO 2026 primary source

**Question**: What is the canonical citation for the KAIO benchmark? Who
published it, when, on what venue? Provide bibkey + bibtex entry.

**Output**:
- URL of paper or release (with verbatim quoted sentence per 5-slot Slot 1)
- Score table for major models (GPT-5, Gemini 2.5 Pro, Qwen3, DeepSeek-R1,
  Claude 3.5/4) with citation/source for each (Slot 2)
- Methodology summary: what does KAIO measure, how, with what sample size
- bibkey suggestion (e.g., `kaio2026`) + complete bibtex entry

### Finding 2 — Concurrent Korean benchmarks (2024-2026)

**Question**: What other Korean-language benchmarks have been published
since 2024 that we should cite alongside KAIO? Specifically:
- KoMMLU / KMMLU (Korea-specific MMLU variants)
- HAE-RAE 2.0 if it exists
- 2024-2026 Korean cultural-grounding benchmarks beyond KoBBQ, CLIcK

**Output per benchmark**:
- Paper URL + verbatim quote
- Top model scores
- bibkey suggestion

### Finding 3 — Cross-model error-correlation evidence

**Question**: MOTIVATION_v2.md cites `tao2024pnas` for "cross-model error
correlation ρ > 0.97 on cultural questions". Verify this. If real, exact
citation + correlation figure. If approximation, find the closest real
paper.

### Finding 4 — Korean LLM model releases 2025-2026

**Question**: What Korean-specific LLMs have been released recently that
could serve as additional baselines or as Korean-pretrained judges in our
LLM panel?
- EXAONE (LG AI Research) — current best version, parameter count, access
- HyperCLOVA X (Naver) — API access status, model variants, pricing
- KULLM (NLP/AI Lab) — current version, license
- Polyglot-Ko — current state, parameters

For each: bibkey + verbatim quote about Korean-specific training + access
modality (API / open weights / paywalled).

## Sources to draw on

- arXiv 검색: "Korean LLM benchmark 2024 OR 2025 OR 2026"
- ACL Anthology — Korean track papers
- Naver Hyperclova X 공식 페이지
- LG AI Research blog
- Hugging Face Korean leaderboard

## Output

Markdown with 4 findings (5-slot each), plus a final section titled
"## Bibtex additions for `reports/bibliography.bib`" containing
ready-to-paste bibtex entries.

## Required meta footer

```
[meta]
verifiability_signal: high|medium|low
n_findings: 4
n_bibtex_added: <int>
n_TODO_remaining: <int>
```

## Hard constraints

- If KAIO 2026 cannot be located, do NOT invent. State "BLOCKED:
  no verifiable KAIO 2026 source" and recommend either (a) dropping the
  cite from MOTIVATION_v2.md, or (b) replacing with the closest verifiable
  alternative (CulturalBench, KMMLU).
- Every bibtex entry must have a verifiable URL or DOI. No "to appear" or
  "in preparation" entries.
