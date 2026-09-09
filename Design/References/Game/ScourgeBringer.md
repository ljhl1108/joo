# ScourgeBringer

리서치 날짜: 2026-09-09

## 기본 정보

- **장르**: 로그라이트, 액션 플랫포머 (No-floor aerial combat)
- **개발사**: Flying Oak Games (Dead Cells 팀 출신)
- **출시**: 2021년 (Early Access 2019)
- **공식 사이트**: https://www.flyingoakgames.com/scourgebringer
- **Steam**: https://store.steampowered.com/app/1037020/ScourgeBringer/
- **위키**: https://scourgebringer.fandom.com/wiki/ScourgeBringer_Wiki

---

## 핵심 메카닉

### 1. 무중력 공중 전투 (Zero-Gravity Aerial Combat)
- 바닥/중력 없음 — 플레이어가 항상 공중에 떠 있으며 자유롭게 이동
- 이동: 조이스틱/WASD로 8방향 즉각 이동, 대시로 순간이동
- 적을 타격하면 **튕김(rebound)** 이 발생 → 연속 공중 체인 가능
- 공중 전투 → 파쿠르 감각이 아니라 **공중 격투** 감각

### 2. 근접 체인 콤보 + 원거리 총기 혼합
- 근접: 칼 / 원거리: 총 (두 가지 입력 상시 사용)
- 적에게 근접 연속 타격 → 스킬 쿨다운 단축 → 퍼펙트 닷지 타이밍
- 총은 무한 탄 but 근접을 쓸수록 총이 강해지는 시너지 구조

### 3. 퍼펙트 닷지 (Perfect Dodge / Parry)
- 적 탄환 발사 직전에 닷지 → 짧은 무적 + 반격 기회
- 타이밍 성공 시 잠깐 슬로우 모션 발동 → 반격 창
- Celeste / Dark Souls 패리와 유사하나 공중에서 이루어짐

### 4. 룸 구조 — 밀봉 전투방
- 진입 시 문이 잠김, 모든 적 처치 시 열림 (Enter the Gungeon 구조)
- 방 크기 작음 → 집중 전투, 회피 공간 제한
- 공중 스크롤: 방 경계 없이 수직/수평으로 이동 가능한 오픈 스페이스

### 5. 업그레이드 시스템 (Weapon & Talent)
- 무기 업그레이드: 능력 선택지(카드 3장 중 1장) — 즉각 강화
- 탤런트 시스템: 패시브 능력 트리 — 런 내 경험치로 해금
- 저주(Curse): 특정 능력 선택 시 부가 단점 → 위험-보상 구조

### 6. 메타 진행 (Crystal / Guardian System)
- 런 후 크리스탈 획득 → 허브에서 영구 언락
- 수호자(Guardian): 강력한 보스 NPC, 특정 수호자 처치 시 런 내 능력 해금

---

## 플레이어가 좋아하는 것

- "공중 전투의 자유로움" — 어디서나 싸울 수 있는 해방감
- "적을 연속 타격할 때의 리듬감" — 근접 체인이 주는 댄스 같은 전투
- "퍼펙트 닷지 성공의 쾌감" — 슬로우 모션 반격 순간
- "빠른 런 시간" — 한 런이 20~40분으로 짧고 집중적
- 정밀한 히트박스 / 예측 가능한 적 패턴 → 실력 향상 체감

---

## OnionCat 적용 포인트

### 적용 1: Cat 근접 → Onion 총기 시너지 구조
ScourgeBringer에서 "근접 타격 → 원거리 강화"처럼:
- P1(Cat)이 근접 슬래시 N회 연속 히트 → P2(Onion) 투사체 대미지 일시 +50%
- 협력 시너지 수치를 UI로 표시 → 두 플레이어가 동시에 붙어 싸울 동기 부여
- 구현: `CombatSynergyCounter.OnMeleeHit() → synergy++` → Onion의 ProjectileDamageMultiplier에 반영

### 적용 2: 공중 이동감 (중력 처리)
OnionCat은 탑다운이라 바닥이 있지만:
- 슬래시 시 Cat이 타격 방향으로 **짧게 이동** (스커지브링거 튕김 느낌)
- 슬래시 히트 → `Rigidbody2D.AddForce(hitDirection * slashBoost)` → 타격감 + 전술 이동 동시 구현
- 슬래시 방향이 이동 방향이 됨 → P1 조작이 공격과 이동을 동시에 담당하는 역할감 강화

### 적용 3: 퍼펙트 타이밍 → 패리로 대응
- ScourgeBringer 퍼펙트 닷지 → OnionCat P2 방향 패리(DirectionalShield)로 대응
- 적 탄환 발사 직전 패리 성공 → 탄 반사 + Cat에게 시너지 게이지 보너스 전달
- 패리 타이밍 창 시각화: 적 탄환 발사 0.15초 전 "패리 윈도우" 흰 링 이펙트 표시

### 적용 4: 방 설계 — 집중 전투 공간
- 방 크기를 작게 유지 (화면의 60~70%) → 회피 공간 제한 → 긴장감
- 방 외곽에 벽 / 장애물 배치 → Cat 슬래시 튕김 이동이 벽에 막히는 상황 발생
- 좁은 공간에서 근접+원거리 협력의 필요성 극대화

### 적용 5: 빠른 런 템포 설계
- ScourgeBringer처럼 런 1회를 20~30분으로 설계
- 방 수: 3층 × 5~7개방 = 15~21개방, 각 방 30초~2분 소요
- 런이 짧아야 2인 플레이어 모두 집중력 유지 / "한 판 더" 동기 부여

---

## 기술 참고 사항

- Unity 기반 개발 (Devlog에서 확인 가능)
- 공중 이동: Rigidbody2D + 마찰 없는 LinearDrag 최소화 설정 → 미끄러운 느낌
- 히트박스: 픽셀 단위 정밀도보다 반응성 우선 → 너그러운 히트박스 철학

## 참고 링크

- Official Trailer: https://www.youtube.com/watch?v=HyeOUzfKPpE
- Flying Oak Devlog: https://www.flyingoakgames.com/news
- ScourgeBringer Game Design Analysis (Mark Brown / GMTK): https://www.youtube.com/watch?v=qb1cNriCYSs
- Steam Community Hub: https://store.steampowered.com/app/1037020/ScourgeBringer/#community
