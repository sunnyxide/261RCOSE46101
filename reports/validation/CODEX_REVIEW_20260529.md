# Codex sub-agent review — 2026-05-29

External NLP engineer reviewer assessment of the repo before submission.

## Critical findings (verified)

| Finding | Verified? | Action |
|---|---|---|
| `.pem` in git history | ❌ Codex was wrong — .pem never committed (gitignore caught it) | none |
| `vanilla-3b_kr_scored.json` n=0 (all judges None) | ✅ confirmed — parsing failure | re-run with 3-judge panel |
| `reasoning_effort="none"` invalid for gpt-5.5 | ❌ Codex was wrong — verified working ("Reply: OK" returned) | none |
| KS stat mis-named (it's max-CDF-distance on discrete dist) | ✅ valid critique — common in lit as "KS distance" but worth documenting | rename in paper §3 or add footnote citing discrete-KS variant |
| README references Hofstede ablation dirs that don't exist locally | ✅ valid — `data/cultural/kr_idv_only/` is on AWS instance B, not synced | add note or rsync from AWS |
| bitsandbytes no macOS wheels for graders | ✅ valid — SETUP.md should warn | add note |
| `reports/sections/04_results_draft.md` = TODO placeholders | ✅ valid — actual paper content not yet integrated | integrate after AWS cross-cultural eval lands |
| `reports/overleaf/template.tex` unmodified boilerplate | ✅ valid — final paper not assembled | assemble after sections ready |
| Cultural-QLoRA KoBBQ degradation 0.66 → 0.56 | ✅ real result — needs honest framing in §5 Analysis | frame as cultural↔bias tradeoff |

## Bottom line from Codex

> "Yes, the scope is remarkable for an undergrad pair. The execution is uneven.
> The paper isn't written. That's the deliverable being graded.
> Path to 'remarkable' in 4 days: (1) fix vanilla-3b_kr rescore, (2) drop real KS
> numbers into §4.3, (3) write §3-5 yourselves using only verified numbers,
> (4) acknowledge KoBBQ degradation honestly."

## Codex's praise

- 6 trained adapters (most undergrad teams ship 1)
- 3-LLM judge panel with documented IRR (published-paper-tier methodology)
- 17 decision-log markdowns showing real engineering judgment
- KoBBQ + KMMLU + HAE-RAE + CLIcK + GO + BLEnD coverage exceeds class average
- Clever Xiaomi Plan endpoint cost optimization
