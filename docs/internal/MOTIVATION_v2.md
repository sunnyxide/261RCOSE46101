# Motivation (v2, long form)

> The Writer agent draws from this document to produce the Introduction and the
> first half of the Discussion. Every claim here must be traceable to a citation
> in `reports/bibliography.bib` or to a quantitative artifact in `results/`.
> Section headers correspond to paragraph hooks the Writer expects to consume.

## 1. The Western-default problem in deployed LLMs

State-of-the-art LLMs trained predominantly on English internet corpora encode
Western individualist defaults across the dimensions that drive consumer
behavior: how purchase decisions are reached, whose opinion is solicited, how
social proof is weighted, how trust is signaled, how dissatisfaction surfaces.
When such a model is asked to predict "what would my customer think?" in a
non-Western market, the response is approximately what an American customer
would think, expressed in the target language.

Three regimes of evidence make this concrete:

**Benchmark evidence.** CulturalBench [@chiu2024culturalbench] reports the best
LLM at 61.5% accuracy versus 92.4% human ceiling on culturally-grounded
questions. KAIO [@kaio2026] — the most recent hard-Korean benchmark we are
aware of — shows GPT-5 at 62.8 and Gemini-2.5-Pro at 52.3, with Qwen3-235B
and DeepSeek-R1 below 30. The 37-point headroom above the best frontier model
is not noise.

**Error-correlation evidence.** Tao et al. [@tao2024pnas] document
cross-model error correlation ρ > 0.97 on cultural questions, indicating a
shared calibration artifact rather than independent random errors. Every
Western-trained model fails in the same direction.

**Operational evidence from ORBT production.** Three observations during D2C
client engagements:
- Korean team-name suggestions read as English-thinking-translated, not
  Korean-native (e.g., literal compounding instead of idiomatic shortening).
- Hollow compliment patterns ("훌륭한 결정이네요") violate efficient Korean
  communication norms — Korean professional discourse weights concision
  much higher than affirmation.
- Chain-of-thought traces, when surfaced, show English-first reasoning then
  translation. This is not just a stylistic concern; it propagates Western
  reasoning patterns (individual deliberation, immediate verbal feedback)
  into outputs framed as Korean.

The aggregate cost is that enterprises in non-Western markets cannot trust
LLM-based consumer modeling. This is the single largest blocker we have
observed to non-US market expansion of LLM products.

## 2. Why prior work does not solve this

Prior work falls into three buckets, none of which produce a deployable
consumer-modeling artifact.

**Measurement of bias.** CulturalBench [@chiu2024culturalbench], KoBBQ
[@kobbq], CLIcK [@click], KMMLU [@kmmlu] — these document the gap. They do
not close it.

**Value alignment.** CultureLLM [@culturellm], CAReDiO [@caredio],
CultureManager [@culturemanager] — these align model values via fine-tuning
or retrieval. They optimize for survey-response congruence, not for
behavioral plausibility in consumer contexts. A model that produces
WVS-aligned answers does not necessarily produce a credible Korean shopper.

**Persona generation without cultural grounding.** Most synthetic persona
work (e.g., Anthropic's PersonaHub, [@personahub]) prioritizes demographic
coverage and linguistic surface variety, not cultural authenticity. The
Korean personas in such datasets read as Americans named Min-jun.

The gap: nobody has produced a pipeline that combines **(a)** demographic
grounding from actual census data, **(b)** cultural descriptors from a
structured KG, **(c)** behavioral validation under realistic scenarios,
**(d)** integration interface for downstream product use.

That gap is the contribution this project occupies.

## 3. Our position

We assert four propositions, each tied to a hypothesis the experimental
design tests.

**Proposition 1 — Cultural retrieval is necessary but not sufficient.**
LightRAG over CultureBank Korean descriptors closes part of the Western
default gap, but without demographic grounding the personas drift toward
"average Korean" stereotypes that defeat the purpose. Tested via H1
(retrieval improves CAS) and PDI (diversity preservation).

**Proposition 2 — Demographic grounding is necessary but not sufficient.**
Nemotron-Personas-Korea provides KOSIS-matched demographic skeletons but
no cultural muscle — personas have correct ages and regions but reason
in American patterns. Tested via condition #4 vs #6 in the ablation.

**Proposition 3 — Static authenticity does not imply behavioral
authenticity.** A persona that scores high on CAS in isolation can still
behave individualistically in a group simulation. Korean culture is
relational; the unit of analysis must include interaction dynamics. This
motivates the BAS metric and the OASIS simulation layer — distinguishing
our work from all prior cultural-NLP evaluation.

**Proposition 4 — These results must transfer to product, not just to
papers.** A research artifact that requires a graduate-student researcher
to operate is not a contribution to industry. The autonomous research lab
architecture (six → eight agents, tiered autonomy, ORBT-integration hooks)
is itself a contribution, demonstrating that culturally-grounded persona
generation can run as a production pipeline.

## 4. Why this matters now (timing argument)

Three converging factors make this the right time to do this work:

**Tooling maturity.** LightRAG (HKU, 2024), CultureBank (SALT-NLP,
EMNLP'24), OASIS (CAMEL-AI, 2025), Nemotron-Personas-Korea (NVIDIA,
2026) — every component piece has shipped in the last 18 months. Two
years ago this study was not buildable.

**Model generation transitions.** Gemma 4 (Apr 2026), Qwen3.6 (Apr 2026),
Llama 4 — three open-weight model families in three months. Testing
cultural-grounding effects across this transition produces a snapshot
that future work will cite as the bridge between pre-MoE and post-MoE
generations.

**Market pull.** Korean D2C is a $30B+ market. ORBT clients are asking
for this capability today. Academic publication and product release can
share an experimental campaign.

## 5. Scope and explicit non-goals

**In scope.**
- Korean consumer personas as the primary artifact.
- Static and dynamic evaluation, with human evaluator validation.
- A deployable Python package and OpenCloud workflow block.
- A peer-reviewable paper at ACL Findings quality or above.

**Explicitly NOT in scope.**
- Other markets (Japan, India, MENA). Future work.
- Aligning the underlying LLM weights via RLHF on Korean data. Different
  research question.
- Real-time recommendation systems. We produce personas; downstream
  consumers use them.
- Fine-tuning ethics audit beyond what the human-evaluator protocol
  requires. We disclose data sources and licenses; we do not claim to
  have solved cultural bias broadly.

## 6. Falsifiability

The project fails if any of the following is observed at the end of W7:
- Full-stack condition is not statistically distinguishable from Vanilla
  on CAS (paired t-test p > 0.05).
- Korean evaluator inter-rater reliability falls below Krippendorff α =
  0.67 — meaning the metric we are using is not measuring a stable
  construct.
- Static gains (CAS, HAD) correlate negatively with dynamic gains (BAS),
  indicating the two evaluation regimes are pulling in opposite
  directions.
- ORBT integration test fails because the pipeline cannot produce a
  persona within latency / cost budgets the product can absorb.

These are not "limitations to acknowledge"; they are conditions under
which we publish a negative result and write the discussion accordingly.

---

*Last updated: 2026-05-24. This file is a living document. Update if and
only if the underlying empirical situation changes; otherwise treat
edits as Tier-3 actions requiring human approval logged in `decisions/`.*
