# 스테이지 테마 에셋 교체 파이프라인

리서치 날짜: 2026-10-19

## 개요

로그라이크는 스테이지마다 시각적·청각적 분위기가 달라야 "새 구간에 왔다"는 느낌이 생긴다.
OnionCat은 현재 **임시로 바닥·벽을 스테이지 색으로 물들이는** 방식을 쓰고 있다.
이 문서는 그것을 **코드 수정 없이 새 테마를 추가**할 수 있는 데이터 기반 파이프라인으로 교체하는 방법을 다룬다.

---

## Unity 구현 방법

### 1. 스테이지 테마 ScriptableObject 정의

```csharp
[CreateAssetMenu(menuName = "OnionCat/StageTheme")]
public class StageTheme : ScriptableObject
{
    [Header("Tilemap")]
    public TileBase floorTile;
    public TileBase wallTile;
    public TileBase pitTile;
    public Color tileColorTint = Color.white;   // 바닥 전체 색조

    [Header("Background")]
    public Sprite backgroundSprite;
    public Color fogColor;                      // 카메라 배경색

    [Header("Lighting (URP 2D)")]
    public Color globalLightColor = Color.white;
    [Range(0f, 1f)] public float globalLightIntensity = 0.85f;

    [Header("Audio")]
    public MusicId bgmId;
    public SfxId ambientLoopId;                 // 룸 앰비언트 (0 = 없음)

    [Header("VFX")]
    public GameObject ambientParticlePrefab;    // 떠다니는 파티클 (nullable)
    public RuntimeAnimatorController propAnimOverride; // 문·횃불 등 배경 소품 애니
}
```

### 2. DungeonManager에 테마 배열 추가

```csharp
// DungeonManager.cs
[SerializeField] private StageTheme[] stageThemes; // 인덱스 = 스테이지 번호(0~2)

public StageTheme CurrentTheme => stageThemes[currentStageIndex];
```

### 3. 테마 적용기 (StageThemeApplier)

방이 로드될 때 한 번 호출:

```csharp
public class StageThemeApplier : MonoBehaviour
{
    [SerializeField] private Tilemap floorTilemap;
    [SerializeField] private Tilemap wallTilemap;
    [SerializeField] private UnityEngine.Rendering.Universal.Light2D globalLight;

    public void Apply(StageTheme theme)
    {
        // 타일 교체
        ReplaceTiles(floorTilemap, theme.floorTile, theme.tileColorTint);
        ReplaceTiles(wallTilemap, theme.wallTile, Color.white);

        // 배경색
        Camera.main.backgroundColor = theme.fogColor;

        // 글로벌 라이트
        if (globalLight != null)
        {
            globalLight.color = theme.globalLightColor;
            globalLight.intensity = theme.globalLightIntensity;
        }

        // BGM
        Music.Play(theme.bgmId);

        // 앰비언트 파티클
        if (theme.ambientParticlePrefab != null)
            PoolManager.Spawn(theme.ambientParticlePrefab, Vector3.zero, Quaternion.identity);
    }

    private void ReplaceTiles(Tilemap map, TileBase tile, Color tint)
    {
        var bounds = map.cellBounds;
        foreach (var pos in bounds.allPositionsWithin)
        {
            if (map.HasTile(pos))
            {
                map.SetTile(pos, tile);
                map.SetColor(pos, tint);
            }
        }
    }
}
```

### 4. 테마 연결 순서 (실제 워크플로우)

```
1. StageTheme ScriptableObject 생성 (Assets/Data/Themes/)
2. 타일셋 준비 → floorTile / wallTile에 드래그
3. URP 2D Light 색·세기 조정
4. DungeonManager의 stageThemes 배열에 인덱스 맞춰 할당
5. Room.ResetForReuse() 안에서 StageThemeApplier.Apply(DungeonManager.Instance.CurrentTheme) 호출
6. 에디터 플레이 → 실제 타일 교체 확인
```

### 5. 성능: 타일 배치가 매 방마다 비쌀 때

타일 수가 많으면(~800개) `SetTile` 루프가 눈에 띄게 느릴 수 있다.
두 가지 해결책:

**A. SetTiles 배치 API 사용**
```csharp
var positions = new List<Vector3Int>();
var tiles = new List<TileBase>();
// ... 수집 ...
map.SetTiles(positions.ToArray(), tiles.ToArray()); // 한 번에 처리
```

**B. 스테이지 진입 시 한 번만 적용 (방마다 X)**
- 각 방은 같은 씬을 재사용(`Room.ResetForReuse`)하므로, 방 Reset 때가 아닌
  **스테이지 시작 직후** 씬의 "기준 방"에 테마를 한 번 구워두고 재사용할 수 있다.
- 단, 방 크기·모양이 다를 경우 적용 범위를 매번 계산해야 하므로 A 방법이 더 안전.

---

## OnionCat 적용 포인트

### 현재 상태
- 스테이지 색 구분: 임시 단색 오버레이 (코드에 직접 Color 값 박힘)
- 타일 에셋: 아직 스테이지별 전용 타일셋 없음 (TODO_Art.md)

### 단계적 도입 계획

| 단계 | 내용 | 비용 |
|------|------|------|
| **1단계** | StageTheme SO 생성 + DungeonManager 연결 + 색 tint만 적용 | 2~3시간 |
| **2단계** | 아티스트가 2~3종 타일셋 완성되면 floorTile/wallTile 교체 | 아트 완성 후 30분 |
| **3단계** | 스테이지별 BGM 분리 + 앰비언트 파티클 (파란 나비, 눈꽃 등) | 1시간 |

1단계 구현만 해도 현재 임시 색 오버레이를 에디터에서 관리할 수 있게 된다.
코드에 박힌 Color 하드코딩을 제거할 수 있으므로 **지금 당장 해도 이득**.

### 스테이지 테마 목록 (현재 설계)

| 스테이지 | 이름 | 분위기 | 제안 색온도 |
|----------|------|--------|------------|
| 0 (고정) | 무너진 정원 | 밝은 초록, 봄 | 따뜻한 노란빛 |
| 1A | 늪 | 어둡고 축축 | 청록·탁한 갈색 |
| 1B | 온실 | 무성하고 뜨거운 | 진한 초록·주황 |
| 1C | 서리 | 차갑고 고요 | 청백·푸른 라이트 |
| 2 (고정) | 마법사의 탑 | 신비, 어두운 보라 | 차가운 보라·흰빛 |

---

## 참고 링크

- Unity Tilemap API: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Tilemaps.Tilemap.html
- `SetTiles` 배치: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Tilemaps.Tilemap.SetTiles.html
- URP 2D Global Light: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/2DLighting-overview.html
- ScriptableObject 데이터 패턴: https://unity.com/how-to/architect-game-code-scriptable-objects
