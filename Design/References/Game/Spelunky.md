# Spelunky

리서치 날짜: 2026-09-21

## 기본 정보

- **개발/출시**: Derek Yu (개인 → Mossmouth), 2012 (HD) / 2020 (2)
- **플랫폼**: PC, Xbox, PS4, Switch
- **장르**: 플랫포머 로그라이크
- **공식 사이트**: https://www.spelunkyworld.com
- **Steam (Spelunky 2)**: https://store.steampowered.com/app/418530/Spelunky_2/
- **위키**: https://spelunky.fandom.com/wiki/Spelunky_Wiki

---

## 핵심 메카닉

### 절차적 레벨 생성 (Procedural Level Generation)
Spelunky의 레벨 생성은 게임디자인의 교과서적 사례:
1. **4×4 방 격자** (총 16개 방 슬롯)
2. 각 슬롯에 사전 제작된 **룸 템플릿** 중 하나 배치
3. 시작에서 출구까지 **반드시 통과 가능한 경로(critical path)** 보장
4. 이후 세부 타일을 무작위 규칙으로 채움 → 플레이 가능성과 무작위성 동시 확보

이 방식 덕에 어떤 레벨이 나와도 항상 **클리어 가능**하면서 **매번 다른 경험** 제공.

### 물리 기반 상호작용
- **모든 오브젝트가 물리 적용**: 돌, 폭탄, 화살, 적, 보물 모두 튕기고 굴러다님
- 플레이어가 오브젝트를 들어서 던지거나, 적을 방패로 쓰거나, 시체를 덫 해제에 사용
- → **창의적 문제 해결**을 강요 (정해진 풀이 없음)

### 카르마 시스템 (Karma/Consequence)
- 상점 도둑질 → 특정 구역에서 상점주인이 영원히 적이 됨
- 신성한 제단 파괴 → 해당 신의 분노(저주) 발생
- **행동에 결과**가 따르는 시스템 → 플레이어가 세계를 살아있는 것으로 느낌

### 일일 도전 (Daily Challenge)
- 매일 같은 씨드로 전 세계 플레이어가 **동일한 레벨**에서 한 번만 도전
- 점수 랭킹으로 경쟁 → 반복 플레이 동기 강화

### 아이템 생태계
- 아이템들이 서로 시너지/충돌: 폭탄 + 용암 = 다이아몬드 생성
- **숨겨진 시스템**을 발견하는 재미가 핵심 장기 유지 요인

---

## 협력 요소 (Spelunky 2 기준)

- **최대 4인 로컬 쿱**
- **아이템 쟁탈**: 같은 아이템을 여러 명이 집으려 할 때 충돌 발생 → 의도적 긴장
- **아군 공격(friendly fire) 옵션**: 켜면 팀킬 가능 — 웃음 포인트
- **동반 사망**: 한 명이 죽어도 다음 레벨 시작 시 부활 (하트 소비)
- **레거시(Legacy) 시스템(Spelunky 2)**: 캐릭터 사망 시 후계자로 계속 → 가계도 형성

---

## 플레이어가 좋아하는 점

- **"내 탓" 원칙**: 모든 죽음이 납득 가능 → 억울함 없음
- 세계의 내부 논리가 일관 → 창의적 공략법 무한
- 레벨 암기 불가 → 매번 새로운 탐험 감각
- 빠른 재도전 (런 하나 5~15분) → "한 판만 더" 중독성
- 히든 지역/아이템 발굴의 탐험 만족감

---

## OnionCat 적용 포인트

### 1. 절차적 방 생성 방식
Spelunky의 **4×4 격자 + 크리티컬 패스 보장** 방식은 OnionCat 던전 설계에 직접 적용 가능:
- 방 슬롯 수를 3×3 또는 4×3으로 설정
- 각 슬롯에 프리팹 방 목록 중 무작위 선택
- 시작(입구) → 출구 간 연결 경로를 생성 알고리즘이 먼저 확보한 뒤 나머지 방 채우기
- → `Procedural_Dungeon_Generation.md` 참고, Spelunky 방식으로 구현하면 난이도 보장

### 2. 행동-결과 피드백 루프
Nuclear Throne처럼 OnionCat도 플레이어 행동이 세계에 영향을 미치면 몰입도 상승:
- 상점 파괴 → 이후 방에서 적 상점주인 추가 스폰
- 특정 적 처치 순서 → 보스 방 변형

### 3. 일일 도전 씨드 시스템
Spelunky의 데일리 챌린지처럼 **오늘 날짜를 씨드로 써서** 모든 플레이어가 동일한 런을 경험하게 하는 기능은 OnionCat 재방문 유인으로 강력:
- Unity `Random.InitState(seed)` 사용
- 씨드 = `System.DateTime.Today.GetHashCode()` 또는 YYYYMMDD 정수값

### 4. 물리 기반 상호작용
현재 OnionCat의 씨앗 투사체에 **바운스(리코셋) 메카닉** 추가 검토:
- Spelunky처럼 "벽에 튕겨서 코너 공격" 전략 가능
- `Physics2D.Bounce` PhysicsMaterial 활용

### 5. "내 탓" 설계 원칙
OnionCat의 적 공격에 **명확한 예고(텔레그래프)** 필수:
- 근접 공격 적 → 선명한 차지업 애니메이션
- 투사체 발사 적 → 발사 전 조준선 또는 발광 이펙트
- 플레이어가 "미리 알 수 있었는데 못 피했다"고 느껴야 함

---

## 참고 링크

- [Spelunky 제작기 (Derek Yu 저서)](https://bossfightbooks.com/products/spelunky-by-derek-yu)
- [GDC 2011: Designing Spelunky's Level Generation](https://www.gdcvault.com/play/1014704/Spelunky)
- [Darius Kazemi의 Spelunky 레벨 생성 분석](https://tinysubversions.com/spelunkyGen/)
- [Spelunky 공식 Wiki](https://spelunky.fandom.com)
