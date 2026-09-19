# Unlock Reward Ceremony System (런 종료 후 영구 잠금해제 연출)

리서치 날짜: 2026-09-19

## 개요

로그라이크 게임에서 런이 끝난 뒤 **새 캐릭터, 아이템, 모드가 잠금 해제**될 때
그 순간을 단순 텍스트 팝업이 아닌 **기억에 남는 연출**로 보여주는 시스템.

대표 예:
- **Hades**: 런 종료 후 허브에서 NPC와 대화하며 잠금해제
- **Dead Cells**: 런 결과 화면에서 "새 무기 잠금해제!" 카드 등장
- **Binding of Isaac**: 클리어 후 즉시 전용 애니메이션 컷씬

OnionCat에 필요한 이유: 메타 프로그레션(런 간 영구 성장)이 있다면, 이 연출이 플레이어가 "다음 런을 하고 싶다"는 동기를 만든다.

---

## Unity 구현 방법

### 1. 잠금해제 조건 감지 시스템

```csharp
// UnlockCondition.cs (ScriptableObject)
[CreateAssetMenu(fileName = "UnlockCondition", menuName = "OnionCat/Unlock/Condition")]
public class UnlockCondition : ScriptableObject
{
    public string unlockId;           // 고유 ID
    public string displayName;        // UI 표시명
    public Sprite icon;               // 아이콘
    [TextArea] public string description;
    public UnlockConditionType conditionType;
    public int requiredValue;         // 예: killCount >= 100
}

public enum UnlockConditionType
{
    TotalRuns,          // 누적 런 수
    TotalKills,         // 누적 처치 수
    BossDefeated,       // 특정 보스 처치
    RunCompleted,       // 런 클리어
    DeathCount,         // 사망 횟수 (역설적 잠금해제)
}
```

```csharp
// UnlockManager.cs (싱글턴)
public class UnlockManager : MonoBehaviour
{
    public static UnlockManager Instance { get; private set; }
    
    [SerializeField] private UnlockCondition[] _allUnlocks;
    private HashSet<string> _unlockedIds = new();

    public List<UnlockCondition> CheckNewUnlocks(RunStats runStats)
    {
        var newUnlocks = new List<UnlockCondition>();
        foreach (var condition in _allUnlocks)
        {
            if (_unlockedIds.Contains(condition.unlockId)) continue;
            if (EvaluateCondition(condition, runStats))
            {
                _unlockedIds.Add(condition.unlockId);
                newUnlocks.Add(condition);
            }
        }
        Save();
        return newUnlocks;
    }

    private bool EvaluateCondition(UnlockCondition c, RunStats stats)
    {
        return c.conditionType switch
        {
            UnlockConditionType.TotalRuns    => stats.totalRuns >= c.requiredValue,
            UnlockConditionType.TotalKills   => stats.totalKills >= c.requiredValue,
            UnlockConditionType.BossDefeated => stats.bossesDefeated.Contains(c.unlockId),
            UnlockConditionType.RunCompleted => stats.lastRunCompleted,
            _ => false
        };
    }

    private void Save()
    {
        // PlayerPrefs 또는 JSON 저장
        PlayerPrefs.SetString("UnlockedIds", string.Join(",", _unlockedIds));
    }
}
```

### 2. 런 결과 화면과 연계 (RunResult → Ceremony)

```csharp
// RunResultScreen.cs
public class RunResultScreen : MonoBehaviour
{
    [SerializeField] private UnlockCeremonyUI _ceremonyUI;

    private async void Start()
    {
        // 1. 런 결과 표시
        await ShowRunSummaryAsync();

        // 2. 잠금해제 확인
        var newUnlocks = UnlockManager.Instance.CheckNewUnlocks(GameManager.LastRunStats);

        // 3. 잠금해제 항목이 있으면 연출 시작
        if (newUnlocks.Count > 0)
        {
            await _ceremonyUI.PlayCeremonyAsync(newUnlocks);
        }

        // 4. 계속 버튼 활성화
        ShowContinueButton();
    }
}
```

### 3. 잠금해제 연출 UI

```csharp
// UnlockCeremonyUI.cs
public class UnlockCeremonyUI : MonoBehaviour
{
    [SerializeField] private CanvasGroup _panelGroup;
    [SerializeField] private Image _itemIcon;
    [SerializeField] private TMP_Text _titleText;
    [SerializeField] private TMP_Text _descriptionText;
    [SerializeField] private AudioClip _unlockSFX;
    [SerializeField] private ParticleSystem _celebrationVFX;

    public async Task PlayCeremonyAsync(List<UnlockCondition> unlocks)
    {
        _panelGroup.gameObject.SetActive(true);

        foreach (var unlock in unlocks)
        {
            await ShowSingleUnlockAsync(unlock);
            await Task.Delay(500); // 다음 잠금해제 전 짧은 대기
        }

        // 패널 페이드 아웃
        await FadeOutAsync(_panelGroup, 0.3f);
        _panelGroup.gameObject.SetActive(false);
    }

    private async Task ShowSingleUnlockAsync(UnlockCondition unlock)
    {
        // 초기화
        _panelGroup.alpha = 0f;
        _itemIcon.sprite = unlock.icon;
        _titleText.text = unlock.displayName;
        _descriptionText.text = unlock.description;

        // SFX + VFX
        AudioSource.PlayClipAtPoint(_unlockSFX, Camera.main.transform.position);
        _celebrationVFX.Play();

        // 패널 페이드 인
        await FadeInAsync(_panelGroup, 0.4f);

        // 텍스트 타이핑 효과 (선택)
        await TypewriterEffectAsync(_descriptionText, unlock.description);

        // 플레이어 입력 대기 또는 타이머
        await WaitForInputOrTimeAsync(3f);

        // 페이드 아웃
        await FadeOutAsync(_panelGroup, 0.3f);
    }

    private async Task WaitForInputOrTimeAsync(float timeout)
    {
        float elapsed = 0f;
        while (elapsed < timeout)
        {
            if (Input.anyKeyDown) break;
            elapsed += Time.deltaTime;
            await Task.Yield();
        }
    }

    private async Task FadeInAsync(CanvasGroup group, float duration)
    {
        float t = 0;
        while (t < duration)
        {
            group.alpha = t / duration;
            t += Time.deltaTime;
            await Task.Yield();
        }
        group.alpha = 1f;
    }

    private async Task FadeOutAsync(CanvasGroup group, float duration)
    {
        float t = 0;
        while (t < duration)
        {
            group.alpha = 1f - (t / duration);
            t += Time.deltaTime;
            await Task.Yield();
        }
        group.alpha = 0f;
    }

    private async Task TypewriterEffectAsync(TMP_Text text, string fullText)
    {
        text.text = "";
        foreach (char c in fullText)
        {
            text.text += c;
            await Task.Delay(30);
        }
    }
}
```

### 4. "처음 잠금해제" vs "이미 해제됨" 구분

```csharp
if (isFirstTime)
{
    await ceremonyUI.PlayFullCeremonyAsync(unlock);
}
else
{
    toastUI.Show($"{unlock.displayName} 획득!");
}
```

### 5. 여러 잠금해제 큐 관리

```csharp
private Queue<UnlockCondition> _unlockQueue = new();

public void EnqueueUnlock(UnlockCondition unlock)
{
    _unlockQueue.Enqueue(unlock);
    if (!_isPlayingCeremony) StartCoroutine(ProcessQueueCoroutine());
}

private IEnumerator ProcessQueueCoroutine()
{
    _isPlayingCeremony = true;
    while (_unlockQueue.Count > 0)
    {
        var unlock = _unlockQueue.Dequeue();
        yield return StartCoroutine(ShowUnlockCoroutine(unlock));
        yield return new WaitForSeconds(0.3f);
    }
    _isPlayingCeremony = false;
}
```

### 6. 사운드 설계

- **잠금해제 SFX**: 명확하고 보람있는 소리 (예: 상승 아르페지오 + 메탈릭 반짝임)
- **배경 음악**: 런 결과 BGM → 잠금해제 시 뮤직 스팅(짧은 팡파레)으로 전환
- **타이핑 효과음**: 설명 텍스트 타이핑 시 미세한 클릭음

```csharp
_bgmPlayer.Stop();
_stingPlayer.PlayOneShot(_unlockStingClip);
StartCoroutine(ResumeBGMAfterStingCoroutine());
```

---

## OnionCat 적용 포인트

### 잠금해제 항목 설계

| 잠금해제 ID | 조건 | 보상 |
|------------|------|------|
| `unlock_cat_dash_upgrade` | 첫 런 클리어 | Cat 강화 대시 잠금해제 |
| `unlock_crop_water_shot` | 총 50회 처치 | Crop 물 투사체 업그레이드 |
| `unlock_boss_room` | 보스 첫 처치 | 보스 전용 방 추가 |
| `unlock_hard_mode` | 10런 완료 | 하드 모드 해제 |

### 협동 연출
- 두 플레이어가 함께 하는 게임이므로 잠금해제 연출도 공동 수신
- P1, P2 모두 컨트롤러 진동(Haptic)으로 잠금해제 알림
- 화면에 Cat + Crop 아이콘 동시 표시

### Unity 구현 순서 (초보자용)

1. `UnlockCondition` ScriptableObject 생성 (3~5개부터 시작)
2. `UnlockManager` 싱글턴 구현 + `PlayerPrefs` 저장
3. `RunResultScreen`에서 런 종료 시 `CheckNewUnlocks()` 호출
4. `UnlockCeremonyUI` 패널 제작 (Canvas, Image, Text)
5. 페이드 인/아웃 + SFX 연결
6. 스킵 기능 추가 (아무 키나 누르면 다음으로)
7. 여러 잠금해제 큐 처리

### 주의사항
- `PlayerPrefs`는 PC에서 레지스트리에 저장 → 민감한 데이터는 JSON 암호화 권장
- `UniTask` 사용 시 `async/await` 패턴이 코루틴보다 깔끔
- 잠금해제 연출 중 씬 전환 버튼 클릭을 막을 것 (연출 완료 전 버튼 비활성화)

---

## 참고 링크

- Unity 공식 문서 - PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Unity 공식 문서 - ScriptableObject: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unity 공식 문서 - CanvasGroup: https://docs.unity3d.com/Manual/class-CanvasGroup.html
- YouTube - Game Feel: Unlock Ceremony Design: https://www.youtube.com/results?search_query=unity+unlock+ceremony+roguelike
- Reddit r/gamedev - Best unlock reveal implementations: https://www.reddit.com/r/gamedev/
- UniTask GitHub: https://github.com/Cysharp/UniTask
