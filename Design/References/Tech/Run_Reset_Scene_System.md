# 런 초기화 & 씬 리셋 시스템

리서치 날짜: 2026-08-25

## 개요

로그라이크 게임에서 "런 재시작"은 매우 빈번하게 발생한다 (게임 오버 → 재시작).
이때 **게임 상태를 완전히 초기화**하지 않으면 이전 런의 데이터(체력, 업그레이드, 적 상태 등)가
다음 런에 오염되는 버그가 발생한다. 초보 개발자에게 가장 많이 발생하는 문제 중 하나.

### 주요 문제 상황
- 이전 런의 업그레이드가 다음 런에 남아있음
- 적이 죽었다가 다음 런에 다시 등장하는 상태 오류
- DontDestroyOnLoad 오브젝트가 중복 생성됨
- Singleton이 이전 런 데이터를 들고 있음
- 이벤트(UnityEvent, Action) 구독이 해제되지 않아 null 참조

---

## 핵심 설계 원칙

### 원칙 1: 런 데이터와 영구 데이터를 명확히 분리

| 데이터 종류 | 예시 | 저장 위치 |
|-------------|------|-----------|
| 런 데이터 (Run Data) | 현재 체력, 이번 런 업그레이드, 현재 층 | 런타임 메모리만, 씬 재로드 시 초기화 |
| 영구 데이터 (Persistent Data) | 최고 기록, 언락된 캐릭터, 총 플레이 시간 | PlayerPrefs 또는 JSON 파일 |

### 원칙 2: 재시작의 두 가지 방법

**방법 A: 씬 완전 재로드**
```
GameOver → SceneManager.LoadScene("GameScene") → 모든 씬 오브젝트 초기화
```
- 장점: 단순하고 확실한 초기화
- 단점: 로딩 시간, 씬 전환 연출 필요
- **초보에게 권장**

**방법 B: 씬 재로드 없이 소프트 리셋**
```
GameOver → 모든 매니저에 Reset() 호출 → 오브젝트 풀 초기화 → 새 런 시작
```
- 장점: 빠른 재시작, 전환 부드러움
- 단점: 구현 복잡, 초기화 누락 버그 위험
- 어느 정도 경험 쌓인 후 도전

---

## Unity 구현 방법 (방법 A - 씬 재로드)

### Step 1: RunDataManager 설계

```csharp
// 런 전용 데이터 컨테이너 (씬 재로드 시 자동 소멸)
public class RunDataManager : MonoBehaviour
{
    public static RunDataManager Instance { get; private set; }

    [Header("Run State")]
    public int currentFloor = 1;
    public int currentHP = 6;
    public int maxHP = 6;
    public List<UpgradeData> currentUpgrades = new List<UpgradeData>();
    public int enemiesKilled = 0;
    public float runStartTime;

    void Awake()
    {
        // DontDestroyOnLoad 사용하지 않음 → 씬 재로드 시 자동 소멸
        if (Instance != null)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        runStartTime = Time.time;
    }

    void OnDestroy()
    {
        // Singleton 참조 정리
        if (Instance == this)
            Instance = null;
    }
}
```

### Step 2: PersistentDataManager (영구 데이터는 DontDestroyOnLoad)

```csharp
public class PersistentDataManager : MonoBehaviour
{
    public static PersistentDataManager Instance { get; private set; }

    [Header("Persistent Stats")]
    public int totalRuns = 0;
    public int totalKills = 0;
    public float bestClearTime = float.MaxValue;

    void Awake()
    {
        if (Instance != null)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject); // 영구 데이터만 유지
        LoadData();
    }

    public void SaveData()
    {
        PlayerPrefs.SetInt("TotalRuns", totalRuns);
        PlayerPrefs.SetInt("TotalKills", totalKills);
        PlayerPrefs.SetFloat("BestClearTime", bestClearTime);
        PlayerPrefs.Save();
    }

    public void LoadData()
    {
        totalRuns = PlayerPrefs.GetInt("TotalRuns", 0);
        totalKills = PlayerPrefs.GetInt("TotalKills", 0);
        bestClearTime = PlayerPrefs.GetFloat("BestClearTime", float.MaxValue);
    }
}
```

### Step 3: GameManager - 런 종료 & 재시작 처리

```csharp
using UnityEngine.SceneManagement;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [SerializeField] private string gameSceneName = "GameScene";
    [SerializeField] private string mainMenuSceneName = "MainMenu";

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    // 게임 오버 시 호출
    public void OnGameOver()
    {
        // 1. 영구 데이터 업데이트
        if (PersistentDataManager.Instance != null)
        {
            PersistentDataManager.Instance.totalRuns++;
            PersistentDataManager.Instance.totalKills += RunDataManager.Instance.enemiesKilled;
            PersistentDataManager.Instance.SaveData();
        }

        // 2. GameOver 화면 표시 (코루틴으로 딜레이 후 씬 전환)
        StartCoroutine(GameOverSequence());
    }

    private IEnumerator GameOverSequence()
    {
        // 잠깐 대기 (게임 오버 연출)
        yield return new WaitForSeconds(2f);

        // GameOver 씬으로 전환 (또는 직접 재시작)
        SceneManager.LoadScene("GameOver");
    }

    // 재시작 버튼에서 호출
    public void RestartRun()
    {
        // 씬 재로드 → RunDataManager 등 씬 오브젝트 자동 소멸 & 재생성
        SceneManager.LoadScene(gameSceneName);
    }

    // 메인 메뉴로 이동
    public void GoToMainMenu()
    {
        SceneManager.LoadScene(mainMenuSceneName);
    }
}
```

### Step 4: 이벤트 구독 해제 (OnDestroy 필수)

```csharp
// 이벤트 사용하는 모든 컴포넌트에 적용
public class EnemySpawner : MonoBehaviour
{
    void OnEnable()
    {
        GameManager.OnRoomCleared += SpawnNextWave;
    }

    void OnDisable()
    {
        // 반드시 구독 해제 - 씬 재로드 시 null 참조 방지
        GameManager.OnRoomCleared -= SpawnNextWave;
    }

    private void SpawnNextWave() { /* ... */ }
}
```

---

## 흔한 버그와 해결법

### 버그 1: Singleton 중복 생성
**증상**: DontDestroyOnLoad 오브젝트가 씬 재로드마다 계속 생성됨
```csharp
// 해결: Awake에서 중복 체크
void Awake()
{
    if (Instance != null && Instance != this)
    {
        Destroy(gameObject); // 새로 생성된 것을 제거
        return;
    }
    Instance = this;
    DontDestroyOnLoad(gameObject);
}
```

### 버그 2: 오브젝트 풀이 초기화 안 됨
**증상**: 이전 런의 투사체/적이 다음 런에 남아있음
```csharp
// ObjectPool을 씬 오브젝트로 두면 씬 재로드 시 자동 초기화
// DontDestroyOnLoad 사용 금지
public class ProjectilePool : MonoBehaviour
{
    // DontDestroyOnLoad 없음 → 씬 재로드 시 자동 파괴 & 재생성
}
```

### 버그 3: static 변수에 런 데이터 저장
**증상**: 씬 재로드해도 데이터가 남아있음
```csharp
// 잘못된 예
public class Player : MonoBehaviour
{
    public static int health = 6; // static → 씬 재로드해도 유지됨!
}

// 올바른 예
public class Player : MonoBehaviour
{
    [SerializeField] private int health = 6; // instance 변수 → 재로드 시 초기화
}
```

### 버그 4: 코루틴이 씬 전환 후 실행됨
**증상**: 씬 전환 직전에 시작된 코루틴이 새 씬에서 오류 발생
```csharp
// 해결: 씬 전환 전 StopAllCoroutines() 호출
public void RestartRun()
{
    StopAllCoroutines(); // 진행 중인 코루틴 모두 중단
    SceneManager.LoadScene(gameSceneName);
}
```

---

## OnionCat 적용 포인트

### OnionCat 런 데이터 항목
```csharp
public class RunDataManager : MonoBehaviour
{
    // 전투 상태
    public int currentHP = 6;
    public int maxHP = 6;
    public int currentFloor = 1;
    public int roomsCleared = 0;
    public int enemiesKilled = 0;

    // 업그레이드
    public List<UpgradeData> catUpgrades = new(); // Cat(근접) 업그레이드
    public List<UpgradeData> onionUpgrades = new(); // Onion(원거리) 업그레이드
    public List<UpgradeData> sharedUpgrades = new(); // 공유 업그레이드

    // 스탯 기록
    public float runStartTime;
    public int parryCount = 0;
    public int meleeKills = 0;
    public int rangedKills = 0;
}
```

### 씬 구성 권장 사항
```
씬 목록:
- MainMenu: 타이틀, 시작 버튼
- GameScene: 실제 게임 플레이 (런 데이터는 여기에만)
- GameOver: 런 결과 화면
- RunResult: 클리어 시 결과 (선택)
```

### 재시작 플로우
```
GameScene → 사망 감지
    → OnGameOver() 호출
    → 영구 데이터 저장
    → 2초 딜레이 (게임 오버 연출)
    → GameOver 씬 로드
        → "재시작" 버튼 → GameScene 재로드 (RunDataManager 초기화)
        → "메뉴" 버튼 → MainMenu 씬 로드
```

---

## 참고 링크

- Unity 공식 - SceneManager: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- Unity 공식 - DontDestroyOnLoad: https://docs.unity3d.com/ScriptReference/Object.DontDestroyOnLoad.html
- Unity Learn - Persistent Data Between Scenes: https://learn.unity.com/tutorial/implement-data-persistence-between-sessions
- Game Dev Beginner - Singleton Pattern Unity: https://gamedevbeginner.com/singletons-in-unity-the-right-way/
- Unity Forum - Best Practices for Game Reset: https://forum.unity.com/threads/best-practice-for-resetting-game-state.html
