# Post-Launch Content Update Pipeline

리서치 날짜: 2026-10-13

## 개요

게임을 출시한 뒤에도 새 장비·방·적·스킬을 계속 추가하는 것은 인디 로그라이크에서 매우 흔한 패턴이다 (Hades, Dead Cells, Vampire Survivors 모두 출시 후 콘텐츠를 크게 확장함). OnionCat처럼 **ScriptableObject 기반 데이터 구조**를 가진 프로젝트는 이미 반은 준비된 상태이지만, 세이브 데이터 마이그레이션·게임 데이터베이스 재빌드·플레이어에게 새 콘텐츠를 보여주는 방식 같은 세부 파이프라인이 없으면 업데이트마다 버그가 터진다. 이 문서는 그 파이프라인을 정리한다.

---

## Unity 구현 방법

### 1. ScriptableObject 기반 콘텐츠 등록 시스템

OnionCat은 이미 `Assets/Data/Gear`에 ScriptableObject 장비가 있고, `RewardTable.asset`에 드롭 목록이 있다. 업데이트 친화적 구조의 핵심은 **명시적 ID 관리**다.

```csharp
// GearItem.cs — 기존 필드에 고유 ID 추가
[CreateAssetMenu(menuName = "OnionCat/GearItem")]
public class GearItem : ItemData
{
    // 출시 이후 절대 바꾸지 않는 고유 ID (세이브 데이터 키)
    [SerializeField] private string _guid;
    public string Guid => _guid;

#if UNITY_EDITOR
    [ContextMenu("Generate GUID")]
    private void GenerateGuid() => _guid = System.Guid.NewGuid().ToString("N")[..8];
#endif
}
```

- 에디터에서 새 장비 SO를 만들 때 우클릭 → "Generate GUID" 한 번으로 고유 ID 확보
- 이 ID를 세이브 데이터에 저장하면, SO 파일 이름·경로가 바뀌어도 세이브를 복원 가능

### 2. GameDatabase Rebuild 자동화

현재 OnionCat은 메뉴 **OnionCat > Rebuild Game Database**를 수동으로 실행해야 한다. CI/배포 전에 자동 실행하는 스크립트를 추가하면 "Rebuild 안 했다가 아이템이 없어진" 사고를 막는다.

```csharp
// DatabaseBuildMenuItem.cs
#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

// 빌드 시작 전 자동으로 데이터베이스 재빌드
public class AutoRebuildDatabase : IPreprocessBuildWithReport
{
    public int callbackOrder => 0;
    public void OnPreprocessBuild(BuildReport report)
    {
        GameDatabaseBuilder.RebuildAll(); // 기존 Rebuild 로직 호출
        Debug.Log("[Build] GameDatabase rebuilt before build.");
    }
}
#endif
```

### 3. 세이브 데이터 마이그레이션

새 필드(예: 새 장비 슬롯, 새 세트 종류)를 추가할 때 기존 세이브 파일이 깨지지 않도록 버전 관리가 필요하다.

```csharp
// SaveData.cs — 버전 필드 추가
[System.Serializable]
public class RunSaveData
{
    public int saveVersion = 1;  // 저장 시 현재 버전 기록
    
    // 기존 필드들...
    public List<string> equippedGearGuids = new();
}

// SaveManager.cs — 로드 시 마이그레이션
public RunSaveData LoadAndMigrate()
{
    var data = LoadRaw();
    if (data.saveVersion < 2) MigrateV1ToV2(data);
    if (data.saveVersion < 3) MigrateV2ToV3(data);
    return data;
}

private void MigrateV1ToV2(RunSaveData data)
{
    // v2에서 새 슬롯 추가 → 기존 세이브는 빈 슬롯으로 시작
    data.saveVersion = 2;
    Debug.Log("[Save] Migrated to v2");
}
```

**핵심 규칙**:
- 세이브 버전은 항상 올림 — 절대 내리지 않음
- 마이그레이션 함수는 추가만 — 기존 마이그레이션 코드는 삭제 금지
- 새 필드는 항상 기본값으로 초기화 (null/0/빈 리스트)

### 4. 새 콘텐츠 알림 (신규 아이템 알림 배지)

업데이트 후 처음 게임을 켰을 때 "새 장비가 추가됐습니다" 같은 안내를 보여주면 플레이어 재참여율이 높아진다.

```csharp
// NewContentNotifier.cs
public static class NewContentNotifier
{
    private const string PrefKey = "LastSeenDatabaseVersion";
    
    public static bool HasNewContent()
    {
        int lastSeen = PlayerPrefs.GetInt(PrefKey, 0);
        return GameDatabase.Instance.Version > lastSeen;
    }
    
    public static void MarkSeen()
    {
        PlayerPrefs.SetInt(PrefKey, GameDatabase.Instance.Version);
    }
}
```

- `GameDatabase.Instance.Version`은 Rebuild 시 SO 수로 자동 계산하거나 수동 관리
- 메인 메뉴 "도감" 버튼 옆에 빨간 점(badge)으로 표시

### 5. 패치 노트 화면

게임 내에서 간단한 패치 노트를 보여주는 화면:

```csharp
// PatchNotes.cs — Resources 폴더에 텍스트 파일로 관리
public class PatchNotesScreen : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI textField;
    
    void Start()
    {
        var asset = Resources.Load<TextAsset>("PatchNotes/Latest");
        if (asset != null) textField.text = asset.text;
    }
}
```

`Resources/PatchNotes/Latest.txt`에 마크다운 형식으로 작성 → 코드 수정 없이 텍스트 파일만 교체해서 업데이트 가능.

---

## OnionCat 적용 포인트

### 현재 구조와의 연결

- OnionCat은 이미 `GameDatabase` 개념이 있고 "Rebuild Game Database" 메뉴가 있다
- `RunData`에 런 상태를 모아두는 구조도 마이그레이션에 유리하다
- **당장 해야 할 것**: 장비 SO에 `_guid` 필드 추가 + 에디터 메뉴로 생성. 세이브에 GUID 목록으로 장비 저장하도록 교체

### 새 장비 추가 워크플로우 (업데이트 시)

```
1. Assets/Data/Gear/ 에 새 GearItem SO 생성
2. "Generate GUID" 실행
3. RewardTable.asset 의 해당 축 목록에 추가
4. OnionCat > Rebuild Game Database 실행 (또는 빌드 시 자동 실행)
5. saveVersion 올리기 (새 슬롯 추가 시에만)
6. Resources/PatchNotes/Latest.txt 업데이트
7. 빌드 → 배포
```

### 세이브 데이터 안전성 우선순위

| 변경 종류 | 마이그레이션 필요? |
|----------|-----------------|
| 새 장비 추가 | ✗ (빈 슬롯으로 시작하면 됨) |
| 장비 능력치 변경 | ✗ (코드만 변경, 저장값 없음) |
| 새 장비 슬롯 추가 | ✓ (기존 세이브에 빈 슬롯 삽입) |
| 세트 종류 추가 | ✗ (기존 세트와 독립) |
| RunData 구조 변경 | ✓ (기존 런 세이브 마이그레이션) |

### 전설 장비 추가 대비

현재 전설 장비 0개 → 향후 추가 예정. 전설은 "빌드를 바꾸는 고유 효과"를 가지므로 코드 연동이 필요하다. 미래 전설 효과가 SaveData에 영향을 준다면 지금부터 GUID 체계를 갖춰두는 것이 훨씬 안전하다.

---

## 참고 링크

- Unity ScriptableObject best practices: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Save Data Migration patterns (Unity blog): https://blog.unity.com/games/saving-game-state-best-practices
- Dead Cells post-launch content approach (GDC): https://www.gdcvault.com/play/1025776
- Semantic versioning for game saves: https://semver.org
