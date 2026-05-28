# Research plan v2 — 165 credits, 6 weeks to ACL Findings quality

> Date: 2026-05-26 (W2 start)
> Status: live plan, supersedes AWS_PERFORMANCE_PLAN.md §4-5
> Inputs: W3 pilot results (negative on KoAlpaca), Brief 01 R4 finding,
>         MiroFish reference, ~165 credits remaining
> Owner: Sunwoo (decides) + autonomous lab (executes)

This document replaces the conservative original AWS plan with an aggressive
research agenda enabled by the ~165 credits (~107 GPU hours) the team has
across two AWS accounts. The W3 pilot already validated the QLoRA pipeline
end-to-end; the remaining budget funds **6 ablation dimensions** that
collectively differentiate this paper from MiroFish, Token Pirates v1,
CultureLLM, CAReDiO, and the COSE461 reference teams (Team 2/4/22).

---

## 1. Credit budget — what 165 credits buys

| Activity | Hours | Credits | Purpose |
|---|---|---|---|
| W3 pilot (done) | 11 | 14 | Pipeline validation + KoAlpaca negative result |
| Run-D: Qwen2.5-7B QLoRA on KoAlpaca | 3 | 4.6 | Backbone-size ablation |
| Run-E: EXAONE-3.0-7.8B QLoRA on KoAlpaca | 3 | 4.6 | Korean-pretrained baseline comparison |
| Run-F: Qwen2.5-3B QLoRA on Nemotron+CultureBank (W4 main) | 3 | 4.6 | **H4 test** — culturally-specific training |
| Run-G: Qwen2.5-7B QLoRA on Nemotron+CultureBank | 4 | 6.1 | H4 + scale interaction |
| Run-H: Llama-3.1-8B QLoRA on Nemotron+CultureBank | 4 | 6.1 | Legacy backbone H2 (RQ2 generational covariate) |
| Korean cultural benchmark × 8 models | 4 | 6.1 | KoBBQ + KMMLU + CLIcK (if accessible) |
| 4,800 persona generation (W3 G3 main) | 16 | 24 | 6 conditions × 4 backbones × 200 |
| OASIS dynamic sims (W6) | 12 | 18 | 50 scenarios × 5 trials × 6 conditions |
| LLM judge panel (CAS via 4-model panel) | 6 | 9 | EVALUATOR_FALLBACK.md Tier C |
| Buffer for re-runs / failed checkpoints | 15 | 23 | Safety margin |
| **Total committed** | **81** | **120** | of 165 |
| **Headroom** | 24 hours | 45 credits | for unexpected ablations |

→ Plan finishes at 120/165 (73% utilization), leaving 45-credit safety margin.

---

## 2. Six ablation dimensions (paper Section 4 structure)

Each ablation answers a specific question. Reviewer-level rigor demands
isolating each dimension; we have credits to do so.

| # | Ablation | Hypothesis tested | Runs needed | Section |
|---|---|---|---|---|
| **A** | General-Korean instruction data **fails** to fix cultural patterns | Counter-H4 prereq | ✅ done (Run-A + Run-B) | §4.1 |
| **B** | Capacity (rank, target_modules, epochs) marginal effect | Capacity ablation | ✅ done (Run-A vs Run-B); add Run-D (7B) | §4.2 |
| **C** | Cultural-specific data **closes** the gap (H4 proper test) | Main H4 | Run-F (3B on Nemotron+CB) | §4.3 |
| **D** | Effect persists across model sizes | H2 generational covariate | Run-G (7B), Run-H (Llama-3.1-8B) | §4.4 |
| **E** | Korean-pretrained baseline doesn't dominate | Differentiates from "just use Korean LLM" | Run-E (EXAONE) | §4.5 |
| **F** | Retrieval (RAG) vs parametric (QLoRA) — different injection regimes | H4 mechanism comparison | RAG version of Run-F | §4.6 |

All 6 ablations together produce a **2×3 factorial table** in Section 4:

|          | Western base (Qwen2.5) | Korean-pretrained (EXAONE) | Legacy (Llama-3.1-8B) |
|---|---|---|---|
| **Vanilla**      | ✅ baseline | Run-E vanilla | Run-H vanilla |
| **+ Retrieval**  | (W4-W5 task) | (W4-W5 task) | (W4-W5 task) |
| **+ QLoRA cultural** | Run-F | Run-E adapter | Run-H |

That's the **richest experimental design Team 2/4/22 reference teams will see** —
they did single-axis ablations; we have 3 axes × 3 conditions.

---

## 3. Differentiation matrix — vs prior work

| Dimension | MiroFish | Token Pirates v1 | CultureLLM | CAReDiO | Team 2/4/22 | **Ours (v2)** |
|---|---|---|---|---|---|---|
| Market specificity | Generic | Korea+Japan | Generic values | Generic | n/a (CV/NLP topics) | **Korea D2C deep** |
| Persona grounding | Seed report | None | None | None | n/a | **KOSIS-quota + CultureBank** |
| Cultural injection paths | RAG + memory | Prompting only | SFT on values | Retrieval | n/a | **3-way: prompt / RAG / QLoRA** |
| Backbone count | 1 (Qwen-plus) | 1 (GPT-4o-mini) | 1 | 1 | 1-2 | **3 (Qwen, EXAONE, Llama)** |
| Standard Korean benchmark | None | None | None | None | n/a | **KoBBQ + KMMLU + CLIcK** |
| Behavioral validation | Report quality | None | Survey-response | Survey-response | n/a | **OASIS + KOSIS ground truth** |
| Negative result reported | No | n/a | No | No | n/a | **Yes (Section 4.1)** |
| Production deployment | Demo sandbox | Vapor | Research only | Research only | n/a | **ORBT Hermes + OpenCloud API** |
| Autonomous methodology | No | No | No | No | No | **8-agent lab + 3-loop self-eval** |
| Decision-log audit trail | No | No | No | No | No | **Versioned `decisions/`** |

**Six axes of differentiation simultaneously.** Reviewers will struggle to
slot this paper into a single existing bucket — that's the goal.

---

## 4. Updated timeline

### W2 (now) — data acquisition + benchmark establishment

| Day | Task | Owner | Status |
|---|---|---|---|
| Tue 5/26 | Run-D launch (Qwen2.5-7B) | AWS | NOW |
| Tue 5/26 | Korean benchmark eval (KoBBQ + KMMLU) | AWS | RUNNING |
| Tue 5/26 | Brief 03-08 (D2C scenarios + Paper drafts) | Hermes cron | every 2h |
| Wed 5/27 | Run-E launch (EXAONE) | AWS | queued |
| Wed 5/27 | Nemotron-Personas-Korea HF acquisition | data_steward + Sunwoo | escalated |
| Thu 5/28 | CultureBank-Korean filter | data_steward + ambiguity LLM | W2-W3 |
| Fri 5/29 | W2 Friday review — gate G2 (50 scenarios drafted + KG indexed) | Sunwoo | review |

### W3 — main persona generation

- Run-F: Qwen2.5-3B on Nemotron+CultureBank (main H4 test)
- Run-G: Qwen2.5-7B on Nemotron+CultureBank
- Generate 200 personas × 6 conditions × 4 backbones = 4,800 personas
- Daily after-corpus diffs

### W4 — fine-tuning week

- Hyperparam sweeps on best backbone
- Comparative: prompt-only vs RAG vs QLoRA × condition

### W5 — static metrics + Tier C panel

- CAS via 4-model judge panel (Claude Opus + GPT-5 + Gemini 2.5 + Qwen3.6)
- HAD via Hofstede 6D inference
- PDI via BGE-m3 embedding diversity
- JSD vs WVS Wave 7 Korea

### W6 — dynamic sims

- 50 D2C scenarios × 5 trials × 6 conditions × 1 backbone = 1,500 OASIS runs
- BAS composite computation **conditional on R4 decision** (see
  decisions/2026-05-24-known-risks.md): may pivot to CCR/AAS/GCS directional
  reporting per Brief 01's recommendation

### W7 — writer-critic loop

- Hermes brief queue 07-12 already drafts Paper Sections (Intro,
  Related Work, IRB)
- Critic reviews on Hermes
- Sunwoo writes Methods (HANDOFF.md §8 rule)

### W8 — ORBT integration + final

- Hermes tool integration test
- OpenCloud block configuration
- Overleaf PDF generation
- Submit GitHub URL via Google Form (deadline 2026-06-02 — early)

---

## 5. Risk register update

| Risk | Original (2026-05-24) | Updated (2026-05-26) | Mitigation |
|---|---|---|---|
| R1 — Loop A cost optimism | $1-3 → maybe 3× | confirmed: 12-task Hermes cron stayed cheap | ✅ acceptable |
| R2 — PI drift detection | weak | not yet exercised | review W4 Friday |
| R3 — OASIS herd bias | confounds BAS delta | bigger now: BAS composite itself questionable | + R7 below |
| R4 — MEAS↔ground-truth mapping | flagged | **confirmed structural gap** (Brief 01) | **Tier-3 decision: option 2 (drop composite, keep directional)** |
| **R5 (new) — KoAlpaca insufficient** | n/a | confirmed by W3 pilot | Cultural-specific data via W2-W3 acquisition |
| **R6 (new) — 7B backbone disk pressure** | n/a | g6.xlarge 7GB free limit | Pre-quantized variants OR /opt/pytorch deletion |
| **R7 (new) — Hermes cron stability** | n/a | 19 silent fails (TCC), then fixed; 1 working | watch next 24h |

---

## 6. Assignment-requirement integration (COSE461)

Per TA notices captured in `AUTONOMOUS_INTEGRATION.md §6`:

| Requirement | Status |
|---|---|
| GitHub repo `261RCOSE46101` (sunnyxide) | ✅ created + pushed |
| GitHub URL submission by 2026-06-02 (Google Form) | ⏳ Sunwoo action |
| Overleaf template + final report | template not yet pulled into lab; Hermes briefs 07-08 produce Intro + Related Work in Markdown, pandoc → tex pipeline at W7 |
| AWS account responsible use | ✅ documented in decisions/2026-05-24-nxtgen-aws-probe.md |
| AI usage disclosure appendix | ✅ `reports/AI_USAGE_DISCLOSURE.md` template; populate at W7 |
| Code repository with documentation | ✅ public + README, AUTONOMOUS_INTEGRATION.md, HANDOFF.md, all decisions/ |
| Reproducibility | manifest + DVC hash for every artifact (KPI G3) |

### Open assignment questions (need user)

1. **Overleaf template ZIP** — Sunwoo to drop `COSE461_Project_Final_Report_Template__2026_.zip` into `reports/overleaf/` so Hermes Writer can target the exact .tex format
2. **Faculty advisor name** — for IRB Section 2 (currently `<TODO>` in Brief 11 output)
3. **Team Google Form submission timing** — submit early (W2-W3) or wait until paper near final?
4. **Public repo timing** — flip to public after grade release (HANDOFF.md §6 says ~2026-06-30)

---

## 7. Hermes brief queue extensions

Current queue (12 briefs, in `briefs/lab/`):
- 01: MEAS mapping (done — R4 surfaced)
- 02: D2C cosmetics scenarios (done)
- 03-06: D2C scenarios (queued, fires every 2h)
- 07: Paper Intro draft
- 08: Paper Related Work draft
- 09-10: Critic reviews
- 11: IRB protocol draft
- 12: KAIO bibliography

Added by this plan (briefs 13-17 — Sunwoo approve first):
- **13**: MiroFish reference write-up + bibtex entry generation
- **14**: KoAlpaca negative result paper writeup (Section 4.1)
- **15**: Korean cultural training data acquisition strategy (HF gated, license audit)
- **16**: ORBT API contract finalization for W8 integration
- **17**: Paper Discussion section draft (covers R4 BAS pivot honestly)

---

## 8. Decision points for Sunwoo (sorted by deadline)

| Decision | Deadline | Default | Options |
|---|---|---|---|
| **R4: BAS composite fate** | W2 Friday | Option 2 (drop composite, directional only) | 1 / 2 / 3 from Brief 01 |
| **Nemotron HF gated access** | W3 Tuesday | Acquire HF_TOKEN + manual gate request | self / Korea Univ access path |
| **/opt/pytorch deletion (frees 7.7GB)** | Run-D launch | ask permission | yes / no / use pre-quantized 7B |
| **Overleaf ZIP** | W7 | drop into reports/overleaf/ | self / I pull from public link |
| **GitHub Form submission** | 2026-06-02 | sunnyxide URL = current | submit now or later |
| **/mcp slack login refresh** | anytime | retry from claude.ai | confirm or skip |

---

## 9. What gets cited in the paper

Bibtex additions needed (Brief 12 in progress):
- `ji2026mirofish` (MiroFish reference)
- `kaio2026` (need to locate actual citation)
- `exaone2024` (LG AI Research EXAONE 3.0)
- `kmmlu2024` (HAERAE-HUB KMMLU)
- `kobbq2024` (Jin et al. TACL)
- Possibly: ShangFan et al. on KoAlpaca, Beom et al. on KULLM

---

*This is a living document. Update if and only if the underlying empirical
situation changes; otherwise edits are Tier-3 actions requiring
`decisions/<date>-research-plan-revision.md`.*
