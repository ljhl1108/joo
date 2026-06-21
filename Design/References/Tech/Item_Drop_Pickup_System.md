# 아이템 드롭 & 픽업 시스템 (Item Drop & Pickup System)

리서치 날짜: 2026-06-21

## 개요

로그라이크 런 중 적 사망 시 아이템이 드롭되고, 플레이어가 접촉 또는 버튼으로 획득하는 시스템. OnionCat에서는 **런 내 전투 루프의 보상**이 되며, 씨앗(원거리 탄약), HP 회복 채소, 런 업그레이드 카드, 골드 등이 드롭 대상이다. 가중치 기반 드롭 테이블 + ScriptableObject + OnTriggerEnter2D 픽업 감지가 핵심 구조다.

## Unity 구현 방법

### 1. 아이템 ScriptableObject 정의

```csharp
[CreateAssetMenu(menuName = "OnionCat/Item")]
public class ItemData : ScriptableObject
{
    public string itemName;
    public Sprite icon;
    public ItemType type;       // Health, Currency, Upgrade, Ammo
    public float value;         // HP 회복량, 골드량 등
    public int dropWeight;      // 드롭 가중치 (높을수록 자주 드롭)
}

public enum ItemType { Health, Currency, Upgrade, Ammo }
```

### 2. 가중치 드롭 테이블 (LootTable ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "OnionCat/LootTable")]
public class LootTable : ScriptableObject
{
    [System.Serializable]
    public struct LootEntry
    {
        public ItemData item;
        public int weight;
        [Range(0f, 1f)] public float dropChance; // 0~1, 별도 확률 제어
    }

    public LootEntry[] entries;

    public ItemData Roll()
    {
        // 1단계: dropChance 체크 (아이템 자체가 드롭될지 여부)
        // 2단계: 가중치 랜덤으로 아이템 선택
        int totalWeight = 0;
        foreach (var e in entries) totalWeight += e.weight;

        int roll = Random.Range(0, totalWeight);
        int cumulative = 0;
        foreach (var e in entries)
        {
            cumulative += e.weight;
            if (roll < cumulative)
            {
                // dropChance 추가 체크
                if (Random.value <= e.dropChance)
                    return e.item;
                return null; // 이 슬롯이 뽑혔으나 확률 실패 → 드롭 없음
            }
        }
        return null;
    }
}
```

### 3. 드롭 아이템 월드 오브젝트

```csharp
public class WorldItem : MonoBehaviour
{
    public ItemData data;

    [SerializeField] private SpriteRenderer spriteRenderer;
    [SerializeField] private float magnetRadius = 2f;
    [SerializeField] private float magnetSpeed = 5f;

    private Transform _playerTransform;
    private bool _isBeingPulled;

    void Awake()
    {
        // 유니티 에디터에서 드래그 앤 드롭 설정 필요: spriteRenderer
    }

    public void Initialize(ItemData itemData)
    {
        data = itemData;
        spriteRenderer.sprite = itemData.icon;
    }

    void Update()
    {
        if (_playerTransform == null) return;

        float dist = Vector2.Distance(transform.position, _playerTransform.position);
        if (dist < magnetRadius)
        {
            // 자석 효과 — 플레이어 방향으로 끌려옴
            transform.position = Vector2.MoveTowards(
                transform.position,
                _playerTransform.position,
                magnetSpeed * Time.deltaTime);
        }
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (!other.CompareTag("Player")) return;

        if (other.TryGetComponent<IItemReceiver>(out var receiver))
        {
            receiver.ReceiveItem(data);
            Destroy(gameObject);
        }
    }

    public void SetPlayerRef(Transform player) => _playerTransform = player;
}
```

### 4. 적 사망 시 드롭 처리

```csharp
public class EnemyDeath : MonoBehaviour
{
    [SerializeField] private LootTable lootTable;
    [SerializeField] private GameObject worldItemPrefab;

    void Awake()
    {
        // 유니티 에디터에서 드래그 앤 드롭 설정 필요: lootTable, worldItemPrefab
    }

    public void Die()
    {
        SpawnLoot();
        Destroy(gameObject);
    }

    void SpawnLoot()
    {
        ItemData dropped = lootTable.Roll();
        if (dropped == null) return;

        var go = Instantiate(worldItemPrefab, transform.position, Quaternion.identity);
        if (go.TryGetComponent<WorldItem>(out var worldItem))
            worldItem.Initialize(dropped);
    }
}
```

### 5. 플레이어 아이템 수신 인터페이스

```csharp
public interface IItemReceiver
{
    void ReceiveItem(ItemData item);
}

public class PlayerInventory : MonoBehaviour, IItemReceiver
{
    public void ReceiveItem(ItemData item)
    {
        switch (item.type)
        {
            case ItemType.Health:
                GetComponent<PlayerHealth>().Heal(item.value);
                break;
            case ItemType.Currency:
                GameManager.Instance.AddGold((int)item.value);
                break;
            case ItemType.Upgrade:
                UpgradeManager.Instance.TriggerUpgradeChoice(item);
                break;
            case ItemType.Ammo:
                GetComponent<CropShooter>().AddAmmo((int)item.value);
                break;
        }
    }
}
```

### 6. 오브젝트 풀링으로 최적화 (적이 많을 때)

```csharp
// 드롭 아이템이 많다면 Instantiate/Destroy 대신 풀 사용
// WorldItemPool.cs — 간단 풀 예시
public class WorldItemPool : MonoBehaviour
{
    public static WorldItemPool Instance;
    [SerializeField] private GameObject worldItemPrefab;
    [SerializeField] private int poolSize = 30;
    private Queue<GameObject> _pool = new();

    void Awake()
    {
        Instance = this;
        for (int i = 0; i < poolSize; i++)
        {
            var obj = Instantiate(worldItemPrefab);
            obj.SetActive(false);
            _pool.Enqueue(obj);
        }
    }

    public GameObject Get(Vector2 pos)
    {
        var obj = _pool.Count > 0 ? _pool.Dequeue() : Instantiate(worldItemPrefab);
        obj.transform.position = pos;
        obj.SetActive(true);
        return obj;
    }

    public void Return(GameObject obj)
    {
        obj.SetActive(false);
        _pool.Enqueue(obj);
    }
}
```

## OnionCat 적용 포인트

### 구현 순서
1. `ItemData.cs` ScriptableObject 생성 + 에셋 세팅 (HP채소, 골드씨앗, 업그레이드카드)
2. `LootTable.cs` ScriptableObject — 적 유형별 드롭 테이블 세팅
3. `WorldItem.cs` + Prefab — 씬에서 물리적으로 나타나는 아이템 오브젝트
4. `EnemyDeath.cs`에 SpawnLoot 연결
5. `PlayerInventory.cs`에 IItemReceiver 구현
6. 드롭 아이템 많아지면 WorldItemPool 도입

### OnionCat 드롭 테이블 설계안
| 아이템 | 타입 | 드롭 가중치 | 드롭 확률 |
|--------|------|-------------|-----------|
| 채소 조각 (HP 소량 회복) | Health | 50 | 60% |
| 씨앗 탄약 | Ammo | 30 | 80% |
| 골드 양파 | Currency | 40 | 50% |
| 업그레이드 씨앗 카드 | Upgrade | 10 | 20% |
| 대형 양파 (HP 다량 회복) | Health | 5 | 10% |

### 주의 사항
- `[SerializeField]` 변수들 → 유니티 에디터에서 드래그 앤 드롭 설정 필요
- OnTriggerEnter2D 사용 시 WorldItem GameObject에 IsTrigger 체크된 Collider2D 필요
- 플레이어와 월드아이템의 레이어 충돌 매트릭스 확인 (Physics 2D → Layer Collision Matrix)
- 업그레이드 카드 드롭 시 게임 일시정지 후 선택 UI 표시 권장

## 참고 링크

- Unity Weighted Random Loot: https://medium.com/@kshesho/unity-how-to-create-a-weighted-loot-table-3bcbf478eaf9
- YouTube - Random Loot Table: https://www.youtube.com/watch?v=OUlxP4rZap0
- YouTube - Flexible Loot System: https://www.youtube.com/watch?v=KjvvRmG7PBM
- Unity Forum - Drop Rarity: https://forum.unity.com/threads/item-drop-rarity-weighted.537363/
- TopDown Engine Loot Docs: https://topdown-engine-docs.moremountains.com/loot.html
