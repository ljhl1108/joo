# Utility AI for Enemy Decision Making

리서치 날짜: 2026-11-11

## 개요

Utility AI는 적이 "다음에 뭘 할 것인지"를 **점수 기반으로 선택**하는 AI 아키텍처다.
상태머신(StateMachine)이 "지금 상태가 뭔가"를 판단한다면, Utility AI는
"지금 가능한 행동 중 어떤 게 가장 가치 있는가"를 계속 평가한다.

OnionCat과의 관련성:
- 적이 "고양이 추격 → 근접 공격 → 후퇴 → 범위 공격" 사이에서 단순한 조건 분기가 아니라
  거리·체력·아군 수·플레이어 패턴을 종합해 더 자연스럽게 행동
- 같은 적 타입도 상황에 따라 다른 행동을 보여 반복 전투 지루함 감소

---

## Utility AI 기본 개념

### 상태머신 vs Utility AI

| 항목 | 상태머신 | Utility AI |
|------|---------|-----------|
| 결정 방식 | 조건이 맞으면 상태 전환 | 모든 행동에 점수 → 최고점 선택 |
| 코드 구조 | if/else 분기 많음 | 행동별 점수 함수 |
| 확장성 | 상태 추가 시 전환 조건 복잡해짐 | 행동 추가 시 점수 함수만 추가 |
| 자연스러움 | 뚝뚝 끊길 수 있음 | 상황에 유연하게 반응 |
| 복잡도 | 낮음 | 중간 |

### 점수 계산 예시 (근접 공격 행동)
```
AttackScore = 
    DistanceScore(distanceToPlayer)   // 가까울수록 높음
  * HealthScore(myHealth)             // 체력 많을수록 높음
  * CooldownScore(attackCooldown)     // 쿨다운 끝났을 때만 높음
  * ThreatScore(playerInRange)        // 플레이어가 공격 범위 내에 있으면 높음
```

각 함수는 0~1 반환. 곱셈으로 하나라도 0이면 행동 선택 안 됨.

---

## Unity 구현 방법

### 1. 행동 클래스 정의

```csharp
public abstract class EnemyAction
{
    public abstract float ScoreFor(EnemyAIContext ctx);
    public abstract IEnumerator Execute(EnemyBase enemy);
}

public class EnemyAIContext
{
    public float DistanceToPlayer;
    public float MyHealthRatio;        // 0~1
    public bool  AttackCooldownReady;
    public int   NearbyAlliesCount;
    public bool  PlayerIsAttacking;
}
```

### 2. 점수 함수 (응답 곡선)

```csharp
// 선형, 역선형, S곡선 등으로 가중치 조절
public static class ScoreCurve
{
    public static float Linear(float value, float min, float max)
        => Mathf.InverseLerp(min, max, value);

    public static float InverseLinear(float value, float min, float max)
        => 1f - Linear(value, min, max);

    // 가까울수록 1에 가까운 공격 거리 점수
    public static float AttackDistanceScore(float dist, float maxRange)
        => dist <= maxRange ? InverseLinear(dist, 0, maxRange) : 0f;
}
```

### 3. 행동 구현 예시 — 근접 공격

```csharp
public class MeleeAttackAction : EnemyAction
{
    [SerializeField] private float attackRange = 1.5f;

    public override float ScoreFor(EnemyAIContext ctx)
    {
        if (!ctx.AttackCooldownReady) return 0f;

        float distScore    = ScoreCurve.AttackDistanceScore(ctx.DistanceToPlayer, attackRange);
        float healthScore  = ctx.MyHealthRatio;         // 체력 없으면 소극적
        float allyBonus    = ctx.NearbyAlliesCount > 1 ? 1.2f : 1f;  // 아군 있으면 대담

        return distScore * healthScore * allyBonus;
    }

    public override IEnumerator Execute(EnemyBase enemy)
    {
        enemy.PlayAnimation("attack");
        yield return new WaitForSeconds(enemy.telegraphDuration);
        enemy.PerformMeleeHit();
        yield return new WaitForSeconds(enemy.attackCooldown);
    }
}
```

### 4. 행동 후퇴 (도망)

```csharp
public class RetreatAction : EnemyAction
{
    public override float ScoreFor(EnemyAIContext ctx)
    {
        // 체력 20% 미만이고 플레이어가 공격 중일 때 후퇴 점수 높아짐
        float lowHealthScore   = ScoreCurve.InverseLinear(ctx.MyHealthRatio, 0f, 0.3f);
        float playerThreaten   = ctx.PlayerIsAttacking ? 1.5f : 0.5f;
        return lowHealthScore * playerThreaten;
    }

    public override IEnumerator Execute(EnemyBase enemy)
    {
        enemy.MoveAwayFromPlayer(duration: 1.5f);
        yield return new WaitForSeconds(1.5f);
    }
}
```

### 5. AI 실행 루프

```csharp
public class UtilityAIController : MonoBehaviour
{
    [SerializeField] private List<EnemyAction> actions;
    private EnemyBase enemy;
    private bool running;

    private void Start()
    {
        enemy = GetComponent<EnemyBase>();
        StartCoroutine(AILoop());
    }

    private IEnumerator AILoop()
    {
        while (true)
        {
            if (!running)
            {
                var ctx    = BuildContext();
                var best   = PickBestAction(ctx);
                if (best != null)
                {
                    running = true;
                    yield return StartCoroutine(best.Execute(enemy));
                    running = false;
                }
            }
            yield return new WaitForSeconds(0.1f);  // 평가 주기
        }
    }

    private EnemyAction PickBestAction(EnemyAIContext ctx)
    {
        EnemyAction best = null;
        float bestScore  = 0.1f;  // 임계값 미만은 무행동

        foreach (var action in actions)
        {
            float score = action.ScoreFor(ctx);
            if (score > bestScore) { bestScore = score; best = action; }
        }
        return best;
    }

    private EnemyAIContext BuildContext() => new EnemyAIContext
    {
        DistanceToPlayer    = Vector2.Distance(transform.position, PlayerRef.Position),
        MyHealthRatio       = enemy.Health / (float)enemy.MaxHealth,
        AttackCooldownReady = enemy.IsAttackReady,
        NearbyAlliesCount   = EnemyBase.Active.Count(e => e != enemy &&
                                Vector2.Distance(e.transform.position, transform.position) < 5f),
        PlayerIsAttacking   = PlayerRef.IsAttacking,
    };
}
```

---

## OnionCat 적용 포인트

### 1. 조합형 적(ModularEnemy)과 호환
OnionCat의 적은 `EnemyBase` 위에 행동 모듈이 붙는 조합형 구조.
Utility AI 행동을 ScriptableObject로 만들면 에디터에서 조합 가능:
```
EnemyBuilder.cs 행동 목록:
  "melee_basic"   → MeleeAttackAction SO
  "retreat_low_hp"→ RetreatAction SO
  "charge"        → ChargeAttackAction SO
```
→ `EnemyBuilder` 표에서 행동 조합을 쉽게 바꿀 수 있음

### 2. 현재 상태머신과 혼용
전면 교체 없이 **현재 StateMachine의 큰 상태(순찰/전투/도망) 안에서** 소행동을 Utility AI로 결정:
- 상태: 전투 상태(기존 StateMachine)
- 소행동 선택: 근접 공격 / 범위 공격 / 잠깐 후퇴 / 소환 (Utility AI)

### 3. 엘리트·보스 적에게 우선 적용
기본 슬라임은 단순 추적으로 충분. 엘리트나 보스는 Utility AI로:
- 체력 낮을 때 행동이 바뀌는 보스 (공격적으로 or 도망)
- 아군이 죽으면 더 대담해지는 엘리트
- 플레이어가 패링할 것 같으면 다른 행동 선택

### 4. 2인 플레이어 대응
OnionCat은 고양이와 작물 두 타깃이 있음. Context에 추가:
```csharp
public float DistanceToCat;
public float DistanceToOnion;
public bool  OnionIsShielding;
public bool  CatIsDashing;
```
→ "고양이가 대쉬 중이면 무적 → 작물 먼저 공격" 같은 전술적 선택 가능

### 5. 구현 우선순위
1. 기존 보스(ShadowWitch)에 먼저 적용해 테스트
2. 체력 단계 전환에 Utility 점수를 연결
3. 양호하면 엘리트 적 2~3종에 확장

---

## 참고 링크

- Utility AI 개요 (Dave Mark, GDC): https://www.gdcvault.com/play/1012410
- Unity 구현 튜토리얼: https://www.youtube.com/watch?v=p3Jbp8r9P3g (검색: "Unity Utility AI tutorial")
- Infinite Axis Utility System: https://github.com/iDVB/IAUS (오픈소스)
- 블로그: https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter09_An_Introduction_to_Utility_Theory.pdf
- Unity Forum: https://discussions.unity.com/t/utility-based-ai-implementation
