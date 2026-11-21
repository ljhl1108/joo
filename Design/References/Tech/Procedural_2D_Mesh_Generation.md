# 런타임 절차적 2D 메시 생성

리서치 날짜: 2026-11-21

## 개요

Unity에서 코드로 직접 Mesh를 만드는 기법. 미리 만든 스프라이트나 타일맵이 아니라 점(vertex)과 삼각형(triangle)을 런타임에 계산해 Mesh 오브젝트에 넣는다.

OnionCat에서는 `RoomShape.Apply`가 글자 지도의 테두리를 굴곡지게 만들고 그 외곽선을 `PolygonCollider2D`와 벽 메시로 동시에 출력한다. 이 메시 생성 원리를 이해하면 버그 수정, 모양 개선, 새 연출 추가가 쉬워진다.

---

## Unity 구현 방법

### 1. 기본 Mesh API

```csharp
Mesh mesh = new Mesh();

// 꼭짓점 (월드 또는 로컬 좌표)
mesh.vertices = new Vector3[] { ... };

// UV (텍스처 좌표)
mesh.uv = new Vector2[] { ... };

// 삼각형 (인덱스 3개씩, 반시계 방향이 앞면)
mesh.triangles = new int[] { 0,1,2,  2,3,0, ... };

mesh.RecalculateNormals();
mesh.RecalculateBounds();

GetComponent<MeshFilter>().mesh = mesh;
```

### 2. 외곽선 → 채워진 도형 (삼각형 분할)

단순 볼록 다각형은 "팬(fan) 삼각분할"로 충분:

```csharp
// points: 외곽선 꼭짓점 목록 (반시계 방향)
Vector3[] vertices = points.Select(p => (Vector3)p).ToArray();
int[] tris = new int[(points.Count - 2) * 3];
for (int i = 0; i < points.Count - 2; i++)
{
    tris[i * 3]     = 0;
    tris[i * 3 + 1] = i + 1;
    tris[i * 3 + 2] = i + 2;
}
```

오목(concave) 다각형은 **귀 잘라내기(Ear Clipping)** 알고리즘 필요:
- 정점이 "귀"인지 판단 (삼각형 안에 다른 정점이 없어야 함)
- 가능한 귀를 하나씩 잘라 삼각형을 만들며 재귀
- Unity Asset Store의 `Clipper2` 또는 `TriangleNet`을 쓰면 간단

### 3. 두께 있는 테두리 (벽 띠)

내곽선과 외곽선 두 줄을 만들고 사이를 삼각형으로 메운다:

```csharp
// offset: 두께의 절반
Vector2[] outer = OffsetPath(outline, +wallThickness * 0.5f);
Vector2[] inner = OffsetPath(outline, -wallThickness * 0.5f);

// outer[i], inner[i], outer[i+1], inner[i+1] 네 점으로 쿼드 두 삼각형
```

경로 오프셋은 각 선분의 법선(normal) 방향으로 점을 미는 방식. 꺾이는 모서리는 평균 법선이나 미터 조인트(miter join)를 쓴다.

### 4. PolygonCollider2D와 메시 동기화

Unity 6에 `Collider2D.CreateMesh()` API가 추가됨:

```csharp
// PolygonCollider2D → Mesh 직접 변환 (Unity 6+)
var col = GetComponent<PolygonCollider2D>();
Mesh colMesh = col.CreateMesh(useBodyPosition: false, useBodyRotation: false);
```

OnionCat처럼 판정 먼저 → 그림 나중 순서라면 이 방법이 가장 깔끔하다.

### 5. 반복 텍스처 UV 계산 (벽 무늬 타일링)

외곽선을 따라가는 텍스처는 각 꼭짓점의 UV.x를 "지금까지 이동한 거리 / 텍스처 폭"으로 계산:

```csharp
float dist = 0f;
for (int i = 0; i < outer.Length; i++)
{
    if (i > 0) dist += Vector2.Distance(outer[i], outer[i-1]);
    uv[i] = new Vector2(dist / textureWidth, 0f);  // 외곽
    uv[outer.Length + i] = new Vector2(dist / textureWidth, 1f);  // 내곽
}
```

### 6. MeshCollider 대신 PolygonCollider2D를 쓰는 이유

- 2D 물리는 MeshCollider를 지원하지 않음
- PolygonCollider2D는 복수의 경로(path)를 지원해 구멍(hole)도 표현 가능
- 판정용 Collider와 그림용 Mesh는 별개 오브젝트로 관리하는 것이 혼동을 줄임

---

## OnionCat 적용 포인트

### 현재 구조 (CLAUDE.md 기준)

```
RoomShape.Apply
  → 글자 지도 외곽선 계산
  → 외곽선을 둥글리고 흔들어 비정형으로
  → PolygonCollider2D (판정) 세팅
  → 벽 메시 생성 (그림)
```

### 버그/개선 시 체크리스트

1. **얇은 복도 문제**: 귀 잘라내기에서 한 변 길이가 너무 짧으면 삼각형이 뒤집힘 → 최소 변 길이 체크 추가
2. **UV 이음새**: 반복 텍스처가 이어지지 않으면 꼭짓점 순서가 뒤섞인 것. 외곽선 순서를 고정 (반시계)
3. **구멍(Pit)**: `PolygonCollider2D`의 복수 경로(path index > 0)를 Inner Hull로 추가하면 구멍이 생김
4. **성능**: 방 입장마다 메시를 재생성하므로 `mesh.Clear()` 후 재사용. `new Mesh()` 반복은 GC 유발
5. **런타임 편집 확인**: `OnDrawGizmos`에서 외곽선 점을 `Gizmos.DrawSphere`로 그려 확인

### 새 벽 형태를 추가하려면

```csharp
// RoomShape.cs 에서 외곽선 생성 로직을 수정
// 예: 출구 근처를 넓히거나 직각 모서리 추가
List<Vector2> outline = BuildOutline(layout);
outline = SmoothOutline(outline, smoothRadius);
outline = JitterOutline(outline, jitterAmount);
ApplyToCollider(outline);
BuildWallMesh(outline);
```

---

## 참고 링크

- [Unity Docs: Collider2D.CreateMesh (Unity 6)](https://docs.unity3d.com/6000.0/ScriptReference/Collider2D.CreateMesh.html)
- [Polygon Mesh 2D (GitHub, NotWoods)](https://github.com/NotWoods/unity-polygon-2d-editor/blob/master/PolygonMesh2D.cs)
- [ProceduralToolkit: MeshDraft](https://github.com/Syomus/ProceduralToolkit)
- [i5 Toolkit Procedural Geometry](https://rwth-acis.github.io/i5-Toolkit-for-Unity/upm/manual/Procedural-Geometry.html)
- [Unity Discussions: PolygonCollider2D 런타임 그리기](https://discussions.unity.com/t/any-standard-way-to-draw-a-polygoncollider2d-at-runtime/590867)
