# Known risks — log for PI agent and weekly Sunwoo review

Date: 2026-05-24
Author: Claude (with Sunwoo critic-mode review)
Status: active — re-evaluated weekly, items move to `resolved/` when retired

These are risks identified BEFORE the lab boots, captured here so the
Principal Investigator agent reads them on every daily audit and Sunwoo
sees them at every Friday review. None blocks lab startup. All have a
named mitigation tied to a specific week.

---

## R1 — Loop A self-check cost estimate is optimistic

**Claim under review.** `SELF_EVAL_LOOP.md` estimates Loop A (per-task
self-check) at $1-3 total over 8 weeks. The estimate assumes ~500 tasks
× ~$0.003/check × 1 self-check per task.

**Why it may be wrong.** When Loop A flags an issue (`submit=false`), the
agent enqueues a correction task. That correction also runs Loop A. If
correction rate is 15-20% (plausible for first-week tasks), realized cost
is 2-3× the headline figure. Plus self-correction tasks themselves can
fail self-check, creating a small but real recursive cost component.

**Why we accept the risk.** The expected blowup is bounded — even at 3× we
are at $9, well under the $400 envelope. `budget.py`'s daily cap ($30)
absorbs it without intervention.

**Mitigation / when re-evaluated.**
- W2 Friday: read first-week Loop A actuals from `costs` table. If the
  per-tick cost is >2× projection, demote Loop A to high-confidence
  agents only (writer, critic) and drop it from data_steward + librarian
  (low-ambiguity workflows).
- PI agent daily audit: includes a `loop_a_cost_ratio` metric.

**Reversal cost.** Free — config flag in `agents.yaml`.

---

## R2 — PI agent only catches abrupt hypothesis drift, not incremental

**Claim under review.** `prompts/principal_investigator.md` and the agent
itself perform a 24-hour-window audit. The PI is supposed to catch when
the work is no longer answering RQ1/RQ2/RQ3.

**Why it may be wrong.** Drift in research practice is usually subtle and
multi-step. A 24h window will catch a sudden topic change ("started
evaluating model on Japanese personas") but will miss slow erosion ("over
two weeks, condition C5 quietly accumulated scenario-engineering tweaks
that target H1 directly"). Incremental drift requires a 7-day diff-based
window and an embedding comparison of last-week task outputs vs this
week's — that costs significant tokens at every audit.

**Why we accept the risk.** Cost of comprehensive drift detection at this
project's scale is prohibitive ($2-5/day for embedding the whole task log
nightly) for a 1-in-N safety check. The detection gap is real but
Sunwoo's Friday review at the level of "are we still answering RQ1?" is
the actual safety net. The PI agent is insurance against between-Friday
catastrophes.

**Mitigation / when re-evaluated.**
- Every Friday, Sunwoo reads PI's weekly summary and the actual RQ-vs-
  output mapping. If the mapping has shifted, log the decision in
  `decisions/`.
- W4 Friday: if PI audits to date have caught nothing AND Sunwoo finds
  drift unaided, switch PI to a 3-day window with a content-diff prompt.

**Reversal cost.** Low — extending PI window is one prompt edit.

---

## R3 — OASIS herd-behavior confounds BAS measurement

**Claim under review.** Dynamic authenticity (BAS = CCR ⊕ AAS ⊕ GCS) is
measured by running personas through OASIS social-network simulations.
OASIS has well-documented herd-behavior tendencies — agents inside an
OASIS sim conform to majority opinion at rates higher than real
populations. The plan controls for this with a relative-to-Vanilla delta.

**Why it may be wrong.** If herd bias is *differentially* expressed across
conditions — e.g., full-stack personas (richer profile, more context)
amplify herd more than Vanilla personas — then the Vanilla delta is
itself contaminated. Conditional inflation of the dependent variable
breaks the natural-experiment intuition we are relying on.

**Why we accept the risk.** Eliminating OASIS herd bias is out of scope.
The honest defense is variance reporting: if delta-BAS is robust across
random seeds, we can argue the herd effect is shared and the delta is
meaningful.

**Mitigation / when re-evaluated.**
- W5 W6: every BAS run uses 5 seeds. Report std as part of the metric.
  If σ across seeds exceeds 0.10 the result is treated as preliminary
  pending more seeds.
- W6 ablation: include a "herd-only" condition (random profile, full
  context) to estimate the herd contribution directly.
- If σ remains high after 10 seeds, BAS is downgraded to "exploratory"
  in the paper and HAD/CAS carry the headline claim.

**Reversal cost.** Compute — extra seeds are cheap if local; AWS hours
add up if we're already past budget.

---

## R4 — MEAS theory ↔ ground-truth data mapping is unspecified

**Claim under review.** Behavioral metrics CCR/AAS/GCS are defined
relative to MEAS (Multi-dimensional Engagement-Authenticity-Sociality)
theory. Ground truth comes from three sources: KOSIS (Statistics Korea
macro indicators), Naver Datalab (search-pattern micro behavior), KOFICE
(Hallyu / cultural influence indicators). The mapping from "what MEAS
theory predicts" to "what these data series measure" is not written down
anywhere. Without it, analyst.py is computing metrics with no defensible
denominator.

**Why this is the most dangerous item on this list.** R1-R3 affect
robustness or cost. R4 affects validity — without the mapping spec, the
paper has a critique-fatal gap: "how do you know your CCR estimate
corresponds to real Korean consumer conformity?" We can't answer that
post-hoc.

**Mitigation / when re-evaluated.**
- W2 Monday: explicit sub-task `meas_to_ground_truth_mapping` in seed
  queue, owned by data_steward + analyst jointly. Output is
  `data/spec/meas_mapping.yaml` — for each of CCR / AAS / GCS, list
  (a) what KOSIS / Naver / KOFICE series we use, (b) what time window,
  (c) what cohort decomposition, (d) what is the mapping function, and
  (e) what the known limitations are.
- W3 Friday: PI agent has authority to flag any analyst output that
  cites these metrics without referencing meas_mapping.yaml — that
  output is blocked from commit.

**Reversal cost.** None — this is purely additive specification work.

---

## How the PI agent uses this file

`prompts/principal_investigator.md` loads this file on every daily audit.
The PI must:

1. Confirm none of R1-R4 has been silently ignored — i.e., for each
   risk, check that the named mitigation owner has either touched the
   relevant file this week or filed a status note.
2. If a risk's "when re-evaluated" date has passed without action,
   escalate severity to orange and add an item to next QA Meta cycle.
3. Quote the risk ID (R1/R2/R3/R4) explicitly in the daily audit YAML so
   downstream tooling can grep.

Sunwoo's Friday review must address each risk's status explicitly. Items
move to a `resolved/` subdirectory only after PI agent confirms the
mitigation produced an artifact (e.g., R4 → `data/spec/meas_mapping.yaml`
exists and is non-empty).
