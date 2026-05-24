"""Run the same 60 prompts as the baseline through the QLoRA-trained model.
Compare side-by-side with vanilla baseline to surface H4-relevant differences.

Reads:
- ~/orbt-research-lab/results/baselines/qwen2.5-3b-vanilla-corpus.json (the BEFORE)
- The latest LoRA adapter from ~/orbt-research-lab/runs/pilot-koalpaca-*/adapter_final

Writes:
- ~/orbt-research-lab/results/baselines/qwen2.5-3b-qlora-corpus.json (the AFTER)
- ~/orbt-research-lab/results/baselines/before_after_diff.md (human-readable)
"""
import json, os, sys, time, glob
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

t0 = time.time()
ROOT = os.path.expanduser("~/orbt-research-lab")

# Find the latest adapter
adapters = sorted(glob.glob(f"{ROOT}/runs/pilot-koalpaca-*/adapter_final"))
if not adapters:
    print("ERROR: no adapter found"); sys.exit(2)
adapter_path = adapters[-1]
print(f"[init] adapter: {adapter_path}", flush=True)

# Load BEFORE corpus
before_path = f"{ROOT}/results/baselines/qwen2.5-3b-vanilla-corpus.json"
with open(before_path) as f:
    before = json.load(f)
print(f"[init] before corpus: {len(before['generations'])} prompts", flush=True)

# Load base + adapter
mid = "Qwen/Qwen2.5-3B-Instruct"
tok = AutoTokenizer.from_pretrained(mid)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                          bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
base = AutoModelForCausalLM.from_pretrained(mid, quantization_config=bnb, device_map="auto",
                                              attn_implementation="sdpa")
model = PeftModel.from_pretrained(base, adapter_path)
model.eval()
print(f"[{time.time()-t0:.1f}s] base+adapter loaded, VRAM={torch.cuda.memory_allocated()/1024**3:.2f} GiB",
      flush=True)

after_gens = []
for i, g in enumerate(before["generations"]):
    msgs = [{"role": "user", "content": g["prompt"]}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inp = tok(text, return_tensors="pt").to("cuda")
    gt = time.time()
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=220, do_sample=False,
                             pad_token_id=tok.eos_token_id)
    n = out.shape[1] - inp.input_ids.shape[1]
    reply = tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)
    after_gens.append({"prompt_id": g["prompt_id"], "category": g["category"],
                       "prompt": g["prompt"], "reply": reply,
                       "new_tokens": int(n), "sec": round(time.time()-gt,2)})
    if (i+1) % 5 == 0:
        with open(f"{ROOT}/results/baselines/qwen2.5-3b-qlora-corpus.json", "w") as f:
            json.dump({"model_id": mid, "adapter": adapter_path,
                       "completed": i+1, "total_sec": round(time.time()-t0,1),
                       "generations": after_gens}, f, indent=2, ensure_ascii=False)
        print(f"[{time.time()-t0:.1f}s] {i+1}/{len(before['generations'])}", flush=True)

# Final save
with open(f"{ROOT}/results/baselines/qwen2.5-3b-qlora-corpus.json", "w") as f:
    json.dump({"model_id": mid, "adapter": adapter_path,
               "completed": len(after_gens), "total_sec": round(time.time()-t0,1),
               "generations": after_gens}, f, indent=2, ensure_ascii=False)

# Build human-readable diff
diff_lines = ["# Vanilla vs QLoRA-Pilot — Side-by-side on 60 Korean prompts",
              f"\n> Base: {mid}", f"> Adapter: {adapter_path}",
              f"> Trained on: KoAlpaca-v1.1a (8000 examples, 1 epoch)\n"]
for b, a in zip(before["generations"], after_gens):
    diff_lines.append(f"\n## [{b['category']}] {b['prompt']}\n")
    diff_lines.append(f"**Vanilla:** {b['reply'][:500]}\n")
    diff_lines.append(f"**QLoRA:** {a['reply'][:500]}\n")
with open(f"{ROOT}/results/baselines/before_after_diff.md", "w") as f:
    f.write("\n".join(diff_lines))

print(f"[{time.time()-t0:.1f}s] DONE", flush=True)
