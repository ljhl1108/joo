# 적 AI 리팩토링 — 유니티 에디터 설정

## 구조 변경 요약

```
이전                        이후
EnemyController.cs    →    SlimeEnemy.cs (EnemyBase 상속)
RangedEnemyController →    RangedEnemy.cs (EnemyBase 상속)
EnemyController1.cs   →    삭제
```

---

## 1단계 — 기존 적 프리팹/오브젝트 교체

씬에서 슬라임 적을 선택하고:

- [ ] Inspector에서 `EnemyController` 컴포넌트 우클릭 → **Remove Component**
- [ ] **Add Component** → `SlimeEnemy` 추가
- [ ] 아래 항목 설정:

| 필드 | 값 |
|------|----|
| Max Health | 3 |
| Move Speed | 2 |
| Knockback Force | 5 |
| Hit Stun Duration | 0.3 |
| Chase Range | 6 |
| Attack Range | 1 |
| Wander Radius | 4 |
| Wander Idle Time | 1.5 |
| Touch Damage | 1 |

---

## 2단계 — 원거리 적 교체 (있는 경우)

- [ ] `RangedEnemyController` 컴포넌트 제거
- [ ] `RangedEnemy` 추가
- [ ] 아래 항목 설정:

| 필드 | 값 |
|------|----|
| Attack Range | 6 (원거리 적 공격 반경) |
| Retreat Range | 3 |
| Fire Interval | 2 |
| Projectile Prefab | 기존 투사체 프리팹 드래그 앤 드롭 |
| Shoot Point | 기존 ShootPoint Transform 드래그 앤 드롭 |

---

## 3단계 — (선택) FOV 시야각 추가

FOV 감지가 필요한 적에게만 추가. 없으면 단순 거리 감지로 동작.

- [ ] 적 오브젝트에 **Add Component** → `EnemyFOV`
- [ ] 설정:

| 필드 | 값 |
|------|----|
| View Radius | 6 |
| View Angle | 90 (기본) / 60 (원거리 적) / 120 (근접 적) |
| Player Mask | `Player` 레이어 선택 |
| Obstacle Mask | `Wall` / `Obstacle` 레이어 선택 |

씬 뷰에서 적을 선택하면 **노란 원(탐지 반경)**과 **파란 선(시야각)**이 Gizmo로 표시됨.

---

## 4단계 — 구 스크립트 파일 삭제

- [ ] Project 창에서 `EnemyController.cs` 우클릭 → Delete
- [ ] `EnemyController1.cs` 우클릭 → Delete
- [ ] `RangedEnemyController.cs` 우클릭 → Delete

> 삭제 전에 씬에서 해당 컴포넌트가 완전히 교체되었는지 확인할 것.

---

## 상태머신 동작 확인

게임 실행 후 적 오브젝트를 선택하면 Inspector에서 현재 상태를 확인 가능:
- `currentState : Wander` → 배회 중 (랜덤 이동)
- `currentState : Chase` → 플레이어 추격 중
- `currentState : Attack` → 공격 중

씬 뷰에서 **Gizmos ON** 상태로 실행하면 탐지 반경(노란), 공격 반경(빨간)이 표시됨.
