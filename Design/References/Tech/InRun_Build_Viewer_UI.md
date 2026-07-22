# 런 중 빌드 확인 UI (In-Run Build Viewer)

리서치 날짜: 2026-07-22

## 개요

로그라이크 게임에서 플레이어는 런 도중 "내가 지금 어떤 업그레이드를 갖고 있지?"를 확인하고 싶어한다. Hades의 장신구 목록, Dead Cells의 장비창, Enter the Gungeon의 아이템 목록처럼, 런 중 빌드 요약을 보여주는 UI는 완성도 있는 로그라이크의 필수 기능이다. 특히 2인 협력 게임에서는 "우리 팀이 어떤 빌드인지" 를 함께 확인하는 순간 자체가 협력의 경험이 된다.

## Unity 구현 방법

### 전체 구조

```
BuildViewerCanvas (Screen Space - Overlay, SortingOrder 높음)
  ├── DimBackground (Image, 반투명 검정)
  ├── Panel (RectTransform)
  │   ├── TabGroup
  │   │   ├── CatTab (Button)
  │   │   ├── CropTab (Button)
  │   │   └── SharedTab (Button)
  │   ├── UpgradeGrid (GridLayoutGroup, ScrollRect 하위)
  │   │   └── UpgradeSlot [프리팹] × N
  │   └── StatSummary
  │       └── StatText (TMP_Text)
  └── CloseHint (TMP_Text: "TAB / SELECT 버튼으로 닫기")
```

### 런 내 업그레이드 데이터 모델

```csharp
public enum UpgradeTarget { Cat, Crop, Shared }

[System.Serializable]
public class RunUpgradeData
{
    public string upgradeName;
    public string description;
    public Sprite icon;
    public UpgradeTarget target;
}

// 싱글톤 — 런 시작 시 초기화, 런 종료 시 클리어
public class RunInventory : MonoBehaviour
{
    public static RunInventory Instance { get; private set; }

    private readonly List<RunUpgradeData> acquiredUpgrades = new();

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    public void AddUpgrade(RunUpgradeData upgrade)
    {
        acquiredUpgrades.Add(upgrade);
    }

    public IReadOnlyList<RunUpgradeData> GetAll() => acquiredUpgrades;

    public IEnumerable<RunUpgradeData> GetByTarget(UpgradeTarget target) =>
        acquiredUpgrades.Where(u => u.target == target);

    public void ClearForNewRun() => acquiredUpgrades.Clear();
}
```

### BuildViewerUI 스크립트

```csharp
using UnityEngine;
using UnityEngine.InputSystem;
using TMPro;
using DG.Tweening;

public class BuildViewerUI : MonoBehaviour
{
    [SerializeField] private CanvasGroup panelGroup;
    [SerializeField] private RectTransform panel;
    [SerializeField] private Transform upgradeGrid;
    [SerializeField] private GameObject upgradeSlotPrefab;
    [SerializeField] private TMP_Text statText;

    private bool isOpen = false;

    // PlayerInput 컴포넌트에서 "BuildView" 액션과 연결
    public void OnBuildViewToggle(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed) return;
        if (isOpen) Close(); else Open();
    }

    private void Open()
    {
        isOpen = true;
        Time.timeScale = 0f;
        panelGroup.gameObject.SetActive(true);

        // DOTween 슬라이드인 (timeScale=0에서도 작동하려면 SetUpdate(true) 필수)
        panel.DOAnchorPosY(0f, 0.2f).SetEase(Ease.OutBack).SetUpdate(true);
        panelGroup.DOFade(1f, 0.15f).SetUpdate(true);

        PopulateGrid(UpgradeTarget.Shared); // 기본 탭
        UpdateStatText();
    }

    private void Close()
    {
        isOpen = false;
        panel.DOAnchorPosY(-Screen.height, 0.15f).SetEase(Ease.InBack).SetUpdate(true)
            .OnComplete(() => {
                panelGroup.gameObject.SetActive(false);
                Time.timeScale = 1f;
            });
    }

    public void ShowTab(int targetInt)
    {
        PopulateGrid((UpgradeTarget)targetInt);
    }

    private void PopulateGrid(UpgradeTarget filter)
    {
        foreach (Transform child in upgradeGrid)
            Destroy(child.gameObject);

        var upgrades = filter == UpgradeTarget.Shared
            ? RunInventory.Instance.GetAll()
            : RunInventory.Instance.GetByTarget(filter);

        foreach (var upgrade in upgrades)
        {
            var slot = Instantiate(upgradeSlotPrefab, upgradeGrid);
            slot.GetComponent<UpgradeSlotUI>().Setup(upgrade);
        }
    }

    private void UpdateStatText()
    {
        var s = PlayerStats.Instance;
        statText.text =
            $"HP: {s.maxHP}\n" +
            $"Cat 공격력: {s.catDamage}\n" +
            $"Crop 투사체: {s.cropDamage}\n" +
            $"이동속도: {s.moveSpeed:F1}";
    }
}
```

### 업그레이드 슬롯 프리팹 스크립트

```csharp
public class UpgradeSlotUI : MonoBehaviour
{
    [SerializeField] private Image iconImage;
    [SerializeField] private Image borderImage;
    [SerializeField] private TMP_Text nameText;
    [SerializeField] private TMP_Text descText;

    private static readonly Color ColorCat    = new Color(1.0f, 0.6f, 0.2f); // 주황
    private static readonly Color ColorCrop   = new Color(0.4f, 0.85f, 0.4f); // 연두
    private static readonly Color ColorShared = Color.white;

    public void Setup(RunUpgradeData data)
    {
        iconImage.sprite = data.icon;
        nameText.text    = data.upgradeName;
        descText.text    = data.description;

        borderImage.color = data.target switch
        {
            UpgradeTarget.Cat    => ColorCat,
            UpgradeTarget.Crop   => ColorCrop,
            _                    => ColorShared,
        };
    }
}
```

### Input Action 설정 (New Input System)

```
Action Map: UI
  Action: BuildView
    Binding 1: <Keyboard>/tab          (Crop P2)
    Binding 2: <Gamepad>/select        (Cat P1)
    Binding 3: <Gamepad>/touchpadClick (PS 계열)
```

PlayerInput 컴포넌트의 UI Action Map을 활성화하고, BuildViewerUI.OnBuildViewToggle을 UnityEvent 또는 SendMessage로 연결.

## OnionCat 적용 포인트

### Cat / Crop / 공유 탭 분리
업그레이드를 Cat 탭 / Crop 탭 / 전체 탭으로 분리해서 표시. 두 플레이어가 "나는 뭐 들었고 넌 뭐 들었어?"를 확인하는 순간 자체가 협력의 순간이 됨. 탭 버튼 테두리 색을 Cat=주황, Crop=연두로 통일.

### 보스 직전 자동 팝업
보스 방 입장 직전 "빌드 확인 방(Rest Room)"에서 BuildViewerUI.Open()을 자동 호출 → 두 플레이어가 자신의 업그레이드를 보면서 보스 전략을 짜는 자연스러운 흐름 유도.

### timeScale 처리 주의사항

| 상황 | 주의 사항 |
|------|-----------|
| DOTween 애니메이션 | `.SetUpdate(true)` 필수 (timeScale=0에서 정지 방지) |
| Coroutine | `WaitForSecondsRealtime` 사용 |
| 파티클 / 애니메이터 | `updateMode = AnimatorUpdateMode.UnscaledTime` |

### 구현 단계 (초보자 권장 순서)

1. `RunInventory` 싱글톤 생성 — 런 시작 시 ClearForNewRun()
2. 업그레이드 선택 화면에서 선택 시 `RunInventory.Instance.AddUpgrade(data)` 호출
3. Canvas에 BuildViewerUI 패널 비활성 상태로 배치 (CanvasGroup alpha=0)
4. PlayerInput에 "BuildView" 액션 추가, Tab / Select 버튼 바인딩
5. GridLayoutGroup + UpgradeSlotPrefab으로 자동 배열
6. PlayerStats 싱글톤에서 statText 직접 읽기
7. DOTween 슬라이드인/아웃 + `SetUpdate(true)` 추가

## 참고 링크

- Unity UI GridLayoutGroup: https://docs.unity3d.com/Manual/script-GridLayoutGroup.html
- Unity ScrollRect: https://docs.unity3d.com/Manual/script-ScrollRect.html
- DOTween 공식 (SetUpdate): http://dotween.demigiant.com/documentation.php
- New Input System PlayerInput: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInput.html
- Unity CanvasGroup: https://docs.unity3d.com/Manual/class-CanvasGroup.html
