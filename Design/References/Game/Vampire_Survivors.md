# Vampire Survivors

## 기본 정보

- **장르**: 불릿 헤븐(Bullet Heaven) / 서바이버 라이크(Survivors-like)
- **개발사**: poncle (개발자: Luca Galante, 사실상 1인 개발로 시작)
- **출시**: 2021년 12월 (Steam Early Access), 2022년 10월 (정식 출시)
- **가격**: 출시 당시 $0.99 (지금은 $4.99) — 저가 전략 성공 사례
- **공식 사이트**: https://poncle.games/vampire-survivors
- **Steam**: https://store.steampowered.com/app/1794680/Vampire_Survivors/
- **위키**: https://vampire-survivors.fandom.com/wiki/Vampire_Survivors_Wiki

---

## 핵심 메카닉

### 자동 전투 시스템
- **플레이어 입력**: 이동(WASD/조이스틱)만. 공격은 완전 자동
- **무기 자동 발사**: 방향·타이밍 모두 자동 계산
- 결과: 시각적 혼돈(총알 지옥)이지만 플레이어는 포지셔닝에만 집중 → 접근성 극대화

### 런 내 성장
- **경험치 & 레벨업**: 적 처치 → 경험 보석 드롭 → 레벨업 시 3가지 선택지
  - 새 무기 획득 / 기존 무기 레벨업 / 패시브 아이템 획득
- **무기 진화(Evolution)**: 특정 무기 MAX + 특정 패시브 아이템 보유 → 합체해 강력한 진화 무기 생성
  - 예: 채찍(MAX) + 빈 토톰 → 피의 채찍(진화)
- **파워 판타지**: 후반부엔 수천 마리 몬스터를 한 번에 쓸어버리는 쾌감

### 런의 구조
- **30분 런**: 타이머 종료 시 "저승사자(Death)" 등장 → 런 강제 종료
- 시간이 지날수록 몬스터 밀도·속도 증가
- 맵 탐색 요소: 상자, 무기 획득 지점, 비밀 캐릭터 해금

### 메타 진행
- **골드**: 런 중 적 처치/상자에서 획득 → 런 종료 후 보관
- **파워업(Power Up)**: 메인 화면에서 골드 소비 → HP, 이동속도, 쿨다운, 행운 등 영구 수치 증가
  - 각 수치 소액 증가 여러 단계 → 그라인딩 부담 최소화
- **캐릭터 해금**: 특정 조건(특정 무기 레벨 10 달성 등)으로 새 캐릭터 해금

---

## 플레이어가 사랑하는 것

1. **낮은 진입 장벽**: 1분 만에 게임 이해 가능. 이동만 하면 됨
2. **시각적 폭발감**: 화면을 가득 채운 총알 → 몬스터 한 방 처리 장면의 만족감
3. **비밀·발견의 기쁨**: 숨겨진 캐릭터, 무기 진화 조합 발견 → 커뮤니티 활성화
4. **짧은 런**: 30분 → 출퇴근 중에도 완주 가능
5. **실패해도 보람**: 런 실패해도 골드·경험 적립 → 영구적 성장감

---

## 1인 개발 교훈 (초보 개발자 시사점)

- **완성 우선**: Vampire Survivors는 그래픽 퀄리티보다 게임 루프 완성에 집중
- **무기 조합**: 소수의 아이템도 조합 가능성이 크면 콘텐츠 풍부하게 느껴짐
- **숫자의 마력**: 레벨업·골드 누적 숫자가 쌓이는 시각적 피드백 → 심리적 진행감
- **낮은 가격 + 높은 완성도** → 입소문 마케팅

---

## OnionCat 적용 포인트

| Vampire Survivors 요소 | OnionCat 적용 |
|----------------------|---------------|
| **무기 진화 시스템** | Cat 근접 능력 + Onion 원거리 능력 특정 조합 → "협동 진화 기술" 해금. 예: 갈퀴 슬래시 + 관통 투사체 → 회오리 사이클론 |
| **런 내 레벨업 선택지 3가지** | 매 방 클리어 후 3장 카드 뽑기 → Cat·Onion·공유 버프 중 선택 |
| **메타 골드 시스템** | 런 실패해도 "씨앗(Seed)" 일부 보관 → 영구 스탯 소폭 증가. 실패 보상감 제공 |
| **파워 판타지 곡선** | 초반 버거운 적 → 후반 한 방에 화면 쓸기 → OnionCat도 런 후반 압도감 연출 설계 |
| **30분 런 구조** | 로그라이크 런 시간을 15~20분으로 제한 → 부담 없는 세션 길이 |
| **비밀 해금 조건** | 특정 적을 처음 처치 시 새 룸 타입 해금 등 발견 요소 삽입 |

---

## 참고 링크

- Vampire Survivors Wikipedia: https://en.wikipedia.org/wiki/Vampire_Survivors
- 핵심 분석 (Lost Attic Games): https://www.lostatticgames.com/post/how-vampire-survivors-made-me-rethink-the-concept-of-the-core-gameplay-loop
- The Secret Sauce 분석: https://jboger.substack.com/p/the-secret-sauce-of-vampire-survivors
- 공식 Wiki: https://vampire-survivors.fandom.com/wiki/Vampire_Survivors_Wiki
