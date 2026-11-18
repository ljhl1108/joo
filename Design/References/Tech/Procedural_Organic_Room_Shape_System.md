# 절차적 유기 방 형태 생성 시스템 (Procedural Organic Room Shape)

리서치 날짜: 2026-11-18

## 개요

격자(타일맵) 기반의 방 레이아웃 데이터를 받아 **실시간으로 유기적인 외곽선을 생성**하고, PolygonCollider2D와 MeshRenderer로 렌더링하는 기술.

OnionCat에서 이미 구현된 `StageArt.organicRooms` / `RoomShape.Apply`의 핵심 알고리즘이다. 개념을 이해하면 버그 수정, 외곽선 품질 개선, 새 방 모양 추가를 직접 할 수 있다.

---

## 핵심 개념

### 왜 직사각형 방이 아닌가?

타일맵 방(W=벽, F=바닥)은 직각이 많고 단조롭다. 외곽선을 흔들고 둥글게 만들면:
- 같은 레이아웃 데이터를 여러 번 써도 판마다 다른 느낌
- 아트와 판정이 자연스럽게 맞음
- 등불·소품이 각진 모서리에 어색하게 붙지 않음

### 처리 파이프라인

```
1. 타일 격자 → 2. 가장자리 꼭짓점 추출 → 3. 외곽선 정렬
       ↓
4. 꼭짓점 평활화 (Catmull-Rom / 가우시안)
       ↓
5. 무작위 흔들기 (Perlin Noise)
       ↓
6. PolygonCollider2D 갱신 → 7. 삼각분할 → MeshRenderer
```

---

## Unity 구현 방법

### Step 1: 타일 경계 꼭짓점 추출

```csharp
// 바닥 타일과 벽 타일 경계에서 꼭짓점을 추출
List<Vector2> ExtractBoundaryPoints(bool[,] floorMap, float cellSize)
{
    var edgeSet = new HashSet<(Vector2, Vector2)>();
    
    for (int x = 0; x < floorMap.GetLength(0); x++)
    for (int y = 0; y < floorMap.GetLength(1); y++)
    {
        if (!floorMap[x, y]) continue;
        
        // 4방향 이웃 중 바닥이 아닌 쪽의 경계선을 등록
        // 위쪽이 벽이면 → 이 타일의 위쪽 가장자리가 경계
        if (y + 1 >= floorMap.GetLength(1) || !floorMap[x, y + 1])
            AddEdge(edgeSet, x * cellSize, (y+1) * cellSize,
                            (x+1) * cellSize, (y+1) * cellSize);
        // ... 나머지 3방향 동일
    }
    
    // edgeSet의 연결된 꼭짓점들을 순서대로 정렬 → 폴리곤
    return SortEdgesToPolygon(edgeSet);
}
```

### Step 2: Catmull-Rom으로 평활화

격자에서 나온 꼭짓점은 직각이 많다. Catmull-Rom 스플라인으로 중간 점을 추가한다.

```csharp
List<Vector2> CatmullRomSmooth(List<Vector2> points, int subdivisions = 3)
{
    var result = new List<Vector2>();
    int n = points.Count;
    
    for (int i = 0; i < n; i++)
    {
        Vector2 p0 = points[(i - 1 + n) % n];
        Vector2 p1 = points[i];
        Vector2 p2 = points[(i + 1) % n];
        Vector2 p3 = points[(i + 2) % n];
        
        for (int s = 0; s < subdivisions; s++)
        {
            float t = s / (float)subdivisions;
            // Catmull-Rom 공식
            Vector2 pt = 0.5f * (
                (-p0 + 3*p1 - 3*p2 + p3) * t*t*t +
                (2*p0 - 5*p1 + 4*p2 - p3) * t*t +
                (-p0 + p2) * t +
                2*p1
            );
            result.Add(pt);
        }
    }
    return result;
}
```

### Step 3: Perlin Noise로 흔들기

```csharp
List<Vector2> PerturbPoints(List<Vector2> points, float amplitude, int seed)
{
    var result = new List<Vector2>(points.Count);
    float offsetX = seed * 13.7f; // 씨드별로 다른 노이즈 위치
    
    for (int i = 0; i < points.Count; i++)
    {
        Vector2 p = points[i];
        // 꼭짓점의 위치를 노이즈 입력값으로 → 판마다 굴곡이 달라짐
        float noiseVal = Mathf.PerlinNoise(p.x * 0.3f + offsetX, p.y * 0.3f) - 0.5f;
        
        // 외곽선의 법선 방향으로만 흔들기 (안쪽/바깥쪽으로)
        Vector2 prev = points[(i - 1 + points.Count) % points.Count];
        Vector2 next = points[(i + 1) % points.Count];
        Vector2 tangent = (next - prev).normalized;
        Vector2 normal = new Vector2(-tangent.y, tangent.x);
        
        result.Add(p + normal * noiseVal * amplitude);
    }
    return result;
}
```

### Step 4: PolygonCollider2D 갱신

```csharp
void ApplyToCollider(PolygonCollider2D col, List<Vector2> points)
{
    // 복잡한 오목 폴리곤이면 Path 여러 개로 분할이 필요할 수 있음
    col.SetPath(0, points.ToArray());
}
```

### Step 5: 삼각분할로 MeshRenderer (벽 메시)

```csharp
Mesh BuildWallMesh(List<Vector2> outerPoints, float wallHeight)
{
    // outerPoints = 바닥 외곽선
    // outerPoints + wallHeight * normal = 벽 꼭대기
    // → 외곽선을 따라 사각형(quad)를 이어 붙임
    
    var vertices = new List<Vector3>();
    var triangles = new List<int>();
    var uvs = new List<Vector2>();
    
    float uvX = 0;
    for (int i = 0; i < outerPoints.Count; i++)
    {
        Vector2 curr = outerPoints[i];
        Vector2 next = outerPoints[(i + 1) % outerPoints.Count];
        float segLen = Vector2.Distance(curr, next);
        
        int vi = vertices.Count;
        vertices.Add(new Vector3(curr.x, curr.y));
        vertices.Add(new Vector3(next.x, next.y));
        vertices.Add(new Vector3(curr.x, curr.y + wallHeight));
        vertices.Add(new Vector3(next.x, next.y + wallHeight));
        
        uvs.Add(new Vector2(uvX, 0));
        uvs.Add(new Vector2(uvX + segLen, 0));
        uvs.Add(new Vector2(uvX, 1));
        uvs.Add(new Vector2(uvX + segLen, 1));
        uvX += segLen;
        
        triangles.AddRange(new[] { vi, vi+1, vi+2, vi+1, vi+3, vi+2 });
    }
    
    var mesh = new Mesh();
    mesh.SetVertices(vertices);
    mesh.SetUVs(0, uvs);
    mesh.SetTriangles(triangles, 0);
    mesh.RecalculateNormals();
    return mesh;
}
```

---

## OnionCat 적용 포인트

### 현재 구조와 대응

OnionCat의 `RoomShape.Apply`가 이미 위 파이프라인을 돌리고 있다:

```
RoomLayoutAsset (글자 지도) 
    → RoomShape.Apply (C# 위 과정 수행)
    → Art/Shape의 PolygonCollider2D 갱신
    → 벽 메시(MeshFilter/MeshRenderer) 갱신
```

**들어갈 때마다 굴곡이 다른 이유**: `PerturbPoints`의 `seed`에 `Random.Range`를 사용하기 때문.

### 버그/튜닝 포인트

**문 근처에서 판정이 튀어나오는 문제**:
```csharp
// 출구 근처 꼭짓점은 흔들기 제외
float distToDoor = Vector2.Distance(point, doorPosition);
float perturbMask = Mathf.Clamp01((distToDoor - 1.5f) / 1.0f);
result.Add(p + normal * noiseVal * amplitude * perturbMask);
```

**폴리곤이 자기 자신과 교차하는 문제**:
- amplitude를 cellSize의 20% 이하로 제한 (보통 0.3 × cellSize)
- 꼭짓점 간 최소 거리 체크 후 너무 가까우면 제거

**얇은 복도에서 폴리곤이 역전되는 문제**:
- 1~2타일 폭의 복도는 organic 처리 대신 직선 유지
- `if (corridorWidth < 2 * cellSize) skipPerturbForSegment = true;`

### 성능 최적화

- **입장 시에만 갱신**: 방에 들어갈 때 1회만 `Apply` 호출, 플레이 중 재생성 안 함
- **꼭짓점 수 제한**: `subdivisions = 2~3` 이상은 불필요. 꼭짓점 200개 이하 유지
- **NativeArray 사용**: PolygonCollider2D.SetPath는 Burst와 함께 쓰면 더 빠름

---

## 참고 링크

- Marching Squares 알고리즘: https://jamie-wong.com/2014/08/19/metaballs-and-marching-squares/
- Catmull-Rom Unity 구현: https://catlikecoding.com/unity/tutorials/curves-and-splines/
- Unity PolygonCollider2D API: https://docs.unity3d.com/ScriptReference/PolygonCollider2D.html
- 2D 메시 삼각분할 (Ear Clipping): https://github.com/rexcardan/EarClipperLib
- Perlin Noise로 외곽선 흔들기: https://www.red3d.com/cwr/papers/2002/jitter.html
