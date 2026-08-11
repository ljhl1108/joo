# 온라인 런 리더보드 시스템 (Online Leaderboard via Unity Gaming Services)

리서치 날짜: 2026-08-11

## 개요

**온라인 리더보드**란 플레이어의 런 기록(클리어 시간, 점수 등)을 클라우드에 저장해 전 세계 플레이어들과 순위를 공유하는 시스템이다.

기존 `Leaderboard_Highscore_System.md`는 로컬 저장 방식을 다뤘다면, 이 문서는 **Unity Gaming Services(UGS) Leaderboards** 서비스를 통한 온라인 구현을 다룬다.

**OnionCat에서 왜 필요한가**:
- 협력 로그라이크에서 "세계 최속 2인 클리어" 경쟁은 강력한 리플레이 동기
- Steam 출시 시 글로벌 랭킹이 있으면 마케팅 효과 (스피드런 커뮤니티 형성)
- 무료 서비스(UGS 무료 티어 존재), Unity와 완벽 통합
- 초보 개발자도 서버리스로 구현 가능

---

## Unity 구현 방법

### 1. UGS 프로젝트 설정

**Unity Editor 설정**:
1. `Edit → Project Settings → Services` 에서 Unity 프로젝트 연결
2. Package Manager에서 `com.unity.services.leaderboards` 설치
3. UGS 대시보드 (https://cloud.unity.com) 에서 Leaderboard ID 생성
   - 예시: `speedrun_coop`, `score_endless`, `boss_clear_time`

**대시보드 설정**:
- **Leaderboard ID**: `onioncat_speedrun`
- **Sort Order**: Ascending (낮은 시간이 1위)
- **Tie Breaking**: Earliest Submit (같은 시간이면 먼저 등록한 사람이 우선)
- **Reset Frequency**: None (영구 유지) or Weekly (주간 리셋)

### 2. 기본 초기화

```csharp
using Unity.Services.Core;
using Unity.Services.Authentication;
using Unity.Services.Leaderboards;

public class UGSLeaderboardManager : MonoBehaviour {
    private static UGSLeaderboardManager _instance;
    public static UGSLeaderboardManager Instance => _instance;

    private const string LEADERBOARD_ID = "onioncat_speedrun";

    private async void Awake() {
        if (_instance != null) { Destroy(gameObject); return; }
        _instance = this;
        DontDestroyOnLoad(gameObject);

        await InitializeUGS();
    }

    private async System.Threading.Tasks.Task InitializeUGS() {
        try {
            await UnityServices.InitializeAsync();

            if (!AuthenticationService.Instance.IsSignedIn) {
                // 익명 로그인 (계정 없이도 랭킹 등록 가능)
                await AuthenticationService.Instance.SignInAnonymouslyAsync();
                Debug.Log($"[UGS] 익명 로그인 성공: {AuthenticationService.Instance.PlayerId}");
            }
        } catch (System.Exception e) {
            Debug.LogWarning($"[UGS] 초기화 실패: {e.Message}");
        }
    }
}
```

### 3. 점수 제출 (런 클리어 시)

```csharp
public async System.Threading.Tasks.Task SubmitRunScore(float clearTimeSeconds, string playerDisplayName = null) {
    if (!AuthenticationService.Instance.IsSignedIn) return;

    // 점수는 정수로 제출 (밀리초 단위로 정밀도 유지)
    long scoreMs = (long)(clearTimeSeconds * 1000);

    try {
        var options = new AddPlayerScoreOptions {
            Metadata = $"{{\"name\":\"{playerDisplayName ?? "Anonymous"}\"," +
                        $"\"floor\":{GameManager.Instance.CurrentFloor}}}"
        };

        var response = await LeaderboardsService.Instance.AddPlayerScoreAsync(
            LEADERBOARD_ID, scoreMs, options
        );

        Debug.Log($"[UGS] 제출 성공! 순위: {response.Rank + 1}위");
        OnScoreSubmitted?.Invoke(response.Rank + 1);
    } catch (System.Exception e) {
        Debug.LogWarning($"[UGS] 제출 실패: {e.Message}");
    }
}

public event System.Action<int> OnScoreSubmitted;
```

### 4. 순위 조회

```csharp
// 전체 상위 10위 조회
public async System.Threading.Tasks.Task<List<LeaderboardEntry>> GetTopScores(int count = 10) {
    try {
        var options = new GetScoresOptions { Limit = count };
        var response = await LeaderboardsService.Instance.GetScoresAsync(LEADERBOARD_ID, options);

        return response.Results.Select(e => new LeaderboardEntry {
            rank = e.Rank + 1,
            playerName = ExtractName(e.Metadata),
            clearTimeMs = (long)e.Score,
            clearTimeFormatted = FormatTime((long)e.Score)
        }).ToList();

    } catch (System.Exception e) {
        Debug.LogWarning($"[UGS] 조회 실패: {e.Message}");
        return null;
    }
}

// 내 주변 순위 조회 (내 ±5위)
public async System.Threading.Tasks.Task<List<LeaderboardEntry>> GetPlayerRange() {
    try {
        var options = new GetPlayerScoreOptions { IncludeMetadata = true };
        var playerScore = await LeaderboardsService.Instance.GetPlayerScoreAsync(LEADERBOARD_ID, options);

        var rangeOptions = new GetScoresByRankOptions {
            RangeLimit = 5,
            Limit = 11
        };
        var response = await LeaderboardsService.Instance.GetScoresByRankAsync(
            LEADERBOARD_ID,
            Mathf.Max(0, (int)playerScore.Rank - 5),
            rangeOptions
        );
        return ParseEntries(response.Results);
    } catch (System.Exception e) {
        Debug.LogWarning($"[UGS] 범위 조회 실패: {e.Message}");
        return null;
    }
}

// 시간 포맷: 123456ms → "2:03.456"
private string FormatTime(long ms) {
    int minutes = (int)(ms / 60000);
    float seconds = (ms % 60000) / 1000f;
    return $"{minutes}:{seconds:00.000}";
}
```

### 5. 리더보드 UI (런 결과 화면 통합)

```csharp
public class LeaderboardUI : MonoBehaviour {
    [SerializeField] private Transform entryContainer;
    [SerializeField] private GameObject entryPrefab;
    [SerializeField] private TextMeshProUGUI myRankText;
    [SerializeField] private GameObject loadingSpinner;
    [SerializeField] private GameObject offlineMessage;

    public async void ShowLeaderboard() {
        loadingSpinner.SetActive(true);

        var entries = await UGSLeaderboardManager.Instance.GetTopScores(10);

        loadingSpinner.SetActive(false);

        if (entries == null) {
            offlineMessage.SetActive(true);
            return;
        }

        foreach (Transform child in entryContainer) Destroy(child.gameObject);

        for (int i = 0; i < entries.Count; i++) {
            var go = Instantiate(entryPrefab, entryContainer);
            var entry = go.GetComponent<LeaderboardEntryUI>();
            entry.Setup(entries[i].rank, entries[i].playerName, entries[i].clearTimeFormatted);

            // 내 항목 하이라이트
            if (entries[i].isLocalPlayer) entry.Highlight(Color.yellow);
        }
    }
}
```

### 6. 오프라인 처리

```csharp
// 네트워크 없을 때 로컬 폴백
public async System.Threading.Tasks.Task<bool> TrySubmitWithFallback(float clearTime) {
    bool online = Application.internetReachability != NetworkReachability.NotReachable;

    if (online) {
        await SubmitRunScore(clearTime);
        return true;
    } else {
        // 로컬에 임시 저장, 다음 플레이 시 재제출
        var pending = PlayerPrefs.GetString("PendingScore", "");
        PlayerPrefs.SetString("PendingScore", $"{clearTime}|{System.DateTime.Now.Ticks}");
        Debug.Log("[UGS] 오프라인 — 다음 실행 시 제출 예정");
        return false;
    }
}
```

---

## OnionCat 적용 포인트

### 리더보드 종류

| ID | 측정 기준 | 정렬 | 리셋 |
|----|----------|------|------|
| `onioncat_speedrun` | 전체 클리어 시간 (ms) | 낮을수록 1위 | 없음 |
| `onioncat_weekly` | 주간 보스 처치 수 | 높을수록 1위 | 주간 |
| `onioncat_floor` | 도달 최고 층수 | 높을수록 1위 | 없음 |

### 런 결과 화면 통합

```
[ 런 결과 ]
클리어 시간: 12:34.567
세계 순위: 🏆 47위 / 1,234명

[ 글로벌 TOP 10 ]
 1위  SpeedCat_KR    8:21.123
 2위  OnionMaster    9:04.567
...
47위  [나]           12:34.567  ← 내 항목 하이라이트
...
```

### 구현 순서 (초보자 기준)

1. UGS 대시보드에서 프로젝트/리더보드 생성 (15분)
2. Package Manager에서 `Leaderboards` 패키지 설치 (5분)
3. `UGSLeaderboardManager.cs` 기본 초기화 + 익명 로그인 (30분)
4. 런 클리어 시 `SubmitRunScore()` 호출 (15분)
5. 런 결과 화면에 TOP 10 표시 (1~2시간)
6. 오프라인 폴백 처리 (30분)

### 무료 티어 한도

| 항목 | 무료 한도 |
|------|----------|
| MAU (월간 활성 유저) | 1,000명 |
| 리더보드 엔트리 | 무제한 |
| 조회 요청/월 | 100만 건 |
| 제출 요청/월 | 10만 건 |

인디 초기 출시 단계에서는 무료 한도 내에서 충분히 운영 가능.

---

## 참고 링크

- **Unity Gaming Services 공식 문서**: https://docs.unity.com/ugs/manual/leaderboards/manual/overview
- **UGS Leaderboards API 레퍼런스**: https://docs.unity.com/ugs/api/leaderboards
- **UGS 대시보드**: https://cloud.unity.com
- **익명 인증 문서**: https://docs.unity.com/ugs/manual/authentication/manual/anonymous-sign-in
- **Unity 공식 튜토리얼**: YouTube "Unity Gaming Services Leaderboards Tutorial" 검색
- **패키지 설치**: `com.unity.services.leaderboards` (Package Manager에서 검색)
