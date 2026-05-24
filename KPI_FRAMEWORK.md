# KPI framework — measurable success criteria

> `agents/qa_meta.py` reads this file at boot and on every hourly tick.
> Every metric here is computable from artifacts in `results/`. If a metric
> is not computable yet (e.g., human evaluators not done), the QA Meta agent
> marks it as "pending data" but tracks projected timing.

## 1. Layered KPI structure

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — Research integrity (PI agent owns)                │
│  - RQ being answered? Hypotheses still live?                 │
│  - Data lineage complete? Reproducibility achievable?        │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 — Metric targets (QA Meta + analyst own)            │
│  - Static: CAS, HAD, PDI, JSD                                │
│  - Dynamic: CCR, AAS, GCS, BAS                               │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 — Process KPIs (QA Meta owns)                       │
│  - Pace: % of W-N deliverables done by W-N Friday            │
│  - Cost: daily, weekly, total budget                         │
│  - Critic pass rate; Writer-Critic round count               │
├─────────────────────────────────────────────────────────────┤
│  Layer 4 — Product / ORBT KPIs (Sunwoo owns)                 │
│  - Hermes agent integration test passes                      │
│  - OpenCloud block exposes 6 conditions via API              │
│  - End-to-end latency < 8s per persona                       │
└─────────────────────────────────────────────────────────────┘
```

## 2. Static authenticity metrics

| Metric | Definition | Target (full stack vs vanilla) | Stat test | Hard floor |
|--------|-----------|-------------------------------|-----------|------------|
| **CAS** | Cultural Authenticity Score: mean of 5 native-speaker Likert ratings on (Realism, Plausibility, Idiom, Reasoning, Behavior) per CURE schema | Δ ≥ +0.8 points on 5-pt scale, paired t-test p < 0.01 | Paired t-test, Bonferroni for 6 conditions | Krippendorff α ≥ 0.67 among annotators |
| **HAD** | Hofstede Alignment Delta: RMSE between persona-inferred Hofstede 6D and Korea's official 6D (60,18,39,85,100,29) | Full-stack RMSE ≤ 15; Vanilla RMSE typically > 30 | One-sample t against Korea vector | RMSE must be < 25 for any condition to ship |
| **PDI** | Persona Diversity Index: 1 − mean pairwise cosine similarity of persona embeddings (BGE-m3) within same condition | PDI ≥ 0.45 in full stack, PDI > Vanilla | Bootstrap CI 95% | No single embedding cluster > 25% of pool (anti-stereotyping) |
| **JSD** | Jensen-Shannon Divergence: persona value-question distribution vs WVS Wave 7 Korea | JSD ≤ 0.10 in full stack | Permutation test vs baseline | JSD ≤ 0.20 hard ceiling |

**Aggregation.** The static score per condition is the macro-average of normalized {CAS_norm, 1-HAD_norm, PDI_norm, 1-JSD_norm}, weighted equally. Reported alongside individual metrics; never replacing them.

## 3. Dynamic / behavioral metrics (BAS family)

These metrics are computed from OASIS simulation transcripts under 50 D2C scenarios. Ground truth is from KOSIS consumer surveys, Naver Datalab shopping insights, and KOFICE Hallyu reports.

| Metric | Definition | Target (full stack) | Ground-truth source |
|--------|-----------|---------------------|---------------------|
| **CCR** | Conformity Cascade Rate: fraction of agents who change opinion after exposure to majority view in 단톡방-style simulation | Within 15% of Korean baseline of 0.62 ± 0.08 | KOSIS consumer behavior (2024-2026) |
| **AAS** | Authority Adoption Slope: gradient of adoption curve after celebrity/influencer endorsement event | Within 15% of Naver-Datalab-measured 1.8x lift slope | Naver Datalab shopping insight |
| **GCS** | Group Consensus Speed: median rounds to consensus in chat-room sims | Within 15% of Korean baseline of 4.2 ± 1.1 rounds | KOFICE Hallyu interaction reports |
| **BAS** | Weighted aggregate: BAS = 0.4·(1-|CCR_delta|) + 0.3·(1-|AAS_delta|) + 0.3·(1-|GCS_delta|) | Full stack ≥ 0.80; Vanilla expected ≤ 0.55 | Composite |

OASIS-specific note: a known herd-behavior bias in LLM-based multi-agent sims [@oasis2025] produces inflated CCR across all conditions. We measure relative-to-Vanilla deltas, not absolutes, to control for this.

## 4. Cross-cutting acceptance gates

These are project-level "ship/no-ship" gates. QA Meta agent monitors. If a gate is at risk by the listed checkpoint date, QA Meta auto-proposes scope reduction.

| Gate | Checkpoint | Target | If miss: action |
|------|------------|--------|-----------------|
| **G1: Layer 1+2 data complete** | End of W1 | All manifests present, all hashes verified | Pause W2 work, debug ingestion |
| **G2: KG built + scenarios drafted** | End of W2 | LightRAG indexed, 50 scenarios written, OASIS runnable | Cut scenarios from 50 to 30 |
| **G3: 6×4 cells generated** | End of W3 | 24 cells × 200 personas = 4,800 personas in `results/personas/` | Drop legacy model (Llama-3.1-8B) |
| **G4: QLoRA training done** | End of W4 | Qwen3.6-27B QLoRA checkpoint with eval loss decrease vs base | Skip QLoRA condition, keep prompted only |
| **G5: Static metrics computed** | End of W5 | All 4 static metrics for all cells, with stat tests | Skip 1 backbone to reduce cell count |
| **G6: Dynamic sims complete** | End of W6 | 30 OASIS runs (6 conditions × 5 trials × 1 backbone), BAS computed | Reduce trials from 5 to 3 |
| **G7: Critic-pass on autonomous sections** | End of W7 | Writer-drafted sections all at Critic score ≥ 0.85 | Sunwoo manually rewrites failed sections |
| **G8: ORBT integration test** | W8 | Hermes wrapper API passes integration test | Defer ORBT release to post-submission |

## 5. Process KPIs (operational health of the lab)

| KPI | Target | Owner | Sampling cadence |
|-----|--------|-------|------------------|
| Daily cost burn | ≤ $30 (hard kill at exceed) | budget.py | Continuous |
| Weekly cost burn | ≤ $150 | budget.py | Daily |
| Total cost through W8 | ≤ $400 | budget.py | Daily |
| Task queue throughput | ≥ 80% of dispatched tasks complete within target wall time | qa_meta | Hourly |
| Critic first-pass rate | ≥ 0.5 (half of Writer outputs pass without revision) | qa_meta | Daily |
| Writer-Critic mean rounds | ≤ 2.0 | qa_meta | Per-section |
| Slack digest delivery | 08:00 KST ± 30min, 6 of 7 days/week | librarian | Daily |
| Decision-log coverage | ≥ 95% of Tier 1/2 actions logged | librarian audit | Weekly |
| Manifest coverage of artifacts | 100% | librarian | Weekly |

## 6. Failure cascade rules (when to call it)

QA Meta agent monitors and triggers escalation under these conditions:

| Severity | Trigger | Action |
|----------|---------|--------|
| **Yellow** | One Layer-2 metric off-target at checkpoint | Slack digest flag, no auto-scope-change |
| **Orange** | Two Layer-2 metrics off-target OR one Gate G1-G3 missed | QA Meta proposes scope reduction via Tier-2; Sunwoo approves on Slack |
| **Red** | Three+ metrics off OR Gate G7 (Critic pass) failing on >50% sections OR budget > 0.9× cap | QA Meta pauses autonomous Writer; halts AWS instances; pages Sunwoo |
| **Black** | Layer 1 (research integrity) violation: data lineage broken OR PI agent flags hypothesis drift | Hard kill (`make emergency-stop`), wait for Sunwoo |

## 7. KPIs for the paper itself

The paper is judged by:

| Dimension | Target | Reference |
|-----------|--------|-----------|
| Length | 8-12 pages NeurIPS-style | Team 2 (8p), Team 4 (12p), Team 22 (10p) |
| Math rigor | ≥ 8 numbered equations | Team 2 (eq 1-14), Team 4 (eq for HIES) |
| Baselines compared | ≥ 5 in main results table | Team 22 had 4 baselines + ours |
| Datasets / benchmarks | ≥ 3 distinct evaluation regimes | Team 2 used 5 datasets |
| Ablation studies | ≥ 2 ablations (α hyperparameter equivalent + condition ablation) | Team 4 had α ablation |
| Visualization | ≥ 3 figures (architecture + heatmap + curve) | Team 4 had 7 figures |
| Limitations | Explicit section, ≥ 3 honest limitations | All three reference teams had this |
| Reproducibility | Code repo + decision log + prompts | None of the reference teams had decision logs — we exceed |

## 8. KPI for the methodological contribution (autonomous lab)

This is our differentiator vs reference teams. Judged by:

- **Reproducibility delta**: can a new researcher rerun the entire study from a clean repo + 1 commit? Target: yes, ≤ 1 hour to first task running.
- **Audit trail completeness**: % of paper claims that resolve to a single artifact + decision entry. Target: 100%.
- **Cost transparency**: per-section, per-experiment cost breakdown in appendix. Target: yes.
- **Generalizability**: framework usable for another market (Japan, India) with config changes only. Target: configuration-only path documented in `ORBT_INTEGRATION.md`.

## 9. KPIs for ORBT integration

| Surface | Acceptance criterion | Owner |
|---------|----------------------|-------|
| Hermes `predict_consumer_response(brand, campaign, market)` tool | Returns persona-grounded prediction in ≤ 8s p95 | ORBT eng |
| OpenCloud block: `cultural-persona-grounded-simulation` | Configurable for 6 conditions, exposes BAS subscores | ORBT eng |
| `persona_mapping` module | No longer returns empty for KR market | Sunwoo |
| `intel_v1` KG schema | Adds `cultural_descriptor` node sourced from CultureBank-KR | Sunwoo |
| Cost per inference | ≤ $0.01 per persona via Qwen3.6-27B Q4 on Mac Mini | Lab benchmark |

---

*This document is the canonical source of truth for "are we succeeding?". When in doubt, defer to numbers here over verbal recollection.*
