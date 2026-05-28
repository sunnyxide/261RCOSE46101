"""Cultural-QLoRA training — fork of qlora_train.py with cultural dataset support.

Differences from qlora_train.py:
  - Trains on data/cultural/{culture}/train.jsonl produced by build_cultural_dataset.py
  - Uses system-prompt-conditioned chat format (Hofstede 6D in system message)
  - Defaults to rank 32 all-linear (more capacity for cultural conditioning than KoAlpaca's rank 16)
  - Saves per-culture run dir: runs/run-{F,G,H,I}-{culture}-{base}-{ts}/

Usage:
  python scripts/cultural_qlora_train.py \
      --culture kr \
      --base-model Qwen/Qwen2.5-3B-Instruct \
      --run-id run-f-kr-3b-rank32-alllinear-$(date -u +%Y%m%dT%H%M%SZ) \
      --num-epochs 2 --lora-rank 32

Run on AWS-A (kr), AWS-B (jp) in parallel.
"""
import argparse, json, os, time
from pathlib import Path

import torch
from datasets import Dataset
from transformers import (AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
                          TrainingArguments, Trainer, DataCollatorForLanguageModeling)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, TaskType

ROOT = Path(__file__).resolve().parent.parent

def load_quantized_base(model_id):
    prequantized = ("-bnb-4bit" in model_id.lower()) or ("4bit" in model_id.lower())
    tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    kw = {"device_map": "auto", "attn_implementation": "sdpa", "trust_remote_code": True}
    if not prequantized:
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16,
        )
    else:
        kw["torch_dtype"] = torch.bfloat16
    model = AutoModelForCausalLM.from_pretrained(model_id, **kw)
    model = prepare_model_for_kbit_training(model)
    return tok, model

def attach_lora(model, rank, target):
    if target == "attn":
        modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
    elif target == "all_linear":
        modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                   "gate_proj", "up_proj", "down_proj"]
    else:
        raise ValueError(f"unknown target: {target}")
    cfg = LoraConfig(
        r=rank, lora_alpha=rank*2, lora_dropout=0.05, bias="none",
        target_modules=modules, task_type=TaskType.CAUSAL_LM,
    )
    return get_peft_model(model, cfg)

def format_cultural_record(record, tokenizer, max_length=1024):
    """Convert a cultural-dataset record into a tokenized chat-format sample."""
    msgs = [
        {"role": "system", "content": record["system"]},
        {"role": "user",   "content": record["instruction"] +
            (("\n\n" + record["input"]) if record.get("input") else "")},
        {"role": "assistant", "content": record["output"]},
    ]
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    enc = tokenizer(text, truncation=True, max_length=max_length, padding=False)
    enc["labels"] = enc["input_ids"].copy()
    return enc

def load_cultural_jsonl(path, tokenizer, max_samples=None, max_length=1024):
    """Read jsonl and tokenize. Returns datasets.Dataset."""
    rows = []
    with open(path) as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if max_samples and len(rows) >= max_samples:
                break
    tokenized = [format_cultural_record(r, tokenizer, max_length) for r in rows]
    return Dataset.from_list(tokenized)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--culture", required=True,
                    help="culture code or ablation variant (e.g. kr, kr_idv_only)")
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-3B-Instruct")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--max-samples", type=int, default=None)
    ap.add_argument("--num-epochs", type=int, default=2)
    ap.add_argument("--lora-rank", type=int, default=32)
    ap.add_argument("--lora-target", default="all_linear", choices=["attn", "all_linear"])
    ap.add_argument("--learning-rate", type=float, default=2e-4)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--max-length", type=int, default=1024)
    ap.add_argument("--save-steps", type=int, default=200)
    ap.add_argument("--eval-steps", type=int, default=400)
    ap.add_argument("--seed", type=int, default=42,
                    help="random seed for HF Trainer (shuffle/dropout); multi-seed runs use 123, 7777")
    args = ap.parse_args()

    t0 = time.time()
    train_path = ROOT / "data" / "cultural" / args.culture / "train.jsonl"
    if not train_path.exists():
        raise FileNotFoundError(
            f"Cultural train.jsonl not found at {train_path}. "
            f"Run scripts/build_cultural_dataset.py --culture {args.culture} first."
        )

    print(f"[init] base={args.base_model} culture={args.culture} run_id={args.run_id}", flush=True)
    tok, model = load_quantized_base(args.base_model)
    model = attach_lora(model, args.lora_rank, args.lora_target)
    model.print_trainable_parameters()

    print(f"[{time.time()-t0:.1f}s] loading cultural train set from {train_path}", flush=True)
    ds = load_cultural_jsonl(train_path, tok,
                              max_samples=args.max_samples,
                              max_length=args.max_length)
    print(f"[{time.time()-t0:.1f}s] dataset size: {len(ds)}", flush=True)

    out_dir = ROOT / "runs" / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    targs = TrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        bf16=True,
        seed=args.seed,
        data_seed=args.seed,
        logging_steps=20,
        save_steps=args.save_steps,
        save_total_limit=2,
        report_to=[],
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        dataloader_num_workers=2,
    )

    collator = DataCollatorForLanguageModeling(tok, mlm=False)
    trainer = Trainer(model=model, args=targs, train_dataset=ds, data_collator=collator)
    print(f"[{time.time()-t0:.1f}s] training start", flush=True)
    trainer.train()
    print(f"[{time.time()-t0:.1f}s] training done", flush=True)

    adapter_dir = out_dir / "adapter_final"
    model.save_pretrained(str(adapter_dir))
    tok.save_pretrained(str(adapter_dir))

    summary = {
        "run_id": args.run_id,
        "culture": args.culture,
        "base_model": args.base_model,
        "lora_rank": args.lora_rank,
        "lora_target": args.lora_target,
        "num_epochs": args.num_epochs,
        "train_size": len(ds),
        "elapsed_sec": round(time.time() - t0, 1),
        "adapter_path": str(adapter_dir),
    }
    with open(out_dir / "run_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[{time.time()-t0:.1f}s] DONE — adapter at {adapter_dir}", flush=True)

if __name__ == "__main__":
    main()
