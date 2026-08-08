# Curse / Downside System (저주·페널티 업그레이드 시스템)

리서치 날짜: 2026-08-08

## 개요

로그라이크에서 **강력한 혜택과 동시에 페널티를 가진 업그레이드**를 구현하는 시스템.
Dead Cells의 "저주 무기", BoI의 "저주 아이템", Hades의 "처벌 계약" 등이 대표적.

OnionCat에서는 Cat·Crop 각자의 능력에 양날의 검 업그레이드를 추가하여
전략적 선택과 리스크 관리를 유도하는 데 필요.

### 왜 필요한가?
- 단순 "좋은 업그레이드"만 있으면 선택이 단조로워짐
- 저주/페널티 아이템은 **전략적 고민**과 **플레이어마다 다른 빌드**를 만들어냄
- "이 업그레이드가 내 현재 빌드와 맞는가?" → 체스판 같은 의사결정

---

## 레퍼런스 사례 분석

| 게임 | 구현 방식 | 특징 |
|------|-----------|------|
| Dead Cells | 저주 무기: 공격력 3배, 피격 시 즉사 | 고위험 고보상, 숙련자용 |
| Binding of Isaac | 저주 아이템: 강력하지만 제거 불가 + 저주 효과 | 누적 페널티 |
| Hades | 처벌 계약: 사용자가 직접 선택하는 핸디캡 | 보상과 연동 |
| Noita | 마법봉 조합: 잘못된 조합은 자해 가능 | 시스템 내재적 리스크 |

---

## Unity 구현 방법

### 1. 데이터 구조 (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "OnionCat/CursedUpgrade")]
public class CursedUpgradeData : UpgradeData
{
    [Header("저주 효과")]
    public string curseDescription;
    public StatModifier[] curseModifiers;  // 페널티 스탯 변경
    public CurseType curseType;            // 열거형: DAMAGE_RECEIVED, SPEED_REDUCTION, etc.
    public float curseValue;

    [Header("비주얼")]
    public Color cursedTintColor = new Color(0.6f, 0f, 0.8f); // 보라색 저주 색
    public Sprite curseIcon;
}

public enum CurseType
{
    DamageReceivedMultiplier,   // 받는 피해 증가
    SpeedReduction,             // 이동속도 감소
    AbilityCooldownIncrease,    // 쿨다운 증가
    MaxHPReduction,             // 최대 체력 감소
    OneHitBreak                 // 피격 시 업그레이드 파괴
}
```

### 2. StatModifier 적용

```csharp
public class PlayerStatManager : MonoBehaviour
{
    [SerializeField] private PlayerStats baseStats;
    private List<StatModifier> activeModifiers = new();

    public void ApplyUpgrade(UpgradeData upgrade)
    {
        foreach (var mod in upgrade.bonusModifiers)
            activeModifiers.Add(mod);

        // 저주 업그레이드면 페널티도 함께 적용
        if (upgrade is CursedUpgradeData cursed)
        {
            foreach (var mod in cursed.curseModifiers)
                activeModifiers.Add(mod);

            NotifyCurseApplied(cursed);
        }

        RecalculateStats();
    }

    private void RecalculateStats()
    {
        // 기본 스탯에서 시작해 모든 modifier 적용
        currentStats = baseStats.Clone();
        foreach (var mod in activeModifiers)
            mod.Apply(ref currentStats);
    }
}
```

### 3. 업그레이드 선택 UI에서 저주 표시

```csharp
public class UpgradeCardUI : MonoBehaviour
{
    [SerializeField] private Image cardBackground;
    [SerializeField] private TextMeshProUGUI curseDescriptionText;
    [SerializeField] private GameObject curseIconObj;

    public void Initialize(UpgradeData data)
    {
        // 일반 정보 셋업 ...

        bool isCursed = data is CursedUpgradeData;
        curseIconObj.SetActive(isCursed);
        curseDescriptionText.gameObject.SetActive(isCursed);

        if (isCursed)
        {
            var cursed = (CursedUpgradeData)data;
            curseDescriptionText.text = "⚠ " + cursed.curseDescription;
            cardBackground.color = Color.Lerp(Color.white, cursed.cursedTintColor, 0.3f);
        }
    }
}
```

### 4. 런 중 저주 상태 추적

```csharp
public class RunDataContainer : MonoBehaviour
{
    public List<UpgradeData> activeUpgrades = new();
    public List<CursedUpgradeData> activeCurses = new();

    public void AddUpgrade(UpgradeData upgrade)
    {
        activeUpgrades.Add(upgrade);
        if (upgrade is CursedUpgradeData cursed)
            activeCurses.Add(cursed);
    }

    public bool HasCurse(CurseType type) =>
        activeCurses.Any(c => c.curseType == type);
}
```

### 5. 저주 발동 이벤트 (OneHitBreak 예시)

```csharp
// 데미지 수신 시 저주 체크
public void OnDamageReceived(int damage)
{
    if (runData.HasCurse(CurseType.OneHitBreak))
    {
        // 해당 저주 업그레이드를 인벤토리에서 제거
        var brokenCurse = runData.activeCurses
            .FirstOrDefault(c => c.curseType == CurseType.OneHitBreak);
        if (brokenCurse != null)
        {
            runData.activeUpgrades.Remove(brokenCurse);
            runData.activeCurses.Remove(brokenCurse);
            statManager.RemoveUpgrade(brokenCurse);
            ShowCurseBreakEffect();
        }
    }
}
```

---

## OnionCat 적용 포인트

### A. Cat 전용 저주 예시
- "맹독의 발톱": 근접 데미지 2배, 하지만 근접 공격 시 자신도 소량 체력 감소
- "돌진의 저주": 대시 무적 유지, 하지만 대시 쿨다운 2배
- "분노의 일격": 체력 20% 이하일 때 근접 데미지 3배, 하지만 체력 회복 불가

### B. Crop(어니언) 전용 저주 예시
- "산탄의 저주": 탄환이 5갈래로 분산, 하지만 단일 데미지 50% 감소
- "관통의 가시": 탄환이 벽을 관통, 하지만 탄속 50% 감소 (예측 사격 필요)
- "방어의 대가": 실드 방어력 2배, 하지만 방어 시간 이후 3초 쿨다운 발생

### C. 두 플레이어 공유 저주 (협력 요구)
- "업보의 사슬": 어느 한 쪽이 데미지를 받으면 다른 플레이어도 절반 데미지 수신
  → 두 플레이어 모두 조심해야 하는 긴장감
- "교대 충전": Cat이 적을 처치하면 Crop의 실드 충전, Crop이 처치하면 Cat 대시 충전
  → 분업을 더 강하게 유도하는 저주

### D. 구현 순서 (초보자용)
1. `CursedUpgradeData` ScriptableObject 생성 (기존 UpgradeData 상속)
2. 업그레이드 선택 UI에 저주 표시 텍스트 + 색상 구분 추가
3. `PlayerStatManager`에 저주 modifier 적용 로직 추가
4. 2~3개 샘플 저주 데이터 에셋 생성 후 테스트
5. 밸런싱: 저주의 페널티 ↔ 혜택이 체감상 "아깝지만 고려할 만한 수준"인지 플레이 확인

---

## 참고 링크

- [Dead Cells 아이템 밸런싱 GDC 발표](https://www.youtube.com/results?search_query=dead+cells+GDC+item+design)
- [Binding of Isaac 저주 시스템 위키](https://bindingofisaacrebirth.fandom.com/wiki/Curses)
- [Unity ScriptableObject 패턴 공식 문서](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
- [Risk vs Reward in Game Design — Mark Brown GMTK](https://www.youtube.com/watch?v=G9FB5R4wVno)
