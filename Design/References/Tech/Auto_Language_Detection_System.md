# 시스템 언어 자동 감지 및 폰트 자동 로딩 (Auto Language Detection & Font Loading)

리서치 날짜: 2026-10-18

## 개요

게임 첫 실행 시 **OS 언어 설정을 자동으로 감지해 게임 언어를 자동 설정**하는 시스템.
별도 설정 화면 없이도 한국어 사용자는 한국어, 영어 사용자는 영어로 자동 시작.
이미 설치된 Unity Localization 패키지와 연동하거나, 독립 구현 모두 가능.

OnionCat에서 중요한 이유:
- 현재 UI 문구가 한글 (Galmuri11 폰트), 나중에 영어 출시 예정
- 해외 플레이어도 Steam에서 다운받을 수 있음 → 첫 실행 경험 중요
- 언어 선택 화면을 띄우지 않아도 자동으로 적절한 언어 적용 가능

## Unity 구현 방법

### 1. OS 언어 감지 — Application.systemLanguage

```csharp
// Unity 내장 열거형으로 OS 언어 바로 접근 가능
SystemLanguage detectedLang = Application.systemLanguage;

// 예:
// SystemLanguage.Korean   → 한국어 OS
// SystemLanguage.English  → 영어 OS
// SystemLanguage.Japanese → 일본어 OS
// SystemLanguage.ChineseSimplified, ChineseTraditional → 중국어
```

### 2. 지원 언어 → 게임 내 언어 코드 매핑

```csharp
public enum GameLanguage { Korean, English }

public static GameLanguage DetectLanguage()
{
    return Application.systemLanguage switch
    {
        SystemLanguage.Korean => GameLanguage.Korean,
        // 지원 언어 추가 시 여기에 추가
        _ => GameLanguage.English  // 기본값: 영어
    };
}
```

### 3. 설정 저장 — PlayerPrefs 활용

```csharp
public static class LanguageSettings
{
    private const string KEY = "game_language";

    // 처음 실행인지 확인 후 감지 → 저장
    public static GameLanguage GetOrDetect()
    {
        if (!PlayerPrefs.HasKey(KEY))
        {
            var detected = DetectLanguage();
            Save(detected);
            return detected;
        }
        return (GameLanguage)PlayerPrefs.GetInt(KEY);
    }

    public static void Save(GameLanguage lang)
    {
        PlayerPrefs.SetInt(KEY, (int)lang);
        PlayerPrefs.Save();
    }
}
```

첫 실행: 자동 감지 후 저장.
이후 실행: 저장된 값 사용 (사용자가 설정 메뉴에서 바꿀 수 있음).

### 4. Unity Localization 패키지 연동 (설치된 경우)

```csharp
using UnityEngine.Localization.Settings;
using UnityEngine.Localization;

public static async void ApplyLanguage(GameLanguage lang)
{
    string localeCode = lang switch
    {
        GameLanguage.Korean => "ko",
        GameLanguage.English => "en",
        _ => "en"
    };

    var locale = LocalizationSettings.AvailableLocales.GetLocale(localeCode);
    if (locale != null)
    {
        LocalizationSettings.SelectedLocale = locale;
    }
}
```

### 5. Unity Localization 없이 직접 구현 (경량 버전)

문자열 테이블을 ScriptableObject로 관리:

```csharp
[CreateAssetMenu(fileName = "StringTable", menuName = "OnionCat/StringTable")]
public class StringTable : ScriptableObject
{
    [System.Serializable]
    public class Entry
    {
        public string key;
        [TextArea] public string korean;
        [TextArea] public string english;
    }

    public List<Entry> entries;

    private Dictionary<string, Entry> _cache;

    public string Get(string key, GameLanguage lang)
    {
        if (_cache == null) BuildCache();
        if (!_cache.TryGetValue(key, out var e)) return $"[{key}]";
        return lang == GameLanguage.Korean ? e.korean : e.english;
    }

    private void BuildCache()
    {
        _cache = new();
        foreach (var e in entries) _cache[e.key] = e;
    }
}
```

호출:
```csharp
// 어디서든
string text = StringTable.Get("ui.start_game", LanguageSettings.Current);
```

### 6. 폰트 자동 교체 — TMP_FontAsset 스왑

한국어 = Galmuri11, 영어 = 다른 폰트로 자동 교체:

```csharp
[System.Serializable]
public class FontSet
{
    public TMP_FontAsset korean;
    public TMP_FontAsset english;

    public TMP_FontAsset Get(GameLanguage lang) =>
        lang == GameLanguage.Korean ? korean : english;
}
```

모든 TMP 텍스트에 적용:

```csharp
// LanguageManager.ApplyFonts()
public void ApplyFonts(GameLanguage lang)
{
    // TMP default font override
    TMP_Settings.defaultFontAsset = fontSet.Get(lang);

    // 이미 생성된 모든 TMP_Text 갱신
    foreach (var text in FindObjectsByType<TMP_Text>(FindObjectsSortMode.None))
    {
        text.font = fontSet.Get(lang);
        text.ForceMeshUpdate();
    }
}
```

### 7. 부트스트랩 씬에서 처리 순서

```csharp
// BootstrapScene의 GameBootstrap.cs
void Awake()
{
    var lang = LanguageSettings.GetOrDetect();  // 1. 감지 or 불러오기
    LanguageManager.Instance.Apply(lang);        // 2. 폰트 + 문자열 적용
    // 3. 메인 메뉴 씬 로드
    SceneManager.LoadScene(SceneNames.MainMenu);
}
```

### 8. 설정 메뉴에서 수동 변경

```csharp
// SettingsMenu.cs
public void OnLanguageChanged(int dropdownIndex)
{
    var lang = (GameLanguage)dropdownIndex;
    LanguageSettings.Save(lang);
    LanguageManager.Instance.Apply(lang);
    // 일부 UI는 씬 재로드 없이 즉시 적용, 일부는 재시작 안내
}
```

### 9. Galmuri SDF 폰트 용량 주의사항

CLAUDE.md에 명시: **커밋 전에 `ClearFontAssetData(true)` 호출 필수** (동적 아틀라스 비우기).
언어 전환 시 Galmuri 폰트가 다시 아틀라스를 빌드하므로, 에디터에서 확인 후 커밋 전 정리.

```csharp
#if UNITY_EDITOR
[UnityEditor.MenuItem("OnionCat/Font/Clear Galmuri Cache")]
static void ClearFontCache()
{
    var font = Resources.Load<TMP_FontAsset>("Fonts/Galmuri11 SDF");
    font?.ClearFontAssetData(setAtlasSizeToZero: true);
    UnityEditor.AssetDatabase.SaveAssets();
}
#endif
```

## OnionCat 적용 포인트

### 지금 당장 해야 할 것 (영어 출시 전 준비)

1. **`LanguageSettings.GetOrDetect()` 부트스트랩에 추가**: 한 줄만 추가하면 언어 감지 준비 완료
2. **문자열 하드코딩 금지**: 모든 UI 문자열을 `StringTable.Get("key")` 형태로 쓰기 시작. 지금부터 해두면 나중에 영어 번역을 "english 열에 채우기"만 하면 됨.
3. **ContentBuilder.cs 장비 이름/설명 외부화**: 장비 163개의 이름/설명을 StringTable 또는 구글 시트로 분리. 영어 출시 시 번역 비용 최소화.

### 권장 구현 순서

1. `GameLanguage` enum + `LanguageSettings` 클래스 추가 (30분)
2. `Application.systemLanguage` → `GameLanguage` 매핑 (10분)
3. Bootstrap에서 호출 (5분)
4. **영어 UI 문자열 준비 완료 시**: StringTable 채우기 + TMP 폰트 교체 연결
5. Unity Localization 패키지는 지원 언어가 3개 이상 될 때 도입 고려

### 한국어 전용 현재 상태에서의 실용적 활용

- 지금은 `Application.systemLanguage != Korean`이면 "영어 미지원 안내 문구" 표시 가능
- 또는 그냥 한국어로만 표시하되, 코드에 언어 체계는 미리 구축해두기

## 참고 링크

- Unity Application.systemLanguage: https://docs.unity3d.com/ScriptReference/Application-systemLanguage.html
- Unity Localization 패키지 공식 문서: https://docs.unity3d.com/Packages/com.unity.localization@1.5/manual/index.html
- TMP Font Asset 동적 아틀라스: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/FontAssetsDynamic.html
- Unity Localization 시작 가이드: https://learn.unity.com/tutorial/localization-in-unity
