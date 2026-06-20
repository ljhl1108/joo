# 로컬라이제이션 시스템 (Localization System)

리서치 날짜: 2026-06-20

## 개요

로컬라이제이션은 게임 텍스트, UI, 폰트, 오디오 등을 여러 언어로 제공하는 시스템이다. OnionCat은 한국 인디 게임이지만 Steam 글로벌 출시를 목표로 한다면, 한국어/영어 최소 2개 언어 지원이 필수다. Unity Localization 패키지를 사용하면 코드 변경 없이 언어 전환이 가능하다.

**우선순위**: 기획 단계에서 텍스트를 하드코딩하지 않는 습관이 중요 — 나중에 로컬라이제이션 추가가 훨씬 쉬워짐.

---

## Unity 구현 방법

### Step 1: Unity Localization 패키지 설치

```
Package Manager → Unity Registry 탭 → "Localization" 검색 → Install
패키지 ID: com.unity.localization (Unity 2021.2+ 공식 지원)
```

### Step 2: 프로젝트 로케일 설정

```
Window → Asset Management → Localization Scene Controls → Open Localization Settings
→ Add Locale: Korean (ko), English (en)
→ Project Locale Identifier: Korean (기본값을 한국어로 설정)
```

### Step 3: String Table 생성 (텍스트 데이터)

```
Asset Menu → Create → Localization → String Table Collection
이름 예시: "UI_Strings" (버튼, 메뉴 텍스트), "GameText" (게임 내 대사)
```

String Table에 키-값 쌍 입력:

| Key | Korean | English |
|-----|--------|---------|
| btn_start | 게임 시작 | Start Game |
| btn_quit | 종료 | Quit |
| ui_hp | 체력 | HP |
| ui_gold | 골드 | Gold |
| boss_warning | 경고! 보스 등장! | Warning! Boss Incoming! |
| gameover_title | 게임 오버 | Game Over |
| upgrade_attack | 공격력 증가 | Attack Up |

### Step 4: UI 텍스트에 Localization 연결

**방법 A: Inspector에서 (코드 없음)**

```
TextMeshPro 오브젝트 → Add Component → Localize String Event
→ String Reference: String Table 선택 → Key 선택
→ Update String: TMP Text.text 연결 (드래그 앤 드롭)
```

**방법 B: 코드에서**

```csharp
using UnityEngine.Localization;
using UnityEngine.Localization.Settings;

public class LocalizedTextExample : MonoBehaviour
{
    [SerializeField] private LocalizedString localizedString;
    private TMPro.TextMeshProUGUI textUI;

    private void Awake() => textUI = GetComponent<TMPro.TextMeshProUGUI>();

    private void Start()
    {
        localizedString.StringChanged += UpdateText;
        // 초기값 즉시 반영
        localizedString.RefreshString();
    }

    private void UpdateText(string value) => textUI.text = value;

    private void OnDestroy()
    {
        localizedString.StringChanged -= UpdateText;
    }
}
```

### Step 5: 런타임 언어 전환

```csharp
using UnityEngine.Localization.Settings;

public class LanguageSwitcher : MonoBehaviour
{
    public async void SetLanguage(string localeCode)
    {
        // localeCode 예: "ko" (한국어), "en" (영어)
        var locale = LocalizationSettings.AvailableLocales.GetLocale(localeCode);
        if (locale != null)
        {
            LocalizationSettings.SelectedLocale = locale;
            // PlayerPrefs에 저장하여 다음 실행 시 유지
            PlayerPrefs.SetString("SelectedLocale", localeCode);
        }
    }

    private void Start()
    {
        // 저장된 언어 불러오기
        string saved = PlayerPrefs.GetString("SelectedLocale", "ko");
        SetLanguage(saved);
    }
}
```

### Step 6: Asset Table (이미지/폰트 다국어화)

언어별로 다른 폰트나 이미지가 필요할 때:

```
Create → Localization → Asset Table Collection
Key: "main_font"
Korean: NanumGothic (한글 폰트)
English: Arial (영문 폰트)
```

```csharp
using UnityEngine.Localization;

public class LocalizedFont : MonoBehaviour
{
    [SerializeField] private LocalizedAsset<TMPro.TMP_FontAsset> localizedFont;
    private TMPro.TextMeshProUGUI textUI;

    private void Awake() => textUI = GetComponent<TMPro.TextMeshProUGUI>();

    private void Start()
    {
        localizedFont.AssetChanged += font => textUI.font = font;
        localizedFont.LoadAssetAsync();
    }
}
```

### Step 7: 설정 메뉴 연동

Settings_Menu.md의 설정 화면에 언어 선택 드롭다운 추가:

```csharp
// SettingsMenu.cs에 추가
[SerializeField] private TMPro.TMP_Dropdown languageDropdown;

private void InitLanguageDropdown()
{
    languageDropdown.ClearOptions();
    var options = new List<string> { "한국어", "English" };
    languageDropdown.AddOptions(options);

    string current = PlayerPrefs.GetString("SelectedLocale", "ko");
    languageDropdown.value = current == "ko" ? 0 : 1;
    languageDropdown.onValueChanged.AddListener(OnLanguageChanged);
}

private void OnLanguageChanged(int index)
{
    string code = index == 0 ? "ko" : "en";
    languageSwitcher.SetLanguage(code);
}
```

---

## OnionCat 적용 포인트

### 최소 구현 계획 (2개 언어 지원)

**필수 String Table: UI_Strings**

| 카테고리 | 키 예시 | 우선순위 |
|---------|---------|---------|
| 메인 메뉴 | btn_start, btn_quit, btn_settings | 최고 |
| 게임 오버 | gameover_title, gameover_restart, gameover_menu | 최고 |
| 업그레이드 | upgrade_atk, upgrade_hp, upgrade_speed | 높음 |
| HUD | ui_hp, ui_gold, ui_floor | 높음 |
| 보스 경고 | boss_warning_floor, boss_name_* | 중간 |
| 튜토리얼 | tutorial_move, tutorial_attack, tutorial_shield | 중간 |

### 하드코딩 방지 습관 (지금 당장 적용)

```csharp
// ❌ 나쁜 예 — 하드코딩
upgradeNameText.text = "공격력 증가";

// ✅ 좋은 예 — LocalizedString 사용
[SerializeField] private LocalizedString upgradeNameKey;
upgradeNameText.text = upgradeNameKey.GetLocalizedString();
```

### 한국어 전용 고려사항

- **폰트**: 한국어 지원 TMP 폰트 필수 (NanumGothic, NotoSansKR 권장)
- **텍스트 길이**: 영어가 한국어보다 평균 30% 길어짐 → UI 레이아웃에 여유 공간 확보
- **글꼴 크기**: 같은 픽셀 크기에서 한국어가 더 크게 보임 → 언어별 fontSize 조정 고려

### 폰트 Atlas 생성 (중요)

```
Window → TextMeshPro → Font Asset Creator
Source Font: NanumGothic.ttf (한글 폰트 파일)
Character Set: Unicode Range → 한글 범위: AC00-D7A3
Generate Font Atlas → 저장
```

---

## 참고 링크

- [Unity Localization 공식 문서](https://docs.unity3d.com/Packages/com.unity.localization@latest)
- [Unity Localization 시작 가이드](https://docs.unity3d.com/Packages/com.unity.localization@1.4/manual/QuickStartGuideWithVariants.html)
- [TMP 한국어 폰트 설정 가이드 (Unity Forum)](https://discussions.unity.com/t/korean-font-in-textmeshpro/747339)
- [Localization 런타임 언어 전환 예제 (Unity Blog)](https://blog.unity.com/engine-platform/localization-in-unity)
- [NotoSansKR 무료 한글 폰트 (Google Fonts)](https://fonts.google.com/noto/specimen/Noto+Sans+KR)
- [Nanum 폰트 무료 다운로드 (네이버 나눔글꼴)](https://hangeul.naver.com/font)
