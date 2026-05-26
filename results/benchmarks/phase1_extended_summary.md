# Phase 1 extended Korean cultural benchmark

**Few-shot K=3**, KoBBQ n=400 (per-cat + ambig/disambig split), KMMLU n=100, HAE-RAE n=100, CLIcK n=0

| Model | KoBBQ corr | KoBBQ bias | KoBBQ ambig corr | KoBBQ disambig corr | KMMLU | HAE-RAE | CLIcK |
|---|---|---|---|---|---|---|---|
| **Vanilla-3B-Qwen** | 66.0% | 43.8% | 47.5% | 84.9% | 30.0% | 0.0% | 0.0% |
| **Run-A-3B-Qwen+KoAlpaca** | 68.0% | 40.8% | 53.5% | 82.8% | 27.0% | 0.0% | 0.0% |
| **Run-B-3B-Qwen+KoAlpaca-bigger** | 64.0% | 37.8% | 56.4% | 71.7% | 33.0% | 0.0% | 0.0% |
| **Vanilla-7B-Qwen** | 78.0% | 35.5% | 73.8% | 82.3% | 32.0% | 0.0% | 0.0% |
| **Run-D-7B-Qwen+KoAlpaca** | 73.8% | 31.2% | 78.2% | 69.2% | 29.0% | 0.0% | 0.0% |