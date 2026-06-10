# 업적/통계 시스템 (Achievement & Stats System)

## 개요

업적(Achievement)과 통계(Stats) 시스템은 **단기 보상(런 내 목표)을 넘어 장기 동기부여**를 제공하는 메타 레이어다.  
로그라이크에서 특히 중요한데, 런이 짧고 반복되기 때문에 "누적되는 무언가"가 없으면 플레이어가 금방 이탈한다.  
OnionCat의 경우 두 플레이어의 플레이 스타일 차이를 통계로 시각화하거나, 업적으로 특정 전술을 유도할 수 있다.

---

## Unity 구현 방법

### 1. 통계 데이터 구조 설계

```csharp
[System.Serializable]
public class GameStats
{
    // 누적 통계 (런 간 영구 보존)
    public int totalRuns;
    public int totalKills;
    public int totalDeaths;
    public float totalPlayTimeSeconds;
    public int totalDamageDealt;
    public int totalDamageTaken;
    
    // 베스트 기록
    public int bestKillCount;
    public float bestClearTimeSeconds;
    public int highestFloorReached;
    
    // 캐릭터별 통계
    public int catMeleeHits;
    public int onionRangedHits;
    public int onionParrySuccesses;
    public int onionShieldBlocks;
    
    // 협력 통계
    public int synergyKills; // 두 플레이어가 같은 적에게 동시 공격
}
```

### 2. 통계 매니저 (싱글턴)

```csharp
public class StatsManager : MonoBehaviour
{
    public static StatsManager Instance { get; private set; }
    
    private GameStats _stats;
    private const string SAVE_KEY = "GameStats";

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        Load();
    }

    public void RecordKill() 
    { 
        _stats.totalKills++;
        if (++_currentRunKills > _stats.bestKillCount)
            _stats.bestKillCount = _currentRunKills;
    }

    public void RecordParry() => _stats.onionParrySuccesses++;

    public void RecordRunEnd(bool cleared, float duration)
    {
        _stats.totalRuns++;
        _stats.totalPlayTimeSeconds += duration;
        if (cleared && duration < _stats.bestClearTimeSeconds || _stats.bestClearTimeSeconds == 0)
            _stats.bestClearTimeSeconds = duration;
        Save();
        CheckAchievements(); // 런 종료 시 업적 체크
    }

    private void Save()
    {
        string json = JsonUtility.ToJson(_stats);
        PlayerPrefs.SetString(SAVE_KEY, json);
        PlayerPrefs.Save();
    }

    private void Load()
    {
        string json = PlayerPrefs.GetString(SAVE_KEY, "");
        _stats = string.IsNullOrEmpty(json) ? new GameStats() : JsonUtility.FromJson<GameStats>(json);
    }

    public GameStats GetStats() => _stats;
    
    private int _currentRunKills; // 현재 런 한정 카운터
    public void ResetRunCounters() => _currentRunKills = 0;
}
```

### 3. 업적 데이터 구조

```csharp
public enum AchievementID
{
    FirstRun,           // 첫 런 완주
    KillCount10,        // 총 처치 10
    KillCount100,       // 총 처치 100
    ParryMaster,        // 패리 50회
    NoDamageBoss,       // 보스 무피격 처치
    Speedrun,           // 5분 이내 클리어
    CoopSynergy         // 시너지 킬 30회
}

[System.Serializable]
public class AchievementData
{
    public AchievementID id;
    public string titleKR;
    public string descriptionKR;
    public bool isUnlocked;
    public bool isNotified; // 알림 표시 여부
}
```

### 4. 업적 매니저

```csharp
public class AchievementManager : MonoBehaviour
{
    public static AchievementManager Instance { get; private set; }
    
    [SerializeField] private AchievementPopupUI _popupUI; // 유니티 에디터에서 드래그 앤 드롭 설정 필요
    
    private List<AchievementData> _achievements = new();
    private const string SAVE_KEY = "Achievements";

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        InitAchievements();
        Load();
    }

    private void InitAchievements()
    {
        _achievements = new List<AchievementData>
        {
            new() { id = AchievementID.FirstRun, titleKR = "첫 발걸음", descriptionKR = "첫 런을 완주하라" },
            new() { id = AchievementID.KillCount10, titleKR = "신참 사냥꾼", descriptionKR = "적 10마리 처치" },
            new() { id = AchievementID.KillCount100, titleKR = "백전노장", descriptionKR = "적 100마리 처치" },
            new() { id = AchievementID.ParryMaster, titleKR = "패리의 달인", descriptionKR = "패리 50회 성공" },
            new() { id = AchievementID.NoDamageBoss, titleKR = "무결", descriptionKR = "보스를 무피격으로 처치" },
            new() { id = AchievementID.Speedrun, titleKR = "질주", descriptionKR = "5분 이내에 클리어" },
            new() { id = AchievementID.CoopSynergy, titleKR = "환상의 콤비", descriptionKR = "협력 공격으로 30회 처치" },
        };
    }

    public void CheckAchievements()
    {
        var stats = StatsManager.Instance.GetStats();
        TryUnlock(AchievementID.FirstRun,     stats.totalRuns >= 1);
        TryUnlock(AchievementID.KillCount10,  stats.totalKills >= 10);
        TryUnlock(AchievementID.KillCount100, stats.totalKills >= 100);
        TryUnlock(AchievementID.ParryMaster,  stats.onionParrySuccesses >= 50);
        TryUnlock(AchievementID.CoopSynergy,  stats.synergyKills >= 30);
    }

    public void CheckSpeedrun(float clearTime)
    {
        TryUnlock(AchievementID.Speedrun, clearTime <= 300f);
    }

    public void CheckNoDamageBoss(bool tookNoDamage)
    {
        TryUnlock(AchievementID.NoDamageBoss, tookNoDamage);
    }

    private void TryUnlock(AchievementID id, bool condition)
    {
        var achievement = _achievements.Find(a => a.id == id);
        if (achievement == null || achievement.isUnlocked || !condition) return;
        
        achievement.isUnlocked = true;
        achievement.isNotified = false;
        Save();
        _popupUI?.ShowAchievement(achievement);
    }

    private void Save()
    {
        var saveData = _achievements.Select(a => new { a.id, a.isUnlocked }).ToList();
        PlayerPrefs.SetString(SAVE_KEY, JsonUtility.ToJson(new { achievements = saveData }));
        PlayerPrefs.Save();
    }

    private void Load()
    {
        // PlayerPrefs에서 잠금 해제 상태만 복원
        foreach (var achievement in _achievements)
        {
            string key = $"Achievement_{achievement.id}";
            achievement.isUnlocked = PlayerPrefs.GetInt(key, 0) == 1;
        }
    }
    
    public List<AchievementData> GetAllAchievements() => _achievements;
}
```

### 5. 업적 팝업 UI

```csharp
public class AchievementPopupUI : MonoBehaviour
{
    [SerializeField] private Text _titleText;        // 유니티 에디터에서 드래그 앤 드롭 설정 필요
    [SerializeField] private Text _descriptionText;  // 유니티 에디터에서 드래그 앤 드롭 설정 필요
    [SerializeField] private Animator _animator;     // 유니티 에디터에서 드래그 앤 드롭 설정 필요
    
    private Queue<AchievementData> _queue = new();
    private bool _isShowing;

    public void ShowAchievement(AchievementData achievement)
    {
        _queue.Enqueue(achievement);
        if (!_isShowing) StartCoroutine(ShowNextInQueue());
    }

    private IEnumerator ShowNextInQueue()
    {
        _isShowing = true;
        while (_queue.Count > 0)
        {
            var achievement = _queue.Dequeue();
            _titleText.text = achievement.titleKR;
            _descriptionText.text = achievement.descriptionKR;
            _animator.SetTrigger("Show");
            yield return new WaitForSeconds(3f); // 3초 표시 후 사라짐
            _animator.SetTrigger("Hide");
            yield return new WaitForSeconds(0.5f); // 숨김 애니메이션 대기
        }
        _isShowing = false;
    }
}
```

### 6. 통계 화면 (게임 오버/클리어 화면에 포함)

```csharp
public class StatsDisplayUI : MonoBehaviour
{
    [SerializeField] private Text _totalRunsText;
    [SerializeField] private Text _totalKillsText;
    [SerializeField] private Text _bestTimeText;
    [SerializeField] private Text _parryCountText;

    private void OnEnable()
    {
        var stats = StatsManager.Instance.GetStats();
        _totalRunsText.text = $"총 런: {stats.totalRuns}회";
        _totalKillsText.text = $"총 처치: {stats.totalKills}마리";
        _bestTimeText.text = stats.bestClearTimeSeconds > 0 
            ? $"최고 기록: {FormatTime(stats.bestClearTimeSeconds)}" 
            : "최고 기록: -";
        _parryCountText.text = $"패리 성공: {stats.onionParrySuccesses}회";
    }

    private string FormatTime(float seconds)
    {
        int m = (int)seconds / 60;
        int s = (int)seconds % 60;
        return $"{m:00}:{s:00}";
    }
}
```

---

## OnionCat 적용 포인트

### 협력 특화 업적 아이디어
| 업적명 | 조건 | 효과 |
|--------|------|------|
| 첫 발걸음 | 첫 런 완주 | 없음 (달성감) |
| 환상의 콤비 | 시너지 킬 30회 | Cat 슬래시 색상 변경 |
| 무결의 방패 | 패리 50회 | Onion 방패 이펙트 강화 |
| 속전속결 | 5분 이내 클리어 | 스피드런 타이머 UI 해금 |
| 불굴 | 10번 런 완주 | 타이틀 화면 배경 변경 |
| 약점 사냥꾼 | 약점 공격으로 100킬 | 적 HP바에 약점 타입 아이콘 표시 |

### 구현 순서 (OnionCat)
1. `GameStats` 클래스 정의 (PlayerPrefs JSON 저장)
2. `StatsManager` 싱글턴 생성, DontDestroyOnLoad
3. 각 이벤트 발생 지점에 `StatsManager.Instance.Record...()` 호출 추가
4. `AchievementManager` 생성, 런 종료 시 `CheckAchievements()` 호출
5. 팝업 UI 프리팹 제작 + `AchievementPopupUI` 연결
6. 게임 오버/클리어 화면에 `StatsDisplayUI` 추가

### 주의사항
- `PlayerPrefs`는 PC에서 레지스트리에 저장됨. 민감한 데이터는 JSON 파일 저장 권장
- 업적은 한번 해금되면 취소 불가 — `isUnlocked`는 절대 false로 되돌리지 않음
- 통계 이벤트 호출을 null 체크 없이 하면 씬 전환 시 크래시 — `Instance?.Record...()` 패턴 사용
- 플레이어 2명의 스탯을 구분하려면 `catStats`, `onionStats`로 분리해서 관리

---

## 참고 링크
- Unity 공식 - PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Unity 공식 - JsonUtility: https://docs.unity3d.com/ScriptReference/JsonUtility.html
- Unity Learn - Save/Load System: https://learn.unity.com/tutorial/implement-data-persistence-between-sessions
- 유튜브 - "Unity Achievement System" (Tarodev, Code Monkey)
- Steam 업적 연동 (Steamworks): https://partner.steamgames.com/doc/features/achievements (출시 시 적용)
