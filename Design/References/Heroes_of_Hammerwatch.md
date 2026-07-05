# Heroes of Hammerwatch

리서치 날짜: 2026-07-05

## 기본 정보

- **장르**: 협동 던전 크롤러 로그라이트 (Co-op Roguelite Dungeon Crawler)
- **개발사**: Crackshell (스웨덴 인디)
- **출시**: 2018년 3월
- **플랫폼**: PC(Steam), Switch, PS4/5, Xbox
- **공식 사이트**: https://www.hammerwatch.com/
- **Steam**: https://store.steampowered.com/app/677120/Heroes_of_Hammerwatch/
- **Wiki**: https://hammerwatchwiki.com/

---

## 핵심 시스템

### 1. 협동 플레이 (1~4인 로컬/온라인 Co-op)
- **공유 자원**: 골드를 플레이어 전원이 공유 — 같이 모아서 같이 씀 → 협업 필수
- **각자 독립 HP**: 개별 캐릭터가 각자 HP 관리 → 부활 미션이 공동 목표
- **역할 분화 강제**: Paladin(근거리 탱크), Ranger(원거리), Wizard(AOE), Priest(힐) 등 클래스 간 상성
- **픽업 경쟁**: 아이템 드롭은 선착순 → 자연스럽게 "누가 먹어야 더 효율적?" 대화 유발

### 2. 메타 진행 (마을 업그레이드)
- **마을(Town)** 시스템: 런 실패 후 획득한 골드로 영구 건물 업그레이드
- 창고(Armory), 성전(Temple), 대장간 등 건물 종류별로 HP / 마나 / 장비 강화
- 초반 런 → 마을 발전 → 후반 런 난이도 하락 → 성취감 루프
- **멀티 메타 공유**: 같이 플레이한 파트너와 마을 업그레이드 공유됨

### 3. 던전 구조 & 층 시스템
- **선형 층 구조**: 1~3층 → 보스 → 다음 세계
- 각 층은 랜덤 방 배치 + 고정 보스방
- 비밀 방(Secret Room)에 강력 아이템 → 탐험 장려
- **스킵 가능한 층**: 일부 층 완전 클리어 필요 없이 보스방만 찾으면 됨 → 효율 vs 자원 딜레마

### 4. 아이템 & 파워업 시스템
- 금고(Chest) 오픈 → 무기/반지/아이템 드롭
- **아이템 희귀도**: 회색 < 파랑 < 보라 < 금 → 시각적 기대감
- 상점 방(Shop Room): 런 내에서 골드로 구매 가능
- **저주(Curse)** 시스템: 저주 상자 열면 패널티 + 보상 선택지 → 리스크 vs 리워드

### 5. 클래스 고유 플레이 스타일
- **Paladin**: 근거리 강타 + 방패 → 탱킹, OnionCat Cat 역할과 유사
- **Ranger**: 원거리 화살 + 이동속도 → OnionCat Onion 역할과 유사
- 각 클래스 스킬 2개(Primary + Special) → 조작 단순하지만 상황 판단 복잡

---

## 플레이어가 사랑하는 점

- **마을 성장 루프**: 런이 실패해도 진전하는 느낌 → 초보자 친화
- **Co-op 긴장감**: 공유 골드 + 파트너 부활 → 같이 살아남는 성취감
- **픽셀아트 미학**: 선명한 스프라이트, 읽기 쉬운 공격 패턴
- **짧은 런 가능**: 층 스킵 전략으로 빠른 런 가능 → 시간 효율
- **클래스 다양성**: 4인 파티 조합에 따라 완전히 다른 플레이

---

## OnionCat 적용 포인트

### 2인 역할 분화의 자연스러운 강제
- Hammerwatch의 Paladin(근접) + Ranger(원거리) 조합 → **OnionCat의 Cat(근접) + Onion(원거리)** 와 동일 구조
- 핵심 인사이트: **역할이 다르면 적에게 다가가는 방식도 달라진다** — Cat은 돌격, Onion은 포지셔닝
- 서로 다른 역할을 강제하는 적 디자인: 근접만 공격되는 적 + 원거리만 닿는 적 조합

### 공유 자원 시스템
- 골드/재화 공유 → OnionCat에서 **런 내 업그레이드 포인트 공유** 구현 참고
- 업그레이드 선택 시 "Cat 강화 vs Onion 강화 vs 공통 강화" 3가지 카테고리로 설계

### 메타 진행 — 마을 시스템
- 마을 건물 업그레이드 → **OnionCat 홈 베이스** 또는 마을 개념 도입 가능
- 기본 플레이: 런마다 1개 영구 능력 언락 → 플레이어 성장 체감

### 저주/리스크 시스템
- Hammerwatch 저주 상자(Curse Chest) → OnionCat에서 **위험한 방 선택지** 로 변환
  - "이 방 들어가면 Cat 속도 -20%, 하지만 희귀 업그레이드 보장"
  - 두 플레이어의 동의가 필요 → 협동 판단 유도

### 비밀 방 탐험 장려
- 랜덤 던전에 비밀 방 숨기기 → 벽 공격 or 특정 조건 → 보상
- 초보 개발자 구현 팁: 방 프리팹에 `SecretRoom` 태그 + 확률 기반 스포너

---

## 참고 링크

- [Steam 페이지](https://store.steampowered.com/app/677120/Heroes_of_Hammerwatch/)
- [공식 위키](https://hammerwatchwiki.com/)
- [YouTube - 협동 플레이 영상: "Heroes of Hammerwatch co-op"](https://www.youtube.com/results?search_query=heroes+of+hammerwatch+co-op+gameplay)
- [Steam 커뮤니티 가이드](https://steamcommunity.com/app/677120/guides/)
