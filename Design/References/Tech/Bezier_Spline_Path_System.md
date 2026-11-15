# Bezier Curve and Spline Path System

리서치 날짜: 2026-11-15

## 개요

베지어 곡선과 스플라인은 "두 점 사이를 직선이 아니라 부드럽게 연결"하는 수학적 경로다.
로그라이크 2D 게임에서 주로 쓰이는 곳:

- **보스 탄막 패턴** — 직선 탄이 아닌 s자·곡선으로 휘어 오는 탄
- **적 등장 연출** — 등장 시 화면 위에서 호를 그리며 착지
- **카메라 경로** — 방 입장 시 카메라가 부드럽게 타겟으로 이동
- **UI 애니메이션** — 보상 아이템이 슬롯으로 날아가는 경로
- **식물 성장** — 덩굴이 뻗어나가는 모양

---

## 베지어 곡선 수식

### 2차 베지어 (Quadratic)

```
P(t) = (1−t)² P0  +  2(1−t)t P1  +  t² P2
```

- P0: 시작점, P1: 제어점(핸들), P2: 끝점
- t: 0~1 사이의 진행도

### 3차 베지어 (Cubic)

```
P(t) = (1−t)³ P0  +  3(1−t)²t P1  +  3(1−t)t² P2  +  t³ P3
```

- P0: 시작, P1·P2: 두 제어점, P3: 끝
- 더 유연한 S자 커브 가능

---

## Unity 구현 방법

### 방법 1: 직접 계산 (경량, 의존성 없음)

```csharp
public static class BezierUtil
{
    // 2차 베지어: 단순한 호(arc) 경로
    public static Vector2 Quadratic(Vector2 p0, Vector2 p1, Vector2 p2, float t)
    {
        float u = 1f - t;
        return u * u * p0 + 2f * u * t * p1 + t * t * p2;
    }

    // 3차 베지어: S자 경로
    public static Vector2 Cubic(Vector2 p0, Vector2 p1, Vector2 p2, Vector2 p3, float t)
    {
        float u = 1f - t;
        return u*u*u * p0 + 3*u*u*t * p1 + 3*u*t*t * p2 + t*t*t * p3;
    }

    // 경로 위 여러 점 샘플링 (LineRenderer나 미리 계산에 사용)
    public static Vector2[] Sample(Vector2 p0, Vector2 p1, Vector2 p2, int steps)
    {
        var points = new Vector2[steps + 1];
        for (int i = 0; i <= steps; i++)
            points[i] = Quadratic(p0, p1, p2, i / (float)steps);
        return points;
    }
}
```

### 방법 2: 코루틴으로 경로 따라 이동

```csharp
// 적이 화면에서 s자로 등장하는 예시
IEnumerator MoveAlongCurve(Vector2 startPos, Vector2 controlPoint, Vector2 endPos, float duration)
{
    float elapsed = 0f;
    while (elapsed < duration)
    {
        elapsed += Time.deltaTime;
        float t = Mathf.Clamp01(elapsed / duration);
        // ease in-out 적용
        float smoothT = t * t * (3f - 2f * t);
        transform.position = BezierUtil.Quadratic(startPos, controlPoint, endPos, smoothT);
        yield return null;
    }
    transform.position = endPos;
}
```

### 방법 3: 연속 스플라인 (Catmull-Rom)

여러 점을 부드럽게 연결하는 경로 — 경유지를 여러 개 지정할 때 편리.

```csharp
// 경유지 목록을 부드럽게 연결
public static Vector2 CatmullRom(Vector2 p0, Vector2 p1, Vector2 p2, Vector2 p3, float t)
{
    return 0.5f * (
        (2f * p1) +
        (-p0 + p2) * t +
        (2f*p0 - 5f*p1 + 4f*p2 - p3) * t * t +
        (-p0 + 3f*p1 - 3f*p2 + p3) * t * t * t
    );
}

// 전체 경로 진행 (waypoints가 4개 이상일 때)
public static Vector2 EvaluatePath(Vector2[] waypoints, float t)
{
    int n = waypoints.Length - 1;
    float scaledT = t * n;
    int i = Mathf.Clamp((int)scaledT, 0, n - 1);
    float localT = scaledT - i;
    
    int i0 = Mathf.Max(0, i - 1);
    int i1 = i;
    int i2 = Mathf.Min(n, i + 1);
    int i3 = Mathf.Min(n, i + 2);
    return CatmullRom(waypoints[i0], waypoints[i1], waypoints[i2], waypoints[i3], localT);
}
```

### 방법 4: DOTween을 쓰는 경우

```csharp
// DOTween의 DOPath가 베지어 경로를 지원
using DG.Tweening;

// 웨이포인트 배열로 부드러운 경로 (CubicBezier 타입)
Vector2[] waypoints = { p1, p2, endPos };
transform.DOPath(waypoints.ToV3(), duration, PathType.CubicBezier)
         .SetEase(Ease.InOutSine);
```

---

## 탄막에 베지어 적용

### 보스 탄이 s자로 휘어 오는 패턴

```csharp
public class CurvingProjectile : MonoBehaviour
{
    private Vector2 startPos;
    private Vector2 controlPoint;
    private Vector2 targetPos;
    private float speed = 1f;
    private float t;

    public void Init(Vector2 start, Vector2 control, Vector2 target, float duration)
    {
        startPos = start;
        controlPoint = control;
        targetPos = target;
        speed = 1f / duration;
        t = 0f;
    }

    void Update()
    {
        t += Time.deltaTime * speed;
        if (t >= 1f)
        {
            transform.position = targetPos;
            // 도착 처리
            Destroy(gameObject);
            return;
        }
        Vector2 pos = BezierUtil.Quadratic(startPos, controlPoint, targetPos, t);
        // 진행 방향으로 회전 (선택)
        Vector2 dir = (BezierUtil.Quadratic(startPos, controlPoint, targetPos, t + 0.01f) - pos).normalized;
        transform.up = dir;
        transform.position = pos;
    }
}
```

### 플레이어를 추적하는 커브 탄

```csharp
// 제어점을 플레이어 위치 기준으로 동적으로 계산
Vector2 playerPos = player.transform.position;
Vector2 spawnPos = transform.position;

// 제어점: 발사 방향의 90도 측면 — 탄이 옆으로 꺾여 들어옴
Vector2 perp = Vector2.Perpendicular((playerPos - spawnPos).normalized);
Vector2 controlPoint = (spawnPos + playerPos) * 0.5f + perp * curveStrength;
```

---

## 카메라 경로 사용

```csharp
// 방 입장 시 카메라가 타겟으로 부드럽게 이동
IEnumerator CameraEnterRoom(Vector3 from, Vector3 target, float duration)
{
    // 위에서 약간 내려오는 느낌의 제어점
    Vector3 control = (from + target) * 0.5f + Vector3.up * 2f;
    float elapsed = 0f;
    while (elapsed < duration)
    {
        elapsed += Time.deltaTime;
        float t = Mathf.SmoothStep(0, 1, elapsed / duration);
        cam.transform.position = BezierUtil.Quadratic(from, control, target, t);
        yield return null;
    }
    cam.transform.position = target;
}
```

---

## OnionCat 적용 포인트

### 1. 그림자 마녀 보스 탄막 패턴 강화
- 현재 직선 탄들을 s자/곡선 패턴으로 변경하면 패턴 다양성 급증
- 2차 베지어 하나로 "옆에서 휘어 들어오는 탄" 쉽게 구현
- 제어점을 무작위로 ±오프셋 → 같은 패턴인데 매번 다른 궤적

### 2. 작물 씨앗 탄 커브 샷 장비 효과
- "씨앗이 적을 추적해 꺾여 들어감" GearEffect 구현에 직접 사용
- `CurvingProjectile.Init(start, control, target)` 한 줄로 적용

### 3. 보상 아이템 UI 연출
- 장비 보상 선택 시 아이템이 슬롯 쪽으로 호를 그리며 날아가는 연출
- DOTween DOPath 또는 2차 베지어 코루틴으로 0.3초 연출

### 4. 고양이 등장 연출 (방 입장 시 걸어들어오기)
- `PaintedRoomView.WalkIn`에서 직선으로 걸어 들어오는 것을 살짝 호 형태로 변경 가능
- 단, 픽셀 아트 특성상 경로가 너무 복잡하면 발 위치가 타일에서 어색하게 보일 수 있음

### 5. 화분에서 식물이 뻗어나가는 연출
- 작물 고유기 R로 "심기" 시 식물이 뻗어나가는 애니메이션
- LineRenderer + Catmull-Rom으로 덩굴 경로 표현

---

## 주의 사항

- **등속 이동 착각 주의**: 베지어는 t에 대해 균일한 속도가 아님. 빠르게 갔다 느려지거나 반대가 될 수 있음.
  등속으로 만들려면 arc-length parameterization 필요 (복잡) → 대부분은 ease curve로 충분
- **픽셀 아트에서는 경로가 간단할수록 좋음**: 복잡한 커브는 픽셀이 너무 빠르게 흐르면 잔상이 보기 나쁠 수 있음
- **제어점 에디터 없이는 튜닝이 어려움**: 보스 패턴에 쓰기 전에 Gizmo로 제어점 시각화 필수

---

## 참고 링크

- Bezier curves explained: https://pomax.github.io/bezierinfo/ (가장 좋은 대화형 튜토리얼)
- Unity DOTween Path: https://dotween.demigiant.com/documentation.php#creatingPath
- Catmull-Rom in Unity: https://www.habrador.com/tutorials/math/4-interpolation/
- YouTube: "Math for Game Developers - Bezier Curves": https://www.youtube.com/watch?v=aVwxzDHniEw
