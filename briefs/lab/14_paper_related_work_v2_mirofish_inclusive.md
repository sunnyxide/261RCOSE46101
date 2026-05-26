# Paper Related Work v2 — MiroFish/OASIS inclusive (replaces brief 08)

**Origin**: Brief 08 produced an initial Related Work draft, but didn't
include MiroFish (we discovered it 2026-05-26 after brief 08 was queued).
This brief reframes Related Work around 4 buckets — bias measurement /
value alignment / multi-agent simulation engines / persona generation —
and positions our work precisely against each.

**Goal**: produce `results/hermes_outputs/14_paper_related_work_v2_mirofish_inclusive.md`
— a 1.2-1.5 page Related Work section that REPLACES brief 08's output for
the final paper.

**Why supersede brief 08**: the original Related Work treated MiroFish-class
work as "out of scope". Our W3 work makes clear we ARE in the multi-agent
simulation space; we extend it. New structure surfaces our 6-axis
differentiation explicitly.

---

## Required structure — four subsections (~250 words each)

### 2.1 Measurement of cultural bias in LLMs

- CulturalBench [chiu2024culturalbench] — best LLM 61.5% vs human 92.4%
- KoBBQ [jin2024kobbq] — Korean bias-QA, our pilot tested all 3 models on
  80-question subset
- CLIcK [kim2024click] — Korean linguistic intelligence
- HAE-RAE Bench [haerae2023] — Korean knowledge
- KAIO 2026 (TODO citation — see brief 12 output)
- Tao et al. PNAS 2024 — cross-model error correlation ρ > 0.97

**Position**: These measure the gap. Our W3 KoBBQ result (vanilla 78.8%
correct, 40% bias) confirms the gap; our SECTION 4.1 negative result
(KoAlpaca QLoRA worsens it) shows that general Korean SFT does NOT close
this gap. Cite our own pilot.

### 2.2 Cultural value alignment + multi-agent simulation engines

This bucket combines value-alignment LLMs with simulation-based prediction
engines.

- CultureLLM [li2024cultureLLM] — fine-tuned on cultural surveys
- CAReDiO — retrieval-augmented cultural reasoning (TODO bibkey)
- **MiroFish [ji2026mirofish]** — 62K-star multi-agent prediction engine on
  OASIS; explicitly produces simulated "social world" trajectories.
  Workflow: Graph → Environment → Simulation → Report → Interaction.
  Uses Zep Cloud memory + Qwen-plus LLM. Targets generic prediction
  (politics, finance, novels). Evaluates by report quality, not standard
  benchmarks.
- **MiroFish-Offline** [mirofishoffline2026] — Graphiti+Neo4j local stack,
  demonstrates Zep is replaceable.
- OASIS [yang2024oasis] — underlying multi-agent social-sim engine,
  CAMEL-AI.
- CultureBank [shen2024culturebank] — community-driven cultural KG.

**Position**: MiroFish is the most relevant prior work — same substrate
(OASIS), different mission. They predict generic outcomes from reports.
We extend with three cultural-grounding layers (Nemotron-quota
demographics + CultureBank-Korean retrieval via LightRAG + QLoRA
parametric injection) and validate against Korean-specific cultural
benchmarks where MiroFish/CultureLLM/CAReDiO use heuristic eval. Our
Section 4 demonstrates each layer's contribution.

### 2.3 Synthetic persona generation

- PersonaHub (TODO bibkey) — generic, English-dominant
- Ge et al. [ge2024scaling] — billion-persona scaling
- Nemotron-Personas-Korea [nvidia2024nemotron] — Korean demographic
  skeleton; our W3 data backbone

**Position**: Prior persona work prioritizes demographic surface +
linguistic surface. Korean personas read as "Americans named Min-jun"
because cultural muscle is missing. Our combination of Nemotron (KOSIS-
quota) + CultureBank-Korean (cultural descriptors via LightRAG) +
optional QLoRA fine-tune fills exactly this gap.

### 2.4 Korean-pretrained LLMs as alternative baseline

- EXAONE 3.0 [exaone2024] — 7.8B Korean bilingual model from LG AI
- HyperCLOVA X — Naver Cloud API
- KULLM v2 [kullm2023] — Korea Univ NLP/AI Lab
- Polyglot-Ko — EleutherAI

**Position**: One might ask "why not just use a Korean-pretrained model
as base?" Our Run-E (EXAONE on KoAlpaca, queued) directly tests this. We
expect Korean-pretrained base to outperform Western multilingual base on
KMMLU (factual recall) but not necessarily on KoBBQ (bias)
— and we propose that cultural grounding (Nemotron+CultureBank
QLoRA) on top of either base type is the dominant intervention.

---

## Hard constraints

- Each subsection: 200-300 words
- Position-statement (1-2 sentences) at end of each subsection — what
  prior work doesn't do + what we add
- Cite ONLY from `reports/bibliography.bib`. Use `[TODO citation: <topic>]`
  for known gaps
- DO NOT discuss our results in detail — Related Work just situates prior
  work
- DO reference our W3 pilot findings (KoBBQ 78.8% / 56.2% / etc.) as
  *evidence to be developed in Section 4*, not as Related Work content
- DO NOT bleed into Methods — keep at the "what was done before" level

## Output format

Plain markdown with `# Related Work` heading + four `## 2.1`, `## 2.2`,
`## 2.3`, `## 2.4` subsections. ~900-1100 total words.

5-slot meta footer:
```
[meta]
verifiability_signal: high|medium|low
n_citations_used: <int>
n_todo_citations: <int>
mirofish_position: <one-sentence summary of how we positioned MiroFish>
```
