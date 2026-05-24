"""Generate a 60-prompt baseline corpus on Qwen2.5-3B-Instruct.

Each prompt covers a Korean consumer scenario with explicit anti-translation
instructions. Output is the vanilla baseline we compare retrieval-augmented
conditions against. Designed to run unattended in ~30-40 min.
"""
import json
import os
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

os.makedirs(os.path.expanduser("~/orbt-research-lab/results/baselines"), exist_ok=True)

# 60 prompts spanning demographics × scenarios. Each enforces "한국 원어민 자연스러운"
# or anti-translation framing.
PROMPTS = []
# A. Demographic profiles (15)
for desc in [
    "30대 직장인 기혼 여성", "20대 대학생 미혼 남성", "40대 중간 관리자 남성",
    "50대 가정주부 여성", "60대 은퇴자 남성", "20대 사회초년생 여성",
    "30대 프리랜서 남성", "40대 워킹맘 여성", "50대 자영업자 남성",
    "20대 취준생 여성", "30대 외국계 회사원 여성", "40대 교사 남성",
    "30대 스타트업 창업자 남성", "20대 인플루언서 여성", "50대 임원 남성"
]:
    PROMPTS.append(f"한국 {desc} 페르소나를 한 문장으로 설명해. 영어식 번역체 말고 한국 원어민 자연스러운 표현으로.")

# B. Purchase decisions (15)
for prod in ["새 신용카드", "건강식품", "전동칫솔", "구독 서비스", "전기차",
             "유아용품", "골프 클럽", "와인 셀러", "노트북", "공기청정기",
             "헬스장 멤버십", "한방 영양제", "유기농 식료품", "스마트워치", "겨울 외투"]:
    PROMPTS.append(f"한국 소비자가 {prod} 구매를 고민할 때 진짜 떠올리는 3가지 요소는? 영어 번역체 안 쓰고 한국식으로.")

# C. Cultural communication (10)
for topic in ["회식 자리에서 상사와의 거리감", "친구에게 돈 빌리는 상황", "회사 그만두는 결정",
              "가족 모임에서 결혼 압박", "소개팅 후 다음 만남 제안", "사춘기 자녀와 갈등 해결",
              "이웃과 층간소음 갈등", "직장 동기와 승진 경쟁", "친정 부모와 시댁 비교",
              "동창회 참석 vs 불참"]:
    PROMPTS.append(f"한국에서 '{topic}'에 대한 진짜 한국인 반응을 한 단락으로. '훌륭한 결정' 같은 공허한 말 X.")

# D. D2C / brand scenarios (10)
for brand in ["한국 D2C 화장품 브랜드", "한국 스타트업 식품 브랜드", "한국 가전 D2C",
              "한국 패션 D2C 브랜드", "한국 유아용품 브랜드", "한국 펫푸드 브랜드",
              "한국 홈인테리어 브랜드", "한국 건강기능식품 브랜드", "한국 캠핑 장비 브랜드",
              "한국 차(茶) 브랜드"]:
    PROMPTS.append(f"{brand}이 신제품 출시 시 한국 소비자에게 통하는 3가지 메시지는? 한국 문화적 맥락 포함.")

# E. Specific Korean cultural concepts (10)
for concept in ["눈치", "정", "체면", "갑질", "꼰대", "한", "효", "예의", "관계", "면접"]:
    PROMPTS.append(f"'{concept}'이 한국 소비자 행동에 미치는 영향을 구체적 예시 하나로 설명. 영어 직역 X.")

print(f"[init] {len(PROMPTS)} prompts queued")
t0 = time.time()
mid = "Qwen/Qwen2.5-3B-Instruct"
tok = AutoTokenizer.from_pretrained(mid)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                          bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
model = AutoModelForCausalLM.from_pretrained(mid, quantization_config=bnb,
                                              device_map="auto", attn_implementation="sdpa")
print(f"[{time.time()-t0:.1f}s] model loaded, VRAM={torch.cuda.memory_allocated()/1024**3:.2f} GiB", flush=True)

gens = []
total_tokens = 0
for i, p in enumerate(PROMPTS):
    msgs = [{"role": "user", "content": p}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inp = tok(text, return_tensors="pt").to("cuda")
    gt = time.time()
    out = model.generate(**inp, max_new_tokens=220, do_sample=False, pad_token_id=tok.eos_token_id)
    elapsed = time.time() - gt
    n = out.shape[1] - inp.input_ids.shape[1]
    total_tokens += n
    reply = tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)
    # Save incrementally so we have data even if interrupted
    gens.append({
        "prompt_id": i,
        "category": ["A_demographic","B_purchase","C_communication","D_brand","E_concept"][i//15 if i//15 < 4 else 4],
        "prompt": p,
        "reply": reply,
        "new_tokens": int(n),
        "sec": round(elapsed, 2),
        "tok_per_sec": round(n/elapsed, 1),
    })
    if (i+1) % 5 == 0:
        with open(os.path.expanduser("~/orbt-research-lab/results/baselines/qwen2.5-3b-vanilla-corpus.json"), "w") as f:
            json.dump({"model_id": mid, "quant": "nf4_double", "n_prompts": len(PROMPTS),
                       "completed": i+1, "total_sec": round(time.time()-t0, 1),
                       "total_tokens": total_tokens, "generations": gens},
                      f, indent=2, ensure_ascii=False)
        print(f"[{time.time()-t0:.1f}s] {i+1}/{len(PROMPTS)} done, {total_tokens} toks total", flush=True)

print(f"[{time.time()-t0:.1f}s] DONE — {len(gens)} generations, {total_tokens} toks", flush=True)
