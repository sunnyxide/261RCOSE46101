# Paper Final Results — Auto-generated

_generated orbt / aggregate_results.py_

## 1. KoBBQ + KMMLU + HAE-RAE + CLIcK (Phase 1)

| Model | KoBBQ corr | KoBBQ bias | Ambig corr | Disambig corr | KMMLU | HAE-RAE | CLIcK |
|---|---|---|---|---|---|---|---|
| Vanilla-3B-Qwen | 0.660 | 0.450 | 0.443 | 0.864 | 0.300 | 0.130 | 0.470 |
| Run-A-3B-Qwen+KoAlpaca | 0.700 | 0.400 | 0.557 | 0.835 | 0.270 | 0.270 | 0.440 |
| Run-B-3B-Qwen+KoAlpaca-bigger | 0.655 | 0.380 | 0.567 | 0.738 | 0.330 | 0.300 | 0.460 |
| Vanilla-7B-Qwen | 0.810 | 0.350 | 0.773 | 0.845 | 0.320 | 0.470 | 0.520 |
| Run-D-7B-Qwen+KoAlpaca | 0.725 | 0.330 | 0.773 | 0.680 | 0.290 | 0.500 | 0.570 |

## 2. Cultural-QLoRA on target benchmark (per culture)

| Culture | Model | KoBBQ corr | KoBBQ bias | KMMLU | HAE-RAE | CLIcK |
|---|---|---|---|---|---|---|
| CN | Cultural-cn-3B | 0.662 | 0.263 | 0.400 | - | - |
| JP | Cultural-jp-3B | 0.650 | 0.250 | 0.300 | - | - |
| KR | Cultural-kr-3B | 0.562 | 0.487 | 0.225 | - | - |
| US | Cultural-us-3B | 0.562 | 0.263 | 0.225 | - | - |

## 3. Cross-cultural alignment (GlobalOpinionQA + BLEnD)

| Adapter | Culture | GO mean KS | GO median KS | BLEnD acc | BLEnD unparsed |
|---|---|---|---|---|---|
| cross_cultural_run-f-kr_kr | kr | 0.597 | 0.600 | 0.388 | 0 |
| cross_cultural_run-g-jp_jp | jp | 0.621 | 0.645 | 0.000 | 0 |
| cross_cultural_run-g-jp_kr | kr | 0.615 | 0.608 | 0.362 | 0 |
| cross_cultural_run-h-us_kr | kr | 0.705 | 0.794 | 0.087 | 0 |
| cross_cultural_run-i-cn_jp | jp | 0.639 | 0.694 | 0.000 | 0 |
| cross_cultural_run-i-cn_kr | kr | 0.629 | 0.621 | 0.388 | 0 |
| cross_cultural_run-j-kr-7b_kr | kr | 0.535 | 0.485 | 0.388 | 0 |
| cross_cultural_run-m-multi_kr | kr | 0.619 | 0.614 | 0.388 | 0 |
| cross_cultural_vanilla-3b_jp | jp | 0.593 | 0.614 | 0.000 | 0 |
| cross_cultural_vanilla-3b_kr | kr | 0.590 | 0.600 | 0.388 | 0 |
| cross_cultural_vanilla-7b_kr | kr | 0.607 | 0.600 | 0.388 | 0 |

## 4. CAS LLM-judge panel (gpt-5.5 + Claude + mimo)

| Adapter | Culture | Authenticity | Consistency | Factual | n_prompts | Multi-judge coverage |
|---|---|---|---|---|---|---|
| Cultural-CN-3B | cn | 2.875 | 4.008 | 3.279 | 60 | 55/60 |