#!/usr/bin/env bash
# reinforcement_a.sh — Instance A reinforcement queue.
# Runs AFTER instance_a_12h.sh finishes. Adds paper-grade polish:
#   R1. CAS persona corpus generation (4 cultural adapters × 60 prompts)
#       → Mac scores via GPT-5 + Claude (Tier A/B judge)
#   R2. Consumer prediction simulation (Cultural-KR on 10 KR product scenarios)
#       → Comparison to vanilla baseline
#
# Estimated: ~1.5h additional GPU work.
set -uo pipefail
LAB="$HOME/orbt-research-lab"
LOG=/tmp/reinforcement_a.log
cd "$LAB"
source .venv/bin/activate
_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) RA] $*" | tee -a "$LOG"; }
_log "START reinforcement A"

# ============================================================================
# R1: Persona corpus generation for CAS LLM-judge
# ============================================================================
# For each adapter we have on this instance, generate 60 culturally-conditioned
# persona prompts to be judged by GPT-5 + Claude on Mac.
ADAPTER_F=$(ls -d "$LAB"/runs/run-f-kr-*/adapter_final 2>/dev/null | head -1)
ADAPTER_H=$(ls -d "$LAB"/runs/run-h-us-*/adapter_final 2>/dev/null | head -1)
ADAPTER_J=$(ls -d "$LAB"/runs/run-j-kr-7b-*/adapter_final 2>/dev/null | head -1)

mkdir -p "$LAB/results/cas_corpus"

python - <<PYEOF 2>&1 | tee -a "$LOG"
import json, time, sys, os
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

ROOT = Path("$LAB")
PROMPTS = {
    "kr": [
        "당신은 한국 사람입니다. 추석 명절에 대해 설명해주세요.",
        "한국 직장 문화에서 회식의 의미를 설명해주세요.",
        "한국에서 부모님을 모시고 사는 것에 대해 어떻게 생각하시나요?",
        "한국 사람들이 '눈치'를 보는 이유를 설명해주세요.",
        "결혼식에서 축의금을 내는 한국 문화에 대해 말해주세요.",
        "한국에서 어른께 술을 따를 때의 예절을 설명해주세요.",
        "한국 사람들이 '우리'라는 단어를 자주 쓰는 이유는?",
        "한국에서 인사할 때 고개를 숙이는 의미를 설명해주세요.",
        "한국의 '정' 문화에 대해 설명해주세요.",
        "한국 사람이 처음 만난 사람에게 나이를 묻는 이유는?",
    ] * 6,  # 60 prompts
    "us": [
        "You are an American. Explain Thanksgiving.",
        "How do Americans typically introduce themselves in a business meeting?",
        "What does the American Dream mean to you?",
        "Explain American tipping culture at restaurants.",
        "Describe a typical American backyard barbecue.",
        "How do Americans view individualism?",
        "Explain American Super Bowl Sunday traditions.",
        "What is the role of small talk in American social interactions?",
        "Describe American attitudes toward personal space.",
        "How do Americans typically celebrate birthdays?",
    ] * 6,
}

def load_model(base, adapter):
    prequantized = ("-bnb-4bit" in base.lower()) or ("4bit" in base.lower())
    tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    kw = {"device_map": "auto", "attn_implementation": "sdpa", "trust_remote_code": True}
    if not prequantized:
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16,
        )
    else:
        kw["torch_dtype"] = torch.bfloat16
    m = AutoModelForCausalLM.from_pretrained(base, **kw)
    if adapter:
        m = PeftModel.from_pretrained(m, adapter)
    m.train(False)
    return tok, m

def gen_corpus(label, base, adapter, prompts, out_path):
    if Path(out_path).exists():
        print(f"[skip] {out_path} exists"); return
    print(f"[gen] {label} -> {len(prompts)} prompts")
    tok, m = load_model(base, adapter)
    out = []
    t0 = time.time()
    for i, prompt in enumerate(prompts):
        msgs = [{"role": "user", "content": prompt}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inp = tok(text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            o = m.generate(**inp, max_new_tokens=200, do_sample=False,
                           pad_token_id=tok.eos_token_id)
        reply = tok.decode(o[0][inp.input_ids.shape[1]:], skip_special_tokens=True)
        out.append({"prompt_id": i, "prompt": prompt, "reply": reply})
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{len(prompts)} ({time.time()-t0:.0f}s)")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"label": label, "base": base, "adapter": adapter,
                   "n": len(out), "generations": out}, f, indent=2, ensure_ascii=False)
    print(f"[done] {out_path} in {time.time()-t0:.0f}s")
    # Free VRAM
    del m, tok; torch.cuda.empty_cache(); import gc; gc.collect()

# Vanilla-3B for KR + US baselines
gen_corpus("Vanilla-3B-KR", "Qwen/Qwen2.5-3B-Instruct", None, PROMPTS["kr"],
           ROOT/"results/cas_corpus/vanilla-3b_kr.json")
gen_corpus("Vanilla-3B-US", "Qwen/Qwen2.5-3B-Instruct", None, PROMPTS["us"],
           ROOT/"results/cas_corpus/vanilla-3b_us.json")

# Cultural-KR on KR + Cultural-US on US (in-distribution)
if "$ADAPTER_F":
    gen_corpus("Cultural-KR-3B", "Qwen/Qwen2.5-3B-Instruct", "$ADAPTER_F", PROMPTS["kr"],
               ROOT/"results/cas_corpus/cultural-kr_kr.json")
if "$ADAPTER_H":
    gen_corpus("Cultural-US-3B", "Qwen/Qwen2.5-3B-Instruct", "$ADAPTER_H", PROMPTS["us"],
               ROOT/"results/cas_corpus/cultural-us_us.json")
# Run-J 7B-KR if exists
if "$ADAPTER_J":
    gen_corpus("Cultural-KR-7B", "unsloth/Qwen2.5-7B-Instruct-bnb-4bit", "$ADAPTER_J", PROMPTS["kr"],
               ROOT/"results/cas_corpus/cultural-kr-7b_kr.json")
print("CAS corpus generation done")
PYEOF

# ============================================================================
# R2: Consumer prediction simulation (Cultural-KR on Korean product scenarios)
# ============================================================================
_log "R2: consumer prediction simulation"
mkdir -p "$LAB/results/consumer_pred"
python - <<PYEOF 2>&1 | tee -a "$LOG"
import json, time
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

ROOT = Path("$LAB")
# 10 KR consumer scenarios with known general directional preferences (from market reports)
SCENARIOS = [
    {"id": 1, "product": "프리미엄 가전 신제품 (LG 시그니처)", "question": "이 제품에 대한 한국 소비자의 일반적 반응은? 1) 즉시 구매 의향 2) 가격대비 가치 평가 3) 브랜드 신뢰도 4) 가족·이웃 의견 영향도", "expected_direction": "high brand trust, family opinion important"},
    {"id": 2, "product": "글로벌 SPA 브랜드 (Uniqlo) 신상", "question": "한국 소비자가 이 제품 구매시 가장 중요하게 고려하는 요인은?", "expected_direction": "price-quality balance, peer influence"},
    {"id": 3, "product": "K-뷰티 신제품", "question": "이 제품에 대한 한국 소비자의 기대치는?", "expected_direction": "high quality expectation, social media driven"},
    {"id": 4, "product": "수입 자동차 (BMW)", "question": "이 제품을 구매하는 한국 소비자의 주된 동기는?", "expected_direction": "status, family approval, group identity"},
    {"id": 5, "product": "프리미엄 식료품 (한우)", "question": "한국 소비자가 이 제품을 구매하는 상황과 동기는?", "expected_direction": "gift-giving, ritual occasions, family gatherings"},
    {"id": 6, "product": "글로벌 OTT 서비스 (Netflix)", "question": "한국 소비자의 구독 결정 요인은?", "expected_direction": "Korean content availability, family sharing"},
    {"id": 7, "product": "교육 서비스 (영어 학원)", "question": "한국 부모가 자녀를 위해 이 서비스를 선택하는 이유는?", "expected_direction": "long-term investment, family pride, peer comparison"},
    {"id": 8, "product": "주거 (강남 아파트)", "question": "한국에서 이 주거지를 선호하는 이유는?", "expected_direction": "education access, status, long-term value"},
    {"id": 9, "product": "결혼 준비 패키지", "question": "한국 신혼부부의 의사결정 과정은?", "expected_direction": "family heavily involved, formal etiquette important"},
    {"id": 10, "product": "노후 보험상품", "question": "한국 소비자의 노후 준비 인식은?", "expected_direction": "family dependency anxiety, long-term planning"},
]

def load_model(base, adapter):
    prequantized = ("-bnb-4bit" in base.lower())
    tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    kw = {"device_map": "auto", "attn_implementation": "sdpa", "trust_remote_code": True}
    if not prequantized:
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16,
        )
    else:
        kw["torch_dtype"] = torch.bfloat16
    m = AutoModelForCausalLM.from_pretrained(base, **kw)
    if adapter: m = PeftModel.from_pretrained(m, adapter)
    m.train(False); return tok, m

def run_predictions(label, base, adapter, out_path):
    if Path(out_path).exists():
        print(f"[skip] {out_path}"); return
    print(f"[predict] {label}")
    tok, m = load_model(base, adapter)
    out = []
    for s in SCENARIOS:
        prompt = f"제품/상황: {s['product']}\n질문: {s['question']}\n한국 소비자 관점에서 답변하세요."
        msgs = [{"role": "user", "content": prompt}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inp = tok(text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            o = m.generate(**inp, max_new_tokens=300, do_sample=False, pad_token_id=tok.eos_token_id)
        reply = tok.decode(o[0][inp.input_ids.shape[1]:], skip_special_tokens=True)
        out.append({**s, "reply": reply})
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"label": label, "scenarios": out}, f, indent=2, ensure_ascii=False)
    del m, tok; torch.cuda.empty_cache(); import gc; gc.collect()
    print(f"[done] {out_path}")

run_predictions("Vanilla-3B", "Qwen/Qwen2.5-3B-Instruct", None,
                ROOT/"results/consumer_pred/vanilla-3b.json")
if "$ADAPTER_F":
    run_predictions("Cultural-KR", "Qwen/Qwen2.5-3B-Instruct", "$ADAPTER_F",
                    ROOT/"results/consumer_pred/cultural-kr.json")
print("Consumer prediction done")
PYEOF

_log "REINFORCEMENT A COMPLETE"
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/REINFORCEMENT_A_COMPLETE"
