# 튜토리얼 시스템

## 개요
OnionCat은 **Cat+Crop 공유 신체**, **역할 분리 입력** (P1=키보드/P2=마우스), **약점 기반 협력 전투**라는 세 가지 진입 장벽이 있다. 튜토리얼 없이 첫 런을 시작하면 두 플레이어 모두 혼란을 겪는다. 튜토리얼 시스템의 목표는:
1. 각자 역할(Cat=이동/대쉬/근접, Crop=조준/발사/실드)을 1분 안에 체험
2. "이 적은 Cat만/Crop만 처치 가능" 패턴을 자연스럽게 발견하도록 유도
3. 숙련 플레이어는 즉시 스킵 가능
4. 런 중에도 상황별 힌트로 학습 보조

---

## Unity 구현 방법

### 1. 첫 실행 감지 (PlayerPrefs)

```csharp
public class TutorialManager : MonoBehaviour
{
    public static TutorialManager Instance { get; private set; }

    [SerializeField] private GameObject tutorialUIRoot;

    public bool HasPlayedTutorial => PlayerPrefs.GetInt("HasPlayedTutorial", 0) == 1;

    void Awake()
    {
        if (Instance == null) Instance = this;
        else { Destroy(gameObject); return; }
    }

    void Start()
    {
        if (!HasPlayedTutorial)
            StartTutorial();
        else
            tutorialUIRoot.SetActive(false);
    }

    public void CompleteTutorial()
    {
        PlayerPrefs.SetInt("HasPlayedTutorial", 1);
        PlayerPrefs.Save();
        tutorialUIRoot.SetActive(false);
    }

    void StartTutorial()
    {
        tutorialUIRoot.SetActive(true);
        // 전용 튜토리얼 씬을 따로 두는 경우: SceneManager.LoadScene("TutorialScene");
    }
}
```

---

### 2. 튜토리얼 트리거 존

전용 튜토리얼 룸(또는 런 첫 방)에 콜라이더 존을 배치해 플레이어 진입 시 팝업 표시:

```csharp
public class TutorialTriggerZone : MonoBehaviour
{
    [SerializeField] private string stepKey;   // "Movement", "MeleeAttack", "Parry" 등

    private bool triggered = false;

    void Awake()
    {
        GetComponent<Collider2D>().isTrigger = true;
    }

    void OnTriggerEnter2D(Collider2D col)
    {
        if (triggered || !col.CompareTag("Player")) return;
        triggered = true;
        TutorialStepManager.Instance.ShowStep(stepKey);
    }
}
```

---

### 3. 단계별 흐름 (TutorialStepManager)

```csharp
[System.Serializable]
public class TutorialStep
{
    public string key;
    public string title;
    [TextArea] public string description;
    public float autoDuration;   // 0 = 수동 진행, >0 = 자동 진행
}

public class TutorialStepManager : MonoBehaviour
{
    public static TutorialStepManager Instance { get; private set; }

    [SerializeField] private List<TutorialStep> steps;
    [SerializeField] private TutorialTooltipUI tooltip;

    private int currentIndex = 0;
    private Coroutine autoCoroutine;

    void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
    }

    // 트리거 존에서 특정 키로 직접 표시
    public void ShowStep(string key)
    {
        TutorialStep step = steps.Find(s => s.key == key);
        if (step == null) return;
        DisplayStep(step);
    }

    // 순서대로 진행
    public void Advance()
    {
        if (currentIndex >= steps.Count)
        {
            TutorialManager.Instance.CompleteTutorial();
            return;
        }
        DisplayStep(steps[currentIndex++]);
    }

    void DisplayStep(TutorialStep step)
    {
        if (autoCoroutine != null) StopCoroutine(autoCoroutine);
        tooltip.Show(step.title, step.description);

        if (step.autoDuration > 0f)
            autoCoroutine = StartCoroutine(AutoAdvance(step.autoDuration));
    }

    IEnumerator AutoAdvance(float delay)
    {
        yield return new WaitForSeconds(delay);
        Advance();
    }
}
```

---

### 4. Canvas UI 팝업

```csharp
public class TutorialTooltipUI : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI titleText;
    [SerializeField] private TextMeshProUGUI bodyText;
    [SerializeField] private CanvasGroup canvasGroup;
    [SerializeField] private float fadeDuration = 0.25f;

    Coroutine fadeRoutine;

    public void Show(string title, string body)
    {
        titleText.text = title;
        bodyText.text = body;
        gameObject.SetActive(true);
        Fade(1f);
    }

    public void Hide()
    {
        Fade(0f, onComplete: () => gameObject.SetActive(false));
    }

    void Fade(float target, System.Action onComplete = null)
    {
        if (fadeRoutine != null) StopCoroutine(fadeRoutine);
        fadeRoutine = StartCoroutine(FadeRoutine(target, onComplete));
    }

    IEnumerator FadeRoutine(float target, System.Action onComplete)
    {
        float start = canvasGroup.alpha;
        float elapsed = 0f;
        while (elapsed < fadeDuration)
        {
            elapsed += Time.deltaTime;
            canvasGroup.alpha = Mathf.Lerp(start, target, elapsed / fadeDuration);
            yield return null;
        }
        canvasGroup.alpha = target;
        onComplete?.Invoke();
    }
}
```

**Canvas 계층 구조**:
```
Canvas (Screen Space Overlay)
└── TutorialPanel
    ├── Background (반투명 Image)
    ├── TitleText (TextMeshPro)
    ├── BodyText (TextMeshPro)
    ├── ContinueButton → TutorialStepManager.Advance()
    ├── SkipButton → TutorialManager.CompleteTutorial()
    └── TutorialTooltipUI.cs
```

---

### 5. 스킵 기능

```csharp
public class SkipTutorialButton : MonoBehaviour
{
    // 두 번 연속 입력으로 의도치 않은 스킵 방지
    private float lastPressTime = -999f;
    private const float confirmWindow = 0.5f;

    public void OnSkipPressed()
    {
        if (Time.time - lastPressTime < confirmWindow)
            TutorialManager.Instance.CompleteTutorial();
        else
            lastPressTime = Time.time;
    }
}
```

---

### 6. 런 중 힌트 시스템 (상황별 자동 표시)

```csharp
public class HintSystem : MonoBehaviour
{
    public static HintSystem Instance { get; private set; }

    [SerializeField] private TutorialTooltipUI hintUI;

    [System.Serializable]
    public class HintData
    {
        public string key;
        public string title;
        [TextArea] public string body;
        public float cooldown = 30f;
    }

    [SerializeField] private List<HintData> hints;
    private Dictionary<string, float> lastShownAt = new Dictionary<string, float>();

    void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
    }

    public void TryShowHint(string key)
    {
        if (!lastShownAt.TryGetValue(key, out float lastTime))
            lastTime = -9999f;

        HintData hint = hints.Find(h => h.key == key);
        if (hint == null) return;

        if (Time.time - lastTime >= hint.cooldown)
        {
            hintUI.Show(hint.title, hint.body);
            lastShownAt[key] = Time.time;
        }
    }
}
```

**사용 예시** — 적 AI에서 약점 힌트 트리거:
```csharp
// EnemyController.cs
void OnTriggerEnter2D(Collider2D col)
{
    if (col.CompareTag("Player") && enemyType == EnemyType.RangeOnly)
        HintSystem.Instance.TryShowHint("EnemyRangeOnly");
}
```

---

## OnionCat 적용 포인트

### 두 플레이어 동시 역할 안내
P1용 팝업과 P2용 팝업을 화면 좌/우에 분리 배치해 각자 역할을 동시에 표시:

```csharp
public void ShowCoopStep(string p1Msg, string p2Msg)
{
    p1Tooltip.Show("Cat (P1)", p1Msg);
    p2Tooltip.Show("Crop (P2)", p2Msg);
}

// 사용 예: 첫 방 진입 시
ShowCoopStep("WASD로 이동, Space로 대쉬", "마우스로 조준, 좌클릭으로 발사");
```

### 약점 시스템 시각 피드백
튜토리얼 적에게 색상 인디케이터를 붙여 약점 패턴을 자연스럽게 발견하도록 유도:
```csharp
// 근접만 약한 적: 주황색 글로우
// 원거리만 약한 적: 파란색 글로우
spriteRenderer.color = isRangeOnly ? new Color(0.3f, 0.6f, 1f) : new Color(1f, 0.5f, 0.2f);
```

### 튜토리얼 씬 설계 (권장 흐름)
```
1. 인트로 팝업 (3초 자동): "고양이와 화분이 힘을 합쳐야 해!"
2. 이동 존 → Cat 이동 안내
3. 대쉬 존 → "Space: 무적 대쉬"
4. Crop 발사 존 → "마우스 조준 + 좌클릭 발사"
5. 주황색 적 등장 → "이 적은 Cat의 근접 공격만 통해요!" 힌트
6. 파란색 적 등장 → "이 적은 Crop의 원거리 공격만 통해요!" 힌트
7. 혼합 적 방 → 협력 필수 (힌트 없음, 자연스럽게 발견)
8. 완료 → CompleteTutorial()
```

### 주의: New Input System과 timeScale
`Time.timeScale = 0f`로 일시 정지 시 Input System 이벤트는 계속 수신됨. 단 `Update()`가 정지되므로 버튼 입력은 `InputAction` 콜백 방식으로 처리해야 함.

---

## 참고 링크
- [PlayerPrefs 공식 문서](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [New Input System 공식 문서](https://docs.unity3d.com/Packages/com.unity.inputsystem@latest)
- [UI Canvas & RectTransform](https://docs.unity3d.com/Manual/UICanvas.html)
- [TextMeshPro](https://docs.unity3d.com/Manual/TextMeshPro.html)
- [Time.timeScale](https://docs.unity3d.com/ScriptReference/Time-timeScale.html)
- [SceneManager.LoadScene](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadScene.html)
- [Brackeys - Tutorial System (YouTube)](https://www.youtube.com/watch?v=dhFH7z8R2BA)
