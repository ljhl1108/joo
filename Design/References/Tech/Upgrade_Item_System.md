# 업그레이드 / 아이템 시스템 (Run Upgrades)

리서치 날짜: 2026-06-13

## 개요

로그라이크 핵심 루프인 "레벨업 → 업그레이드 선택" 구조. 런 중 플레이어가 3개의 아이템/능력 중 하나를 선택해 캐릭터를 성장시킨다. OnionCat에서는 Cat과 Onion이 공유하는 단일 업그레이드 풀이거나, 각자의 능력을 강화하는 별도 업그레이드 풀로 분리할 수 있다. ScriptableObject 기반으로 데이터와 로직을 분리하는 것이 Unity에서의 표준 구현법이다.

---

## Unity 구현 방법

### Step 1: UpgradeData ScriptableObject 정의

```csharp
// UpgradeData.cs
[CreateAssetMenu(menuName = "OnionCat/UpgradeData")]
public class UpgradeData : ScriptableObject
{
    public string upgradeName;
    [TextArea] public string description;
    public Sprite icon;
    public UpgradeRarity rarity;
    public UpgradeTarget target; // Cat, Onion, Both

    // 실제 효과는 상속 or UnityEvent로 처리
    public virtual void Apply(PlayerStats stats) { }
}

public enum UpgradeRarity { Common, Rare, Epic, Legendary }
public enum UpgradeTarget { Cat, Onion, Shared }
```

### Step 2: 구체 업그레이드 구현 (상속 방식)

```csharp
// DamageUpgrade.cs
[CreateAssetMenu(menuName = "OnionCat/Upgrades/DamageUpgrade")]
public class DamageUpgrade : UpgradeData
{
    public float damageMultiplier = 1.2f;

    public override void Apply(PlayerStats stats)
    {
        stats.attackDamage *= damageMultiplier;
    }
}
```

### Step 3: UpgradePool — 드롭 가중치 관리

```csharp
// UpgradePool.cs
[CreateAssetMenu(menuName = "OnionCat/UpgradePool")]
public class UpgradePool : ScriptableObject
{
    [System.Serializable]
    public struct WeightedUpgrade
    {
        public UpgradeData upgrade;
        public int weight; // 숫자 클수록 자주 등장
    }

    public List<WeightedUpgrade> upgrades;

    public List<UpgradeData> PickRandom(int count)
    {
        // 가중치 합산 후 랜덤 추출 (중복 없이)
        var result = new List<UpgradeData>();
        var available = new List<WeightedUpgrade>(upgrades);

        for (int i = 0; i < count && available.Count > 0; i++)
        {
            int totalWeight = 0;
            foreach (var w in available) totalWeight += w.weight;

            int roll = Random.Range(0, totalWeight);
            int cumulative = 0;
            for (int j = 0; j < available.Count; j++)
            {
                cumulative += available[j].weight;
                if (roll < cumulative)
                {
                    result.Add(available[j].upgrade);
                    available.RemoveAt(j);
                    break;
                }
            }
        }
        return result;
    }
}
```

### Step 4: UpgradeManager — 게임플레이 흐름 제어

```csharp
// UpgradeManager.cs
public class UpgradeManager : MonoBehaviour
{
    [SerializeField] private UpgradePool upgradePool;
    [SerializeField] private UpgradeUIPanel upgradeUI;
    [SerializeField] private PlayerStats catStats;
    [SerializeField] private PlayerStats onionStats;

    public void TriggerUpgradeSelection()
    {
        Time.timeScale = 0f; // 게임 일시정지
        var choices = upgradePool.PickRandom(3);
        upgradeUI.Show(choices, OnUpgradeSelected);
    }

    private void OnUpgradeSelected(UpgradeData chosen)
    {
        switch (chosen.target)
        {
            case UpgradeTarget.Cat:    chosen.Apply(catStats);   break;
            case UpgradeTarget.Onion:  chosen.Apply(onionStats); break;
            case UpgradeTarget.Shared:
                chosen.Apply(catStats);
                chosen.Apply(onionStats);
                break;
        }
        upgradeUI.Hide();
        Time.timeScale = 1f;
    }
}
```

### Step 5: 업그레이드 UI 패널

```csharp
// UpgradeUIPanel.cs
public class UpgradeUIPanel : MonoBehaviour
{
    [SerializeField] private UpgradeCard[] cards; // 카드 3개 UI 오브젝트

    private System.Action<UpgradeData> onSelected;

    public void Show(List<UpgradeData> choices, System.Action<UpgradeData> callback)
    {
        gameObject.SetActive(true);
        onSelected = callback;
        for (int i = 0; i < cards.Length; i++)
        {
            if (i < choices.Count)
            {
                cards[i].gameObject.SetActive(true);
                cards[i].Setup(choices[i], () => onSelected(choices[i]));
            }
            else
            {
                cards[i].gameObject.SetActive(false);
            }
        }
    }

    public void Hide() => gameObject.SetActive(false);
}
```

### Step 6: 레벨 경험치 연동 (간단한 구조)

```csharp
// ExperienceSystem.cs
public class ExperienceSystem : MonoBehaviour
{
    [SerializeField] private UpgradeManager upgradeManager;

    private int currentXP;
    private int level = 1;
    private int xpToNextLevel = 100;

    public void AddXP(int amount)
    {
        currentXP += amount;
        if (currentXP >= xpToNextLevel)
        {
            currentXP -= xpToNextLevel;
            level++;
            xpToNextLevel = Mathf.RoundToInt(xpToNextLevel * 1.3f); // 요구량 증가
            upgradeManager.TriggerUpgradeSelection();
        }
    }
}
```

### 리롤 기능 추가 (선택)

```csharp
public void Reroll()
{
    if (currency >= rerollCost)
    {
        currency -= rerollCost;
        rerollCost += 10; // 리롤할수록 비싸짐
        var newChoices = upgradePool.PickRandom(3);
        upgradeUI.Refresh(newChoices);
    }
}
```

---

## OnionCat 적용 포인트

### 1. 업그레이드 타겟 분리
- `UpgradeTarget.Cat`: 슬래시 범위 확대, 대시 쿨다운 감소, 이동속도 증가
- `UpgradeTarget.Onion`: 투사체 피어싱, 실드 지속시간 증가, 패리 히트박스 확대
- `UpgradeTarget.Shared`: 체력 증가, 경험치 보너스, 이동속도 공유 버프

### 2. 협력 시너지 업그레이드
- Rogue Genesia의 "무기 진화" 개념 적용:
  - Cat이 "슬래시 차지" 업그레이드 + Onion이 "관통탄" 업그레이드 → **조합 업그레이드 해금**
  - 두 플레이어가 같은 선택을 맞춰야 발동 → 실제 협력 대화 유도

### 3. 중복 선택 = 레벨업
- 같은 업그레이드를 다시 선택하면 효과가 강화됨 (Lv.1 → Lv.2 → Lv.3)
- `UpgradeData`에 `int currentLevel`과 `float[] multipliersByLevel` 추가

### 4. ScriptableObject 기반의 장점
- 기획자(개발자 본인)가 유니티 에디터에서 직접 업그레이드 수치 조정 가능
- 코드 재빌드 없이 밸런스 조정 → 빠른 이터레이션
- `Resources.LoadAll<UpgradeData>("Upgrades")` 로 자동 풀 구성 가능

### 5. PlayerStats 구조 권장
```csharp
public class PlayerStats : MonoBehaviour
{
    public float attackDamage = 10f;
    public float moveSpeed = 5f;
    public float dashCooldown = 1f;
    public float maxHealth = 100f;
    // ... 업그레이드가 수정할 모든 스탯
}
```

---

## 주의사항

- `Time.timeScale = 0f` 일시정지 시 애니메이션과 파티클이 멈출 수 있음 → `unscaledTime` 사용 고려
- 업그레이드 적용은 반드시 **런 시작 시 스탯 리셋** 로직과 함께 구현 (퍼머데스 = 런 종료 = 스탯 초기화)
- UI 리롤 버튼은 `InputSystem`의 특정 버튼에 바인딩 → 마우스 없는 컨트롤러 플레이어 지원

---

## 참고 링크

- Unity ScriptableObject 공식 문서: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Brackeys - Scriptable Objects 튜토리얼: https://www.youtube.com/watch?v=aPXvoWVabPY
- Unity 공식 - Pause Game (Time.timeScale): https://docs.unity3d.com/ScriptReference/Time-timeScale.html
- GDC Talk - Isaac의 아이템 디자인 철학: https://www.gdcvault.com/play/1015756
- Rogue Genesia 아이템 조합 시스템 분석 (팬덤 위키): https://rogue-genesia.fandom.com/wiki/Weapons
