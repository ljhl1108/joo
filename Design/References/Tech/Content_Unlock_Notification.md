# Content Unlock Notification System

리서치 날짜: 2026-08-27

## 개요

새로운 콘텐츠(캐릭터 능력, 적 도감 등록, 업적, 비밀 방)가 잠금 해제될 때 화면에 팝업 알림을 표시하는 시스템. 게임의 "발견의 즐거움"을 강화하고, 플레이어에게 진행 피드백을 제공한다.

OnionCat에서는 메타 진행(런 간 영구 해금)이 있으므로, 런 종료 후 "이번 런 해금 요약"과 런 중 실시간 슬라이드 팝업 두 가지 모드가 필요하다.

## Unity 구현 방법

### 1. UnlockData ScriptableObject

```csharp
[CreateAssetMenu(fileName = "UnlockData", menuName = "OnionCat/UnlockData")]
public class UnlockData : ScriptableObject
{
    public string unlockId;           // 고유 ID (저장에 사용)
    public string displayName;        // "새 능력: 관통 투사체"
    public string description;        // 한 줄 설명
    public Sprite icon;               // 아이콘 이미지
    public UnlockCategory category;   // 카테고리
    [TextArea] public string loreText; // 서사 힌트 텍스트 (선택)
}

public enum UnlockCategory { Character, Enemy, Achievement, Item, Room }
```

---

### 2. UnlockManager (싱글톤)

```csharp
public class UnlockManager : MonoBehaviour
{
    public static UnlockManager Instance { get; private set; }

    private HashSet<string> _unlockedIds = new HashSet<string>();
    private List<UnlockData> _thisRunUnlocks = new List<UnlockData>();
    private const string SAVE_KEY = "UnlockedIds";

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        LoadUnlocks();
    }

    public bool IsUnlocked(string id) => _unlockedIds.Contains(id);

    public void Unlock(UnlockData data)
    {
        if (data == null || _unlockedIds.Contains(data.unlockId)) return;

        _unlockedIds.Add(data.unlockId);
        _thisRunUnlocks.Add(data);
        SaveUnlocks();

        // 런 중 실시간 팝업
        UnlockNotificationUI.Instance?.EnqueueNotification(data);

        // 이벤트 버스 발행 (다른 시스템 연동)
        EventBus.Publish(new OnUnlockEvent { Data = data });
    }

    public List<UnlockData> GetThisRunUnlocks() => _thisRunUnlocks;

    public void ResetRunUnlocks() => _thisRunUnlocks.Clear();

    private void SaveUnlocks()
    {
        PlayerPrefs.SetString(SAVE_KEY, string.Join(",", _unlockedIds));
        PlayerPrefs.Save();
    }

    private void LoadUnlocks()
    {
        string saved = PlayerPrefs.GetString(SAVE_KEY, "");
        if (string.IsNullOrEmpty(saved)) return;
        foreach (var id in saved.Split(','))
            _unlockedIds.Add(id);
    }
}
```

---

### 3. UnlockNotificationUI (슬라이드 팝업)

```csharp
public class UnlockNotificationUI : MonoBehaviour
{
    public static UnlockNotificationUI Instance { get; private set; }

    [SerializeField] private RectTransform notificationPanel;
    [SerializeField] private Image iconImage;
    [SerializeField] private TMP_Text titleText;
    [SerializeField] private TMP_Text descriptionText;
    [SerializeField] private float displayDuration = 3f;
    [SerializeField] private float slideDuration = 0.3f;
    [SerializeField] private float offscreenX = 500f;  // 화면 오른쪽 밖
    [SerializeField] private float onscreenX = -20f;   // 화면 안쪽

    private Queue<UnlockData> _queue = new Queue<UnlockData>();
    private bool _isShowing = false;

    private void Awake()
    {
        Instance = this;
        notificationPanel.gameObject.SetActive(false);
    }

    public void EnqueueNotification(UnlockData data)
    {
        _queue.Enqueue(data);
        if (!_isShowing) StartCoroutine(ShowNextCoroutine());
    }

    private IEnumerator ShowNextCoroutine()
    {
        while (_queue.Count > 0)
        {
            _isShowing = true;
            var data = _queue.Dequeue();

            iconImage.sprite = data.icon;
            titleText.text = $"[해금] {data.displayName}";
            descriptionText.text = data.description;

            notificationPanel.gameObject.SetActive(true);
            yield return SlideCoroutine(offscreenX, onscreenX); // 슬라이드 인
            yield return new WaitForSecondsRealtime(displayDuration);
            yield return SlideCoroutine(onscreenX, offscreenX); // 슬라이드 아웃
            notificationPanel.gameObject.SetActive(false);

            yield return new WaitForSecondsRealtime(0.2f); // 팝업 간 간격
        }
        _isShowing = false;
    }

    private IEnumerator SlideCoroutine(float fromX, float toX)
    {
        float elapsed = 0f;
        while (elapsed < slideDuration)
        {
            elapsed += Time.unscaledDeltaTime; // 일시정지 중에도 동작
            float t = Mathf.SmoothStep(0f, 1f, elapsed / slideDuration);
            notificationPanel.anchoredPosition = new Vector2(
                Mathf.Lerp(fromX, toX, t),
                notificationPanel.anchoredPosition.y
            );
            yield return null;
        }
        notificationPanel.anchoredPosition = new Vector2(toX, notificationPanel.anchoredPosition.y);
    }
}
```

---

### 4. 런 종료 후 해금 요약 (RunResultScreen 연동)

```csharp
public class RunResultScreen : MonoBehaviour
{
    [SerializeField] private Transform unlockListParent;
    [SerializeField] private GameObject unlockItemPrefab;
    [SerializeField] private GameObject unlockSectionHeader;

    public void ShowNewUnlocks()
    {
        var unlocks = UnlockManager.Instance.GetThisRunUnlocks();
        unlockSectionHeader.SetActive(unlocks.Count > 0);

        foreach (var unlock in unlocks)
        {
            var item = Instantiate(unlockItemPrefab, unlockListParent);
            item.GetComponentInChildren<TMP_Text>().text = unlock.displayName;
            item.GetComponentInChildren<Image>().sprite = unlock.icon;
        }

        UnlockManager.Instance.ResetRunUnlocks();
    }
}
```

---

### 5. 사용 예시 — 적 처치, 비밀 방 발견

```csharp
// EnemyBase.cs
private void OnDeath()
{
    if (bestiaryUnlockData != null)
        UnlockManager.Instance.Unlock(bestiaryUnlockData);
}

// HiddenWall.cs
public void OnDestroyed()
{
    if (secretRoomUnlockData != null)
        UnlockManager.Instance.Unlock(secretRoomUnlockData);
}
```

유니티 에디터에서 **드래그 앤 드롭 설정 필요**:
- `UnlockNotificationUI`의 `notificationPanel`, `iconImage`, `titleText`, `descriptionText` 오브젝트 연결
- 각 적 프리팹 Inspector에서 `bestiaryUnlockData` ScriptableObject 할당
- 비밀 방 오브젝트에 `secretRoomUnlockData` ScriptableObject 할당

## OnionCat 적용 포인트

### 해금 이벤트 우선순위
| 순위 | 이벤트 | 해금 내용 |
|------|--------|---------|
| 1 | 새 적 첫 처치 | 도감 등록 팝업 + 약점 힌트 |
| 2 | 비밀 방 발견 | "비밀 통로 발견!" + 서사 텍스트 |
| 3 | 특정 아이템 조합 | Cat/Onion 강화 능력 해금 |
| 4 | 업적 달성 | 업적 팝업 |

### 주의 사항
- `HashSet<string>`으로 중복 해금 방지 필수
- 알림 큐(Queue) 사용: 동시 해금 시 순차 표시
- `Time.unscaledDeltaTime` 사용: 일시정지 중 팝업이 사라지는 버그 방지
- UI 위치: 화면 우측 상단 권장 (HUD 미니맵과 겹치지 않도록)
- 런 종료 씬 전환 전에 `ResetRunUnlocks()` 호출 필수

## 참고 링크

- Unity PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Queue<T> 문서: https://docs.microsoft.com/dotnet/api/system.collections.generic.queue-1
- 관련 시스템: `Design/References/Tech/Achievement_Stats_System.md`
- 관련 시스템: `Design/References/Tech/Bestiary_Gallery_System.md`
- 관련 시스템: `Design/References/Tech/Toast_Notification_System.md`
- 관련 시스템: `Design/References/Tech/Run_Result_Screen.md`
