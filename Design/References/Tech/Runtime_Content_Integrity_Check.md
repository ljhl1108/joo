# 런타임 콘텐츠 무결성 검사 시스템

리서치 날짜: 2026-10-19

## 개요

혼자 개발하는 게임은 새 기능을 추가하다 **"전에 잘 되던 부분이 조용히 깨지는"** 문제가 잦다.
빌드를 뒤늦게 실행해 보면 보스 BGM이 없거나 아이콘이 missing이거나 DB에서 장비를 못 찾는 경우가 생긴다.

이 시스템은 게임 시작 직후(또는 빌드 시) **모든 핵심 데이터가 올바르게 연결되어 있는지 자동으로 검사**하고,
문제가 있으면 디버그 로그(또는 인게임 오버레이)로 즉시 알려준다.

---

## Unity 구현 방법

### 1. IIntegrityCheck 인터페이스

```csharp
public interface IIntegrityCheck
{
    string CheckName { get; }
    bool Run(out string errorMessage);
}
```

### 2. 검사 항목 구현 예시

```csharp
// 장비 DB에 null 참조가 있는지 확인
public class GearDatabaseCheck : IIntegrityCheck
{
    public string CheckName => "GearDatabase NullRef";
    public bool Run(out string errorMessage)
    {
        var db = Resources.Load<GameDatabase>("GameDatabase");
        if (db == null) { errorMessage = "GameDatabase 리소스 없음"; return false; }

        var nullItems = db.allGear.Where(g => g == null).Count();
        if (nullItems > 0)
        {
            errorMessage = $"GameDatabase.allGear에 null {nullItems}개";
            return false;
        }
        errorMessage = string.Empty;
        return true;
    }
}

// 보상 테이블에 빈 리스트가 있는지 확인
public class RewardTableCheck : IIntegrityCheck
{
    public string CheckName => "RewardTable Empty";
    public bool Run(out string errorMessage)
    {
        var rt = Resources.Load<RewardTable>("RewardTable");
        if (rt == null) { errorMessage = "RewardTable 리소스 없음"; return false; }

        var emptyCats = rt.catGear.Count == 0;
        var emptyCrops = rt.cropGear.Count == 0;
        if (emptyCats || emptyCrops)
        {
            errorMessage = $"보상 테이블 비어있음 — cat:{rt.catGear.Count} crop:{rt.cropGear.Count}";
            return false;
        }
        errorMessage = string.Empty;
        return true;
    }
}

// 사운드뱅크에 등록된 SfxId가 모두 클립을 가졌는지 확인
public class SoundBankCheck : IIntegrityCheck
{
    public string CheckName => "SoundBank Missing Clips";
    public bool Run(out string errorMessage)
    {
        var bank = Resources.Load<SoundBank>("Audio/SoundBank");
        if (bank == null) { errorMessage = "SoundBank 리소스 없음"; return false; }

        var missing = bank.entries.Where(e => e.clips == null || e.clips.Length == 0)
                                  .Select(e => e.id.ToString())
                                  .ToList();
        if (missing.Count > 0)
        {
            errorMessage = $"클립 없는 SfxId: {string.Join(", ", missing)}";
            return false;
        }
        errorMessage = string.Empty;
        return true;
    }
}
```

### 3. 검사 실행기 (IntegrityRunner)

```csharp
public static class IntegrityRunner
{
    private static readonly IIntegrityCheck[] Checks = new IIntegrityCheck[]
    {
        new GearDatabaseCheck(),
        new RewardTableCheck(),
        new SoundBankCheck(),
        // 새 검사 추가: 여기에 한 줄만
    };

    public static void RunAll()
    {
        int passed = 0, failed = 0;
        foreach (var check in Checks)
        {
            if (check.Run(out var err))
            {
                passed++;
            }
            else
            {
                failed++;
                Debug.LogError($"[IntegrityCheck FAIL] {check.CheckName}: {err}");
            }
        }
        Debug.Log($"[IntegrityCheck] {passed} 통과 / {failed} 실패");
    }
}
```

### 4. 게임 시작 시 호출 (Bootstrap)

```csharp
// GameBootstrap.cs 또는 App_Boot 씬의 MonoBehaviour
private void Awake()
{
#if UNITY_EDITOR || DEVELOPMENT_BUILD
    IntegrityRunner.RunAll();   // 에디터와 개발 빌드에서만 실행
#endif
}
```

`DEVELOPMENT_BUILD` 정의를 쓰면 최종 릴리즈 빌드에서는 검사가 통째로 날아가
퍼포먼스 비용이 전혀 없다.

### 5. 에디터 메뉴로도 실행 (선택)

```csharp
#if UNITY_EDITOR
[UnityEditor.MenuItem("OnionCat/Integrity Check/Run All")]
private static void RunFromMenu()
{
    IntegrityRunner.RunAll();
    UnityEditor.EditorUtility.DisplayDialog(
        "Integrity Check", "Console 창 확인 (에러 없으면 통과)", "확인");
}
#endif
```

---

## 권장 검사 항목 목록 (OnionCat 기준)

| 항목 | 검사 내용 |
|------|-----------|
| `GearDatabaseCheck` | `GameDatabase.allGear`에 null 없음 |
| `RewardTableCheck` | `RewardTable` cat/cropGear 리스트 비어있지 않음 |
| `SoundBankCheck` | 모든 `SfxId`에 클립 1개 이상 |
| `MusicBankCheck` | 모든 `MusicId`에 클립 있음 |
| `EnemyRosterCheck` | `EnemyRoster` 프리팹 참조 null 없음 |
| `RoomLayoutCheck` | `Assets/Data/RoomLayouts/` 에셋 최소 1개 이상 |
| `StageThemeCheck` | `DungeonManager.stageThemes` 길이 = 스테이지 수 |
| `GalmuriFontCheck` | TMP Default/Fallback 폰트에 Galmuri11 설정됨 |

---

## OnionCat 적용 포인트

### 왜 지금 필요한가

- 장비가 163종이 되면서 `ContentBuilder`로 자동 생성하지만, **빌드를 새로 열 때 `GameDatabase`를 Rebuild 안 하면 없는 아이템 참조**가 생긴다.
- 메뉴 `OnionCat > Rebuild Game Database`를 까먹고 커밋하면 런타임에서만 발견됨.
- 검사기를 달아두면 게임 시작 Console에 즉시 에러가 뜨므로 조기 발견이 된다.

### 구현 순서

1. `IntegrityRunner` 클래스 + `GearDatabaseCheck` 하나만 먼저 만들고 연결
2. 게임이 실행될 때마다 Console에 "IntegrityCheck: X 통과" 메시지를 확인
3. 새 빌더 메뉴(Content, Enemies)를 추가할 때마다 대응하는 검사 항목 1개씩 추가

### CI 연동 (나중에)

GitHub Actions에서 Unity Test Runner를 돌릴 때 `IntegrityRunner.RunAll()`을 테스트로 포함하면
**PR마다 자동 무결성 검사**가 된다. 지금은 로컬 실행만으로 충분하지만 팀이 커지면 가치가 크다.

---

## 참고 링크

- Unity Scripting Define Symbols: https://docs.unity3d.com/Manual/CustomScriptingSymbols.html
- Unity Test Runner: https://docs.unity3d.com/Packages/com.unity.test-framework@1.3/manual/index.html
- ScriptableObject 런타임 로드: https://docs.unity3d.com/ScriptReference/Resources.Load.html
