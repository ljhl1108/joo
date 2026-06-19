# 상태이상 시스템 (Status Effect System)

리서치 날짜: 2026-06-19

## 개요

상태이상(버프/디버프)은 플레이어나 적에게 일시적으로 적용되는 특수 효과 시스템이다.  
OnionCat에서는 적에게 화상/빙결/감속을 가하거나, 아이템으로 플레이어를 강화하는 모든 효과가 여기에 해당한다.  
잘 설계된 상태이상 시스템은 전투 다양성을 폭발적으로 늘려주며, 로그라이크 업그레이드와 시너지를 만든다.

---

## 핵심 설계 결정

### 지속시간(Duration) 방식 vs 스택(Stack) 방식

| 방식 | 설명 | 예시 |
|------|------|------|
| **Duration** | 지속시간 동안 효과 유지, 재적용 시 리셋 or 연장 | 감속 3초 |
| **Stack** | 중첩될수록 효과 강화 | 독 x3 = 3배 데미지/초 |
| **혼합** | 일부는 스택, 일부는 지속시간 | 로그라이크에서 일반적 |

OnionCat 추천: **Duration 기반 + 최대 스택 제한** (단순하고 직관적)

---

## Unity 구현 방법

### 1. ScriptableObject로 상태이상 정의

```csharp
[CreateAssetMenu(menuName = "OnionCat/StatusEffect")]
public class StatusEffectData : ScriptableObject
{
    public string effectName;
    public float duration;
    public float tickInterval;   // 0 = 즉발형 (틱 없음)
    public float tickDamage;     // 초당 데미지 (독, 화상)
    public float slowMultiplier; // 1.0 = 효과 없음, 0.5 = 50% 감속
    public bool canStack;
    public int maxStacks;
    public GameObject vfxPrefab; // 상태이상 표시 파티클
    public Color tintColor;      // 캐릭터 색상 변화
}
```

### 2. 상태이상 인스턴스 클래스

```csharp
public class StatusEffectInstance
{
    public StatusEffectData data;
    public float remainingTime;
    public int stackCount;
    private float tickTimer;

    public StatusEffectInstance(StatusEffectData data)
    {
        this.data = data;
        remainingTime = data.duration;
        stackCount = 1;
        tickTimer = 0f;
    }

    // 반환값: 이번 프레임에 입힐 데미지
    public float Update(float deltaTime)
    {
        remainingTime -= deltaTime;
        float damage = 0f;

        if (data.tickInterval > 0)
        {
            tickTimer += deltaTime;
            if (tickTimer >= data.tickInterval)
            {
                tickTimer -= data.tickInterval;
                damage = data.tickDamage * stackCount;
            }
        }
        return damage;
    }

    public bool IsExpired => remainingTime <= 0f;

    public void Refresh() => remainingTime = data.duration;

    public bool TryAddStack()
    {
        if (!data.canStack || stackCount >= data.maxStacks) return false;
        stackCount++;
        return true;
    }
}
```

### 3. StatusEffectHandler — 대상 오브젝트에 붙이는 컴포넌트

```csharp
public class StatusEffectHandler : MonoBehaviour
{
    private List<StatusEffectInstance> activeEffects = new();
    private HealthSystem healthSystem;
    private SpriteRenderer spriteRenderer;

    [SerializeField] private Transform vfxParent;

    private void Awake()
    {
        healthSystem = GetComponent<HealthSystem>();
        spriteRenderer = GetComponent<SpriteRenderer>();
    }

    public void ApplyEffect(StatusEffectData data)
    {
        // 기존 동일 효과 탐색
        var existing = activeEffects.Find(e => e.data == data);
        if (existing != null)
        {
            existing.Refresh();
            if (!existing.TryAddStack())
                return; // 최대 스택 도달
        }
        else
        {
            activeEffects.Add(new StatusEffectInstance(data));
            if (data.vfxPrefab != null)
                Instantiate(data.vfxPrefab, vfxParent);
        }
        UpdateVisuals();
    }

    private void Update()
    {
        for (int i = activeEffects.Count - 1; i >= 0; i--)
        {
            float dmg = activeEffects[i].Update(Time.deltaTime);
            if (dmg > 0f)
                healthSystem.TakeDamage(dmg);

            if (activeEffects[i].IsExpired)
            {
                activeEffects.RemoveAt(i);
                UpdateVisuals();
            }
        }
    }

    public float GetSpeedMultiplier()
    {
        float multiplier = 1f;
        foreach (var effect in activeEffects)
            multiplier *= effect.data.slowMultiplier;
        return multiplier;
    }

    public bool HasEffect(StatusEffectData data) =>
        activeEffects.Exists(e => e.data == data);

    private void UpdateVisuals()
    {
        if (activeEffects.Count == 0)
        {
            spriteRenderer.color = Color.white;
            return;
        }
        // 마지막에 적용된 효과 색상 표시
        spriteRenderer.color = activeEffects[^1].data.tintColor;
    }
}
```

### 4. 이동 속도에 상태이상 반영

```csharp
// EnemyMovement.cs 또는 PlayerMovement.cs 내부
private StatusEffectHandler statusHandler;

private void Awake()
{
    statusHandler = GetComponent<StatusEffectHandler>();
}

private void Move()
{
    float speedMult = statusHandler != null ? statusHandler.GetSpeedMultiplier() : 1f;
    rb.linearVelocity = direction * moveSpeed * speedMult;
}
```

### 5. 투사체에서 상태이상 적용

```csharp
// OnionProjectile.cs
[SerializeField] private StatusEffectData onHitEffect; // Inspector에서 드래그

private void OnTriggerEnter2D(Collider2D other)
{
    if (other.TryGetComponent<StatusEffectHandler>(out var handler))
    {
        if (onHitEffect != null)
            handler.ApplyEffect(onHitEffect);
    }
}
```

---

## 자주 쓰이는 상태이상 목록

| 이름 | 효과 | 구현 방식 |
|------|------|-----------|
| **화상 (Burn)** | 초당 데미지, 빨간 틴트 | tickDamage > 0 |
| **독 (Poison)** | 느린 지속 데미지, 초록 | tickDamage, 스택 가능 |
| **감속 (Slow)** | 이동속도 감소 | slowMultiplier < 1 |
| **빙결 (Freeze)** | 이동/공격 완전 정지 | slowMultiplier = 0 |
| **기절 (Stun)** | 행동 불능 | 별도 isStunned 플래그 |
| **강화 (Buff)** | 공격력/방어력 증가 | damageMultiplier 필드 추가 |
| **무적 (Invincible)** | 피격 무시 | HealthSystem에서 체크 |

---

## OnionCat 적용 포인트

### 1. P2(양파) 투사체 → 상태이상 부여
- 기본 투사체: 피해만 입힘
- 업그레이드 후: 투사체에 화상/감속 효과 추가
- 런마다 다른 상태이상 투사체 → 전략 다양화

### 2. 근접/원거리 취약 + 상태이상 연계
- 원거리만 약점인 적에게 감속 → P1(고양이)가 쫓기 용이
- 근접만 약점인 적에게 빙결 → P1이 안전하게 접근

### 3. 파리(Parry) 상태이상 반사
- P2가 파리 성공 시 → 적에게 투사체의 상태이상을 반사로 적용
- "적 투사체를 받아쳐 독 효과 반사" → 협동 시너지

### 4. 보스 상태이상 단계 트리거
- 보스 체력 50% 이하 + 화상 상태 → 2페이즈 돌입
- 상태이상이 단순 데미지 외에 AI 변화와 연동

### 5. 에셋 구성
```
StatusEffects/
  Burn.asset
  Poison.asset
  Slow.asset
  Freeze.asset
VFX/StatusEffects/
  BurnVFX.prefab
  PoisonVFX.prefab
  SlowVFX.prefab
```

---

## 주의사항

- `activeEffects` 순회 중 삭제는 **역방향 for문** 필수 (인덱스 오류 방지)
- 감속이 0이 될 경우 Rigidbody2D가 완전 정지하는지 별도 검증 필요
- `[SerializeField] private StatusEffectData onHitEffect` → **유니티 에디터에서 드래그 앤 드롭 설정 필요**
- `[SerializeField] private Transform vfxParent` → **유니티 에디터에서 자식 Transform 연결 필요**

---

## 참고 링크

- [Unity ScriptableObjects](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
- [Unity Time.deltaTime](https://docs.unity3d.com/ScriptReference/Time-deltaTime.html)
- [Status Effect Pattern in Game Dev (Game Programming Patterns)](https://gameprogrammingpatterns.com/type-object.html)
- [Unity 2D SpriteRenderer Color](https://docs.unity3d.com/ScriptReference/SpriteRenderer-color.html)
