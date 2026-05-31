# OnionCat — Claude Code 지침서

2인 1캐릭터 협동 로그라이크. 고양이(P1)와 작물(P2)이 하나의 바디를 공유.

---

## 역할

버그 없는 C# 코드 작성, 기존 시스템과의 호환성 유지가 목표.
코드 수정 후 반드시 `.claude/scripts/check_compile.ps1` 실행으로 컴파일 검증.

---

## 안전 수칙

- `.unity` / `.prefab` 파일은 텍스트로 직접 수정 금지 (YAML 파싱 오류 위험)
- `[SerializeField]` 변수가 생기면 "유니티 에디터에서 드래그 앤 드롭 설정 필요"라고 명시

---

## 게임 컨셉

| | Player 1 — 고양이 | Player 2 — 작물 |
|---|---|---|
| 담당 | 이동 · 대쉬 · 근접 공격 | 원거리 공격 · 방향 실드 · 패링 |
| 입력 | 게임패드 (WASD 호환) | 키보드 + 마우스 |

- 고양이 등에 화분을 메고 다님. 화분 속 작물이 P2 캐릭터.
- 적 중 일부는 근접만, 일부는 원거리만 유효 → 협력 강제
- 런 시작 시 고양이 종류 + 작물 종류 선택 (로그라이크 핵심 선택)

---

## 실드 시스템

| 레이어 | 스크립트 | 역할 |
|--------|----------|------|
| 패시브 실드 | `PlayerHealth.cs` | HP 버퍼. 피격 시 먼저 소모. 4초 후 2초마다 1칸 자동 회복 |
| 액티브 실드 | `OnionShield.cs` | 마우스 방향 차단막. 활성화 직후 0.2~0.3초 = 패링 윈도우 |

---

## 모듈형 공격 / 대쉬 구조

```
BaseMeleeAttack
└── MeleeAttack_Slash   (현재 — 180° 부채꼴)

BaseDash
└── Dash_Default        (현재 — 직선 돌진 + 무적)
```

---

## 경로 정보

| 항목 | 경로 |
|------|------|
| Unity 프로젝트 | `C:\workspace\unity\Onioncat_AG` |
| 문서 / 설계 워크스페이스 | `C:\workspace\claude\Game_Develop\OnionCat` |
| 스크립트 | `C:\workspace\unity\Onioncat_AG\Assets\Scripts\` |
| 컴파일 체크 스크립트 | `.claude\scripts\check_compile.ps1` |
| GitHub 저장소 | `https://github.com/ljhl1108/joo` |

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
│     │     └── Animator             (CatAnimator 연결)
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
├── HUD                               (Canvas)
│     └── HUDPanel                   (Horizontal Layout Group)
│           ├── HeartContainer       (Horizontal Layout Group + Content Size Fitter)
│           └── ShieldContainer      (Horizontal Layout Group + Content Size Fitter)
│                 └── HUDController.cs
│
├── DungeonManager
│     └── DungeonManager.cs
│
└── Map
      ├── SimpleMapGenerator.cs      (임시 — 제거 예정)
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
- CropHolder 위치: `CropHolderOffset.cs`로 방향별 자동 오프셋
- 레이어 정렬: NE/N/NW + 이동 중일 때만 양파가 앞 레이어

---

## 일일 루틴 (자동화)

매일 오전 9시(서울) 클라우드에서 자동 실행.
컴퓨터가 꺼져 있어도 동작. 결과 확인: `claude.ai/code/routines`

**작업 내용**: 탑다운 로그라이크 게임 리서치 → Design/ 항목별 아이디어 3개씩 작성 → GitHub 커밋

| 항목 | 내용 |
|------|------|
| 루틴 ID | `trig_01RUueN3etcTT1WNuSWwJCEN` |
| 저장소 | `https://github.com/ljhl1108/joo` |
| 결과 파일 | `Design/01~05_*.md` |
| 로컬 업데이트 | `git pull` 실행 |

---

## 코딩 컨벤션

- `Update()` 내 `GetComponent` / `FindObjectOfType` / `GameObject.Find` 금지 → `Awake()`에서 캐싱
- Inspector 노출 변수는 `public` 대신 `[SerializeField] private`
- 외부 참조 시 항상 null 체크
- 입력: New Input System (UnityEngine.InputSystem) — Legacy Input 금지
- 교체 가능한 능력은 추상 기반 클래스 상속 구조 유지
