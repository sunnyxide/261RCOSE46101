```markdown
# Abstract (186 words)

Large language models (LLMs) encode dominant Anglo-American cultural priors, limiting their global applicability. To enable targeted cultural adaptation, we introduce Cultural-QLoRA, a method for fine-tuning instruction-tuned models using low-rank adapters (rank 16-32, attn-only or all-linear) on curated datasets from CultureBank and Nemotron-Personas-Korea, coupled with Hofstede's 6-dimensional cultural model for system-prompt conditioning. We create distinct cultural adapters (KR, JP, US, CN) for both 3B and 7B parameter models. We evaluate cultural alignment by measuring the Kolmogorov-Smirnov (KS) distance between the model's response distribution and the empirical GlobalOpinionQA distribution for the target culture. Our results show that Cultural-QLoRA produces a measurable shift, with a mean reduction in KS distance of ΔKS=XX.X across adapters. Cross-cultural transfer analysis reveals a matrix of reweighting rather than deletion of opposing cultural traits. Ablations of Hofstede dimensions identify primary drivers of cultural expression in the models. Finally, we demonstrate the feasibility of a single unified multi-cultural adapter. This work provides a scalable framework for personalizing LLMs to specific cultural contexts.

---
**Word count**: 186 words
```
