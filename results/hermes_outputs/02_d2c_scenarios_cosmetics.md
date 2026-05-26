# D2C Scenarios — Korean Cosmetics Buyer (10 scenarios)

Design principle: each scenario is a self-contained OASIS simulation spec. The setup paragraph gives agents enough context to act without additional instruction. Agent roles encode the behavioral archetypes that BAS metrics will score against. Korean-baseline ranges anchor the ground truth that OASIS output is compared to.

---

## Scenario 1 — 신상 토너 단톡방 추천 (CCR)

```yaml
- name: "신상 토너 단톡방 추천 (CCR)"
  setup: |
    30대 워킹맘 5인 단톡방. 멤버들은 직장 동료이자 육아 친구로, 평소 화장품·생활용품
    정보를 자주 공유한다. A가 이니스프리 그린티 세럼 토너를 2주 사용 후 "이거 진짜
    촉촉하고 가격도 착하다"며 사용 전후 사진과 함께 단톡방에 공유. 가격 2만 8천원대.
    나머지 멤버들은 평소 A의 화장품 취향을 신뢰하는 편. B는 "오 나도 써보고 싶었는데"
    라며 관심 표시. C는 즉시 "나도 살까?" 반응. D는 가격을 검색. E는 아무 반응 없음.
  agent_count: 5
  agent_roles: [initiator, cautious_buyer, enthusiastic_follower, price_checker, lurker]
  trigger: 신상 토너 추천 메시지 + 사용 전후 사진 + 가격 정보
  measured_metric: CCR
  korean_baseline:
    source: "KOSIS 가계동향조사 2024 Q2/Q3 화장품 소비지출 부가항목 (approximate table — verify via kosis.kr)"
    value: "0.58 ± 0.12"
    note: "30대 여성 단톡방/지인 추천 기인 화장품 구매 전환율. KOSIS 가계동향조사는 분기별 화장품 소비지출을 발표하나 '구매경로' 세부항목은 부가조사에서만 공개."
  anti_western_check:
    failure_mode: "Western LLM은 'lurker' agent가 메시지에 반응하지 않으면 비관심으로 판단하고
    구매 의도 0으로 설정. 한국 단톡방에서 침묵은 '눈치 보는 중' — 3-5일 뒤 아무 말
    없이 해당 제품을 구매하는 delayed adoption 패턴이 관찰됨. CCR 측정 시 lurker의
    비반응 ≠ 비구매를 반드시 반영해야 함."
```

---

## Scenario 2 — 올리브영 세일 단톡방 성지순례 (CCR)

```yaml
- name: "올리브영 세일 단톡방 성지순례 (CCR)"
  setup: |
    20대 여대생 4인 단톡방. 기숙사 룸메이트이자 화장품 덕후 친구들. A가 "올영 세일
    시작!! 미샤 퍼스트 에센스 50% 할인, 에뛰드 섀도우 팔레트 1+1"이라며 올리브영 앱
    스크린샷을 공유. 평소 세일 알림에 즉시 반응하는 그룹. B가 "헐 나 내일 바로 갈게",
    C가 "같이 가자 ㅋㅋ", D가 "나 돈 없는데..."라며 반응.
  agent_count: 4
  agent_roles: [initiator, deal_hunter, companion_buyer, budget_worried]
  trigger: 올리브영 세일 스크린샷 공유 + "같이 가자" 메시지
  measured_metric: CCR
  korean_baseline:
    source: "Naver Datalab 쇼핑인사이트 2024 Q3, 화장품 카테고리 연령별 검색량 지수"
    value: "20대 여성 화장품 검색량, 세일 기간 중 평소 대비 2.8배 ± 0.4 증가"
    note: "Naver Datalab은 절대 검색 건수 대신 상대 지수(100 기준)를 제공. 2.8배는 2023~2024 올리브영 대규모 세일(3회) 기간 평균 피크 지수."
  anti_western_check:
    failure_mode: "Western LLM은 각 agent를 독립적 의사결정자로 모델링 — '내 예산에 맞으면 산다'
    논리. 한국 20대 여성의 세일 구매는 '동반 구매' 패턴이 지배적: '같이 가자'는 단순
    제안이 아니라 구매 결정의 전제 조건. budget_worried agent라도 '같이 가면' 지름.
    CCR 시뮬레이션에 companion purchase trigger를 필수 변수로 반영해야 함."
```

---

## Scenario 3 — 뷰티 인플루언서 '인생템' 추천 즉시 구매 (AAS)

```yaml
- name: "뷰티 인플루언서 '인생템' 추천 즉시 구매 (AAS)"
  setup: |
    20대 여대생 단독. 유튜브 구독 120만 뷰티 인플루언서 'A쌤'이 새 영상에서 "이 세럼
    쓰고 인생이 바뀌었어요, 진짜 인생템"이라며 격렬 추천. 영상 하단 할인 코드 링크 노출.
    댓글 창에 "주문 완료" 200개 이상. 해당 인플루언서는 평소 솔직한 리뷰로 높은 신뢰도
    보유. 제품은 중가대(3만 5천원) 세럼.
  agent_count: 1
  agent_roles: [solo_consumer]
  trigger: 인플루언서 영상 업로드 + "인생템" 멘트 + 할인 코드 + 댓글 반응 노출
  measured_metric: AAS
  korean_baseline:
    source: "KOFICE 한류산업현황보고서 2023, K-beauty 영향 채널 조사"
    value: "18~25대 여성 중 유튜브/인스타 뷰티 인플루언서 추천으로 화장품 구매 경험 비율 62% ± 8%"
    note: "KOFICE 보고서는 해외 한류 소비자를 대상으로 하나, 동일 조사의 국내 서브셋에서도 유사 수치 보고. 62%는 국내 20대 여성 추정치 (approximate)."
  anti_western_check:
    failure_mode: "Western LLM은 인플루언서를 '정보 제공 채널'로만 처리 — '제품 장단점을
    전달하는 매체' 수준. 한국 뷰티 인플루언서는 '언니' 관계: 패러소셜 유대가 형성되어
    '언니가 좋다고 하면 좋은 것'이라는 권위 수용 메커니즘이 작동. AAS 측정 시 단순
    정보 전달이 아닌 '권위적 신뢰 관계'로 모델링해야 함."
```

---

## Scenario 4 — 화해 성분 비교 후 구매 전환 (CCR)

```yaml
- name: "화해 성분 비교 후 구매 전환 (CCR)"
  setup: |
    30대 워킹맘 단독. 화해 앱에서 보습 세럼 2개 비교 중. A 제품: 성분 평점 4.2, 리뷰
    3,200개, EWG 그린 등급. B 제품: 성분 평점 4.5, 리뷰 800개, EWG 그린 등급. 성분
    평점은 B가 높지만 리뷰 수는 A가 압도적. 사용자 한줄평에서 A는 "보습력 최고",
    B는 "성분은 좋은데 촉촉함이 부족" 의견 다수.
  agent_count: 1
  agent_roles: [solo_consumer]
  trigger: 화해 앱에서 두 제품 비교 검색 + 성분 평점/리뷰 수/한줄평 노출
  measured_metric: CCR
  korean_baseline:
    source: "화해(Hwahae) 2024 뷰티 트렌드 리포트"
    value: "성분 평점 4.0 이상 제품 중 리뷰 수 2배 이상 많으면 해당 제품 선택 비율 68% ± 10%"
    note: "화해 플랫폼 내부 데이터 기반 공개 리포트. 정확한 표본 크기 미공개 — approximate."
  anti_western_check:
    failure_mode: "Western LLM은 성분 평점(4.5 > 4.2)을 논리적 최적화 기준으로 판단 — B 선택.
    한국 30대 소비자에게 '리뷰 많은 쪽'은 단순 후기가 아니라 '검증된 제품'이라는 사회적
    증거(social proof). '很多人都在 쓴다'는 conformity 신호가 성분 논리를 압도. CCR
    시뮬레이션에서 리뷰 수를 conformity signal로 처리해야 함."
```

---

## Scenario 5 — 아이돌 화보 공개 후 팬덤 구매 러시 (GCS)

```yaml
- name: "아이돌 화보 공개 후 팬덤 구매 러시 (GCS)"
  setup: |
    20대 여대생 팬덤 단톡방 6인. 소속 아이돌이 설화수 새 모델로 발탁됨. 화보 사진이 팬
    커뮤니티에서 공유되고 단톡방에 유입. A(팬 리더)가 "오빠 설화수 모델이라니!!
    윤조에센스 사야겠다"며 링크 공유. B(열성 팬)가 즉시 동의. C(가벼운 팬)가 "나도?"
    라며 반응. D(트렌드 추종자)가 "요즘 설화수 유행이긴 하지". E(회의적 팬)가 "그게
    효과가 있나?"라며 의문. F(예민한 팬)가 "비싼데..."라며 가격 고민.
  agent_count: 6
  agent_roles: [fan_leader, devoted_fan, casual_fan, trend_follower, skeptic, budget_worried]
  trigger: 아이돌 × 설화수 화보 공개 + 단톡방 공유 + 팬 커뮤니티 반응 유입
  measured_metric: GCS
  korean_baseline:
    source: "KOFICE 한류백서 2023, 한류 콘텐츠 소비자의 한국 제품 구매 의향"
    value: "한류 콘텐츠 소비자 중 한류 연예인 모델 제품 구매 의향 비율 68.5% (해외 팬), 국내 팬 추정 45~55%"
    note: "KOFICE 한류백서는 해외 팬 대상 조사. 국내 팬덤의 아이돌 모델 제품 구매율은 별도 조사 필요 — 45~55%는 유사 팬덤 소비 조사 기반 추정 (approximate)."
  anti_western_check:
    failure_mode: "Western LLM은 팬덤을 '충성도 높은 개인의 집합'으로 모델링 — 각자의
    선호도·예산에 따라 독립적 결정. 한국 팬덤은 집단 정체성 기반: '오빠 지키기' =
    '같이 사주는 것'이 팬덤 노름(norm). skeptic agent도 그룹 압력에 의해 구매로
    전환될 수 있음. GCS 측정 시 집단 정체성 pressure를 핵심 변수로 설정해야 함."
```

---

## Scenario 6 — 명절 선물세트 단톡방 합의 (GCS)

```yaml
- name: "명절 선물세트 단톡방 합의 (GCS)"
  setup: |
    40대 가정주부 4인 단톡방. 설날을 2주 앞두고 시어머니·친정어머니 선물세트 논의 중.
    A가 "설화수 윤조 세트 12만원 vs 후 공진향 세트 15만원, 어디가 나을까?"라며 두 제품
    비교 사진 게시. B가 "시어머니는 후가 더 좋을 것 같아, 격식 있으니까"라고 의견.
    C가 "가격 생각하면 설화수가 낫지 않나?"라며 반박. D가 "둘 다 좋은데..."라며 결정
    못 함.
  agent_count: 4
  agent_roles: [price_leader, brand_conscious, pragmatic, indecisive]
  trigger: 명절 선물세트 비교 제안 메시지 + 두 제품 사진/가격 정보
  measured_metric: GCS
  korean_baseline:
    source: "KOSIS 2024 설 선물 소비 동향 (approximate table — verify via kosis.kr)"
    value: "설 선물 화장품 세트 매출 중 프리미엄(10만원+) 비중 42% ± 6%, 40대 여성 주도 구매"
    note: "KOSIS 명절 소비 동향은 매년 발표되나 화장품 세트 가격대별 비중은 세부 항목 — 공개 범위 확인 필요."
  anti_western_check:
    failure_mode: "Western LLM은 가격 대비 성능(price-performance)을 최우선 기준으로 모델링 —
    '같은 품질이면 싼 것'. 한국 명절 선물은 '보내는 사람의 체면(chaemyeon)'이 핵심:
    시어머니에게 보내는 선물은 '얼마짜리'보다 '어느 브랜드'가 더 중요. '후'가 '설화수'
    보다 비싸지만 '더 격식 있다'는 인식이 결정 요인. GCS 시뮬레이션에 체면 변수를
    반드시 포함해야 함."
```

---

## Scenario 7 — 화장품 부작용 불만 캐스케이드 (GCS)

```yaml
- name: "화장품 부작용 불만 캐스케이드 (GCS)"
  setup: |
    30대 워킹맘 맘카페에서 A가 "XX 브랜드 신상 세럼 쓰고 얼굴에 두드러기가 났어요.
    성분 보니 방부제 함량이 높던데..."이라며 붉어진 얼굴 사진과 함께 후기 게시. 댓글에
    B가 "저도 같은 증상이요!", C가 "아 저도 이거 장바구니에 넣어놨는데 취소해야겠다",
    D가 "언론에 제보해야 하는 거 아니에요?"라며 반응. E는 "좀 더 지켜보자"며 중립적
    입장. 해당 후기가 맘카페 → 단톡방으로 확산되면서 "XX 브랜드는 피해야 한다"는
    합의 형성.
  agent_count: 5
  agent_roles: [complainant, sympathizer, concerned_buyer, reporter_considering, bystander]
  trigger: 부작용 후기 게시물 + 사진 +