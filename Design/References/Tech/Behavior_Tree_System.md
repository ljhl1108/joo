# Behavior Tree 시스템

리서치 날짜: 2026-07-07

## 개요

Behavior Tree(행동 트리)는 적 AI를 계층적 트리 구조로 표현하는 방법론이다. 상태머신(State Machine)이 "현재 어떤 상태인가"를 관리한다면, 행동 트리는 "지금 무엇을 해야 하는가"를 매 프레임 결정한다. 상태가 5개 이상 늘어나거나 조건 분기가 복잡해질 때 State Machine보다 훨씬 유지보수가 쉽다.

OnionCat 입장에서는 일반 잡몹은 State Machine으로 충분하지만, **엘리트 적이나 보스**처럼 패턴이 복합적인 경우 Behavior Tree가 유리하다.

---

## 핵심 노드 종류

### Control Flow 노드 (흐름 제어)

| 노드 | 동작 방식 | 반환 |
|---|---|---|
| **Sequence** | 자식을 순서대로 실행, 하나라도 Fail이면 즉시 Fail | 모두 Success → Success |
| **Selector** | 자식을 순서대로 시도, 하나라도 Success면 즉시 Success | 모두 Fail → Fail |
| **Parallel** | 자식을 동시에 실행 (조건 정책 설정 가능) | 정책에 따라 다름 |

### Decorator 노드 (수식자)

- **Inverter**: 자식 결과를 반전 (Success↔Fail)
- **Repeater**: N번 반복 또는 무한 반복
- **Cooldown**: 일정 시간 동안 자식 실행 금지
- **Timeout**: N초 안에 완료 안 되면 Fail

### Leaf 노드 (실제 동작)

- **Action**: 실제 행동 수행 (이동, 공격, 애니메이션)
- **Condition**: 조건 확인만 (True/False 반환)

---

## Unity 구현 방법

### 기본 구조 (직접 구현)

```csharp
// 노드 기본 클래스
public abstract class BehaviorNode
{
    public enum NodeState { Running, Success, Failure }
    public abstract NodeState Evaluate();
}

// Sequence: 모든 자식이 성공해야 성공
public class SequenceNode : BehaviorNode
{
    private List<BehaviorNode> _children;

    public SequenceNode(List<BehaviorNode> children)
    {
        _children = children;
    }

    public override NodeState Evaluate()
    {
        foreach (var child in _children)
        {
            var result = child.Evaluate();
            if (result == NodeState.Failure) return NodeState.Failure;
            if (result == NodeState.Running) return NodeState.Running;
        }
        return NodeState.Success;
    }
}

// Selector: 하나라도 성공하면 성공
public class SelectorNode : BehaviorNode
{
    private List<BehaviorNode> _children;

    public SelectorNode(List<BehaviorNode> children)
    {
        _children = children;
    }

    public override NodeState Evaluate()
    {
        foreach (var child in _children)
        {
            var result = child.Evaluate();
            if (result == NodeState.Success) return NodeState.Success;
            if (result == NodeState.Running) return NodeState.Running;
        }
        return NodeState.Failure;
    }
}
```

```csharp
// Condition 노드 예시: 플레이어가 공격 범위 안에 있는지
public class IsPlayerInAttackRange : BehaviorNode
{
    private Transform _enemy;
    private Transform _player;
    private float _range;

    public IsPlayerInAttackRange(Transform enemy, Transform player, float range)
    {
        _enemy = enemy;
        _player = player;
        _range = range;
    }

    public override NodeState Evaluate()
    {
        float dist = Vector2.Distance(_enemy.position, _player.position);
        return dist <= _range ? NodeState.Success : NodeState.Failure;
    }
}

// Action 노드 예시: 플레이어 방향으로 이동
public class MoveTowardPlayer : BehaviorNode
{
    private Rigidbody2D _rb;
    private Transform _player;
    private float _speed;

    public MoveTowardPlayer(Rigidbody2D rb, Transform player, float speed)
    {
        _rb = rb;
        _player = player;
        _speed = speed;
    }

    public override NodeState Evaluate()
    {
        Vector2 dir = ((Vector2)_player.position - _rb.position).normalized;
        _rb.linearVelocity = dir * _speed;
        return NodeState.Running;
    }
}
```

```csharp
// 적 AI 컨트롤러에서 트리 조립
public class EliteEnemyAI : MonoBehaviour
{
    private BehaviorNode _rootNode;

    [SerializeField] private Transform playerTransform;
    [SerializeField] private float attackRange = 2f;
    [SerializeField] private float chaseRange = 8f;
    [SerializeField] private float moveSpeed = 3f;

    private void Awake()
    {
        // 유니티 에디터에서 playerTransform 드래그 앤 드롭 설정 필요
        BuildTree();
    }

    private void BuildTree()
    {
        // 트리 구조:
        // Selector
        //   ├─ Sequence (공격 조건)
        //   │    ├─ IsPlayerInAttackRange
        //   │    └─ PerformAttack
        //   ├─ Sequence (추적 조건)
        //   │    ├─ IsPlayerInChaseRange
        //   │    └─ MoveTowardPlayer
        //   └─ Idle

        _rootNode = new SelectorNode(new List<BehaviorNode>
        {
            new SequenceNode(new List<BehaviorNode>
            {
                new IsPlayerInAttackRange(transform, playerTransform, attackRange),
                new PerformMeleeAttack(GetComponent<Animator>(), GetComponent<EnemyAttack>())
            }),
            new SequenceNode(new List<BehaviorNode>
            {
                new IsPlayerInRange(transform, playerTransform, chaseRange),
                new MoveTowardPlayer(GetComponent<Rigidbody2D>(), playerTransform, moveSpeed)
            }),
            new IdleAction(GetComponent<Rigidbody2D>())
        });
    }

    private void Update()
    {
        _rootNode?.Evaluate();
    }
}
```

### Cooldown Decorator 구현 (공격 쿨다운에 필수)

```csharp
public class CooldownDecorator : BehaviorNode
{
    private BehaviorNode _child;
    private float _cooldownTime;
    private float _lastExecuteTime = -999f;

    public CooldownDecorator(BehaviorNode child, float cooldown)
    {
        _child = child;
        _cooldownTime = cooldown;
    }

    public override NodeState Evaluate()
    {
        if (Time.time - _lastExecuteTime < _cooldownTime)
            return NodeState.Failure;

        var result = _child.Evaluate();
        if (result == NodeState.Success)
            _lastExecuteTime = Time.time;

        return result;
    }
}
```

### 기존 패키지 활용 (권장)

Unity Package Manager에서 사용 가능한 옵션:
- **Unity Behavior** (공식, 2023.3+): `com.unity.behavior` — 비주얼 에디터 제공
- **NodeCanvas** (유료): 강력한 비주얼 트리 에디터
- 초보자에게는 **직접 구현(위 코드)**이 학습 목적에 더 적합

---

## OnionCat 적용 포인트

### 잡몹 vs 엘리트/보스 분류

| 적 타입 | 권장 AI 방식 | 이유 |
|---|---|---|
| 기본 잡몹 (2~3개 행동) | State Machine | 단순, 유지보수 쉬움 |
| 엘리트 (4~6개 조건 분기) | Behavior Tree | 조건 복잡도 증가 |
| 보스 (페이즈 전환 + 패턴) | State Machine + Behavior Tree 혼용 | 페이즈 = SM, 각 페이즈 내 패턴 = BT |

### OnionCat 엘리트 적 예시 트리

```
Selector
├─ Sequence (위기 탈출 — HP 30% 이하)
│    ├─ IsLowHealth
│    └─ Selector
│         ├─ Sequence (Cat이 근거리이면 도망)
│         │    ├─ IsCatInMeleeRange
│         │    └─ FleeFromCat
│         └─ Sequence (Onion이 원거리이면 돌진)
│              ├─ IsOnionAiming
│              └─ ChargeTowardOnion
├─ Sequence (근접 공격 — Cat 감지)
│    ├─ IsCatInRange(3f)
│    ├─ CooldownDecorator(1.5f)
│    └─ MeleeAttack
└─ MoveTowardNearestPlayer
```

### 핵심 포인트
- **Cat/Onion을 별개 타겟으로 관리**: 적이 현재 누구를 노리는지 `BlackBoard`(공유 데이터 딕셔너리)에 저장
- **약점 기반 행동 분기**: Cat 전용 적은 Onion 투사체 감지 시 방어 자세 전환 노드 추가
- **Cooldown Decorator 필수**: 모든 공격 Action 노드 위에 CooldownDecorator 감싸기

---

## 참고 링크

- Unity 공식 Behavior 패키지: https://docs.unity3d.com/Packages/com.unity.behavior@1.0/manual/index.html
- Behavior Tree 개념 설명: https://www.gamedeveloper.com/design/behavior-trees-for-ai-how-they-work
- 튜토리얼 (커스텀 구현): https://www.youtube.com/watch?v=G4TBCuJRE4A
- Behavior Tree 패턴 참고: https://behaviortree.dev/
- Unity Learn — AI Pathfinding: https://learn.unity.com/tutorial/ai-and-pathfinding
