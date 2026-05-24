"""Persona generation pilot — uses a trained QLoRA adapter to generate N Korean
consumer personas. Pilot for W3 persona corpus.

Each persona has demographic profile + cultural descriptors + a narrative.
Output: results/personas_pilot/personas.jsonl (one per line) + summary.md.
"""
import argparse
import json
import os
import time

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--adapter", required=True, help="Path to adapter_final dir")
    p.add_argument("--base-model", default="Qwen/Qwen2.5-3B-Instruct")
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--out-dir", default=os.path.expanduser("~/orbt-research-lab/results/personas_pilot"))
    return p.parse_args()


# 30 demographic cells from KOSIS Korea, balanced across sex/age/region/SES
CELLS = [
    ("F", "20대", "수도권",     "사회초년생"),
    ("F", "20대", "수도권",     "대학생"),
    ("F", "20대", "비수도권",  "사회초년생"),
    ("F", "30대", "수도권",     "기혼 워킹맘"),
    ("F", "30대", "수도권",     "미혼 직장인"),
    ("F", "30대", "비수도권",  "기혼 전업주부"),
    ("F", "40대", "수도권",     "기혼 직장맘"),
    ("F", "40대", "비수도권",  "기혼 자영업"),
    ("F", "50대", "수도권",     "기혼 전업주부"),
    ("F", "50대", "비수도권",  "농촌 가구"),
    ("F", "60대+", "수도권",    "은퇴자"),
    ("F", "60대+", "비수도권",  "농촌 노인"),
    ("M", "20대", "수도권",     "대학생"),
    ("M", "20대", "수도권",     "사회초년생"),
    ("M", "20대", "수도권",     "취준생"),
    ("M", "30대", "수도권",     "기혼 직장인"),
    ("M", "30대", "수도권",     "미혼 프리랜서"),
    ("M", "30대", "비수도권",  "스타트업 창업자"),
    ("M", "40대", "수도권",     "중간 관리자"),
    ("M", "40대", "수도권",     "기혼 외국계"),
    ("M", "40대", "비수도권",  "자영업"),
    ("M", "50대", "수도권",     "임원"),
    ("M", "50대", "수도권",     "전문직"),
    ("M", "50대", "비수도권",  "농촌 가구주"),
    ("M", "60대+", "수도권",    "은퇴자"),
    ("M", "60대+", "비수도권",  "농촌 노인"),
    ("F", "20대", "수도권",     "프리랜서"),
    ("F", "30대", "비수도권",  "직장맘"),
    ("M", "30대", "수도권",     "스타트업 직원"),
    ("M", "40대", "비수도권",  "교사"),
]

PROMPT_TEMPLATE = """다음 인구통계 정보로 한국 소비자 페르소나를 생성해줘. 영어식 번역체 X.
한국 원어민이 자연스럽게 묘사할 표현으로.

성별: {sex}
연령대: {age}
거주지: {region}
직업/사회경제적 위치: {ses}

다음 3가지를 한국어로:
1. 이름 (한국인 자연스러운 풀네임)
2. 일주일 라이프스타일 (2-3문장)
3. 한국 D2C 브랜드 신제품에 반응할 가장 가능성 높은 패턴 (눈치/관계/체면 중 어느 요소가 결정에 가장 큰 영향?)

응답은 JSON 형식 외 다른 설명 X:
{{"name": "...", "lifestyle": "...", "d2c_response_pattern": "..."}}
"""


def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    t0 = time.time()

    print(f"[init] adapter: {args.adapter}", flush=True)
    tok = AutoTokenizer.from_pretrained(args.base_model)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_use_double_quant=True,
                              bnb_4bit_compute_dtype=torch.bfloat16)
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model, quantization_config=bnb,
        device_map="auto", attn_implementation="sdpa",
    )
    model = PeftModel.from_pretrained(base, args.adapter)
    # Inference mode — no gradients, no dropout side effects.
    print(f"[{time.time()-t0:.1f}s] loaded, VRAM={torch.cuda.memory_allocated()/1024**3:.2f}GB",
          flush=True)

    cells = CELLS[:args.n]
    personas = []
    out_path = os.path.join(args.out_dir, "personas.jsonl")
    # Truncate file on start
    open(out_path, "w").close()

    with torch.inference_mode():
        for i, (sex, age, region, ses) in enumerate(cells):
            prompt = PROMPT_TEMPLATE.format(sex=sex, age=age, region=region, ses=ses)
            msgs = [{"role": "user", "content": prompt}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inp = tok(text, return_tensors="pt").to("cuda")
            out = model.generate(
                **inp, max_new_tokens=280, do_sample=True,
                temperature=0.8, top_p=0.9,
                pad_token_id=tok.eos_token_id,
            )
            n_new = out.shape[1] - inp.input_ids.shape[1]
            reply = tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)
            persona = {
                "id": f"p{i:03d}",
                "demographic": {"sex": sex, "age": age, "region": region, "ses": ses},
                "raw_reply": reply,
                "new_tokens": int(n_new),
            }
            try:
                import re
                m = re.search(r"\{.*\}", reply, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    persona["parsed"] = parsed
            except Exception as e:
                persona["parse_error"] = str(e)
            personas.append(persona)
            with open(out_path, "a") as f:
                f.write(json.dumps(persona, ensure_ascii=False) + "\n")
            if (i + 1) % 5 == 0:
                print(f"[{time.time()-t0:.1f}s] {i+1}/{len(cells)}", flush=True)

    summary_path = os.path.join(args.out_dir, "summary.md")
    n_parsed = sum(1 for p in personas if "parsed" in p)
    with open(summary_path, "w") as f:
        f.write(f"# Persona pilot — {len(personas)} Korean personas\n\n")
        f.write(f"- Adapter: `{args.adapter}`\n")
        f.write(f"- Base: `{args.base_model}`\n")
        f.write(f"- Generated: {len(personas)} personas\n")
        f.write(f"- JSON-parseable: {n_parsed}/{len(personas)}\n")
        f.write(f"- Total time: {time.time()-t0:.1f}s\n\n")
        f.write("## Sample personas\n\n")
        for p in personas[:5]:
            d = p["demographic"]
            f.write(f"### {p['id']} — {d['sex']} {d['age']} {d['region']} {d['ses']}\n\n")
            f.write(f"```\n{p['raw_reply'][:600]}\n```\n\n")
    print(f"[{time.time()-t0:.1f}s] DONE — {len(personas)} personas, {n_parsed} parsed", flush=True)


if __name__ == "__main__":
    main()
