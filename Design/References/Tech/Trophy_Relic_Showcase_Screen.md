# Trophy & Relic Showcase Screen

리서치 날짜: 2026-09-09

## 개요

런 중 획득한 유물·아이템·특수 오브젝트들을 **영구 갤러리 형태**로 보여주는 화면이다. Achievement_Stats(숫자 기록)나 Bestiary(적 도감)와 달리, 이 화면은 **플레이어가 발견한 아이템·유물의 시각적 컬렉션**을 자랑할 수 있는 "트로피 룸"이다. Hades의 관계 기록실, Dead Cells의 무기 갤러리처럼 컬렉션 완성 동기를 제공하고, 반복 플레이(론 반복)를 자연스럽게 유도한다.

OnionCat에서는 "화분 선반" 테마로 — Cat이 발견한 씨앗·유물을 화분에 담아 선반에 진열하는 비주얼로 세계관 연결이 가능하다.

---

## Unity 구현 방법

### 1. 데이터 구조 설계 (ScriptableObject)

```csharp
[CreateAssetMenu(fileName = "RelicData", menuName = "OnionCat/RelicData")]
public class RelicData : ScriptableObject
{
    public string relicId;          // 고유 ID (저장 키로 사용)
    public string displayName;
    [TextArea] public string loreText;
    public Sprite icon;
    public RelicRarity rarity;      // Common / Rare / Legendary
    public bool isDiscovered;       // 런 중 한 번이라도 획득했는지
}

public enum RelicRarity { Common, Rare, Legendary }
```

### 2. 영구 발견 상태 저장 (Save System 연동)

```csharp
public static class RelicDiscoveryManager
{
    private const string SAVE_KEY_PREFIX = "relic_discovered_";

    public static void MarkDiscovered(string relicId)
    {
        PlayerPrefs.SetInt(SAVE_KEY_PREFIX + relicId, 1);
        PlayerPrefs.Save();
    }

    public static bool IsDiscovered(string relicId)
    {
        return PlayerPrefs.GetInt(SAVE_KEY_PREFIX + relicId, 0) == 1;
    }

    public static List<string> GetAllDiscovered(List<RelicData> allRelics)
    {
        return allRelics
            .Where(r => IsDiscovered(r.relicId))
            .Select(r => r.relicId)
            .ToList();
    }
}
```

### 3. 트로피 룸 UI 구성

```
[TrophyRoomUI] (Canvas)
├── [ShelfContainer] (ScrollRect + VerticalLayoutGroup)
│   ├── [ShelfRow_Common] (HorizontalLayoutGroup)
│   │   ├── [RelicSlot] (미발견 = 물음표 실루엣)
│   │   ├── [RelicSlot] (발견됨 = 아이콘 + 빛나는 이펙트)
│   │   └── ...
│   ├── [ShelfRow_Rare]
│   └── [ShelfRow_Legendary]
├── [DetailPanel] (선택 시 확대 표시)
│   ├── [RelicIcon_Large]
│   ├── [RelicName]
│   └── [LoreText]
└── [ProgressLabel] ("발견 23 / 40")
```

### 4. RelicSlot 컴포넌트

```csharp
public class RelicSlot : MonoBehaviour, IPointerClickHandler
{
    [SerializeField] private Image iconImage;
    [SerializeField] private Image silhouetteImage;
    [SerializeField] private GameObject glowEffect;
    [SerializeField] private Image rarityBorder;

    private RelicData data;
    private TrophyRoomUI parentUI;

    public void Setup(RelicData relicData, TrophyRoomUI ui)
    {
        data = relicData;
        parentUI = ui;

        bool discovered = RelicDiscoveryManager.IsDiscovered(relicData.relicId);
        iconImage.gameObject.SetActive(discovered);
        silhouetteImage.gameObject.SetActive(!discovered);
        glowEffect.SetActive(discovered && relicData.rarity == RelicRarity.Legendary);

        if (discovered)
            iconImage.sprite = relicData.icon;

        rarityBorder.color = GetRarityColor(relicData.rarity);
    }

    public void OnPointerClick(PointerEventData eventData)
    {
        if (RelicDiscoveryManager.IsDiscovered(data.relicId))
            parentUI.ShowDetail(data);
    }

    Color GetRarityColor(RelicRarity rarity) => rarity switch
    {
        RelicRarity.Common    => new Color(0.7f, 0.7f, 0.7f),
        RelicRarity.Rare      => new Color(0.3f, 0.5f, 1.0f),
        RelicRarity.Legendary => new Color(1.0f, 0.8f, 0.1f),
        _ => Color.white
    };
}
```

### 5. 신규 발견 연출 (First Discovery Animation)

런 종료 후 Run Result Screen에서 "새로 발견된 유물" 강조 연출:

```csharp
public class NewRelicDiscoveryPopup : MonoBehaviour
{
    [SerializeField] private Image relicIcon;
    [SerializeField] private TextMeshProUGUI relicName;
    [SerializeField] private CanvasGroup canvasGroup;

    public IEnumerator ShowNewDiscovery(RelicData relic)
    {
        relicIcon.sprite = relic.icon;
        relicName.text = $"새 발견: {relic.displayName}";

        // 페이드 인
        canvasGroup.alpha = 0f;
        float t = 0f;
        while (t < 0.4f)
        {
            t += Time.deltaTime;
            canvasGroup.alpha = t / 0.4f;
            yield return null;
        }

        yield return new WaitForSeconds(2f);

        // 페이드 아웃
        t = 0f;
        while (t < 0.3f)
        {
            t += Time.deltaTime;
            canvasGroup.alpha = 1f - (t / 0.3f);
            yield return null;
        }

        gameObject.SetActive(false);
    }
}
```

### 6. 완성도 진행 표시 (Progress Bar)

```csharp
public void UpdateProgressBar()
{
    int total = allRelics.Count;
    int found = allRelics.Count(r => RelicDiscoveryManager.IsDiscovered(r.relicId));
    progressLabel.text = $"발견 {found} / {total}";
    progressBar.fillAmount = (float)found / total;

    if (found == total)
        ShowAllDiscoveredBanner(); // "컬렉션 완성!" 연출
}
```

---

## OnionCat 적용 포인트

### 1. "화분 선반" 테마 비주얼

- 트로피 룸 = 고양이 집 안 나무 선반
- 각 유물 = 작은 화분 / 씨앗 주머니 / 꽃 모양 오브젝트
- 미발견 슬롯 = 빈 화분 흙만 있는 상태 (물음표 대신 세계관 연결)
- 전설 유물 = 선반 위 조명이 비추는 황금 꽃 화분

### 2. 발견 트리거 — 런 중 유물 획득 즉시 저장

```csharp
// ItemPickupSystem.cs
public void OnRelicPickedUp(RelicData relic)
{
    if (!RelicDiscoveryManager.IsDiscovered(relic.relicId))
    {
        RelicDiscoveryManager.MarkDiscovered(relic.relicId);
        RunData.Instance.newDiscoveriesThisRun.Add(relic); // 런 결과 화면용
    }
}
```

### 3. Main Menu에서 접근 가능하도록

- 메인 메뉴 버튼: "화분 선반" (트로피 룸) → TrophyRoomScene 로드 or Additive 씬
- 컬렉션 진행도를 메인 메뉴 화면에 작은 뱃지로 표시 ("23/40")

### 4. 컬렉션 완성 보상

- 특정 카테고리 완성 → 새 런에서 해당 유물 더 자주 등장 (드롭률 보정)
- 전설 유물 전체 발견 → 특별 스킨 언락 (세계관 보상)

### 5. 구현 우선순위

1. `RelicData` ScriptableObject + 유물 목록 작성
2. `RelicDiscoveryManager` (PlayerPrefs 저장)
3. `RelicSlot` UI 구성 (발견/미발견 분기)
4. RunResult 화면에 신규 발견 표시 연동
5. Main Menu 진입 버튼 추가

---

## 참고 링크

- Hades — 관계 기록실 & 무기 기록 UI 레퍼런스: https://www.supergiantgames.com/games/hades/
- Dead Cells — 무기 갤러리 디자인: https://deadcells.fandom.com/wiki/Weapons
- Unity ScriptableObject 활용: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unity UI ScrollRect: https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-ScrollRect.html
- IPointerClickHandler 인터페이스: https://docs.unity3d.com/ScriptReference/EventSystems.IPointerClickHandler.html
