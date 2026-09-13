# Enemy Leash Return System (적 유인 & 귀환 시스템)

리서치 날짜: 2026-09-13

## 개요

"리시(Leash)"란 개 목줄처럼, 적이 스폰 위치 또는 패트롤 구역으로부터 일정 거리 이상 벗어나면 자동으로 귀환하는 시스템이다.

**왜 필요한가**: 방 기반 로그라이크에서 플레이어가 적을 방 밖으로 유인하면 안전 지역에서 일방적으로 처치할 수 있다. 리시 시스템은 이를 막아 방 안에서의 전투를 강제하고, 적들이 한 곳에 뭉치는 것을 방지하며, 각 방의 설계 의도(좁은 공간, 장애물 등)를 살린다.

OnionCat에서는 방 문이 클리어 전까지 잠기므로 플레이어가 방 밖으로 도망칠 수 없지만, **방 안에서 한 구석으로 적을 유인해 스폰 위치를 이탈시키는** 상황에 대응하기 위해 필요하다. 또한 패트롤 적이 너무 넓게 퍼지지 않도록 통제한다.

---

## Unity 구현 방법

### 핵심 구조

```csharp
public class EnemyLeash : MonoBehaviour
{
    [SerializeField] private float leashRadius = 8f;       // 스폰에서 최대 이탈 거리
    [SerializeField] private float returnRadius = 1.5f;    // 귀환 완료로 판정할 거리
    [SerializeField] private float leashTriggerDelay = 1f; // 범위 이탈 후 귀환 시작까지 대기
    [SerializeField] private float returnSpeed = 5f;       // 귀환 이동 속도

    private Vector2 _spawnPosition;
    private EnemyStateMachine _stateMachine;
    private float _outOfRangeTimer;
    private bool _isReturning;

    public bool IsReturning => _isReturning;

    private void Awake()
    {
        _stateMachine = GetComponent<EnemyStateMachine>();
    }

    private void Start()
    {
        _spawnPosition = transform.position; // Start()에서 캐싱 — Awake() 아님
    }

    private void Update()
    {
        float distFromSpawn = Vector2.Distance(transform.position, _spawnPosition);

        if (!_isReturning)
        {
            if (distFromSpawn > leashRadius)
            {
                _outOfRangeTimer += Time.deltaTime;
                if (_outOfRangeTimer >= leashTriggerDelay)
                    StartReturn();
            }
            else
            {
                _outOfRangeTimer = 0f;
            }
        }
        else
        {
            MoveTowardSpawn();
            if (distFromSpawn <= returnRadius)
                EndReturn();
        }
    }

    private void StartReturn()
    {
        _isReturning = true;
        _stateMachine.ForceState(EnemyState.Returning);
        GetComponent<SpriteRenderer>().color = Color.gray; // 귀환 중 시각 표시
    }

    private void MoveTowardSpawn()
    {
        Vector2 dir = (_spawnPosition - (Vector2)transform.position).normalized;
        GetComponent<Rigidbody2D>().MovePosition(
            (Vector2)transform.position + dir * returnSpeed * Time.deltaTime
        );
    }

    private void EndReturn()
    {
        _isReturning = false;
        _outOfRangeTimer = 0f;
        GetComponent<SpriteRenderer>().color = Color.white;
        _stateMachine.ForceState(EnemyState.Idle);
        // 선택: 귀환 후 체력 일부 회복
        // GetComponent<EnemyHealth>().Heal(returnHealAmount);
    }
}
```

### EnemyStateMachine 연동 (상태 추가)

```csharp
public enum EnemyState
{
    Idle,
    Patrol,
    Chase,
    Attack,
    Returning,  // 귀환 상태 추가
    Dead
}
```

귀환 상태일 때 AI 로직에서 플레이어 추적/공격을 비활성화:

```csharp
// EnemyAI Update() 내부
if (_leash != null && _leash.IsReturning) return; // 귀환 중엔 AI 비활성
```

### 리시 반경 Gizmo 시각화

```csharp
private void OnDrawGizmosSelected()
{
    Gizmos.color = new Color(1f, 0.5f, 0f, 0.3f);
    Vector2 center = Application.isPlaying ? _spawnPosition : (Vector2)transform.position;
    Gizmos.DrawWireSphere(center, leashRadius);

    Gizmos.color = new Color(0f, 1f, 0f, 0.3f);
    Gizmos.DrawWireSphere(center, returnRadius);
}
```

### ScriptableObject 기반 설정

```csharp
[CreateAssetMenu(menuName = "OnionCat/EnemyLeashConfig")]
public class EnemyLeashConfig : ScriptableObject
{
    public float leashRadius = 8f;
    public float returnRadius = 1.5f;
    public float leashTriggerDelay = 1f;
    public bool healOnReturn = false;
    public float healAmount = 10f;
}
```

Inspector에서 방 유형별로 다른 설정 적용 가능.

---

## OnionCat 적용 포인트

### 1. 방 전투 무결성 보장
OnionCat 방에는 장애물, 가시 함정, 좁은 통로가 있음. 적이 Cat에게 유인되어 방 한쪽 구석에만 모이면 Onion의 사거리 밖으로 벗어날 수 있음. 리시 시스템으로 적이 스폰 구역 ±4~6 타일 내에 머물도록 제한 → 방 설계 의도 유지.

### 2. 약점 메카닉과 결합
OnionCat의 핵심: "근접 약점 적" vs "원거리 약점 적". 이 적들이 Cat이 원하는 방향으로만 끌려다니면 Onion이 닿지 않는 곳에 갇힐 수 있음. 리시로 적이 방 중앙으로 귀환하면 자연스럽게 두 플레이어 모두의 사거리 내로 진입.

### 3. 귀환 중 무적 처리 여부
- **무적 부여 X (OnionCat 권장)**: 귀환 도중 처치 가능. Cat의 대시+슬래시로 추격 처치 가능 → 공격적인 플레이 보상. "도망가는 적은 취약하다"는 직관적 전술.
- **무적 부여 O**: 귀환이 확실히 완료됨, 하지만 "갑자기 안 죽는 적" 발생.

### 4. 귀환 후 체력 회복
OnionCat 권장: 귀환 시 HP 20% 회복. 짧은 도주는 의미 없고 방 안 싸움을 강제. 플레이어가 적을 방 내에서 즉시 처치해야 하는 긴장감 생성.

### 5. 보스에는 리시 미적용
보스는 방 전체를 자유롭게 이동. `EnemyLeash` 컴포넌트를 일반 적 프리팹에만 부착, 보스 프리팹에는 미부착.

---

## 참고 링크

- Unity Docs - Rigidbody2D.MovePosition: https://docs.unity3d.com/ScriptReference/Rigidbody2D.MovePosition.html
- Game Developer - Enemy AI Design: https://www.gamedeveloper.com/design/enemy-ai-design-patterns
- Enter the Gungeon 적 AI 분석: YouTube 검색 "Enter the Gungeon AI breakdown"
- GDC Vault 검색 "roguelike enemy ai design"
