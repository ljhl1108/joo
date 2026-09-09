# Enemy Flanking & Encirclement AI

리서치 날짜: 2026-09-09

## 개요

적들이 단순히 플레이어를 향해 직선으로 돌진하는 것이 아니라, **옆면·뒤쪽을 노리는 포위 전술**을 사용하는 AI 시스템이다. 탑다운 로그라이크에서 적이 밀집 공격이 아닌 **포위망을 형성**하면 플레이어가 한 방향만 방어할 수 없게 되어 전략적 깊이가 크게 증가한다. OnionCat에서는 근접/원거리 취약 구분 시스템과 결합해 "왼쪽 측면은 Cat이 슬래시, 오른쪽은 Onion이 투사체" 같은 자연스러운 역할 분담 상황을 만들어낼 수 있다.

---

## Unity 구현 방법

### 방법 1: 각도 기반 대형 배치 (Angle-Based Formation)

각 적에게 "담당 각도(assignedAngle)"를 배정하고, 해당 각도 방향의 플레이어 주변 포인트를 목표로 이동시킨다.

```csharp
public class FlankingEnemy : MonoBehaviour
{
    [SerializeField] private float flankRadius = 2.5f;   // 플레이어 주변 공전 반지름
    [SerializeField] private float assignedAngle = 0f;   // 담당 각도 (도)
    [SerializeField] private float moveSpeed = 3f;
    [SerializeField] private float attackRange = 1.5f;

    private Transform player;
    private Rigidbody2D rb;
    private bool isAttacking;

    void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    public void Initialize(Transform playerTransform, float angle)
    {
        player = playerTransform;
        assignedAngle = angle;
    }

    void FixedUpdate()
    {
        if (player == null || isAttacking) return;

        Vector2 flankTarget = GetFlankPosition();
        float distToTarget = Vector2.Distance(transform.position, flankTarget);

        if (distToTarget < 0.3f)
        {
            // 포위 위치 도달 → 공격 전환
            StartCoroutine(AttackSequence());
        }
        else
        {
            Vector2 dir = (flankTarget - (Vector2)transform.position).normalized;
            rb.linearVelocity = dir * moveSpeed;
        }
    }

    Vector2 GetFlankPosition()
    {
        float rad = assignedAngle * Mathf.Deg2Rad;
        return (Vector2)player.position + new Vector2(
            Mathf.Cos(rad) * flankRadius,
            Mathf.Sin(rad) * flankRadius
        );
    }

    IEnumerator AttackSequence()
    {
        isAttacking = true;
        rb.linearVelocity = Vector2.zero;
        // 공격 로직 (애니메이션, 데미지)
        yield return new WaitForSeconds(0.8f);
        isAttacking = false;
    }
}
```

### 방법 2: EnemyGroupCoordinator — 그룹 단위 각도 배분

```csharp
public class EnemyGroupCoordinator : MonoBehaviour
{
    private List<FlankingEnemy> members = new List<FlankingEnemy>();
    private Transform player;

    public void RegisterEnemy(FlankingEnemy enemy)
    {
        members.Add(enemy);
        ReassignAngles();
    }

    public void UnregisterEnemy(FlankingEnemy enemy)
    {
        members.Remove(enemy);
        ReassignAngles();
    }

    void ReassignAngles()
    {
        if (members.Count == 0) return;
        float step = 360f / members.Count;
        for (int i = 0; i < members.Count; i++)
        {
            members[i].Initialize(player, i * step);
        }
    }
}
```

### 방법 3: 동적 포위 — 사망 시 틈새 메우기

적이 하나 죽으면 남은 적들이 각도를 재분배해 포위망을 유지한다.
→ `EnemyGroupCoordinator.UnregisterEnemy()` 호출 시 `ReassignAngles()` 자동 실행

### 방법 4: 후방 우선 포위 (Blind Spot Flanking)

단순 균등 배치 대신, **플레이어가 바라보는 방향 반대쪽 적이 먼저 접근**하도록:

```csharp
Vector2 GetPriorityFlankPosition(Vector2 playerFacingDir)
{
    // 뒤쪽(180도) 방향 우선 배치
    float backAngle = Mathf.Atan2(-playerFacingDir.y, -playerFacingDir.x) * Mathf.Rad2Deg;
    float finalAngle = backAngle + assignedAngle;   // assignedAngle은 작은 오프셋
    float rad = finalAngle * Mathf.Deg2Rad;
    return (Vector2)player.position + new Vector2(
        Mathf.Cos(rad) * flankRadius,
        Mathf.Sin(rad) * flankRadius
    );
}
```

### 방법 5: 장애물 회피와의 결합

`Physics2D.Raycast`로 포위 목표 지점까지의 장애물을 감지하고, 가로막히면 각도를 조금씩 회전해 우회한다:

```csharp
Vector2 FindClearFlankPosition(Vector2 ideal)
{
    for (int deg = 0; deg <= 90; deg += 15)
    {
        float tryAngle = (assignedAngle + deg) * Mathf.Deg2Rad;
        Vector2 candidate = (Vector2)player.position + new Vector2(
            Mathf.Cos(tryAngle) * flankRadius,
            Mathf.Sin(tryAngle) * flankRadius
        );
        if (!Physics2D.Linecast(transform.position, candidate, wallLayer))
            return candidate;
    }
    return ideal;   // 모두 막혀있으면 원래 위치로
}
```

---

## OnionCat 적용 포인트

### 1. 근접/원거리 취약 적의 포위 조합

- **근접 취약 적(Cat이 잡아야 함)**: 플레이어 측면·후방에 배치 → Cat이 몸을 돌려 슬래시해야 함
- **원거리 취약 적(Onion이 잡아야 함)**: 플레이어 전방에 배치 → Onion 마우스 조준으로 자연스럽게 맡음
- 포위 조합 하나가 이미 역할 분담 시나리오를 자동 생성

### 2. EnemyGroupCoordinator → Room에 1개 배치

방 진입 시 `RoomCombatDirector`가 적 그룹 조율자에게 플레이어 Transform 전달:
```csharp
void OnRoomEntered(Transform playerTransform)
{
    coordinator.SetPlayer(playerTransform);
    foreach (var enemy in spawnedEnemies)
        coordinator.RegisterEnemy(enemy);
}
```

### 3. 포위 해제 보상

- Cat이 슬래시로 측면 적을 처치 → 포위망 개방 → P2가 뒤를 봐줘야 하는 압박 해소
- 포위 해제 순간 도파민 피크 → 협력 플레이의 만족감

### 4. 구현 시 주의 사항

- 적이 3마리 이상일 때 포위 효과 발생 → 1~2마리는 일반 추격 AI 사용
- 포위 반지름(`flankRadius`)을 방 크기의 30% 이내로 설정 → 좁은 방에서 무효화 방지
- 협력 적(Coordinator) 제거 시 나머지 적이 다시 직선 추격으로 전환 → AI "보스" 개념으로 활용 가능

---

## 참고 링크

- Unity Steering Behaviors (Craig Reynolds) - AI 이동 기반 이론: https://www.red3d.com/cwr/steer/
- Game AI Pro — Formations & Flanking 챕터: http://gameaipro.com/GameAIPro/GameAIPro_Chapter19_Tactics_Without_Giving_It_Much_Thought.pdf
- Unity Forum — Group Enemy AI Discussion: https://discussions.unity.com/t/group-enemy-ai/
- Gamasutra — Coordinated AI Movement: https://www.gamedeveloper.com/design/designing-coordinated-multi-enemy-encounters
- YouTube — Code Monkey Enemy AI Tutorial: https://www.youtube.com/watch?v=db0KWYaWfeM
