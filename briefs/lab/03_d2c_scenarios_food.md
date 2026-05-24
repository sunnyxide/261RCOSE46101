# D2C scenarios — Korean food/health-supplement buyer (10 scenarios)

**Origin**: Same as `01_d2c_scenarios_cosmetics.md` — 10 of the 50 W2 G2 scenarios.

**Goal**: 10 distinct Korean food + health-supplement D2C buyer scenarios with
BAS-family metric coverage and Korean-baseline grounding.

**Decisions affected**: same as cosmetics brief.

---

## Required scenario structure

Same as the cosmetics brief (10 fields per scenario, including
`anti_western_check`). See `02_d2c_scenarios_cosmetics.md` for the full schema.

## Coverage requirements

- At least 2 scenarios per BAS metric (CCR / AAS / GCS)
- Mix of food subcategories: 가정간편식 (HMR) / 건강기능식품 / 한식 밀키트 / 신선식품 구독 / 다이어트 보조제
- Mix of cohorts: 30-40대 부모 (자녀 영양 결정) / 50-60대 (건기식 적극 구매) / 20대 (편의점·배달 의존) / 워킹맘
- At least 2 scenarios involve 가족 단톡방 (Korean family dynamics — 부모-자녀, 부부, 시댁/친정)
- At least 1 scenario involves Naver Smart Store / 쿠팡 Rocket Fresh discovery
- At least 1 scenario involves 홈쇼핑 (live commerce) influence — distinct
  from social-media; uniquely Korean for older cohorts
- At least 1 scenario involves health-supplement skepticism after 식약처
  warning announcement (cascade-of-disbelief, complaint dynamics)

## Specific anti-Western failure modes to surface

- **건기식 (Health functional food)** — Korean 건기식 culture treats supplements
  as a form of 효도 (filial gift), often purchased by adult children FOR
  parents, not by users themselves. Western LLM defaults to "I buy a vitamin
  for myself" framing; Korean reality has decision-maker ≠ consumer often.
- **HMR / 밀키트** — Korean working mothers carry the cognitive load of
  family meal planning; Western models often describe it as "convenience"
  while Korean discourse frames it as "엄마 노릇 vs 직장인 양립" tension.
- **다이어트 보조제** — Korean diet-supplement marketing exploits 미모지상주의
  + 단톡방 비교 dynamics in ways that direct user research surveys often
  underreport (taboo to admit in survey, but real in single-message-level
  단톡방 data).

## Sources to draw on

- KOSIS 건강기능식품 시장 규모 + 이용률 (식약처 발간 연차 보고서)
- Naver Datalab 식품/건강식품 카테고리 트렌드
- KCA 건강식품 분쟁 통계
- 식약처 (Ministry of Food and Drug Safety) 건강기능식품 통계
- KOFICE Hallyu 푸드 (K-food) 보고서
- 11번가 / 쿠팡 / 마켓컬리 — 구체 매출 데이터 없으면 카테고리 분류 참조

## Required meta footer

```
[meta]
verifiability_signal: high|medium|low
n_scenarios: 10
n_with_citation: <int>
```
