# Peer review notes — Cultural-QLoRA paper

**Status**: Interim draft. Major bugs surfaced by 2026-05-29 multi-agent audit have been fixed; several rigor improvements are running in background.

**What to focus on (high-value feedback areas)**:

1. **Section 1 (Introduction)**: Is the motivation clear? Are the 7 listed contributions (lines 53-62) honestly differentiated from prior work (MiroFish/OASIS/CultureLLM)?

2. **Section 4.3 — Cross-cultural alignment**: This is the paper's main contribution. Table 4 shows KS distances for 10 model variants × 4 cultures. Codex critique was that at n=20 per-question bootstrap, almost no pairwise comparisons are significant. **Currently rerunning with full n=150 — will arrive in ~50 min.**

3. **Section 4.4 — Hofstede dimension ablation**: The "UAI-only beats Cultural-KR" finding (0.457 vs 0.580) is the strongest paper claim. Originally framed as "BEATS", softened to "numerically lower, CIs overlap by 0.07; suggestive not conclusive". After full n=150 rerun, this may become statistically significant. **Critical reviewer question**: if UAI-only does win, does that mean Cultural-QLoRA was unnecessary?

4. **Section 5.2 — Cultural-KR asymmetry**: The narrative was recently flipped. Originally claimed bias rises (+3.7pp); corrected to honest asymmetry (KR adapter has smallest debiasing of cultural adapters). The mechanistic explanation invokes Nemotron-Personas-Korea as the asymmetric data source. **Is the new narrative believable?**

5. **Section 6 — Conclusion + limitations**: Does the limitations section adequately acknowledge:
   - n=20 per-question CI weakness (being fixed)
   - Single seed for 5 of 6 adapters (multi-seed only on KR, std=0.025 added)
   - KS metric on nominal options (Codex flagged — needs limitation note)
   - 4 silent eval-loader bugs found by audit

**What is *not* expected to be fixed before deadline (6/02 GitHub URL)**:
- Krippendorff's α for CAS (currently mean pairwise diff; planned to update if time permits)
- KS-on-nominal-options Monte-Carlo null (acknowledged in limitations)
- Human evaluation (IRB time-budget)
- Comparison with CultureLLM head-to-head (cited but not run)

**Page count**: 7 pages of source ≈ likely ~8-9 PDF pages after Overleaf compile. Hard limit is 8. May need to move Table 6 (CAS) to appendix.

**Files for verification**:
- Results: `results/benchmarks/cross_cultural_*.json` (46 cells), `results/cas_scores/*.json` (13), `results/benchmarks/phase1_*FIXED*.json`
- Decision log: `decisions/2026-05-2*.md` (17 documented engineering choices)
- Audit logs: `reports/validation/CODEX_REVIEW_20260529.md`

**Submission timeline**:
- GitHub URL Google Form: 6/02 (Mon)
- PDF BlackBoard: W8 end (~6/06)

**What this draft is *not* yet**:
- 8-page-compiled PDF (Overleaf compile pending)
- Multi-seed bars in Table 4 (mean ± std being integrated)
- Full n=150 CI (data arriving ~50 min)

Thank you for the review!
