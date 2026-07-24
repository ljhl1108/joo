# Ability System Architecture

리서치 날짜: 2026-07-24

## 개요

모듈형 능력(스킬/업그레이드) 시스템을 어떻게 설계하면 OnionCat처럼 "교체 가능한 능력"을 유지보수하기 쉽게 만들 수 있는가. 핵심은 **ScriptableObject 기반 데이터 + 추상 기반 클래스 상속** 조합이다. 이 구조가 없으면 능력이 늘어날수록 코드가 스파게티가 된다.

---

## Unity 구현 방법

### 1. 추상 기반 클래스 (AbilityBase)

```csharp
// 모든 능력의 공통 인터페이스
public abstract class AbilityBase : ScriptableObject
{
    [SerializeField] private string abilityName;
    [SerializeField] private Sprite icon;
    [SerializeField] private string description;

    // 능력 발동 (구현은 각 서브클래스에서)
    public abstract void Activate(AbilityContext ctx);

    // 능력이 적용 가능한지 조건 체크 (선택적 오버라이드)
    public virtual bool CanActivate(AbilityContext ctx) => true;

    // 능력 해제/정리 (지속형 능력용)
    public virtual void Deactivate(AbilityContext ctx) { }
}

// 능력 실행 시 필요한 컨텍스트 (실행 주체, 타깃 등)
public class AbilityContext
{
    public GameObject Owner;       // 능력 소유자
    public GameObject Target;      // 타깃 (없으면 null)
    public Vector2 AimDirection;   // 에임 방향
    public PlayerStats Stats;      // 현재 스탯 참조
}
```

### 2. 구체 능력 구현 예시

```csharp
// 근접 공격 강화 능력
[CreateAssetMenu(menuName = "Abilities/MeleeBoost")]
public class MeleeBoostAbility : AbilityBase
{
    [SerializeField] private float damageMultiplier = 1.5f;
    [SerializeField] private float duration = 3f;

    public override void Activate(AbilityContext ctx)
    {
        ctx.Stats.StartCoroutine(ApplyBoost(ctx.Stats));
    }

    private IEnumerator ApplyBoost(PlayerStats stats)
    {
        stats.MeleeDamageMultiplier *= damageMultiplier;
        yield return new WaitForSeconds(duration);
        stats.MeleeDamageMultiplier /= damageMultiplier;
    }
}

// 패리 시 폭발 능력
[CreateAssetMenu(menuName = "Abilities/ParryExplosion")]
public class ParryExplosionAbility : AbilityBase
{
    [SerializeField] private float explosionRadius = 2f;
    [SerializeField] private int damage = 20;
    [SerializeField] private GameObject explosionVFX;

    public override void Activate(AbilityContext ctx)
    {
        Collider2D[] hits = Physics2D.OverlapCircleAll(
            ctx.Owner.transform.position, explosionRadius, LayerMask.GetMask("Enemy"));

        foreach (var hit in hits)
        {
            hit.GetComponent<EnemyHealth>()?.TakeDamage(damage);
        }
        Instantiate(explosionVFX, ctx.Owner.transform.position, Quaternion.identity);
    }
}
```

### 3. 능력 소유자 컴포넌트 (AbilityHolder)

```csharp
public class AbilityHolder : MonoBehaviour
{
    [SerializeField] private List<AbilityBase> equippedAbilities = new();
    private AbilityContext _context;

    private void Awake()
    {
        _context = new AbilityContext
        {
            Owner = gameObject,
            Stats = GetComponent<PlayerStats>()
        };
    }

    // 특정 트리거로 모든 능력 발동 (예: OnParry 이벤트)
    public void ActivateAll(Vector2 aimDir, GameObject target = null)
    {
        _context.AimDirection = aimDir;
        _context.Target = target;

        foreach (var ability in equippedAbilities)
        {
            if (ability.CanActivate(_context))
                ability.Activate(_context);
        }
    }

    // 런 중 능력 추가 (업그레이드 픽업 시)
    public void AddAbility(AbilityBase ability)
    {
        equippedAbilities.Add(ability);
    }

    // 런 종료 시 초기화
    public void ClearAbilities()
    {
        equippedAbilities.Clear();
    }
}
```

### 4. 이벤트 트리거 연동

```csharp
// Player 2 컴포넌트 — 패리 성공 시 능력 발동
public class CropPlayer : MonoBehaviour
{
    [SerializeField] private AbilityHolder abilityHolder;

    private void OnParrySuccess(Vector2 deflectDir)
    {
        // 패리 관련 능력 모두 발동
        abilityHolder.ActivateAll(deflectDir);
    }
}
```

### 5. 업그레이드 선택 화면 연동

```csharp
// 업그레이드 선택 UI에서 호출
public class UpgradeCard : MonoBehaviour
{
    [SerializeField] private AbilityBase ability;

    public void OnPlayerSelect(AbilityHolder holder)
    {
        holder.AddAbility(ability);
        // 선택 애니메이션, 씬 재개 등
    }
}
```

---

## OnionCat 적용 포인트

### 능력 카테고리 분류

| 카테고리 | 소유자 | 예시 능력 |
|---------|--------|---------|
| Cat 전용 | Player 1 AbilityHolder | 슬래시 강화, 대시 데미지, 연속 콤보 |
| Crop 전용 | Player 2 AbilityHolder | 투사체 분열, 패리 폭발, 실드 반격 |
| 공유(몸) | 공통 AbilityHolder | 이동 속도 UP, 체력 회복, 무적 시간 연장 |

### 패리 폭발 체인 예시
```
Player 2 패리 성공
  → CropPlayer.OnParrySuccess() 호출
    → AbilityHolder.ActivateAll() 
      → ParryExplosionAbility.Activate() → 주변 폭발
      → ParryChainAbility.Activate()    → 다음 투사체 2배 속도
```

### ScriptableObject 관리 팁
- `Assets/Data/Abilities/Cat/` 와 `Assets/Data/Abilities/Crop/` 폴더 분리
- 업그레이드 선택지 풀: `AbilityPool.asset` (List<AbilityBase>) ScriptableObject로 관리
- 런마다 풀에서 랜덤 N개 뽑아 선택지 표시

---

## 참고 링크

- Unity ScriptableObject 공식 문서: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- GDC: ScriptableObject 활용법 (Ryan Hipple): https://www.youtube.com/watch?v=raQ3iHhE_Kk
- Unity 공식 아키텍처 가이드: https://unity.com/how-to/architect-game-code-scriptable-objects
- Ability System 설계 패턴 (Game Programming Patterns): https://gameprogrammingpatterns.com/command.html
- Unite Austin 2017 — Game Architecture with SO: https://unity.com/resources/scripting-best-practices-ebook
