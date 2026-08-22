# 물리 기반 로프/테더 시스템 (Rope & Tether System)

리서치 날짜: 2026-08-22

## 개요
두 GameObject를 물리적으로 연결하는 로프·줄·체인 시스템. 협동 게임에서 두 캐릭터의 행동 반경을 제한하거나, 적을 묶거나, 이동 수단으로 활용할 수 있다. OnionCat의 "하나의 몸 공유" 컨셉을 시각적·물리적으로 강화할 수 있는 핵심 기술이다.

---

## Unity 구현 방법

### 방법 1: DistanceJoint2D (단순 거리 제한)
두 오브젝트가 최대 거리를 넘지 못하게 막는 가장 단순한 방법.

```csharp
// 설정: CharacterA에 DistanceJoint2D 추가
// Inspector에서 ConnectedBody = CharacterB의 Rigidbody2D
DistanceJoint2D joint = GetComponent<DistanceJoint2D>();
joint.maxDistanceOnly = true;   // 거리 초과 시만 힘 작용
joint.distance = 3f;             // 최대 허용 거리(유닛)
joint.connectedBody = otherRb;
```

**장점**: 구현 단순, 성능 우수  
**단점**: 탄성 없음, 로프처럼 보이지 않음

---

### 방법 2: SpringJoint2D (탄성 로프)
스프링처럼 늘어나고 줄어드는 물리 로프. 텐션 피드백 구현에 적합.

```csharp
SpringJoint2D spring = GetComponent<SpringJoint2D>();
spring.connectedBody = otherRb;
spring.distance = 2f;        // 자연 길이
spring.frequency = 1.5f;     // 진동 주파수 (낮을수록 출렁임)
spring.dampingRatio = 0.5f;  // 감쇠 (1.0 = 진동 없음)
spring.enableCollision = true;
```

---

### 방법 3: 다중 세그먼트 로프 (Chain Rope)
여러 개의 작은 Rigidbody2D를 HingeJoint2D로 연결해 실제 로프처럼 늘어지게 만든다.

```csharp
public class RopeBuilder : MonoBehaviour
{
    [SerializeField] private GameObject segmentPrefab;
    [SerializeField] private int segmentCount = 10;
    [SerializeField] private Rigidbody2D anchorA;
    [SerializeField] private Rigidbody2D anchorB;

    private List<Rigidbody2D> segments = new();

    void Awake()
    {
        BuildRope();
    }

    void BuildRope()
    {
        Rigidbody2D prev = anchorA;
        float spacing = 1f / segmentCount;

        for (int i = 0; i < segmentCount; i++)
        {
            Vector3 pos = Vector3.Lerp(anchorA.position, anchorB.position, (i + 1) * spacing);
            GameObject seg = Instantiate(segmentPrefab, pos, Quaternion.identity);
            Rigidbody2D rb = seg.GetComponent<Rigidbody2D>();
            segments.Add(rb);

            HingeJoint2D hinge = seg.GetComponent<HingeJoint2D>();
            hinge.connectedBody = prev;

            prev = rb;
        }

        // 마지막 세그먼트를 anchorB에 연결
        HingeJoint2D lastHinge = segments[^1].gameObject.AddComponent<HingeJoint2D>();
        lastHinge.connectedBody = anchorB;
    }
}
```

**주의**: 세그먼트가 많을수록 물리 연산 비용 증가. 10-15개가 적절.

---

### 방법 4: LineRenderer로 로프 시각화

```csharp
public class RopeVisualizer : MonoBehaviour
{
    [SerializeField] private LineRenderer lr;
    [SerializeField] private Transform pointA;
    [SerializeField] private Transform pointB;
    [SerializeField] private int resolution = 20;
    [SerializeField] private float sag = 0.5f; // 처짐 정도

    void Update()
    {
        DrawCatenary();
    }

    void DrawCatenary()
    {
        lr.positionCount = resolution;
        for (int i = 0; i < resolution; i++)
        {
            float t = i / (float)(resolution - 1);
            Vector3 pos = Vector3.Lerp(pointA.position, pointB.position, t);
            // 중력에 의한 처짐 (포물선 근사)
            float droop = Mathf.Sin(t * Mathf.PI) * sag;
            pos.y -= droop;
            lr.SetPosition(i, pos);
        }
    }
}
```

---

### 방법 5: 텐션 감지 및 피드백

```csharp
public class TetherTensionSensor : MonoBehaviour
{
    [SerializeField] private Rigidbody2D bodyA;
    [SerializeField] private Rigidbody2D bodyB;
    [SerializeField] private float maxDistance = 3f;

    public float TensionRatio => Mathf.Clamp01(
        Vector2.Distance(bodyA.position, bodyB.position) / maxDistance
    );

    public bool IsMaxTension => TensionRatio >= 0.95f;

    void Update()
    {
        if (IsMaxTension)
        {
            // 화면 진동, UI 경고, 사운드 트리거
        }
    }
}
```

---

## OnionCat 적용 포인트

### 1. 화분 안정성 시스템
고양이(P1)가 대시·방향 전환 시 화분(P2 카메라 기준점)이 흔들리는 효과. SpringJoint2D로 화분 카메라가 고양이를 약간 느리게 따라가도록 구현.

```
고양이(Rigidbody2D) ←─ SpringJoint2D ─→ 화분 카메라 앵커
```

### 2. "연결 끊어짐" 위험 표현
두 플레이어가 화면 밖으로 너무 벌어지면 UI에 빨간 텐션 바 표시. DistanceJoint2D의 maxDistance를 스크린 크기 기준으로 계산.

### 3. 적 묶기 메커닉 (미래 확장)
고양이가 적 주위를 돌면 Composite의 물리 계산을 활용, 적 AI 이동 속도 감소 → 양파 원거리 공격으로 마무리하는 협동 콤보.

### 4. 시각적 연결 표현
두 플레이어 사이의 LineRenderer로 "생명 줄" 시각화. 텐션에 따라 선 색상 변경 (여유: 초록 → 긴장: 빨강).

---

## 성능 고려사항

| 방법 | CPU 비용 | 시각적 품질 | 권장 상황 |
|------|---------|------------|----------|
| DistanceJoint2D | 매우 낮음 | 없음 | 보이지 않는 로직 전용 |
| SpringJoint2D | 낮음 | 없음 | 텐션 피드백 전용 |
| 다중 HingeJoint | 중간 | 높음 | 실제 로프 시뮬레이션 |
| LineRenderer만 | 매우 낮음 | 중간 | 시각 전용 (물리 없음) |

OnionCat처럼 2인 협동이지만 "로프를 조작"하지 않는 경우: **DistanceJoint2D(로직) + LineRenderer(시각)** 조합이 최적.

---

## 참고 링크

- Unity 공식 - DistanceJoint2D: https://docs.unity3d.com/Manual/class-DistanceJoint2D.html
- Unity 공식 - SpringJoint2D: https://docs.unity3d.com/Manual/class-SpringJoint2D.html
- Unity 공식 - LineRenderer: https://docs.unity3d.com/Manual/class-LineRenderer.html
- Catenary curve 로프 시각화 수식: https://en.wikipedia.org/wiki/Catenary
- 유튜브 - Unity 2D Rope Physics Tutorial: 검색어 "Unity 2D rope linerenderer joint"
