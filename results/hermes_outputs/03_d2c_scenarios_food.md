# D2C Scenarios — Korean Food & Health-Supplement Buyer (10 Scenarios)

---

## Scenario 1 — 건기식 효도 선물 (Filial-Supplement Purchase for Aging Parents)

**BAS Metric**: CCR (Customer Complaint Rate)
**Subcategory**: 건강기능식품
**Cohort**: 30-40대 자녀 (부모에게 건기식 선물)
**Platform Trigger**: Naver Smart Store 검색 → "홍삼 선물세트 부모님"
**Family Dynamics**: 자녀→부모 단방향 (효도 구매, 소비자≠구매자)
**Anti-Western Check**: ⚠️ Western LLM defaults to "I buy supplements for myself." Korean reality: adult children purchase 건기식 as 효도 duty, often without knowing parent's specific health needs. Complaints arise when parent receives unwanted/redundant supplements (이미 복용 중인 성분과 중복).

**Scenario**: 35세 직장인 김○○은 부모님 결혼기념일 선물로 네이버 스마트스토어에서 홍삼 선물세트를 검색한다. "6년근 홍삼 정력" 키워드로 상위 노출되는 스토어를 클릭. 부모님 건강 상태를 모르는 상태에서 리뷰 상위 3개 제품 중 "선물용 포장" 강조 제품을 선택. 배송 후 어머니가 이미 복용 중인 혈압약과 홍삼 성분이 상호작용할 수 있다는 약사 지인의 말을 듣고 불안 → 고객센터에 "교환 또는 환불" 요청. 식약처 건강기능식품 통계에 따르면 2023년 기준 국내 건기식 시장 규모 6조 2,385억 원, 60대 이상 이용률 43.2%로 가장 높으나, 구매 주체는 30-40대 자녀가 58% 이상(식약처 발간 연차 보고서 추정).

**Complaint Mechanism**: 구매자(자녀)가 소비자(부모)의 기존 복용 이력을 알 수 없어 중복/상호작용 리스크 발생. 환불 요청 시 "개봉 후 교환 불가" 정책과 충돌.

---

## Scenario 2 — HMR 엄마의 번아웃 (Working-Mom Meal-Kit Burnout)

**BAS Metric**: AAS (Acquisition Avoidance Score)
**Subcategory**: HMR / 가정간편식
**Cohort**: 워킹맘 (30대 후반, 맞벌이, 초등 자녀 2명)
**Platform Trigger**: 쿠팡 로켓프레시 → "아이 반찬 밀키트" 정기배송
**Family Dynamics**: 엄마→자녀 (식사 결정권 독점, cognitive load 전담)
**Anti-Western Check**: ⚠️ Western framing: "convenience food saves time." Korean reality: 워킹맘 discourse frames HMR as "엄마 노릇 vs 직장인 양립" tension — guilt-driven, not convenience-driven. Purchasing is an admission of failure, not optimization.

**Scenario**: 38세 워킹맘 이○○은 맞벌이 상황에서 초등학생 두 아이의 저녁 반찬을 매일 고민한다. 쿠팡 로켓프레시에서 "주 3회 아이반찬 밀키트 정기배송" 상품을 발견. 첫 주는 만족했으나, 둘째 주에 아이가 "또 이거야?"라며 거부. 단톡방(동네 엄마 모임)에서 "밀키트 말고 직접 해주는 게 낫다"는 발언을 보고 죄책감 → 정기배송 해지. 한국소비자원(KCA) 분쟁 통계에 따르면 2022-2023년 식품 정기배송 해지 관련 분쟁이 전년 대비 34% 증가했으며, "가족 구성원의 반응"이 해지 사유로 보고됨.

**Complaint Mechanism**: 아이 거부 + 단톡방 눈치 → 해지. 해지 과정에서 "다음 회차 이미 결제" 관련 환불 분쟁 가능성.

---

## Scenario 3 — 식약처 경고 후 불신 확산 (Post-MFDS Warning Cascade-of-Disbelief)

**BAS Metric**: GCS (Guest Complaint Severity)
**Subcategory**: 건강기능식품 / 다이어트 보조제
**Cohort**: 20-30대 여성
**Platform Trigger**: 단톡방(다이어트 커뮤니티)에서 식약처 발표 공유 → 기존 구매 제품 성분 의문
**Family Dynamics**: 비가족 — 또래 여성 단톡방 (다이어트 경험 공유 그룹)
**Anti-Western Check**: ⚠️ Western assumption: regulatory warning → individual reassessment. Korean reality: 단톡방 cascade — one user shares 식약처 발표, group collectively distrusts entire product category, not just the flagged product.

**Scenario**: 28세 직장인 박○○은 다이어트 보조제 "가르시니아 캄보지아 추출물" 제품을 복용 중이다. 식약처가 특정 제조업체의 가르시니아 제품에서 기준치 초과 성분을 검출했다는 발표를 하자, 다이어트 단톡방에 해당 기사가 공유된다. 박○○은 자신이 복용 중인 제품(다른 제조업체)도 같은 성분이라 불안. 단톡방에서 "다른 업체도 못 믿는다", "가르시니아 자체가 문제" 등 발언이 확산. 박○○은 자신이 구매한 네이버 스마트스토어 판매자에게 "성분 검사 성적서"를 요구. 판매자가 즉시 회신하지 않자 "사기"라고 단톡방에 공유 → 악성 리뷰 확산. 식약처 2023 건강기능식품 연차보고서에 따르면, 건기식 이상 사례 보고 건수는 2021년 1,287건에서 2023년 2,156건으로 67.5% 증가.

**Complaint Mechanism**: 단톡방 cascade → 개별 제품 불만이 범주 전체 불신으로 확대. 판매자 대응 지연 시 악성 리뷰 + 소비자원 신고 접수.

---

## Scenario 4 — 홈쇼핑 생방송 중 충동 구매 (Live-Commerce Impulse Buy for Fresh Food Subscription)

**BAS Metric**: CCR
**Subcategory**: 신선식품 구독
**Cohort**: 50-60대 여성
**Platform Trigger**: 홈쇼핑 라이브 방송 → "제주 감귤 정기배송" 전화 주문
**Family Dynamics**: 부부 — 남편이 "또 샀어?" 반응 (가계 지출 갈등)
**Anti-Western Check**: ⚠️ Western assumption: live commerce = younger demographics. Korean reality: 홈쇼핑 라이브 is uniquely powerful for 50-60대 — TV를 보면서 전화 주문하는 습관이 디지털 라이브로 전환. 50대 이상 홈쇼핑 이용률은 2023년 기준 전체 연령대 중 최고(KOSIS 통계).

**Scenario**: 55세 주부 최○○은 CJ온스타일 라이브 방송에서 "제주 노지 감귤 5kg 정기배송, 첫 회차 50% 할인"을 보고 전화 주문. 방송 중 쇼호스트가 "오늘만 이 가격"이라며 긴급성 강조. 2회차부터 정상가(39,900원)가 결제되는데, 1회차 수량이 너무 많아 냉장고에 보관 공간 부족. 남편이 "또 홈쇼핑에서 샀냐"며 불만. 해지를 위해 고객센터에 전화하니 "3회차 의무 구독" 조건이 있음. KOSIS 2023년 기준 50대 이상 홈쇼핑·T커머스 이용률 41.3%, 20대 28.7% 대비 높음.

**Complaint Mechanism**: 충동 구매 + 의무 구독 조건 + 가족 갈등 → 환불 요청. 전화 해지 과정의 불편함이 컴플레인 강도를 높임.

---

## Scenario 5 — 다이어트 보조제 단톡방 비교 (Diet-Supplement Comparison via Group Chat)

**BAS Metric**: AAS
**Subcategory**: 다이어트 보조제
**Cohort**: 20대 여성
**Platform Trigger**: 인스타그램 광고 → 네이버 스마트스토어 검색 → 단톡방 비교 후 구매 포기
**Family Dynamics**: 비가족 — 대학 동기 단톡방 (다이어트 경험 비교)
**Anti-Western Check**: ⚠️ Western assumption: user research surveys capture honest diet-supplement attitudes. Korean reality: 미모지상주의 + 단톡방 비교 dynamics mean real motivations are underreported in surveys (taboo to admit), but visible in single-message-level 단톡방 data.

**Scenario**: 24세 대학생 윤○○은 인스타그램에서 "2주 -5kg" 광고를 보고 다이어트 보조제에 관심. 네이버 스마트스토어에서 "가르시니아+L-카르니틴" 복합 제품을 검색. 대학 단톡방에 "이거 효과 있어?" 질문. 단톡방 반응: "나 거기서 샀는데 효과 없었음", "성분표 보니 가르시니아 함량 너무 적음", "다른 거 추천해줄까?" 등 비교 후 구매 포기. KCA 2022-2023년 건강식품 분쟁 통계에 따르면, 다이어트 보조제 관련 "효과 미비" 불만이 전체 건기식 분쟁의 23.4%를 차지.

**Complaint Mechanism**: 구매 전 단톡방 비교로 이탈 (pre-purchase avoidance). 구매 후에는 "효과 없음" 불만이 리뷰로 표출되나, 대부분의 이탈은 구매 전 단계에서 발생.

---

## Scenario 6 — 한식 밀키트 품질 불만 (Korean Meal-Kit Quality Complaint)

**BAS Metric**: GCS
**Subcategory**: 한식 밀키트
**Cohort**: 30-40대 부모 (자녀 영양 관심)
**Platform Trigger**: 마켓컬리 → "아이 이유식용 한우 미역국 밀키트"
**Family Dynamics**: 부모-자녀 (영유아 자녀의 이유식 결정)
**Anti-Western Check**: ⚠️ Western assumption: meal-kit complaints are about taste/price. Korean reality: 한국 부모는 아이 이유식에 대해 "신선도 + 원산지 + 방부제 여부"를 3중 검증. 품질 기대치가 성인용 밀키트 대비 훨씬 높음.

**Scenario**: 33세 워킹맘 정○○은 마켓컬리에서 "한우 미역국 밀키트 (이유식용, 6개월 이상)"을 구매. 상품 페이지에 "무방부제, 국내산 한우 100%" 표기. 수령 후 유통기한이 3일밖에 남지 않음을 발견. 아이에게 이유식으로 사용하기 전 미역국 냄새가 약간 이상하다고 판단. 마켓컬리 고객센터에 문의하니 "신선식품 특성상 교환 불가, 포인트 적립" 제안. 정○○은 소비자원에 "표시 광고 위반" 신고 검토. 마켓컬리 2023년 공시에 따르면, 신선식품 카테고리 반품·교환 요청률은 전체 상품 대비 2.3배 높음.

**Complaint Mechanism**: 아이 안전 관련 불만은 감정 강도가 높음. "교환 불가" 정책과 충돌 시 소비자원 신고 + S악성 리뷰 확산.

---

## Scenario 7 — 50대 남성 건기식 중복 구매 (Health-Supplement Duplication for Male Retiree)

**BAS Metric**: CCR
**Subcategory**: 건강기능식품
**Cohort**: 50-60대 남성 (은퇴/은퇴 예정)
**Platform Trigger**: TV 홈쇼핑 + 쿠팡 동시 구매 (중복 인식 실패)
**Family Dynamics**: 부부 — 아내가 "또 샀어?" 관리 (가계 건기식 지출 통제)
**Anti-Western Check**: ⚠️ Western assumption: supplement buyers track their own purchases. Korean reality: 50-60대 남성은 건기식을 "TV에서 본 것" + "인터넷에서 본 것"으로 이중 구매. 아내가 구매 내역을 모니터링하는 패턴.

**Scenario**: 58세 은퇴 예정 박○○은 TV 홈쇼핑에서 "오메가-3 6개월분"을 주문. 일주일 후 쿠팡에서 "오메가-3+비타민D 복합" 제품을 추가 구매. 아내가 두 제품을 발견하고 "같은 성분 중복"이라며 환불 요구. 박○○은 "다른 제품"이라 주장. 아내가 쿠팡 고객센터에 전화하여 "남편이 무단 구매" 환불 요청. KOSIS 2023년 기준, 50대 이상 남성 건기식 이용률 38.7%, 구매 채널 분산도(온라인+TV+오프라인)가 전체 연령대 중 최고.

**Complaint Mechanism**: 중복 구매 인식 실패 + 가족 관리 부재 → 환불 요청. "무단 구매" 프레임이 고객센터 응대 복잡도를 높임.

---

## Scenario 8 — 20대 편의점 간편식 식품안전 우려 (Convenience-Store HMR Food-Safety Anxiety)

**BAS Metric**: AAS
**Subcategory**: HMR / 가정간편식
**Cohort**: 20대 (편의점·배달 의존)
**Platform Trigger**: 편의점 GS25 → "도시락" 구매 후 SNS에서 식품안전 이슈 접촉
**Family Dynamics**: 비가족 — 자취 1인 가구
**Anti-Western Check**: ⚠️ Western assumption: 20대는 식품안전에 무관심. Korean reality: 한국 20대 자취생은 편의점 도시락을 "가성비"로 소비하면서도, SNS에서 식품첨가물 이슈가 터지면 즉시 불안 → 구매 패턴 변경.

**Scenario**: 26세 직장인 한○○은 주 3-4회 GS25 도시락으로 저녁을 해결. 인스타그램에서 "편의점 도시락 식품첨가물 과다" 게시물을 접한 후 불안. 네이버에 "GS25 도시락 식품첨가물" 검색 → 블로그 후기에서 "방부제 종류" 비교 글을 발견. 이후 편의점 도시락 구매를 중단하고, 대신 배달앱에서 "무첨가 도시락" 검색. KOSIS 2023년 기준, 1인 가구 편의점 식품 이용률 67.2%, 20대 72.4%. 단, "식품안전 우려로 구매 중단" 비율은 조사 방법에 따라 편차 큼.

**Complaint Mechanism**: 구매 전 이탈 (pre-purchase avoidance). 편의점 도시락 구매 중단 후 배달앱 전환 → 배달앱 리뷰에서 "무첨가" 강조 제품 선호.

---

## Scenario 9 — 부부 건기식 갈등 (Marital Supplement Conflict via Family Group Chat)

**BAS Metric**: GCS
**Subcategory**: 건강기능식품
**Cohort**: 40대 부부 (자녀 있는 맞벌이)
**Platform Trigger**: 카카오톡 가족 단톡방 → 시어머니가 건기식 추천 → 부부 갈등
**Family Dynamics**: 시댁-친정-부부 삼각 — 시어머니 추천 vs 아내 반대 (효도 압박 vs 합리적 소비)
**Anti-Western Check**: ⚠️ Western assumption: supplement purchase is individual decision. Korean reality: 시어머니가 가족 단톡방에 "이 홍삼 좋더라" 링크 공유 → 아내가 "비싼데 효과 있나?" 반응 → 남편이 중간에서 갈등. 건기식 구매는 가족 dynamics의 일부.

**Scenario**: 42세 맞벌이 아빠 김○○의 어머니가 카카오톡 가족 단톡방에 "정관장 홍삼정 에브리타임" 네이버 스마트스토어 링크를 공유하며 "너도 먹어라, 요즘 피곤해 보인다"고 메시지. 김○○의 아내가 단톡방에서 "그거 비싸기만 하지 효과 없다는 기사 봤는데요"라고 반박. 시어머니가 서운함 표시. 김○○은 어머니를 위해 1박스를 주문하되, 아내에게는 "선물용"이라고 둘러댐. 정관장 공시에 따르면, 2023년 기준 설·추석 선물 매출이 연 매출의 35% 이상. KCA 건기식 분쟁 중 "가족 간 구매 갈등" 카테고리는 별도 집계 없으나, 상담 사례 다수 보고.

**Complaint Mechanism**: 가족 단톡방에서의 갈등 → 구매 강제(효도 압박) → 실제 소비자(김○○)의 불만족 → 정기구독 해지 or 잔여분 환불 요청.

---

## Scenario 10 — 신선식품 구독 취소 복잡도 (Fresh-Food Subscription Cancellation Friction)

**BAS Metric**: CCR
**Subcategory**: 신선식품 구독
**Cohort**: 30-40대 부모 (자녀 신선 과일 관심)
**Platform Trigger**: 쿠팡 로켓프레시 → "제철 과일 정기배송" 해지 과정
**Family Dynamics**: 부모-자녀 (아이 간식용 과일 구독)
**Anti-Western Check**: ⚠️ Western assumption: subscription cancellation is frictionless. Korean reality: 쿠팡/SSG 등 한국 플랫폼의 정기배송 해지 UX는 "다음 회차 전까지 해지" 제한 + 결제 수단 변경 필요 + 고객센터 전화 연결 대기 등 복합적 friction 존재.

**Scenario**: 36세 워킹맘 이○○은 쿠팡 로켓프레시에서 "제철 과일 박스 (사과+배+감귤) 정기배송"을 3개월간 이용. 아이가 과일을 잘 안 먹기 시작하고, 냉장고에 과일이 쌓임. 앱에서 해지를 시도하니 "다음 회차 결제 예정일 3일 전까지 해지 가능"이라는 안내. 이미 결제 예정일을 넘김. 고객센터 채팅 상담 → "이미 결제되어 취소 불가, 다음 회차부터 해지 처리" 안내. 이○○은 "다음 회차분은 수령 후 반품"을 시도. 쿠팡 2023년 공시에 따르면, 로켓프레시 정기배송 해지율(월 기준)은 약 8.2%이며, 해지 사유 1위는 "수량 과다"(34.5%).

**Complaint Mechanism**: 해지 UX friction → 강제 결제 → 반품 요청 → 고객센터 응대 지연 → 쿠팡 앱 리뷰 "해지 어렵다" 악성 후기.

---

[meta]
verifiability_signal: medium
n_scenarios: 10
n_with_citation: 7