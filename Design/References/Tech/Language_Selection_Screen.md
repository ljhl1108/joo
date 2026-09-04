# 언어 선택 화면 시스템 (Language Selection Screen)

리서치 날짜: 2026-09-04

## 개요

언어 선택 화면은 게임 최초 실행 시 또는 설정 메뉴에서 플레이어가 언어를 고르는 UI 흐름이다. 인디 게임이 한국어·영어를 지원하기 시작할 때 반드시 구현해야 하는 완성 기능이다. Unity의 `Localization` 패키지와 연동하거나 직접 구현할 수 있다. OnionCat은 한국 개발자 작품이므로 한국어·영어 최소 지원이 필요하다.

---

## Unity 구현 방법

### 1. 언어 코드 정의

```csharp
public enum GameLanguage
{
    Korean,
    English
}
```

---

### 2. LanguageManager (싱글턴)

```csharp
public class LanguageManager : MonoBehaviour
{
    public static LanguageManager Instance { get; private set; }

    public GameLanguage CurrentLanguage { get; private set; }

    private const string PrefKey = "SelectedLanguage";

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);

        // 저장된 언어 불러오기 (없으면 시스템 언어 기반 자동 감지)
        if (PlayerPrefs.HasKey(PrefKey))
        {
            CurrentLanguage = (GameLanguage)PlayerPrefs.GetInt(PrefKey);
        }
        else
        {
            CurrentLanguage = DetectSystemLanguage();
        }
    }

    public void SetLanguage(GameLanguage lang)
    {
        CurrentLanguage = lang;
        PlayerPrefs.SetInt(PrefKey, (int)lang);
        PlayerPrefs.Save();
        // 언어 변경 이벤트 발행 → UI 갱신
        OnLanguageChanged?.Invoke(lang);
    }

    public static event Action<GameLanguage> OnLanguageChanged;

    private GameLanguage DetectSystemLanguage()
    {
        return Application.systemLanguage == SystemLanguage.Korean
            ? GameLanguage.Korean
            : GameLanguage.English;
    }
}
```

---

### 3. 텍스트 데이터 — ScriptableObject 방식

```csharp
[CreateAssetMenu(menuName = "Localization/LocalizedText")]
public class LocalizedTextSO : ScriptableObject
{
    public string key;
    [TextArea] public string korean;
    [TextArea] public string english;

    public string Get()
    {
        return LanguageManager.Instance.CurrentLanguage == GameLanguage.Korean
            ? korean : english;
    }
}
```

```csharp
// UI 텍스트 컴포넌트에 부착
public class LocalizedText : MonoBehaviour
{
    [SerializeField] private LocalizedTextSO textData;
    private TMP_Text _label;

    void Awake() => _label = GetComponent<TMP_Text>();

    void OnEnable()
    {
        RefreshText();
        LanguageManager.OnLanguageChanged += OnLangChanged;
    }

    void OnDisable() => LanguageManager.OnLanguageChanged -= OnLangChanged;

    void RefreshText() => _label.text = textData.Get();
    void OnLangChanged(GameLanguage _) => RefreshText();
}
```

---

### 4. 언어 선택 UI 흐름

```csharp
public class LanguageSelectionScreen : MonoBehaviour
{
    [SerializeField] private Button koreanBtn;
    [SerializeField] private Button englishBtn;
    [SerializeField] private string nextSceneName = "MainMenu";

    void Start()
    {
        // 이미 언어 선택한 적 있으면 이 화면 스킵
        if (PlayerPrefs.HasKey("SelectedLanguage"))
        {
            LoadNextScene();
            return;
        }

        koreanBtn.onClick.AddListener(() => SelectLanguage(GameLanguage.Korean));
        englishBtn.onClick.AddListener(() => SelectLanguage(GameLanguage.English));
    }

    void SelectLanguage(GameLanguage lang)
    {
        LanguageManager.Instance.SetLanguage(lang);
        LoadNextScene();
    }

    void LoadNextScene()
    {
        SceneManager.LoadScene(nextSceneName);
    }
}
```

---

### 5. 설정 메뉴에서 언어 변경

```csharp
// 설정 메뉴 드롭다운과 연동
public class LanguageDropdown : MonoBehaviour
{
    [SerializeField] private TMP_Dropdown dropdown;

    void Start()
    {
        // 드롭다운 옵션: 0 = 한국어, 1 = English
        dropdown.value = (int)LanguageManager.Instance.CurrentLanguage;
        dropdown.onValueChanged.AddListener(OnValueChanged);
    }

    void OnValueChanged(int index)
    {
        LanguageManager.Instance.SetLanguage((GameLanguage)index);
    }
}
```

---

### 6. 폰트 처리 (한국어/영어 혼용)

```csharp
// 언어별 폰트 전환이 필요한 경우
public class LocalizedFont : MonoBehaviour
{
    [SerializeField] private TMP_FontAsset koreanFont;
    [SerializeField] private TMP_FontAsset englishFont;
    private TMP_Text _label;

    void Awake() => _label = GetComponent<TMP_Text>();

    void OnEnable()
    {
        ApplyFont(LanguageManager.Instance.CurrentLanguage);
        LanguageManager.OnLanguageChanged += ApplyFont;
    }

    void OnDisable() => LanguageManager.OnLanguageChanged -= ApplyFont;

    void ApplyFont(GameLanguage lang)
    {
        _label.font = lang == GameLanguage.Korean ? koreanFont : englishFont;
    }
}
```

> **[SerializeField] 설정 필요**: koreanFont, englishFont에 유니티 에디터에서 TMP 폰트 에셋 드래그 앤 드롭.

---

### 7. 최초 실행 감지 — 언어 선택 화면 표시 로직

```
게임 실행
    ↓
SplashScreen (로고)
    ↓
PlayerPrefs에 "SelectedLanguage" 있음? → YES → MainMenu
                                       → NO  → LanguageSelectionScreen → MainMenu
```

`App Boot Sequence`에서 이 분기를 처리하는 것이 권장.

---

## OnionCat 적용 포인트

### 1. 최초 실행 언어 선택
- 게임 최초 실행 시 한국어 / English 두 버튼만 있는 심플한 화면
- 시스템 언어가 Korean이면 자동으로 한국어 기본 선택 상태
- 선택 후 PlayerPrefs에 저장 → 이후 실행 시 스킵

### 2. ScriptableObject 기반 텍스트 관리
- 모든 UI 텍스트를 `LocalizedTextSO`로 관리 → 에디터에서 한/영 함께 작성
- `LocalizedText` 컴포넌트가 언어 변경 시 자동 갱신

### 3. 설정 메뉴 연동
- Settings → 언어 드롭다운 → 즉시 전체 UI 갱신
- `OnLanguageChanged` 이벤트로 모든 `LocalizedText` 컴포넌트가 동시 반응

### 4. 한국어 픽셀폰트 주의
- 픽셀아트 스타일에 한국어 폰트 지원은 글자 수가 많아 복잡
- 해결책: TextMeshPro + Dynamic font (런타임 생성) 또는 영문 픽셀폰트 + 한국어 시스템폰트 혼용
- 개발 초기에는 한국어 시스템폰트 사용 후, 픽셀폰트는 출시 전에 교체

### 5. 스팀 출시 시 추가 언어
- Steam이 표시하는 언어 리스트와 게임 내 언어 리스트 일치시킬 것
- `Application.systemLanguage`로 스팀 클라이언트 언어 감지 가능

---

## 구현 순서 요약

1. `GameLanguage` enum 정의
2. `LanguageManager` 싱글턴 씬에 배치 (DontDestroyOnLoad)
3. `LocalizedTextSO` ScriptableObject 생성 (메뉴 텍스트, HUD 텍스트 등)
4. 모든 UI TMP_Text에 `LocalizedText` 컴포넌트 부착
5. `LanguageSelectionScreen` 씬 생성 → Boot 씬에서 최초 분기 처리
6. 설정 메뉴에 `LanguageDropdown` 추가

---

## 참고 링크

- Unity Localization 패키지 공식 문서: https://docs.unity3d.com/Packages/com.unity.localization@latest
- Unity Learn — Localize your game: https://learn.unity.com/tutorial/localizing-your-game
- PlayerPrefs API: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Application.systemLanguage: https://docs.unity3d.com/ScriptReference/Application-systemLanguage.html
- TextMeshPro 한국어 폰트 설정 가이드: https://docs.unity3d.com/Packages/com.unity.textmeshpro@latest
