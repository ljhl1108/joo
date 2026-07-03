# Tilemap & Rule Tile 시스템

리서치 날짜: 2026-07-03

## 개요
Unity Tilemap은 2D 게임에서 레벨을 타일 단위로 구성하는 내장 도구다. Rule Tile은 이웃 타일 유무에 따라 자동으로 알맞은 스프라이트를 선택하는 지능형 타일이다. 이 두 가지를 조합하면 픽셀아트 로그라이크에서 방 바닥·벽·코너를 코드 한 줄로 자동 처리할 수 있어, 절차적 방 생성의 핵심 인프라가 된다.

OnionCat에서는 각 방(Room)의 벽·바닥·장식 타일을 Tilemap 레이어로 분리 관리하고, Rule Tile로 자동 연결 처리를 적용해야 수작업 없이 절차적 방 생성이 가능하다.

---

## Unity 구현 방법

### 1. 기본 Tilemap 설정

```
Hierarchy:
Grid (Auto 생성)
├── Tilemap_Floor      (Z Order: 0) — 바닥 타일
├── Tilemap_Walls      (Z Order: -1) — 벽 타일 (위에 그려야 가려짐)
└── Tilemap_Decoration (Z Order: -2) — 장식 (횃불, 풀 등)
```

1. Hierarchy → Create → 2D Object → Tilemap → Rectangular
2. Grid 오브젝트 하위에 Tilemap을 여러 개 추가하여 레이어 분리
3. 각 TilemapRenderer의 Sorting Layer + Order in Layer 설정

### 2. Rule Tile 설치 및 생성

**2D Tilemap Extras 패키지 필수:**
```
Package Manager → com.unity.2d.tilemap.extras 검색 → Install
```

**Rule Tile 생성:**
1. Project 뷰 우클릭 → Create → 2D → Tiles → Rule Tile
2. Inspector에서 규칙 추가:
   - Default Sprite: 기본 타일 스프라이트 (규칙 미일치 시 사용)
   - Rules 목록: 3×3 이웃 그리드로 조건 설정
     - 녹색 화살표: 해당 방향에 같은 타입 타일 필요
     - 빨간 X: 해당 방향에 타일 없어야 함
     - 빈칸: 무관 (any)

**규칙 예시 (자동 벽 연결용):**
| 조건 | 스프라이트 |
|------|-----------|
| 좌우 이웃 있음, 위아래 없음 | 가로 벽 중간 |
| 위아래 이웃 있음, 좌우 없음 | 세로 벽 중간 |
| 좌측만 이웃 있음 | 오른쪽 끝 캡 |
| 4방향 모두 이웃 있음 | 내부 바닥 |
| 이웃 없음 | 단독 타일 |

### 3. Tilemap Collider 2D 설정 (벽 충돌)

```
Tilemap_Walls 컴포넌트:
├── TilemapCollider2D
│   └── Used By Composite: ✓ (체크)
├── CompositeCollider2D  ← 인접 충돌 자동 병합 (성능 ↑)
└── Rigidbody2D
    └── Body Type: Static
```

CompositeCollider2D가 인접 타일 충돌을 하나로 합쳐 Physics 오버헤드를 크게 줄임.

### 4. 픽셀아트 타일 임포트 설정

```
Texture Import Settings:
- Filter Mode: Point (no filter)  ← 픽셀 경계 선명하게
- Compression: None
- Pixels Per Unit: 16 (or 32, 게임 밀도에 맞춤)
- Sprite Mode: Multiple (스프라이트 시트) or Single
```

### 5. 코드로 타일 배치 — 절차적 생성 연동

```csharp
using UnityEngine;
using UnityEngine.Tilemaps;

public class RoomPainter : MonoBehaviour
{
    [SerializeField] private Tilemap floorTilemap;
    [SerializeField] private Tilemap wallTilemap;
    [SerializeField] private RuleTile floorRuleTile;
    [SerializeField] private RuleTile wallRuleTile;

    public void PaintRoom(BoundsInt roomBounds)
    {
        // 바닥 영역 칠하기
        foreach (var pos in roomBounds.allPositionsWithin)
            floorTilemap.SetTile(pos, floorRuleTile);

        // 외곽 한 칸: 벽
        for (int x = roomBounds.xMin - 1; x <= roomBounds.xMax; x++)
        {
            for (int y = roomBounds.yMin - 1; y <= roomBounds.yMax; y++)
            {
                var pos = new Vector3Int(x, y, 0);
                if (!roomBounds.Contains(pos))
                    wallTilemap.SetTile(pos, wallRuleTile);
            }
        }
    }

    public void ClearAll()
    {
        floorTilemap.ClearAllTiles();
        wallTilemap.ClearAllTiles();
    }
}
```

유니티 에디터에서 드래그 앤 드롭 설정 필요:
- `floorTilemap` / `wallTilemap`: 각 Tilemap 오브젝트 연결
- `floorRuleTile` / `wallRuleTile`: 생성한 Rule Tile 에셋 연결

### 6. 2D Tilemap Extras 주요 타일 타입

| 타일 타입 | 용도 |
|-----------|------|
| Rule Tile | 이웃 기반 자동 스프라이트 선택 |
| Animated Tile | 물결, 횃불 같은 애니메이션 타일 |
| Random Tile | 여러 스프라이트 중 무작위 선택 (바닥 다양화) |
| Pipeline Tile | 직선 연결 자동 처리 (통로, 파이프) |

### 7. 방 전환 시 타일 재활용 패턴

```csharp
// 방 이동 시: 이전 방 지우고 새 방 그리기
void OnRoomTransition(RoomData nextRoom)
{
    roomPainter.ClearAll();
    roomPainter.PaintRoom(nextRoom.bounds);
    // 이전 방 오브젝트(적, 아이템)도 별도 정리 필요
}
```

---

## OnionCat 적용 포인트

### 방 레이아웃 자동화
- 방 프리팹 전체 대신 `BoundsInt` 데이터만 저장
- `RoomPainter.PaintRoom(bounds)` 한 번 호출로 모든 방 그리기
- Rule Tile 덕분에 어떤 모양의 방이든 벽·코너·단독 타일이 자동으로 알맞은 스프라이트 선택

### 테마별 타일셋 교체 (층 테마 변경)
```csharp
// ThemeData ScriptableObject에 층별 타일셋 저장
roomPainter.floorRuleTile = currentTheme.floorTile;
roomPainter.wallRuleTile  = currentTheme.wallTile;
roomPainter.PaintRoom(bounds);
```
- 1~2층: 지하 흙 던전 타일셋
- 3~4층: 석재 성 내부 타일셋
- 보스 방: 뿌리로 뒤덮인 특수 타일셋

### 바닥 다양화 (Random Tile)
- 바닥 타일맵에 Random Tile 적용: 크랙, 이끼, 핏자국 스프라이트 무작위 배치
- 추가 코드 없이 Tilemap Extras만으로 처리 → 단조로운 바닥 해소

### 성능 최적화
- `CompositeCollider2D`로 벽 충돌 연산 최소화
- 현재 방 외 타일맵 `SetActive(false)`로 렌더링 및 Physics 제외
- 방 전환 시 `ClearAllTiles()` 후 재배치 (RefreshAllTiles보다 빠름)

---

## 참고 링크
- Unity Tilemap 공식 문서: https://docs.unity3d.com/Manual/class-Tilemap.html
- 2D Tilemap Extras 패키지 문서: https://docs.unity3d.com/Packages/com.unity.2d.tilemap.extras@latest/manual/index.html
- Rule Tile 공식 설명: https://docs.unity3d.com/Packages/com.unity.2d.tilemap.extras@latest/manual/RuleTile.html
- Unity Tilemap Collider 2D: https://docs.unity3d.com/Manual/class-TilemapCollider2D.html
- Composite Collider 2D: https://docs.unity3d.com/Manual/class-CompositeCollider2D.html
