# Save Slot Selection Screen

리서치 날짜: 2026-10-02

## 개요

게임 시작 시 여러 저장 슬롯 중 하나를 고르거나 새 슬롯을 만드는 화면.
"세이브/로드 시스템"(데이터 영속성)과 다르게, 이것은 **유저가 슬롯을 눈으로 보고 선택하는 UX 레이어**다.

OnionCat에 필요한 이유:
- 두 플레이어가 서로 다른 메타 진행을 갖고 싶을 수 있음
- 테스트 슬롯 따로 두기, 새 런 시작 슬롯 분리 등 QOL
- 데모 빌드에서 "항상 새 슬롯으로" 강제 가능

---

## Unity 구현 방법

### 1. 저장 데이터 구조

```csharp
// SaveSlotData.cs
[Serializable]
public class SaveSlotData
{
    public bool isEmpty = true;
    public string slotName;          // "Player 1", "New Run" 등
    public int totalRuns;
    public int totalKills;
    public float totalPlayTime;      // 초 단위
    public DateTime lastPlayed;
    public string lastUnlockedItem;  // 미리보기용
}
```

### 2. 슬롯 파일 저장/로드

```csharp
// SaveSlotManager.cs
public class SaveSlotManager : MonoBehaviour
{
    public const int SlotCount = 3;
    private static readonly string SaveDir = Application.persistentDataPath + "/saves/";

    public static void SaveSlot(int slotIndex, SaveSlotData data)
    {
        Directory.CreateDirectory(SaveDir);
        string json = JsonUtility.ToJson(data, true);
        File.WriteAllText(GetSlotPath(slotIndex), json);
    }

    public static SaveSlotData LoadSlot(int slotIndex)
    {
        string path = GetSlotPath(slotIndex);
        if (!File.Exists(path)) return new SaveSlotData { isEmpty = true };
        
        try
        {
            string json = File.ReadAllText(path);
            return JsonUtility.FromJson<SaveSlotData>(json);
        }
        catch { return new SaveSlotData { isEmpty = true }; }
    }

    public static void DeleteSlot(int slotIndex)
    {
        string path = GetSlotPath(slotIndex);
        if (File.Exists(path)) File.Delete(path);
    }

    private static string GetSlotPath(int index) => $"{SaveDir}slot_{index}.json";

    // 현재 선택된 슬롯 (씬 간 유지)
    public static int ActiveSlotIndex { get; private set; } = -1;
    public static void SetActiveSlot(int index) => ActiveSlotIndex = index;
}
```

### 3. UI 슬롯 카드 컴포넌트

```csharp
// SaveSlotCard.cs
public class SaveSlotCard : MonoBehaviour
{
    [SerializeField] private TMP_Text slotNameText;
    [SerializeField] private TMP_Text statsText;
    [SerializeField] private TMP_Text lastPlayedText;
    [SerializeField] private Button selectButton;
    [SerializeField] private Button deleteButton;
    [SerializeField] private GameObject emptyPanel;   // 빈 슬롯 UI
    [SerializeField] private GameObject dataPanel;    // 데이터 있는 슬롯 UI

    private int slotIndex;

    public void Setup(int index, SaveSlotData data)
    {
        slotIndex = index;
        
        bool isEmpty = data.isEmpty;
        emptyPanel.SetActive(isEmpty);
        dataPanel.SetActive(!isEmpty);
        deleteButton.gameObject.SetActive(!isEmpty);

        if (!isEmpty)
        {
            slotNameText.text = data.slotName;
            statsText.text = $"Runs: {data.totalRuns}  Kills: {data.totalKills}";
            lastPlayedText.text = data.lastPlayed.ToString("yyyy-MM-dd");
        }

        selectButton.onClick.RemoveAllListeners();
        selectButton.onClick.AddListener(OnSelect);

        deleteButton.onClick.RemoveAllListeners();
        deleteButton.onClick.AddListener(OnDelete);
    }

    private void OnSelect()
    {
        SaveSlotManager.SetActiveSlot(slotIndex);
        SceneManager.LoadScene(SceneNames.RunStart); // 또는 CharacterSelect
    }

    private void OnDelete()
    {
        // 확인 다이얼로그 먼저 (Game_Exit_Confirm_Dialog 패턴 재사용)
        ConfirmDialog.Show("Delete this save?", () =>
        {
            SaveSlotManager.DeleteSlot(slotIndex);
            Setup(slotIndex, new SaveSlotData { isEmpty = true });
        });
    }
}
```

### 4. 슬롯 선택 씬 매니저

```csharp
// SlotSelectScreen.cs
public class SlotSelectScreen : MonoBehaviour
{
    [SerializeField] private SaveSlotCard[] slotCards; // Inspector에서 3개 할당

    void Start()
    {
        for (int i = 0; i < SaveSlotManager.SlotCount; i++)
        {
            var data = SaveSlotManager.LoadSlot(i);
            slotCards[i].Setup(i, data);
        }
    }
}
```

### 5. 씬 흐름

```
MainMenu
    └─► SlotSelectScreen  ← 새 게임 버튼
            ├─ 빈 슬롯 클릭 → 슬롯 이름 입력(선택) → RunStart
            ├─ 기존 슬롯 클릭 → RunStart (이어하기)
            └─ 슬롯 삭제 → 확인 다이얼로그 → 슬롯 초기화
```

### 6. 게임패드 내비게이션

```csharp
// 슬롯 카드 사이 gamepad 이동
// EventSystem + Navigation 자동 설정
slotCards[0].selectButton.navigation = new Navigation
{
    mode = Navigation.Mode.Explicit,
    selectOnRight = slotCards[1].selectButton
};
// ... (Gamepad_UI_Navigation_System 참고)
```

---

## OnionCat 적용 포인트

### 1. 슬롯 3개로 시작
3개면 "내 슬롯 / 테스트 슬롯 / 공용 슬롯" 용도 분리 가능.
나중에 최대 슬롯 수는 `SlotCount` 상수 하나만 바꾸면 됨.

### 2. 두 플레이어 공유 슬롯
Cat(Player1)+Onion(Player2) 조합이 슬롯에 묶여 있으면 다음 런에서 같은 슬롯 계속 사용.
`SaveSlotData`에 `cumulativeUnlocks[]` 같은 메타 진행 필드 추가 가능.

### 3. 데모 빌드 분기
```csharp
#if DEMO_BUILD
    // 슬롯 선택 화면 건너뛰고 슬롯 0 강제
    SaveSlotManager.SetActiveSlot(0);
    SaveSlotManager.DeleteSlot(0); // 항상 새 런
    SceneManager.LoadScene(SceneNames.RunStart);
    return;
#endif
```

### 4. 빠른 구현 순서 (초보자용)
1. `SaveSlotManager` 정적 클래스 작성
2. `SlotSelectScreen` 씬 생성 (MainMenu 씬 복사 후 정리)
3. `SaveSlotCard` 프리팹 3개 배치 (HorizontalLayoutGroup 사용)
4. MainMenu "New Game" 버튼 → SlotSelectScreen 씬 이동으로 변경
5. 실제 런 데이터와 연결은 나중에 (`isEmpty=false` 처리부터)

---

## 참고 링크

- Unity Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- JsonUtility: https://docs.unity3d.com/ScriptReference/JsonUtility.html
- Unity UI Navigation: https://docs.unity3d.com/Manual/UIE-focus-navigation.html
- Hades 세이브 슬롯 UX 분석: https://www.youtube.com/results?search_query=hades+save+slot+ui+design
- 데모 빌드 분기 기법: Design/References/Tech/GameJam_Demo_Build_Config.md 참고
