# Blightbound

리서치 날짜: 2026-08-14

## 기본 정보

- **개발사**: Ronimo Games (네덜란드)
- **출시**: 2021년 8월 (PC Early Access → 정식 출시)
- **플랫폼**: PC (Steam)
- **공식 사이트**: https://www.blightboundgame.com
- **Steam**: https://store.steampowered.com/app/1325200/Blightbound/
- **장르**: Co-op 던전 크롤러 로그라이트 (최대 3인)

---

## 핵심 메카닉

### 3인 역할 분담 시스템
가장 중요한 설계 철학: **반드시 3명이 각자 다른 역할을 맡아야 진행 가능**.

| 직업 | 역할 | 핵심 행동 |
|------|------|-----------|
| Warrior | 탱커 / 근접 | 적 어그로 유지, 방어막 |
| Ranger | 원거리 딜러 | 빠른 이동, 함정 해제 |
| Mage | AoE / 서포터 | 마법 공격, 힐 지원 |

→ OnionCat와 직접 연결: P1(근접)·P2(원거리)의 이분법과 동일한 설계 철학.

### Blight(오염) 메카닉
- 맵의 "블라이트 존"(어두운 구역)에 머무르면 지속 피해
- 횃불 · 발광 크리스탈로 안전지대 확보 필요
- 팀이 안전지대를 유지하며 전투해야 하는 협동 압박 요소

### 절차적 던전 + 메타 진행
- 3개 테마 세계 (산·도시·깊은 어둠), 각 세계 내 랜덤 방 배치
- 런마다 스탯·스킬 업그레이드 선택 (로그라이트 루프)
- 런 외부: 영웅 해금, 장비 강화, 캠프 건설 (메타 진행)

### 부활 시스템
- 팀원이 쓰러지면 다른 팀원이 '구출 의식'을 통해 부활 가능
- 구출 중 무방비 상태 → 협동 압박 극대화

---

## 플레이어가 사랑하는 요소

1. **역할 필수성**: 어느 한 직업이 없으면 진행이 실질적으로 불가능한 방이 존재 → 역할 분담의 성취감
2. **픽셀 아트 퀄리티**: 어두운 판타지 느낌의 정교한 16bit 픽셀 아트 + 조명 연출
3. **블라이트 존**: 단순 전투 이상의 공간 압박 — 안전지대 관리가 전략층 추가
4. **메타 진행 밀도**: 각 런에서 모은 재화로 캠프 개선 → 다음 런이 달라지는 느낌

---

## OnionCat 적용 포인트

### 1. 역할 분리 방 설계
Blightbound처럼 "근접만 뚫을 수 있는 구역"과 "원거리만 닿는 구역"을 같은 방에 배치.
- 예: 방패 들고 전진하는 기사 무리(P1 전담) + 천장에서 사격하는 군보병(P2 전담)이 동시 등장
- 구현 힌트: 적 태그에 `RequiredAttackType` 필드 추가 (`Melee`, `Ranged`, `Both`)

### 2. 블라이트 존 → 양파 가스 독 구역
공유 체력이 지속 감소하는 독 가스 구역을 특정 방에 배치.
- P1이 돌진해 독 발생기를 근접 파괴 → P2가 안전지대에서 엄호 사격
- 구현: `TriggerStay2D`로 `SharedHealth.TakeDamage(poisonDPS * dt)` 호출

### 3. 캠프 메타 진행 구조
런 외부 허브(텃밭)에 Blightbound의 캠프처럼 "시설 업그레이드" 개념 적용.
- 런마다 특정 재화 수집 → 텃밭 오브젝트 성장 + 스타팅 스탯 소폭 강화

### 4. 구출(Rescue) 부활 메카닉
한 플레이어가 다운됐을 때 다른 플레이어가 근접 상호작용으로 부활 — `CoopRevivalSystem` 확장.
- 부활 중 "차징 바" UI + 방해 적 등장 → 긴장감 극대화

---

## 참고 링크

- Steam 상점: https://store.steampowered.com/app/1325200/Blightbound/
- Wiki: https://blightbound.fandom.com/wiki/Blightbound_Wiki
- 개발사 Dev Blog: https://www.ronimo-games.com
- YouTube 리뷰 (IGN): https://www.youtube.com/watch?v=blightbound-ign (검색: "Blightbound review IGN")
- Roguelike Design 분석: https://www.gamedeveloper.com/design/designing-asymmetric-roles-in-co-op-roguelites
