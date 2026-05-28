# AWS performance plan — L4-optimized W3-W4 training schedule

> Date: 2026-05-24
> Status: live plan, updated by QA Meta at every Friday review
> Supersedes: AUTONOMOUS_INTEGRATION.md §5 cost arithmetic (which assumed g5.2xlarge)
> Constraint inputs: decisions/2026-05-24-nxtgen-aws-probe.md

This document answers: *given an NVIDIA L4 (23 GB VRAM, compute 8.9), 15 GB
system RAM, 14 GB free disk, 97.92 credits at 1.53/hr, and a 4-hour auto-stop
timer, what is the fastest sequence of training runs that answers H1-H4?*

The answer is **not** "biggest model, longest training". It's **smaller
backbones, more configs, more eval coverage, all in parallel where possible**.

---

## 1. The actual constraints

| Constraint | Value | Implication |
|------------|-------|-------------|
| GPU VRAM | 22 GiB free (L4) | Q4 model + 2K context + rank-16 LoRA fits comfortably up to ~14B; 27B is tight only with offloading |
| System RAM | 15 GiB | Model weights stream from disk to GPU; 14 GB headroom for tokenizer, dataloader, accelerate caches |
| Swap | 8 GiB | Allocated 2026-05-24 as OOM safety net |
| Free disk | 14 GiB | Holds: 1 model snapshot (~4-15 GiB) + dataset cache + ~3 GiB LoRA adapter checkpoints |
| Auto-stop | 4 hours | Every training run MUST checkpoint at most every 30 min and resume cleanly |
| Credits | 97.92 (team pool ≈195.84) | Hard kill at 75 credits; planned spend ≤40 |
| Compute capability | 8.9 (Ada Lovelace) | Flash Attention 2 works, bfloat16 + fp8 supported |

The 4-hour auto-stop is the single hardest constraint. Every run must either
(a) finish inside 4 hours, or (b) checkpoint, resume after Sunwoo extends.

---

## 2. Backbone matrix (revised from HANDOFF.md §3)

| Backbone | Params | Q4 disk | Q4 VRAM | Fit on L4? | Use case |
|----------|--------|---------|---------|------------|----------|
| Qwen2.5-0.5B | 0.5B | 0.4 GB | 1.5 GB | ✅ trivial | Smoke testing pipeline |
| Qwen2.5-3B-Instruct | 3B | 2 GB | 4 GB | ✅ easy | Quick hyperparam sweep, baseline |
| **Qwen3-7B-Instruct** | 7B | 4.5 GB | 8 GB | ✅ comfortable | **Primary QLoRA target (H4 main run)** |
| Gemma-2-9B-it | 9B | 5.5 GB | 11 GB | ✅ good | Secondary QLoRA (H4 robustness) |
| Llama-3.1-8B-Instruct | 8B | 5 GB | 9 GB | ✅ good | Legacy condition (if W4 budget allows) |
| Qwen3.6-27B (FP8 inference only) | 27B | 16 GB | 22 GB | ⚠ inference yes, QLoRA no | Eval-only via API panel |
| Gemma 4 26B MoE | 26B | 14 GB | 20 GB | ⚠ inference only | Eval-only via API panel |

**Decision:** primary QLoRA target is **Qwen3-7B-Instruct**. The H4 hypothesis
("QLoRA closes ≥50% of vanilla → full-stack-retrieval gap") is measured
*within* the same backbone — bigger model isn't needed and would crowd out
hyperparam exploration. Qwen3.6-27B remains in the paper as an **inference-only
condition** evaluated by the panel API at the standard $0.005/persona rate.

---

## 3. Per-run hyperparams (sized for L4 + 4h auto-stop)

```yaml
qlora_default:
  backbone: Qwen3-7B-Instruct
  quantization: nf4_double_quant   # bitsandbytes 0.44.1, paged optimizer
  attention_impl: flash_attention_2  # confirmed supported on compute 8.9
  dtype_compute: bfloat16
  max_seq_len: 2048
  rank: 16
  alpha: 32
  target_modules: [q_proj, k_proj, v_proj, o_proj]   # attn-only, ~50% of training cost vs all-linear
  lora_dropout: 0.05
  optimizer: paged_adamw_8bit
  learning_rate: 2.0e-4
  scheduler: cosine
  warmup_ratio: 0.03
  batch_size: 4
  grad_accum_steps: 4              # effective batch 16, fits in 22 GiB
  num_train_epochs: 3.0
  save_steps: 200                  # ~every 20 min on L4 → survives auto-stop
  save_total_limit: 3
  logging_steps: 10
  bf16: true
  gradient_checkpointing: true
  group_by_length: true
  report_to: tensorboard
  output_dir: ~/orbt-research-lab/runs/<run_id>/checkpoints
```

**Expected training time per run** (Nemotron+CultureBank Korean subset ≈ 50K
training pairs, 2K seq):

- Forward + backward at 1.5 it/s on L4 with bf16 + flash-attn-2
- 50K samples / (effective batch 16) = 3,125 steps/epoch
- 3 epochs = 9,375 steps
- At 1.5 it/s = ~6,250 seconds ≈ **1h 45m**
- Plus eval + checkpointing overhead = **~2 hours per run**

→ 2h per run leaves 2h buffer inside the 4h auto-stop. Comfortable.

---

## 4. Run schedule (W3 — the QLoRA week)

W3 budget: 8 training hours total ≈ 12 credits. Half the projection in
AUTONOMOUS_INTEGRATION.md §5; we recovered headroom by going to a smaller
backbone.

| Slot | Day | Run | Backbone | Diff vs default | Purpose | Credits |
|------|-----|-----|----------|-----------------|---------|---------|
| 1 | Mon | smoke | Qwen2.5-0.5B | epochs=0.1, batch=2 | End-to-end pipeline validation, OOM probe | 0.05 |
| 2 | Mon | bench-vanilla | Qwen3-7B-Instruct | no QLoRA, eval only | Vanilla CAS/HAD baseline on L4 | 0.5 |
| 3 | Tue | qlora-default | Qwen3-7B-Instruct | (default config) | H4 primary run | 3.1 |
| 4 | Wed | qlora-rank32 | Qwen3-7B-Instruct | rank=32, alpha=64 | Rank ablation (do bigger adapters help?) | 3.1 |
| 5 | Thu | qlora-allmodules | Qwen3-7B-Instruct | target_modules += [gate, up, down] | All-linear vs attn-only ablation | 3.6 |
| 6 | Fri | qlora-gemma | Gemma-2-9B-it | default config, backbone swap | H4 robustness (does effect persist?) | 3.5 |
| | **Total** | | | | **13.85 credits**, headroom **61 credits** |

If any slot 1-2 fails, halt and re-plan. If slot 3 passes but slot 4 doesn't
move the needle (rank-32 ≈ rank-16 within noise), skip slot 5 (don't sweep
more knobs on the same backbone).

---

## 5. Run schedule (W4 — eval + benchmark week)

| Slot | Day | Job | Compute | Credits |
|------|-----|-----|---------|---------|
| 1 | Mon | Inference benchmark: generate 200 personas/condition × 6 conditions = 1,200 personas, all 6 backbones | L4 4h | 6 |
| 2 | Tue | Korean cultural benchmark eval (KoBBQ + CLIcK + HAERAE) on Vanilla vs QLoRA Qwen3-7B | L4 2h | 3 |
| 3 | Wed | Hard cases for the LLM judge panel: 200 personas where Vanilla and full-stack disagree most | local + panel API | n/a (panel cost ~$3) |
| 4 | Thu | Spot-check ablation: turn off LightRAG vs turn off Nemotron — which contributes more? | L4 3h | 4.5 |
| | **Total** | | **13.5 credits**, cumulative **27.35** |

---

## 6. Resume protocol — surviving the 4h auto-stop

Every training script writes `last_checkpoint.txt` after each save. On
restart:

1. `train.py` reads `last_checkpoint.txt`
2. If present, passes `resume_from_checkpoint=<path>` to `trainer.train()`
3. Otherwise starts from step 0

The 30-min healthcheck cron (`scripts/healthcheck_30min.sh`) probes for
`train_pid` on the instance every tick. If the cron sees:

- AWS UP + train_pid present → all good
- AWS UP + train_pid absent + last checkpoint < 30 min old → assume just
  finished or just paused; no action
- AWS UP + train_pid absent + last checkpoint > 90 min old → orange band,
  alert Sunwoo (training crashed silently)
- AWS DOWN + last checkpoint < auto_stop_window → expected (auto-stop
  fired), green
- AWS DOWN persistent for 3 ticks (90 min) → yellow, Slack reminder

Sunwoo's role: when AWS DOWN, log in to NxtGen portal and click "시작"
(start). The training resumes from checkpoint automatically.

---

## 7. Local Mac compute usage policy

Per Sunwoo's instruction (2026-05-24): "로컬 컴퓨트 파워는 사용가능한
범위내에서만 쓰거나 최대한 피해". Translation: minimize Mac CPU/GPU use,
push everything possible to AWS.

| Workload | Where it runs | Why |
|----------|---------------|-----|
| QLoRA training | AWS L4 | Only place with GPU big enough |
| Inference benchmarking | AWS L4 | Same GPU as training, no transfer cost |
| OASIS social simulation | AWS L4 (added W5) | CPU-bound but Mac is shared with other agents |
| LLM judge panel (cloud judges) | API calls from Mac | Trivial CPU, network-bound |
| LLM judge panel (Qwen judge) | AWS L4 | Avoid eating Mac inference capacity |
| KOSIS / Naver / KOFICE data fetch | Mac (small, network) | Trivial |
| pandas/polars metric compute | Mac (small) | <30s tasks, no real load |
| LightRAG ingestion + Neo4j | Mac docker | Already running, persistent |
| Writer + Critic LLM calls | API from Mac | Network-bound |
| 30-min healthcheck cron | Mac launchd | ~2s CPU per tick, negligible |

**The Mac becomes a thin client.** Heavy lifting is on AWS.

---

## 8. Cross-job safety (do not interfere with existing agents)

Confirmed running on the Mac (2026-05-24 probe):

- `com.orbt.ralph-lab-24x7` launchd (PID 60883, 60886 caffeinate)
- `com.orbt.daily-growth` launchd
- `ai.hermes.gateway` launchd (PID 2030)
- 5 tmux sessions: nl-paper-deep-dive-20260521, patent-overnight-20260520,
  rd-ontology-framework-20260521, rd-weekly-research-20260521,
  us-bd-overnight-20260520

Rules for this research lab:

1. NEVER `pkill`, `kill -9`, or `pgrep | xargs kill` anything not owned by
   us. Use `pgrep -f research-lab` to target only our processes.
2. ALL new launchd jobs use `com.orbt.research-lab.*` namespace.
3. Lab orchestrator state lives at `data/orchestrator.db` — separate from
   any other agent's database.
4. Slack posts go to `C0ASJUD7JJX` (hermes-home, Sunwoo's personal channel)
   for now. Move to a dedicated `#orbt-research-lab` channel once Sunwoo
   creates it.
5. Mac swap pressure: do not run anything > 4 GB resident on the Mac while
   training is active on AWS. `htop` snapshot in healthcheck cron will flag
   if Mac memory pressure hits 70%.
6. CPU contention: the lab does NOT spawn parallel orchestration locally.
   All concurrency is on AWS or in cloud API calls. Mac concurrency: serial
   per-task scheduler ticks only.

---

## 9. KPI re-anchored for L4 + Qwen3-7B (replaces some HANDOFF.md numbers)

| Metric | Old target (HANDOFF.md) | New L4-anchored target | Why changed |
|--------|------------------------|------------------------|-------------|
| H4: CAS gap closure | ≥50% on Qwen3.6-27B | ≥50% on Qwen3-7B (primary), reported also on Gemma-2-9B | 27B can't QLoRA on 15 GiB host RAM. 7B is the realistic primary |
| Total credit spend | $400 USD | 40 NxtGen credits (~$60 USD equivalent) | g6.xlarge is 1.53 cr/hr; the team only needs ~26 hours of GPU |
| Run wall-clock | 16h max per QLoRA | 2h typical, 4h max per QLoRA | Smaller backbone trains faster |
| Number of QLoRA runs | 1-2 | 3-4 (rank + module + backbone ablations) | Credit headroom allows broader sweep |

The headline claims in MOTIVATION_v2.md and KPI_FRAMEWORK.md remain
unchanged. The mechanism is just sized correctly for the actual GPU.

---

## 10. Triggers for re-planning (read by qa_meta hourly)

QA Meta agent escalates this plan to Sunwoo's Friday review if any of:

- Smoke run (slot 1) fails with non-OOM error → pipeline bug, halt training
- bench-vanilla CAS shows <0.5 Likert gap to full-stack (slot 2) → H1 itself
  is in trouble; QLoRA story matters less, pivot W3 to retrieval ablation
- Any QLoRA run shows training_loss not decreasing across 1k steps → bad
  hyperparams, kill + restart with smaller LR
- Cumulative credit spend > 30 by end of W3 Wednesday → on pace for ≥45,
  cancel slot 6 (Gemma backbone)
- Two consecutive 4h auto-stops without Sunwoo extending → switch to
  smaller (3B) backbone so each run fits in one window
- Mac memory pressure >70% per healthcheck for 3 consecutive ticks →
  pause local Critic loop until pressure releases
