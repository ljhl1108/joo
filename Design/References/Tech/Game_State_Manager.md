# 게임 상태 관리 FSM (Game State Manager)

리서치 날짜: 2026-06-30

## 개요

게임 상태 관리 FSM은 게임 전체 흐름(타이틀 → 런 진행 → 일시정지 → 게임오버 → 결과 화면)을 **유한 상태 기계(Finite State Machine)** 로 관리하는 설계 패턴이다.

OnionCat에 이것이 필요한 이유:
- 씬 전환, UI 표시, 입력 처리, 물리 시뮬레이션 활성화 여부 등이 **현재 게임 상태**에 따라 달라짐
- 상태를 명시적으로 관리하지 않으면 "일시정지 중에도 적이 움직인다", "게임오버 후에도 플레이어 입력이 먹힌다" 같은 버그 발생

---

## Unity 구현 방법

### 방법 1: 열거형 + 이벤트 기반 (권장 - 초급자 친화적)

```csharp
// GameState.cs
public enum GameState
{
    MainMenu,
    InRun,
    Paused,
    GameOver,
    RunResult,
    Loading
}
```

```csharp
// GameManager.cs
using UnityEngine;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    private GameState _currentState;
    public GameState CurrentState => _currentState;

    // 상태 변경 이벤트 — 다른 시스템이 구독
    public static event System.Action<GameState, GameState> OnStateChanged;

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    void Start()
    {
        ChangeState(GameState.MainMenu);
    }

    public void ChangeState(GameState newState)
    {
        if (_currentState == newState) return;

        GameState previousState = _currentState;
        _currentState = newState;

        OnExitState(previousState);
        OnEnterState(newState);

        OnStateChanged?.Invoke(previousState, newState);
    }

    private void OnExitState(GameState state)
    {
        switch (state)
        {
            case GameState.Paused:
                Time.timeScale = 1f;
                break;
        }
    }

    private void OnEnterState(GameState state)
    {
        switch (state)
        {
            case GameState.MainMenu:
                Time.timeScale = 1f;
                break;

            case GameState.InRun:
                Time.timeScale = 1f;
                break;

            case GameState.Paused:
                Time.timeScale = 0f; // 물리/애니메이션 정지
                break;

            case GameState.GameOver:
                Time.timeScale = 1f;
                break;

            case GameState.RunResult:
                Time.timeScale = 1f;
                break;
        }
    }
}
```

### 방법 2: UI 구독 패턴

UI 요소들이 GameManager 이벤트를 구독하여 자동으로 표시/숨김:

```csharp
// PauseMenuUI.cs
public class PauseMenuUI : MonoBehaviour
{
    void OnEnable()
    {
        GameManager.OnStateChanged += HandleStateChange;
    }

    void OnDisable()
    {
        GameManager.OnStateChanged -= HandleStateChange;
    }

    private void HandleStateChange(GameState prev, GameState next)
    {
        gameObject.SetActive(next == GameState.Paused);
    }
}
```

### 방법 3: 입력 차단 패턴

상태에 따라 플레이어 입력 비활성화:

```csharp
// PlayerInputHandler.cs
public class PlayerInputHandler : MonoBehaviour
{
    private PlayerInput _playerInput;

    void Awake()
    {
        _playerInput = GetComponent<PlayerInput>();
    }

    void OnEnable()
    {
        GameManager.OnStateChanged += HandleStateChange;
    }

    void OnDisable()
    {
        GameManager.OnStateChanged -= HandleStateChange;
    }

    private void HandleStateChange(GameState prev, GameState next)
    {
        bool inputEnabled = next == GameState.InRun;
        _playerInput.enabled = inputEnabled;
    }
}
```

### 상태 전환 다이어그램

```
[MainMenu]
    ↓ 게임 시작
[Loading]
    ↓ 로딩 완료
[InRun] ←────────────────────────────┐
    ↓ ESC          ↓ HP=0            │
[Paused]       [GameOver]            │
    ↓ 재개          ↓ 확인 / 재시작   │
[InRun]        [RunResult] ──────────┘
                   ↓ 메인 메뉴로
               [MainMenu]
```

### 씬 전환과 연동

```csharp
public void StartNewRun()
{
    ChangeState(GameState.Loading);
    StartCoroutine(LoadRunScene());
}

private IEnumerator LoadRunScene()
{
    // 페이드 아웃
    yield return FadeManager.Instance.FadeOut();
    
    // 비동기 씬 로드
    var operation = SceneManager.LoadSceneAsync("RunScene");
    while (!operation.isDone)
        yield return null;

    ChangeState(GameState.InRun);
    
    // 페이드 인
    yield return FadeManager.Instance.FadeIn();
}
```

---

## OnionCat 적용 포인트

### 전체 상태 목록 (OnionCat용)

```csharp
public enum GameState
{
    MainMenu,       // 타이틀 화면
    CharacterSelect, // (나중에 추가 가능) 캐릭터 선택
    Loading,        // 씬 로딩 중
    InRun,          // 실제 게임 플레이
    Paused,         // ESC로 일시정지
    UpgradeSelect,  // 방 클리어 후 업그레이드 선택
    ShopOpen,       // 상점 UI 열린 상태
    GameOver,       // 플레이어 전멸
    RunResult,      // 런 결과 화면 (클리어 또는 게임오버 통계)
    Credits         // 크레딧 (나중에)
}
```

### 주의 사항

1. **UpgradeSelect / ShopOpen 상태**: Time.timeScale을 0으로 하면 UI 애니메이션도 멈춤
   → `Time.timeScale = 0`이지만 UI는 `UnscaledTime` 사용 → `DOTween.SetUpdate(true)` 또는 `Animator.updateMode = AnimatorUpdateMode.UnscaledTime`

2. **두 플레이어 입력 분리**: 코옵 게임이므로 Player1, Player2 각각 상태에 따라 입력 처리
   → `LocalCoopInputSystem` 참조

3. **GameManager는 DontDestroyOnLoad**: 씬이 바뀌어도 상태 유지

4. **첫 구현 우선순위**: `MainMenu → InRun → Paused → GameOver` 4개만 먼저 구현하고 나머지 추가

---

## 참고 링크

- Unity 공식 문서 (Time.timeScale): https://docs.unity3d.com/ScriptReference/Time-timeScale.html
- Unity GameManager 싱글톤 패턴: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Game Programming Patterns (State Machine): https://gameprogrammingpatterns.com/state.html
- Unity C# 이벤트 시스템: https://docs.unity3d.com/ScriptReference/Events.UnityEvent.html
- Brackeys - Game Manager Tutorial: https://www.youtube.com/watch?v=4I0vonyqyki
