# OnionCat — 게임 컨셉 문서

---

## 기본 설정

- **장르**: 2인 협동 탑다운 로그라이크
- **비주얼**: 픽셀 아트 (Binding of Isaac / Enter the Gungeon 참고)
- **플랫폼**: PC — P1 게임패드, P2 키보드+마우스

### 2인 1캐릭터 구조

| | Player 1 — 고양이 | Player 2 — 작물 |
|---|---|---|
| 담당 | 이동 · 대쉬 · 근접 공격 | 원거리 공격 · 방향 실드 · 패링 |
| 입력 | 게임패드 (WASD 호환) | 키보드 + 마우스 |
| 이동 | 직접 이동 | 이동 없음 |

- 고양이 등에 화분을 메고 다님. 화분 속 작물이 P2 캐릭터.
- 런 시작 시 고양이 종류 + 작물 종류 각각 선택 → 로그라이크 핵심 선택
- 일부 적은 근접만, 일부는 원거리만 유효 → 협력 자연스럽게 강제

---

## 실드 시스템 (2레이어)

| 레이어 | 스크립트 | 역할 |
|--------|----------|------|
| 패시브 실드 | `PlayerHealth.cs` | HP 버퍼. 피격 시 먼저 소모. 4초 대기 후 2초마다 1칸 자동 회복 |
| 액티브 실드 | `OnionShield.cs` | 마우스 방향 차단막. 활성화 직후 0.2~0.3초 = 패링 윈도우 |

---

## 모듈형 공격 / 대쉬 구조

교체 가능한 컴포넌트 방식. 추후 고양이·작물 종류 추가 시 구현체만 교체.

```
BaseMeleeAttack
├── MeleeAttack_Slash   (현재 — 180° 부채꼴)
├── MeleeAttack_Stab    (예정 — 직선 찌르기)
└── MeleeAttack_Spin    (예정 — 360° 회전)

BaseDash
├── Dash_Default        (현재 — 직선 돌진 + 무적)
└── Dash_Blink          (예정 — 순간이동)
```

---

## Unity Hierarchy

```
[씬]
├── Player_Cat                         (Tag: Player)
│     ├── CatController.cs
│     ├── CropHolderOffset.cs
│     ├── Dash_Default.cs
│     ├── PlayerHealth.cs
│     ├── PlayerInput
│     ├── Rigidbody2D
│     ├── CircleCollider2D
│     │
│     ├── CatBody
│     │     ├── SpriteRenderer
│     │     └── Animator               (CatAnimator 연결)
│     │
│     ├── MeleePivot
│     │     ├── MeleeAttack_Slash.cs
│     │     └── AttackPoint
│     │
│     └── CropHolder
│           ├── OnionController.cs
│           ├── OnionShield.cs
│           ├── PotSprite / SpriteRenderer
│           ├── CropSprite / SpriteRenderer
│           └── AimPivot
│                 └── ShootPoint
│
├── Main Camera
│     ├── Camera
│     ├── CameraController.cs
│     └── AudioListener
│
├── HUD                                (Canvas)
│     └── HUDPanel                    (Horizontal Layout Group)
│           ├── HeartContainer        (Horizontal Layout Group + Content Size Fitter)
│           └── ShieldContainer       (Horizontal Layout Group + Content Size Fitter)
│                 └── HUDController.cs
│
├── DungeonManager
│     └── DungeonManager.cs
│
└── Map
      ├── SimpleMapGenerator.cs       (임시 — 제거 예정)
      └── Grid
            ├── FloorTilemap
            └── WallTilemap
```

---

## 스크립트 현황

### Player
| 파일 | 상태 | 비고 |
|------|------|------|
| `CatController.cs` | 완료 | 이동 · Animator 연동 · 공격/대쉬 위임 |
| `PlayerHealth.cs` | 완료 | HP + 패시브 실드 |
| `Dash_Default.cs` | 완료 | 직선 대쉬 + 무적 |
| `MeleeAttack_Slash.cs` | 완료 | 180° 부채꼴 근접 |
| `OnionController.cs` | 완료 | 마우스 조준 + 투사체 발사 |
| `OnionShield.cs` | 완료 | 액티브 실드 + 패링 |
| `CropHolderOffset.cs` | 완료 | 방향별 화분 위치 + 레이어 정렬 |

### Map / UI / 기타
| 파일 | 상태 | 비고 |
|------|------|------|
| `DungeonManager.cs` | 완료 | 방 연결 + 페이드 전환 |
| `Room.cs` | 완료 | 방 클리어 감지 |
| `HUDController.cs` | 완료 | HP/실드 아이콘 HUD |
| `CameraController.cs` | 완료 | SmoothDamp 추적 |
| `EnemyController.cs` | 완료 | 슬라임 AI |
| `GameOverManager.cs` | 미구현 | |

---

## 애니메이션

- 8방향 걷기 + Idle: Blend Tree (MoveX, MoveY 파라미터)
- 정지 시 Idle = Blend Tree 중앙 (MoveX=0, MoveY=0)
- CropHolder 위치: `CropHolderOffset.cs`로 방향별 자동 오프셋
- 레이어 정렬: NE/N/NW + 이동 중일 때만 양파가 앞 레이어. 정지 시 항상 뒤.
