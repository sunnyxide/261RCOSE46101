# Deviations from the Token Pirates project proposal

> The original proposal (`Team Token Pirates Project Proposal Presentation.pptx`)
> defined a Korea+Japan, 5-condition, GPT-4o-mini study with static metrics.
> The current plan extends it across six dimensions. Each deviation is
> documented here with rationale and impact. The Writer agent pulls from
> this file to produce the Methods "design evolution" subsection.

## 1. Scope: dropped Japan

| Aspect | Original | v2 |
|--------|----------|----|
| Markets | Korea + Japan | Korea only |
| Cultures per study | 2 | 1 (deep dive) |

**Why.** Behavioral ground truth for Japan is harder to source than for Korea
within the 8-week budget. KOSIS, Naver Datalab, KOFICE, and the Korean
Consumer Agency are all openly accessible and Korean-readable; equivalent
Japanese sources (Statistics Bureau of Japan, Rakuten Insight) require
either purchase or are less granular for our scenarios. Within a fixed
budget, depth on one culture produces a more publishable result than
shallow coverage of two.

**Cost.** Reduced demographic generality of conclusions. Mitigation: explicit
"single-market study" framing in the paper. Future work section explicitly
identifies cross-market replication as the natural extension.

**Risk if reversed.** Japan can be added in W6-W8 as an optional dimension
if Korea results stabilize early and budget allows. Implementation cost is
low because the same six-condition factorial just runs with different
inputs.

## 2. Conditions: 5 → 6

| Aspect | Original | v2 |
|--------|----------|----|
| Conditions | Vanilla, Multilingual, CultureLLM, Anthropological, CultureBank+KG | Vanilla, Hofstede-only, CultureBank+KG, Nemotron-only, Nemotron+Hofstede, Nemotron+CultureBank+KG (full stack) |

**Why.** The original 5 conditions mixed two questions — *cultural conditioning
approach* (Multilingual, CultureLLM, Anthropological, CultureBank+KG) and
*against-baseline measurement* (Vanilla). The redesign isolates two
independent contributions: demographic grounding (Nemotron) and cultural
retrieval (CultureBank+KG), letting us answer "which matters more, and how
much do they compose?".

**Cost.** Drops three baselines from the original (Multilingual,
CultureLLM, Anthropological). We re-add Anthropological-style prompting as
a Hofstede-only condition because it's substantively similar. CultureLLM
and Multilingual are explicitly addressed in related-work as "prior
approaches our retrieval-augmented method subsumes".

**Risk if reversed.** Low. Reviewers would likely accept the v2 design as
cleaner, since it disentangles two confounded factors.

## 3. Models: 1 → 4-5 backbones

| Aspect | Original | v2 |
|--------|----------|----|
| Backbones | GPT-4o-mini only | GPT-4o-mini, GPT-5, Qwen3.6-27B, Gemma 4 26B MoE, +1 optional legacy (Llama-3.1-8B) |
| Generation covariate | No | Yes |

**Why.** RQ2 ("does the effect persist across model generations?") is
defensible only if multiple generations are sampled. With a single closed-
source API model, reviewers can dismiss findings as "GPT-4o-mini-specific".
Adding open-weight SOTA (Qwen3.6, Gemma 4), a closed-source ceiling
(GPT-5), and an optional legacy anchor (Llama-3.1-8B) covers the
"scaling solves culture" critique directly.

**Cost.** Compute and API spend roughly double. AWS credits ($391.68
across two accounts) absorb the GPU portion. API spend stays bounded by
using GPT-4o-mini for bulk persona generation and reserving GPT-5 calls
for the Critic agent and a small "ceiling sanity check" run.

**Risk if reversed.** None — model registry is configuration in
`config/models.yaml`. If W4 budget burn projects > $300, the legacy
backbone is dropped first (decision logged automatically by QA Meta).

## 4. Evaluation: static-only → static + dynamic (BAS)

| Aspect | Original | v2 |
|--------|----------|----|
| Static metrics | CAS, HAD, PDI, JSD | Same |
| Dynamic metrics | None | CCR, AAS, GCS, BAS (composite) |
| Simulation engine | None | OASIS (CAMEL-AI, direct use, not via MiroFish wrapper) |

**Why.** Korean culture is *relational* — collectivist (IDV=18), long-term
orientation (LTO=100), high uncertainty avoidance (UAI=85). These are
properties of *interactions*, not of isolated personas. Measuring a
single persona's authenticity in isolation is like measuring teamwork by
interviewing one person alone. The dynamic layer puts personas into
realistic D2C scenarios and measures group dynamics against Korean
behavioral baselines (KOSIS, Naver Datalab, KOFICE).

**Cost.** ~60-80 hours of OASIS simulation compute and the scenario
authoring effort (50 D2C scenarios with expected behavioral
distributions). Mitigated by the OASIS simulator being external-LLM-call
dominated (Mac Mini orchestrates, AWS not needed).

**Risk if reversed.** High value-add. Drop only if W6 deadline pressure
forces it; in that case retain BAS for the full-stack vs Vanilla cells
at minimum (3 conditions × 5 trials × 1 backbone = 15 sims, ~20h).

## 5. Fine-tuning: out of scope → in scope (QLoRA)

| Aspect | Original | v2 |
|--------|----------|----|
| Fine-tuning | Not in scope | QLoRA on Qwen3.6-27B (and optionally Gemma 4 26B MoE) |
| Training data | n/a | Nemotron-Personas-Korea + CultureBank Korean subset |

**Why.** Two reasons. (1) AWS credits unlocked the compute. (2) RQ2 is
better answered if we test parametric (fine-tuning), prompting, and
retrieval as three distinct cultural-knowledge injection regimes. H4
specifically asks whether fine-tuned models close ≥50% of the Vanilla-
to-full-stack gap.

**Cost.** ~25 hours of g6e.xlarge time (~$46) for one backbone, ~50h for
two. Within budget.

**Risk if reversed.** Skip QLoRA condition if W3 G3 gate slips. Falls
back to prompt-only ablation. H4 becomes future work.

## 6. Orchestration: manual → 8-agent autonomous lab

| Aspect | Original | v2 |
|--------|----------|----|
| Pipeline orchestration | Manual scripts | 8 specialized agents under tiered autonomy |
| Writer-Critic loop | None | Adversarial review with separate model families |
| QA / self-eval | None | Three nested loops (per-task, per-draft, system-wide) |
| Decision auditability | Code comments | Versioned `decisions/` directory |

**Why.** 2-person, 8-week budget. Manual orchestration consumes most of
the time on coordination. Autonomous infrastructure is also a
*methodological contribution* — the kind of thing that distinguishes our
paper from the reference teams (Team 2, 4, 22 all describe algorithms;
none describes an autonomous research infrastructure).

**Cost.** ~$400 in feedback-loop API calls across W1-W8 (Critic, QA Meta,
PI). Worth it because it scales to future ORBT projects without
re-construction.

**Risk if reversed.** Heavy autonomy mode requires COSE461 AI-policy
verification (`make verify-policy`). If policy forbids agent-authored
sections, the autonomy tier drops to Medium and Sunwoo writes more
sections manually. Lab infrastructure (data fetch, sims, metrics) still
runs autonomously regardless.

## 7. NEW (2026-05-26): MiroFish reference + 6-axis differentiation framing

| Aspect | Original (none) | v2 |
|--------|-----------------|----|
| Reference engine cited | n/a | MiroFish (Ji et al. 2026, 62K stars) + OASIS (Yang et al. 2024) |
| Adjacent forks surveyed | n/a | MiroFish-Offline (Neo4j+Ollama), miroclaw, MiroFish-DE/ESP, hermes-geopolitical-market-sim (~30 derivatives) |
| Differentiation axes | implicit | 6 explicit axes: market specificity, persona grounding, cultural injection paths, backbone diversity, standard benchmarks, autonomous methodology — see RESEARCH_PLAN_v2.md §3 |

**Why.** Without MiroFish reference, reviewers slot us into "cultural-LLM bucket" (CultureLLM, CAReDiO peers). With it, our positioning sharpens to: *cultural-grounding extension to the leading multi-agent prediction engine, applied to Korean D2C market*. Sentence-level paper pitch becomes much clearer.

**Cost.** None — bibliography.bib + Related Work §2.2 expansion only.

**Risk if reversed.** Genuine omission of most-relevant prior work — reviewer weakness.

## 8. NEW (2026-05-26): KoAlpaca QLoRA pilot — negative result reframes Section 4

| Aspect | Original | v2 |
|--------|----------|----|
| W3 pilot scope | Validate pipeline | + Demonstrate general Korean SFT is INSUFFICIENT (KoBBQ correct 78.8% → 56.2%, KMMLU 42.5% → 32.5%) |
| Paper Section 4 structure | Single static-metrics table | 4.1 Why general Korean SFT fails / 4.2 Cultural-specific QLoRA result / 4.3 Capacity ablation / 4.4 Standard benchmarks |

**Why.** Run-A and Run-B both showed catastrophic forgetting on Korean knowledge benchmarks (KoBBQ correct rate dropped 17.5pp / 22.6pp; KMMLU dropped 2.5pp / 10pp). Run-B's bias reduction (-6.2pp) was paid for with massive accuracy loss. This is **the strongest empirical argument** for requiring cultural-specific training data (Nemotron-Personas-Korea + CultureBank-Korean) in W4.

See `decisions/2026-05-26-koalpaca-negative-result.md` for the full analysis.

**Cost.** None — restructure prose, no extra experiments. Adds Proposition 4 to MOTIVATION_v2 ("general Korean SFT ≠ cultural fix").

**Risk if reversed.** Negative results are assets in ML/NLP venues when they sharpen the positive contribution.

## Aggregate impact on the paper

Comparing the original PPT's expected contributions vs v2:

| PPT contribution | v2 status |
|------------------|-----------|
| Pipeline bridging cultural measurement → actionable persona generation | Strengthened (Nemotron + CultureBank + LightRAG) |
| Empirical comparison: prompting vs RAG vs embedding | Expanded to prompting vs RAG vs QLoRA fine-tuning |
| Human-validated authenticity benchmarks for Korean and Japanese personas | Korean only, deeper |
| (none) | **NEW**: BAS — dynamic behavioral authenticity metric (pivoted to directional reporting per R4 finding) |
| (none) | **NEW**: Autonomous research-lab methodology |
| (none) | **NEW**: ORBT product transfer surface |
| (none) | **NEW (2026-05-26)**: MiroFish/OASIS as reference engine — 6-axis differentiation |
| (none) | **NEW (2026-05-26)**: KoAlpaca negative result — quantitatively justifies cultural-specific training data |

## Where this appears in the paper

The Writer agent uses this document to produce:
- Introduction: one paragraph on motivation for the redesign.
- Methods: subsection "Design evolution from initial proposal" listing
  the six deviations in compact form.
- Discussion: tie back to which deviations turned out essential vs
  cosmetic, with empirical evidence.
- Appendix B: full deviation table (this file's table 1).

## Re-deviation policy

Any further deviation from the v2 plan must be:
1. Logged as a new entry in `decisions/`.
2. Reviewed by PI agent in next daily audit.
3. Reflected back in this file with a new section.

QA Meta agent monitors the diff between this file and committed code; if
they drift apart for > 48h, it pages Sunwoo.
