# InGame Timer System (인게임 타이머 시스템)

리서치 날짜: 2026-08-05

## 개요

로그라이크 런 중 **경과 시간을 측정·표시하는 인게임 타이머** 시스템. 스피드런 지원, 시간 제한 챌린지 방, 최단 런 기록 저장 등에 활용됨. 일시정지 시 자동 정지, 씬 전환 시 초기화·연속 유지 선택 가능. OnionCat에서는 협력 플레이 페이스 확인 및 챌린지 룸 시간 제한에 사용.

---

## Unity 구현 방법

### 1. 기본 타이머 컴포넌트

```csharp
using UnityEngine;

public class InGameTimer : MonoBehaviour
{
    public static InGameTimer Instance { get; private set; }

    private float elapsedSeconds;
    private bool isRunning;

    public float ElapsedSeconds => elapsedSeconds;

    // 포맷: "MM:SS" 또는 "MM:SS.ff"
    public string FormattedTime
    {
        get
        {
            int minutes = Mathf.FloorToInt(elapsedSeconds / 60f);
            int seconds = Mathf.FloorToInt(elapsedSeconds % 60f);
            int centiseconds = Mathf.FloorToInt((elapsedSeconds * 100f) % 100f);
            return $"{minutes:00}:{seconds:00}.{centiseconds:00}";
        }
    }

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    private void Update()
    {
        if (isRunning)
            elapsedSeconds += Time.unscaledDeltaTime; // unscaled: 일시정지(Time.timeScale=0) 영향 없음
    }

    public void StartTimer() { isRunning = true; }
    public void StopTimer()  { isRunning = false; }
    public void ResetTimer() { elapsedSeconds = 0f; isRunning = false; }

    // 일시정지 메뉴에서 호출
    public void PauseTimer()  { isRunning = false; }
    public void ResumeTimer() { isRunning = true; }
}
```

> **주의**: `Time.unscaledDeltaTime` 사용 이유 — 히트스톱(Time.timeScale < 1) 시 타이머가 멈추지 않아야 하기 때문. 일시정지는 명시적 `PauseTimer()` 호출로 제어.

---

### 2. 타이머 UI 표시

```csharp
using UnityEngine;
using TMPro;

public class TimerDisplay : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI timerText;
    [SerializeField] private bool showOnlyWhenRunning = true;

    private void Update()
    {
        if (InGameTimer.Instance == null) return;
        timerText.text = InGameTimer.Instance.FormattedTime;

        if (showOnlyWhenRunning)
            timerText.gameObject.SetActive(InGameTimer.Instance.ElapsedSeconds > 0);
    }
}
```

---

### 3. 일시정지 메뉴 연동

```csharp
// Pause_Menu.md의 PauseManager에 추가
public class PauseManager : MonoBehaviour
{
    public void Pause()
    {
        Time.timeScale = 0f;
        InGameTimer.Instance?.PauseTimer();
        pausePanel.SetActive(true);
    }

    public void Resume()
    {
        pausePanel.SetActive(false);
        Time.timeScale = 1f;
        InGameTimer.Instance?.ResumeTimer();
    }
}
```

---

### 4. 씬 간 유지 (런 전체 타이머)

`DontDestroyOnLoad`로 InGameTimer는 씬 전환 후에도 유지됨. 런 시작 씬(예: 첫 방 진입)에서 `StartTimer()`, 게임오버 또는 클리어 씬에서 `StopTimer()`.

```csharp
// 게임 시작 시
void OnRunStart()
{
    InGameTimer.Instance.ResetTimer();
    InGameTimer.Instance.StartTimer();
}

// 런 종료 시
void OnRunEnd()
{
    InGameTimer.Instance.StopTimer();
    float finalTime = InGameTimer.Instance.ElapsedSeconds;
    SaveBestTime(finalTime);
    RunResultData.bestTimeThisRun = finalTime;
}
```

---

### 5. 최단 기록 저장

```csharp
void SaveBestTime(float runTime)
{
    float savedBest = PlayerPrefs.GetFloat("BestRunTime", float.MaxValue);
    if (runTime < savedBest)
    {
        PlayerPrefs.SetFloat("BestRunTime", runTime);
        PlayerPrefs.Save();
        ShowNewRecordEffect(); // 신기록 UI 팝업
    }
}
```

---

### 6. 챌린지 방 — 제한 시간 타이머 (카운트다운)

챌린지 방 전용: 별도 카운트다운 타이머 (전역 런 타이머와 별개).

```csharp
public class RoomChallengeTimer : MonoBehaviour
{
    [SerializeField] private float timeLimit = 30f;
    [SerializeField] private TextMeshProUGUI countdownText;
    [SerializeField] private UnityEvent onTimeUp;

    private float remaining;
    private bool isActive;

    public void StartChallenge()
    {
        remaining = timeLimit;
        isActive = true;
    }

    private void Update()
    {
        if (!isActive) return;
        remaining -= Time.deltaTime;
        int displaySeconds = Mathf.CeilToInt(remaining);
        countdownText.text = displaySeconds.ToString();

        // 5초 이하: 텍스트 빨간색 + 점멸
        if (remaining <= 5f)
            countdownText.color = Mathf.Sin(Time.time * 10f) > 0 ? Color.red : Color.white;

        if (remaining <= 0f)
        {
            isActive = false;
            countdownText.text = "0";
            onTimeUp?.Invoke();
        }
    }

    public void StopChallenge() { isActive = false; }
}
```

---

## OnionCat 적용 포인트

### 런 타이머 — 스피드런 지원
런 시작 시 상단 HUD 코너에 작은 타이머 표시 (기본 OFF, 설정에서 ON 가능). 런 결과 화면(Run_Result_Screen.md)에 클리어 타임 표시. 최단 기록 갱신 시 "신기록" 팝업 + 효과음.

### 협력 챌린지 방 타임 어택
특정 방에 30초 카운트다운 도전: "30초 내 모든 적 처치 시 희귀 아이템 획득". Cat + Crop이 빠른 역할 분담으로 효율적인 처치 순서를 소통하게 유도. RoomChallengeTimer를 방 트리거에 연결.

### 방 클리어 등급 (Deadlink 참고)
방 클리어 시 걸린 시간에 따라 S/A/B/C 등급:
```
S등급: 15초 이내 → 재화 +3
A등급: 30초 이내 → 재화 +1
B등급: 60초 이내 → 기본 보상
C등급: 60초 초과 → 보상 없음
```

### 구현 순서 (초보자용)
1. InGameTimer 싱글톤 컴포넌트 생성 (DontDestroyOnLoad)
2. TimerDisplay UI를 InGame HUD에 추가
3. 게임 시작/종료 이벤트에서 Start/Stop 호출
4. PauseManager에 Pause/Resume 연동
5. Run_Result_Screen에 최종 시간 전달
6. PlayerPrefs로 최단 기록 저장
7. (선택) RoomChallengeTimer 추가

---

## 참고 링크

- Unity Time.unscaledDeltaTime 공식 문서: https://docs.unity3d.com/ScriptReference/Time-unscaledDeltaTime.html
- Unity PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- 스피드런 타이머 구현 가이드: https://gamedevbeginner.com/how-to-make-a-timer-in-unity/
- TextMeshPro 숫자 포맷팅: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
