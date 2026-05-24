# MEAS ↔ Korean ground-truth mapping spec (R4 risk mitigation)

**Origin**: `decisions/2026-05-24-known-risks.md` flagged R4 as the most dangerous
risk — "MEAS theory ↔ ground-truth data mapping is unspecified". Without this
spec, `agents/analyst.py` computes CCR/AAS/GCS with no defensible denominator,
and the paper has a critique-fatal gap when reviewers ask "how do you know
your CCR estimate corresponds to real Korean consumer conformity?"

**Goal**: produce `data/spec/meas_mapping.yaml` — a concrete, source-cited
mapping from each MEAS-theory behavioral metric (CCR, AAS, GCS) to the Korean
ground-truth data series we will use as the denominator. For each metric:
(a) which series, (b) what time window, (c) what cohort decomposition, (d) the
mapping function, (e) known limitations.

**Decisions affected**:
- `agents/analyst.py` behavioral-metric computation logic (W3 sub-task)
- KPI_FRAMEWORK.md "Dynamic / behavioral metrics" section (BAS family)
- W6 OASIS simulation scoring (compares sim CCR/AAS/GCS to ground truth)
- Paper Methods subsection on dynamic-metric validity

**Why now**: blocks W3 analyst work. PI agent has authority to flag any
analyst output that cites these metrics without referencing this spec.

---

## Required findings (each in 5-slot format per research_v2)

### Finding 1 — CCR (Conformity Cascade Rate)

**Question**: What Korean macro/micro data series can serve as the
behavioral-truth denominator for CCR (the fraction of agents who change
opinion after exposure to majority view in 단톡방-style settings)?

Specifically:
- Is there a KOSIS table that measures opinion change after exposure to peer/
  reference-group opinion? (e.g., consumer behavior surveys, household
  decision-making panels)
- Naver Datalab search-pattern data: how do trending-topic adoption curves
  decompose by demographic cohort? Can we extract a "conformity-after-exposure"
  proxy from search-term diffusion timing?
- KOFICE Hallyu White Paper: cross-influence patterns between groups
  (단톡방, 인플루언서 추천, 가족/지인 추천) and conversion — is there a
  per-cohort baseline we can cite?

**Output for each candidate source**:
- Exact series ID / table number
- Verbatim sentence from official documentation (5-slot Slot 1)
- Quantitative measure: what is the baseline CCR estimate for Korean adults?
  (5-slot Slot 2)
- Limitation: where does this data fail to capture what OASIS simulates? (Slot 5)

### Finding 2 — AAS (Authority Adoption Slope)

**Question**: What measures the slope of adoption after a celebrity/influencer
endorsement event in Korea? The KPI framework cites "Naver-Datalab-measured
1.8x lift slope" — verify, find the specific series, document the methodology.

**Verify**:
- Is the 1.8x figure published officially, or is it our heuristic? If heuristic,
  what is the proper denominator we should cite instead?
- Naver Datalab provides search-volume time series; can we extract
  endorsement-driven slopes from public dashboards (e.g., specific brand-name
  spike correlation with celebrity endorsement announcement dates)?
- KCA (Korea Consumer Agency) complaint patterns post-endorsement-fraud: does
  this give us a slope-down corollary?

### Finding 3 — GCS (Group Consensus Speed)

**Question**: What is the empirically-grounded "Korean baseline of 4.2 ± 1.1
rounds to consensus" the KPI framework cites? Verify or replace.

**Verify**:
- Is 4.2 ± 1.1 from a published Korean group-decision study? If so, citation
  and methodology.
- If our own estimate, what experimental design would actually measure GCS in
  a 단톡방-style chat (length to lock-in, message count to convergence,
  cross-cohort variance)?
- KOFICE or Communication-Korea journal data on K-group decision dynamics.

### Finding 4 — BAS composite

**Question**: The BAS = 0.4·(1-|CCR_delta|) + 0.3·(1-|AAS_delta|) +
0.3·(1-|GCS_delta|) weighting is heuristic. Defend or revise.

**Required**:
- Reference Korean cultural-psychology work (Hofstede 6D Korea: IDV=18, LTO=100,
  UAI=85) for principled weighting argument
- Sensitivity: how does the composite shift if weights move to 0.5/0.3/0.2 vs
  0.3/0.4/0.3 vs equal? Suggest a defensible default with rationale.

---

## Output format

Write `data/spec/meas_mapping.yaml` with structure:

```yaml
ccr:
  series:
    - id: <KOSIS table id or Naver Datalab series>
      verbatim: "<sentence from docs>"
      cohort_decomposition: <how we slice>
      baseline_value: <number ± stddev>
      limitations: <text>
  mapping_function: |
    <python-like pseudocode mapping OASIS sim output to this baseline>
  known_limitations:
    - <limitation 1>
    - <limitation 2>

aas: { ... }
gcs: { ... }

bas_composite:
  default_weights: { ccr: 0.4, aas: 0.3, gcs: 0.3 }
  rationale: |
    <Korean cultural-psychology argument from Hofstede / Triandis / others>
  sensitivity_table: |
    <text table showing BAS under different weights>
```

Plus a markdown summary at top explaining each choice.

**Required meta footer** at bottom (line-anchored):

```
[meta]
verifiability_signal: high|medium|low
n_findings: 4
known_unknowns:
  - <list of things we couldn't verify>
```

---

## Failure modes to address

1. Some Korean series may be paywalled or PDF-only. Document this honestly —
   if a series is inaccessible, mark `accessibility: paywalled` and note the
   citation.
2. Korean cultural metrics are often not directly comparable to Western
   social-psych concepts. If a mapping requires translation/transformation,
   document it explicitly rather than papering over the gap.
3. The PI agent will reject this spec if any metric cites a data series
   without a verbatim quote AND a concrete cohort decomposition.

If you cannot find a defensible series for one of CCR/AAS/GCS, output
`status: unmapped` for that metric and recommend either (a) dropping it from
the BAS composite or (b) running a pilot study to generate our own baseline.
