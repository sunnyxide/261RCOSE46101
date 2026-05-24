# Paper Introduction draft (Writer agent task — pushes to draft/agent-* branch)

**Origin**: Paper drafting (W4-W5 work, started early because AWS-down hours
give us deep-reasoning time without GPU contention). MOTIVATION_v2.md is the
canonical source the Writer pulls from.

**Goal**: produce `reports/sections/draft_introduction.md` — a 1-1.5 page
paper Introduction following the section 1-2 of MOTIVATION_v2.md. The
Critic agent will review this on a follow-up cycle (`brief 09`).

**Decisions affected**:
- `reports/sections/draft_introduction.md` — Writer-authored, draft/agent-*
  branch only (never main per HANDOFF §8)
- Critic's review queue (Phase 9 brief)

**Why now**: Introduction is human-readable, doesn't require finished
experimental data (it argues for the work, doesn't report results). Drafting
early lets us iterate before W5-W7 results crunch.

---

## What the Introduction must contain (in this order)

1. **Opening (1-2 paragraphs)**: the Western-default problem in deployed
   LLMs for non-Western markets. Use MOTIVATION_v2.md §1 verbatim where
   possible. Cite chiu2024culturalbench + kobbq + tao2024pnas.
   Concrete examples: ORBT production observations (Korean team names,
   hollow compliments, English-first reasoning).

2. **Gap in prior work (1 paragraph)**: three buckets fail to produce
   deployable artifacts — measurement, value alignment, persona-without-
   grounding. Cite culturellm, caredio, personahub.

3. **Our contribution (1 paragraph)**: a pipeline that combines (a)
   demographic grounding from KOSIS-matched Nemotron-Personas-Korea, (b)
   cultural descriptors from CultureBank Korean subset via LightRAG, (c)
   QLoRA fine-tuning for parametric injection, (d) OASIS-based behavioral
   validation, (e) ORBT product-integration surface.

4. **Hypotheses (compact list)**: H1-H4 from HANDOFF.md §2, one sentence
   each, with the corresponding metric. No bullet list — integrate into
   prose with bold-emphasized hypothesis names.

5. **Roadmap (1 paragraph)**: section 2 = method, section 3 = experiments,
   section 4 = results, section 5 = discussion + limitations, appendix =
   ablations + autonomous-lab methodology.

## Required style (reports/style_guide.md condensed)

- Tense: present tense for what we do, past tense for prior work
- Voice: "we" for our contributions, "prior work" or named-author for others
- No marketing voice — concrete claims with citation tags `[bibkey]`
- No first-person plural in sentences that are about empirics ("We find" OK,
  "We feel" not OK)
- Every numerical claim has a `[results/file.json]` traceability tag OR a
  citation `[bibkey]`. NO orphan numbers.

## Cite from these bibkeys only

`chiu2024culturalbench`, `jin2024kobbq`, `kim2024click`, `haerae2023`,
`li2024cultureLLM`, `shen2024culturebank`, `nvidia2024nemotron`,
`ge2024scaling`, `guo2024lightrag`, `yang2024oasis`, `kosis2024`,
`naverdatalab2024`, `kofice2024`.

If you need a citation not in this list, mark `[TODO citation: <topic>]`
and the librarian will queue a lit-search task. Do NOT invent bibkeys.

## Hard constraints

- Length: 600-900 words (Introduction is ~10% of an 8-page paper)
- DO NOT write Methods. Methods is human-authored per HANDOFF §8. Critic
  will reject any Introduction draft that bleeds into Methods territory.
- DO NOT write Results. Results need finished experimental data; we have
  pilot data only.
- DO discuss the *autonomous lab itself* as a methodology contribution in
  the final paragraph — it's one of our distinguishing features from
  Team 2/4/22 reference papers.

## Output format

Plain markdown with section heading `# Introduction`, no other top-level
heading. Use `## ` for any subdivision if needed (but ideally none — flow
as continuous prose).

Append the **research_v2 5-slot meta footer** at the very end:

```
[meta]
verifiability_signal: high|medium|low
n_citations_used: <count>
n_orphan_numbers: 0  (must be 0 — Critic will fail this otherwise)
unaddressed_motivation_sections: <list of MOTIVATION_v2 sections you didn't pull from, with reason>
```
