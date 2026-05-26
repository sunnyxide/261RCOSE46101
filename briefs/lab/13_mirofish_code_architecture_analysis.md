# MiroFish code architecture analysis + ORBT-lab mapping table

**Origin**: RESEARCH_PLAN_v2.md identifies MiroFish (666ghj/MiroFish, 62K
stars) as the most relevant prior-work reference engine. We share OASIS
(CAMEL-AI) as the underlying simulation substrate. To position our work
precisely vs MiroFish in Section 2 and to potentially reuse some of their
patterns, we need a structural understanding of the MiroFish codebase
and an explicit mapping to our lab.

**Goal**: produce `results/hermes_outputs/13_mirofish_code_architecture_analysis.md`
— a 5-section technical writeup of MiroFish's architecture with a mapping
table to our `orbt-research-lab/`.

---

## Required findings (5-slot format)

### Finding 1 — MiroFish's 5-step workflow detailed

**Question**: What does each of MiroFish's 5 workflow steps actually do
internally? Pull from README + DeepWiki (https://deepwiki.com/666ghj/MiroFish):
1. Graph Building — what does seed extraction look like? what KG framework?
2. Environment Setup — entity-relationship extraction methodology?
3. Simulation — OASIS configuration, agent count typical range?
4. Report Generation — ReportAgent toolset?
5. Deep Interaction — chat interface mechanism?

**Output**: file paths in their repo for each step + 1-2 sentence summary.

### Finding 2 — Dependency stack

**Question**: Concrete tech choices:
- Frontend (Vue + framework version)
- Backend (Flask? FastAPI? other?)
- LLM provider abstraction (provider catalog architecture)
- Memory layer: Zep Cloud vs Graphiti (in MiroFish-Offline fork)
- Database: anything beyond Zep?
- Multi-agent runtime: bare OASIS or wrapper?

**Output**: dependency tree compact.

### Finding 3 — Mapping to ORBT-research-lab

**Output**: a table mapping MiroFish components to our lab paths:

| MiroFish | ORBT-research-lab | Reuse/Replace |
|---|---|---|
| Seed extraction | data_steward Layer 1 | replace (our data is structured KOSIS+Nemotron, not freeform seeds) |
| GraphRAG construction | LightRAG over CultureBank-Korean | replace with our approach |
| ReportAgent | analyst.py + writer.py | reuse pattern, different prompts |
| Zep memory | DVC manifests + decisions/ | replace |
| OASIS simulation | experiment_runner.py + OASIS direct | shared substrate |
| 5-step pipeline | scheduler.py + agents/ | parallel structure |
| Vue frontend | none (we ship Python API for ORBT) | replace |

### Finding 4 — Three reusable patterns from MiroFish

**Question**: What can we ADOPT from MiroFish without rewriting our lab?
- The 5-step workflow ORDER (good cognitive structure for paper Methods)
- ReportAgent's tool palette pattern (we could mirror for analyst)
- Provider-catalog abstraction (model swap without code changes)

For each: where in our lab would it go, and is it worth the engineering?

### Finding 5 — Three differences we MUST emphasize in paper

**Question**: What does MiroFish NOT do that we do?
1. Demographic grounding (KOSIS-quota persona sampling) — MiroFish generates
   personas from seed reports ad-hoc
2. Parametric culture injection (QLoRA on Nemotron+CB) — MiroFish has no
   training path, only retrieval + memory
3. Standard benchmark evaluation (KoBBQ, KMMLU, CLIcK, HAERAE) — MiroFish
   evaluates report quality qualitatively
4. Production API contract (orbt_research_lab/api.py) — MiroFish is a demo
5. Decision-log audit trail — MiroFish has no provenance tracking

---

## Output format

Plain markdown with five `## Finding N` sections, then a final
`## Recommendations` section with prioritized action items (e.g., "adopt
5-step naming in paper Methods § 3.1", "skip Vue frontend port", etc.).

Append research_v2 meta footer:
```
[meta]
verifiability_signal: high|medium|low
n_repo_files_inspected: <int>
n_patterns_adopted: <int>
n_patterns_rejected: <int>
```

## Sources

- https://github.com/666ghj/MiroFish (primary, English README)
- https://github.com/666ghj/MiroFish/blob/main/README-ZH.md (Chinese — more detail typically)
- https://deepwiki.com/666ghj/MiroFish (auto-generated code wiki)
- https://github.com/nikmcfly/MiroFish-Offline (English fork with Graphiti+Neo4j)
- https://github.com/camel-ai/oasis (substrate documentation)

## Hard constraints

- DO NOT recommend rewriting our existing lab to match MiroFish — we have
  a different mission (Korean D2C deep, not general prediction)
- DO call out clear adoption candidates (workflow naming, tool patterns)
- DO NOT invent file paths — verify via GitHub raw browsing
