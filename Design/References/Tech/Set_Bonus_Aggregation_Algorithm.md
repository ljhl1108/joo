# 세트 보너스 집계·조합 알고리즘

리서치 날짜: 2026-10-30

## 개요

**세트 보너스(Set Bonus)**는 "같은 테마의 장비를 일정 수 이상 장착하면 추가 효과가 발동"하는 시스템이다.  
Diablo, Path of Exile, Risk of Rain 2 등 장비 기반 게임의 핵심 빌드 레이어.  
OnionCat은 10개 세트 × 2/4/6/8단계 = 40개 보너스, Cat·Onion **합산** 집계.

---

## Unity 구현 방법

### 1단계: 데이터 구조 설계

```csharp
// 세트 종류 열거형
public enum SetType { Sun, Wind, Storm, Root, Frost, Flame, Shadow, Iron, Bloom, Tide }

// 장비(ScriptableObject)에 세트 정보 포함
[CreateAssetMenu]
public class GearItem : ScriptableObject
{
    public SetType set;
    // ... 기타 필드
}
```

### 2단계: 집계 로직 (RunData 또는 CombatModifiers)

```csharp
public class CombatModifiers
{
    // 세트별 현재 장착 수 캐시 (재계산 비용 최소화)
    private static readonly Dictionary<SetType, int> _setCounts = new();

    // 장비 변경 시 호출 (PassiveHost.Recalculate 트리거)
    public static void Recalculate(IEnumerable<GearItem> catGear, IEnumerable<GearItem> onionGear)
    {
        _setCounts.Clear();
        foreach (var item in catGear.Concat(onionGear))
        {
            if (item == null) continue;
            _setCounts.TryGetValue(item.set, out int count);
            _setCounts[item.set] = count + item.level; // 레벨 = 중복 강화
        }
    }

    // 특정 세트가 특정 단계에 도달했는지 확인
    public static bool Has(SetType set, int tier)
    {
        return _setCounts.TryGetValue(set, out int count) && count >= tier;
    }

    // 모든 활성 보너스 적용 (GearEffect.Apply()에서 호출)
    public static bool HasAny(SetType set) => _setCounts.GetValueOrDefault(set) > 0;
    public static int Count(SetType set) => _setCounts.GetValueOrDefault(set);
}
```

### 3단계: 보너스 발동 확인

```csharp
// 실드 패시브 예시 - 세트 보너스 체크
void OnDamageTaken(DamageInfo dmg)
{
    float reduction = 1f;

    // Frost 세트 2단계: 받는 피해 10% 감소
    if (CombatModifiers.Has(SetType.Frost, 2)) reduction -= 0.10f;

    // Iron 세트 4단계: 물리 피해 추가 20% 감소
    if (CombatModifiers.Has(SetType.Iron, 4) && dmg.type == DamageType.Physical)
        reduction -= 0.20f;

    dmg.amount *= reduction;
}
```

### 4단계: 이벤트 기반 재계산 (성능 최적화)

```csharp
// 매 프레임 계산 금지 - 장비 변경 시에만 재계산
public class PassiveHost : MonoBehaviour
{
    void OnEnable()  => RunData.OnGearChanged += Recalculate;
    void OnDisable() => RunData.OnGearChanged -= Recalculate;

    void Recalculate()
    {
        CombatModifiers.Recalculate(
            RunData.Current.catGear,
            RunData.Current.onionGear
        );
    }
}
```

### 5단계: HUD에 세트 진행상황 표시

```csharp
// 현재 활성 세트 상위 2개 찾기 (HUD 표시용)
public static (SetType set, int count)[] GetTopSets(int topN = 2)
{
    return _setCounts
        .OrderByDescending(kv => kv.Value)
        .Take(topN)
        .Select(kv => (kv.Key, kv.Value))
        .ToArray();
}
```

---

## 성능 고려사항

| 상황 | 권장 방법 |
|------|-----------|
| 장비 장착/해제 | 전체 재계산 (비용 낮음 - 최대 10개 아이템) |
| 피해 계산 중 | `Has()` 캐시 조회 (O(1)) |
| 화면 렌더링 | `GetTopSets()` 프레임마다 호출 금지 → 변경 이벤트 시 UI 갱신 |
| 보스 전투 중 | 재계산 없음 (전투 중 장비 변경 불가) |

---

## OnionCat 적용 포인트

### 현재 OnionCat 구조와 일치 확인
- `CombatModifiers.Has(세트, 단계)` ← 이미 이 방식으로 구현됨 ✓
- `PassiveHost.Recalculate` ← 재계산 트리거 존재 ✓
- Cat + Onion 합산 집계 ✓

### 개선 여지 — 레벨 가중치
- 현재 중복 = 레벨업, 레벨이 높을수록 더 강해지는 수치 효과
- **세트 카운트에 레벨을 가중치로 반영할지 여부 결정 필요**
  - 방법 A: 레벨 무관 (장착 수만 카운트) → 레벨업의 의미가 스탯 증가에만 한정
  - 방법 B: `count += item.level` → 레벨 2 아이템이 세트 2개처럼 카운트 (현재 코드의 방식)
  - OnionCat은 어느 쪽이 재미있을지 플레이테스트로 확인 필요

### 세트 시너지 크로스 체크 패턴
```csharp
// 두 세트가 동시에 활성이면 시너지 발동
if (CombatModifiers.Has(SetType.Sun, 2) && CombatModifiers.Has(SetType.Wind, 2))
{
    // 햇살+바람 세트 동시 보유 시 특별 효과
    ApplySunWindSynergy();
}
```
- 이 패턴으로 "세트 간 시너지"를 나중에 쉽게 추가 가능

### 디버그 도구
```csharp
// OnionCat > Debug 메뉴에 추가하면 유용
[MenuItem("OnionCat/Debug/Print Set Counts")]
static void PrintSetCounts()
{
    foreach (SetType s in Enum.GetValues(typeof(SetType)))
        Debug.Log($"{s}: {CombatModifiers.Count(s)}");
}
```

---

## 참고 링크

- Unity Docs - Dictionary performance: https://docs.unity3d.com/ScriptReference/Collections.Generic.Dictionary.html
- Risk of Rain 2 ItemStat 분석 (커뮤니티): 세트 효과 집계 방식 리버스 엔지니어링 글들
- Path of Exile 세트 아이템 설계 철학: https://www.pathofexile.com/forum/view-thread/820218
- Diablo III 세트 보너스 시스템 설계: https://us.battle.net/forums/en/d3/topic/20745755027
