# 로어 코덱스 / 내부 백과사전 화면

리서치 날짜: 2026-08-03

## 개요

플레이어가 게임 내에서 발견한 캐릭터, 적, 아이템, 세계관 정보를 언제든 볼 수 있는 **인게임 사전 화면**. Hades의 코덱스(Codex), The Binding of Isaac의 Paper (아이템 설명), Slay the Spire의 카드 설명 시스템 등에서 확인 가능.

**OnionCat에 필요한 이유**:
- 아이템/업그레이드가 많아질수록 플레이어가 효과를 잊음
- Cat과 Onion의 스토리 배경을 자연스럽게 전달
- 적의 약점(근접/원거리) 정보를 플레이어가 직접 확인
- 게임 완성도 지표 — "이 게임에는 세계가 있다"는 느낌 제공

---

## Unity 구현 방법

### 1단계: 코덱스 항목 ScriptableObject 정의

```csharp
// CodexEntrySO.cs
using UnityEngine;

[CreateAssetMenu(menuName = "OnionCat/Codex Entry")]
public class CodexEntrySO : ScriptableObject {
    public string entryId;          // "cat_background", "slime_enemy" 등 고유 키
    public string displayName;      // "고양이 (Cat)"
    public CodexCategory category;  // Characters, Enemies, Items, World
    [TextArea(3, 8)]
    public string description;      // 설명 텍스트
    public Sprite illustration;     // 픽셀아트 일러스트
    public bool unlockedByDefault;  // true면 처음부터 해금
}

public enum CodexCategory {
    Characters,
    Enemies,
    Items,
    World
}
```

### 2단계: 코덱스 해금 매니저

```csharp
// CodexManager.cs
using System.Collections.Generic;
using UnityEngine;

public class CodexManager : MonoBehaviour {
    private static CodexManager _instance;
    public static CodexManager Instance => _instance;
    
    [SerializeField] private CodexEntrySO[] allEntries;
    
    // 세이브 데이터에 저장될 해금 목록
    private HashSet<string> unlockedIds = new HashSet<string>();
    
    void Awake() {
        if (_instance != null) { Destroy(gameObject); return; }
        _instance = this;
        DontDestroyOnLoad(gameObject);
        
        // 기본 해금 항목 적용
        foreach (var entry in allEntries)
            if (entry.unlockedByDefault) unlockedIds.Add(entry.entryId);
        
        LoadFromSave();
    }
    
    // 외부에서 호출: 새 항목 해금
    public bool TryUnlock(string entryId) {
        if (unlockedIds.Contains(entryId)) return false;
        unlockedIds.Add(entryId);
        SaveToFile();
        // 토스트 알림 (Toast_Notification_System 연동)
        ToastNotificationManager.Show($"코덱스 업데이트: {GetEntry(entryId)?.displayName}");
        return true;
    }
    
    public bool IsUnlocked(string entryId) => unlockedIds.Contains(entryId);
    
    public CodexEntrySO GetEntry(string id) {
        foreach (var e in allEntries) if (e.entryId == id) return e;
        return null;
    }
    
    public List<CodexEntrySO> GetUnlockedByCategory(CodexCategory cat) {
        var result = new List<CodexEntrySO>();
        foreach (var e in allEntries)
            if (e.category == cat && unlockedIds.Contains(e.entryId)) result.Add(e);
        return result;
    }
    
    private void SaveToFile() {
        string json = JsonUtility.ToJson(new SerializableStringArray(unlockedIds));
        System.IO.File.WriteAllText(
            Application.persistentDataPath + "/codex_save.json", json);
    }
    
    private void LoadFromSave() {
        string path = Application.persistentDataPath + "/codex_save.json";
        if (!System.IO.File.Exists(path)) return;
        var data = JsonUtility.FromJson<SerializableStringArray>(
            System.IO.File.ReadAllText(path));
        foreach (var id in data.ids) unlockedIds.Add(id);
    }
    
    [System.Serializable]
    private class SerializableStringArray {
        public List<string> ids;
        public SerializableStringArray(HashSet<string> set) => ids = new List<string>(set);
    }
}
```

### 3단계: 코덱스 해금 트리거 (게임 이벤트 연동)

```csharp
// 적 처치 시 코덱스 해금 예시 (EnemyHealth.cs 내)
void Die() {
    CodexManager.Instance?.TryUnlock(codexEntryId); // [SerializeField] string codexEntryId
    // 드롭, 방 클리어 처리 등...
}

// 아이템 픽업 시 (ItemPickup.cs 내)
void OnPickup() {
    CodexManager.Instance?.TryUnlock(itemSO.codexEntryId);
}
```

### 4단계: 코덱스 UI 화면

```csharp
// CodexUI.cs
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class CodexUI : MonoBehaviour {
    [SerializeField] private GameObject codexPanel;
    [SerializeField] private Transform categoryButtonContainer;
    [SerializeField] private Transform entryListContainer;
    [SerializeField] private GameObject entryButtonPrefab;
    
    // 상세 보기 영역
    [SerializeField] private Image illustration;
    [SerializeField] private TMP_Text nameText;
    [SerializeField] private TMP_Text descriptionText;
    
    private CodexCategory currentCategory = CodexCategory.Characters;
    
    public void Open() {
        codexPanel.SetActive(true);
        ShowCategory(CodexCategory.Characters);
    }
    
    public void Close() => codexPanel.SetActive(false);
    
    public void ShowCategory(CodexCategory cat) {
        currentCategory = cat;
        
        // 기존 목록 클리어
        foreach (Transform child in entryListContainer) Destroy(child.gameObject);
        
        var entries = CodexManager.Instance.GetUnlockedByCategory(cat);
        foreach (var entry in entries) {
            var btn = Instantiate(entryButtonPrefab, entryListContainer);
            btn.GetComponentInChildren<TMP_Text>().text = entry.displayName;
            btn.GetComponent<Button>().onClick.AddListener(() => ShowEntry(entry));
        }
        
        // 첫 번째 항목 자동 선택
        if (entries.Count > 0) ShowEntry(entries[0]);
    }
    
    private void ShowEntry(CodexEntrySO entry) {
        illustration.sprite = entry.illustration;
        nameText.text = entry.displayName;
        descriptionText.text = entry.description;
    }
}
```

### 5단계: 메인 메뉴 / 일시정지에서 코덱스 접근

```csharp
// PauseMenu.cs에 추가
[SerializeField] private CodexUI codexUI;
[SerializeField] private Button codexButton;

void Awake() {
    codexButton.onClick.AddListener(() => {
        // 일시정지 메뉴 숨기고 코덱스 표시
        codexUI.Open();
    });
}
```

---

## OnionCat 적용 포인트

### 코덱스 카테고리 설계

| 카테고리 | 항목 예시 | 해금 조건 |
|---------|----------|---------|
| **Characters** | Cat 배경 이야기, Onion 배경 이야기 | 게임 시작 시 기본 해금 |
| **Enemies** | 슬라임 적, 탄막 새 적, 보스 A | 해당 적 첫 처치 시 |
| **Items** | 씨앗 발사체 업그레이드, 대시 강화 | 아이템 첫 획득 시 |
| **World** | 정원 세계관, 적들의 정체 | 특정 층 클리어 시 |

### 적 약점 정보 표시
OnionCat 핵심 필라(적마다 근접/원거리 약점) → 코덱스에서 확인 가능:

```csharp
// CodexEntrySO에 추가 필드
public WeaknessType weakness; // Melee, Ranged, Both, None
public string weaknessNote;   // "이 적은 원거리 공격에만 피해를 받습니다"
```

적을 처음 만났을 때는 코덱스에 `???` 로 약점 숨김, 처치 후 공개 → 탐험 동기 부여.

### 미니멀 구현 전략 (초보 개발자)
1. ScriptableObject에 텍스트만 먼저 작성 (이미지 없이)
2. 일시정지 메뉴에 "코덱스" 버튼 1개 추가
3. 스크롤 뷰 + TextMeshPro로 단순 구현
4. 추후 일러스트 추가하며 폴리싱

**최소 필요 항목**:
- Cat 설명 1개
- Onion 설명 1개  
- 기본 적 3~5종 설명

---

## 참고 링크

- Hades Codex 디자인 분석: https://www.youtube.com/watch?v=bLSTMmplDJ8 (GDC Talk)
- Unity ScriptableObject 활용 가이드: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unity UI 스크롤 뷰: https://docs.unity3d.com/Manual/UIE-uxml-element-ScrollView.html
- TextMeshPro 공식 문서: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
