# 스피드런 타이머 & 인게임 기록 시스템 (Speedrun Timer System)

리서치 날짜: 2026-08-22

## 개요
인게임 타이머는 단순히 플레이 시간을 보여주는 것을 넘어, 플레이어가 자신의 런을 평가하고 재도전 동기를 갖게 하는 중요한 완성도 요소다. 로그라이크 장르에서 특히 중요한데, 런의 길이가 다양하고 플레이어가 "이번 런이 얼마나 잘 됐는지"를 수치로 확인하고 싶어하기 때문이다. Hades, Dead Cells 등 주요 로그라이크 모두 인게임 타이머를 지원한다.

---

## IGT vs RTA 구분

| 종류 | 설명 | 구현 |
|------|------|------|
| **IGT** (In-Game Time) | 실제 게임 플레이 시간 — 일시정지, 메뉴, 로딩 제외 | `Time.time` 기반 — 일시정지 시 누적 중단 |
| **RTA** (Real Time Attack) | 게임 시작부터 클리어까지 벽시계 기준 시간 | `Time.unscaledTime` — 일시정지 무시 |
| **Load Removed Time** | RTA에서 로딩 시간 제거 | 씬 전환 구간을 별도 플래그로 제외 |

로그라이크 게임에서는 **IGT**가 공정하다. 플레이어 PC 성능 차이나 로딩 시간 차이가 기록에 영향을 주지 않아야 한다.

---

## Unity 구현 방법

### 1. RunTimerManager — IGT 핵심 로직

```csharp
using UnityEngine;
using TMPro;

public class RunTimerManager : MonoBehaviour
{
    public static RunTimerManager Instance { get; private set; }

    [SerializeField] private TextMeshProUGUI timerDisplay;

    private float elapsedTime;
    private bool isRunning;
    private bool isLoading; // 씬 전환 중엔 멈춤

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    void Update()
    {
        if (!isRunning || isLoading) return;
        elapsedTime += Time.deltaTime; // 일시정지 시 Time.deltaTime = 0이 됨
        UpdateDisplay();
    }

    public void StartRun()
    {
        elapsedTime = 0f;
        isRunning = true;
    }

    public void PauseTimer() => isRunning = false;
    public void ResumeTimer() => isRunning = true;
    public void SetLoadingState(bool loading) => isLoading = loading;

    public float GetElapsedTime() => elapsedTime;

    public string GetFormattedTime()
    {
        int minutes = (int)(elapsedTime / 60f);
        int seconds = (int)(elapsedTime % 60f);
        int millis = (int)((elapsedTime * 100f) % 100f);
        return $"{minutes:00}:{seconds:00}.{millis:00}";
    }

    void UpdateDisplay()
    {
        if (timerDisplay != null)
            timerDisplay.text = GetFormattedTime();
    }
}
```

**중요**: `Time.timeScale = 0`으로 일시정지하면 `Time.deltaTime`도 0이 되어 자동으로 타이머가 멈춘다.

---

### 2. 개인 최고 기록 저장 (PlayerPrefs 활용)

```csharp
public class PersonalBestManager : MonoBehaviour
{
    private const string KEY_BEST_TIME = "BestRunTime";

    public float GetBestTime() => PlayerPrefs.GetFloat(KEY_BEST_TIME, float.MaxValue);

    public bool TrySetNewBest(float time)
    {
        float current = GetBestTime();
        if (time < current)
        {
            PlayerPrefs.SetFloat(KEY_BEST_TIME, time);
            PlayerPrefs.Save();
            return true; // 신기록!
        }
        return false;
    }

    public string GetFormattedBest()
    {
        float best = GetBestTime();
        if (best == float.MaxValue) return "--:--.--";
        return FormatTime(best);
    }

    static string FormatTime(float t)
    {
        int m = (int)(t / 60f);
        int s = (int)(t % 60f);
        int ms = (int)((t * 100f) % 100f);
        return $"{m:00}:{s:00}.{ms:00}";
    }
}
```

---

### 3. 스플릿 타이머 (구간 기록)

각 방/보스 클리어 시 스플릿 기록을 남긴다.

```csharp
public class SplitTracker : MonoBehaviour
{
    private List<(string label, float time)> splits = new();

    public void RecordSplit(string label)
    {
        float t = RunTimerManager.Instance.GetElapsedTime();
        splits.Add((label, t));
        Debug.Log($"[SPLIT] {label}: {t:F2}s");
    }

    public IReadOnlyList<(string, float)> GetSplits() => splits;

    public void ResetSplits() => splits.Clear();
}
```

호출 예시:
```csharp
// 보스 처치 시
splitTracker.RecordSplit("Boss_1_Defeat");
// 방 클리어 시
splitTracker.RecordSplit($"Room_{roomIndex}_Clear");
```

---

### 4. 런 결과 화면에서 기록 표시

```csharp
public class RunResultTimerDisplay : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI finalTimeText;
    [SerializeField] private TextMeshProUGUI bestTimeText;
    [SerializeField] private GameObject newRecordBadge;

    void Start()
    {
        float finalTime = RunTimerManager.Instance.GetElapsedTime();
        finalTimeText.text = RunTimerManager.Instance.GetFormattedTime();

        var pb = FindObjectOfType<PersonalBestManager>();
        bool isNewBest = pb.TrySetNewBest(finalTime);
        bestTimeText.text = pb.GetFormattedBest();
        newRecordBadge.SetActive(isNewBest);
    }
}
```

---

### 5. 타이머 UI — HUD 위치 권장

```
[화면 상단 우측]
  00:03.47  ← 현재 런 시간
  PB 00:02.55  ← 개인 최고기록 (회색 소자)
```

- 기본 상태: 작고 반투명하게 표시
- 신기록 페이스 진행 중: 녹색 강조
- 최고기록보다 뒤처질 때: 빨간색 표시 (선택적)

---

## OnionCat 적용 포인트

### 1. 2인 협동 기록의 공정성
- **런 타이머는 IGT 기준**으로 구현. 두 플레이어 중 한 명이 멈추면 타이머도 멈추는가? → 일시정지 처리와 통합.
- Player 2(양파)가 조준하느라 멈춰있어도 타이머는 계속 — 전략적 일시정지는 아이템 선택 화면에서만.

### 2. 스플릿 활용
- 방 클리어마다 스플릿 기록 → 런 결과 화면에서 "어느 방에서 시간을 많이 썼는지" 표시
- 초보 개발자 본인이 밸런스 테스트할 때도 유용: 특정 방이 너무 오래 걸리면 난이도 조정 신호

### 3. 구현 순서 권장
```
1. RunTimerManager 싱글톤 생성 → DontDestroyOnLoad
2. GameManager에서 런 시작 시 StartRun() 호출
3. PauseMenu에서 PauseTimer() / ResumeTimer() 연동
4. GameOver/Clear 시 타이머 정지 → RunResultScreen에 전달
5. PersonalBestManager로 기록 저장
6. (선택) SplitTracker로 구간 기록 추가
```

### 4. 주의할 점
- 씬 전환 시 `SetLoadingState(true)` 호출 잊지 말 것
- PlayerPrefs는 초기화 버그가 있을 수 있으므로, 나중에 JSON 저장으로 마이그레이션 고려
- `DontDestroyOnLoad` 타이머 오브젝트가 씬 재시작 시 중복 생성되지 않도록 싱글톤 패턴 필수

---

## 참고 링크

- Unity 공식 - Time: https://docs.unity3d.com/ScriptReference/Time.html
- Unity 공식 - PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Hades 스피드런 커뮤니티 (IGT 활용 사례): https://www.speedrun.com/hades
- Dead Cells 인게임 타이머 구현 방식 분석: 검색어 "Dead Cells speedrun IGT implementation"
- 유튜브 - Unity Run Timer Tutorial: 검색어 "Unity roguelike run timer UI"
