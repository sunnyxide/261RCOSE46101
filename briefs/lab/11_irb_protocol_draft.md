# IRB protocol draft — Korean human-evaluator panel

**Origin**: `EVALUATOR_FALLBACK.md` outlines tiers A/B/C/D. Tier A requires
15 Korean evaluators × 200 personas with native-speaker Likert ratings,
which means IRB (Institutional Review Board) approval at Korea University.
IRB review takes 4-6 weeks, so the protocol must be drafted NOW (W1) to
keep Tier A in play.

**Goal**: produce `results/hermes_outputs/11_irb_protocol_draft.md` — a
complete IRB protocol following Korea University's IRB template, ready
for Sunwoo to submit to ku-irb.ac.kr.

**Why now**: blocks Tier A. Decided by W2 Friday per QA Meta evaluator-tier
proposal protocol.

---

## Required sections (matches Korea University IRB application format)

### 1. Project title (Korean + English)
Korean: 한국어 LLM 페르소나 문화적 진정성 평가
English: Evaluation of cultural authenticity in Korean LLM-generated personas

### 2. Investigator info
- Principal: 주선우 (2023320312), Korea University, sunwo1224@korea.ac.kr
- Co-investigator: 김민수 (2022320337)
- Faculty advisor: <TODO: course advisor for COSE461>

### 3. Background and rationale (1 page)
- Reference MOTIVATION_v2.md §1: Western-default LLM problem
- Cite CulturalBench, KoBBQ, KAIO as evidence base
- Explain why human evaluation is needed (LLM judges have shared bias)

### 4. Research questions and hypotheses (compact)
- Pull from HANDOFF.md §2 (H1-H4)
- Focus on what human-evaluator-derived CAS specifically tests

### 5. Methods
- Recruitment: Korea University students (Tier B fallback) or Prolific
  (Tier A target); both via online posting
- Inclusion criteria: native Korean speaker (born in Korea, primary
  education in Korean), age 20-65, not employed in marketing/advertising
  (to reduce expert bias)
- Exclusion criteria: prior involvement in cultural-NLP research,
  current employment at LLM-providing companies
- Procedure: each evaluator rates 200 personas (or 50 for Tier B) on
  CURE 5-dimension Likert (Realism, Plausibility, Idiom, Reasoning,
  Behavior)
- Compensation: ₩100,000 per full panel (or pro-rated)
- Duration: ~2 hours per evaluator
- Materials: web-based survey platform (LimeSurvey self-hosted on Mac
  Mini, or KU institutional Qualtrics)

### 6. Data handling
- No PII collected on evaluators (anonymous numeric ID only)
- Persona ratings stored at `data/raw/human_ratings/` under DVC, hashed
- Recording of any qualitative comments (free-text only, no audio)
- Retention: 5 years per Korean Personal Information Protection Act
- Destruction protocol: cryptographic shred after retention period

### 7. Ethical considerations
- Minimal risk study (rating fictional personas, no deception, no
  emotional manipulation)
- Right to withdraw at any time without penalty
- Compensation paid even if withdrawn mid-study
- Consent form (both Korean + English versions)

### 8. Consent form template (Korean)
Full text of consent including:
- 연구 목적 + 절차 + 소요시간
- 자발적 참여 + 중도 철회 권리
- 보상 + 비밀유지
- 연락처: PI 이메일

### 9. Risks and benefits
- Risks: minimal — fatigue from 2-hour rating task; mitigated by
  scheduled breaks
- Benefits: ₩100,000 compensation + contribution to publicly-released
  research

### 10. Timeline
- IRB submission: <within W2 of project, target 2026-05-31>
- Expected approval: 4-6 weeks (target 2026-07-15)
- Data collection: 2 weeks
- Analysis: 1 week
- Publication: anonymous data release per FAIR principles

### 11. Budget
- Evaluator compensation: 15 × ₩100,000 = ₩1.5M (Tier A) or
  5 × ₩50,000 = ₩250K (Tier B)
- Platform: ~₩50K
- Total: ₩1.55M (Tier A) or ₩300K (Tier B)

### 12. Data-sharing plan
- De-identified ratings released alongside the paper on Hugging Face
- Persona generations released on the repo + HF Hub
- Adapter weights released on HF Hub under permissive license

## Required style

- Korean: 정중한 학술 문체
- English (where dual-language): formal academic English
- No marketing claims
- Cite IRB-relevant standards: Belmont Report, Declaration of Helsinki,
  Korean Personal Information Protection Act (PIPA)

## Required meta footer

```
[meta]
verifiability_signal: high|medium|low
sections_complete: <list>
sections_with_TODO: <list>
estimated_review_weeks: <int>
```

## Hard constraints

- If section 2 (Investigator info) has unknown faculty advisor name, mark
  `<TODO: ask Sunwoo for COSE461 instructor of record>` — do NOT invent.
- If section 12 (data-sharing) is uncertain about license, default to
  CC BY 4.0 for human-rated data + Apache 2.0 for code + research-only
  for adapter weights, but mark `<verify with course IRB on commercial use>`.
- This document is a DRAFT, not a submission. Sunwoo must review every
  section, fill TODOs, and sign before submitting to KU IRB.
