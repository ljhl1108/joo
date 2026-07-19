# 멀티 엔딩 & 분기 조건 시스템 (Multiple Endings System)

리서치 날짜: 2026-07-19

## 개요

로그라이크에서 멀티 엔딩은 단순한 연출 분기가 아닌 **반복 플레이 동기 부여 핵심 장치**. Hades처럼 10번 도전 끝에 처음 성공해도 "진짜 엔딩은 더 있다"는 것을 알면 플레이어가 계속 돌아옴. Enter the Gungeon의 캐릭터별 과거 청산 결말, Dead Cells의 숨겨진 보스 루트처럼 엔딩은 게임의 마지막 퍼즐이자 메타 진행의 목표가 된다.

OnionCat은 싱글 플레이도 있지만 Co-op 여부, 성공/실패 조건, 특정 보스 처치 방식 등에 따라 자연스럽게 멀티 엔딩을 설계할 수 있는 구조를 가짐.

---

## Unity 구현 방법

### 1. 엔딩 조건 플래그 — RunFlags ScriptableObject

런 도중 발생하는 특수 사건을 담는 플래그 컨테이너:

```csharp
[CreateAssetMenu(fileName = "RunFlags", menuName = "OnionCat/RunFlags")]
public class RunFlags : ScriptableObject
{
    // 런 시작 시 ResetFlags() 호출
    public bool coopMode;            // 2인 Co-op 여부
    public bool noDamageTaken;       // 무피격 클리어
    public bool cropDiedMidRun;      // 작물이 기절한 적 있음
    public bool secretBossDefeated;  // 히든 보스 처치
    public int  totalFloorsCleared;  // 클리어 층 수
    public bool usedDashOnlyBoss;    // 보스를 대시 공격만으로 처치

    public void ResetFlags()
    {
        coopMode = false;
        noDamageTaken = false;
        cropDiedMidRun = false;
        secretBossDefeated = false;
        totalFloorsCleared = 0;
        usedDashOnlyBoss = false;
    }
}
```

### 2. 엔딩 정의 — EndingData ScriptableObject

각 엔딩을 독립 ScriptableObject로 정의:

```csharp
[CreateAssetMenu(fileName = "Ending_Normal", menuName = "OnionCat/EndingData")]
public class EndingData : ScriptableObject
{
    public string endingId;          // "ending_normal", "ending_secret" 등
    public string endingTitle;       // 화면에 표시될 엔딩 이름
    [TextArea] public string description;
    public Sprite endingArtwork;     // 엔딩 일러스트
    public AudioClip bgm;
}
```

### 3. 엔딩 평가 — EndingResolver

조건을 평가해 어떤 엔딩을 재생할지 결정:

```csharp
public class EndingResolver : MonoBehaviour
{
    [SerializeField] private RunFlags runFlags;
    [SerializeField] private EndingData endingNormal;
    [SerializeField] private EndingData endingSecret;
    [SerializeField] private EndingData endingCoop;
    [SerializeField] private EndingData endingTrueEnding;

    public EndingData ResolveEnding()
    {
        // 우선순위 순서로 평가 (위에서 먼저 매칭되면 반환)
        if (runFlags.secretBossDefeated && runFlags.noDamageTaken)
            return endingTrueEnding;

        if (runFlags.secretBossDefeated)
            return endingSecret;

        if (runFlags.coopMode && !runFlags.cropDiedMidRun)
            return endingCoop;

        return endingNormal;
    }
}
```

### 4. 엔딩 재생 — EndingPresenter

```csharp
public class EndingPresenter : MonoBehaviour
{
    [SerializeField] private Image artworkImage;
    [SerializeField] private TextMeshProUGUI titleText;
    [SerializeField] private AudioSource bgmSource;
    [SerializeField] private CanvasGroup canvasGroup;

    public IEnumerator PlayEnding(EndingData ending)
    {
        // 페이드 인
        canvasGroup.alpha = 0f;
        artworkImage.sprite = ending.endingArtwork;
        titleText.text = ending.endingTitle;
        bgmSource.clip = ending.bgm;
        bgmSource.Play();

        yield return StartCoroutine(FadeIn(1.5f));

        // 일정 시간 후 결과 화면으로
        yield return new WaitForSeconds(5f);
        SceneManager.LoadScene("RunResult");
    }

    private IEnumerator FadeIn(float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            canvasGroup.alpha = elapsed / duration;
            elapsed += Time.deltaTime;
            yield return null;
        }
        canvasGroup.alpha = 1f;
    }
}
```

### 5. 최종 보스 처치 시 트리거

```csharp
public class FinalBossController : MonoBehaviour
{
    [SerializeField] private RunFlags runFlags;
    [SerializeField] private EndingResolver endingResolver;
    [SerializeField] private EndingPresenter endingPresenter;

    private void OnBossDefeated()
    {
        runFlags.totalFloorsCleared++;
        EndingData ending = endingResolver.ResolveEnding();
        StartCoroutine(endingPresenter.PlayEnding(ending));
    }
}
```

### 6. 엔딩 잠금 해제 기록 — 영구 저장

```csharp
public static class EndingUnlockSave
{
    private const string KEY = "unlockedEndings";

    public static void UnlockEnding(string endingId)
    {
        HashSet<string> unlocked = LoadUnlocked();
        unlocked.Add(endingId);
        PlayerPrefs.SetString(KEY, string.Join(",", unlocked));
        PlayerPrefs.Save();
    }

    public static bool IsUnlocked(string endingId)
    {
        return LoadUnlocked().Contains(endingId);
    }

    private static HashSet<string> LoadUnlocked()
    {
        string raw = PlayerPrefs.GetString(KEY, "");
        return new HashSet<string>(raw.Split(',', System.StringSplitOptions.RemoveEmptyEntries));
    }
}
```

---

## OnionCat 엔딩 설계 제안

| 엔딩 ID | 조건 | 내용 |
|---------|------|------|
| `ending_normal` | 최종 보스 처치 | 고양이와 작물이 집으로 돌아옴. 일반 결말 |
| `ending_coop` | Co-op + 작물 기절 없이 클리어 | 두 플레이어의 완벽한 협력. 특별 일러스트 |
| `ending_solo_perfect` | 솔로 + 무피격 클리어 | 고양이의 단독 영웅담 (작물은 관망) |
| `ending_secret` | 히든 보스 처치 | 던전의 진짜 비밀 공개. 스토리 확장 |
| `ending_true` | 히든 보스 + 무피격 + Co-op | 진 엔딩: 작물과 고양이의 완전한 결속 |

### Co-op 전용 엔딩의 가치
- P1(고양이)과 P2(작물)가 함께 클리어해야만 볼 수 있는 엔딩 → Co-op 플레이 동기 자동 생성
- "이 엔딩을 보려면 같이 플레이해야 해"는 강력한 소셜 훅

### 구현 순서 (추천)
1. `RunFlags.cs` ScriptableObject 먼저 만들고 런 시작 시 `ResetFlags()` 연결
2. 최종 보스 처치 이벤트에 `EndingResolver.ResolveEnding()` 연결
3. 엔딩 씬을 별도로 만들어 `EndingPresenter`가 씬 내에서 동작하도록 구성
4. 영구 잠금 해제 저장은 `UnlockEnding()` 호출 한 줄로 연결

---

## 주의사항

- **엔딩 조건은 게임 내에서 절대 명시하지 말 것**: 플레이어가 탐험하며 발견하게 두는 것이 핵심 재미. 힌트는 NPC 대사나 배경 오브젝트로만 암시
- **엔딩 분기를 너무 많이 만들지 말 것**: 초기 버전은 2~3개로 시작, 플레이어 피드백 후 확장
- **RunFlags는 씬 전환 후에도 유지**: DontDestroyOnLoad 또는 싱글턴으로 관리, 씬 로드 시 초기화되지 않도록 주의

---

## 참고 링크

- [Game Developer - How to Design Multiple Endings](https://www.gamedeveloper.com/design/how-to-design-multiple-endings)
- [Unity ScriptableObject 공식 문서](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
- [Hades 엔딩 분기 분석 - GDC 2020](https://www.gdcvault.com/play/1027443)
- [Dead Cells - 보스 처치 조건 분기 분석 (팬 위키)](https://deadcells.wiki.gg/wiki/True_Ending)
- [Unity SceneManager 공식 문서](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html)
