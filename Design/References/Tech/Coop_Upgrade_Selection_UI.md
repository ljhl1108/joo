# 협동 업그레이드 선택 UI (Co-op Upgrade Selection UI)

리서치 날짜: 2026-08-02

## 개요

OnionCat은 **2명의 플레이어가 하나의 캐릭터를 공유**한다. 방 클리어 후 업그레이드를 선택할 때 일반적인 1인용 UI와 다른 특수한 도전이 있다:

- **두 플레이어 중 누가 선택권을 갖는가?** 둘 다? 한 명씩?
- Cat 전용 업그레이드 vs Onion 전용 업그레이드 vs 공유 업그레이드 — 어떻게 구분하나?
- 상대방이 고르는 것을 기다리는 동안 지루하지 않으려면?
- 선택 시간 제한이 있어야 하는가?

이 파일은 이 UI를 Unity에서 설계·구현하는 방법을 다룬다.

---

## 설계 패턴 선택지

### 패턴 A: 동시 선택 (Simultaneous Pick)
- Cat 화면 왼쪽, Onion 화면 오른쪽에 각자 3개 업그레이드 제시
- 동시에 독립적으로 선택
- **장점**: 빠름, 두 플레이어 모두 능동적  
- **단점**: 서로 상의 없이 선택하면 시너지 미스 가능

### 패턴 B: 순차 선택 (Sequential Pick)
- 먼저 Cat이 선택, 그다음 Onion이 선택
- 선택 완료 전까지 다른 플레이어는 관전
- **장점**: 상대방 선택을 보고 시너지 선택 가능  
- **단점**: 기다리는 플레이어가 지루함

### 패턴 C: 공유 선택지 + 협의 (Shared Pool + Agreement)
- 전체 업그레이드 6개(Cat 전용 2 + Onion 전용 2 + 공유 2)를 한 화면에 표시
- 두 플레이어가 각자 커서로 강조(hover) → 서로 추천 신호 전달
- 둘 다 같은 카드에 커서 올리면 확정 OR 각자 독립 확정
- **장점**: 협동 대화 촉진, 화면이 흥미로움  
- **단점**: 구현 복잡도 높음

**OnionCat 추천: 패턴 C (공유 선택지 + 협의)**

---

## Unity 구현 방법

### 1. 업그레이드 데이터 구조

```csharp
public enum UpgradeTarget { Cat, Onion, Shared }

[CreateAssetMenu(menuName = "OnionCat/Upgrade")]
public class UpgradeSO : ScriptableObject
{
    public string upgradeId;
    public string displayName;
    [TextArea] public string description;
    public Sprite icon;
    public UpgradeTarget target;  // Cat / Onion / Shared
    public Color themeColor;      // Cat = 주황, Onion = 초록, Shared = 흰색
}
```

### 2. 업그레이드 선택 화면 진입

```csharp
// RoomClearHandler.cs
public class RoomClearHandler : MonoBehaviour
{
    [SerializeField] private UpgradeSelectionUI upgradeUI;
    [SerializeField] private UpgradeDatabase upgradeDB;

    public void OnRoomCleared()
    {
        // 랜덤으로 Cat 전용 2 + Onion 전용 2 + Shared 2 = 6개 선택
        var options = upgradeDB.GetRandomOptions(catCount: 2, onionCount: 2, sharedCount: 2);
        upgradeUI.Show(options);
        Time.timeScale = 0f;  // 선택 중 게임 일시정지
    }
}
```

### 3. UI 컨트롤러

```csharp
// UpgradeSelectionUI.cs
public class UpgradeSelectionUI : MonoBehaviour
{
    [SerializeField] private UpgradeCard[] upgradeCards;  // UI 카드 6개 배열
    [SerializeField] private float selectionTimeout = 30f;  // 선택 제한 시간

    // 두 플레이어의 커서 위치 추적
    private int p1HoveredIndex = -1;
    private int p2HoveredIndex = -1;
    private bool p1Confirmed = false;
    private bool p2Confirmed = false;

    private List<UpgradeSO> currentOptions;
    private float timeRemaining;

    public void Show(List<UpgradeSO> options)
    {
        currentOptions = options;
        timeRemaining = selectionTimeout;
        gameObject.SetActive(true);

        for (int i = 0; i < upgradeCards.Length; i++)
        {
            upgradeCards[i].Setup(options[i]);
        }
    }

    void Update()
    {
        if (!gameObject.activeSelf) return;

        // 제한 시간 감소
        timeRemaining -= Time.unscaledDeltaTime;
        if (timeRemaining <= 0f)
        {
            AutoSelectRandom();
        }
    }

    // P1이 인덱스 i번 카드에 커서 올림
    public void OnP1Hover(int index)
    {
        p1HoveredIndex = index;
        RefreshHighlights();
    }

    // P2가 인덱스 i번 카드에 커서 올림
    public void OnP2Hover(int index)
    {
        p2HoveredIndex = index;
        RefreshHighlights();
    }

    // P1이 선택 확정
    public void OnP1Confirm()
    {
        if (p1HoveredIndex < 0) return;
        p1ConfirmedIndex = p1HoveredIndex;
        p1Confirmed = true;
        TryFinalize();
    }

    // P2가 선택 확정
    public void OnP2Confirm()
    {
        if (p2HoveredIndex < 0) return;
        p2ConfirmedIndex = p2HoveredIndex;
        p2Confirmed = true;
        TryFinalize();
    }

    private int p1ConfirmedIndex = -1;
    private int p2ConfirmedIndex = -1;

    private void TryFinalize()
    {
        if (!p1Confirmed || !p2Confirmed) return;

        // 둘 다 확정했을 때만 진행
        ApplyUpgrade(currentOptions[p1ConfirmedIndex]);
        ApplyUpgrade(currentOptions[p2ConfirmedIndex]);
        CloseUI();
    }

    private void RefreshHighlights()
    {
        for (int i = 0; i < upgradeCards.Length; i++)
        {
            bool isP1Hover = (i == p1HoveredIndex);
            bool isP2Hover = (i == p2HoveredIndex);
            bool bothHover = isP1Hover && isP2Hover;
            upgradeCards[i].SetHighlight(isP1Hover, isP2Hover, bothHover);
        }
    }

    private void AutoSelectRandom()
    {
        // 시간 초과: Cat/Onion 각각 랜덤 선택
        if (!p1Confirmed)
        {
            var catOptions = currentOptions.Where(u => u.target == UpgradeTarget.Cat || u.target == UpgradeTarget.Shared).ToList();
            p1ConfirmedIndex = currentOptions.IndexOf(catOptions[Random.Range(0, catOptions.Count)]);
            p1Confirmed = true;
        }
        if (!p2Confirmed)
        {
            var onionOptions = currentOptions.Where(u => u.target == UpgradeTarget.Onion || u.target == UpgradeTarget.Shared).ToList();
            p2ConfirmedIndex = currentOptions.IndexOf(onionOptions[Random.Range(0, onionOptions.Count)]);
            p2Confirmed = true;
        }
        TryFinalize();
    }

    private void ApplyUpgrade(UpgradeSO upgrade)
    {
        // UpgradeManager에 위임
        UpgradeManager.Instance.AddUpgrade(upgrade);
    }

    private void CloseUI()
    {
        gameObject.SetActive(false);
        Time.timeScale = 1f;
        p1Confirmed = p2Confirmed = false;
        p1HoveredIndex = p2HoveredIndex = -1;
        p1ConfirmedIndex = p2ConfirmedIndex = -1;
    }
}
```

### 4. 카드 UI 하이라이트 시각화

```csharp
// UpgradeCard.cs
public class UpgradeCard : MonoBehaviour
{
    [SerializeField] private Image background;
    [SerializeField] private Image p1Indicator;   // Cat 커서 표시 (고양이 발바닥 아이콘)
    [SerializeField] private Image p2Indicator;   // Onion 커서 표시 (새싹 아이콘)
    [SerializeField] private Image bothGlow;      // 둘 다 호버 시 빛나는 테두리
    [SerializeField] private TextMeshProUGUI titleText;
    [SerializeField] private TextMeshProUGUI descText;

    private UpgradeSO data;

    public void Setup(UpgradeSO upgrade)
    {
        data = upgrade;
        titleText.text = upgrade.displayName;
        descText.text = upgrade.description;
        background.color = upgrade.themeColor;
    }

    public void SetHighlight(bool isP1, bool isP2, bool bothHover)
    {
        p1Indicator.gameObject.SetActive(isP1);
        p2Indicator.gameObject.SetActive(isP2);
        bothGlow.gameObject.SetActive(bothHover);  // 동의 시 금색 테두리 표시
    }
}
```

---

## UI 레이아웃 제안

```
┌──────────────────────────────────────────────┐
│         ✨ 업그레이드 선택 ✨         [30s] │
│                                              │
│  [Cat 아이콘] 고양이 업그레이드              │
│  ┌──────┐  ┌──────┐                         │
│  │ 발톱 │  │ 대시 │                         │
│  │ +20% │  │ 쿨↓  │                         │
│  └──────┘  └──────┘                         │
│                                              │
│  [공유] 공용 업그레이드                      │
│  ┌──────┐  ┌──────┐                         │
│  │ HP+  │  │ 속도 │                         │
│  │ 20   │  │ +10% │                         │
│  └──────┘  └──────┘                         │
│                                              │
│  [Onion 아이콘] 작물 업그레이드              │
│  ┌──────┐  ┌──────┐                         │
│  │ 연사 │  │ 방패 │                         │
│  │ +1발 │  │ 반사 │                         │
│  └──────┘  └──────┘                         │
│                                              │
│  🐱 Cat: [선택 중...]   🌱 Onion: [확정!]   │
└──────────────────────────────────────────────┘
```

---

## OnionCat 적용 포인트

1. **Cat은 컨트롤러, Onion은 마우스**라는 입력 차이 → P1(Cat)은 스틱/버튼으로 카드 탐색, P2(Onion)은 마우스 클릭으로 선택
2. **둘 다 같은 카드에 커서 올리면 금색 글로우** → "서로 추천" 신호로 협동감 강화
3. **Cat 전용 카드는 주황빛 배경, Onion 전용은 초록빛 배경, 공유는 흰색/금색** → 색으로 즉시 구분
4. **한 명이 확정 시 확정한 카드에 잠금 아이콘 표시** → 남은 플레이어가 자신의 카드를 빠르게 고르도록 유도
5. **30초 타임아웃** → 너무 오래 고민하지 않도록, 과도한 분석 마비 방지
6. **두 플레이어가 같은 카드를 선택하면** → "한 명에게만 적용" or "양쪽에 반절씩 적용" 규칙 사전 정의 필요

---

## 참고 링크

- Unity UI Toolkit 공식: https://docs.unity3d.com/Manual/UIElements.html
- Unity 멀티플레이어 Input System 분리: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html
- Slay the Spire 카드 선택 UI 분석: https://slay-the-spire.fandom.com/wiki/Card
- Hades Boon 선택 UI 분석 (비대칭 선택 패턴): https://hades.fandom.com/wiki/Boons
