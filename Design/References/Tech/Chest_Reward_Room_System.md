# 보상 상자 & 보물방 시스템 (Chest Reward Room System)

리서치 날짜: 2026-07-31

## 개요
로그라이크에서 **보물방(Treasure Room)**은 전투 없이 보상만 주는 특수 방. 그 안의 **상자(Chest)**는 아이템/골드/업그레이드를 드롭하는 핵심 보상 오브젝트.

OnionCat에서는 방마다 클리어 후 등장하는 보상 상자, 또는 특수 보물방 자체를 구현할 때 이 시스템이 필요. 상자 등급(나무/은/황금)과 열기 인터랙션까지 포함.

## Unity 구현 방법

### 1. 상자 등급 및 데이터 ScriptableObject
```csharp
public enum ChestType { Wooden, Silver, Golden, Boss }

[CreateAssetMenu(fileName = "ChestData", menuName = "OnionCat/ChestData")]
public class ChestData : ScriptableObject
{
    public ChestType chestType;
    public Sprite closedSprite;
    public Sprite openedSprite;
    public int itemCount;               // 드롭할 아이템 수
    public float legendaryChance;       // Legendary 등급 보정
    [Range(0f, 1f)] public float goldDropChance; // 골드 드롭 여부
    public int goldAmount;
}
```

### 2. Chest 컴포넌트
```csharp
public class Chest : MonoBehaviour, IInteractable
{
    [SerializeField] private ChestData _data;
    [SerializeField] private SpriteRenderer _spriteRenderer;
    [SerializeField] private GameObject _interactPrompt;
    [SerializeField] private Transform _dropOrigin;

    private bool _opened;
    private ItemDatabase _itemDatabase;

    private void Awake()
    {
        _itemDatabase = FindObjectOfType<ItemDatabase>(); // Awake에서 한 번만
        _spriteRenderer.sprite = _data.closedSprite;
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (!_opened && other.CompareTag("Player"))
            _interactPrompt.SetActive(true);
    }

    private void OnTriggerExit2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
            _interactPrompt.SetActive(false);
    }

    public void Interact()
    {
        if (_opened) return;
        StartCoroutine(OpenSequence());
    }

    private IEnumerator OpenSequence()
    {
        _opened = true;
        _interactPrompt.SetActive(false);

        // 열기 애니메이션 (스프라이트 교체 + 약간의 딜레이)
        yield return new WaitForSeconds(0.1f);
        _spriteRenderer.sprite = _data.openedSprite;

        // 아이템 드롭
        for (int i = 0; i < _data.itemCount; i++)
        {
            float lucky = _data.legendaryChance;
            ItemData item = _itemDatabase.RollRandom(lucky);
            SpawnItemPickup(item, i);
            yield return new WaitForSeconds(0.08f); // 드롭 사이 딜레이
        }

        // 골드 드롭
        if (Random.value < _data.goldDropChance)
            SpawnGold(_data.goldAmount);
    }

    private void SpawnItemPickup(ItemData item, int index)
    {
        float angle = (index / (float)_data.itemCount) * 360f;
        Vector2 offset = new Vector2(
            Mathf.Cos(angle * Mathf.Deg2Rad),
            Mathf.Sin(angle * Mathf.Deg2Rad)) * 0.8f;
        // ItemPickup 오브젝트 생성 (오브젝트 풀 사용 권장)
        // ItemPickupPool.Instance.Spawn(_dropOrigin.position + (Vector3)offset, item);
    }

    private void SpawnGold(int amount)
    {
        // GoldPickup 오브젝트 생성
    }
}
```

### 3. 인터랙션 인터페이스
```csharp
public interface IInteractable
{
    void Interact();
}
```

플레이어 컨트롤러에서 충돌 범위 내 `IInteractable` 감지:
```csharp
// PlayerController.cs — Awake에서 캐싱 금지, OverlapCircle로 매 프레임 탐색 아님
// 대신 OnTriggerEnter2D에서 _nearbyInteractable = other.GetComponent<IInteractable>()
private IInteractable _nearbyInteractable;

private void OnInteractInput(InputAction.CallbackContext ctx)
{
    _nearbyInteractable?.Interact();
}
```

### 4. 보물방(Treasure Room) 배치
보물방은 Room 시스템과 연동:
```csharp
public enum RoomType { Normal, Elite, Boss, Treasure, Shop, Rest }

public class RoomData : ScriptableObject
{
    public RoomType roomType;
    // ...
}
```

방 배치 규칙:
- 보물방은 층(Floor)당 1개 보장 (가중치 고정)
- 보스 방 직전 방에 보물방 금지 (너무 쉬운 보상 방지)
- 보물방은 적이 없어 바로 상자 열기 가능

```csharp
public class FloorGenerator : MonoBehaviour
{
    private void PlaceTreasureRoom(List<Room> rooms)
    {
        // 보스 방에서 최소 2칸 이상 떨어진 방 필터링
        var candidates = rooms.FindAll(r =>
            r.roomType == RoomType.Normal &&
            r.distanceToBoss >= 2);

        if (candidates.Count == 0) return;
        var chosen = candidates[Random.Range(0, candidates.Count)];
        chosen.roomType = RoomType.Treasure;
    }
}
```

### 5. 상자 애니메이션 (Sprite-based)
```
Chest_Wooden_Closed  → idle 애니메이션 (살짝 진동)
Chest_Wooden_Open    → open 애니메이션 (뚜껑 열림)
```
Animator 대신 단순 SpriteRenderer 교체로도 충분. 파티클 이펙트(빛 퍼짐, 별)는 `Feedback_System.md` 참고.

### 6. 상자 타입별 설정 예시
| 타입 | 아이템 수 | Legendary 보정 | 골드 확률 |
|------|-----------|----------------|-----------|
| Wooden | 1 | 0% | 50% |
| Silver | 2 | 0% | 30% |
| Golden | 2 | 15% | 80% |
| Boss   | 3 | 30% | 100% |

## OnionCat 적용 포인트

### 보상 흐름
```
방 클리어
  └→ 문 잠금 해제
       └→ 다음 방 이동 또는 보물방 입장
            └→ 상자 Interact
                 └→ 등급 결정 → 아이템 선택 UI 표시
```

### 협동 아이템 선택
보물방에서 상자를 열면 **Cat용 아이템 + Onion용 아이템** 각각 별도 슬롯에 표시:
- Cat(P1): 근접 능력 3개 선택지
- Onion(P2): 원거리/방패 능력 3개 선택지
- 둘 다 동시에 선택 화면이 떠서 각자 고름

### 상자 잠금 해제 조건 변형
기본 열기 외 조건부 열기로 긴장감 추가:
- **저주받은 상자**: 열면 랜덤 디버프 + 강력한 아이템 세트 (리스크/리워드)
- **2인 동시 열기**: Cat과 Onion이 동시에 상자의 양쪽을 잡아야 열림 → 협동 필수

### 세이브 연동
상자 오픈 여부는 RoomSaveData에 bool로 저장:
```csharp
[System.Serializable]
public class RoomSaveData
{
    public bool chestOpened;
    // ...
}
```
런 중 게임 종료 후 재시작해도 이미 열린 상자는 다시 열 수 없음.

## 참고 링크
- Unity ScriptableObject 공식 가이드: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Enter the Gungeon 보물방 설계: `Design/References/Game/Enter_the_Gungeon.md`
- 아이템 등급 시스템 연동: `Design/References/Tech/Loot_Rarity_Tier_System.md`
- 방 시스템 연동: `Design/References/Tech/Room_System.md`
- 아이템 픽업 연동: `Design/References/Tech/Item_Drop_Pickup_System.md`
- 피드백 이펙트 연동: `Design/References/Tech/Feedback_System.md`
