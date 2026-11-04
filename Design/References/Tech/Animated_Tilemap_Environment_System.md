# Animated Tilemap Environment System

리서치 날짜: 2026-11-04

## 개요

Unity 타일맵에서 물·불·용암·컨베이어·포탈 등 살아있는 환경 타일을 구현하는 기법. OnionCat처럼 방 기반 로그라이크에서 같은 방 에셋을 계속 재사용하므로, 애니메이션 타일로 각 스테이지 테마의 분위기를 차별화할 수 있다.

---

## Unity 구현 방법

### 1. AnimatedTile (2D Extras)

Unity 공식 `com.unity.2d.extras` 패키지에 포함된 준비된 솔루션.

```csharp
// Project 창에서 우클릭 → Create → 2D → Tiles → Animated Tile
// AnimatedTile 에셋이 생성됨
// Inspector에서:
// - Animated Sprites: 프레임 순서대로 스프라이트 배열
// - Minimum Speed / Maximum Speed: 프레임 속도 범위 (랜덤성 부여 가능)
// - Start Time: 시작 오프셋 (여러 타일이 같은 프레임에서 시작하지 않도록)
```

**장점**: 에디터에서 세팅만 하면 끝, 코드 불필요  
**단점**: 모든 같은 타일이 같은 속도 → 단조로움 (MinSpeed ≠ MaxSpeed로 완화)

### 2. 커스텀 AnimatedTile (스크립팅)

```csharp
using UnityEngine;
using UnityEngine.Tilemaps;

[CreateAssetMenu]
public class CustomAnimatedTile : TileBase
{
    public Sprite[] frames;
    public float frameRate = 8f;

    public override void GetTileData(Vector3Int position, ITilemap tilemap, ref TileData tileData)
    {
        tileData.sprite = frames[0];
        tileData.flags = TileFlags.None;
    }

    public override bool GetTileAnimationData(
        Vector3Int position, ITilemap tilemap, ref TileAnimationData tileAnimationData)
    {
        tileAnimationData.animatedSprites = frames;
        tileAnimationData.animationSpeed = frameRate;
        // 위치 기반 시작 오프셋 → 타일마다 다른 프레임에서 시작
        tileAnimationData.animationStartTime = (position.x * 7 + position.y * 13) * 0.1f;
        return true;
    }
}
```

**핵심**: `GetTileAnimationData`의 `animationStartTime`을 위치 기반으로 계산하면 타일마다 위상이 달라져 자연스러운 물결 효과.

### 3. RuleTile + AnimatedTile 조합

```csharp
// RuleTile에서 Output을 Animated Tile로 설정 가능
// 조건(주변 타일 패턴)에 따라 다른 애니메이션 재생
// 예: 물 가장자리는 splash 애니메이션, 중앙은 잔잔한 물결
```

에디터에서: RuleTile 에셋 → 규칙 항목의 Output → "Sprite" 대신 "Animation" 선택 → 프레임 배열 지정

### 4. Shader Graph 애니메이션 (고급)

픽셀 아트에서는 보통 프레임 애니메이션이 더 자연스럽지만, 화면 전체에 적용되는 왜곡 효과엔 셰이더가 유리.

```hlsl
// URP 2D → Shader Graph → Sprite Unlit Shader
// UV 오프셋으로 스크롤 효과:
// UV.x += Time * ScrollSpeed
// 사인파 왜곡으로 물 표면:
// UV.y += sin(UV.x * Frequency + Time * Speed) * Amplitude
```

**픽셀 아트 주의**: `Filter Mode = Point (no filter)` 유지해야 픽셀이 번지지 않음.

### 5. Tilemap 위 파티클 레이어

타일 자체 애니메이션 외에, 타일맵 위에 파티클 시스템을 배치해 불꽃 튀기기·물방울 등 추가.

```csharp
// 용암 타일이 있는 셀 위치를 순회해 파티클 오브젝트 배치
public class LavaTileParticleSpawner : MonoBehaviour
{
    [SerializeField] Tilemap lavaMap;
    [SerializeField] GameObject particlePrefab;

    void Start()
    {
        foreach (var pos in lavaMap.cellBounds.allPositionsWithin)
        {
            if (lavaMap.HasTile(pos))
            {
                var worldPos = lavaMap.CellToWorld(pos) + lavaMap.cellSize / 2;
                Instantiate(particlePrefab, worldPos, Quaternion.identity, transform);
            }
        }
    }
}
```

---

## 성능 고려사항

| 방법 | CPU 비용 | GPU 비용 | 비고 |
|------|---------|---------|------|
| AnimatedTile (공식) | 낮음 | 낮음 | 타일맵 GPU 배칭 그대로 활용 |
| 커스텀 AnimatedTile | 낮음 | 낮음 | 같음 |
| Shader Graph 스크롤 | 없음 | 낮음~중간 | 픽셀 수 많을수록 증가 |
| 파티클 오버레이 | 중간 | 중간 | 개수 제한 필요 (방당 50개 이하 권장) |

**타일맵 배칭**: 같은 타일셋의 타일들은 하나의 DrawCall로 묶임 → 애니메이션 타일도 같은 셋이면 배칭 유지.  
단, **다른 Tilemap 레이어를 많이 쌓으면 DrawCall 증가** → 환경 효과용 레이어는 1~2개로 제한.

---

## OnionCat 적용 포인트

### 스테이지 테마별 환경 애니메이션

| 스테이지 테마 | 추천 애니메이션 타일 |
|-------------|------------------|
| 초원 (1~2) | 흔들리는 풀, 반짝이는 이슬 |
| 동굴 / 지하 (3) | 흘러내리는 물, 반짝이는 광물 |
| 화산 / 용암 (4) | 흐르는 용암, 불꽃 가장자리 |
| 등대탑 (5~6) | 물결치는 바다 배경, 번개 번쩍임 |

### 구현 우선순위

1. **AnimatedTile**로 각 스테이지용 물·불 타일 먼저 제작 (에디터에서 Sprite 배열만 세팅)
2. `RoomLayouts/*.asset`의 방 모양 적용 시, 스테이지 테마에 맞는 Tilemap Set 교체
3. 위험한 타일(용암·함정)은 `EnemyHazard`와 연동 — 애니메이션 타일과 별개의 콜라이더 오브젝트 필요

### 픽셀 아트 주의사항

- 모든 환경 애니메이션 스프라이트는 **PPU 32** 맞추기
- 애니메이션 프레임 수 최소화 (물 흔들림: 4~6프레임으로 충분)
- Aseprite에서 태그로 "water_idle", "lava_flow" 등 애니메이션 분리 → Unity 임포터 자동 생성

### 방 적용 워크플로우

```
// RoomLayouts 적용 시 테마별 타일셋 교체 아이디어
// (현재 단일 타일셋, 나중에 다중 테마 지원 시 참고)
// OnionCat > Rooms > Apply Room Layouts 메뉴 확장:
// - stagePlan에서 현재 스테이지 테마 읽기
// - Tilemap의 TileBase를 테마별 애니메이션 타일로 교체
```

---

## 참고 링크

- Unity 공식 AnimatedTile: https://docs.unity3d.com/Packages/com.unity.2d.extras@3.0/manual/AnimatedTile.html
- 2D Extras GitHub: https://github.com/Unity-Technologies/2d-extras
- Unity 타일맵 최적화 가이드: https://docs.unity3d.com/Manual/Tilemap-BestPractices.html
- Unity 블로그 - 2D 타일맵 심화: https://unity.com/blog/engine-platform/2d-tilemap-asset-workflow
