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
| cross_cultural_abl-kr-all6d_cn | cn | 0.581 | 0.550 | 0.275 | 0 |
| cross_cultural_abl-kr-all6d_jp | jp | 0.587 | 0.580 | 0.000 | 0 |
| cross_cultural_abl-kr-all6d_kr | kr | 0.556 | 0.521 | 0.388 | 0 |
| cross_cultural_abl-kr-all6d_us | us | 0.540 | 0.500 | 0.050 | 0 |
| cross_cultural_abl-kr-idv-only_kr | kr | 0.565 | 0.540 | 0.388 | 0 |
| cross_cultural_abl-kr-uai-only_kr | kr | 0.557 | 0.550 | 0.350 | 0 |
| cross_cultural_run-b-koalpaca_cn | cn | 0.622 | 0.660 | 0.312 | 0 |
| cross_cultural_run-b-koalpaca_jp | jp | 0.609 | 0.636 | 0.000 | 0 |
| cross_cultural_run-b-koalpaca_kr | kr | 0.609 | 0.609 | 0.325 | 0 |
| cross_cultural_run-b-koalpaca_us | us | 0.580 | 0.540 | 0.138 | 0 |
| cross_cultural_run-d-7b-koalpaca_cn | cn | 0.531 | 0.520 | 0.050 | 0 |
| cross_cultural_run-d-7b-koalpaca_jp | jp | 0.543 | 0.520 | 0.000 | 0 |
| cross_cultural_run-d-7b-koalpaca_kr | kr | 0.534 | 0.494 | 0.388 | 0 |
| cross_cultural_run-d-7b-koalpaca_us | us | 0.498 | 0.481 | 0.037 | 0 |
| cross_cultural_run-f-kr_cn | cn | 0.594 | 0.652 | 0.275 | 0 |
| cross_cultural_run-f-kr_jp | jp | 0.611 | 0.636 | 0.000 | 0 |
| cross_cultural_run-f-kr_kr | kr | 0.597 | 0.600 | 0.388 | 0 |
| cross_cultural_run-f-kr_us | us | 0.570 | 0.562 | 0.087 | 0 |
| cross_cultural_run-g-jp_cn | cn | 0.613 | 0.660 | 0.325 | 0 |
| cross_cultural_run-g-jp_jp | jp | 0.621 | 0.645 | 0.000 | 0 |
| cross_cultural_run-g-jp_kr | kr | 0.615 | 0.608 | 0.362 | 0 |
| cross_cultural_run-g-jp_us | us | 0.585 | 0.581 | 0.325 | 0 |
| cross_cultural_run-h-us_cn | cn | 0.660 | 0.728 | 0.200 | 0 |
| cross_cultural_run-h-us_jp | jp | 0.718 | 0.788 | 0.000 | 0 |
| cross_cultural_run-h-us_kr | kr | 0.705 | 0.794 | 0.087 | 0 |
| cross_cultural_run-h-us_us | us | 0.705 | 0.714 | 0.087 | 0 |
| cross_cultural_run-i-cn_cn | cn | 0.592 | 0.630 | 0.375 | 0 |
| cross_cultural_run-i-cn_jp | jp | 0.639 | 0.694 | 0.000 | 0 |
| cross_cultural_run-i-cn_kr | kr | 0.629 | 0.621 | 0.388 | 0 |
| cross_cultural_run-i-cn_us | us | 0.600 | 0.590 | 0.325 | 0 |
| cross_cultural_run-j-kr-7b_cn | cn | 0.568 | 0.550 | 0.050 | 0 |
| cross_cultural_run-j-kr-7b_jp | jp | 0.559 | 0.540 | 0.000 | 0 |
| cross_cultural_run-j-kr-7b_kr | kr | 0.535 | 0.485 | 0.388 | 0 |
| cross_cultural_run-j-kr-7b_us | us | 0.535 | 0.500 | 0.037 | 0 |
| cross_cultural_run-m-multi_cn | cn | 0.611 | 0.656 | 0.300 | 0 |
| cross_cultural_run-m-multi_jp | jp | 0.630 | 0.648 | 0.000 | 0 |
| cross_cultural_run-m-multi_kr | kr | 0.619 | 0.614 | 0.388 | 0 |
| cross_cultural_run-m-multi_us | us | 0.587 | 0.559 | 0.100 | 0 |
| cross_cultural_vanilla-3b_cn | cn | 0.616 | 0.663 | 0.062 | 0 |
| cross_cultural_vanilla-3b_jp | jp | 0.593 | 0.614 | 0.000 | 0 |
| cross_cultural_vanilla-3b_kr | kr | 0.590 | 0.600 | 0.388 | 0 |
| cross_cultural_vanilla-3b_us | us | 0.545 | 0.493 | 0.037 | 0 |
| cross_cultural_vanilla-7b_cn | cn | 0.553 | 0.545 | 0.050 | 0 |
| cross_cultural_vanilla-7b_jp | jp | 0.558 | 0.526 | 0.000 | 0 |
| cross_cultural_vanilla-7b_kr | kr | 0.607 | 0.600 | 0.388 | 0 |
| cross_cultural_vanilla-7b_us | us | 0.541 | 0.495 | 0.037 | 0 |

## 4. CAS LLM-judge panel (gpt-5.5 + Claude + mimo)

| Adapter | Culture | Authenticity | Consistency | Factual | n_prompts | Multi-judge coverage |
|---|---|---|---|---|---|---|
| Cultural-CN-3B | cn | 2.875 | 4.008 | 3.279 | 60 | 55/60 |
| Cultural-JP-3B | jp | 1.550 | 2.742 | 1.942 | 60 | 56/60 |
| Cultural-KR-7B | kr | 3.925 | 4.733 | 4.242 | 60 | 60/60 |
| Cultural-KR-3B | kr | 2.700 | 3.767 | 2.708 | 60 | 60/60 |
| Cultural-US-3B | us | 2.258 | 3.575 | 3.417 | 60 | 60/60 |
| Run-M-multi_cn | cn | 3.800 | 4.783 | 4.300 | 30 | 30/30 |
| Run-M-multi_jp | jp | 3.250 | 4.533 | 3.450 | 30 | 26/30 |
| Run-M-multi_kr | kr | 1.817 | 3.833 | 3.017 | 30 | 15/30 |
| Run-M-multi_us | us | 2.333 | 3.850 | 3.083 | 30 | 17/30 |
| Vanilla-3B-CN | cn | 3.983 | 4.592 | 4.100 | 60 | 55/60 |
| Vanilla-3B-JP | jp | 2.842 | 3.917 | 3.158 | 60 | 53/60 |
| Vanilla-3B-KR | kr | 2.583 | 3.517 | 2.758 | 60 | 58/60 |
| Vanilla-3B-US | us | 3.325 | 4.333 | 3.833 | 60 | 59/60 |