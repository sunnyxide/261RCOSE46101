#!/usr/bin/env bash
# reinforcement_b.sh — Instance B reinforcement queue.
# Runs AFTER instance_b_12h.sh finishes. Adds:
#   R1. Persona corpus for Cultural-JP + Cultural-CN + Run-M (multi-cultural)
#   R2. Multi-seed cross-cultural re-eval on Cultural-KR (using KR adapter — needs sync from A)
#       SKIPPED if KR adapter not present (Instance A has it).
#
# Estimated: ~1h additional GPU work.
set -uo pipefail
LAB="$HOME/orbt-research-lab"
LOG=/tmp/reinforcement_b.log
cd "$LAB"
source .venv/bin/activate
_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) RB] $*" | tee -a "$LOG"; }
_log "START reinforcement B"

ADAPTER_G=$(ls -d "$LAB"/runs/run-g-jp-*/adapter_final 2>/dev/null | head -1)
ADAPTER_I=$(ls -d "$LAB"/runs/run-i-cn-*/adapter_final 2>/dev/null | head -1)
ADAPTER_M=$(ls -d "$LAB"/runs/run-m-multi-*/adapter_final 2>/dev/null | head -1)

mkdir -p "$LAB/results/cas_corpus"

# Persona corpus for JP / CN / Multi
python - <<PYEOF 2>&1 | tee -a "$LOG"
import json, time
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

ROOT = Path("$LAB")
PROMPTS = {
    "jp": [
        "あなたは日本人です。お正月の伝統を説明してください。",
        "日本の職場での「飲み会」の意味を説明してください。",
        "日本人が「すみません」をよく使う理由を説明してください。",
        "日本のお花見文化について教えてください。",
        "日本の和食における「おもてなし」の精神を説明してください。",
        "日本人が約束時間を厳守する理由は?",
        "日本のお辞儀の意味と種類を説明してください。",
        "日本の「察する」文化について説明してください。",
        "日本の結婚式における「ご祝儀」の慣習を説明してください。",
        "日本人が集団行動を重視する理由は?",
    ] * 6,
    "cn": [
        "你是中国人。请说明春节的传统。",
        "请说明中国职场中的'面子'文化。",
        "中国人为什么重视家族关系?",
        "请说明中国的茶文化。",
        "中国人在送礼时有什么讲究?",
        "请说明中国的'关系'文化在商业中的作用。",
        "中国人为什么重视长辈的意见?",
        "请说明中国的婚礼传统。",
        "中国饮食文化中聚餐的意义是什么?",
        "中国人对儿女教育的态度如何?",
    ] * 6,
}

def load_model(base, adapter):
    tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    kw = {"device_map": "auto", "attn_implementation": "sdpa", "trust_remote_code": True,
          "quantization_config": BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
              bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)}
    m = AutoModelForCausalLM.from_pretrained(base, **kw)
    if adapter: m = PeftModel.from_pretrained(m, adapter)
    m.train(False); return tok, m

def gen_corpus(label, base, adapter, prompts, out_path):
    if Path(out_path).exists():
        print(f"[skip] {out_path}"); return
    print(f"[gen] {label} -> {len(prompts)} prompts")
    tok, m = load_model(base, adapter)
    out = []
    t0 = time.time()
    for i, prompt in enumerate(prompts):
        msgs = [{"role": "user", "content": prompt}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inp = tok(text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            o = m.generate(**inp, max_new_tokens=200, do_sample=False, pad_token_id=tok.eos_token_id)
        reply = tok.decode(o[0][inp.input_ids.shape[1]:], skip_special_tokens=True)
        out.append({"prompt_id": i, "prompt": prompt, "reply": reply})
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(prompts)} ({time.time()-t0:.0f}s)")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"label": label, "base": base, "adapter": adapter,
                   "n": len(out), "generations": out}, f, indent=2, ensure_ascii=False)
    del m, tok; torch.cuda.empty_cache(); import gc; gc.collect()
    print(f"[done] {out_path} in {time.time()-t0:.0f}s")

gen_corpus("Vanilla-3B-JP", "Qwen/Qwen2.5-3B-Instruct", None, PROMPTS["jp"],
           ROOT/"results/cas_corpus/vanilla-3b_jp.json")
gen_corpus("Vanilla-3B-CN", "Qwen/Qwen2.5-3B-Instruct", None, PROMPTS["cn"],
           ROOT/"results/cas_corpus/vanilla-3b_cn.json")
if "$ADAPTER_G":
    gen_corpus("Cultural-JP-3B", "Qwen/Qwen2.5-3B-Instruct", "$ADAPTER_G", PROMPTS["jp"],
               ROOT/"results/cas_corpus/cultural-jp_jp.json")
if "$ADAPTER_I":
    gen_corpus("Cultural-CN-3B", "Qwen/Qwen2.5-3B-Instruct", "$ADAPTER_I", PROMPTS["cn"],
               ROOT/"results/cas_corpus/cultural-cn_cn.json")
# Multi-cultural Run-M on all 4 cultures (with culture token)
if "$ADAPTER_M":
    for c_code, prompts in [("kr", PROMPTS.get("kr", PROMPTS["jp"])), ("jp", PROMPTS["jp"]),
                              ("us", PROMPTS.get("us", PROMPTS["jp"])), ("cn", PROMPTS["cn"])]:
        # Prepend culture token to multi-cultural prompts
        tagged = [f"<<culture:{c_code}>> {p}" for p in prompts[:30]]  # 30 per culture
        gen_corpus(f"Run-M-multi_{c_code}", "Qwen/Qwen2.5-3B-Instruct", "$ADAPTER_M", tagged,
                   ROOT/f"results/cas_corpus/run-m-multi_{c_code}.json")
print("Persona corpus B done")
PYEOF

_log "REINFORCEMENT B COMPLETE"
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/REINFORCEMENT_B_COMPLETE"
