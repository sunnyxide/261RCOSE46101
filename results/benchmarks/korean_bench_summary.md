# Korean cultural benchmark — multi-way comparison

- N KoBBQ: 80 (10 categories)
- N KMMLU: 40 (Korean-History)
- Base: Qwen/Qwen2.5-3B-Instruct

## KoBBQ (Korean Bias Benchmark)
| Model | Correct rate | Bias rate | n |
|---|---|---|---|
| vanilla | **78.8%** | 40.0% | 80 |
| run-a | **61.3%** | 41.2% | 80 |
| run-b | **56.2%** | 33.8% | 80 |

Lower bias_rate is better — measures how often model picks the biased answer.
Higher correct_rate is better — measures factual correctness on unbiased ground.

## KMMLU Korean History
| Model | Accuracy | Unparsed | n |
|---|---|---|---|
| vanilla | **42.5%** | 0 | 40 |
| run-a | **40.0%** | 1 | 40 |
| run-b | **32.5%** | 4 | 40 |