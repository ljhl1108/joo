# 방 프리팹 구조 설정 가이드

Room.cs / Door.cs / ExitTrigger.cs / DungeonManager.cs 는 이미 완성됨.  
이 가이드는 **유니티 에디터에서 방을 직접 배치**하는 작업을 다룬다.

---

## 핵심 개념

방(Room)은 런타임에 생성되지 않는다.  
씬에 미리 여러 방을 **다른 위치에 배치**해 두고, DungeonManager가 플레이어를 텔레포트시킨다.  
카메라는 `Snap()`으로 즉시 이동 → 방 이동이 자연스러운 페이드 전환처럼 보인다.

```
[씬 전체 레이아웃]
Room_Combat_01  위치 (0, 0)
Room_Combat_02  위치 (25, 0)
Room_Combat_03  위치 (50, 0)
Room_Boss_01    위치 (75, 0)
```

---

## Phase 1 — 씬 정리

- [ ] `Map` GameObject를 클릭
- [ ] `SimpleMapGenerator` 컴포넌트 오른쪽 ⋮ → **Remove Component** (또는 체크박스 해제로 비활성화)

> SimpleMapGenerator는 런타임에 방을 자동생성하므로 새 시스템과 충돌한다.

---

## Phase 2 — 첫 번째 방 만들기 (Room_Combat_01)

### 2-1. 루트 오브젝트

- [ ] Hierarchy 빈 공간 우클릭 → **Create Empty** → 이름: `Room_Combat_01`
- [ ] Transform Position: `(0, 0, 0)`
- [ ] `Room.cs` 컴포넌트 추가 (Add Component → Room)

### 2-2. 타일맵 (Floor + Wall)

- [ ] `Room_Combat_01` 우클릭 → **2D Object → Tilemap → Rectangular**  
  → 자동으로 `Grid` + `Tilemap` 생성됨
- [ ] `Tilemap` 이름을 `FloorTilemap`으로 변경
- [ ] `Grid` 우클릭 → **2D Object → Tilemap → Rectangular** → 이름: `WallTilemap`

**WallTilemap 콜라이더 설정:**

- [ ] `WallTilemap` 선택 → `TilemapCollider2D` 추가
  - Used By Composite: **체크**
- [ ] `CompositeCollider2D` 추가 (자동으로 Rigidbody2D도 추가됨)
  - Geometry Type: **Polygons**
- [ ] Rigidbody2D → Body Type: **Static**

> WallTilemap은 레이어를 `Wall`로 설정할 것 (Phase 5에서 EnemyBase wallMask 연결)

### 2-3. 타일 그리기

- [ ] **Window → 2D → Tile Palette** 열기
- [ ] `FloorTilemap` 선택 후 바닥 타일 그리기 (약 10×10 크기 추천)
- [ ] `WallTilemap` 선택 후 방 테두리 벽 그리기

### 2-4. PlayerSpawnPoint

- [ ] `Room_Combat_01` 우클릭 → **Create Empty** → 이름: `PlayerSpawnPoint`
- [ ] Position: 방 중앙 (예: `(0, 0, 0)`)

### 2-5. EnemySpawnPoints

- [ ] `Room_Combat_01` 우클릭 → **Create Empty** → 이름: `EnemySpawnPoints`
- [ ] `EnemySpawnPoints` 우클릭 → **Create Empty** → 이름: `SpawnPoint_01`
- [ ] 위 과정 반복 → `SpawnPoint_02`, `SpawnPoint_03`
- [ ] 각 SpawnPoint를 방 내부 원하는 위치로 이동 (Scene 뷰에서 드래그)

### 2-6. Door (출구 문)

- [ ] `Room_Combat_01` 우클릭 → **Create Empty** → 이름: `Door_Exit`
- [ ] `Door.cs` 컴포넌트 추가
- [ ] Position: 방 출구 위치 (예: 방 오른쪽 끝 `(5, 0, 0)`)

**Blocker (잠긴 문 비주얼):**

- [ ] `Door_Exit` 우클릭 → **Create Empty** → 이름: `Blocker`
- [ ] `SpriteRenderer` 추가 → 문 스프라이트 설정 (없으면 임시로 흰 사각형 사용)
- [ ] `BoxCollider2D` 추가 → 크기 맞추기

**OpenVisual (열린 문 비주얼):**

- [ ] `Door_Exit` 우클릭 → **Create Empty** → 이름: `OpenVisual`
- [ ] `SpriteRenderer` 추가 → 열린 문 스프라이트 설정 (없으면 빈 상태로 둠)

**ExitTrigger (통과 트리거):**

- [ ] `Door_Exit` 우클릭 → **Create Empty** → 이름: `ExitTrigger_GO`
- [ ] `BoxCollider2D` 추가 → **Is Trigger: 체크** → 크기는 문보다 약간 작게
- [ ] `ExitTrigger.cs` 컴포넌트 추가
- [ ] Tag: **Player** 설정 확인 (ExitTrigger는 Player 태그로 감지)

---

## Phase 3 — Door Inspector 연결

`Door_Exit` GameObject 선택:

- [ ] **Blocker** 필드 → `Blocker` GameObject 드래그
- [ ] **Open Visual** 필드 → `OpenVisual` GameObject 드래그
- [ ] **Exit Trigger** 필드 → `ExitTrigger_GO` 의 `ExitTrigger` 컴포넌트 드래그

---

## Phase 4 — Room Inspector 연결

`Room_Combat_01` GameObject 선택:

- [ ] **Room Type** → `Combat`
- [ ] **Exit Door** 필드 → `Door_Exit` 드래그
- [ ] **Player Spawn Point** 필드 → `PlayerSpawnPoint` 드래그
- [ ] **Enemy Spawns** 배열 크기 설정 (예: 3)
  - Element 0: Prefab = 슬라임 프리팹 / Spawn Point = `SpawnPoint_01`
  - Element 1: Prefab = 슬라임 프리팹 / Spawn Point = `SpawnPoint_02`
  - Element 2: Prefab = 원거리 적 프리팹 / Spawn Point = `SpawnPoint_03`

> 적 프리팹이 아직 없으면 Enemy Spawns는 비워도 됨 (방 입장 시 즉시 클리어 처리)

---

## Phase 5 — 나머지 방 복제

- [ ] `Room_Combat_01` 선택 → **Ctrl+D** 로 복제 → 이름: `Room_Combat_02`
- [ ] Position X를 25로 이동 (방끼리 겹치지 않도록)
- [ ] 타일을 다시 그리거나 레이아웃 변경 (복제 시 타일도 복제됨)
- [ ] EnemySpawnPoints 위치 및 적 구성 변경
- [ ] 위 과정 반복하여 3~4개 전투방 + 보스방 생성

**보스방:**
- [ ] Room Type → `Boss`
- [ ] 방 크기 더 크게 (15×15 권장)
- [ ] Enemy Spawns에 보스 프리팹 연결

---

## Phase 6 — DungeonManager 등록

`DungeonManager` GameObject (또는 GameManager) 선택:

- [ ] **Rooms** 배열 크기 설정 (예: 5)
- [ ] 순서대로 드래그:
  - Element 0: `Room_Combat_01`
  - Element 1: `Room_Combat_02`
  - Element 2: `Room_Combat_03`
  - Element 3: `Room_Combat_04`
  - Element 4: `Room_Boss_01`

---

## Phase 7 — EnemyBase wallMask 설정

벽에 부딪히지 않고 배회하려면 wallMask를 연결해야 한다.

- [ ] **Edit → Project Settings → Tags and Layers**
  - Layer 추가: `Wall` (예: User Layer 8)
- [ ] 씬의 모든 `WallTilemap` → Inspector → Layer → `Wall` 로 변경
- [ ] 씬에 있는 모든 적 프리팹 선택 → **Wall Mask** 필드에 `Wall` 레이어 체크

---

## Phase 8 — 테스트 체크리스트

- [ ] 플레이 버튼 → 1번 방에서 시작 (DungeonManager.EnterRoom(0) 자동 호출)
- [ ] 방 안의 적 모두 처치 → 문이 열리는 것 확인
- [ ] 열린 문 통과 → 페이드 아웃/인 후 다음 방으로 이동 확인
- [ ] 카메라가 순간이동하는 것 확인 (Snap으로 즉시 이동)
- [ ] 마지막 방 클리어 → Console에 "런 완료" 로그 확인

---

## 임시 스프라이트 없이 테스트하는 법

Door의 Blocker/OpenVisual 스프라이트가 없어도 기능은 동작한다.

- Blocker: 빈 GameObject + BoxCollider2D만 있어도 벽 역할 함
- OpenVisual: 없어도 무방 (Door.SetLocked에서 null 체크 있음)
- 테스트 시 Scene 뷰에서 Collider 색으로 문 위치 확인

---

완료 후 이 파일을 `Guides/Done/` 폴더로 이동.
