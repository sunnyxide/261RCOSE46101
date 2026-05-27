```markdown
# Reviewer Rebuttal Preparation

## Objection #1: No human evaluation — all results rely on automatic metrics and LLM-judge
- **Likelihood**: HIGH
- **Severity**: MAJOR
- **Why raised**: Reviewers at ACL consistently flag cultural/subjective generation work that lacks human judgments. The KS-distance metric measures distributional shift but cannot confirm that outputs are *perceptibly* more culturally appropriate to native speakers. An LLM-judge evaluating "cultural authenticity" is circular when the base model already embeds cultural priors.
- **Our response**: We acknowledge this limitation and frame the paper as a *feasibility and mechanistic study* — demonstrating that QLoRA-based cultural reweighting is possible and interpretable, not claiming SOTA cultural generation. KS distance against empirical WVS ground-truth distributions is an objective, human-data-anchored metric (it measures alignment to how real Koreans actually answer, not LLM opinions about Koreanness). We will explicitly state that human evaluation is the necessary next step and describe a concrete protocol (native-speaker pairwise preference, IRB-ready) for the camera-ready or follow-up work.
- **Action**: Add a dedicated "Human Evaluation Roadmap" paragraph in §Limitations specifying annotator demographics, pairwise design, and inter-annotator agreement targets. Reframe LLM-judge results as supplementary only.

---

## Objection #2: KS distance computed on only 6–8 GlobalOpinionQA items per topic is statistically unreliable
- **Likelihood**: HIGH
- **Severity**: MAJOR
- **Why raised**: The Kolmogorov–Smirnov test is sensitive to sample size; with only 6–8 discrete response options per question, the empirical CDF is extremely coarse, and reported ΔKS values could easily be within noise. Without bootstrap confidence intervals or permutation tests, reviewers cannot assess whether the reported shifts are significant.
- **Our response**: We agree the per-question granularity is limited and will add bootstrap 95% CIs (10,000 resamples) over the KS distances aggregated across all questions within each topic, as well as a paired permutation test comparing Cultural-QLoRA vs. base model KS distances across the full question set. Additionally, we will report results at the topic-aggregate level (pooling all questions per cultural dimension) where sample sizes are larger, and show that the pattern holds. The KS distance is applied to the full option-distribution per question (not binary), giving a 5–7 point CDF — sufficient for a rank-based distance metric, though we concede power is limited for individual questions.
- **Action**: Add bootstrap CIs and permutation p-values to all KS tables. Add a supplementary table showing topic-aggregate KS with pooled N. Add a brief statistical power discussion in §Limitations.

---

## Objection #3: The paper assumes monolithic national cultures ("Korean culture") — within-country heterogeneity is ignored
- **Likelihood**: HIGH
- **Severity**: MAJOR
- **Why raised**: Cultural psychology has moved away from treating nations as cultural units. South Korea contains generational, regional, urban/rural, and ideological variation. Training a single adapter on aggregated CultureBank data for "Korea" risks reifying stereotypes and erasing minority perspectives. A reviewer with area-studies or sociolinguistics expertise will flag this immediately.
- **Our response**: We fully agree that national culture is a lossy proxy and will sharpen our framing: we treat *country-level WVS distributions* as a target because that is the empirical baseline available, not because we endorse methodological nationalism. The Hofstede ablation actually helps here — by identifying which dimension(s) drive the shift, we can test whether the model captures *distributional patterns* (e.g., high uncertainty avoidance) rather than stereotypes. We will add a "Sub-national heterogeneity" limitation paragraph noting that CultureBank itself contains demographic metadata (age, gender, region) that could enable future subgroup-specific adapters.
- **Action**: Add explicit discussion in §Limitations and §Ethical Considerations. Soften language throughout — replace "Korean culture" with "aggregated Korean WVS response distribution" where possible. Cite Sambasivan et al. (2021) and Röttger et al. (2024) on within-country variation.

---

## Objection #4: Only one random seed; no variance reporting across training runs
- **Likelihood**: HIGH
- **Severity**: MAJOR
- **Why raised**: QLoRA fine-tuning is known to have non-trivial variance across seeds, especially at small scale (3B/7B). Without multiple seeds, any reported ΔKS could be seed-specific. This is a basic reproducibility concern that workshop reviewers (especially those from the empirical NLP tradition) will not overlook.
- **Our response**: We acknowledge this as a cost-driven limitation and will run 3 additional seeds (total: 4) for the key Korean 3B and 7B conditions before submission. We will report mean ± std for all primary metrics and note that compute constraints prevented full multi-seed runs for all ablation cells. Where single-seed results are reported, we will include a sensitivity analysis by varying the random seed for data shuffling only (holding weight initialization constant via QLoRA's frozen base model) to isolate data-ordering effects.
- **Action**: Run 3 additional seeds for primary conditions. Report mean ± std in all tables. Add a "Seed Variance" paragraph in §Experimental Setup.

---

## Objection #5: Novelty is incremental — CulturalBank (Li et al., 2024) and BLEnD (Myung et al., 2024) already provide cultural data; what is new beyond applying QLoRA to it?
- **Likelihood**: MEDIUM-HIGH
- **Severity**: MAJOR
- **Why raised**: The cultural NLP space has moved quickly. If reviewers see CulturalBank as simply a data source and Hofstede prompts as a rebranding of prior cultural prompting work, they may view the contribution as an engineering exercise (fine-tuning on existing data with an existing method). The novelty claim needs to be razor-sharp.
- **Our response**: Our contribution is threefold and distinct from prior work: (1) we are the first to show that *parameter-efficient fine-tuning* (not prompting or full fine-tuning) can shift a small model's response distribution toward empirically measured cultural distributions — this is a different and more deployable mechanism; (2) we provide *mechanistic interpretability* via the transfer matrix showing which answers are reweighted vs. suppressed (not deletion), which no prior cultural-adaptation paper does; (3) the Hofstede-dimension ablation reveals *which cultural axis* drives the shift, providing actionable insights beyond "culture in, culture out." We will sharpen the Related Work comparison table to make these distinctions explicit.
- **Action**: Add a "Contributions vs. Prior Work" comparison table in §2. Revise §1 contribution bullets to emphasize mechanism and interpretability, not just the method itself.

---

## Objection #6: Hofstede's 6-D framework is heavily critiqued and may not be the right cultural lens
- **Likelihood**: MEDIUM
- **Severity**: MAJOR
- **Why raised**: Hofstede's dimensions have been criticized for (a) being derived from IBM employees in the 1970s, (b) assuming temporal stability, (c) conflating national averages with individual-level traits, and (d) Eurocentric framing. Cultural studies reviewers will question whether building system prompts around these dimensions introduces a Western-imposed taxonomy of culture.
- **Our response**: We use Hofstede as a *structuring heuristic for ablation*, not as ground truth about culture. The ablation's purpose is to show which prompt-level cultural framing has the largest effect on output distributions — this is an empirical question about prompt sensitivity, not a claim that Hofstede dimensions are ontologically correct. We will add an explicit discussion of Hofstede's limitations (citing McSweeney 2002, Venaik & Brewer 2013) and note that alternative frameworks (Schwartz, GLOBE, World Values Survey dimensions) could be substituted. The key finding — that certain dimensions drive larger shifts — would likely hold with any reasonable dimensional framework because it reflects *model sensitivity to cultural framing*, not the validity of the framework itself.
- **Action**: Add a "Limitations of Hofstede" paragraph in §2/Discussion citing major critiques. Add a sentence noting that the ablation methodology is framework-agnostic and extendable.

---

## Objection #7: GlobalOpinionQA is not WVS — using it as a proxy introduces distributional mismatch
- **Likelihood**: MEDIUM
- **Severity**: MAJOR
- **Why raised**: GlobalOpinionQA is a *derived* dataset (likely paraphrased/filtered from WVS or similar survey items), and its response options may not perfectly match the original WVS distributions. If the mapping is lossy or introduces artifacts, KS distances measured against GlobalOpinionQA could be misleading about actual WVS alignment. Reviewers will want to see the provenance and any validation of this proxy.
- **Our response**: We will add a detailed provenance section for GlobalOpinionQA explaining its construction from WVS/EVS items, including any paraphrasing or option-merging steps. Where possible, we will cross-validate by computing KS distance against the raw WVS microdata for the exact same question subset. If the correlation between GlobalOpinionQA-based and raw-WVS-based KS distances is high (which we expect), this validates the proxy. If not, we will report both and discuss the discrepancy transparently.
- **Action**: Add a dataset provenance paragraph in §Data. Run a cross-validation against raw WVS for the Korean subset. Report correlation in a supplementary table.

---

## Objection #8: LLM-judge for "cultural authenticity" inherits Western/Anglo biases from its own training
- **Likelihood**: MEDIUM
- **Severity**: MAJOR
- **Why raised**: Using GPT-4 or similar as a judge of whether outputs are "culturally appropriate for Korea" is problematic — the judge model was trained predominantly on English, Western-centric data and may penalize authentically Korean expressions that deviate from Western norms. Several ACL 2024/2025 papers have documented this judge bias.
- **Our response**: We treat the LLM-judge as a secondary/supplementary metric only — all primary claims rest on KS distance against empirical WVS data (which is human-generated, not LLM-generated). For the judge evaluations, we will (a) report inter-rater agreement between the LLM judge and a small set of Korean-native human annotations (even if preliminary, N=50 items), (b) analyze whether the judge's scores correlate with KS-distance shifts (if they do, this provides convergent validity; if not, we downweight the judge results), and (c) add a fairness analysis of the judge's scoring patterns across cultural dimensions.
- **Action**: Demote LLM-judge results to supplementary material. Run a small human-vs-LLM-judge correlation pilot (N=50). Add explicit discussion of judge limitations in §4.

---

## Objection #9: Model scale (3B/7B only) limits ecological validity — results may not hold for frontier models
- **Likelihood**: MEDIUM
- **Severity**: MINOR
- **Why raised**: Cultural adaptation methods are most needed for *accessible* small models, but reviewers may question whether the mechanisms observed (transfer matrix patterns, Hofstede dimension sensitivity) scale to 13B+ or to different model families. If the findings are scale-specific, the contribution is narrower.
- **Our response**: We intentionally focus on small models because they are the *target deployment scenario* — cultural adaptation for resource-constrained communities who cannot run 70B+ models. We acknowledge scale as a variable and note that QLoRA's rank-16 adapter at 3B already captures meaningful cultural shifts, suggesting the method is not scale-limited in principle. We will add a brief 13B experiment (if compute permits) or, alternatively, provide a theoretical argument about why adapter capacity (rank × parameters) is the relevant variable, not total model size, drawing on QLoRA scaling literature.
- **Action**: If compute available, add one 13B run for the primary Korean condition. Otherwise, add a scaling discussion paragraph citing adapter capacity arguments and flag it as future work.

---

## Objection #10: Cultural reweighting may amplify stereotypes rather than capture genuine cultural nuance
- **Likelihood**: LOW-MEDIUM
- **Severity**: MAJOR
- **Why raised**: A sophisticated reviewer may argue that shifting model distributions toward WVS country averages risks encoding *descriptive stereotypes* ("Koreans think X") rather than *prescriptive cultural competence* (understanding when and how cultural context matters). The transfer matrix "reweighting, not deletion" finding helps, but doesn't fully address whether the model is learning genuine cultural reasoning vs. surface-level pattern matching on survey responses.
- **Our response**: This is a legitimate concern and we will address it head-on. The transfer matrix evidence shows that the adapter *reweights* existing answer options rather than deleting minority positions — this is consistent with capturing a distributional tendency, not enforcing a stereotype. We will add an analysis comparing the adapter's shift against the *within-country variance* in WVS: if the adapter shifts toward the mean while preserving the tail, it is acting as a soft prior, not a stereotype. We will also note that the Hofstede ablation helps disentangle which *dimension* of cultural orientation is captured (e.g., collectivism vs. food preferences), and that stereotype-like behavior would manifest as indiscriminate shifting across all dimensions, which we do not observe.
- **Action**: Add a "Stereotype vs. Distributional Prior" analysis paragraph in §Discussion. Add a figure showing that adapter outputs preserve within-country variance (not just shift the mean). Add an ethical considerations paragraph citing Blodgett et al. (2020) on representational harms.

---

## Cross-cutting themes

Three patterns emerge across likely objections: (1) **Evaluation validity** — objections #1, #2, #7, and #8 all question whether our metrics actually measure what we claim; the unified mitigation is to triangulate KS distance with at least preliminary human judgments and to add statistical rigor (CIs, permutation tests). (2) **Construct validity of "culture"** — objections #3, #6, and #10 challenge whether national culture + Hofstede is a defensible operationalization; the response is to treat these as pragmatic heuristics with explicit limitations, not ontological claims, and to show the method is framework-agnostic. (3) **Experimental rigor** — objections #4 and #9 flag missing baselines and variance; these are the easiest to fix concretely (additional seeds, one larger model run) and should be addressed before submission to preempt the most straightforward desk-reject-level criticism.
```
