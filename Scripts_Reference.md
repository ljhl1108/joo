# Scripts Reference

---

## Player

| 파일 | 부착 위치 | 역할 |
|------|-----------|------|
| `CatController.cs` | Player_Cat | P1 이동 · MeleePivot 회전 · 공격/대쉬 위임 |
| `PlayerHealth.cs` | Player_Cat | HP + 패시브 실드 · 피격 무적 · 실드 자동 회복 |
| `Dash_Default.cs` | Player_Cat | 직선 대쉬 · 무적 · 반투명 (BaseDash 구현체) |
| `BaseDash.cs` | — | 대쉬 추상 기반 클래스 |
| `MeleeAttack_Slash.cs` | MeleePivot | 180° 부채꼴 근접 공격 (BaseMeleeAttack 구현체) |
| `BaseMeleeAttack.cs` | — | 근접 공격 추상 기반 클래스 |
| `OnionController.cs` | CropHolder | P2 마우스 조준 · 투사체 발사 |
| `OnionShield.cs` | CropHolder | 액티브 실드 + 패링 |

---

## Enemy

| 파일 | 부착 위치 | 역할 |
|------|-----------|------|
| `EnemyController.cs` | 적 루트 | 슬라임 AI · 직선 추적 · 접촉 데미지 · 넉백 |
| `RangedEnemyController.cs` | 적 루트 | 원거리 적 AI |

---

## Map

| 파일 | 부착 위치 | 역할 |
|------|-----------|------|
| `DungeonManager.cs` | DungeonManager | 런 단위 방 연결 · 페이드 전환 |
| `Room.cs` | Room 프리팹 | 방 클리어 조건 · 문 관리 |
| `Door.cs` | Door 오브젝트 | 문 열림/닫힘 |
| `ExitTrigger.cs` | Exit 트리거 | 다음 방 진입 감지 |
| `SimpleMapGenerator.cs` | Map | 테스트용 임시 맵 (제거 예정) |

---

## UI

| 파일 | 부착 위치 | 역할 |
|------|-----------|------|
| `HUDController.cs` | HUD Canvas | HP 하트 · 패시브 실드 아이콘 표시 |

---

## Camera / Projectile

| 파일 | 부착 위치 | 역할 |
|------|-----------|------|
| `CameraController.cs` | Main Camera | SmoothDamp 플레이어 추적 |
| `Projectile.cs` | 투사체 프리팹 | 방향 이동 · 적 충돌 시 데미지 후 Destroy |

---

## 상속 구조

```
BaseDash
└── Dash_Default          (직선 대쉬)

BaseMeleeAttack
└── MeleeAttack_Slash     (180° 부채꼴)
```
