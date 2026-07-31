# 아이템 등급(레어리티) 시스템 (Loot Rarity Tier System)

리서치 날짜: 2026-07-31

## 개요
로그라이크 장르의 핵심 동기 부여 장치. 아이템/능력에 등급을 부여해 **드롭 기대감과 빌드 다양성**을 동시에 제공. 낮은 등급은 자주 나오지만 약하고, 높은 등급은 희귀하지만 런을 뒤집을 정도로 강력.

OnionCat에서는 방 클리어 후 나오는 **능력 업그레이드 선택지**와 **보상 상자**에 등급 시스템을 적용해, "이번 런에 전설 아이템 나왔다!" 같은 흥분 포인트를 만들 수 있음.

## Unity 구현 방법

### 1. 등급 enum 정의
```csharp
public enum ItemRarity
{
    Common,    // 회색 — 기본 강화
    Uncommon,  // 녹색 — 소소한 특수 효과
    Rare,      // 파랑 — 플레이 스타일 변화
    Epic,      // 보라 — 강력한 시너지
    Legendary  // 금색 — 런을 정의하는 강력함
}
```

### 2. ScriptableObject 아이템 데이터
```csharp
[CreateAssetMenu(fileName = "NewItem", menuName = "OnionCat/Item")]
public class ItemData : ScriptableObject
{
    public string itemName;
    [TextArea] public string description;
    public ItemRarity rarity;
    public Sprite icon;
    public Sprite glowIcon; // 등급별 테두리 포함 버전

    [Header("Effect")]
    public AbilityEffectBase effect; // 추상 클래스 상속
}
```

### 3. 등급별 색상 매핑
```csharp
public static class RarityColorMap
{
    private static readonly Dictionary<ItemRarity, Color> Colors = new()
    {
        { ItemRarity.Common,    new Color(0.78f, 0.78f, 0.78f) }, // #C8C8C8
        { ItemRarity.Uncommon,  new Color(0.29f, 0.73f, 0.29f) }, // 녹색
        { ItemRarity.Rare,      new Color(0.27f, 0.53f, 0.95f) }, // 파랑
        { ItemRarity.Epic,      new Color(0.64f, 0.21f, 0.93f) }, // 보라
        { ItemRarity.Legendary, new Color(1.00f, 0.80f, 0.00f) }, // 금색
    };

    public static Color Get(ItemRarity rarity) => Colors[rarity];
}
```

### 4. 가중치 기반 랜덤 등급 뽑기
```csharp
public static class RarityWeightTable
{
    // 기본 웨이트: 합계 100
    private static readonly Dictionary<ItemRarity, int> BaseWeights = new()
    {
        { ItemRarity.Common,    50 },
        { ItemRarity.Uncommon,  28 },
        { ItemRarity.Rare,      14 },
        { ItemRarity.Epic,       6 },
        { ItemRarity.Legendary,  2 },
    };

    public static ItemRarity Roll(float luckyBonus = 0f)
    {
        // luckyBonus: 0~1, 높을수록 희귀 등급 확률 증가
        var weights = new Dictionary<ItemRarity, int>(BaseWeights);
        if (luckyBonus > 0f)
        {
            int boost = Mathf.RoundToInt(luckyBonus * 20f);
            weights[ItemRarity.Rare]      += boost;
            weights[ItemRarity.Epic]      += boost / 2;
            weights[ItemRarity.Legendary] += boost / 4;
            weights[ItemRarity.Common]    = Mathf.Max(1, weights[ItemRarity.Common] - boost);
        }

        int total = 0;
        foreach (var w in weights.Values) total += w;

        int roll = Random.Range(0, total);
        int cumulative = 0;
        foreach (var (rarity, weight) in weights)
        {
            cumulative += weight;
            if (roll < cumulative) return rarity;
        }
        return ItemRarity.Common;
    }
}
```

### 5. 등급에 맞는 아이템 풀 필터링
```csharp
public class ItemDatabase : MonoBehaviour
{
    [SerializeField] private List<ItemData> allItems;

    public ItemData GetRandomByRarity(ItemRarity rarity)
    {
        var pool = allItems.FindAll(item => item.rarity == rarity);
        if (pool.Count == 0) return null;
        return pool[Random.Range(0, pool.Count)];
    }

    public ItemData RollRandom(float luckyBonus = 0f)
    {
        ItemRarity rarity = RarityWeightTable.Roll(luckyBonus);
        return GetRandomByRarity(rarity) ?? GetRandomByRarity(ItemRarity.Common);
    }
}
```

### 6. UI — 등급 테두리 & 파티클
```csharp
public class ItemSlotUI : MonoBehaviour
{
    [SerializeField] private Image iconImage;
    [SerializeField] private Image borderImage;
    [SerializeField] private ParticleSystem rarityParticles;

    public void Setup(ItemData data)
    {
        iconImage.sprite = data.icon;
        Color rarityColor = RarityColorMap.Get(data.rarity);
        borderImage.color = rarityColor;

        // Epic 이상이면 파티클 재생
        rarityParticles.gameObject.SetActive(data.rarity >= ItemRarity.Epic);
        if (data.rarity >= ItemRarity.Epic)
        {
            var main = rarityParticles.main;
            main.startColor = rarityColor;
            rarityParticles.Play();
        }
    }
}
```

## OnionCat 적용 포인트

### 적용 위치
1. **방 클리어 보상**: 랜덤 능력 업그레이드 3개 선택지 — 각 슬롯이 RarityWeightTable로 등급 결정
2. **보상 상자**: 상자 등급(나무/은/황금)에 따라 가중치 다르게 설정
3. **보스 처치 보상**: Legendary 확률 20%로 고정 보너스

### Cat / Onion 분리 아이템 풀
```
ItemDatabase
├── catItems[]    → P1(Cat) 근접 특화 능력
└── onionItems[]  → P2(Onion) 원거리/방패 특화 능력
```
동일 등급이라도 캐릭터마다 별도 풀에서 뽑아 역할 비대칭 유지.

### 운(Lucky) 스탯 연동
특정 업그레이드가 "운" 수치를 올리면 `luckyBonus` 파라미터에 반영 → 높은 등급 드롭 확률 상승. 플레이어가 빌드로 드롭 확률을 조작하는 메타 전략 가능.

## 참고 링크
- Unity ScriptableObject 공식 문서: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Random.Range 가중치 랜덤 패턴: Unity 공식 Learn 튜토리얼 참고
- Diablo 4 아이템 등급 색상 참고: 게임 업계 표준 (회색/녹색/파랑/보라/금)
- Enter the Gungeon 아이템 품질 시스템: `Design/References/Game/Enter_the_Gungeon.md`
- Binding of Isaac 아이템 풀: `Design/References/Game/Binding_of_Isaac.md`
