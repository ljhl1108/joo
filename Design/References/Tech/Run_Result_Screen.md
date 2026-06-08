# 런 결과 화면 (Run Result Screen)

## 개요
런 결과 화면은 플레이어가 죽거나 게임을 클리어했을 때 보여주는 요약 화면이다. 처치 수, 클리어 시간, 획득한 업그레이드, 최고 기록 갱신 여부 등을 보여주며 **"이번 런에 무언가 의미 있었다"는 피드백**을 준다. 로그라이크에서 재도전 의욕을 높이는 핵심 UX.

---

## Unity 구현 방법

### 1. 런 데이터 수집 (RunData)
런 내내 통계를 기록할 데이터 클래스:

```csharp
[System.Serializable]
public class RunData
{
    public int killCount;
    public int roomsCleared;
    public float runDurationSeconds;
    public bool isClear;
    public List<string> upgradesObtained = new();
    public int totalDamageTaken;
    public int bossesDefeated;

    // 타이머
    private float startTime;
    public void StartTimer() => startTime = Time.time;
    public void StopTimer() => runDurationSeconds = Time.time - startTime;
    public string FormattedTime()
    {
        int min = (int)(runDurationSeconds / 60);
        int sec = (int)(runDurationSeconds % 60);
        return $"{min:D2}:{sec:D2}";
    }
}
```

### 2. 런 매니저 (RunManager) — 싱글톤
게임 전반에서 데이터를 쌓는 중앙 관리자:

```csharp
public class RunManager : MonoBehaviour
{
    public static RunManager Instance { get; private set; }
    public RunData CurrentRun { get; private set; }

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void StartNewRun()
    {
        CurrentRun = new RunData();
        CurrentRun.StartTimer();
    }

    public void RegisterKill() => CurrentRun.killCount++;
    public void RegisterRoomClear() => CurrentRun.roomsCleared++;
    public void RegisterDamage(int dmg) => CurrentRun.totalDamageTaken += dmg;
    public void RegisterUpgrade(string name) => CurrentRun.upgradesObtained.Add(name);

    public void EndRun(bool isClear)
    {
        CurrentRun.isClear = isClear;
        CurrentRun.StopTimer();
        SaveBestRecord();
        SceneManager.LoadScene("RunResultScene");
    }

    void SaveBestRecord()
    {
        int prevBest = PlayerPrefs.GetInt("BestKillCount", 0);
        if (CurrentRun.killCount > prevBest)
            PlayerPrefs.SetInt("BestKillCount", CurrentRun.killCount);

        float prevBestTime = PlayerPrefs.GetFloat("BestClearTime", float.MaxValue);
        if (CurrentRun.isClear && CurrentRun.runDurationSeconds < prevBestTime)
            PlayerPrefs.SetFloat("BestClearTime", CurrentRun.runDurationSeconds);

        PlayerPrefs.Save();
    }
}
```

### 3. 런 결과 UI 스크립트

```csharp
public class RunResultUI : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI titleText;
    [SerializeField] private TextMeshProUGUI killCountText;
    [SerializeField] private TextMeshProUGUI timeText;
    [SerializeField] private TextMeshProUGUI roomsClearedText;
    [SerializeField] private TextMeshProUGUI damageTakenText;
    [SerializeField] private Transform upgradeListParent;
    [SerializeField] private GameObject upgradeItemPrefab;
    [SerializeField] private GameObject newRecordBadge;
    [SerializeField] private Button retryButton;
    [SerializeField] private Button mainMenuButton;

    void Start()
    {
        var run = RunManager.Instance.CurrentRun;

        titleText.text = run.isClear ? "클리어!" : "도전 종료";
        killCountText.text = $"처치: {run.killCount}";
        timeText.text = $"시간: {run.FormattedTime()}";
        roomsClearedText.text = $"방 클리어: {run.roomsCleared}";
        damageTakenText.text = $"받은 피해: {run.totalDamageTaken}";

        foreach (var upgradeName in run.upgradesObtained)
        {
            var item = Instantiate(upgradeItemPrefab, upgradeListParent);
            item.GetComponentInChildren<TextMeshProUGUI>().text = upgradeName;
        }

        // 신기록 배지
        int prevBest = PlayerPrefs.GetInt("BestKillCount", 0);
        newRecordBadge.SetActive(run.killCount >= prevBest && run.killCount > 0);

        retryButton.onClick.AddListener(OnRetry);
        mainMenuButton.onClick.AddListener(OnMainMenu);
    }

    void OnRetry()
    {
        RunManager.Instance.StartNewRun();
        SceneManager.LoadScene("GameScene");
    }

    void OnMainMenu() => SceneManager.LoadScene("MainMenuScene");
}
```

### 4. 숫자 카운트업 연출 (선택 사항, 추천)
숫자가 0에서 실제 값까지 올라가는 연출로 만족감 강화:

```csharp
IEnumerator CountUp(TextMeshProUGUI label, string prefix, int targetValue, float duration)
{
    float elapsed = 0f;
    while (elapsed < duration)
    {
        elapsed += Time.deltaTime;
        int current = Mathf.RoundToInt(Mathf.Lerp(0, targetValue, elapsed / duration));
        label.text = $"{prefix}: {current}";
        yield return null;
    }
    label.text = $"{prefix}: {targetValue}";
}
```

### 5. 씬 구성 (Unity Editor에서 해야 할 작업)
- `RunResultScene` 씬 생성
- Canvas → 결과 패널 UI 배치
- `RunResultUI` 스크립트를 Canvas에 부착
- `[SerializeField]` 항목들 Inspector에서 드래그 연결 필요
- File → Build Settings에 `RunResultScene` 추가

---

## OnionCat 적용 포인트

### 2인 협동 특화 통계
혼자 하는 게임과 달리 OnionCat은 두 플레이어 각각의 기여도를 보여줄 수 있음:

```
[런 결과]
총 처치: 47
  └ 고양이(근접): 28마리
  └ 양파(원거리): 19마리

클리어 시간: 14:32
받은 피해: 85 (패리 성공: 6회)
방 클리어: 12
```

- **패리 성공 횟수** 표시 → 양파 플레이어에게 활약 피드백
- **대시 사용 횟수** → 고양이 플레이어 피드백
- 두 플레이어가 화면을 보며 서로의 기여를 인정하는 사회적 순간 생성

### 업그레이드 목록 표시
획득한 업그레이드를 카드 형태로 나열. 각 카드에 고양이/양파 아이콘으로 누구 전용인지 표시.

### 최고 기록 저장 항목
- 최단 클리어 시간
- 최다 처치 수
- 최고 패리 성공 횟수
- 무피해 방 클리어 수 (Perfect Room)

### 재도전 유도 메시지
```csharp
string[] retryHints = {
    "힌트: 근접 전용 적에게 원거리 공격은 효과가 없어요!",
    "힌트: 패리 성공 시 양파의 다음 공격이 강화됩니다.",
    "힌트: 고양이 대시 중에는 무적입니다."
};
hintText.text = retryHints[Random.Range(0, retryHints.Length)];
```

---

## 참고 링크
- Unity SceneManager 공식 문서: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- Unity PlayerPrefs 공식 문서: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- TextMeshPro 공식 문서: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
- Game UI Database (결과 화면 레퍼런스): https://www.gameuidatabase.com/index.php?scrn=137
- Hades 런 결과 화면 분석 (유튜브 검색): "Hades end screen design"
