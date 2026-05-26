# Paper Final Results — Auto-generated

_generated orbt / aggregate_results.py_

## 1. KoBBQ + KMMLU + HAE-RAE + CLIcK (Phase 1)

| Model | KoBBQ corr | KoBBQ bias | Ambig corr | Disambig corr | KMMLU | HAE-RAE | CLIcK |
|---|---|---|---|---|---|---|---|
| Vanilla-3B-Qwen | 0.660 | 0.438 | 0.475 | 0.849 | 0.300 | 0.000 | - |
| Run-A-3B-Qwen+KoAlpaca | 0.680 | 0.407 | 0.535 | 0.828 | 0.270 | 0.000 | - |
| Run-B-3B-Qwen+KoAlpaca-bigger | 0.640 | 0.378 | 0.564 | 0.717 | 0.330 | 0.000 | - |
| Vanilla-7B-Qwen | 0.780 | 0.355 | 0.738 | 0.823 | 0.320 | 0.000 | - |
| Run-D-7B-Qwen+KoAlpaca | 0.738 | 0.312 | 0.782 | 0.692 | 0.290 | 0.000 | - |

## 2. Cultural-QLoRA on target benchmark (per culture)

| Culture | KoBBQ corr | KoBBQ bias | KMMLU | HAE-RAE | CLIcK |
|---|---|---|---|---|---|

## 3. Cross-cultural alignment (GlobalOpinionQA + BLEnD)

| Adapter | Culture | GO mean KS | GO median KS | BLEnD acc | BLEnD unparsed |
|---|---|---|---|---|---|