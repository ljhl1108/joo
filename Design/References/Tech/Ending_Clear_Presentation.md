# 엔딩 & 클리어 연출 시스템 (Ending & Clear Presentation System)

리서치 날짜: 2026-06-26

## 개요

로그라이크 게임에서 "보스를 쓰러뜨린 순간"부터 "다음 런 선택"까지의 흐름이 게임의 클라이맥스를 결정한다.  
엔딩 연출이 빈약하면 "그래서 이게 끝이야?"라는 허무감이 남고, 잘 만들면 다음 런에 대한 동기부여가 된다.  
OnionCat에서는 최종 보스 처치 → 승리 연출 → 런 결과 → 메뉴 복귀까지의 흐름을 매끄럽게 구성해야 한다.

---

## 핵심 구성 요소

### 1. 보스 처치 연출 시퀀스
- 마지막 타격 → **히트스톱** (시간 정지 0.3~0.5초)
- **사망 애니메이션** 재생 (보스 폭발, 소멸, 쓰러짐 등)
- **페이드 아웃 / 플래시** 효과
- 승리 컷씬 또는 카메라 연출

### 2. 승리 화면 (Victory Screen)
- 런 통계: 처치 수, 클리어 시간, 받은 대미지
- 획득한 업그레이드 목록
- 최고 기록 갱신 여부

### 3. 메타 진행 보상
- 영구 해금 조건 충족 알림
- 새 컨텐츠 잠금해제 표시

---

## Unity 구현 방법

### 1. 보스 처치 → 클리어 시퀀스 제어

```csharp
public class ClearSequenceManager : MonoBehaviour
{
    [SerializeField] private float hitStopDuration = 0.4f;
    [SerializeField] private float deathAnimDuration = 2.0f;
    [SerializeField] private CanvasGroup fadeOverlay;
    [SerializeField] private GameObject victoryUI;
    [SerializeField] private AudioClip victoryBGM;
    
    private AudioSource _audioSource;
    
    void Awake() => _audioSource = GetComponent<AudioSource>();
    
    // 보스 사망 시 호출
    public void OnBossDefeated()
    {
        StartCoroutine(ClearSequence());
    }
    
    private IEnumerator ClearSequence()
    {
        // 1. 히트스톱
        Time.timeScale = 0f;
        yield return new WaitForSecondsRealtime(hitStopDuration);
        Time.timeScale = 1f;
        
        // 2. 보스 사망 애니메이션 대기
        yield return new WaitForSeconds(deathAnimDuration);
        
        // 3. 입력 차단
        GameManager.Instance.SetInputEnabled(false);
        
        // 4. BGM 전환
        _audioSource.Stop();
        _audioSource.clip = victoryBGM;
        _audioSource.Play();
        
        // 5. 페이드 아웃 → 클리어 씬 페이드 인
        yield return StartCoroutine(FadeOut(1.5f));
        
        // 6. 런 결과 저장
        RunResultData result = RunResultManager.Instance.FinalizeRun(success: true);
        
        // 7. Victory UI 표시
        victoryUI.SetActive(true);
        VictoryUI victoryComp = victoryUI.GetComponent<VictoryUI>();
        victoryComp.Display(result);
        
        yield return StartCoroutine(FadeIn(1.0f));
    }
    
    private IEnumerator FadeOut(float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            fadeOverlay.alpha = Mathf.Lerp(0f, 1f, elapsed / duration);
            yield return null;
        }
        fadeOverlay.alpha = 1f;
    }
    
    private IEnumerator FadeIn(float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            fadeOverlay.alpha = Mathf.Lerp(1f, 0f, elapsed / duration);
            yield return null;
        }
        fadeOverlay.alpha = 0f;
    }
}
```

### 2. Victory UI 표시

```csharp
public class VictoryUI : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI killCountText;
    [SerializeField] private TextMeshProUGUI clearTimeText;
    [SerializeField] private TextMeshProUGUI damageReceivedText;
    [SerializeField] private TextMeshProUGUI newRecordText;
    [SerializeField] private Transform upgradeListContainer;
    [SerializeField] private GameObject upgradeItemPrefab;
    [SerializeField] private Button restartButton;
    [SerializeField] private Button mainMenuButton;
    
    public void Display(RunResultData data)
    {
        killCountText.text = $"처치 수: {data.killCount}";
        clearTimeText.text = $"클리어 시간: {FormatTime(data.clearTimeSeconds)}";
        damageReceivedText.text = $"받은 대미지: {data.totalDamageReceived}";
        
        // 최고 기록 갱신
        newRecordText.gameObject.SetActive(data.isNewRecord);
        
        // 업그레이드 목록
        foreach (var upgrade in data.acquiredUpgrades)
        {
            GameObject item = Instantiate(upgradeItemPrefab, upgradeListContainer);
            item.GetComponent<TextMeshProUGUI>().text = upgrade.displayName;
        }
        
        restartButton.onClick.AddListener(OnRestartClicked);
        mainMenuButton.onClick.AddListener(OnMainMenuClicked);
    }
    
    private string FormatTime(float seconds)
    {
        int min = Mathf.FloorToInt(seconds / 60f);
        int sec = Mathf.FloorToInt(seconds % 60f);
        return $"{min:00}:{sec:00}";
    }
    
    private void OnRestartClicked()
    {
        SceneManager.LoadScene("GameScene");
    }
    
    private void OnMainMenuClicked()
    {
        SceneManager.LoadScene("MainMenu");
    }
}
```

### 3. 런 결과 데이터 관리

```csharp
[System.Serializable]
public class RunResultData
{
    public int killCount;
    public float clearTimeSeconds;
    public int totalDamageReceived;
    public bool isNewRecord;
    public bool isSuccess;
    public List<UpgradeData> acquiredUpgrades = new List<UpgradeData>();
}

public class RunResultManager : MonoBehaviour
{
    private static RunResultManager _instance;
    public static RunResultManager Instance => _instance;
    
    private int _killCount = 0;
    private float _runStartTime;
    private int _damageReceived = 0;
    private List<UpgradeData> _upgrades = new List<UpgradeData>();
    
    void Awake()
    {
        _instance = this;
        _runStartTime = Time.time;
    }
    
    public void RecordKill() => _killCount++;
    public void RecordDamage(int amount) => _damageReceived += amount;
    public void RecordUpgrade(UpgradeData upgrade) => _upgrades.Add(upgrade);
    
    public RunResultData FinalizeRun(bool success)
    {
        float clearTime = Time.time - _runStartTime;
        
        // 최고 기록 비교
        float bestTime = PlayerPrefs.GetFloat("BestClearTime", float.MaxValue);
        bool newRecord = success && clearTime < bestTime;
        
        if (newRecord)
            PlayerPrefs.SetFloat("BestClearTime", clearTime);
        
        // 총 처치 수 누적 저장
        int totalKills = PlayerPrefs.GetInt("TotalKills", 0) + _killCount;
        PlayerPrefs.SetInt("TotalKills", totalKills);
        PlayerPrefs.Save();
        
        return new RunResultData
        {
            killCount = _killCount,
            clearTimeSeconds = clearTime,
            totalDamageReceived = _damageReceived,
            isNewRecord = newRecord,
            isSuccess = success,
            acquiredUpgrades = _upgrades
        };
    }
}
```

### 4. 카메라 클리어 연출 (선택적)

```csharp
// 보스 사망 후 카메라가 느리게 줌인하는 연출
public class ClearCameraEffect : MonoBehaviour
{
    [SerializeField] private CinemachineVirtualCamera virtualCam;
    [SerializeField] private float zoomInSize = 3f;
    [SerializeField] private float zoomDuration = 1.5f;
    
    public IEnumerator PlayClearZoom()
    {
        float startSize = virtualCam.m_Lens.OrthographicSize;
        float elapsed = 0f;
        
        while (elapsed < zoomDuration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.SmoothStep(0f, 1f, elapsed / zoomDuration);
            virtualCam.m_Lens.OrthographicSize = Mathf.Lerp(startSize, zoomInSize, t);
            yield return null;
        }
    }
}
```

---

## OnionCat 적용 포인트

### 연출 시퀀스 제안
1. 보스 최후 타격 → **히트스톱 0.4초** + 화면 흰색 플래시
2. 보스 사망 애니메이션 (폭발 파티클, 2초)
3. Cat + Crop 승리 포즈 애니메이션 재생 (커스텀 Victory 스프라이트)
4. 카메라 **줌인** → Cat과 Crop에 포커스 (1.5초)
5. BGM → 승리 팡파레로 전환
6. **페이드 아웃** → 결과 화면 페이드 인

### Victory UI 포함 요소
- 처치 수 / 클리어 시간 / 받은 대미지
- **Cat 기여도 vs Crop 기여도** (각자 가한 대미지 분리 표시) → 재미 요소
- 이번 런에서 획득한 업그레이드 리스트 (아이콘으로)
- "다시 도전" / "메인 메뉴" 버튼

### 주의 사항
- `Time.timeScale = 0f` 히트스톱 중에는 `WaitForSecondsRealtime` 사용 필수
- SceneManager.LoadScene 전에 반드시 `Time.timeScale = 1f` 복구
- 결과 화면에서 BGM이 다음 씬으로 넘어가지 않게 `AudioSource` 관리 필요
  - `DontDestroyOnLoad`된 AudioManager를 통해 BGM 전환 처리 권장

### 구현 순서 (초보자용)
1. `RunResultManager` 싱글톤 만들기 (킬카운트, 시간 추적)
2. 보스 `OnDeath()`에서 `ClearSequenceManager.OnBossDefeated()` 호출
3. 간단한 **검정 패널 페이드** 먼저 구현
4. Victory UI 배치 (TextMeshPro 텍스트 + 버튼 2개)
5. `RunResultManager.FinalizeRun()` 연결
6. 나중에 카메라 줌, 파티클, BGM 전환 추가

---

## 참고 링크

- Unity SceneManager 공식 문서: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- Cinemachine Impulse (화면 진동): https://docs.unity3d.com/Packages/com.unity.cinemachine@2.9/manual/CinemachineImpulse.html
- PlayerPrefs 공식 문서: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- TextMeshPro 시작 가이드: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
- Hades 엔딩 연출 분석: https://www.youtube.com/results?search_query=hades+ending+sequence+analysis (YouTube 검색 권장)
