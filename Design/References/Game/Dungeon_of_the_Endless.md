# Dungeon of the Endless

리서치 날짜: 2026-09-03

## 기본 정보

- **장르**: Roguelike Tower Defense / Tactical RPG
- **개발사**: Amplitude Studios (현재 SEGA 산하)
- **플랫폼**: PC (Steam), Xbox, Mobile
- **출시**: 2014
- **공식 사이트**: https://www.amplitude-studios.com/games/dungeon-of-the-endless
- **Steam**: https://store.steampowered.com/app/249050/Dungeon_of_the_Endless/
- **Wiki**: https://dungeon-of-the-endless.fandom.com/wiki/Dungeon_of_the_Endless_Wiki

---

## 핵심 게임 메카닉

### 기본 구조
- 탈출선에 실린 "크리스탈 코어"를 들고 절차적 생성 던전의 출구까지 운반
- 문을 열면 새로운 방이 생성되고, 방 개방 시 적 웨이브 스폰 가능
- 방에 자원(Industry, Science, Food, Dust)을 배치해 타워 및 지원 시설 건설
- 크리스탈 코어를 직접 운반하는 동안 적 공격 집중 → 진행 경로 설계 필수

### 협동 시스템 (1~4인 로컬/온라인)
- 각 플레이어가 독립된 영웅 캐릭터 조종
- 같은 화면 공유 또는 스플릿 없이 개별 카메라 (코어 운반 시 수렴)
- **역할 분담 강제**: 일부 영웅은 전투 특화, 일부는 자원 생산 특화
- 코어를 운반하는 플레이어는 느려지고 공격 불가 → 호위 필수
- 모든 플레이어가 죽으면 런 실패 (개인 부활 가능하지만 다른 플레이어가 소생)

### 자원 관리
- **Dust**: 모든 행동의 기본 자원, 문 개방 시 소비 또는 획득 가능
- **Industry**: 방어 시설 건설 속도
- **Food**: 영웅 HP 회복
- **Science**: 업그레이드/연구 속도
- 자원 배분이 팀 결정의 핵심 → 대화와 합의 필수

### 영웅 시스템
- 런 시작 시 영웅 선택, 각각 고유 패시브/액티브 스킬
- 예: Elise Ness (고스트): 아군 버프 전문 / Max Munro: 탱커 전투 전문
- 레벨업 시 스탯 포인트 배분 (힘/지능/민첩)

---

## 플레이어가 좋아하는 것

1. **"문 하나 열기가 두렵다"** — 매 문 개방 전 팀 토론 발생, 극한의 긴장감
2. **역할 분업의 자연스러운 발생** — 지시 없이도 누가 운반, 누가 경비할지 정해짐
3. **픽셀아트 + SF 분위기** — 독특한 SF-던전 크로스오버 미학
4. **짧은 런** — 평균 30~60분, 가볍게 즐기기 좋음
5. **학습 곡선** — 처음에는 어렵지만 시스템 이해 후 "아하!" 순간이 강력

### 자주 언급되는 불만
- 싱글 플레이는 멀티 대비 많이 어려움
- 튜토리얼 부족, 자원 시스템 직관성 낮음
- 온라인 멀티 연결 불안정

---

## OnionCat 적용 포인트

### 1. "운반 + 호위" 역할 강제 패턴
Dungeon of the Endless에서 코어 운반자는 느리고 무력해진다. OnionCat에서:
- **Cat이 특정 오브젝트(씨앗, 구출 NPC)를 운반하면 이동 속도 70%로 감소**
- Onion이 호위하지 않으면 지속 데미지
- 협력하지 않으면 클리어 불가능한 특수 방 타입으로 활용

### 2. "문 개방 결정" 긴장감 → "다음 방 선택" 긴장감
DotE의 핵심 재미는 "이 문을 열까 말까"의 팀 결정. OnionCat에서:
- 방 클리어 후 다음 방 입장 전 짧은 준비 시간 (5초) 부여
- 두 플레이어가 진행 방향 또는 보상 선택 시 **동시 확인(양손 버튼 동시)** 방식 실험 가능
- "서두르면 실수한다"는 긴장감 재현

### 3. 역할 특화 업그레이드 트리
DotE처럼 각 캐릭터가 전혀 다른 방향으로 성장:
- **Cat 전용 업그레이드**: 대시 사거리, 슬래시 범위, 이동속도
- **Onion 전용 업그레이드**: 투사체 종류, 방패 파리 반사각, 조준 보조
- 두 플레이어가 업그레이드 선택에서 합의해야 하는 시너지 아이템 도입

### 4. 방 공개 전 "정보 공유" 패턴
DotE에서 방을 열기 전 Science 투자로 방 내용을 미리 볼 수 있음. OnionCat에서:
- 특정 아이템/스킬 보유 시 문 너머 적 타입 미리 표시 (원거리형/근거리형)
- 팀이 미리 전략을 잡을 수 있게 → 협력 결정의 깊이 증가

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/249050/Dungeon_of_the_Endless/
- GameSpot 리뷰: 8/10 "Roguelikes만의 협력 경험"
- PC Gamer 전략 가이드: https://www.pcgamer.com/dungeon-of-the-endless-guide/
- 팬덤 Wiki: https://dungeon-of-the-endless.fandom.com/wiki/Dungeon_of_the_Endless_Wiki
