# 게임 오버 화면 (Game Over Screen)

## 개요

Unity 2D 로그라이크 게임 오버 화면은 세 레이어로 구성된다.

1. **데이터 레이어** — 런 중 통계(처치 수, 방 클리어, 경과 시간, 업그레이드)를 씬 전환에 걸쳐 유지하는 `RunStats` 객체
2. **로직 레이어** — 두 플레이어가 모두 사망했을 때 게임 오버 이벤트를 발생시키는 `GameManager`
3. **UI 레이어** — 통계를 표시하고 재시작/메인 메뉴 버튼을 제공하는 Canvas 패널

OnionCat처럼 2인 협동 퍼마데스 로그라이크에서는 두 플레이어가 **모두 사망해야만** 게임 오버가 트리거되므로, 이 조건 추적이 핵심이다.

**두 가지 구현 방식:**

| 방식 | 장점 | 단점 |
|------|------|------|
| **동일 씬 내 패널** (추천) | 구현 단순, 즉각 표시 | 씬 재로드 시 상태 관리 필요 |
| **별도 GameOverScene** | 관심사 분리 명확 | 씬 간 데이터 전달 복잡 |

초보자에게는 **동일 씬 내 패널 방식**이 더 쉽다.

---

## Unity 구현 방법

### 1. RunStats 데이터 클래스

씬을 재로드해도 통계가 유지되어야 하므로 `DontDestroyOnLoad` 싱글턴이 보관한다.

```csharp
// RunStats.cs — MonoBehaviour를 상속하지 않는 순수 데이터 클래스
[System.Serializable]
public class RunStats
{
    public int enemiesKilled = 0;
    public int roomsCleared = 0;
    public int upgradesCollected = 0;
    public float elapsedTime = 0f;

    public string GetFormattedTime()
    {
        int minutes = Mathf.FloorToInt(elapsedTime / 60f);
        int seconds = Mathf.FloorToInt(elapsedTime % 60f);
        return string.Format("{0:00}:{1:00}", minutes, seconds);
    }
}
```

---

### 2. GameManager 싱글턴

```csharp
// GameManager.cs
using UnityEngine;
using UnityEngine.SceneManagement;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }
    public static event System.Action OnGameOver;

    public RunStats CurrentRun { get; private set; }

    private bool _player1Dead = false;
    private bool _player2Dead = false;
    private bool _isGameOver = false;

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    void Start()
    {
        CurrentRun = new RunStats();
    }

    void Update()
    {
        if (!_isGameOver)
            CurrentRun.elapsedTime += Time.deltaTime;
    }

    public void ReportPlayerDeath(int playerIndex)
    {
        if (playerIndex == 1) _player1Dead = true;
        if (playerIndex == 2) _player2Dead = true;

        if (_player1Dead && _player2Dead)
            TriggerGameOver();
    }

    void TriggerGameOver()
    {
        if (_isGameOver) return;
        _isGameOver = true;
        OnGameOver?.Invoke();
    }

    public void RestartRun()
    {
        _player1Dead = false;
        _player2Dead = false;
        _isGameOver = false;
        CurrentRun = new RunStats();
        SceneManager.LoadScene("GameScene");
    }

    public void GoToMainMenu()
    {
        _player1Dead = false;
        _player2Dead = false;
        _isGameOver = false;
        CurrentRun = new RunStats();
        SceneManager.LoadScene("MainMenuScene");
    }

    public void AddKill() => CurrentRun.enemiesKilled++;
    public void AddRoomClear() => CurrentRun.roomsCleared++;
    public void AddUpgrade() => CurrentRun.upgradesCollected++;
}
```

**PlayerHealth.cs에서 사망 신고:**

```csharp
// PlayerHealth.cs
public class PlayerHealth : MonoBehaviour, IDamageable
{
    [SerializeField] private int playerIndex = 1; // 1 또는 2
    [SerializeField] private int maxHealth = 3;
    private int _currentHealth;

    void Awake() => _currentHealth = maxHealth;

    public void TakeDamage(float amount, Vector2 knockbackDir)
    {
        _currentHealth -= (int)amount;
        if (_currentHealth <= 0)
        {
            gameObject.SetActive(false);
            GameManager.Instance?.ReportPlayerDeath(playerIndex);
        }
    }
}
```

---

### 3. Canvas UI 구조

**Hierarchy 구조:**
```
Canvas (Screen Space - Overlay)
└── GameOverPanel          ← 기본 비활성화
    ├── BackgroundImage    ← 반투명 검정 배경
    ├── TitleText          ← "GAME OVER" (TextMeshPro)
    ├── StatsPanel
    │   ├── KillsText      ← "처치: 0"
    │   ├── RoomsText      ← "방 클리어: 0"
    │   ├── TimeText       ← "생존 시간: 00:00"
    │   └── UpgradesText   ← "업그레이드: 0"
    ├── RestartButton
    └── MainMenuButton
```

**Canvas 설정:**
1. `Render Mode: Screen Space - Overlay`
2. `Canvas Scaler` → `UI Scale Mode: Scale With Screen Size` → Reference Resolution `1920x1080`
3. `GameOverPanel`은 Inspector에서 기본 비활성화

---

### 4. GameOverUI.cs

```csharp
// GameOverUI.cs
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;

public class GameOverUI : MonoBehaviour
{
    // [유니티 에디터에서 드래그 앤 드롭 설정 필요]
    [SerializeField] private GameObject gameOverPanel;
    [SerializeField] private TextMeshProUGUI killsText;
    [SerializeField] private TextMeshProUGUI roomsText;
    [SerializeField] private TextMeshProUGUI timeText;
    [SerializeField] private TextMeshProUGUI upgradesText;
    [SerializeField] private Button restartButton;
    [SerializeField] private Button mainMenuButton;

    void Awake()
    {
        if (gameOverPanel != null)
            gameOverPanel.SetActive(false);
    }

    void OnEnable() => GameManager.OnGameOver += ShowGameOver;
    void OnDisable() => GameManager.OnGameOver -= ShowGameOver;

    void Start()
    {
        restartButton?.onClick.AddListener(() => GameManager.Instance?.RestartRun());
        mainMenuButton?.onClick.AddListener(() => GameManager.Instance?.GoToMainMenu());
    }

    void ShowGameOver()
    {
        StartCoroutine(FadeInPanel());

        if (GameManager.Instance != null)
        {
            RunStats stats = GameManager.Instance.CurrentRun;
            if (killsText != null) killsText.text = $"처치한 적: {stats.enemiesKilled}";
            if (roomsText != null) roomsText.text = $"클리어한 방: {stats.roomsCleared}";
            if (timeText != null) timeText.text = $"생존 시간: {stats.GetFormattedTime()}";
            if (upgradesText != null) upgradesText.text = $"수집한 업그레이드: {stats.upgradesCollected}";
        }
    }

    IEnumerator FadeInPanel()
    {
        CanvasGroup cg = gameOverPanel.GetComponent<CanvasGroup>();
        if (cg == null) { gameOverPanel.SetActive(true); yield break; }

        cg.alpha = 0f;
        gameOverPanel.SetActive(true);

        while (cg.alpha < 1f)
        {
            cg.alpha += Time.unscaledDeltaTime * 2f; // 0.5초 페이드
            yield return null;
        }
        cg.alpha = 1f;
    }
}
```

`Time.unscaledDeltaTime`을 사용하는 이유: `Time.timeScale = 0`으로 게임을 일시정지해도 애니메이션이 동작하기 때문이다.

---

### 5. New Input System 연동

**필수 확인:**
- `EventSystem` 오브젝트의 `StandaloneInputModule` → `InputSystemUIInputModule`로 교체
- 두 모듈이 동시에 존재하면 충돌. 하나만 남긴다.
- 버튼의 `Navigation` 속성을 `Automatic`으로 설정하면 게임패드 방향키 탐색 자동 지원

---

### 6. 전체 플로우 요약

```
[게임플레이]
    ├─ 적 사망 → EnemyHealth.Die() → GameManager.AddKill()
    ├─ 방 클리어 → GameManager.AddRoomClear()
    └─ Update() → RunStats.elapsedTime 증가

[플레이어 사망]
    PlayerHealth.TakeDamage() → HP <= 0 → Die()
    → GameManager.ReportPlayerDeath(index)
    → 둘 다 죽으면 → OnGameOver 이벤트 발생

[게임 오버 UI]
    GameOverUI.ShowGameOver() 호출
    → FadeInPanel() 코루틴
    → 통계 텍스트 채우기

[버튼 선택]
    Restart → SceneManager.LoadScene("GameScene")
    Main Menu → SceneManager.LoadScene("MainMenuScene")
```

---

## OnionCat 적용 포인트

| 항목 | OnionCat 특이사항 | 구현 방법 |
|------|-------------------|-----------|
| **2인 공유 몸체** | "한 몸"이므로 HP 공유 가능 | `ReportPlayerDeath`를 단일 이벤트로 변경, 공유 HP 풀 사용 |
| **표시할 통계** | 처치 수, 방 클리어, 업그레이드, 생존 시간 | `RunStats` 4개 필드가 정확히 대응 |
| **픽셀아트 스타일** | UI도 픽셀아트 분위기 | Canvas Scaler를 픽셀 퍼펙트 모드 또는 `Pixel Perfect Camera` 패키지 사용 |
| **New Input System** | 이미 사용 중 | `InputSystemUIInputModule`만 활성화 확인 |

**권장 스크립트 배치:**
```
Assets/Scripts/
├── Core/
│   ├── GameManager.cs
│   └── RunStats.cs
├── UI/
│   └── GameOverUI.cs
└── Player/
    └── PlayerHealth.cs
```

**[유니티 에디터에서 드래그 앤 드롭 설정 필요]:**
- `GameOverUI`: `gameOverPanel`, `killsText`, `roomsText`, `timeText`, `upgradesText`, `restartButton`, `mainMenuButton`
- `PlayerHealth`: `playerIndex` (Player1 = 1, Player2 = 2)
- `gameOverPanel`에 `CanvasGroup` 컴포넌트 추가 (페이드 인 효과용)

---

## 참고 링크

- [Unity 공식 2D 로그라이크 튜토리얼](https://learn.unity.com/project/2d-roguelike-tutorial)
- [Unity Learn — Start Menu and Game Manager](https://learn.unity.com/tutorial/start-menu-and-game-manager)
- [SceneManager.LoadScene 공식 API](https://docs.unity3d.com/6000.3/Documentation/ScriptReference/SceneManagement.SceneManager.LoadScene.html)
- [Creating Screen Transitions — Unity UI 문서](https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/HOWTO-UIScreenTransition.html)
- [UI Support — New Input System 문서](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.4/manual/UISupport.html)
- [Singletons in Unity (Game Dev Beginner)](https://gamedevbeginner.com/singletons-in-unity-the-right-way/)
- [Events and Delegates in Unity (Game Dev Beginner)](https://gamedevbeginner.com/events-and-delegates-in-unity/)
- [Unity 2D Roguelike GameManager.cs (GitHub)](https://github.com/antfarmar/Unity-2D-Roguelike-Tutorial/blob/master/Assets/Scripts/GameManager.cs)
