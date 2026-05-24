# Paper Related Work draft (Writer agent task)

**Origin**: Paper drafting continues. Related Work is the next-most-isolated
section after Introduction — doesn't need our experimental results.

**Goal**: produce `reports/sections/draft_related_work.md` — 1-1.5 page
Related Work that situates our contribution against three buckets of prior
work (matching MOTIVATION_v2.md §2 structure).

**Decisions affected**:
- `reports/sections/draft_related_work.md` (draft/agent-* branch only)
- Critic queue (brief 10)

---

## Structure required

Three subsections, each ~250-300 words:

### 2.1 Measurement of cultural bias

- CulturalBench [chiu2024culturalbench]: benchmark structure, GPT-5 score 61.5%
  vs human 92.4%, multi-language coverage
- KoBBQ [jin2024kobbq]: Korean bias benchmark, what dimensions it measures
- CLIcK [kim2024click]: Korean linguistic/cultural intelligence, dimensions
  covered
- HAE-RAE Bench [haerae2023]: complementary Korean knowledge benchmark
- KAIO benchmark (2026): cite as `[TODO citation: KAIO 2026]` since we don't
  yet have the bibkey

Position: these measure the gap, don't close it. Our work treats their
metrics as ceilings to validate against, not as solutions in themselves.

### 2.2 Value-alignment approaches

- CultureLLM [li2024cultureLLM]: fine-tuning on culturally-aligned data —
  what they did, what they reported, scope (mainly survey-response alignment)
- CAReDiO: retrieval-augmented cultural reasoning (cite as
  `[TODO citation: CAReDiO]`)
- CultureBank [shen2024culturebank]: community-driven KG — strengths and
  what they don't tackle (behavioral validation under scenarios)

Position: these optimize for survey-response congruence; we extend to
*deployable persona generation with behavioral validation*. Our LightRAG
over CultureBank Korean subset is the first to combine cultural-KG
retrieval with demographic grounding for D2C use cases.

### 2.3 Persona generation

- PersonaHub: prior work on synthetic persona generation, what their
  Korean cohort looks like (cite as `[TODO citation: PersonaHub]`)
- Ge et al. [ge2024scaling]: billion-persona scaling
- Nemotron-Personas-Korea [nvidia2024nemotron]: NVIDIA's release as our
  seed corpus

Position: prior persona work prioritizes demographic surface and
linguistic variety; we add cultural-descriptor grounding via KG retrieval +
behavioral validation. The Korean personas in prior datasets read as
"Americans named Min-jun" — this paper closes that.

## Hard constraints

- Each subsection: 250-300 words (3 × ~300 = ~900 total)
- No more than 3 sentences per cited work
- Position-statement at end of each subsection (1-2 sentences) explaining
  why prior work doesn't suffice and what specifically we add
- DO NOT cite anything not in `reports/bibliography.bib`. Use
  `[TODO citation: <topic>]` for known-gap items.
- DO NOT discuss methods or results. Just situate prior work + our gap-filling.

## Output

Plain markdown with `# Related Work` heading + three `## 2.1`, `## 2.2`,
`## 2.3` subsections.

5-slot meta footer:
```
[meta]
verifiability_signal: high|medium|low
n_citations_used: <int>
n_todo_citations: <int>
```
