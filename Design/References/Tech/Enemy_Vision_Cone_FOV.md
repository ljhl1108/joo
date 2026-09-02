# Enemy Vision Cone FOV (시야각 감지)

리서치 날짜: 2026-09-02

## 개요

적이 "눈앞에 있는 것만" 인식하도록 시야각(Field of View)을 구현하는 기법.
단순 거리 감지에서 벗어나 방향성과 장애물 차단을 추가해 전략적 AI를 만든다.

OnionCat에서 Cat(근접)은 몸통으로 접근, Onion(원거리)은 뒤에서 지원하는 구조상
적이 "뒤를 못 봄" → 플레이어가 포지셔닝을 활용할 수 있어 협력 유도가 강해진다.

---

## Unity 구현 방법

### 핵심 3단계
1. **거리 체크** → 일정 반경 안에 있는지
2. **각도 체크** → 적의 전방(facing direction) 기준 시야각 내에 있는지
3. **레이캐스트** → 벽/장애물에 가려졌는지

### 단계별 코드

#### Step 1: 기본 구조 (FSM 연동 가능)

```csharp
public class EnemyVisionCone : MonoBehaviour
{
    [SerializeField] private float viewRadius = 6f;      // 시야 거리
    [SerializeField] private float viewAngle = 90f;      // 시야각 (양쪽 합산, 예: 90 = 좌우 45도)
    [SerializeField] private LayerMask playerMask;       // 플레이어 레이어
    [SerializeField] private LayerMask obstacleMask;     // 장애물 레이어

    private Transform detectedTarget;

    public bool CanSeePlayer(out Transform target)
    {
        target = null;

        // 1. 거리 내 플레이어 탐색
        Collider2D[] targetsInRadius = Physics2D.OverlapCircleAll(
            transform.position, viewRadius, playerMask);

        foreach (var col in targetsInRadius)
        {
            Transform t = col.transform;
            Vector2 dirToTarget = (t.position - transform.position).normalized;

            // 2. 시야각 체크
            float angle = Vector2.Angle(transform.up, dirToTarget); // up = 적의 전방
            if (angle < viewAngle / 2f)
            {
                float dist = Vector2.Distance(transform.position, t.position);

                // 3. 레이캐스트로 장애물 확인
                if (!Physics2D.Raycast(transform.position, dirToTarget,
                    dist, obstacleMask))
                {
                    target = t;
                    return true;
                }
            }
        }
        return false;
    }
}
```

#### Step 2: 전방 방향 설정

```csharp
// 이동 방향 = 전방으로 설정
private Vector2 facingDirection = Vector2.up;

void UpdateFacing(Vector2 moveDir)
{
    if (moveDir.sqrMagnitude > 0.01f)
        facingDirection = moveDir.normalized;
}

// 시야각 계산 시 facingDirection 사용
float angle = Vector2.Angle(facingDirection, dirToTarget);
```

#### Step 3: FSM과 연동

```csharp
public enum EnemyState { Idle, Patrol, Chase, Attack }

void Update()
{
    switch (currentState)
    {
        case EnemyState.Patrol:
            if (visionCone.CanSeePlayer(out Transform t))
            {
                detectedTarget = t;
                ChangeState(EnemyState.Chase);
            }
            break;

        case EnemyState.Chase:
            // 시야 잃으면 마지막 위치로 이동
            if (!visionCone.CanSeePlayer(out _))
            {
                ChangeState(EnemyState.Patrol);
            }
            break;
    }
}
```

#### Step 4: 시각화 (Gizmos)

```csharp
void OnDrawGizmosSelected()
{
    Gizmos.color = Color.yellow;
    Gizmos.DrawWireSphere(transform.position, viewRadius);

    // 시야각 경계선 2개
    Vector3 leftDir = DirFromAngle(-viewAngle / 2, false);
    Vector3 rightDir = DirFromAngle(viewAngle / 2, false);

    Gizmos.color = Color.red;
    Gizmos.DrawLine(transform.position,
        transform.position + leftDir * viewRadius);
    Gizmos.DrawLine(transform.position,
        transform.position + rightDir * viewRadius);
}

Vector3 DirFromAngle(float angle, bool isGlobal)
{
    if (!isGlobal) angle += transform.eulerAngles.z;
    return new Vector3(
        Mathf.Sin(angle * Mathf.Deg2Rad),
        Mathf.Cos(angle * Mathf.Deg2Rad), 0);
}
```

---

## 성능 최적화

```csharp
// OverlapCircleAll 대신 NonAlloc 버전 사용
private Collider2D[] hitBuffer = new Collider2D[10];

int count = Physics2D.OverlapCircleNonAlloc(
    transform.position, viewRadius, hitBuffer, playerMask);

for (int i = 0; i < count; i++)
{
    // hitBuffer[i] 처리
}
```

또는 감지 체크를 매 프레임이 아닌 0.2초 간격으로 실행:

```csharp
void Start()
{
    StartCoroutine(DetectionRoutine());
}

IEnumerator DetectionRoutine()
{
    WaitForSeconds wait = new WaitForSeconds(0.2f);
    while (true)
    {
        CheckVision();
        yield return wait;
    }
}
```

---

## OnionCat 적용 포인트

### 1. "뒤에서 공격" 협력 유도
```
적 시야각 = 120도 (전방 집중)
Cat이 정면에서 주의 끌기 → Onion이 사각지대에서 원거리 공격
→ 두 플레이어가 자연스럽게 역할 분담
```

### 2. 적 타입별 시야각 변형

| 적 타입 | 시야각 | 시야 거리 | 특성 |
|---------|--------|-----------|------|
| 근접 전사 | 90° | 5m | 정면만 봄, 뒤로 돌아가기 유리 |
| 순찰병 | 180° | 7m | 넓지만 멀리 못 봄 |
| 저격수 | 40° | 12m | 좁지만 매우 멀리 봄 |
| 사방경계 | 360° | 4m | 스텔스 회피 불가 |

### 3. "약점" 시스템과 연동
근접(Cat)에만 반응하는 적 = 원거리(Onion) 시야각에서 Onion 레이어 제외:

```csharp
// 원거리에만 약한 적: playerMask에서 Cat 레이어 제거
// 근접에만 약한 적: playerMask에서 Onion 레이어 제거
[SerializeField] private LayerMask playerMask; // 유니티 에디터에서 설정
```

### 4. 청각 감지 추가 (optional)
공격 소리 → 시야 없어도 감지:

```csharp
public void HearSound(Vector2 soundPos, float loudness)
{
    float dist = Vector2.Distance(transform.position, soundPos);
    if (dist < loudness) // 소리 반경 내
    {
        lastKnownPosition = soundPos;
        ChangeState(EnemyState.Investigate);
    }
}
```

---

## Inspector 설정 필요 항목
- `EnemyVisionCone` 컴포넌트:
  - `playerMask`: "Player" 레이어 드래그
  - `obstacleMask`: "Wall", "Obstacle" 레이어 드래그
  - `viewRadius`: 5~8 (방 크기에 맞게)
  - `viewAngle`: 90~120 (기본 적), 360 (360도 감지 적)

---

## 참고 링크

- Sebastian Lague - Field of View: https://youtu.be/rQG9aUWarwE
- Unity Docs - Physics2D.OverlapCircleNonAlloc: https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircleNonAlloc.html
- Unity Docs - Physics2D.Raycast: https://docs.unity3d.com/ScriptReference/Physics2D.Raycast.html
- Brackeys - 2D FOV Tutorial: https://youtu.be/-uOCnpRPMbU
