# 상점 시스템 (In-Run Shop)

리서치 날짜: 2026-06-30

## 개요

런 중 등장하는 상점(In-Run Shop)은 로그라이크 게임의 핵심 경제 루프다. 플레이어가 런 중 모은 골드/자원을 소비해 아이템/업그레이드를 구매하는 장소로, 전략적 선택과 자원 관리 긴장감을 부여한다.

OnionCat에 이것이 필요한 이유:
- 방 클리어 후 단순 업그레이드 선택만 있으면 긴장감 부족
- 상점은 "지금 살 것인가, 나중을 위해 아낄 것인가" 결정을 만들어 줌
- 픽셀 아트 상인 NPC로 월드 분위기 형성에도 기여

---

## Unity 구현 방법

### 1. 데이터 구조 설계

```csharp
// ShopItem.cs - ScriptableObject로 아이템 정의
[CreateAssetMenu(menuName = "OnionCat/Shop/ShopItem")]
public class ShopItemSO : ScriptableObject
{
    public string itemName;
    public string description;
    public Sprite icon;
    public int basePrice;
    public ItemRarity rarity;
    public ItemType itemType; // Upgrade, Consumable, Equipment
}

public enum ItemRarity { Common, Uncommon, Rare, Legendary }
public enum ItemType { Upgrade, Consumable, RelicPassive }
```

```csharp
// ShopInventory.cs - 런마다 상점 인벤토리 생성
public class ShopInventory
{
    public List<ShopItemSO> availableItems;
    public Dictionary<ShopItemSO, int> prices;
    public HashSet<ShopItemSO> soldOutItems;

    // 상점 초기화: 풀에서 랜덤 N개 선택
    public void GenerateInventory(List<ShopItemSO> itemPool, int slotCount)
    {
        availableItems = new List<ShopItemSO>();
        prices = new Dictionary<ShopItemSO, int>();
        soldOutItems = new HashSet<ShopItemSO>();

        var shuffled = itemPool.OrderBy(_ => Random.value).Take(slotCount).ToList();
        
        foreach (var item in shuffled)
        {
            availableItems.Add(item);
            // 레어리티에 따른 가격 배율
            float rarityMultiplier = item.rarity switch
            {
                ItemRarity.Common    => 1.0f,
                ItemRarity.Uncommon  => 1.5f,
                ItemRarity.Rare      => 2.5f,
                ItemRarity.Legendary => 4.0f,
                _ => 1.0f
            };
            prices[item] = Mathf.RoundToInt(item.basePrice * rarityMultiplier);
        }
    }
}
```

### 2. 상점 매니저

```csharp
// ShopManager.cs
public class ShopManager : MonoBehaviour
{
    [SerializeField] private List<ShopItemSO> commonPool;
    [SerializeField] private List<ShopItemSO> rarePool;
    [SerializeField] private int shopSlots = 4;

    private ShopInventory _inventory;
    private RunCurrencyManager _currency; // 런 내 골드 관리

    void Awake()
    {
        _currency = RunCurrencyManager.Instance;
    }

    public void OpenShop()
    {
        if (_inventory == null)
            GenerateNewShop();

        GameManager.Instance.ChangeState(GameState.ShopOpen);
        ShopUI.Instance.Show(_inventory);
    }

    public void CloseShop()
    {
        GameManager.Instance.ChangeState(GameState.InRun);
        ShopUI.Instance.Hide();
    }

    private void GenerateNewShop()
    {
        var allItems = new List<ShopItemSO>();
        allItems.AddRange(commonPool);
        allItems.AddRange(rarePool);

        _inventory = new ShopInventory();
        _inventory.GenerateInventory(allItems, shopSlots);
    }

    public bool TryPurchase(ShopItemSO item)
    {
        if (_inventory.soldOutItems.Contains(item)) return false;
        
        int price = _inventory.prices[item];
        if (!_currency.CanAfford(price)) return false;

        _currency.Spend(price);
        _inventory.soldOutItems.Add(item);
        
        // 아이템 효과 적용
        ItemEffectApplier.Apply(item);
        
        return true;
    }

    // 다음 방에서도 같은 상점 유지 (Enter the Gungeon 방식)
    public void RefreshShop()
    {
        _inventory = null; // 다음 GenerateNewShop() 호출 시 새 상점
    }
}
```

### 3. 상점 UI 구현

```csharp
// ShopUI.cs
public class ShopUI : MonoBehaviour
{
    public static ShopUI Instance { get; private set; }

    [SerializeField] private GameObject shopPanel;
    [SerializeField] private ShopSlotUI[] slots; // 4개 슬롯
    [SerializeField] private TextMeshProUGUI goldDisplay;

    void Awake() => Instance = this;

    public void Show(ShopInventory inventory)
    {
        shopPanel.SetActive(true);
        
        for (int i = 0; i < slots.Length; i++)
        {
            if (i < inventory.availableItems.Count)
            {
                var item = inventory.availableItems[i];
                bool soldOut = inventory.soldOutItems.Contains(item);
                slots[i].Setup(item, inventory.prices[item], soldOut);
                slots[i].gameObject.SetActive(true);
            }
            else
            {
                slots[i].gameObject.SetActive(false);
            }
        }
        
        UpdateGoldDisplay();
    }

    public void Hide() => shopPanel.SetActive(false);

    private void UpdateGoldDisplay()
    {
        goldDisplay.text = $"골드: {RunCurrencyManager.Instance.CurrentGold}";
    }
}
```

```csharp
// ShopSlotUI.cs - 개별 아이템 슬롯
public class ShopSlotUI : MonoBehaviour
{
    [SerializeField] private Image itemIcon;
    [SerializeField] private Image rarityBorder; // 레어리티 색상 테두리
    [SerializeField] private TextMeshProUGUI itemNameText;
    [SerializeField] private TextMeshProUGUI priceText;
    [SerializeField] private TextMeshProUGUI descriptionText;
    [SerializeField] private Button buyButton;
    [SerializeField] private GameObject soldOutOverlay;

    private ShopItemSO _item;
    private int _price;

    public void Setup(ShopItemSO item, int price, bool soldOut)
    {
        _item = item;
        _price = price;

        itemIcon.sprite = item.icon;
        itemNameText.text = item.itemName;
        priceText.text = $"{price}G";
        descriptionText.text = item.description;
        
        // 레어리티 색상
        rarityBorder.color = GetRarityColor(item.rarity);
        
        soldOutOverlay.SetActive(soldOut);
        buyButton.interactable = !soldOut;
    }

    public void OnBuyButtonClick()
    {
        if (ShopManager.Instance.TryPurchase(_item))
        {
            soldOutOverlay.SetActive(true);
            buyButton.interactable = false;
            ShopUI.Instance.UpdateGoldDisplay(); // 골드 UI 갱신
        }
        else
        {
            // 골드 부족 피드백: 텍스트 빨간색 깜빡임
            StartCoroutine(FlashNotEnoughGold());
        }
    }

    private Color GetRarityColor(ItemRarity rarity) => rarity switch
    {
        ItemRarity.Common    => Color.gray,
        ItemRarity.Uncommon  => Color.green,
        ItemRarity.Rare      => new Color(0.2f, 0.5f, 1f), // 파랑
        ItemRarity.Legendary => Color.yellow,
        _ => Color.white
    };

    private IEnumerator FlashNotEnoughGold()
    {
        priceText.color = Color.red;
        yield return new WaitForSecondsRealtime(0.3f);
        priceText.color = Color.white;
    }
}
```

### 4. 런 골드 시스템

```csharp
// RunCurrencyManager.cs
public class RunCurrencyManager : MonoBehaviour
{
    public static RunCurrencyManager Instance { get; private set; }

    private int _gold;
    public int CurrentGold => _gold;

    public static event System.Action<int> OnGoldChanged;

    void Awake() => Instance = this;

    public void AddGold(int amount)
    {
        _gold += amount;
        OnGoldChanged?.Invoke(_gold);
    }

    public bool CanAfford(int price) => _gold >= price;

    public void Spend(int amount)
    {
        _gold = Mathf.Max(0, _gold - amount);
        OnGoldChanged?.Invoke(_gold);
    }
}
```

---

## OnionCat 적용 포인트

### 상점 등장 위치
Enter the Gungeon / Hades 방식 혼합:
```
[전투방] → [전투방] → [전투방] → [상점방] → [보스방]
```
- 각 층(Floor)마다 1개 상점 방 고정 배치
- 상점 방 입장 → ShopManager.OpenShop() 호출
- 상점 방 나가기 → CloseShop() + 다음 전투방으로 이동

### 상점 아이템 종류 (OnionCat)
| 타입 | 예시 | 가격 |
|------|------|------|
| Cat 강화 | 연속 슬래시 추가, 대시 쿨타임 감소 | 15~40G |
| Crop 강화 | 투사체 속도 증가, 방패 지속시간 연장 | 15~40G |
| 공용 강화 | 최대 HP +1, 피격 무적시간 연장 | 25~50G |
| 소모품 | 포션 (HP +2), 수류탄 (광역 딜) | 5~15G |
| 유물(Relic) | 패시브 특수 효과 (레전더리) | 80~120G |

### 두 플레이어 구매 방식
- **공동 골드**: 두 플레이어가 같은 골드 풀 공유 (협력 결정 유도)
- 플레이어 1(Cat) 또는 플레이어 2(Crop) 아무나 구매 가능
- "이거 살까?" "아니 나중에 유물 사자" → 대화 유도

### 상점 새로고침 기능
- 골드 10개로 상점 아이템 새로고침 가능 (Binding of Isaac 방식)
- `RerollButton` → `ShopManager.RefreshShop()` + `ShopUI.Show(newInventory)`

### 구현 우선순위
1. RunCurrencyManager (골드 시스템)
2. ShopItemSO ScriptableObject 3~5개 제작
3. ShopManager + ShopUI 기본 버전
4. 방 배치에 상점 방 타입 추가
5. 레어리티 및 가격 밸런싱

---

## 참고 링크

- Unity UI Button 이벤트: https://docs.unity3d.com/ScriptReference/UI.Button-onClick.html
- ScriptableObject 아이템 시스템: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Enter the Gungeon 상점 설계 분석: https://www.gamedeveloper.com/design/enter-the-gungeon-postmortem
- Unity 상점 UI 튜토리얼 (Brackeys): https://www.youtube.com/watch?v=HQNl3Ff2Lpo
- Hades 상점(Wretched Broker) 분석: https://hades.fandom.com/wiki/Wretched_Broker
