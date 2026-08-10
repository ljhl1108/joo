# GRIME

리서치 날짜: 2026-08-10

## 기본 정보

- **개발사**: Clover Bite
- **퍼블리셔**: Akupara Games
- **출시**: 2021년 8월 (PC), GRIME: Definitive Edition 2022년 발매
- **장르**: 2D 액션 RPG / 소울라이크 + 메트로이드바니아
- **플랫폼**: PC(Steam), PS4/5, Xbox, Switch
- **공식 사이트**: https://www.grimegame.com/
- **Steam**: https://store.steampowered.com/app/1078710/GRIME/
- **Meta 점수**: 75/100 (PC 기준)

---

## 핵심 메카닉

### 1. 흡수 패리 (Absorption Parry)

GRIME 최대의 정체성. 플레이어는 단순히 피해를 피하는 것이 아니라 **적의 공격을 흡수**할 수 있다.

- 적이 공격하는 순간 정확한 타이밍에 패리 입력 → 흡수 성공
- 흡수한 적 유형에 따라 **패시브 스탯 보너스** 또는 **새로운 특성(Trait)** 해금
- 동일 적 여러 번 흡수 → 스탯 누적 상승
- 흡수로만 얻을 수 있는 특성이 있어 패리를 "리스크 없는 행동"이 아닌 **적극적 전략**으로 만듦

**흡수 카테고리 예시**:
| 흡수 적 유형 | 획득 효과 |
|-------------|----------|
| 근접 돌격형 | 최대 HP 증가 |
| 독 분사형 | 독 저항 + 독 데미지 강화 |
| 방패형 | 패리 윈도우 확장 |
| 폭발형 | 폭발 반경 확대 |

### 2. 무기 시스템과 패리 윈도우

- 각 무기마다 **패리 윈도우 타이밍이 다름** (클릭 후 0.1초 vs 0.3초 등)
- 무기 선택이 곧 플레이스타일 선택 → 빠른 무기=좁은 윈도우, 느린 무기=넓은 윈도우
- 무기는 고정 능력이 아닌 **장착형 조각(Shaper)** 형태로 변경 가능

### 3. 무게 중심 중력 이동

- 플레이어 = 블랙홀 생물 → 중력 흡수로 구르거나 벽 타기
- 환경 퍼즐과 전투가 이동성으로 연결됨

---

## 협력·협동 요소

GRIME는 싱글플레이어 게임이지만, 내부 디자인 철학이 OnionCat의 협동 구조와 강하게 공명한다.

- **흡수 = 적의 능력 전용화**: 일부 적은 근접 패리로만, 일부는 특수 상태에서만 흡수 가능
  → OnionCat에서 "Cat이 어그로를 끌어야 Crop이 패리 가능" 구조와 동일한 역할 분리 원리
- **타이밍 의존 전투**: 패리 실패 시 큰 피해 → 신중한 관찰 후 행동 강제
  → 협력 게임에서 두 플레이어가 서로 적의 패턴을 공유해야 하는 상황과 동일

---

## 플레이어가 사랑하는 이유

1. **패리의 보상이 명확하고 즉각적** — 성공 패리 = 데미지 0 + 자원 획득, 실패 = 큰 피해
2. **성장이 전투 스타일과 직결** — 어떤 적을 흡수했냐가 캐릭터의 개성을 만듦
3. **독특한 아트 디렉션** — 유기체+광물 혼합의 다크 픽셀아트 (Zdzisław Beksiński 영향)
4. **조용한 스토리텔링** — 대사 없이 환경과 적 배치로 세계관 전달

---

## OnionCat 적용 포인트

### A. Crop 패리 메카닉 심화

GRIME의 흡수 패리를 참고해 Crop의 방어 시스템을 단순 "실드 블록"보다 풍부하게:

```
기본 패리 성공 → 투사체 반사 또는 근접 공격 튕겨냄
타이밍 퍼펙트 패리 (윈도우 앞 0.1초) → 적을 잠시 기절 + Crop에게 "에너지 충전"
에너지 충전 완료 → 1회 강화 투사체 사용 가능 (GRIME 흡수 특성의 소규모 버전)
```

Unity 구현 힌트:
```csharp
// ParrySystem.cs
public enum ParryResult { Miss, Normal, Perfect }

ParryResult CheckParry(float attackStartTime) {
    float delta = Time.time - attackStartTime;
    if (delta > parryWindowEnd) return ParryResult.Miss;
    if (delta < perfectWindow) return ParryResult.Perfect; // 에너지 충전
    return ParryResult.Normal; // 반사만
}
```

### B. 방어적 공격형 방향 실드

GRIME 무기별 패리 윈도우 차이 → Crop 실드 방향 설계에 적용:
- 전방 실드(넓은 커버, 좁은 패리 윈도우)
- 집중 실드(작은 커버, 넓은 패리 윈도우)
- 방향은 마우스 위치 기준으로 실시간 8방향 전환

### C. 적 설계 — "흡수 가능 표식"

GRIME에서 흡수 가능한 적은 시각적 힌트를 가짐.
OnionCat에서 Cat 근접에만 약한 적 vs Crop 원거리에만 약한 적에 **색깔/테두리 차이** 적용:
- 근접 약점: 빨간 테두리 / 몸통에 균열 이펙트
- 원거리 약점: 파란 테두리 / 안테나 느낌의 돌출부
- `EnemyWeaknessType` 열거형 + Sprite Outline 컴포넌트로 구현

---

## 참고 링크

- Steam 스토어: https://store.steampowered.com/app/1078710/GRIME/
- 공식 사이트: https://www.grimegame.com/
- Itch.io 데모: https://clover-bite.itch.io/grime
- GRIME 리뷰 (RPS): https://www.rockpapershotgun.com/grime-review
- 흡수 시스템 설계 인터뷰 (작성 참고): Clover Bite의 GDC 세션 자료 검색 권장
- Wiki: https://grime.fandom.com/wiki/GRIME_Wiki
