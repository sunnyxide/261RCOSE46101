# Phase 1 extended Korean cultural benchmark

**Few-shot K=3**, KoBBQ n=200 (per-cat + ambig/disambig split), KMMLU n=100, HAE-RAE n=100, CLIcK n=100

| Model | KoBBQ corr | KoBBQ bias | KoBBQ ambig corr | KoBBQ disambig corr | KMMLU | HAE-RAE | CLIcK |
|---|---|---|---|---|---|---|---|
| **Vanilla-3B-Qwen** | 66.0% | 45.0% | 44.3% | 86.4% | 30.0% | 13.0% | 47.0% |
| **Run-A-3B-Qwen+KoAlpaca** | 70.0% | 40.0% | 55.7% | 83.5% | 27.0% | 27.0% | 44.0% |
| **Run-B-3B-Qwen+KoAlpaca-bigger** | 65.5% | 38.0% | 56.7% | 73.8% | 33.0% | 30.0% | 46.0% |
| **Vanilla-7B-Qwen** | 81.0% | 35.0% | 77.3% | 84.5% | 32.0% | 47.0% | 52.0% |
| **Run-D-7B-Qwen+KoAlpaca** | 72.5% | 33.0% | 77.3% | 68.0% | 29.0% | 50.0% | 57.0% |