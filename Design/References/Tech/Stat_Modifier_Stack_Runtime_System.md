# Stat Modifier Stack Runtime System

리서치 날짜: 2026-11-10

## 개요

스탯 수정 스택(Stat Modifier Stack)은 여러 출처(장비·버프·세트 보너스·상태이상)의 수치 변경이 올바르게 합산·곱산되도록 관리하는 런타임 시스템이다. OnionCat처럼 장비 163종 + 세트 보너스 + 상태이상이 동시에 적용되는 게임에서 "어디서 왔는지 모르는 수치 오차"를 막는 핵심 인프라.

**필요한 이유:**
- `PlayerStats.Current.AttackPower = BaseAttack + 장비A + 장비B + 세트보너스 × 버프배율` 형태의 수식이 늘어날수록 직접 계산이 불가능해진다.
- 장비 교체·장착 해제 시 이전 값이 남아 있는 "스탯 오염" 버그가 가장 흔한 문제.
- 멀티플라이어가 겹칠 때 가산(additive)인지 승산(multiplicative)인지 모호해지면 밸런스 계산이 틀린다.

## Unity 구현 방법

### 1. 수정자(Modifier) 타입 정의

```csharp
public enum ModifierOp
{
    FlatAdd,        // 덧셈: base + flat
    FlatMul,        // 최종 배율: result * (1 + mul의 합)
    Override        // 완전 덮어쓰기 (희귀하게만)
}

[System.Serializable]
public struct StatModifier
{
    public StatType stat;
    public ModifierOp op;
    public float value;
    public object source; // 출처 (장비 인스턴스, 버프 등)
}
```

### 2. 스탯 계산 순서 (표준 패턴)

```
최종값 = (BaseValue + Σ FlatAdd) × (1 + Σ FlatMul)
```

이 순서를 고정하면 어떤 장비 조합도 예측 가능한 결과가 나온다.

```csharp
public float Compute(StatType stat, float baseValue, List<StatModifier> modifiers)
{
    float flat = 0f;
    float mul  = 0f;
    
    foreach (var m in modifiers)
    {
        if (m.stat != stat) continue;
        if (m.op == ModifierOp.FlatAdd) flat += m.value;
        if (m.op == ModifierOp.FlatMul) mul  += m.value;
    }
    
    return (baseValue + flat) * (1f + mul);
}
```

### 3. PlayerStats — 출처별 수정자 목록 관리

```csharp
public class PlayerStats : MonoBehaviour
{
    private readonly List<StatModifier> _mods = new();

    // 장비 장착 시
    public void AddModifiers(IEnumerable<StatModifier> mods, object source)
    {
        foreach (var m in mods)
            _mods.Add(m with { source = source });
        _dirty = true;
    }

    // 장비 해제 시 — source 기준으로 전부 제거
    public void RemoveModifiers(object source)
    {
        _mods.RemoveAll(m => m.source == source);
        _dirty = true;
    }

    // 최종값 조회 (캐시)
    private bool _dirty = true;
    private ComputedStats _cache;

    public ComputedStats Current
    {
        get
        {
            if (_dirty) { _cache = Recompute(); _dirty = false; }
            return _cache;
        }
    }
}
```

### 4. OnionCat 적용 — RunData.RecomputeGear 연동

OnionCat의 `RunData.RecomputeGear`가 장비에서 Modifier를 읽는 현행 흐름:

```csharp
// GearItem ScriptableObject에서
public IEnumerable<StatModifier> GetModifiers() { /* ... */ }

// RecomputeGear 호출 시 PlayerStats에 반영
void RecomputeGear()
{
    catStats.RemoveModifiers(GearSource.Gear);
    foreach (var item in equippedGear)
        catStats.AddModifiers(item.GetModifiers(), GearSource.Gear);
}
```

이렇게 하면 장비 교체 시 이전 수정자가 완전히 제거된 뒤 새 수정자가 추가됨.

### 5. 세트 보너스 연동

세트 보너스는 별도 source(`GearSource.SetBonus`)로 관리:

```csharp
void RecalculateSetBonuses()
{
    catStats.RemoveModifiers(GearSource.SetBonus);
    foreach (var bonus in PassiveHost.ActiveBonuses)
        catStats.AddModifiers(bonus.GetModifiers(), GearSource.SetBonus);
}
```

### 6. 임시 버프/상태이상

전투 중 발생하는 임시 수정자도 같은 시스템 사용:

```csharp
// 햇빛 기둥: 10초 동안 공격력 +20%
StartCoroutine(TempBuff(StatType.AttackPower, ModifierOp.FlatMul, 0.2f, 10f, BuffSource.SunPillar));

IEnumerator TempBuff(StatType t, ModifierOp op, float v, float dur, object src)
{
    catStats.AddModifiers(new[] { new StatModifier { stat=t, op=op, value=v } }, src);
    yield return new WaitForSeconds(dur);
    catStats.RemoveModifiers(src);
}
```

### 7. 디버그 — 수정자 목록 출력

```csharp
// 에디터 메뉴 또는 Debug 모드에서
void PrintAllModifiers(StatType stat)
{
    foreach (var m in _mods.Where(m => m.stat == stat))
        Debug.Log($"[{m.source}] {m.op} {m.value:+0.##;-0.##}");
}
```

밸런스 작업 중 "이 스탯이 왜 이 값인지" 추적 가능.

## OnionCat 적용 포인트

### 현행 구조와의 통합

OnionCat의 `PlayerStats.Current`가 이미 장비 수치를 합산하는 역할. 이 패턴을 적용하면:

1. **새 스탯 추가**: `StatType` enum에 항목 추가 + `GearItem`에서 모디파이어 반환 → 사용처에서 `Current.Get(StatType.X)` 호출. 계산 로직은 중앙에서 자동 처리.

2. **장비 교체 버그 제로**: `source` 기반 제거로 이전 장비 값이 남지 않음.

3. **세트 보너스 디버그**: `OnionCat > Debug > Show Stat Modifiers`로 현재 수정자 전부 출력 — 밸런스 조정 시 "어디서 왔는지" 즉시 파악.

4. **작물과 고양이 별개 관리**: `catStats`, `cropStats` 두 인스턴스로 나눠 관리. 세트 보너스는 양쪽 장비를 합산해서 판단(`PassiveHost.Recalculate`)하되 적용은 각자 `PlayerStats`에.

### 주의사항

- `ComputedStats` 캐시는 `_dirty` 플래그로만 무효화 — 매 프레임 재계산 금지
- `source`는 ScriptableObject 레퍼런스나 enum 사용 (string 비교 금지 — GC)
- Override 타입 수정자가 여럿이면 최후 적용이 이기는 규칙 사전 정의 필요

## 참고 링크

- [Unity Blog: ScriptableObject 기반 아이템 시스템](https://unity.com/how-to/architect-game-code-scriptable-objects)
- [Game Programming Patterns: Command/Strategy](https://gameprogrammingpatterns.com/)
- [Roguelike Dev — Stat Modifier Pattern (Reddit)](https://www.reddit.com/r/roguelikedev/comments/stat_modifier_pattern/)
- [Unite 2016 — 모디파이어 스탯 패턴 발표](https://www.youtube.com/watch?v=raQ3iHhE_Kk)
