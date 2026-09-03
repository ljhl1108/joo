# 빠른 재시작 & 런 간 전환 화면 시스템

리서치 날짜: 2026-09-03

## 개요

로그라이크의 핵심 중독성은 **"한 판 더"** 심리에서 온다. 사망 또는 클리어 후 다음 런까지의 마찰(friction)을 최소화하는 것이 플레이어 리텐션에 직결된다. Dead Cells는 사망 후 0.5초 안에 재시작 버튼을 보여주고, Hades는 패배를 스토리로 감싸 이탈 충동을 막는다. OnionCat도 **두 플레이어 모두에게 빠른 재시작 경험**을 설계해야 한다.

---

## 핵심 설계 원칙

1. **사망 → 결과 화면 → 재시작 3단계를 10초 이내로** (불필요한 로딩 없음)
2. **두 플레이어 중 한 명만 확인해도 재시작 가능** (한 명이 기다리지 않도록)
3. **이전 런 결과 요약을 간단히 보여준 뒤 자동 진행** (결과 화면이 중단이 아니라 전환의 일부)
4. **메타 진행도 확인 가능** (새로 해금된 것이 있으면 여기서 보여주기)

---

## Unity 구현 방법

### 1. 런 간 전환 흐름 설계

```
[런 종료 (사망/클리어)]
        ↓ (0.5초 사망 애니메이션)
[런 결과 오버레이 표시]
  - 처치 수, 클리어 시간, 획득 아이템 목록
  - 새 해금 항목 (있으면 반짝임 표시)
        ↓ (두 플레이어 중 하나가 버튼 누르거나 5초 자동)
[씬 전환 — 페이드 아웃]
        ↓
[런 시작 씬 (Run_Start_Screen)]
  - 난이도 선택
  - 캐릭터 확인 (선택 불가 — OnionCat은 고정)
  - 시작 확인 (양 플레이어 버튼)
        ↓
[게임플레이 씬 로드]
```

### 2. RunEndManager — 런 종료 처리

```csharp
// RunEndManager.cs
public class RunEndManager : MonoBehaviour
{
    [SerializeField] private GameObject resultOverlay;
    [SerializeField] private float autoAdvanceDelay = 5f;

    private Coroutine autoAdvanceCoroutine;

    public void OnRunEnded(bool isVictory)
    {
        // 런 데이터 저장
        RunDataStore.Save(RunDataCollector.GetCurrentRunData());

        // 결과 오버레이 표시
        resultOverlay.SetActive(true);
        ResultOverlayUI.Instance.Populate(RunDataCollector.GetCurrentRunData(), isVictory);

        // 자동 진행 타이머
        autoAdvanceCoroutine = StartCoroutine(AutoAdvanceRoutine());

        // 입력 등록 (UI 맵으로 전환)
        GameStateManager.Instance.EnterPostRun();
    }

    public void OnPlayerPressedContinue()
    {
        if (autoAdvanceCoroutine != null)
            StopCoroutine(autoAdvanceCoroutine);
        StartCoroutine(TransitionToRunStart());
    }

    private IEnumerator AutoAdvanceRoutine()
    {
        yield return new WaitForSecondsRealtime(autoAdvanceDelay);
        StartCoroutine(TransitionToRunStart());
    }

    private IEnumerator TransitionToRunStart()
    {
        // 페이드 아웃
        yield return FadeTransitionManager.Instance.FadeOut(0.5f);
        // 런 데이터 초기화
        RunDataCollector.Reset();
        // 씬 전환
        SceneManager.LoadScene("RunStartScene");
    }
}
```

### 3. RunDataCollector — 런 데이터 수집

```csharp
// RunDataCollector.cs — 싱글톤, DontDestroyOnLoad
public class RunDataCollector : MonoBehaviour
{
    public static RunDataCollector Instance { get; private set; }

    private int killCount;
    private float runDuration;
    private List<string> collectedItems = new();
    private float startTime;

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void StartRun() => startTime = Time.unscaledTime;

    public void RegisterKill() => killCount++;

    public void RegisterItemPickup(string itemId) => collectedItems.Add(itemId);

    public static RunData GetCurrentRunData()
    {
        return new RunData
        {
            killCount = Instance.killCount,
            durationSeconds = Time.unscaledTime - Instance.startTime,
            items = Instance.collectedItems.ToArray()
        };
    }

    public static void Reset()
    {
        Instance.killCount = 0;
        Instance.collectedItems.Clear();
    }
}

[System.Serializable]
public class RunData
{
    public int killCount;
    public float durationSeconds;
    public string[] items;
}
```

### 4. RunStartScreen — 런 시작 전 화면

```csharp
// RunStartScreen.cs
public class RunStartScreen : MonoBehaviour
{
    [SerializeField] private Button startButton;
    [SerializeField] private GameObject p1ReadyIndicator;
    [SerializeField] private GameObject p2ReadyIndicator;

    private bool p1Ready = false;
    private bool p2Ready = false;

    public void OnP1Ready()
    {
        p1Ready = true;
        p1ReadyIndicator.SetActive(true);
        CheckBothReady();
    }

    public void OnP2Ready()
    {
        p2Ready = true;
        p2ReadyIndicator.SetActive(true);
        CheckBothReady();
    }

    private void CheckBothReady()
    {
        if (p1Ready && p2Ready)
            StartCoroutine(StartRunSequence());
    }

    private IEnumerator StartRunSequence()
    {
        yield return new WaitForSecondsRealtime(0.3f); // 짧은 연출 딜레이
        yield return FadeTransitionManager.Instance.FadeOut(0.5f);
        RunDataCollector.Instance.StartRun();
        SceneManager.LoadScene("GameplayScene");
    }
}
```

### 5. 새 해금 알림 연동

```csharp
// UnlockChecker.cs — RunEndManager에서 호출
public class UnlockChecker : MonoBehaviour
{
    public List<UnlockData> CheckNewUnlocks(RunData runData)
    {
        var newUnlocks = new List<UnlockData>();

        // 예: 처치 수 50 달성 → "철갑 적" 해금
        if (runData.killCount >= 50 && !PlayerPrefs.HasKey("unlock_armored_enemy"))
        {
            PlayerPrefs.SetInt("unlock_armored_enemy", 1);
            newUnlocks.Add(new UnlockData { id = "armored_enemy", displayName = "철갑 병사" });
        }

        return newUnlocks;
    }
}
```

---

## OnionCat 적용 포인트

### 두 플레이어 재시작 UX 설계

```
[런 결과 화면]
┌──────────────────────────────────┐
│  이번 런: 처치 23 | 시간 4:32     │
│  획득 아이템: [아이콘 목록]        │
│                                   │
│  ★ 새로운 해금: 독소 방울 (Onion)  │
│                                   │
│  [P1 Cat] ──── 계속하기 ────      │
│  [P2 Onion] ─ 계속하기 ────      │
│         (자동 진행: 5초)           │
└──────────────────────────────────┘
```

- P1 또는 P2 중 하나만 "계속" 눌러도 진행 (기다림 방지)
- 5초 자동 진행 카운트다운 표시
- 새 해금 항목은 반짝임 효과로 명확히 표시

### OnionCat 전용 런 사이 정보 표시

- **Cat 기여도**: 슬래시 처치 수 vs Onion 투사체 처치 수 (팀 균형 분석)
- **파리 성공률**: Onion 방패 파리 성공/시도 비율
- **대시 횟수**: Cat이 무적 대시를 얼마나 활용했는지
- → 두 플레이어가 자신의 역할을 얼마나 잘 수행했는지 빠르게 파악

### 주의사항 (구현 순서)

1. `RunDataCollector`를 DontDestroyOnLoad 싱글톤으로 먼저 구현
2. 게임오버 이벤트(`EventBus`나 `Action` 델리게이트)를 명확히 정의
3. 결과 오버레이는 별도 씬이 아닌 **인게임 오버레이(Canvas)**로 — 씬 전환 비용 없음
4. `Time.unscaledTime` 사용 필수 (일시정지 중 런 타이머 멈추지 않도록)
5. `PlayerPrefs`로 간단한 해금 상태 관리, 이후 JSON으로 마이그레이션 가능

---

## 참고 링크

- Unity SceneManager: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- Unity PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Game Feel (재시작 경험 디자인): https://www.gamedeveloper.com/design/game-feel-the-secret-ingredient
- Dead Cells 재시작 분석: https://www.youtube.com/watch?v=mFw8M1nKyF4
- Hades 내러티브 재시작 설계: https://www.youtube.com/watch?v=bTdn6V1AJd8
