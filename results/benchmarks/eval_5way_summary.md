# Multi-base Korean cultural benchmark — controlled study

N KoBBQ: 80, N KMMLU: 40

| Model | Base | Adapter | KoBBQ correct | KoBBQ bias | KMMLU acc |
|---|---|---|---|---|---|
| **Vanilla-3B-Qwen** | Qwen/Qwen2.5-3B-Instruct | none | **78.8%** | 40.0% | **42.5%** |
| **Run-A-3B-Qwen+KoAlpaca** | Qwen/Qwen2.5-3B-Instruct | run-a-rank16-attn-20260524T133846Z | **61.3%** | 41.2% | **40.0%** |
| **Run-B-3B-Qwen+KoAlpaca-bigger** | Qwen/Qwen2.5-3B-Instruct | run-b-rank32-alllinear-20260524T142126Z | **56.2%** | 33.8% | **32.5%** |
| **Vanilla-7B-Qwen** | unsloth/Qwen2.5-7B-Instruct-bnb-4bit | none | **87.5%** | 23.8% | **22.5%** |
| **Run-D-7B-Qwen+KoAlpaca** | unsloth/Qwen2.5-7B-Instruct-bnb-4bit | run-d-7b-rank16-attn-20260526T053015Z | **67.5%** | 32.5% | **32.5%** |