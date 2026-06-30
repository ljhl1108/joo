# Synthetik: Legion Rising

리서치 날짜: 2026-06-30

## 기본 정보

- **개발사**: Flow Fire Games (독일 2인 팀)
- **출시**: 2018년 Early Access → 2019년 정식 출시
- **플랫폼**: PC (Steam)
- **공식 사이트**: https://store.steampowered.com/app/528230/SYNTHETIK_Legion_Rising/
- **Steam 링크**: https://store.steampowered.com/app/528230/SYNTHETIK_Legion_Rising/
- **장르**: 탑다운 슈터 로그라이크

---

## 핵심 메카닉

### 1. 총기 조작 시스템 (Gun Mechanics)
Synthetik 최대 차별점. 모든 총기에 **실제 사격 흐름**이 구현됨:
- **수동 급탄 배출**: 탄창 교체 전 Q키로 탄피(Chamber) 수동 배출 필요
- **과열 관리**: 연속 사격 시 총기 과열 → 스페이스로 냉각 타이밍 맞춰야 함
- **걸림 현상(Jam)**: 무작위로 총기 걸림 발생 → 특정 입력으로 해제
- **리로드 타이밍**: 리로드 바에서 정확한 타이밍에 키 입력 → 보너스 효과

**결과**: 같은 총기도 조작 숙련도에 따라 DPS 차이 극심. '총기를 다룬다'는 물리적 감각 구현.

### 2. 클래스 시스템 (8종)
- Trooper, Riot Guard, Engineer, Assassin, Medic, Raider, Saboteur, Heavy Guard 등
- 각 클래스마다 패시브 능력 + 활성 스킬 세트 다름
- 클래스 선택이 빌드 방향을 결정

### 3. 아이템 & 칩 시스템
- **칩(Chips)**: 케릭터 강화 모듈 (총기 반동 감소, 이동속도 증가 등)
- **아이템**: 전투 중 사용 가능한 소모품 (수류탄, 의료 키트 등)
- **레어리티**: 4등급 (Common → Legendary)

### 4. 진행 구조
- 8개 구역(Zone), 각 구역마다 보스
- 방 클리어 → 다음 방 이동 (선형 + 일부 분기)
- **무기고 방**: 상점/무기 선택 방이 중간에 등장
- 도달 구역에 따라 영구적 메타 해금

### 5. 로컬 & 온라인 코옵 (2인)
- 2인 코옵 지원 (온라인/로컬 모두)
- 한 플레이어 사망 시 파트너가 부활 아이템으로 살릴 수 있음
- 각자 독립 인벤토리 → 아이템 교환 불가 (협력보다 병렬 플레이)

---

## 플레이어가 사랑하는 것

1. **총기 피드백**: 업계 최고 수준의 탑다운 슈터 게임 느낌. 소리, 이펙트, 반동 삼위일체.
2. **기계적 깊이**: 단순해 보이지만 총기 조작 마스터링에 수십 시간 소요
3. **다양성**: 클래스 × 총기 조합의 경우의 수가 방대
4. **투명한 난이도**: 죽었을 때 "내 잘못"이라고 느껴지는 설계 → 좌절감 < 성취감

---

## OnionCat 적용 포인트

### A. 탄창/재장전 피드백
Crop(양파) 플레이어의 투사체 발사에 **조작 레이어** 추가 가능:
- 투사체 발사 후 짧은 쿨타임 바 → 적절한 타이밍에 재사용 버튼 누르면 쿨타임 단축 (Just-Reload 시스템)
- 복잡성을 높이지 않고 "skill ceiling"을 만드는 방법

### B. 총기(투사체) 피드백 3요소
Synthetik에서 배울 것:
1. **사운드**: 발사음 + 착탄음 반드시 분리
2. **이펙트**: 총구 화염(Muzzle Flash) + 착탄 파티클
3. **카메라**: 발사 시 미세 흔들림 (CinemachineImpulse)

### C. 아이템 레어리티 컬러코딩
- Common: 회색, Uncommon: 초록, Rare: 파랑, Legendary: 금색
- OnionCat 업그레이드 아이템도 동일 컬러 코딩 즉시 적용 가능

### D. 구역 보스 패턴
Synthetik 보스는 **페이즈 전환** 없이 체력에 따른 행동 변화:
- 체력 50% 이하 → 추가 패턴 활성화
- 단순하지만 효과적 → OnionCat 초기 보스 설계 참고

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/528230/SYNTHETIK_Legion_Rising/
- 공식 위키: https://synthetik.fandom.com/wiki/SYNTHETIK_Wiki
- 개발자 인터뷰 (Game Feel 설계): https://www.gamedeveloper.com/design/the-making-of-synthetik
- 후속작 Synthetik 2 (2023): https://store.steampowered.com/app/1243320/SYNTHETIK_2/
