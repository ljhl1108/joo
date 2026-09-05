# Bootstrap Scene 아키텍처

리서치 날짜: 2026-09-05

## 개요

**Bootstrap Scene(부트스트랩 씬)** 패턴은 Unity 게임에서 씬(Scene)을 어떻게 구조화할지에 대한 아키텍처 설계다. 초보 개발자가 가장 자주 마주치는 문제는:

- GameManager, AudioManager 같은 싱글톤이 씬 전환 때 사라짐
- `DontDestroyOnLoad`를 남발하다가 씬 재로드 시 오브젝트 중복 생성
- 모든 코드가 Gameplay 씬 하나에 몰려 복잡도 폭발

Bootstrap Pattern은 이 문제를 **씬 역할 분리**로 해결한다.

---

## 씬 구조 설계

### 권장 씬 구성

```
씬 계층:
├── 0_Bootstrap     ← 앱 시작 시 1번만 로드, 영구 매니저 초기화
├── 1_MainMenu      ← 타이틀 화면
├── 2_Gameplay      ← 로그라이크 게임플레이
│   ├── [Additive] HUD       ← 게임플레이 중 항상 있는 UI
│   └── [Additive] Room_XXX  ← 현재 활성 방
└── 3_GameOver      ← 런 종료 화면
```

### 각 씬의 역할

| 씬 | 역할 | 포함 오브젝트 |
|----|------|---------------|
| Bootstrap | 영구 매니저 초기화 | GameManager, AudioManager, InputManager, SceneLoader |
| MainMenu | UI + 배경 | 캔버스, 배경 오브젝트 |
| Gameplay | 게임 로직 | Player, EnemySpawner, RoomManager |
| HUD (Additive) | 인게임 UI | HP바, 미니맵, 스킬 쿨다운 |

---

## Unity 구현 방법

### 1. Bootstrap 씬 진입점

```csharp
// BootstrapLoader.cs — Bootstrap 씬에만 존재
public class BootstrapLoader : MonoBehaviour
{
    [SerializeField] private GameManager gameManagerPrefab;
    [SerializeField] private AudioManager audioManagerPrefab;
    [SerializeField] private string firstSceneName = "1_MainMenu";

    private IEnumerator Start()
    {
        // 영구 매니저 생성
        Instantiate(gameManagerPrefab);
        Instantiate(audioManagerPrefab);

        // 첫 씬 로드
        yield return SceneManager.LoadSceneAsync(firstSceneName);
    }
}
```

### 2. 영구 매니저 — DontDestroyOnLoad 안전하게 사용

```csharp
// GameManager.cs
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    private void Awake()
    {
        // 중복 방지: 이미 존재하면 자신을 파괴
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }
}
```

> 핵심: Bootstrap 씬에서만 Instantiate → 이후 씬 전환 시 자동 중복 방지

### 3. 씬 전환 관리자

```csharp
// SceneLoader.cs — Bootstrap에서 생성, 영구 유지
public class SceneLoader : MonoBehaviour
{
    public static SceneLoader Instance { get; private set; }

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void LoadScene(string sceneName)
    {
        StartCoroutine(LoadWithFade(sceneName));
    }

    private IEnumerator LoadWithFade(string sceneName)
    {
        // 1. 페이드 아웃
        yield return FadeManager.Instance.FadeOut(0.5f);

        // 2. 씬 전환
        yield return SceneManager.LoadSceneAsync(sceneName);

        // 3. 페이드 인
        yield return FadeManager.Instance.FadeIn(0.5f);
    }
}
```

### 4. 에디터에서 Bootstrap 없이 씬 실행하기

개발 중 Gameplay 씬만 열고 Play를 누르면 매니저가 없어 오류 발생. 이를 막는 패턴:

```csharp
// RuntimeBootstrap.cs — Gameplay 씬에 배치 (개발용)
#if UNITY_EDITOR
[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
private static void EnsureBootstrap()
{
    // Bootstrap 씬이 이미 로드된 씬 중 있는지 확인
    for (int i = 0; i < SceneManager.sceneCount; i++)
    {
        if (SceneManager.GetSceneAt(i).name == "0_Bootstrap") return;
    }
    // 없으면 Bootstrap 씬을 Additive로 로드
    SceneManager.LoadScene("0_Bootstrap", LoadSceneMode.Additive);
}
#endif
```

### 5. Build Settings 씬 순서

```
File → Build Settings → Scenes In Build:
[0] 0_Bootstrap      ← 반드시 0번 (앱 시작 씬)
[1] 1_MainMenu
[2] 2_Gameplay
[3] 3_GameOver
```

Build Index 0번 씬이 앱 시작 시 자동 로드됨 → Bootstrap이 항상 먼저 실행

---

## Additive Scene 로딩 (방 전환)

로그라이크의 방(Room)을 **Additive Load**로 교체하는 패턴:

```csharp
// RoomManager.cs
public class RoomManager : MonoBehaviour
{
    private Scene currentRoomScene;

    public IEnumerator LoadRoom(string roomSceneName)
    {
        // 기존 방 언로드
        if (currentRoomScene.IsValid())
            yield return SceneManager.UnloadSceneAsync(currentRoomScene);

        // 새 방 로드 (Additive — HUD나 Gameplay 씬은 유지)
        yield return SceneManager.LoadSceneAsync(roomSceneName, LoadSceneMode.Additive);
        currentRoomScene = SceneManager.GetSceneByName(roomSceneName);

        // 플레이어 위치 리셋
        SceneManager.SetActiveScene(currentRoomScene);
    }
}
```

---

## OnionCat 적용 포인트

### 권장 씬 구성 (OnionCat)

```
0_Bootstrap
  └── GameManager (런 데이터, 현재 HP, 업그레이드 목록)
  └── AudioManager (BGM/SFX 채널 관리)
  └── InputManager (Cat 조작 / Onion 마우스 조작)
  └── SceneLoader (씬 전환 + 페이드)

1_MainMenu
  └── 타이틀, 시작/종료 버튼

2_Gameplay
  └── Cat + Onion 캐릭터
  └── RoomManager (현재 방 추적)
  └── [Additive] HUD_Scene (HP바, 업그레이드 칸, 쿨다운)
  └── [Additive] Room_Forest_01 / Room_Cave_03 ... (방 프리팹별 씬)

3_GameOver
  └── 런 결과 요약 UI
```

### 런 데이터 유지

Bootstrap의 `GameManager`가 런 간 데이터를 보유:

```csharp
public class GameManager : MonoBehaviour
{
    // 런 시작 시 초기화
    public int CurrentHP { get; set; } = 6;
    public List<UpgradeData> ActiveUpgrades { get; } = new();
    public int CurrentFloor { get; set; } = 1;

    public void StartNewRun()
    {
        CurrentHP = 6;
        ActiveUpgrades.Clear();
        CurrentFloor = 1;
        SceneLoader.Instance.LoadScene("2_Gameplay");
    }

    public void EndRun(bool cleared)
    {
        // GameOver 씬으로 결과 전달
        SceneLoader.Instance.LoadScene("3_GameOver");
    }
}
```

---

## 주의사항

| 문제 | 원인 | 해결 |
|------|------|------|
| 매니저 오브젝트 중복 | DontDestroyOnLoad + 씬 재로드 | Awake에서 Instance null 체크 + Destroy(this) |
| Bootstrap 씬이 Build에 없음 | Index 0가 다른 씬 | Build Settings에서 0번 확인 |
| Additive 씬의 라이팅 충돌 | 각 씬의 Lighting Settings가 다름 | Active Scene을 명시적으로 SetActiveScene |
| 에디터에서만 오류 | Bootstrap 없이 씬 실행 | RuntimeInitializeOnLoadMethod로 자동 로드 |

---

## 참고 링크

- Unity 공식 - Scene Management: https://docs.unity3d.com/Manual/MultiSceneEditing.html
- Unity Learn - Additive Scene Loading: https://learn.unity.com/tutorial/loading-scenes
- Jason Weimann - Bootstrap Pattern: https://www.youtube.com/watch?v=Mk7SJkRDk6s
- Game Programming Patterns - Service Locator: https://gameprogrammingpatterns.com/service-locator.html
