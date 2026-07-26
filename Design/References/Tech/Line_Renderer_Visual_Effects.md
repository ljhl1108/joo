# Line Renderer 2D 시각 이펙트 시스템

리서치 날짜: 2026-07-26

## 개요

Unity의 `LineRenderer` 컴포넌트는 3D/2D 공간에서 두 점 이상을 연결하는 선을 그린다.
로그라이크 게임에서 **레이저 조준선, 방어막 외곽선, 번개/체인 이펙트, 투사체 트레일** 등에 핵심적으로 쓰인다.
OnionCat에서는 Onion의 방어막 시각화, 레이저형 투사체, 패리 성공 이펙트에 바로 활용 가능.

---

## Unity 구현 방법

### 1. 기본 LineRenderer 설정

```csharp
// 컴포넌트 추가 후 코드로 제어
LineRenderer lr = gameObject.AddComponent<LineRenderer>();
lr.positionCount = 2;                          // 점 개수
lr.SetPosition(0, startPoint);
lr.SetPosition(1, endPoint);
lr.startWidth = 0.05f;
lr.endWidth = 0.05f;
lr.useWorldSpace = true;                       // 월드 좌표 사용
```

**Inspector 주요 설정**:
- `Positions`: 점 배열 (코드로 동적 변경 가능)
- `Width Curve`: 선의 두께 변화 애니메이션 (애니메이션 커브)
- `Color Gradient`: 시작~끝 색상 그라디언트
- `Material`: Sprite Lit Default 또는 커스텀 글로우 머티리얼
- `Sorting Layer / Order in Layer`: 2D 스프라이트와 레이어 정렬 필수

---

### 2. 레이저 조준선 (Laser Sight)

Onion의 조준 방향에 레이저 점선/실선 표시:

```csharp
public class LaserSight : MonoBehaviour
{
    [SerializeField] private LineRenderer lineRenderer;
    [SerializeField] private float maxRange = 10f;
    [SerializeField] private LayerMask hitLayers;

    void Update()
    {
        Vector2 dir = (aimTarget - (Vector2)transform.position).normalized;
        RaycastHit2D hit = Physics2D.Raycast(transform.position, dir, maxRange, hitLayers);

        lineRenderer.SetPosition(0, transform.position);
        lineRenderer.SetPosition(1, hit ? hit.point : (Vector2)transform.position + dir * maxRange);
    }
}
```

**팁**: Sprite Default Material 대신 `Additive` 블렌딩 머티리얼 쓰면 빛나는(glow) 레이저 효과.

---

### 3. 방어막 외곽선 (Shield Visualizer)

원형 방어막을 LineRenderer로 그리기:

```csharp
public class ShieldRenderer : MonoBehaviour
{
    [SerializeField] private LineRenderer lineRenderer;
    [SerializeField] private int segments = 32;
    [SerializeField] private float radius = 1.2f;

    void Start()
    {
        lineRenderer.positionCount = segments + 1;
        for (int i = 0; i <= segments; i++)
        {
            float angle = i / (float)segments * Mathf.PI * 2f;
            lineRenderer.SetPosition(i, new Vector3(Mathf.Cos(angle), Mathf.Sin(angle), 0) * radius);
        }
        lineRenderer.loop = true;
    }
}
```

패리 성공 시 `radius`를 순간 확장 후 축소하면 파동 이펙트:
```csharp
IEnumerator ParryFlash()
{
    float t = 0;
    while (t < 0.3f)
    {
        lineRenderer.startWidth = Mathf.Lerp(0.1f, 0f, t / 0.3f);
        radius = Mathf.Lerp(1.5f, 1.2f, t / 0.3f);
        RefreshShieldShape();
        t += Time.deltaTime;
        yield return null;
    }
}
```

---

### 4. 번개/체인 이펙트 (Lightning Chain)

직선에 랜덤 노이즈를 주어 지글거리는 번개 표현:

```csharp
public class LightningEffect : MonoBehaviour
{
    [SerializeField] private LineRenderer lineRenderer;
    [SerializeField] private int segments = 10;
    [SerializeField] private float displacement = 0.3f;
    [SerializeField] private float updateInterval = 0.05f;

    private Vector2 _start, _end;

    public void SetPoints(Vector2 start, Vector2 end)
    {
        _start = start; _end = end;
        lineRenderer.positionCount = segments + 1;
        InvokeRepeating(nameof(UpdateLightning), 0, updateInterval);
    }

    void UpdateLightning()
    {
        lineRenderer.SetPosition(0, _start);
        lineRenderer.SetPosition(segments, _end);
        for (int i = 1; i < segments; i++)
        {
            float t = i / (float)segments;
            Vector2 basePos = Vector2.Lerp(_start, _end, t);
            Vector2 perp = Vector2.Perpendicular((_end - _start).normalized);
            basePos += perp * Random.Range(-displacement, displacement);
            lineRenderer.SetPosition(i, basePos);
        }
    }
}
```

---

### 5. 투사체 트레일 (Projectile Trail)

LineRenderer로 투사체 꼬리 만들기 (TrailRenderer 대안):

```csharp
public class ProjectileTrail : MonoBehaviour
{
    [SerializeField] private LineRenderer lineRenderer;
    [SerializeField] private int trailLength = 8;

    private Queue<Vector3> _positions = new Queue<Vector3>();

    void Update()
    {
        _positions.Enqueue(transform.position);
        if (_positions.Count > trailLength) _positions.Dequeue();

        lineRenderer.positionCount = _positions.Count;
        lineRenderer.SetPositions(_positions.ToArray());
    }
}
```

---

### 6. 머티리얼 & 글로우 설정

```
Project Settings > Graphics > URP Asset
→ Post Processing: Bloom 활성화
  → Threshold: 0.8, Intensity: 1.5

머티리얼:
- Shader: Universal Render Pipeline/2D/Sprite-Lit-Default
- Emission Color: 원하는 글로우 색상 (HDR 모드로 1 이상 값)
```

LineRenderer의 색상을 HDR + 밝은 값으로 설정하면 Bloom이 자동 글로우 처리.

---

## OnionCat 적용 포인트

### Onion 방어막 시각화
- `ShieldRenderer`로 Onion 주위에 원형 방어막 외곽선 상시 표시
- 방향키 입력 시 해당 방향 호(Arc)만 밝게 강조 → 어느 방향 막는지 시각화
- 패리 성공: 외곽선 순간 확장(pulse) + 흰색 플래시

### 레이저 조준선
- Onion의 마우스 조준 시 얇은 점선 또는 반투명 레이저로 조준 방향 표시
- 벽·적에 닿으면 `RaycastHit2D`로 끊김 처리
- 적에게 닿을 때 색상 변경 (흰→빨강) → "지금 쏘면 맞는다" 피드백

### 특수 적 이펙트
- 범위 공격 예고: 공격 방향에 빨간 선을 표시 (Cat Quest II 방식)
- 체인 공격 적: 두 플레이어 사이를 연결하는 번개 시각화

### 구현 우선순위
1. Onion 방어막 외곽선 (항상 표시)
2. 레이저 조준선 (선택적, 조준 모드 시)
3. 패리 펄스 이펙트
4. 적 공격 예고선

---

## 참고 링크

- [Unity Docs: Line Renderer](https://docs.unity3d.com/Manual/class-LineRenderer.html)
- [Unity Docs: LineRenderer Scripting](https://docs.unity3d.com/ScriptReference/LineRenderer.html)
- [Making a shield with LineRenderer (Unity forum)](https://forum.unity.com/threads/drawing-circle-with-line-renderer.489959/)
- [Brackeys: Line Renderer Tutorial](https://www.youtube.com/watch?v=AT3bFcjnzZw)
- [Unity Learn: VFX with LineRenderer](https://learn.unity.com/tutorial/introduction-to-visual-effects)
- [2D Lightning Effect in Unity](https://www.youtube.com/watch?v=NzqhB3Q4mzA)
