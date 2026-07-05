# Roboquest

리서치 날짜: 2026-07-05

## 기본 정보

- **장르**: 1인칭 슈터 로그라이트 (FPS Roguelite)
- **개발사**: RyseUp Studios (프랑스 인디)
- **출시**: 2023년 11월 (Early Access 2020년)
- **플랫폼**: PC(Steam), Xbox
- **공식 사이트**: https://www.roboquest.com/
- **Steam**: https://store.steampowered.com/app/692890/Roboquest/
- **Wiki**: https://roboquest.wiki.gg/

---

## 핵심 시스템

### 1. 협동 플레이 (1~2인 로컬/온라인 Co-op)
- **솔로 밸런스 유지**: 혼자 할 때도 밸런스 깨지지 않음 — 적 HP/수가 인원에 비례
- **각자 독립 캐릭터**: 두 플레이어 각각 별도 클래스 선택 → 역할 분담 자연스럽게 발생
- **리소스 공유 없음**: 총알·체력 각자 관리 → 협업보다 병렬 플레이에 가까움
- **공유 부활**: 한 명 사망 시 파트너가 부활 가능 (일정 쿨타임) → 긴장감 유지

### 2. 클래스 & 빌드 다양성
- **Ranger / Guardian / Engineer / Recon / Elementalist** 등 클래스 보유
- 클래스별 패시브 능력이 크게 다름 → 조합 실험 유도
- **메타 진행(Meta Progression)**: 런 클리어마다 영구 업그레이드 포인트 획득 — 초반 난이도 완화

### 3. 이동 시스템 (코어 루프의 핵심)
- **Wall Run + 대시 + 점프** — 3D임에도 2D 스타일 이동 레이어
- 이동 자체가 재미 — 적 회피가 '잘 맞추기'보다 '잘 피하기'에 집중
- 빠른 이동 속도 → 짧은 TTK(Time to Kill)와 균형

### 4. 무기 & 업그레이드 시스템
- 방마다 무기 드롭 — 총·특수무기 2개 슬롯
- **워크벤치(Workbench)**: 중간 거점에서 업그레이드/재조합
- 업그레이드 경로가 분지 구조 → 빌드 방향 선택 강요

### 5. 맵 구조
- **3가지 세계(World)** → 각 2~3개 구역(Zone) → 보스
- 구역 내 분기 경로 (어려운 길 vs 쉬운 길)
- 비밀 방, 상인 방, 도전 방 포함

---

## 플레이어가 사랑하는 점

- **빠른 페이스**: 룸 클리어 속도가 빠름 → 높은 흐름감
- **협동 재미**: 2인이지만 과도하게 의존하지 않아도 됨 → 초보자 친화
- **빌드 다양성**: 클래스 × 무기 × 업그레이드 조합이 매 런 다른 경험 제공
- **시각적 피드백**: 히트 이펙트, 사운드 피드백 선명 → 전투 쾌감 높음
- **짧은 런 시간**: 1회 런 30~60분 → 부담 적음

---

## OnionCat 적용 포인트

### 협동 밸런스 설계
- Roboquest처럼 **한 명 사망 시 파트너 부활** 메커닉 적용 가능
- OnionCat의 특수성: 두 플레이어가 같은 몸 → 사망 개념을 HP 고갈로 통합하되 **조작 장애**(Cat만 움직이고 Onion 사용 불가, 또는 반대)를 부활 전 패널티로 활용

### 이동과 전투의 분리
- Cat의 대시 무적 + Onion의 방패 패리 → Roboquest의 '이동이 방어' 철학과 동일선
- **이동 자체를 전투 도구**로 디자인 — 데미지 회피가 반응속도보다 위치선택에 달리도록

### 구역 분기 경로
- Roboquest의 "어려운 길 / 쉬운 길" 분기 → OnionCat에서 **전투 방 vs 이벤트 방** 선택지로 구현
- 어려운 적 조합 방에는 더 좋은 업그레이드 드롭

### 메타 진행 참고
- 영구 업그레이드 포인트 시스템 → OnionCat의 메타 진행에 직접 적용 가능
- 단, 초보 개발자라면 **초기엔 런 내 업그레이드만** 구현하고 메타 진행은 나중에 추가

### 클래스 없는 버전의 OnionCat
- OnionCat은 클래스가 Cat/Onion으로 고정 → 빌드 다양성은 **업그레이드 선택**으로만 제공
- Roboquest의 클래스별 고유 스킬 → OnionCat에선 **특수 능력 업그레이드**(예: Cat 3단 대시, Onion 다중 탄환)로 역할

---

## 참고 링크

- [Steam 페이지](https://store.steampowered.com/app/692890/Roboquest/)
- [공식 위키](https://roboquest.wiki.gg/)
- [GameSpot 리뷰](https://www.gamespot.com/reviews/roboquest-review/1900-6418074/)
- [YouTube - Gameplay 영상 검색: "Roboquest co-op gameplay"](https://www.youtube.com/results?search_query=roboquest+co-op+gameplay)
