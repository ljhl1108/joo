# Runtime Tilemap Modification

리서치 날짜: 2026-10-21

## 개요

Unity Tilemap의 타일을 **게임 실행 중에 코드로 바꾸는** 기법. 벽이 무너지거나, 물이 차오르거나, 얼음이 녹는 등 **환경이 전투 중에 변화**하는 방을 구현할 때 필요하다. OnionCat TODO의 "방 모양 D — 싸우는 중에 바뀌는 방"과 "늪 얕은 물·독 웅덩이" 같은 스테이지 지형에 직접 사용된다.

---

## Unity 구현 방법

### 기본 API

```csharp
// 단일 타일 변경
tilemap.SetTile(Vector3Int position, TileBase newTile);

// 타일 제거 (null = 빈 칸)
tilemap.SetTile(new Vector3Int(x, y, 0), null);

// 타일 읽기
TileBase current = tilemap.GetTile(new Vector3Int(x, y, 0));

// 대량 변경 (성능 우수)
Vector3Int[] positions = { ... };
TileBase[] tiles = { ... };
tilemap.SetTiles(positions, tiles); // 내부적으로 batch 처리
```

### 월드 좌표 → 셀 좌표 변환

```csharp
// 월드 좌표 → Tilemap 셀 좌표
Vector3Int cell = tilemap.WorldToCell(worldPosition);

// 셀 좌표 → 월드 중심 좌표
Vector3 worldCenter = tilemap.GetCellCenterWorld(cell);
```

### 구역 전체를 새 타일로 채우기 (홍수/물 차오름)

```csharp
IEnumerator FloodArea(Tilemap tilemap, BoundsInt bounds, TileBase waterTile, float delayPerRow)
{
    // 아래 행부터 위로 올라오며 채움
    for (int y = bounds.yMin; y <= bounds.yMax; y++)
    {
        for (int x = bounds.xMin; x <= bounds.xMax; x++)
        {
            var pos = new Vector3Int(x, y, 0);
            if (tilemap.GetTile(pos) == null) // 빈 칸만 채움
                tilemap.SetTile(pos, waterTile);
        }
        yield return new WaitForSeconds(delayPerRow);
    }
}
```

### 벽 무너뜨리기 (단계적 교체)

```csharp
[SerializeField] TileBase crackedWallTile;
[SerializeField] TileBase rubbleTile;

IEnumerator CrumbleWall(Tilemap tilemap, Vector3Int wallPos)
{
    tilemap.SetTile(wallPos, crackedWallTile); // 1단계: 균열
    yield return new WaitForSeconds(0.5f);
    tilemap.SetTile(wallPos, rubbleTile);      // 2단계: 잔해
    yield return new WaitForSeconds(0.5f);
    tilemap.SetTile(wallPos, null);            // 3단계: 제거
    
    // 물리 충돌체 갱신 (TilemapCollider2D 사용 시 자동)
    // CompositeCollider2D 사용 시:
    GetComponent<CompositeCollider2D>().GenerateGeometry();
}
```

### 주의: TilemapCollider2D + CompositeCollider2D

런타임에 타일을 지우거나 추가하면 충돌체도 자동으로 갱신된다. 단:
- `CompositeCollider2D`의 `Geometry Type`이 `Polygons`일 때 런타임 갱신 지원
- 갱신이 느리다면 `GenerateGeometry()`를 직접 호출하거나, 갱신 빈도를 줄이기 위해 `Physics2D.autoSyncTransforms = false` 후 배치 변경 완료 시점에 한 번만 갱신

### AnimatedTile (타일맵 애니메이션)

물·용암 같은 반복 애니메이션 타일:
```csharp
// Unity 2D Extras 패키지의 AnimatedTile
// Inspector에서 스프라이트 배열 + 속도 설정 → 그냥 SetTile()로 배치
tilemap.SetTile(pos, animatedWaterTile);
```

---

## OnionCat 적용 포인트

### 1. 방 모양 D — 전투 중 변하는 방

TODO 항목 직접 구현 가이드:

**벽이 무너지는 방**:
- 특정 적 처치 시 또는 일정 시간 후 `CrumbleWall()` 코루틴 발동
- 무너진 자리가 구덩이(Pit)가 되면 걷어차기 즉사 유도
- `Room.OnRoomEvent(RoomEventType.WallCrumble)`로 방 스크립트에서 트리거

**물이 차오르는 방**:
- `FloodArea()` 코루틴으로 아래 행부터 위로 서서히 채움
- 물 타일 = Props 레이어, `PitCollider`와 동일 태그로 처리 (걷어차인 적이 닿으면 빠짐)
- 5~8초 주기로 한 행씩 차오르면 긴장감 생성

**구현 순서**:
1. `AnimatedTile` 타일 2개 제작 (물·잔해)
2. `DynamicRoomModifier` 컴포넌트 작성 (트리거 + 코루틴 묶음)
3. Room 에셋에 `RoomLayout` 문자 `W` (벽) 위치에 변경 대상 마킹
4. `ApplyRoomLayouts` 도구가 마킹 정보를 `DynamicRoomModifier`에 넘기도록 확장
5. 플레이 테스트: 물 타일 충돌 판정이 올바른지 + FPS 저하 없는지 확인

### 2. 스테이지 지형 타일 런타임 교체

서리 스테이지 빙판 효과: 특정 방 진입 시 바닥 타일을 기존 `floorTile` → `iceTile`로 일괄 교체
```csharp
void ApplyIceFloor(Tilemap floorTilemap, TileBase iceTile, BoundsInt roomBounds)
{
    var positions = new List<Vector3Int>();
    var tiles = new List<TileBase>();
    
    foreach (var pos in roomBounds.allPositionsWithin)
    {
        if (floorTilemap.GetTile(pos) != null) // 기존 바닥 타일 위치
        {
            positions.Add(pos);
            tiles.Add(iceTile);
        }
    }
    floorTilemap.SetTiles(positions.ToArray(), tiles.ToArray());
}
```

이 방식으로 `StageTheme`이 `floorTile`만 제공하면 `RoomLayoutStamper`가 방 전환 시 일괄 적용 가능.

### 3. 성능 주의사항

- `SetTile` 반복 호출보다 `SetTiles(positions[], tiles[])` 배치 호출이 10배 이상 빠름
- 초당 수십 타일 이상 바꾸지 않는 이상 성능 문제 없음
- `TilemapCollider2D`가 있는 레이어에서 런타임 타일 변경 시 ColliderGeometry 재생성 비용 있음 → 벽 레이어(충돌)와 바닥 레이어(장식)를 분리해 관리

---

## 참고 링크

- Unity 공식 문서 — Tilemap.SetTile: https://docs.unity3d.com/ScriptReference/Tilemaps.Tilemap.SetTile.html
- Unity 공식 문서 — Tilemap.SetTiles (배치): https://docs.unity3d.com/ScriptReference/Tilemaps.Tilemap.SetTiles.html
- Unity 2D Extras (AnimatedTile 포함): https://github.com/Unity-Technologies/2d-extras
- "Creating Dynamic Tilemaps at Runtime" — Unity Learn (검색)
