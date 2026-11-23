# 로그라이크 런 맵 / 갈림길 선택 UI (Run Map Path Selection UI)

리서치 날짜: 2026-11-23

## 개요

Slay the Spire, Dead Cells, Hades처럼 한 판의 방 순서를 시각화한 "갈림길 지도" UI. 플레이어가 다음에 어느 방에 들어갈지 선택하고, 선택지마다 방 종류(전투·보물·상점·휴식 등)를 미리 보여준다. OnionCat의 `RunMap.cs`·`MapScreen` (GameState.Map)과 직결되는 완성 기능.

## Unity 구현 방법

### 핵심 데이터 구조
```csharp
// 맵 노드 하나
public class RunNode {
    public int layer;           // 0 = 시작, 7 = 보스
    public int col;             // 같은 층 안의 열 번호
    public StepKind kind;       // Combat / Treasure / Shop / Rest / Village / Boss
    public List<RunNode> next;  // 연결된 다음 노드들
    public bool visited;
}
```

### 맵 생성 (OnionCat의 RunMap.cs 패턴)
```csharp
// 1. 각 층에 2~3개 노드 배치
// 2. 이전 층 노드에서 다음 층 노드로 연결 (교차 없는 선으로)
// 3. 각 노드에 가중치로 방 종류 배정 (예: 전투 70%, 보물 10%, 상점 10%, 휴식 10%)
// 4. 보스 층은 항상 단일 노드
```

### UI 렌더링 (uGUI)
```csharp
// 노드마다 Button + Image 생성
// 현재 위치 → 도달 가능 노드만 활성화 (interactable = true)
// 연결선은 LineRenderer 또는 UI Image (회전한 1px 선 스프라이트)
// 아이콘: 방 종류별 스프라이트 (칼·상자·돈주머니·침대·별 등)
```

### 화면 흐름
```
GameState.Map → MapScreen 열림
  ↓ 플레이어가 다음 방 선택 (Button 클릭)
  ↓ DungeonManager.EnterRoom(selectedNode)
  ↓ 방 클리어 후 GameState.Map 복귀 (보스 방 클리어 시 다음 스테이지)
```

### 선택 UX 패턴 (레퍼런스 게임별)

| 게임 | 패턴 | OnionCat 적합도 |
|---|---|---|
| Slay the Spire | 세로 스크롤 나무 그래프, 아이콘만 | 높음 — 단순하고 읽기 쉬움 |
| Dead Cells | 없음 (선형) | 낮음 |
| Hades | 방 아이콘 + 보상 미리보기 | 중간 — 보상 미리보기 추가 복잡도 |
| FTL | 성계 지도 + 위험도 표시 | 낮음 — 너무 복잡 |

**OnionCat 권장**: Slay the Spire 패턴. 아이콘(방 종류) + 현재 위치 표시. 2인 협동이므로 둘 다 버튼 입력(고양이 A / 양파 클릭)이 필요하면 카운트다운이나 먼저 선택한 쪽이 확정하는 방식.

## OnionCat 적용 포인트

- **이미 구현됨**: `RunMap.cs` (8층 갈림길), `MapScreen` (GameState.Map), `StepKind` enum
- **아직 없는 것**: 방 종류별 아이콘, 보상 미리보기 (보물/상점 방에만), 2P 선택 확인 UX
- 2인 선택 UX: 고양이 / 양파 중 한 명이 고르면 3초 카운트다운 → 상대방이 같은 것에 동의하거나 타임아웃 시 확정
- 마을 방(Village) 아이콘은 등불/샘물/가판대 그림으로 구분
- 방문한 노드는 회색 처리, 현재 노드는 강조 (글로우 또는 화살표)

## 참고 링크

- [Slay the Spire 맵 구현 분석 (GitHub)](https://github.com/daviscook477/BaseMod/wiki)
- [Unity uGUI LineRenderer 대신 UI Line 그리기](https://docs.unity3d.com/Manual/UIHowTos.html)
- [Procedural map generation patterns — roguelikedev wiki](https://www.roguebasin.com/index.php/Dungeon_builder_implemented_as_a_simple_structure)
