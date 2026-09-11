# Furi

리서치 날짜: 2026-09-11

## 기본 정보

- **개발사**: The Game Bakers (프랑스 인디)
- **출시**: 2016년 7월 (PS4), 이후 PC/Switch
- **공식 사이트**: https://www.thegamebakers.com/furi/
- **Steam**: https://store.steampowered.com/app/423230/Furi/
- **위키**: https://furi.fandom.com/
- **장르**: 보스 러시 액션, 슈터 혼합

---

## 핵심 메카닉

### 1. 듀얼 레인지 전투 시스템 (OnionCat 핵심 레퍼런스)
Furi의 모든 전투는 **근접(Melee)**과 **원거리(Ranged)**의 혼합으로 구성됨.

| 상황 | 최적 수단 | 이유 |
|------|----------|------|
| 보스가 근접 | 원거리 포지셔닝 후 사격 | 근접 공격 피하며 딜 |
| 보스가 먼 거리 | 돌진 후 근접 연격 | 탄막 패턴 끊기 |
| 보스 취약 순간 | 둘 다 동시 사용 | 최대 피해 |

→ **"근접 약점 vs. 원거리 약점"이 보스마다 다름** — OnionCat의 핵심 컨셉과 1:1 대응.

### 2. 패리(Parry) 시스템
- 적 공격 직전 정확한 타이밍에 방어 버튼 → 피해 무효 + 반격 기회
- **성공 시 슬로우**: 히트스톱 + 시간 감속 → 극적인 피드백
- **실패 시 큰 피해**: 하이리스크-하이리워드 → 긴장감 유지
- Hollow Knight의 Crystal Heart 패리와 유사하나 Furi는 훨씬 전면적으로 활용

### 3. 대시 / 무적 시간
- 짧은 순간이동형 대시 (약 0.2초 무적)
- 탄막을 뚫고 가까이 접근하는 핵심 기동기
- 쿨다운 없음, 무한 사용 가능 → 대신 연속 대시 불가 (짧은 선딜)

### 4. 체력 구조 (두 레이어 HP)
- **실드(외피)**: 원거리 딜로 깎음 → 실드가 0 되면 취약 상태
- **HP(내피)**: 취약 상태에서 근접 공격 시 대미지 → 실제 체력 소모
- 두 레이어를 번갈아 공략해야 하는 구조 → OnionCat의 "근접/원거리 각각 필요한 적" 구현의 완벽한 레퍼런스

### 5. 보스 러시 순수 구조
- 일반 스테이지 없음, 오직 보스들만
- 각 보스 사이에 걷는 구간 (대화/스토리 전달)
- 집중된 디자인 → 각 보스가 독립적인 "테마"를 가짐

---

## 플레이어들이 사랑하는 요소

1. **게임 감각(Game Feel)**: 대시·패리·공격의 속도감과 임팩트가 최고 수준
2. **공정한 어려움**: 패턴을 익히면 클리어 가능, 하지만 결코 쉽지 않음
3. **아트 디자인**: 화려한 파티클, 빛 효과, 미니멀한 캐릭터 실루엣
4. **음악**: 보스마다 다른 전자음악 트랙 → 각 보스의 개성 강화
5. **내러티브**: 단순하지만 강렬한 "죄수와 간수의 역설적 관계" 스토리

---

## OnionCat 적용 포인트

### 가장 직접적인 레퍼런스: 2레이어 HP 적 설계
```
[Furi 구조]           [OnionCat 적용]
Shield → Ranged 딜    → Onion(P2) 원거리로 방어막 제거
HP → Melee 딜        → Cat(P1) 근접으로 본체 타격
```

**구현 제안**: `EnemyBase` 클래스에 `float shield`와 `float hp` 두 변수 추가.
- `shield > 0`이면 근접 피해 무효, 원거리 피해만 적용 → `shield` 감소
- `shield == 0`이면 근접 피해 적용 → `hp` 감소. 일정 시간 후 `shield` 재생성.

### 패리 시스템 OnionCat 버전 (Onion P2)
Furi의 패리를 Onion의 방패 메카닉에 직접 적용:
- **퍼펙트 패리**: 적 투사체가 방패에 닿기 0.1초 이내에 방패 방향이 맞으면 → 투사체 반사 + 히트스톱 0.3초 + Onion 시너지 게이지 +20%
- **일반 막기**: 방향은 맞았지만 타이밍 놓침 → 피해 50% 감소만

### 아트 레퍼런스: 탄막 시각화
Furi의 보스 탄막은 **색상으로 피하는 법 안내**:
- 빨간 탄막 → 패리 불가, 대시로만 피함
- 흰 탄막 → 패리 가능
→ OnionCat 적용: 원거리 약점 적의 탄막은 파란색 (Onion 방패로 막을 수 있음), 근접 약점 적의 공격은 주황색 (Cat 대시로 피함) → 색상으로 즉각 판단 가능.

### 대시 무적 시간 (Cat P1 적용)
Furi의 대시 무적 0.2초를 OnionCat Cat 대시에 동일 적용.
- `isDashing = true` 상태에서 Trigger 충돌 무시 → Invincibility 프레임
- Dash_IFrame_System.md 참고

---

## 참고 링크

- 공식 사이트: https://www.thegamebakers.com/furi/
- Steam: https://store.steampowered.com/app/423230/Furi/
- 위키: https://furi.fandom.com/
- "Furi Game Design Analysis" (YouTube 검색): 근접+원거리 혼합 전투 분석 영상 다수
- "The Perfect Boss Design of Furi" (Game Maker's Toolkit): https://www.youtube.com/watch?v=av1AyQMuPwI (레퍼런스)
- Reddit r/Furi: 커뮤니티 전략 및 패리 타이밍 연구
- The Game Bakers 포스트모템: GDC Vault 참고
