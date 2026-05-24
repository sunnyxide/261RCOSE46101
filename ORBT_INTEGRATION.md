# ORBT integration plan — research → product transfer

> How the COSE461 research deliverables become production-ready ORBT
> features. This document is the bridge between the academic artifact
> (paper + repo) and the commercial artifact (Hermes agent + OpenCloud
> pipeline). Sunwoo owns this integration; it happens in W8 after the
> paper is final.

## 1. ORBT product surface today (as-is)

| Component | What it does today | What it lacks |
|-----------|-------------------|---------------|
| **Hermes agent** | Consumer-intelligence agent for D2C brands. Answers questions like "what trends are emerging in our category?" | No per-market persona-grounded prediction. Korea responses are Western-default. |
| **OpenCloud** | Pipeline workflow product, lets users compose intelligence/simulation blocks. | No simulation block. Blocks today are mostly retrieval + summarization. |
| **intel_v1 KG** | Internal knowledge graph for brand/category/trend data. | No cultural descriptor layer. |
| **persona_mapping module** | Returns persona profiles for a given consumer cohort. | Returns empty for Korea (production bug, motivates this research). |
| **evaluate_graphrag.py** | Evaluation harness for GraphRAG pipelines. | No cultural authenticity evaluation. |

## 2. ORBT product surface after integration (to-be)

| Component | New capability | Sourced from |
|-----------|----------------|--------------|
| **Hermes agent** | `predict_consumer_response(brand, campaign, market="KR")` tool | This lab's full-stack pipeline (Nemotron + CultureBank + LightRAG) |
| **OpenCloud** | `cultural-persona-grounded-simulation` block, configurable for 6 conditions | OASIS harness + scenario library |
| **intel_v1 KG** | `cultural_descriptor` node type, edges to brand/category nodes | CultureBank Korean subset, LightRAG indexer |
| **persona_mapping** | Returns full personas with demographic + cultural grounding for KR | data_steward output + LightRAG-grounded generation |
| **evaluate_graphrag.py** | Adds CAS, HAD, PDI, JSD, BAS as evaluation regimes | This lab's `agents/analyst.py` |

## 3. API contracts

The lab exposes its capability via a Python package the ORBT codebase
imports. Stable surface:

```python
# orbt_research_lab/api.py

from orbt_research_lab import (
    PersonaGenerator,
    KoreanCulturalKG,
    BehavioralSimulator,
    AuthenticityEvaluator,
)

# 1. Persona generation
gen = PersonaGenerator(
    condition="full_stack",       # one of: vanilla, hofstede, kg, nemotron,
                                  #         nemotron_hofstede, nemotron_kg
    backbone="qwen3.6-27b-q4",    # local model for low-cost inference
    market="KR",
)
personas = gen.generate(
    n=10,
    cohort_filter={"age_range": "20-39", "region": "수도권"},
)
# returns: list[Persona] with .demographic, .cultural_descriptors, .narrative

# 2. KG access
kg = KoreanCulturalKG()  # backed by LightRAG + Neo4j running on Mac Mini
descriptors = kg.retrieve("brand-loyalty in Korean cosmetics buyers", k=5)

# 3. Behavioral simulation
sim = BehavioralSimulator(scenario="discovery_via_단톡방")
result = sim.run(personas=personas, rounds=10)
# returns: SimResult with .ccr, .aas, .gcs, .bas, .transcript

# 4. Evaluation (for ORBT QA on customer-facing outputs)
eval = AuthenticityEvaluator()
score = eval.score(persona=personas[0])
# returns: AuthenticityScore with .cas, .had, .pdi, .jsd
```

## 4. Hermes agent tool

ORBT's Hermes agent gets a new tool that wraps the lab's pipeline:

```python
@tool
def predict_consumer_response(
    brand: str,
    campaign_description: str,
    market: Literal["KR"],
    cohort: dict | None = None,
    n_personas: int = 5,
) -> dict:
    """Predict how Korean consumers in `cohort` would respond to `campaign`.

    Returns a structured prediction grounded in n_personas synthetic
    Korean consumer personas, with both individual responses and
    aggregate group dynamics (CCR, AAS).

    Latency target: ≤ 8s p95.
    Cost target: ≤ $0.05 per call (using local Qwen3.6-27B Q4).
    """
    ...
```

Implementation calls into `orbt_research_lab.PersonaGenerator` +
`BehavioralSimulator` with a fixed `condition="full_stack"`. Other
conditions are exposed only to internal users (for A/B comparison).

## 5. OpenCloud block

ORBT's OpenCloud product gets a new draggable block users can place in
their workflow:

```yaml
block:
  name: cultural-persona-grounded-simulation
  category: simulation
  inputs:
    - name: brand
      type: brand_ref
    - name: scenario
      type: scenario_template
    - name: market
      type: enum
      values: ["KR"]   # JP/IN/MENA in future
  outputs:
    - name: aggregate_response
      type: simulation_result
    - name: individual_responses
      type: array<persona_response>
    - name: authenticity_scores
      type: authenticity_metrics
  config:
    n_personas: { default: 10, range: [1, 100] }
    rounds: { default: 5, range: [1, 20] }
    condition:
      default: full_stack
      values: [vanilla, hofstede, kg, nemotron, nemotron_hofstede, nemotron_kg]
```

The condition selector is exposed because some ORBT internal users
(e.g., consulting team running ablation reports for clients) need to
show before/after of cultural grounding to justify the value-add.

## 6. intel_v1 KG schema extension

```cypher
// New node type
CREATE CONSTRAINT cultural_descriptor_id IF NOT EXISTS
  FOR (cd:CulturalDescriptor) REQUIRE cd.id IS UNIQUE;

// CulturalDescriptor properties
// - id: unique
// - market: 'KR' (for now)
// - dimension: 'collectivism' | 'authority' | 'group_consensus' | ...
// - source: 'culturebank' | 'hofstede' | 'wvs' | 'manual'
// - description: text
// - example: text (concrete behavior example)
// - confidence: 0..1 (from cultural_filter agent)

// Relationships
// CulturalDescriptor -[:APPLIES_TO]-> Brand
// CulturalDescriptor -[:APPLIES_TO]-> Category
// CulturalDescriptor -[:CONFLICTS_WITH]-> CulturalDescriptor
// Persona -[:GROUNDED_IN]-> CulturalDescriptor
```

The data_steward agent already produces the descriptor list. The schema
extension happens in `intel_v1` repo (separate); the lab provides the
populated descriptors as a JSONL export.

## 7. Cost model for production

The research budget ($400) does not constrain product economics. Production
cost per Hermes call (target: $0.05):

| Component | Per-call cost |
|-----------|---------------|
| Persona generation (Qwen3.6-27B Q4 on Mac Mini, free amortized) | $0.00 (compute amortized) |
| OASIS sim (5 personas × 10 rounds = 50 LLM calls @ GPT-4o-mini) | $0.04 |
| Evaluation (CAS via LLM-judge, cached for common cohorts) | $0.01 |
| Storage / network | trivial |
| **Total** | **$0.05** |

Mac Mini serves as the persona-generation node in production initially.
Scaling beyond 100 calls/day means moving inference to a dedicated GPU
or contracting with a Korean cloud provider (Naver Cloud has L40S
instances). Migration is a config change.

## 8. Deployment plan

| Step | When | Action | Owner |
|------|------|--------|-------|
| 1 | W7 | Freeze the lab's `orbt_research_lab/api.py` surface | Sunwoo |
| 2 | W7 | Write Hermes-side wrapper + unit tests (in ORBT repo) | Sunwoo |
| 3 | W8 day 1 | Run integration test: Hermes calls lab API end-to-end | Sunwoo |
| 4 | W8 day 2 | Deploy to staging: 1 D2C client (volunteer) tests for 48h | ORBT eng |
| 5 | W8 day 4 | Production roll-out for KR market with feature flag | ORBT eng |
| 6 | Post-W8 | Monitor: latency, cost, customer-reported authenticity issues | Sunwoo + ORBT eng |

## 9. What the integration does NOT promise

- **Not a general-purpose cultural alignment fix.** Only Korea, only D2C
  consumer scenarios, only the cohorts represented in the Nemotron+KOSIS
  sampling.
- **Not a replacement for native-speaker validation.** Production calls
  surface authenticity scores; calls below CAS=4.0 are flagged for
  human-in-the-loop review.
- **Not a real-time chat agent.** Personas are generated, simulated, and
  reported — not used as live conversational characters.
- **Not a fine-tuning service for client models.** ORBT does not expose
  the QLoRA adapters to clients in v1.

## 10. Pre-conditions before W8 integration

Hard requirements that the lab must satisfy before integration begins:

- [ ] All Tier-1 KPIs (G1-G6) green.
- [ ] `orbt_research_lab/api.py` covered by ≥ 80% unit-test line coverage.
- [ ] At least one full-stack condition passing CAS target (Δ ≥ 0.8 vs Vanilla, p<0.01).
- [ ] BAS for full-stack at ≥ 0.80 with target Korean baselines.
- [ ] OpenAI / API key separation between research and production accounts
  documented in `decisions/`.
- [ ] License attribution drafted in `reports/AI_USAGE_DISCLOSURE.md`
  AND in ORBT production legal-disclosures repo.

If any pre-condition is unmet by W7 Friday, ORBT integration defers to
post-submission (W9+) and the paper still ships on schedule.

## 11. Risk: research timeline drag delaying ORBT roadmap

Mitigation: the lab is structured so that even partial completion is
useful. If the dynamic layer (BAS) isn't ready, ORBT can ship with
static-only authenticity scoring. If only one backbone (Qwen3.6) is
ready, ORBT ships single-backbone. Each milestone produces a
deployable subset.

The autonomous lab's `qa_meta` agent monitors ORBT integration
pre-conditions weekly starting W5 and flags slippage before it cascades.
