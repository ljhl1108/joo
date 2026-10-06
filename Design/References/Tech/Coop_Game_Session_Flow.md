# 협동 게임 세션 전체 흐름 설계

리서치 날짜: 2026-10-06

## 개요
2인 협동 로그라이트에서 "앱 시작"부터 "런 종료 후 재시작"까지 전체 씬·UI·입력 흐름을 어떻게 설계하고 구현하는지.
개별 씬(메인 메뉴, 게임 오버 화면 등)은 각각의 Tech 파일에 있지만, **전체 오케스트레이션**을 다루는 파일은 없어서 별도 작성.
OnionCat처럼 "두 플레이어가 단일 바디를 공유"하는 비대칭 협동 구조에 맞게 서술.

---

## 세션 흐름 다이어그램

```
[앱 시작]
    ↓
[Splash / 부트스트랩 씬]  (초기화: AudioManager, PoolManager, InputManager 등)
    ↓
[메인 메뉴 씬]
    ↓ "Start" 버튼
[컨트롤러 페어링 화면]  ← 고양이(키보드/패드) + 양파(마우스) 할당
    ↓ 페어링 완료
[Pre-Run 로비 / 캐릭터 확인 화면]  ← 간단한 시작 확인
    ↓ "Begin" 버튼
[게임플레이 씬 - 시작 방]
    ↓ 방 클리어 반복
[게임플레이 씬 - 전투 방 n개]
    ↓ 보스 방 클리어 or 전멸
[런 결과 화면 (오버레이 또는 별도 씬)]
    ↓ "Restart" or "Menu"
[Quick Restart → 페어링 유지 채 새 런] or [메인 메뉴]
```

---

## Unity 구현 방법

### 1. 부트스트랩 패턴
```csharp
// BootstrapScene (씬 인덱스 0): 게임 시작 시 항상 로드
// DontDestroyOnLoad 서비스들 초기화
public class Bootstrap : MonoBehaviour
{
    void Awake()
    {
        // 순서 중요: 서비스 → 입력 → 오디오 → 씬 전환
        ServiceLocator.Register<IPoolManager>(PoolManager.Instance);
        ServiceLocator.Register<IAudioManager>(AudioManager.Instance);
        InputPairManager.Initialize();
        SceneTransitionManager.LoadScene("MainMenu");
    }
}
```

### 2. 씬 목록 및 로드 순서
```csharp
// SceneNames 상수 (OnionCat 기존 규칙 준수)
public static class SceneNames
{
    public const string Bootstrap  = "Bootstrap";
    public const string MainMenu   = "MainMenu";
    public const string Pairing    = "ControllerPairing";  // 생략 가능 - 인게임 UI로 대체
    public const string GamePlay   = "GamePlay";           // 단일 영구 씬 + 방 로드
    public const string RunResult  = "RunResult";          // 또는 오버레이 UI
}
```

### 3. 컨트롤러 페어링 타이밍
OnionCat 특수 케이스: 고양이(키보드/패드)와 양파(마우스)는 사실상 항상 동일 컴퓨터의 다른 입력 장치.
별도 페어링 화면 없이 **자동 페어링** 가능:
```csharp
// CoopInputLayout.cs (기존 시스템)가 자동 전환 처리
// 패드 연결 시: 고양이 = 패드, 양파 = 마우스
// 패드 없음:   고양이 = WASD, 양파 = 마우스
// → 페어링 화면 필요 없음 — 시작 버튼 바로 게임 씬으로
```

### 4. 런 시작 흐름
```csharp
// MainMenuUI.cs
public void OnStartButtonClicked()
{
    GameManager.Instance.StartNewRun();          // RunData 초기화
    SceneTransitionManager.LoadScene(SceneNames.GamePlay, FadeType.FadeBlack);
}

// GameManager.StartNewRun()
public void StartNewRun()
{
    Run = new RunData();                         // 기존 RunData 초기화
    DungeonManager.Instance.GenerateRun();       // 방 순서 무작위 생성
    ChangeState(GameState.Playing);
}
```

### 5. 게임 오버 / 런 종료 흐름
```csharp
// 두 플레이어 모두 사망 또는 보스 클리어 시 런 종료
public void OnRunEnd(bool isVictory)
{
    ChangeState(isVictory ? GameState.Victory : GameState.GameOver);
    // 결과 데이터 수집
    var result = new RunResultData
    {
        IsVictory     = isVictory,
        FloorsCleared = Run.FloorsCleared,
        KillCount     = Run.KillCount,
        ElapsedTime   = Run.ElapsedTime,
        Upgrades      = Run.AcquiredUpgrades
    };
    RunResultUI.Show(result);   // 오버레이 UI (씬 전환 없이)
}
```

### 6. 빠른 재시작 (Quick Restart)
페어링 상태 유지, 런 데이터만 리셋:
```csharp
// RunResultUI "Restart" 버튼
public void OnRestartClicked()
{
    // 입력 페어링 유지
    // 씬 재로드 (GamePlay 씬 자체를 리로드하면 모든 오브젝트 초기화)
    SceneTransitionManager.ReloadScene(FadeType.FadeBlack);
    // SceneTransitionManager.LoadScene(SceneNames.GamePlay) 와 동일하지만 더 명확
}
```

### 7. 씬 전환 시 상태 보존
```csharp
// DontDestroyOnLoad 서비스들은 씬 전환 후에도 유지:
//   GameManager, RunData, AudioManager, PoolManager, InputPairManager
// 반면 씬 오브젝트들(DungeonManager, EnemyBase.Active 등)은 씬 언로드 시 파괴

// 씬 전환 전 풀 초기화
public void OnSceneUnloading()
{
    PoolManager.Instance.ReturnAll();   // 모든 풀 오브젝트 반환
    EnemyBase.Active.Clear();           // 적 목록 초기화
}
```

### 8. 일시정지 → 재개 흐름
```csharp
// ESC 키 or 패드 Start → PauseMenu 토글
// GameManager.IsGameplayActive = false → 입력 차단 (기존 규칙 준수)
public void Pause()
{
    ChangeState(GameState.Paused);
    PauseMenuUI.Show();
}

public void Resume()
{
    PauseMenuUI.Hide();
    ChangeState(GameState.Playing);
}

// PauseMenu 옵션:
//   Resume → Resume()
//   Restart → SceneTransitionManager.ReloadScene()
//   Main Menu → SceneTransitionManager.LoadScene("MainMenu") + Run 파기
//   Quit → Application.Quit()
```

### 9. 씬 전환 매니저 (간단 구현)
```csharp
public class SceneTransitionManager : MonoBehaviour
{
    public static void LoadScene(string sceneName, FadeType fade = FadeType.None)
    {
        // 페이드 아웃 → LoadSceneAsync → 페이드 인
        Instance.StartCoroutine(Instance.TransitionCoroutine(sceneName, fade));
    }

    private IEnumerator TransitionCoroutine(string sceneName, FadeType fade)
    {
        if (fade != FadeType.None) yield return FadeOut();
        yield return SceneManager.LoadSceneAsync(sceneName);
        if (fade != FadeType.None) yield return FadeIn();
    }
}
```

---

## OnionCat 적용 포인트

### 현재 구조와의 매핑
OnionCat은 GameManager.ChangeState() 기반 상태 관리가 이미 구현됨:
```
GameState.MainMenu   → 메인 메뉴 UI 표시
GameState.Playing    → 게임플레이 진행
GameState.Paused     → PauseMenu 표시 + 입력 차단
GameState.GameOver   → GameOver UI 표시
GameState.Victory    → Victory UI 표시
GameState.Upgrade    → UpgradeSelectUI 표시 (방 클리어 후)
```
→ 위 상태들로 전체 세션 흐름이 이미 커버됨.

### OnionCat 특수: 단일 바디 세션 이슈
두 플레이어가 한 오브젝트를 공유하므로:
- **재시작 시 주의**: 씬 리로드가 고양이/양파 모든 컴포넌트를 초기화 — RunData가 DontDestroyOnLoad에 있는지 확인
- **게임 오버 판정**: 고양이(PlayerHealth)가 0 → OnRunEnd(false) 트리거. 양파는 독립 체력 없음
- **Victory 판정**: 보스 방 클리어 → GameManager가 OnRunEnd(true) 트리거

### 추천 씬 구조 (OnionCat 기준)
```
씬 0: Bootstrap    (서비스 초기화, 자동 MainMenu 로드)
씬 1: MainMenu     (타이틀, 시작/설정/종료)
씬 2: GamePlay     (전투, 방 전환은 DungeonManager가 처리)
씬 3: RunResult    (런 결과 — 별도 씬 또는 GamePlay 위 오버레이 UI)

현재 OnionCat이 Bootstrap씬 없다면:
→ GamePlay 씬 Awake()에서 서비스 Lazy Init
→ MainMenu 씬에서 GamePlay 씬으로 단순 LoadScene()
```

### 런 시작 체크리스트
런을 시작하기 전 확인해야 할 항목들:
- [ ] RunData 완전 초기화 (업그레이드, 스킬, 가방 초기화)
- [ ] DungeonManager 방 순서 재생성
- [ ] PoolManager 풀 비우기 (이전 런 잔존 오브젝트 제거)
- [ ] PlayerHealth 최대 체력 복구
- [ ] AudioManager BGM 전환 (메뉴 → 인게임)
- [ ] 카메라 위치 시작 방으로 스냅

---

## 참고 링크

- Unity SceneManager 공식: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- Unity DontDestroyOnLoad 패턴: https://docs.unity3d.com/ScriptReference/Object.DontDestroyOnLoad.html
- Bootstrap Scene 패턴 설명: https://gamedevbeginner.com/singletons-in-unity-the-right-way/
- 씬 전환 페이드 구현: https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-CanvasGroup.html
- Game State Machine 패턴: https://gameprogrammingpatterns.com/state.html
- 관련 Tech 파일: `Scene_Transition.md`, `Game_State_Manager.md`, `Full_Scene_Flow_Architecture.md`, `Quick_Restart_Between_Runs.md`
