# R4 — BAS composite scope decision (Tier-3, Sunwoo approved 2026-05-26)

> HANDOFF.md §8 forbids autonomous modification of research questions or
> hypotheses. This document logs Sunwoo's Tier-3 approval of the R4
> mitigation, captured in conversation 2026-05-26.

## Context

`decisions/2026-05-24-known-risks.md` flagged R4 as "the most dangerous"
known risk: MEAS theory's CCR / AAS / GCS behavioral metrics had no
verified mapping to Korean ground-truth data sources (KOSIS, Naver Datalab,
KOFICE).

Brief 01 (`results/hermes_outputs/01_meas_mapping_spec.md`) — produced by
mimo-v2.5-pro 2026-05-24 — confirmed the problem is structural:

- **CCR (Conformity Cascade Rate)**: No KOSIS table measures opinion change
  after exposure to peer/reference-group opinion in the 단톡방-style sense.
- **AAS (Authority Adoption Slope)**: Partial. Naver Datalab data is real;
  the "1.8x lift slope" figure cited in KPI_FRAMEWORK.md is internal
  heuristic with no verified citation.
- **GCS (Group Consensus Speed)**: No published source for "4.2 ± 1.1 rounds
  to consensus". Appears to be internal estimate.

The brief recommended Option 2 (drop BAS composite, keep CCR/AAS/GCS as
directional simulation outputs).

## Decision

**Sunwoo approves Option 2** (conversation 2026-05-26, "권장 방향성으로 가줘"
in response to RESEARCH_PLAN_v2.md decision options + recommendation).

### What changes

1. **MOTIVATION_v2.md Proposition 3** — REPHRASE from:
   - Old: "Static authenticity does not imply behavioral authenticity."
   - New: "Static authenticity does not imply behavioral authenticity.
     Group dynamics under D2C scenarios provide *directional* evidence
     for the persona's behavioral fidelity (CCR / AAS / GCS), reported
     against OASIS-internal baselines rather than against external
     ground truth, because verified Korean ground truth for these
     metrics is not yet established."

2. **KPI_FRAMEWORK.md §3 (Dynamic metrics)** — REPHRASE from:
   - Old: each metric had `Target` against KOSIS/Naver/KOFICE baseline.
   - New: each metric reports *Vanilla → Full-stack delta* against
     OASIS-internal Vanilla baseline. No external ground truth claim.
   - BAS composite formula stays defined for completeness, but is reported
     as exploratory/secondary; the headline H3 metric becomes:
     "delta-CCR + delta-AAS + delta-GCS, each between Vanilla and
     full-stack, paired across same scenario × same seed."

3. **HANDOFF.md §2 H3 hypothesis** — REPHRASE from:
   - Old: "Static authenticity gains correlate (Spearman ρ > 0.6) with
     behavioral authenticity gains measured in OASIS simulations."
   - New: same wording, but "behavioral authenticity" is operationally
     defined as the *delta from Vanilla baseline* in CCR/AAS/GCS, NOT as
     match against external Korean baseline.

4. **Paper Section 4 (Experiments) / Section 5 (Analysis)**:
   - Report static-CAS deltas vs Vanilla
   - Report directional CCR/AAS/GCS deltas vs Vanilla under D2C scenarios
   - Discuss in Section 5 the limitation that absolute behavioral
     calibration against Korean ground truth is future work — and why
     (R4 finding)

5. **DEVIATIONS_FROM_PPT.md** — already updated 2026-05-26 with §7 + §8
   covering MiroFish + KoAlpaca findings; will add §9 noting this R4
   decision and its propagation through MOTIVATION / KPI / HANDOFF.

### What does NOT change

- Six conditions × four backbones factorial — frozen
- 50 D2C scenarios as evaluation substrate — frozen
- Static metrics (CAS, HAD, PDI, JSD) — frozen
- ORBT integration surface (`orbt_research_lab/api.py`) — frozen
- W3 → W8 timeline — frozen

### Why Option 2 (not Option 1 or 3)

- **Option 1** (accept unmapped, synthesize baselines via OASIS pilot)
  is over-engineered: synthesizing a baseline from the same simulator
  whose output we want to evaluate is circular. Reviewers would flag.
- **Option 3** (shelve R4) is dishonest: it papers over a real validity
  gap, and reviewers reading our decision log would find it.
- **Option 2** is defensible: we report what we can measure (deltas),
  explicitly limit our claim ("authenticity *changes* induced by
  cultural grounding"), and label the absolute calibration as future
  work. Standard scientific practice when ground truth is unestablished.

### Risk if reviewer pushes back

If a reviewer asks "but you don't tell us if the Vanilla baseline itself
is a good model of Korean group dynamics" — our answer is:
- (a) cite Vanilla CAS / HAD / PDI / JSD results which document its
  known Western-default failures (Section 4.1, our W3 pilot data
  already collected)
- (b) the *relative improvement* claim is independent of Vanilla's
  absolute fidelity; if Full-stack is 50% more consensus-prone than
  Vanilla under the same scenario, that's a real intervention effect.
- (c) cite OASIS herd-behavior literature (R3 in known risks) as
  acknowledged confound, controlled by paired-seed comparison.

## Approval trail

- Risk flagged: `decisions/2026-05-24-known-risks.md` R4 (2026-05-24)
- Empirical evidence: `results/hermes_outputs/01_meas_mapping_spec.md`
  (Brief 01, mimo-v2.5-pro, 2026-05-24)
- Decision conversation: 2026-05-26, Sunwoo response to
  RESEARCH_PLAN_v2.md option presentation
- Approved by: 주선우 (sunnyxide / 2023320312)
- Implementation: this document + downstream edits to MOTIVATION_v2.md,
  KPI_FRAMEWORK.md, HANDOFF.md (H3 phrasing), DEVIATIONS_FROM_PPT.md

## Next steps

1. Update H3 phrasing in HANDOFF.md (this commit)
2. Update KPI_FRAMEWORK.md §3 (this commit)
3. Update MOTIVATION_v2.md Proposition 3 (this commit)
4. Brief 15 (new): rewrite Section 5 (Analysis) draft incorporating
   directional reporting language
5. PI agent audit — confirm propagation across all canonical files
