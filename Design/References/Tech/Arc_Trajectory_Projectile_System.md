# 포물선 투사체 시스템 (Arc Trajectory Projectile)

리서치 날짜: 2026-08-21

## 개요

직선이 아닌 **포물선(Arc)** 궤도로 이동하는 투사체 시스템.
중력의 영향을 받아 날아가는 수류탄, 박격포탄, 씨앗 투척 등에 사용.
OnionCat에서는 Onion이 씨앗/폭탄을 위로 던지거나, 적 박격포 공격 등에 활용.
기존 `Projectile_System.md`(직선/호밍)를 보완하는 포물선 전용 서브시스템.

---

## Unity 구현 방법

### 방법 1: Rigidbody2D + 중력 (물리 기반, 가장 단순)

```csharp
public class ArcProjectile : MonoBehaviour
{
    private Rigidbody2D _rb;

    public void Launch(Vector2 startPos, Vector2 targetPos, float height = 3f)
    {
        transform.position = startPos;
        _rb = GetComponent<Rigidbody2D>();
        _rb.gravityScale = 1f;
        
        // 포물선 초기 속도 계산
        Vector2 velocity = CalculateLaunchVelocity(startPos, targetPos, height);
        _rb.linearVelocity = velocity;
    }

    private Vector2 CalculateLaunchVelocity(Vector2 from, Vector2 to, float apexHeight)
    {
        float g = Mathf.Abs(Physics2D.gravity.y) * _rb.gravityScale;

        // 최고점까지 올라가는 데 걸리는 시간
        float displacementY = to.y - from.y;
        float timeUp = Mathf.Sqrt(2f * apexHeight / g);
        float timeDown = Mathf.Sqrt(2f * (apexHeight - displacementY) / g);
        float totalTime = timeUp + timeDown;

        float vx = (to.x - from.x) / totalTime;
        float vy = g * timeUp;  // 위로 쏘는 속도

        return new Vector2(vx, vy);
    }
}
```

### 방법 2: Lerp 기반 (물리 없이 수학적 궤도 제어)

물리 없이 정확한 궤도를 원할 때. OnionCat처럼 격실감이 있는 픽셀아트 스타일에 더 잘 맞음.

```csharp
public class ArcProjectileLerp : MonoBehaviour
{
    public IEnumerator MovArc(Vector2 start, Vector2 end, float duration, float arcHeight)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / duration;

            // 직선 보간
            Vector2 linear = Vector2.Lerp(start, end, t);
            
            // 포물선 오프셋 (sin 곡선으로 자연스러운 아치)
            float arcOffset = arcHeight * Mathf.Sin(Mathf.PI * t);
            
            transform.position = new Vector2(linear.x, linear.y + arcOffset);
            
            // 투사체 회전 (이동 방향으로 자동 회전)
            Vector2 dir = end - start;
            float angle = Mathf.Atan2(dir.y + arcOffset, dir.x) * Mathf.Rad2Deg;
            transform.rotation = Quaternion.Euler(0, 0, angle);
            
            yield return null;
        }
        
        // 착탄 처리
        OnLand();
    }
}
```

### 방법 3: LineRenderer로 궤도 미리보기

플레이어에게 투척 궤도를 미리 보여주는 점선 표시.

```csharp
[RequireComponent(typeof(LineRenderer))]
public class ArcTrajectoryPreview : MonoBehaviour
{
    [SerializeField] private int _resolution = 20;
    private LineRenderer _lr;

    private void Awake() => _lr = GetComponent<LineRenderer>();

    public void ShowPreview(Vector2 start, Vector2 end, float height)
    {
        _lr.positionCount = _resolution;
        for (int i = 0; i < _resolution; i++)
        {
            float t = i / (float)(_resolution - 1);
            Vector2 linear = Vector2.Lerp(start, end, t);
            float arcOffset = height * Mathf.Sin(Mathf.PI * t);
            _lr.SetPosition(i, new Vector3(linear.x, linear.y + arcOffset, 0));
        }
    }

    public void HidePreview() => _lr.positionCount = 0;
}
```

### 착탄 판정 (그림자 / 착지점 표시)

```csharp
public class ArcProjectileShadow : MonoBehaviour
{
    [SerializeField] private GameObject _shadowPrefab;
    private GameObject _shadow;

    public void SpawnShadow(Vector2 landingPoint)
    {
        _shadow = Instantiate(_shadowPrefab, landingPoint, Quaternion.identity);
    }

    private void OnLand()
    {
        if (_shadow != null) Destroy(_shadow);
        // 착탄 폭발 이펙트, 범위 피해 등
        Explode();
    }
}
```

---

## OnionCat 적용 포인트

### Onion 씨앗 투척 업그레이드
- 기본 직선 투사체 → 업그레이드 후 포물선 씨앗으로 변경
- 씨앗이 착탄 후 독 웅덩이 / 불꽃 구역 / 슬로우 존 생성
- Cat과의 협동: Cat이 적을 특정 착탄 예상 지점으로 유인 → Onion이 씨앗 투척

### 적 박격포 타입 추가
- "박격포 고블린": 플레이어에게 포물선 폭탄 투척
- 착탄 직전 바닥에 빨간 원 경고 표시 (0.5초 전)
- 이동으로 회피 가능 → 패턴 학습 로그라이크 기본기

### 메카닉 조합
- 원거리 약점 적: Onion의 직선 투사체로만 처치
- 포물선 전용 약점 적: 아치형 공격에만 반응 (벽 뒤에 숨어있는 적)
- Cat의 근접 공격으로 장막을 뚫고 들어간 후 Onion이 포물선으로 마무리

### 궤도 미리보기 = 협동 커뮤니케이션
- Onion이 조준 시 점선 미리보기 표시
- Cat 플레이어가 "거기로 적 유인해야겠다" 인식 → 비언어적 협동 유도

---

## 참고 링크

- Unity 공식 - Rigidbody2D: https://docs.unity3d.com/Manual/class-Rigidbody2D.html
- 포물선 수학 (게임 개발): https://gamedev.stackexchange.com/questions/17080/throw-object-to-target-in-2d
- LineRenderer 공식 문서: https://docs.unity3d.com/Manual/class-LineRenderer.html
- 유튜브 튜토리얼: "Unity 2D Arc Projectile" (Game Dev Guide 채널 참고)
- 탄도 계산 공식 정리: https://en.wikipedia.org/wiki/Projectile_motion
