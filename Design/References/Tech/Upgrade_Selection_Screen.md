# 업그레이드 선택 화면 (Mid-Run Upgrade Pick Screen)

리서치 날짜: 2026-06-27

## 개요
로그라이크의 핵심 피드백 루프 중 하나: **방 클리어 → 업그레이드 선택 → 다음 방**. 플레이어가 "내 빌드를 직접 만든다"는 감각을 주는 가장 중요한 인터페이스다.

Hades의 신의 축복, The Binding of Isaac의 아이템 방, Dead Cells의 블루프린트 선택이 모두 이 화면의 구현 예시다.

OnionCat에서 중요한 이유:
- Cat(P1)과 Crop(P2)이 각자 업그레이드를 선택하거나, 같이 상의해서 하나를 고르는 장면 자체가 협동 경험
- 업그레이드 화면의 느낌(연출, 텍스트, 카드 수)이 게임의 "쥬스(Juice)"를 좌우함

---

## Unity 구현 방법

### 1. 전체 흐름
```
방 클리어 이벤트 발생
    → 모든 적 사망 확인
    → 문이 열리기 전에 업그레이드 화면 표시
    → 플레이어가 업그레이드 선택
    → 화면 닫기 + 업그레이드 적용
    → 문 열림 + 이동 가능
```

### 2. UpgradeSelectionUI 구조
```
Canvas (Screen Space - Overlay)
  └── UpgradePanel (GameObject)
        ├── Background (반투명 검정 패널)
        ├── TitleText ("업그레이드를 선택하세요!")
        ├── CardContainer (Horizontal Layout Group)
        │     ├── UpgradeCard_0
        │     ├── UpgradeCard_1
        │     └── UpgradeCard_2
        └── SkipButton (optional: "다음에", 패널티 없이 패스)
```

### 3. UpgradeCard 컴포넌트
```csharp
public class UpgradeCard : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
{
    [SerializeField] private Image iconImage;
    [SerializeField] private TMP_Text titleText;
    [SerializeField] private TMP_Text descriptionText;
    [SerializeField] private TMP_Text rarityText;

    private UpgradeData upgradeData;
    private System.Action<UpgradeData> onSelected;

    public void Initialize(UpgradeData data, System.Action<UpgradeData> callback)
    {
        upgradeData = data;
        onSelected = callback;
        iconImage.sprite = data.icon;
        titleText.text = data.upgradeName;
        descriptionText.text = data.description;
        rarityText.text = data.rarity.ToString();
        rarityText.color = GetRarityColor(data.rarity);
    }

    public void OnPointerEnter(PointerEventData e) =>
        transform.DOScale(1.05f, 0.1f);

    public void OnPointerExit(PointerEventData e) =>
        transform.DOScale(1.0f, 0.1f);

    public void OnClickCard() => onSelected?.Invoke(upgradeData);

    private Color GetRarityColor(UpgradeRarity r) => r switch {
        UpgradeRarity.Common   => Color.white,
        UpgradeRarity.Rare     => new Color(0.3f, 0.5f, 1f),
        UpgradeRarity.Epic     => new Color(0.7f, 0.3f, 1f),
        _ => Color.white
    };
}
```

### 4. UpgradeData (ScriptableObject)
```csharp
[CreateAssetMenu(fileName = "UpgradeData", menuName = "OnionCat/Upgrade")]
public class UpgradeData : ScriptableObject
{
    public string upgradeName;
    [TextArea] public string description;
    public Sprite icon;
    public UpgradeRarity rarity;
    public UpgradeTarget target; // Cat, Crop, Both
    public UpgradeType type;    // Stat, Ability, Passive
    public float value;         // 수치 업그레이드일 경우
}

public enum UpgradeRarity  { Common, Rare, Epic }
public enum UpgradeTarget  { Cat, Crop, Both }
public enum UpgradeType    { DamageUp, SpeedUp, CooldownDown, NewAbility, Passive }
```

### 5. UpgradeSelectionManager
```csharp
public class UpgradeSelectionManager : MonoBehaviour
{
    [SerializeField] private GameObject upgradePanel;
    [SerializeField] private UpgradeCard[] cards;
    [SerializeField] private UpgradeDatabase upgradeDatabase;

    public void ShowUpgradeSelection()
    {
        Time.timeScale = 0f;                    // 게임 일시정지
        upgradePanel.SetActive(true);

        var options = upgradeDatabase.GetRandomUpgrades(3); // 가중치 랜덤 3개
        for (int i = 0; i < cards.Length; i++)
            cards[i].Initialize(options[i], OnUpgradeSelected);

        // DOTween: 패널 페이드인 (Time.timeScale=0이므로 SetUpdate(true) 필수!)
        upgradePanel.GetComponent<CanvasGroup>().alpha = 0f;
        upgradePanel.GetComponent<CanvasGroup>()
            .DOFade(1f, 0.3f)
            .SetUpdate(true);  // ← Time.timeScale=0f 상태에서도 작동
    }

    private void OnUpgradeSelected(UpgradeData upgrade)
    {
        ApplyUpgrade(upgrade);
        upgradePanel.GetComponent<CanvasGroup>()
            .DOFade(0f, 0.2f)
            .SetUpdate(true)
            .OnComplete(() => {
                upgradePanel.SetActive(false);
                Time.timeScale = 1f;          // 게임 재개
            });
    }

    private void ApplyUpgrade(UpgradeData upgrade)
    {
        // 업그레이드 적용 로직 (PlayerStats, AbilityManager 등에 전달)
        UpgradeApplier.Apply(upgrade);
        // 현재 런의 업그레이드 기록 저장
        RunData.Instance.AddUpgrade(upgrade);
    }
}
```

### 6. 가중치 랜덤 선택 (UpgradeDatabase)
```csharp
public class UpgradeDatabase : MonoBehaviour
{
    [SerializeField] private List<UpgradeData> allUpgrades;

    public List<UpgradeData> GetRandomUpgrades(int count)
    {
        // 이미 보유한 업그레이드 제외 + 희귀도별 가중치 적용
        var pool = allUpgrades
            .Where(u => !RunData.Instance.HasUpgrade(u))
            .ToList();

        var result = new List<UpgradeData>();
        var shuffled = pool.OrderBy(_ => Random.value).ToList(); // 단순 셔플
        // 실제로는 가중치 기반 뽑기 권장 (Random_Generation.md 참고)
        for (int i = 0; i < Mathf.Min(count, shuffled.Count); i++)
            result.Add(shuffled[i]);

        return result;
    }
}
```

### 7. 핵심 주의사항
- `Time.timeScale = 0f`로 일시정지 시, `DOTween`은 **`.SetUpdate(true)`** 없으면 멈춤
- `Time.timeScale` 복구(`= 1f`)를 OnComplete 콜백 안에서 하지 않으면 게임이 계속 정지 상태
- 업그레이드 선택 도중 씬 전환 이벤트가 발생하면 패널이 남아있는 버그 — `OnDestroy`에서 `Time.timeScale = 1f` 방어 코드 추가

---

## OnionCat 적용 포인트

### A. Cat / Crop 독립 업그레이드 vs 공동 업그레이드
- **방식 1**: 방 클리어 후 Cat/Crop 각자 별도 화면에서 선택 (4~6초 소요)
- **방식 2**: 3가지 업그레이드 중 한 명이 선택 → 상대에게도 효과 적용
- **추천**: 방식 2로 시작. 상의하며 고르는 과정이 협동 경험. 카드 좌측엔 Cat 아이콘, 우측엔 Crop 아이콘으로 "누구에게 영향을 주는지" 표시

### B. 카드 3장 구성 비율
- **Common 2장 + Rare 1장**: 런 초반
- **Rare 2장 + Epic 1장**: 런 중반 (3~5층)
- **Epic 2장 + Unique 1장**: 런 후반 (보스 전)

### C. 업그레이드 선택 카드 등장 연출 (DOTween 연계)
```csharp
// DOTween_Animation_System.md 의 Sequence 패턴 활용
for (int i = 0; i < 3; i++) {
    int idx = i;
    cards[idx].transform.localPosition = new Vector3(0, 800, 0);
    cards[idx].transform.DOLocalMoveY(0, 0.4f)
        .SetEase(Ease.OutBack)
        .SetDelay(idx * 0.12f)
        .SetUpdate(true); // timeScale=0 대응
}
```

### D. "다시 굴리기" 메타 업그레이드
- 런 중 획득 가능한 특수 아이템 "재추첨권" 보유 시 카드 3장 다시 뽑기
- `UpgradeSelectionManager`에 `RerollCount` 변수 + 버튼 활성화/비활성화 로직 추가
- Hades의 "신의 선물 재추첨" 시스템 참고

### E. 업그레이드 이력 표시 (런 결과 화면 연계)
- `RunData.Instance.upgrades` 리스트에 선택한 업그레이드 순서대로 저장
- 게임 오버/클리어 화면에서 이 이력을 타임라인 형태로 표시
- `Run_Result_Screen.md` 참고

---

## 참고 링크
- Unity UI 공식 문서: https://docs.unity3d.com/Manual/UISystem.html
- ScriptableObject 활용: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- DOTween SetUpdate 공식 문서: http://dotween.demigiant.com/documentation.php#creatingTweener
- Hades 업그레이드 UI 분석 (영상): YouTube "Hades boon system design breakdown"
- 로그라이크 업그레이드 UX 분석: https://www.gamedeveloper.com/design/designing-roguelike-upgrade-systems
