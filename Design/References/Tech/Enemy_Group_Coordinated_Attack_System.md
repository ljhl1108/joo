# 적 그룹 협동 공격 패턴 설계 (Enemy Group Coordinated Attack System)

리서치 날짜: 2026-08-15

## 개요
단일 적의 AI는 상태머신(State Machine)으로 충분하지만, **여러 적이 그룹으로 협동**할 때는 그룹 레벨의 조율 시스템이 필요하다. OnionCat처럼 "근접 약점 적 + 원거리 약점 적"이 같은 방에 등장할 때, 이들이 역할 분담해서 플레이어를 압박하는 구조가 핵심 재미를 만든다.

단순히 개별 AI들이 각자 움직이는 것과, 그룹으로 조율된 공격 사이의 차이는 플레이어가 체감하는 "적이 영리하다"는 인상에 직결된다.

---

## Unity 구현 방법

### 1. 기본 구조: EnemyGroup 컴포넌트

스폰된 적 그룹을 관리하는 상위 컴포넌트. 개별 EnemyAI는 자신의 역할만 수행하고, EnemyGroup이 전체를 조율한다.

```csharp
public enum GroupRole { Pressure, Support, Flank, Idle }

public class EnemyGroup : MonoBehaviour
{
    [SerializeField] private List<EnemyAI> members = new();

    private void Start()
    {
        AssignRoles();
    }

    private void AssignRoles()
    {
        int total = members.Count;
        for (int i = 0; i < total; i++)
        {
            // 첫 번째는 압박(P1 타겟), 나머지는 지원(P2 타겟) 또는 측면
            if (i == 0)
                members[i].SetGroupRole(GroupRole.Pressure);
            else if (i % 2 == 1)
                members[i].SetGroupRole(GroupRole.Support);
            else
                members[i].SetGroupRole(GroupRole.Flank);
        }
    }

    // 그룹원 사망 시 역할 재조정
    public void OnMemberDied(EnemyAI deadMember)
    {
        members.Remove(deadMember);
        if (members.Count > 0)
            AssignRoles();
    }
}
```

### 2. EnemyAI에 역할 수신 연동

```csharp
public class EnemyAI : MonoBehaviour
{
    private GroupRole groupRole = GroupRole.Idle;
    private Transform player1; // P1(고양이): 근접 타겟
    private Transform player2; // P2(파): 원거리 타겟
    [SerializeField] private float supportMinDistance = 5f;
    [SerializeField] private float moveSpeed = 3f;

    private Rigidbody2D rb;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        // 반드시 Awake에서 캐싱
        player1 = GameManager.Instance.Player1.transform;
        player2 = GameManager.Instance.Player2.transform;
    }

    public void SetGroupRole(GroupRole role)
    {
        groupRole = role;
    }

    private void FixedUpdate()
    {
        switch (groupRole)
        {
            case GroupRole.Pressure:
                MoveToward(player1.position);
                break;
            case GroupRole.Support:
                MaintainDistanceAndShoot();
                break;
            case GroupRole.Flank:
                // 그룹 매니저가 위치 계산 후 SetFlankTarget() 호출
                break;
        }
    }

    private void MoveToward(Vector3 target)
    {
        Vector2 dir = ((Vector2)target - rb.position).normalized;
        rb.MovePosition(rb.position + dir * moveSpeed * Time.fixedDeltaTime);
    }

    private void MaintainDistanceAndShoot()
    {
        float dist = Vector2.Distance(transform.position, player1.position);
        if (dist < supportMinDistance)
        {
            // 너무 가까우면 뒤로 물러남
            Vector2 away = ((Vector2)transform.position - (Vector2)player1.position).normalized;
            rb.MovePosition(rb.position + away * moveSpeed * Time.fixedDeltaTime);
        }
        // P2 방향으로 사격 (별도 ShootController 연동)
        ShootAt(player2.position);
    }

    private void ShootAt(Vector3 target)
    {
        // ProjectileSystem 연동 (기존 구현 활용)
    }

    // 사망 시 EnemyGroup에 알림
    private void OnDestroy()
    {
        GetComponentInParent<EnemyGroup>()?.OnMemberDied(this);
    }
}
```

### 3. 측면 포위 패턴 (Flanking Pattern)

3마리가 120도씩 분산하여 플레이어를 삼각형으로 포위:

```csharp
public class FlankCoordinator : MonoBehaviour
{
    [SerializeField] private List<EnemyAI> flankers = new();
    [SerializeField] private float flankRadius = 3f;
    private Transform player1;

    private void Awake()
    {
        player1 = GameManager.Instance.Player1.transform;
    }

    private void Update()
    {
        for (int i = 0; i < flankers.Count; i++)
        {
            if (flankers[i] == null) continue;
            Vector2 targetPos = CalculateFlankPosition(i, flankers.Count);
            flankers[i].SetFlankTarget(targetPos);
        }
    }

    private Vector2 CalculateFlankPosition(int index, int total)
    {
        float angle = (360f / total) * index * Mathf.Deg2Rad;
        return (Vector2)player1.position
               + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * flankRadius;
    }
}
```

### 4. 동기화 공격 패턴 (Synchronized Attack)

모든 그룹원이 **텔레그래프 → 동시 돌진**하는 패턴. 보스 미니언에 적합:

```csharp
public class GroupAttackCoordinator : MonoBehaviour
{
    [SerializeField] private List<EnemyAI> members = new();
    [SerializeField] private float telegraphDuration = 1.5f; // 경고 시간

    public void TriggerSyncAttack()
    {
        StartCoroutine(SyncAttackSequence());
    }

    private IEnumerator SyncAttackSequence()
    {
        // 1단계: 전원 공격 준비 자세 (빨간 테두리 등 시각 신호)
        foreach (var m in members)
            if (m != null) m.PlayAttackTelegraph();

        yield return new WaitForSeconds(telegraphDuration);

        // 2단계: 동시 공격 실행
        foreach (var m in members)
            if (m != null) m.ExecuteAttack();
    }
}
```

### 5. 교대 압박 패턴 (Alternating Pressure)

한 적이 공격하는 동안 다른 적은 재충전. 회피 창구를 열어두되 쉬지 못하게 하는 패턴:

```csharp
private IEnumerator AlternatingAttackLoop()
{
    int current = 0;
    while (members.Count > 0)
    {
        if (members[current] == null)
        {
            members.RemoveAt(current);
            if (members.Count == 0) break;
        }

        members[current].BeginAttack();
        yield return new WaitForSeconds(attackDuration);
        members[current].EndAttack();

        current = (current + 1) % members.Count;
        yield return new WaitForSeconds(0.3f); // 짧은 교대 텀
    }
}
```

### 6. 스포너에서 EnemyGroup 초기화

방 스포너(RoomSpawner)가 그룹을 한 번에 생성하고 EnemyGroup에 등록:

```csharp
public class RoomSpawner : MonoBehaviour
{
    [SerializeField] private GameObject[] enemyPrefabs;
    [SerializeField] private Transform[] spawnPoints;

    public void SpawnEnemyGroup()
    {
        EnemyGroup group = new GameObject("EnemyGroup").AddComponent<EnemyGroup>();

        for (int i = 0; i < enemyPrefabs.Length; i++)
        {
            GameObject enemy = Instantiate(enemyPrefabs[i], spawnPoints[i].position, Quaternion.identity);
            enemy.transform.SetParent(group.transform);
        }
        // EnemyGroup.Start()에서 자동으로 역할 배분됨
    }
}
```

---

## OnionCat 적용 포인트

### 핵심 우선순위 구현 순서

1. **압박-지원 패턴 (Pressure-Support)** — 가장 먼저 구현
   - Pressure 적: P1(고양이) 타겟, 근접 돌진
   - Support 적: P2(파) 타겟, 안전 거리 유지 + 원거리 사격
   - 이 패턴 하나만으로도 "P1이 막는 동안 P2가 원거리 처리" 협동이 자동 발생

2. **측면 포위 패턴** — 중간 스테이지부터 도입
   - 3마리 포위 시 P1이 이동하며 하나씩 근접, P2가 측면 원거리 지원
   - 너무 이른 도입은 초보자에게 가혹하므로 3~5번째 방 이후

3. **동기화 공격** — 엘리트 그룹 or 보스 페이즈에서만
   - 텔레그래프 1.5초는 반드시 시각적으로 명확하게 (빨간 색상 / 경고음)
   - 이 패턴은 "대비할 수 있는 위험"이어야 함. 텔레그래프 없으면 불공정

4. **교대 압박** — 보스 2페이즈 또는 고난이도 방에서
   - 쉬지 못하게 하되, 교대 타이밍마다 반격 창구를 줌

### 약점 타입과 역할 분화 연동 (OnionCat 핵심)
```
Pressure 역할 = 근접 약점 (원거리 면역) → P1만 처치 가능
Support 역할  = 원거리 약점 (근접 회피)  → P2만 처치 가능
```
이 구조가 완성되면 플레이어가 **"자연스럽게 역할을 소통"**하게 됨.
"저 앞쪽 거 내가 갈게, 뒤에 빛나는 거 쏴줘!"

### 구현 주의사항
- `EnemyGroup.OnMemberDied()`에서 역할 재조정: 멤버가 줄어도 남은 멤버끼리 역할 균형 유지
- `GetComponentInParent<EnemyGroup>()` 대신 직접 참조 주입 권장 (성능)
- 방 클리어 시 `Destroy(enemyGroup.gameObject)` 호출로 그룹 전체 일괄 정리

---

## 참고 링크
- Unity State Machine 문서: https://docs.unity3d.com/Manual/StateMachineBasics.html
- Game AI Pro (그룹 전술 챕터): https://www.gameaipro.com/
- GDC — Enemy Design in Into the Breach: https://www.gdcvault.com/play/1024324/
- Spelunky AI 설계 분석: https://tinysubversions.com/spelunky-book/
- Unity Rigidbody2D MovePosition: https://docs.unity3d.com/ScriptReference/Rigidbody2D.MovePosition.html
- 2D 레이어 매트릭스: https://docs.unity3d.com/Manual/LayerBasedCollision.html
