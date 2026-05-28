# COSE461 Final Project — assignment requirements audit

> Compiled from TA Junhyeok Oh's announcements (2026-05-24).
> Source: Korea University LMS course 86924 / mylms.korea.ac.kr

## 1. Hard requirements (per TA notices)

### 1.1 GitHub Repository

| Item | Requirement | Status |
|---|---|---|
| URL format | `https://github.com/{GitHubID}/261RCOSE46101` | ✅ sunnyxide/261RCOSE46101 |
| Visibility | Public (private allowed until grade release) | currently private, flip after 2026-06-30 |
| Naming | Exact: `261RCOSE46101` | ✅ matches |
| Code + documentation upload | Required | ✅ all 80+ files pushed |
| Submission deadline | 2026-06-02 via Google Form | ⏳ Sunwoo action |
| Survey URL | https://docs.google.com/forms/d/e/1FAIpQLSd3sPqlhaFTEHI4KwONjPq9ziVRow5YSheqiDpcRbavkoJx6A/viewform | ⏳ |

### 1.2 Final Report (Overleaf template — confirmed 2026-05-26)

| Item | Requirement | Status |
|---|---|---|
| Template source | NeurIPS 2020 style (.tex + .sty in ZIP) | ✅ landed in `reports/overleaf/` |
| Page limit | **8 content pages MAX** (excluding references) | confirmed — "no bonus for full 8p; be brief" |
| Style file | `neurips_2020.sty` (NeurIPS 2020 template) | ✅ ready |
| Required sections | Introduction, Related Work, **Approach**, Experiments (Data / Eval / Details / Results), **Analysis**, Conclusion | Writer briefs 07-08-14 align ✅ |
| Abstract | < 300 words | W7 task |
| Appendix | NOT counted in 8p; include **Team contributions** section | required for multi-person teams |
| Submission | **PDF via BlackBoard** (one per team) | ≠ GitHub URL Google Form |
| Citation style | `unsrt` (NeurIPS default) | ✅ bibliography.bib uses standard BibTeX |

**Note**: BlackBoard submission is DIFFERENT from the GitHub Google Form.
Two separate submissions required:
1. GitHub repo URL via Google Form (deadline 2026-06-02) — EVERY team member submits with SAME team repo URL
2. Final PDF via BlackBoard (one per team) — end of W8

### 1.3 AWS Account

| Item | Requirement | Status |
|---|---|---|
| Account allocation | Per team via NxtCloud spreadsheet | ✅ allocated, two accounts active |
| Password change | Mandatory at first login | ✅ done (per Sunwoo) |
| Instance usage | One instance per student, single g6.xlarge L4 | ✅ verified |
| Credit pool | $97.92/student × 2 students = ~$195.84 | ✅ confirmed (179 credits combined after pilot use) |
| Cross-member credit transfer | Allowed (TA message him) | available |

## 2. Team identification (confirmed via TA spreadsheet 2026-05-26)

| Field | Value |
|---|---|
| **Team number** | **8** |
| **Team name** | **토큰해적단 (Token Pirates)** |
| Member 1 | **주선우 (Sunwoo)** — Student ID **2023320312** — GitHub: sunnyxide |
| Member 2 | **김민수 (Min-su)** — Student ID **2022320337** — GitHub: (unknown, optional collaborator add) |
| (Josh / teammate) | — | external presentation, NOT in COSE461 team |

**Final report format**: Team 8 should use the format corresponding to team
number 8 in the TA's spreadsheet:
https://docs.google.com/spreadsheets/d/1z86LURwobe29ZGp8SArp9PXniMtY1akSRoyPjEep1lU/edit?gid=0#gid=0

(Most likely NeurIPS-style 8-page-max — confirmed via Overleaf template ZIP
landed in `reports/overleaf/`.)

## 3. Course-policy considerations

| Item | Requirement (inferred) | Action |
|---|---|---|
| AI usage policy | Allowed; disclosure required | ✅ `reports/AI_USAGE_DISCLOSURE.md` template ready, populate at W7 |
| Reference paper quality bar | Team 2 (8p, 14 eq), Team 4 (12p, 7 fig, α ablation), Team 22 (10p, 4 baselines) | KPI_FRAMEWORK.md §7 enforces matching bar |
| Methodology novelty | Implicit: differentiates from class peers | RESEARCH_PLAN_v2.md §3 differentiates from MiroFish + 5 others |

## 4. Submission timeline (working backward from 2026-06-02)

| Date | Milestone | Owner |
|---|---|---|
| 2026-06-02 | GitHub URL submission via Google Form (hard) | Sunwoo |
| 2026-W8 Fri | Overleaf PDF submission to TA | Sunwoo |
| 2026-W7 Fri | Writer-Critic loop convergence on all sections | autonomous lab |
| 2026-W6 Fri | All experimental data complete (G6 gate) | AWS + Hermes |
| 2026-W5 Fri | Static metrics computed (G5 gate) | analyst |
| 2026-W4 Fri | QLoRA trained on Nemotron+CB (G4 gate) | AWS |
| 2026-W3 Fri | 4,800 personas generated (G3 gate) | AWS |
| 2026-W2 Fri (this week) | KG + 50 scenarios + R4 decision (G2 gate) | Hermes cron + Sunwoo |
| 2026-W1 Fri (done) | Layer 1+2 data (G1 gate) | data_steward |

## 5. Missing inputs from user (gentle ask)

These are blockers I cannot resolve without you:

1. **Overleaf template ZIP** — drop `COSE461_Project_Final_Report_Template__2026_.zip`
   anywhere visible (Downloads/, Desktop/, lab dir), I'll unpack into
   `reports/overleaf/`. Writer agent needs the actual .tex format to target.

2. **Faculty advisor name** — Brief 11 (IRB protocol) has `<TODO>` placeholder
   for `Faculty advisor: <COSE461 instructor of record>`. Provide name + email.

3. **김민수 (2022320337) GitHub handle** — if he contributes commits, his
   git config + push permission. Otherwise current setup (sunnyxide solo
   author) is fine.

4. **Korea Univ IRB submission decision** — Tier A (15 evaluators × 200
   personas) needs IRB approval starting NOW for 4-6 week window. If
   skipping IRB, we lock to Tier B (5 × 50 + LLM panel calibration) or
   Tier C (LLM panel only). See `EVALUATOR_FALLBACK.md`.

5. **Google Form submission timing** — submit URL early (now) or wait
   until paper near-final? My recommendation: submit now since URL is
   stable; minor commits don't affect submission link.

## 5b. Course-policy updates (2026-05-26 TA messages)

- **Survey deadline**: 2026-06-02 (hard) — both Sunwoo AND Min-su submit
  Google Form individually but enter the SAME team repo URL
- **Collaborator add**: Add 김민수 as collaborator to sunnyxide/261RCOSE46101
  once we have their GitHub handle (Sunwoo to ask)
- **Slack workspace**: `cose461012026-hfu6687.slack.com` — both members
  should be in the workspace, name format `{name}_{student_id}`
- **Repo visibility**: PRIVATE until final grades release, then flip to
  PUBLIC. We can flip after 2026-06-30 (estimated grade release).

## 6. Gate conformance — current paper quality bar vs targets

Per KPI_FRAMEWORK.md §7 ("KPIs for the paper itself") — UPDATED with
template constraints:

| Dimension | Target (HANDOFF) | Template constraint | Current |
|---|---|---|---|
| Length | 8-12p NeurIPS-style | **8p MAX** (not 12) | Not yet drafted |
| Numbered equations | ≥ 8 | Team 2 (14 eq) | 0 (W7 task) |
| Baselines compared | ≥ 5 in main table | Team 22 (4+ours) | Run-A, Run-B, vanilla = 3; aiming for 6+ |
| Distinct evaluation regimes | ≥ 3 | Team 2 (5 datasets) | KoBBQ, KMMLU, custom CAS = 3 ✅ |
| Ablation studies | ≥ 2 (capacity + condition) | Team 4 α ablation | Capacity (Run-A/B), data (Run-F/G), backbone size (3B/7B/8B), pretraining (Western vs Korean), retrieval vs parametric — **5 axes** ✅+ |
| Figures | ≥ 3 (arch + heatmap + curve) | Team 4 (7 fig) | W7 task |
| Limitations | ≥ 3 explicit | All 3 ref teams | R3-R7 documented in decisions/ — easy to surface |
| Reproducibility | Code repo + decision log + prompts | None ref had | **Decision log** ✅, prompts ✅, code ✅, agent traces ✅ — **exceeds bar** |

The methodological-contribution KPI (autonomous lab) is the main
**reproducibility/transparency differentiator** none of the reference teams have.

## 7. Risk to assignment compliance

| Risk | Severity | Mitigation |
|---|---|---|
| Miss 2026-06-02 GitHub submission | Hard fail | Submit URL NOW via Google Form (low cost) |
| Overleaf template mismatch | Medium (formatting deduction) | Pull template ZIP at W4 start, target .tex from W7 |
| Methods section auto-drafted | Hard fail (HANDOFF.md §8 rule) | Critic enforces; Sunwoo writes methods personally |
| IRB unavailable, Tier C fallback paper weaker | Medium | Make Tier C scientifically defensible (LLM panel + variance reporting); see EVALUATOR_FALLBACK.md |
| Korean cultural data unavailable (Nemotron gated) | High | Have HF_TOKEN ready + manual gate-request fallback to KULLM/Polyglot |

## 8. Compliance sanity check

Final pre-submission audit (W8 Day 5):

- [ ] GitHub repo URL submitted via Google Form
- [ ] Repo flipped to public (after grade release per §1.1)
- [ ] PDF generated from Overleaf template targeting submitted format
- [ ] All 4,800 personas + ablation results + benchmarks in `results/`
- [ ] `reports/AI_USAGE_DISCLOSURE.md` populated with model versions + token counts
- [ ] Methods section human-authored confirmed (Critic + Sunwoo sign-off)
- [ ] No fabricated citations (Critic last-pass on bibliography.bib)
- [ ] Decision log audit complete (PI agent final report)
