# D2C scenarios — Korean fashion buyer (10 scenarios)

**Origin**: Same as cosmetics/food briefs.

**Goal**: 10 distinct Korean fashion D2C buyer scenarios with BAS coverage +
Korean-baseline grounding.

---

## Required scenario structure

Same 10-field structure as `02_d2c_scenarios_cosmetics.md`.

## Coverage requirements

- 2+ per BAS metric (CCR / AAS / GCS)
- Mix: 무신사·29CM·W컨셉 (온라인 패션 플랫폼) / 스파오·탑텐 (SPA 저가) /
  소호몰 / 명품 리셀 (크림·솔드아웃) / 가심비 신상
- Cohorts: 20대 남성 (스트릿/캐주얼) / 20대 여성 (트렌드) / 30-40대
  (오피스룩, 캐주얼 분리) / 패션 인플루언서 추종 그룹
- At least 2 scenarios involve 인스타그램 발견 → 단톡방 공유 dynamics
- At least 1 scenario involves 무신사 사이즈 큐레이션 / 리뷰 기반 결정
- At least 1 scenario involves 리셀 시장 (Stockx-like, but Korea-specific:
  Kream, 솔드아웃) — uniquely Korean youth+name-brand dynamic
- At least 1 scenario involves K-pop idol 공항패션 또는 협찬 효과 (AAS)

## Specific anti-Western failure modes

- **사이즈/체형** — Korean clothing sizing differs from Western, AND Korean
  consumers reference body-type comparison ("내가 OO이랑 비슷한데...") more
  than abstract size charts. Western LLM gives "size M" advice; Korean
  reality is "OO 인플루언서가 이걸 입었는데 키 X / 체형 Y야"
- **명품 vs 가심비** — Korean discourse around 가심비 (psychological-price
  ratio) is distinct from Western "value"; involves social-signal calculus
  Western models flatten
- **공구 (group buying)** — Korean 공구 dynamics (Naver Band, 단톡방-driven
  collective purchase for bulk discount) has no clean Western equivalent
- **인스타 협찬 표시** — Korean consumers are highly attuned to 협찬 / 광고
  표시 detection; trust dynamics differ from Western influencer scene

## Sources

- 무신사 / 29CM 카테고리 트렌드 리포트
- Naver Datalab 패션 검색 트렌드
- KCA 의류 분쟁 통계
- Kream / 솔드아웃 거래 데이터 (공개분)
- KOFICE K-fashion 한류 자료
- 사단법인 한국패션산업연구원

## Required meta footer

```
[meta]
verifiability_signal: high|medium|low
n_scenarios: 10
```
