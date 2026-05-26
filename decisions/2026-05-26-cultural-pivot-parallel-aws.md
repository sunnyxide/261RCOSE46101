# 2026-05-26 — Research contribution pivot + parallel-AWS architecture

## Trigger

Sunwoo (2026-05-26): "우리가 아무것도 안했는데 ... 한국 문화를 잘 이해하거나 다른 지역별로 문화 맥락을 가진 ai로 만들기 위해서 데이터셋도 쓰고?"

Translation: Vanilla-only evaluation is not a research contribution. The PPT promised cultural-grounded persona generation, but our QLoRA runs so far (Run-A/B/D) trained on generic Korean instruction data (KoAlpaca), not cultural data. The cultural contribution slot is still empty.

## Honest scope diff (what we have vs. what the paper needs)

| Layer | Vanilla-only | KoAlpaca-QLoRA (Run-A/B/D) | **Cultural-QLoRA (Run-F+)** |
|---|---|---|---|
| Training corpus | none (vendor SFT only) | KoAlpaca v1.1a (translated Alpaca + KR) | **CultureBank + Hofstede + WVS + Nemotron-Personas-KR** |
| What it teaches | nothing | Korean instruction-following | **Korean cultural reasoning + persona alignment** |
| Contribution type | benchmarking | negative finding (catastrophic forgetting) | **positive contribution** (cultural conditioning works) |
| PPT promise covered | ❌ | ⚠️ partial | ✅ this is the actual deliverable |

## Decision

Pivot W4 to **Cultural-QLoRA with multi-cultural extension**, option **B → stretch to C**:

- **B (committed)**: Train Korean Cultural-QLoRA (Run-F) + one comparison culture, Japanese (Run-G), to show cross-cultural shift is measurable.
- **C (stretch)**: Extend to US (Run-H) + CN (Run-I) for 4-way Hofstede heatmap, contingent on B finishing in time and AWS credits remaining.

## Architecture: 2-instance parallel AWS + Mac orchestration

```
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│ AWS-A  (existing, IP 34.224...) │    │ AWS-B  (new, IP TBD)            │
│ g6.xlarge L4 24GB / 48GB EBS    │    │ g6.xlarge L4 24GB / 48GB EBS    │
├──────────────────────────────────┤    ├──────────────────────────────────┤
│ KR pipeline:                    │    │ JP pipeline:                    │
│  1. Cultural-KR dataset build   │    │  1. Cultural-JP dataset build   │
│  2. Run-F: Qwen-3B + KR rank32  │    │  2. Run-G: Qwen-3B + JP rank32  │
│  3. KoBBQ/HAE-RAE/CLIcK + WVS-KR│    │  3. JBBQ/JMMLU + WVS-JP         │
│ Phase 2 (if B succeeds):        │    │ Phase 2 (if B succeeds):        │
│  4. Run-H: US Cultural-QLoRA    │    │  4. Run-I: CN Cultural-QLoRA    │
└──────────────┬───────────────────┘    └─────────────────┬────────────────┘
               │                                          │
               └────────────┬─────────────────────────────┘
                            ▼
              ┌─────────────────────────────────┐
              │ Mac (local — orchestration)     │
              │  • API baselines (continues)    │
              │  • CAS LLM-judge (GPT-5/Claude) │
              │  • WVS KS-test distribution     │
              │  • Hofstede 6D shift heatmap    │
              │  • Paper LaTeX + figures        │
              └─────────────────────────────────┘
```

### Why parallel beats serial

Serial 4-culture: 4 × ~4h = ~16h.
Parallel 2-instance: 2 × (~4h + ~4h) = **~8h**, 50% reduction.

### Disk solution

48 GiB EBS is the real bottleneck (not VRAM — L4 24GB can hold 32B at 4-bit).

Path: Each instance handles **one culture's full pipeline** so disk pressure is local. After phase 1 (KR/JP) completes, clear caches, then phase 2 (US/CN). At any time only:
- 1 base model (3B FP16 ~6GB)
- 1-2 adapters (~1GB each)
- 1 dataset (~2GB)
- HF cache headroom (~10GB)

Stays well under 48 GiB.

Optional upgrade: EBS resize to 100GB ($5/mo) if we want to keep 7B FP16 + 14B in cache simultaneously.

## Cultural dataset construction (delegated to Hermes briefs 06-10)

| Source | KR | JP | US | CN | Use |
|---|---|---|---|---|---|
| CultureBank | ~500 KR descriptors | ~500 JP | ~500 US | ~500 CN | Cultural facts/practices |
| Hofstede 6D | IDV=18, UAI=85, LTO=100, MAS=39 | IDV=46, UAI=92, LTO=88, MAS=95 | IDV=91, UAI=46, LTO=26, MAS=62 | IDV=20, UAI=30, LTO=87, MAS=66 | System prompt conditioning |
| WVS Wave 7 | KR cohort (~1.2K resp) | JP (~1.4K) | US (~2.6K) | CN (~3.0K) | Gold-label survey responses for KS-test |
| Nemotron-Personas | Korea variant | - (synth ourselves) | - | - | Persona demonstration |
| Bias mitigation | KoBBQ train split | JBBQ train | BBQ train | - | Bias-aware tuning |

**Output**: per-culture jsonl, ~10K-20K instructions each, in `data/cultural/<culture>/train.jsonl`.

## Evaluation matrix

For each culture C ∈ {KR, JP, US, CN}, compare three models:

| Model | Description |
|---|---|
| Vanilla-3B | Off-the-shelf Qwen2.5-3B-Instruct |
| KoAlpaca-3B (Run-A) | Generic Korean instruction-tuned (reference baseline) |
| Cultural-C-3B (Run-F/G/H/I) | Our cultural-QLoRA for culture C |

**Metrics**:
1. **Bias** — KoBBQ/JBBQ/BBQ score (lower-is-better stereotype reinforcement)
2. **Cultural knowledge** — HAE-RAE/CLIcK (KR), JMMLU (JP), MMLU (US), CMMLU (CN)
3. **WVS distribution alignment** — KS test between Cultural-C generations and WVS-C survey responses (paper's main contribution)
4. **CAS (Cultural Alignment Score)** — Tier A=GPT-5, Tier B=Claude Opus 4.7 LLM-judge rates persona authenticity (0-5 scale)
5. **Cross-cultural shift** — Hofstede 6D probe: does Cultural-KR shift toward (low IDV, high UAI) vs Cultural-US shift toward (high IDV, low UAI)?

## Paper-grade story (what reviewers will see)

> "Off-the-shelf instruction-tuned LLMs over-represent Anglo cultural priors even on Korean prompts (Finding 1: GPT-5 31% KoBBQ bias > Vanilla-7B-Qwen 24%). Generic Korean instruction-tuning (KoAlpaca) causes catastrophic forgetting on Korean factual knowledge (Finding 2: -X% KMMLU). **Cultural-QLoRA with curated cultural training data shifts model behavior toward target-culture WVS distributions (Finding 3, KS-stat reduction Δ=Y), generalizes across 4 cultures (Finding 4, Hofstede shift heatmap), and improves persona authenticity scored by LLM judges (Finding 5, CAS +Z points).** The same architecture is plug-and-play across cultures, with no per-culture pretraining required."

## Hermes/OpenCloud usage

**Keep both running.** Redirect, don't pause.
- Hermes briefs 06-10 → cultural data prep (replaces analysis briefs)
- OpenCloud → code review for cultural_qlora_train.py and dataset builders before launch

## What Sunwoo needs to do

1. **Launch AWS-B** (g6.xlarge, same ku-lbj-key.pem, us-east-1)
2. **Send IP** to me — I'll bootstrap it identically to A
3. Decide on EBS resize: keep 48GB per instance (each handles 1 culture at a time) OR resize one/both to 100GB (more headroom for 7B/14B experiments). Default = stay at 48GB unless 14B becomes critical.

## What runs while waiting

- Mac: phase1_extended_eval continues (API baselines + extended local eval)
- AWS-A: phase1 5-way evaluation continues
- I prep cultural dataset builder + cultural_qlora_train script
- Hermes: brief 06 (CultureBank-KR extraction)

## References
- PPT divergence analysis: `decisions/2026-05-26-ppt-vs-current-divergence-analysis.md`
- Quantization confound (to be resolved alongside): `decisions/2026-05-26-quantization-confound.md`
- Controlled study findings (will be revised post-W4): `decisions/2026-05-26-controlled-study-findings.md`
