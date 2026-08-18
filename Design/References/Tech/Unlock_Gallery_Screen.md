# Unlock Gallery Screen (잠금 해제 갤러리 화면)

리서치 날짜: 2026-08-18

## 개요

잠금 해제 갤러리 화면은 플레이어가 지금까지 달성한 해금 항목(캐릭터 스킨, 업그레이드 아이템, 아트워크, 비하인드 씬, 도전과제)을 한눈에 볼 수 있는 컬렉션 허브다.

- **왜 중요한가**: 로그라이크에서 재플레이 동기를 제공하는 핵심 요소. "다음엔 무엇을 해금할 수 있는가?"가 플레이어를 붙잡는다.
- Dead Cells의 스킨 컬렉션, Hades의 비밀 수기(Codex), Binding of Isaac의 Paper's Please 잠금 해제 화면이 대표 사례
- OnionCat에서는 Cat/Crop 스킨, 무기 업그레이드 아이템, 스토리 파편, 도전과제를 갤러리로 통합 가능

---

## Unity 구현 방법

### 1. 데이터 구조 — UnlockableItemSO

```csharp
[CreateAssetMenu(fileName = "UnlockableItem", menuName = "OnionCat/UnlockableItem")]
public class UnlockableItemSO : ScriptableObject
{
    public string itemId;               // 고유 ID (저장/로드용)
    public string displayName;
    [TextArea] public string description;
    public UnlockCategory category;    // Skin, Upgrade, Artwork, Achievement, Lore
    public Sprite previewSprite;        // 해금 시 표시 이미지
    public Sprite lockedSprite;         // 잠금 상태 실루엣 (옵션)
    public string unlockCondition;      // UI 표시용 힌트 문자열
}

public enum UnlockCategory
{
    CharacterSkin,
    UpgradeItem,
    Artwork,
    Achievement,
    LoreFragment
}
```

### 2. 잠금 해제 상태 관리 — UnlockManager.cs

```csharp
public class UnlockManager : MonoBehaviour
{
    public static UnlockManager Instance { get; private set; }

    private HashSet<string> unlockedIds = new HashSet<string>();

    private const string SaveKey = "UnlockedItems";

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        LoadUnlocks();
    }

    public bool IsUnlocked(string itemId) => unlockedIds.Contains(itemId);

    public void Unlock(string itemId)
    {
        if (unlockedIds.Add(itemId))
        {
            SaveUnlocks();
            OnItemUnlocked?.Invoke(itemId);
        }
    }

    public event Action<string> OnItemUnlocked;

    private void SaveUnlocks()
    {
        PlayerPrefs.SetString(SaveKey, string.Join(",", unlockedIds));
        PlayerPrefs.Save();
    }

    private void LoadUnlocks()
    {
        string saved = PlayerPrefs.GetString(SaveKey, "");
        if (string.IsNullOrEmpty(saved)) return;
        foreach (var id in saved.Split(','))
            unlockedIds.Add(id);
    }
}
```

### 3. 갤러리 UI — GalleryScreen.cs

```csharp
public class GalleryScreen : MonoBehaviour
{
    [SerializeField] private UnlockableItemSO[] allItems;   // Inspector에서 전체 목록 할당
    [SerializeField] private GalleryItemUI itemUIPrefab;
    [SerializeField] private Transform gridParent;
    [SerializeField] private UnlockCategory currentFilter;

    [Header("Detail Panel")]
    [SerializeField] private Image detailImage;
    [SerializeField] private TMP_Text detailName;
    [SerializeField] private TMP_Text detailDescription;
    [SerializeField] private GameObject lockedHint;

    private void OnEnable() => RefreshGallery();

    public void SetFilter(UnlockCategory category)
    {
        currentFilter = category;
        RefreshGallery();
    }

    private void RefreshGallery()
    {
        foreach (Transform child in gridParent)
            Destroy(child.gameObject);

        var filtered = allItems.Where(i => i.category == currentFilter);
        foreach (var item in filtered)
        {
            var ui = Instantiate(itemUIPrefab, gridParent);
            bool unlocked = UnlockManager.Instance.IsUnlocked(item.itemId);
            ui.Initialize(item, unlocked, () => ShowDetail(item, unlocked));
        }
    }

    private void ShowDetail(UnlockableItemSO item, bool unlocked)
    {
        detailImage.sprite = unlocked ? item.previewSprite : item.lockedSprite;
        detailName.text = unlocked ? item.displayName : "???";
        detailDescription.text = unlocked ? item.description : $"해금 조건: {item.unlockCondition}";
        lockedHint.SetActive(!unlocked);
    }
}
```

### 4. 개별 갤러리 아이템 UI — GalleryItemUI.cs

```csharp
public class GalleryItemUI : MonoBehaviour
{
    [SerializeField] private Image thumbnailImage;
    [SerializeField] private Image lockOverlay;
    [SerializeField] private Button button;
    [SerializeField] private GameObject newBadge;   // 최근 해금 표시

    public void Initialize(UnlockableItemSO item, bool unlocked, Action onClick)
    {
        thumbnailImage.sprite = unlocked ? item.previewSprite : item.lockedSprite;
        thumbnailImage.color = unlocked ? Color.white : new Color(0.2f, 0.2f, 0.2f);
        lockOverlay.gameObject.SetActive(!unlocked);

        // "NEW" 뱃지: 마지막 확인 이후 해금된 항목
        bool isNew = unlocked && !PlayerPrefs.HasKey("seen_" + item.itemId);
        newBadge.SetActive(isNew);

        button.onClick.AddListener(() =>
        {
            if (isNew)
            {
                PlayerPrefs.SetInt("seen_" + item.itemId, 1);
                newBadge.SetActive(false);
            }
            onClick?.Invoke();
        });
    }
}
```

### 5. 해금 알림 팝업 — 런 종료 시 새 해금 항목 표시

```csharp
public class UnlockNotificationPopup : MonoBehaviour
{
    [SerializeField] private GameObject popup;
    [SerializeField] private Image unlockedItemImage;
    [SerializeField] private TMP_Text unlockedItemName;

    private void OnEnable()
    {
        UnlockManager.Instance.OnItemUnlocked += ShowUnlockPopup;
    }

    private void OnDisable()
    {
        if (UnlockManager.Instance != null)
            UnlockManager.Instance.OnItemUnlocked -= ShowUnlockPopup;
    }

    private void ShowUnlockPopup(string itemId)
    {
        // itemId로 SO 찾아서 표시 (Editor에서 Dictionary 빌드하거나 Resources.Load 활용)
        popup.SetActive(true);
        StartCoroutine(AutoHide(3f));
    }

    private IEnumerator AutoHide(float delay)
    {
        yield return new WaitForSeconds(delay);
        popup.SetActive(false);
    }
}
```

---

## OnionCat 적용 포인트

### 갤러리 카테고리 설계 제안

| 카테고리 | 내용 | 해금 조건 예시 |
|---|---|---|
| **Cat 스킨** | 고양이 외형 변경 (색상, 모자, 무기 디자인) | 특정 보스 처치, 런 횟수 달성 |
| **Crop 스킨** | 양파 외형 변경 (색상, 화분 디자인, 투사체 모양) | 특정 패링 횟수, 도전과제 |
| **업그레이드 도감** | 수집한 모든 업그레이드 아이템 + 설명 | 해당 아이템을 런에서 1회 획득 |
| **스토리 파편** | 세계관 로어 텍스트 조각 | 숨겨진 방 발견, 특정 NPC 조우 |
| **아트워크** | 개발자 아트, 컨셉 아트 (선택 해금) | 일정 런 완료 시 |
| **도전과제** | 달성/미달성 목록 + 진행도 표시 | 자동 |

### 구현 우선순위 (초보 개발자용)
1. **1단계**: `UnlockManager` + `PlayerPrefs` 저장 (30분)
2. **2단계**: 업그레이드 아이템 도감만 먼저 구현 (UI Grid + SO 데이터)
3. **3단계**: 카테고리 필터 탭 추가
4. **4단계**: "NEW" 뱃지 + 해금 팝업 알림
5. **5단계**: 스킨 미리보기 → 실제 스킨 적용 연동

### 주의사항
- `PlayerPrefs`는 단순하지만 플랫폼 이식 시 한계 있음 → 나중에 JSON 저장으로 마이그레이션 고려
- 갤러리 아이템 수가 많아지면 UI 가상화(Virtual Scroll) 필요 → Unity UI Toolkit의 `ListView` 활용
- "잠금 상태" 실루엣은 원본 스프라이트를 흑백+어둡게 처리하는 shader 또는 `Color(0.15f, 0.15f, 0.15f)` 단순 처리로 빠르게 구현

---

## 참고 링크

- [Unity ScriptableObject 공식 문서](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
- [Unity UI Toolkit ListView](https://docs.unity3d.com/Manual/UIE-ListView.html)
- [PlayerPrefs 공식 문서](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [Hades Codex 잠금해제 UX 분석](https://www.gamedeveloper.com/design/how-supergiant-games-uses-narrative-to-make-players-feel-smart)
- [Unity 컬렉션 시스템 구현 튜토리얼 (YouTube)](https://www.youtube.com/results?search_query=unity+collectibles+unlock+system+tutorial)
