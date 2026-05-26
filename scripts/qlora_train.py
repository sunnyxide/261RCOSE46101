"""QLoRA training script — pilot run on Korean instruction data.

Trains a LoRA adapter on Qwen2.5-3B-Instruct against KoAlpaca-v1.1a.
Pilot for the H4 hypothesis run scheduled for W4 (which will use
Nemotron-Personas-Korea + CultureBank-Korean once W1 data ingest completes).

The pipeline this validates is the same one W4 will run; only the dataset
changes. So a successful pilot de-risks the critical-path W4 training.

Output:
- runs/<run_id>/checkpoints/        — LoRA adapter weights, eval per step
- runs/<run_id>/logs/train.log      — stdout + final metrics
- runs/<run_id>/spec.json           — exact config for reproducibility
- runs/<run_id>/last_checkpoint.txt — for resume-after-4h-auto-stop

Resilience:
- Checkpoint every 100 steps (saves last 3)
- If KeyboardInterrupt or instance kill, resume picks up from
  resume_from_checkpoint=<last_dir> on next launch

Cost on L4 (1.53 credits/hr): ~1.5h * 1.53 = 2.3 credits.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--base-model", default="Qwen/Qwen2.5-3B-Instruct")
    p.add_argument("--dataset", default="beomi/KoAlpaca-v1.1a")
    p.add_argument("--run-id", default=time.strftime("pilot-koalpaca-%Y%m%dT%H%M%SZ"))
    p.add_argument("--output-root", default=os.path.expanduser("~/orbt-research-lab/runs"))
    p.add_argument("--max-samples", type=int, default=10000,
                   help="Subsample dataset to this many examples for pilot timing.")
    p.add_argument("--max-seq-len", type=int, default=1024)
    p.add_argument("--lora-rank", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--grad-accum", type=int, default=4)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--num-epochs", type=float, default=1.0)
    p.add_argument("--save-steps", type=int, default=100)
    p.add_argument("--logging-steps", type=int, default=10)
    p.add_argument("--eval-steps", type=int, default=200)
    p.add_argument("--resume", action="store_true", help="Resume from last checkpoint if present.")
    p.add_argument("--prequantized", action="store_true",
                   help="Base model is already bnb-4bit pre-quantized (e.g., unsloth/*-bnb-4bit). Skip BnB config.")
    return p.parse_args()


def load_quantized_base(model_id: str, prequantized: bool = False):
    kwargs = {
        "device_map": "auto",
        "attn_implementation": "sdpa",
    }
    if not prequantized:
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
    else:
        # Pre-quantized models (unsloth/*-bnb-4bit) already have the BnB config
        # baked into config.json; passing BitsAndBytesConfig again causes conflicts.
        kwargs["torch_dtype"] = torch.bfloat16
    model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    return model


def attach_lora(model, rank: int, alpha: int):
    cfg = LoraConfig(
        r=rank,
        lora_alpha=alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    peft_model = get_peft_model(model, cfg)
    return peft_model


def format_koalpaca(example: dict) -> dict:
    """KoAlpaca columns: instruction, input, output, url. Render Qwen2.5 chat format."""
    user_msg = example["instruction"]
    if example.get("input"):
        user_msg = f"{user_msg}\n\n{example['input']}"
    return {
        "messages": [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": example["output"]},
        ]
    }


def tokenize_batched(tokenizer, max_len: int):
    def _fn(batch):
        texts = []
        for msgs in batch["messages"]:
            text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
            texts.append(text)
        out = tokenizer(
            texts,
            truncation=True,
            max_length=max_len,
            padding=False,
            return_tensors=None,
        )
        # DataCollatorForLanguageModeling(mlm=False) clones input_ids to labels
        # automatically AND pads both consistently. Setting labels here causes
        # excessive-nesting errors during collation.
        return out

    return _fn


def find_last_checkpoint(ckpt_dir: Path) -> str | None:
    if not ckpt_dir.exists():
        return None
    cands = sorted(
        [p for p in ckpt_dir.iterdir() if p.is_dir() and p.name.startswith("checkpoint-")],
        key=lambda p: int(p.name.split("-")[1]),
    )
    return str(cands[-1]) if cands else None


def main() -> int:
    args = parse_args()
    run_dir = Path(args.output_root) / args.run_id
    ckpt_dir = run_dir / "checkpoints"
    log_dir = run_dir / "logs"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Persist spec for reproducibility
    (run_dir / "spec.json").write_text(json.dumps(vars(args), indent=2))
    print(f"[init] run_id={args.run_id}", flush=True)
    print(f"[init] output={run_dir}", flush=True)

    t0 = time.time()
    print(f"[{time.time()-t0:.1f}s] loading tokenizer + base model", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = load_quantized_base(args.base_model, prequantized=args.prequantized)
    print(f"[{time.time()-t0:.1f}s] base loaded, VRAM={torch.cuda.memory_allocated()/1024**3:.2f} GiB",
          flush=True)

    model = attach_lora(model, args.lora_rank, args.lora_alpha)
    trainable, total = 0, 0
    for p in model.parameters():
        total += p.numel()
        if p.requires_grad:
            trainable += p.numel()
    print(f"[{time.time()-t0:.1f}s] LoRA attached: {trainable:,}/{total:,} "
          f"= {100*trainable/total:.3f}% trainable", flush=True)

    print(f"[{time.time()-t0:.1f}s] loading dataset {args.dataset}", flush=True)
    raw = load_dataset(args.dataset, split="train")
    if args.max_samples and len(raw) > args.max_samples:
        raw = raw.shuffle(seed=42).select(range(args.max_samples))
    print(f"[{time.time()-t0:.1f}s] {len(raw):,} examples (sampled from full set)", flush=True)

    formatted = raw.map(format_koalpaca, remove_columns=raw.column_names)
    # Train / eval split: 95/5
    splits = formatted.train_test_split(test_size=0.05, seed=42)
    train_ds = splits["train"].map(
        tokenize_batched(tokenizer, args.max_seq_len),
        batched=True, batch_size=64, remove_columns=["messages"],
    )
    eval_ds = splits["test"].map(
        tokenize_batched(tokenizer, args.max_seq_len),
        batched=True, batch_size=64, remove_columns=["messages"],
    )
    print(f"[{time.time()-t0:.1f}s] tokenized: train={len(train_ds)}, eval={len(eval_ds)}", flush=True)

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    targs = TrainingArguments(
        output_dir=str(ckpt_dir),
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        bf16=True,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=3,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        report_to="none",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        dataloader_pin_memory=False,
        optim="paged_adamw_8bit",
        max_grad_norm=0.3,
        group_by_length=True,
        seed=42,
    )

    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=collator,
    )

    resume = None
    if args.resume:
        resume = find_last_checkpoint(ckpt_dir)
        if resume:
            print(f"[{time.time()-t0:.1f}s] resuming from {resume}", flush=True)

    print(f"[{time.time()-t0:.1f}s] starting train()", flush=True)
    train_result = trainer.train(resume_from_checkpoint=resume)
    print(f"[{time.time()-t0:.1f}s] train() done", flush=True)

    eval_metrics = trainer.evaluate()
    print(f"[{time.time()-t0:.1f}s] eval: {eval_metrics}", flush=True)

    final_adapter = run_dir / "adapter_final"
    trainer.model.save_pretrained(str(final_adapter))
    tokenizer.save_pretrained(str(final_adapter))
    (run_dir / "last_checkpoint.txt").write_text(str(final_adapter))

    summary = {
        "run_id": args.run_id,
        "base_model": args.base_model,
        "dataset": args.dataset,
        "n_train": len(train_ds),
        "n_eval": len(eval_ds),
        "final_train_loss": float(train_result.metrics.get("train_loss", -1)),
        "final_eval_loss": float(eval_metrics.get("eval_loss", -1)),
        "perplexity": float(torch.exp(torch.tensor(eval_metrics.get("eval_loss", float("inf"))))),
        "trainable_params": trainable,
        "total_params": total,
        "trainable_pct": round(100 * trainable / total, 4),
        "total_sec": round(time.time() - t0, 1),
        "converged": bool(train_result.metrics.get("train_loss", float("inf")) < 2.0),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    # Sentinels for aws_qlora.py polling
    print(f"FINAL_TRAIN_LOSS={summary['final_train_loss']:.4f}")
    print(f"FINAL_EVAL_LOSS={summary['final_eval_loss']:.4f}")
    print(f"CONVERGED={summary['converged']}")
    print(f"PERPLEXITY={summary['perplexity']:.2f}")
    print(f"TRAINING_COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
