# D2C scenarios — Korean cosmetics buyer (10 scenarios)

**Origin**: W2 G2 gate requires 50 D2C scenarios drafted, OASIS-runnable. This
brief covers the cosmetics category (10 of the 50). The scenario corpus is
used in W6 to compute BAS (dynamic behavioral authenticity score) by running
persona-grounded agents through them and comparing to KOSIS+Naver+KOFICE
ground truth.

**Goal**: produce 10 distinct Korean cosmetics-buyer D2C scenarios that
exercise the three BAS-family metrics (CCR conformity / AAS authority
adoption / GCS group consensus). Each scenario has a setup, expected
behavioral outputs, and an expected Korean-baseline range to compare against.

**Decisions affected**:
- `data/scenarios/cosmetics.jsonl` — the actual scenario corpus
- OASIS simulation harness configuration (W6)
- KPI_FRAMEWORK.md BAS calibration (50 scenarios × 5 trials × 1 backbone = 250 sim runs)

**Why now**: scenarios block W6. Drafting them in W2/W3 means the OASIS
harness has them ready when persona generation completes.

---

## Required scenario structure (10 instances)

Each scenario MUST have:

1. **Scenario name** — short Korean phrase (e.g., "신상 토너 단톡방 추천")
2. **Setup paragraph** — what's happening (3-5 sentences in 한국어, 자연스러운 표현)
3. **Agent count + roles** — e.g., 5 agents: 1 initiator, 3 peers, 1 skeptic
4. **Trigger event** — what kicks off the scenario (a product launch, a price
   drop, a celebrity endorsement, a 단톡방 message)
5. **Expected behavioral output to measure** — one of: CCR / AAS / GCS / all
6. **Korean-baseline range** — what real Korean consumers do (cite source from
   KOSIS / Naver Datalab / KOFICE / Korea Consumer Agency); express as a
   number ± stddev or a percentage range
7. **Anti-Western-default check** — what a Western-defaulting LLM would
   plausibly get wrong about this scenario (e.g., over-weighting individual
   preference, missing 눈치 dynamics, mistranslating 정 as "love")

## Coverage requirements across the 10 scenarios

- At least 2 scenarios per BAS metric (CCR / AAS / GCS) — full coverage
- Mix of cohorts: 20대 여대생 / 30대 워킹맘 / 40대 가정주부 / 50대 임원 (any 4+)
- Mix of price tiers: 저가(LG생활건강 PB) / 중가(미샤·이니스프리) / 고가(설화수·후)
- At least 3 scenarios involve 단톡방 dynamics (the most distinctive Korean
  group-decision setting)
- At least 1 scenario involves a hallyu/idol endorsement (KOFICE territory)
- At least 1 scenario involves a complaint cascade (KCA territory)

## Concrete example to anchor format

```yaml
- name: "에센스 단톡방 신상 추천 (CCR)"
  setup: |
    30대 워킹맘 5인 단톡방. 평소에 화장품을 자주 공유하는 사이. 한 명이
    "이번에 [브랜드] 에센스 진짜 좋더라" 라고 사진과 함께 올림. 단톡방
    분위기는 평소 신상에 적극적인 편. 가격은 5만원대.
  agent_count: 5
  agent_roles: [initiator, peer_skeptic, peer_enthusiast, peer_quiet, peer_busy]
  trigger: 신상 에센스 추천 메시지 + 사용 후기 사진
  measured_metric: CCR
  korean_baseline:
    source: "KOSIS 가구별 소비지출, 화장품 추천경로 부가조사 2024"
    value: "0.58 ± 0.12"
    note: "30대 여성 단톡방-기인 화장품 구매율"
  anti_western_check:
    failure_mode: "Western LLM은 'peer_quiet' agent가 침묵하면 무관심으로 해석. 한국 단톡방에서는 침묵이 '눈치 보는 중'일 수 있음 — 추가 메시지 없이도 후속 구매로 이어지는 패턴을 잡아야 함"
```

## Sources to draw on

- KOSIS 화장품/이미용품 소비 지출 (분기별)
- Naver Datalab 쇼핑인사이트 — 화장품 카테고리 검색 트렌드 + 연령/성별 분포
- KCA (한국소비자원) 화장품 분쟁/피해 통계
- KOFICE 한류 백서 — K-beauty 채널 영향
- Olive Young / 화해 (Hwahae) — 한국 화장품 리뷰 플랫폼 데이터 paradigms

## Required meta footer

```
[meta]
verifiability_signal: high|medium|low
n_scenarios: 10
n_with_citation: <how many have a real source>
n_without_citation: <how many had to use heuristic baseline>
```

---

## Anti-failure check

- If a scenario does NOT have a Korean-baseline range tied to a real source,
  mark `baseline_source: heuristic` and add a TODO for human verification.
- Do NOT invent KOSIS table numbers; if uncertain, state "approximate
  table — verify via kosis.kr search".
- Each scenario should be runnable as a self-contained OASIS sim spec — if
  the setup paragraph is ambiguous about what agents should do, rewrite it.
