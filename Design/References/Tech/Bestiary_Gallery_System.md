# 도감/갤러리 시스템 (Bestiary / Gallery)

리서치 날짜: 2026-07-03

## 개요
도감 시스템은 플레이어가 게임 내에서 처음 마주친 적·아이템·환경을 수집 가능한 항목으로 기록하는 기능이다. Hades의 "Codex", Hollow Knight의 "Hunter's Journal", Binding of Isaac의 "Bestiary"가 대표 예시다.

OnionCat에서는 여러 런을 반복하면서 적과 아이템을 조금씩 알아가는 **발견의 재미**를 제공하고, 동시에 OnionCat의 핵심 메카닉인 **적 약점 정보**를 자연스럽게 점진적으로 공개하는 메타 진행 축으로 활용할 수 있다.

---

## Unity 구현 방법

### 1. 데이터 구조 (ScriptableObject)

```csharp
// EnemyData.cs
[CreateAssetMenu(menuName = "OnionCat/EnemyData")]
public class EnemyData : ScriptableObject
{
    public string enemyId;       // 고유 식별자 (저장 키로 사용)
    public string enemyName;
    public Sprite portrait;
    public string weakness;      // "melee" / "ranged" / "both"
    [TextArea] public string description;
    [TextArea] public string lore;  // 10회 처치 후 공개
}
```

```csharp
// BestiaryEntry.cs — 런타임 상태 (JSON 저장)
[System.Serializable]
public class BestiaryEntry
{
    public string enemyId;
    public bool discovered;       // 첫 조우 시 잠금 해제
    public int killCount;         // 누적 처치 수
    public bool fullyUnlocked;    // 일정 처치 후 상세 정보 공개
}
```

### 2. BestiaryManager 싱글톤

```csharp
// BestiaryManager.cs
using System.Collections.Generic;
using System.IO;
using UnityEngine;

public class BestiaryManager : MonoBehaviour
{
    public static BestiaryManager Instance { get; private set; }

    [SerializeField] private List<EnemyData> allEnemies;

    private Dictionary<string, BestiaryEntry> entries = new();
    private const int KILLS_FOR_FULL_UNLOCK = 10;
    private string SavePath => Path.Combine(Application.persistentDataPath, "bestiary.json");

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        LoadEntries();
    }

    public void RegisterEncounter(string enemyId)
    {
        if (!entries.TryGetValue(enemyId, out var entry))
        {
            entry = new BestiaryEntry { enemyId = enemyId };
            entries[enemyId] = entry;
        }

        if (!entry.discovered)
        {
            entry.discovered = true;
            NotifyNewEntry(enemyId);
        }
    }

    public void RegisterKill(string enemyId)
    {
        RegisterEncounter(enemyId);
        var entry = entries[enemyId];
        entry.killCount++;
        if (entry.killCount >= KILLS_FOR_FULL_UNLOCK)
            entry.fullyUnlocked = true;
        SaveEntries();
    }

    public BestiaryEntry GetEntry(string enemyId)
        => entries.TryGetValue(enemyId, out var e) ? e : null;

    private void NotifyNewEntry(string enemyId)
    {
        // TODO: UI에 "새 도감 항목!" 팝업 표시
        Debug.Log($"[Bestiary] New entry discovered: {enemyId}");
    }

    private void SaveEntries()
    {
        var list = new List<BestiaryEntry>(entries.Values);
        var json = JsonUtility.ToJson(new BestiaryEntryList { entries = list });
        File.WriteAllText(SavePath, json);
    }

    private void LoadEntries()
    {
        if (!File.Exists(SavePath)) return;
        var json = File.ReadAllText(SavePath);
        var list = JsonUtility.FromJson<BestiaryEntryList>(json);
        foreach (var e in list.entries)
            entries[e.enemyId] = e;
    }

    [System.Serializable]
    private class BestiaryEntryList { public List<BestiaryEntry> entries; }
}
```

### 3. 적 사망 시 도감 연결

```csharp
// Enemy.cs (기존 적 클래스에 추가)
[SerializeField] private EnemyData enemyData;

void OnDeath()
{
    BestiaryManager.Instance?.RegisterKill(enemyData.enemyId);
    // ... 기존 사망 처리 (드롭, 파티클 등)
}

void OnFirstSight()  // 플레이어 시야에 처음 들어올 때
{
    BestiaryManager.Instance?.RegisterEncounter(enemyData.enemyId);
}
```

### 4. 도감 UI 구성

```
Canvas
└── BestiaryPanel
    ├── GridLayoutGroup — 적 아이콘 격자
    │   └── BestiaryEntryButton (×N)
    │       ├── Portrait (Image)
    │       ├── LockOverlay (Image, alpha 0.7) — 미발견 시 어둡게
    │       └── KillCountText (TextMeshPro)
    └── DetailPanel — 선택 시 우측 상세 표시
        ├── PortraitLarge
        ├── NameText
        ├── WeaknessIcon  ← OnionCat 핵심: 칼/씨앗 아이콘
        ├── DescriptionText
        └── LoreText (fullyUnlocked 시 표시)
```

### 5. 단계적 정보 공개 (Progressive Disclosure)

```csharp
public string GetDisplayName(BestiaryEntry entry, EnemyData data)
{
    if (entry == null || !entry.discovered) return "???";
    return data.enemyName;
}

public Sprite GetWeaknessIcon(BestiaryEntry entry, Sprite knifeIcon, Sprite seedIcon, Sprite unknownIcon)
{
    if (entry == null || !entry.discovered) return unknownIcon;  // "???"
    if (entry.killCount < 1) return unknownIcon;
    return data.weakness == "melee" ? knifeIcon : seedIcon;      // 첫 처치 후 공개
}

public string GetDescription(BestiaryEntry entry, EnemyData data)
{
    if (entry == null || !entry.discovered) return "아직 만난 적 없습니다.";
    if (entry.killCount < 1) return "처음 조우했습니다.";
    if (!entry.fullyUnlocked) return data.description;
    return data.description + "\n\n" + data.lore;               // 10회 처치 후 Lore 공개
}
```

단계 요약:
| 단계 | 조건 | 공개 정보 |
|------|------|-----------|
| 미발견 | 아직 못 만남 | 이름 "???", 실루엣만 |
| 발견 | 첫 조우 | 이름 + 외형 잠금 해제 |
| 처치 1회 | 첫 처치 | 약점 아이콘 공개 |
| 처치 10회 | fullyUnlocked | 배경 이야기(Lore) 공개 |

---

## OnionCat 적용 포인트

### 약점 발견 루프 연동
도감을 OnionCat의 핵심 메카닉 "약점 발견"과 연결:
- **첫 조우**: 적 머리 위 약점 아이콘 "???" — 직접 시도해야 약점 파악
- **첫 처치 후**: 도감에 약점 아이콘 공개 → 다음 런부터 미리 알고 대처
- **10회 처치 후**: 행동 패턴 상세, 특수 조건(분노 전환 등) 공개

→ "몰라서 죽었던 적"이 다음 런의 준비 목표가 됨 → **런 반복 동기 강화**

### 메타 진행 연결 제안
```
도감 달성 조건 → 영구 보상 예시:
- "10종 이상 발견" → 특별 시작 아이템 잠금 해제
- "특정 적 50회 처치" → 그 적의 능력 모방 업그레이드 잠금 해제
- "모든 적 발견 완료" → 히든 적 또는 도전 방 해금
```

### 구현 우선순위 (단계별)
1. `EnemyData` ScriptableObject 모든 적에 대해 생성
2. `BestiaryManager` 싱글톤 구현 + JSON 저장
3. `Enemy.OnDeath()`에서 `RegisterKill()` 연결
4. 메인 메뉴 또는 런 시작 전 로비에 도감 패널 UI 추가
5. 약점 아이콘 단계적 공개 로직 적용

---

## 참고 링크
- Hades Codex 디자인 분석: https://www.gamedeveloper.com/design/the-design-of-hades
- Hollow Knight Hunter's Journal: https://hollowknight.fandom.com/wiki/Hunter%27s_Journal
- Unity ScriptableObject 공식 문서: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unity GridLayoutGroup (UI): https://docs.unity3d.com/Manual/script-GridLayoutGroup.html
- Unity Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
