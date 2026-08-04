# Nuclear Throne

리서치 날짜: 2026-08-04

## 기본 정보

- **개발사**: Vlambeer
- **출시**: 2015년 12월 5일 (Steam Early Access 2013 시작)
- **플랫폼**: PC, PS4, PS Vita, Switch
- **장르**: 탑다운 2D 로그라이크 슈터
- **Steam**: https://store.steampowered.com/app/351090/Nuclear_Throne/
- **위키**: https://nuclear-throne.fandom.com/wiki/Nuclear_Throne_Wiki
- **공식 사이트**: https://www.vlambeer.com/

---

## 핵심 시스템

### 캐릭터 시스템 (13종)
각 캐릭터가 완전히 다른 플레이 스타일을 제공:
- **Fish**: 특수 능력으로 롤(회피), 총기 특화
- **Crystal**: 방어막 생성, 초보자 친화
- **Eyes**: 원거리 정신 공격, 유리 대포
- **Melting**: 매 레벨 HP -1, 대신 강력한 변이

각 캐릭터마다 고유 패시브 + 액티브 스킬 1개 → **OnionCat처럼 역할 분담 강제**

### 변이(Mutation) 시스템
- 레벨업마다 4개 중 1개 선택
- 200개 이상의 변이 카드
- 변이끼리 시너지 발생 (예: "Stress" + "Bloodlust")
- 카테고리별 분류: Red(공격), Green(기동), Yellow(총기), Purple(특수), Blue(원거리)

### 무기 시스템
- 피스톨, 샷건, 에너지건, 근접무기, 폭발물 등 100종 이상
- 무기는 바닥에서 줍는 방식 (인벤토리 없음, 2슬롯만)
- 탄약 관리: 방사선(Rads)은 XP, 탄약은 별도 자원

### 레벨 구조
- 7개 월드 (Sewers → Desert → Jungle → Frozen City → Labs → Crystal Caves → Nuclear Throne)
- 각 월드 2~3 레벨 + 보스
- 완전 절차생성: 방 배치, 적 조합, 무기 드롭 모두 랜덤

### 2인 협동
- 로컬 2인 코업 지원
- 각자 독립적으로 행동 (같은 화면 공유)
- 한 명이 죽으면 기다리다가 다음 방에서 부활 가능
- 둘이 다른 역할로 플레이 가능 (근접 캐릭터 + 원거리 캐릭터)

---

## 플레이어가 사랑하는 것

1. **Juicy 피드백**: 히트스톱, 카메라 흔들림, 파티클이 매우 과장됨 → 타격감 극강
2. **단계적 난이도 상승**: 초반엔 쉽다가 후반부에 급격히 어려워짐
3. **캐릭터 개성**: 13캐릭터가 전혀 다른 게임처럼 느껴짐
4. **빠른 런 길이**: 1런 = 15~30분 (초보) / 5~10분 (숙련)
5. **B.U.T.T.S 시스템**: Daily Challenge, Throne Butt (뉴게임+ 개념)

---

## OnionCat 적용 포인트

### 1. 역할 강제 메커니즘 참고
Nuclear Throne에서 근접 캐릭터(Crystal, Rebel)와 원거리 캐릭터(Eyes, Rogue)는 자연스럽게 역할 분담이 된다. OnionCat은 **시스템으로 강제**한다는 점이 차별점:
- 특정 적은 근접(Cat)만 처치 가능
- 특정 적은 원거리(Crop)만 처치 가능
→ 2인 협력이 선택이 아닌 **필수**가 되는 설계

### 2. 변이 시스템 응용
Nuclear Throne의 변이 분류(근접/원거리/기동/방어)처럼 OnionCat도 Cat 전용 변이 / Crop 전용 변이 / 공용 변이로 분류하면 빌드 다양성이 생김

### 3. 피드백 강도 참고
Vlambeer의 "Game Feel" 철학:
- 총알이 없어도 발사 소리가 먼저 들림 (오디오 선행)
- 히트 시 0.05초 히트스톱
- 적 피격 시 흰색 플래시 + 소량 넉백
→ OnionCat 전투 피드백 설계의 기준점으로 삼기

### 4. 2인 부활 시스템
죽은 플레이어가 다음 방 진입 시 부활하는 방식 → Coop_Revival_System.md 참고하여 OnionCat에 맞게 변형 (공유 몸이므로 한 명이 죽으면 런 종료가 맞음)

### 5. 무기 드롭 밸런스
2슬롯 무기 시스템으로 선택의 강요가 발생함. OnionCat은 Cat의 근접 + Crop의 원거리가 고정이므로, 업그레이드 아이템이 이 역할에 맞게 설계되어야 함.

---

## 개발 인사이트 (Vlambeer 공개 자료 기반)

- **GDC 2013 "Game Feel"**: 타격감을 만드는 7가지 요소 — 화면흔들림, 소리, 파티클, 스톱모션, 에임보조, 스폰, 잔상
- **히트박스 철학**: "너그럽게" — 플레이어 히트박스는 실제 스프라이트보다 30% 작게
- **총알 속도**: 초당 20타일 이상 → 예측 가능성보다 반응 속도 중시

---

## 참고 링크

- https://store.steampowered.com/app/351090/Nuclear_Throne/
- https://nuclear-throne.fandom.com/wiki/Nuclear_Throne_Wiki
- Vlambeer GDC 2013 "Game Feel" 강연: https://www.gdcvault.com/play/1017965
- Vlambeer YouTube (개발 일지): https://www.youtube.com/@Vlambeer
