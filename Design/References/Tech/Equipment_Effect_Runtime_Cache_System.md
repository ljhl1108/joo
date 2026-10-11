# 장비 효과 런타임 캐싱 및 수정자 파이프라인

리서치 날짜: 2026-10-11

## 개요

장비 아이템이 캐릭터 능력치에 영향을 주는 구조를 설계할 때, **"장비 데이터(ScriptableObject) → 런타임 수정자 스택 → 캐시된 최종 스탯"**으로 이어지는 파이프라인을 잘 만들어 두면 수십 개의 효과가 붙어도 매 프레임 재계산 없이 올바른 값을 유지할 수 있다.

OnionCat은 현재 `RunData.RecomputeGear()`가 장비에서 스탯을 다시 계산하고 `PlayerStats.Current`에 반영하는 구조를 갖추고 있다. 이 파이프라인을 체계적으로 정리해두면 새 장비·효과 추가가 단순해진다.

---

## 핵심 개념

### 1. 스탯 수정자의 세 종류
모든 장비/패시브 효과는 아래 세 종류 중 하나다:

| 종류 | 수식 | 예 |
|---|---|---|
| **Flat** (덧셈) | base + flat | 최대 HP +20 |
| **Additive %** (퍼센트 합산) | base × (1 + Σadditive) | 공격력 +15%, +10% → ×1.25 |
| **Multiplicative** (곱셈) | 이전 결과 × multi | 전설 효과: 전체 ×1.5 |

연산 순서: `finalStat = (base + flatSum) × (1 + additiveSum) × multiplicativeProduct`

Path of Exile·Diablo 계열이 쓰는 표준 순서. 이 순서를 코드 한 곳에 고정해두면 기획자가 숫자를 조정하기 쉬워진다.

### 2. 재계산 트리거 시점

매 프레임 계산하면 비용이 크고, 너무 드물면 버그가 생긴다.  
재계산이 필요한 **이벤트**만 트리거로 쓴다:

```
장비 장착/해제
장비 레벨업
방 진입/클리어 (버프 초기화)
세트 카운트 변경
특정 런타임 효과 발동 ("이번 방 동안 공격력 +50%")
```

### 3. 더티 플래그 패턴 (Dirty Flag)

```csharp
public class PlayerStats
{
    private bool _dirty = true;
    private StatBlock _cached;

    public StatBlock Current
    {
        get
        {
            if (_dirty)
            {
                _cached = Recompute();
                _dirty = false;
            }
            return _cached;
        }
    }

    public void Invalidate() => _dirty = true; // 장비가 바뀔 때 호출
}
```

`Invalidate()`를 장비 변경 이벤트에 연결해두면, 실제 스탯이 필요한 시점에만 한 번 계산된다.

---

## Unity 구현 방법

### ScriptableObject 효과 자산 구조

```csharp
// 효과 하나를 나타내는 ScriptableObject
public abstract class GearEffect : ScriptableObject
{
    public abstract void Apply(StatModifiers mods, RunData run);
}

// 구체 예시: 공격력 플랫 보너스
[CreateAssetMenu(menuName = "OnionCat/GearEffect/FlatAtk")]
public class FlatAtkEffect : GearEffect
{
    [SerializeField] private float amount;

    public override void Apply(StatModifiers mods, RunData run)
    {
        mods.catAtkFlat += amount;
    }
}
```

`GearItem` ScriptableObject가 `GearEffect[]` 배열을 들고 있으면, 장비마다 효과 목록을 Inspector에서 드래그앤드롭으로 조립 가능.

### 수정자 컨테이너

```csharp
// 한 번의 Recompute에서 채워지는 임시 구조체
public struct StatModifiers
{
    // Cat stats
    public float catAtkFlat, catAtkAdditive, catAtkMulti;
    public float catSpeedFlat;
    public int   catDashCharges;
    // Onion stats
    public float onionAtkFlat, onionAtkAdditive;
    public float shieldCooldownMult;
    // Shared
    public int   maxHpFlat;
    public int   passiveShieldSlots;
    // ...
}
```

### Recompute 흐름

```csharp
private StatBlock Recompute()
{
    var mods = new StatModifiers();

    // 1. 장비 효과 전부 적용
    foreach (var slot in run.catGear)
        foreach (var eff in slot.item.effects)
            eff.Apply(mods, run);

    foreach (var slot in run.cropGear)
        foreach (var eff in slot.item.effects)
            eff.Apply(mods, run);

    // 2. 세트 보너스 적용 (PassiveHost.Recalculate 결과 활용)
    ApplySetBonuses(mods, run.setProgress);

    // 3. 최종 스탯 계산 (flat → additive → multi 순)
    return new StatBlock
    {
        catAtk    = (BaseCatAtk + mods.catAtkFlat)
                    * (1f + mods.catAtkAdditive)
                    * mods.catAtkMulti,
        catSpeed  = BaseCatSpeed + mods.catSpeedFlat,
        dashCharges = BaseDashCharges + mods.catDashCharges,
        maxHp     = BaseMaxHp + mods.maxHpFlat,
        // ...
    };
}
```

### 런타임(씬 한정) 임시 버프

방 안에서만 유효한 효과(예: "이 방 동안 공격력 +30%")는 별도 스택으로 관리:

```csharp
public class RuntimeBuffStack : MonoBehaviour
{
    private List<(StatType type, float value, float expireAt)> _buffs = new();

    public void Add(StatType type, float value, float duration)
    {
        _buffs.Add((type, value, Time.time + duration));
        PlayerStats.Instance.Invalidate();
    }

    private void Update()
    {
        int prev = _buffs.Count;
        _buffs.RemoveAll(b => b.expireAt < Time.time);
        if (_buffs.Count != prev) PlayerStats.Instance.Invalidate();
    }
}
```

영구 장비 효과(`GearEffect`)와 임시 버프를 `Recompute()` 안에서 순서대로 합산하면 하나의 파이프라인으로 통합된다.

---

## OnionCat 적용 포인트

OnionCat의 현재 구조(`RunData.RecomputeGear` → `PlayerStats.Current`)는 이미 올바른 방향이다.  
구체적으로 점검/보강할 부분:

1. **`GearEffect`를 ScriptableObject 기반 다형성으로 교체**  
   지금 효과가 하드코딩돼 있다면, 각 효과를 독립 SO 자산으로 분리하면 Inspector에서 새 장비를 조립할 때 코드 수정 없이 가능.

2. **더티 플래그 추가**  
   `PlayerStats.Current`를 매번 `RecomputeGear()`를 부르는 대신, 장비 변경 시 `Invalidate()`, 접근 시 캐시에서 읽도록 리팩터. Update에서 스탯을 읽는 컴포넌트가 많으면 프레임당 1회 재계산으로 충분.

3. **Flat / Additive / Multi 구분 명시**  
   같은 `atk` 스탯에 "+10 플랫"과 "+10%" 두 효과가 섞이면 순서가 중요. `StatModifiers`에 이미 구분돼 있다면 OK; 그렇지 않으면 계산 결과가 장비 조합에 따라 예상과 달라질 수 있다.

4. **세트 보너스를 같은 파이프라인에 통합**  
   `PassiveHost.Recalculate` 결과를 `Recompute()` 안에서 `ApplySetBonuses(mods, ...)` 형태로 받으면, 세트/장비 효과가 모두 하나의 최종 스탯으로 합산돼 버그가 줄어든다.

5. **레벨업 = 기본 능력치 × 레벨로 단순화**  
   `item.baseAtk * item.level`처럼 레벨이 flat 보너스를 선형으로 올린다면, GearEffect.Apply 쪽에 level 파라미터를 전달해서 한 곳에서 처리.

---

## 참고 링크

- GDC "Balancing for Fun and Profit" (stat modifier patterns): https://gdcvault.com/play/1012426
- Unity Forum: ScriptableObject-based modifier system — https://forum.unity.com/threads/scriptableobject-architecture.677029/
- Kryzarel stat system tutorial: https://youtu.be/SH25f3cXBVc
- Game Dev TV "Character Stats System": https://www.gamedev.tv/p/unity-rpg
- Path of Exile passive tree math (계산 순서 레퍼런스): https://www.pathofexile.com/forum/view-thread/11545
