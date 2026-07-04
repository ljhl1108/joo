# 인게임 컷씬/연출 시스템 (In-game Cutscene System)

리서치 날짜: 2026-07-04

## 개요

보스 등장, 층 전환, 게임 클리어 등 **특별한 순간에 플레이어 조작을 잠깐 멈추고 극적인 연출을 삽입**하는 시스템. 유니티에서는 레벨에 따라 세 가지 방식으로 구현할 수 있다.

| 방식 | 난이도 | 적합 상황 |
|------|--------|---------|
| 코루틴 기반 SimpleDialogue | ★☆☆ | 2~5초 짧은 보스 등장, 텍스트 연출 |
| Unity Timeline | ★★☆ | 카메라 이동·오브젝트 애니메이션 타이밍 맞춤 컷씬 |
| Cinemachine + Timeline | ★★★ | 영화적 카메라 컷 전환, 복잡한 보스 인트로 |

OnionCat 초기 개발에는 **코루틴 기반 방식**을 먼저 구현하고, 나중에 Timeline으로 업그레이드하는 전략이 현실적이다.

---

## Unity 구현 방법

### 방법 A: 코루틴 기반 (초급, 바로 적용 가능)

```csharp
// CutsceneManager.cs
using System.Collections;
using UnityEngine;
using TMPro;

public class CutsceneManager : MonoBehaviour
{
    public static CutsceneManager Instance { get; private set; }

    [SerializeField] private CanvasGroup blackOverlay;       // 검은 화면 오버레이
    [SerializeField] private TMP_Text titleText;              // "BOSS NAME" 텍스트
    [SerializeField] private CanvasGroup titlePanel;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    // 보스 등장 컷씬 (약 3초)
    public IEnumerator PlayBossIntro(string bossName)
    {
        // 1. 플레이어 입력 잠금
        GameManager.Instance.SetInputEnabled(false);
        Time.timeScale = 1f; // 게임 시간은 유지

        // 2. 검은 화면 페이드 인 (0.3초)
        yield return StartCoroutine(FadeOverlay(0f, 1f, 0.3f));

        // 3. 보스 이름 텍스트 표시
        titleText.text = bossName;
        titlePanel.alpha = 0f;
        titlePanel.gameObject.SetActive(true);
        yield return StartCoroutine(FadeGroup(titlePanel, 0f, 1f, 0.4f));

        // 4. 텍스트 유지 1.5초
        yield return new WaitForSeconds(1.5f);

        // 5. 텍스트 페이드 아웃
        yield return StartCoroutine(FadeGroup(titlePanel, 1f, 0f, 0.4f));
        titlePanel.gameObject.SetActive(false);

        // 6. 검은 화면 페이드 아웃 (0.4초)
        yield return StartCoroutine(FadeOverlay(1f, 0f, 0.4f));

        // 7. 플레이어 입력 해제
        GameManager.Instance.SetInputEnabled(true);
    }

    // 짧은 플래시 연출 (층 전환 후 등장)
    public IEnumerator PlayFlashReveal()
    {
        blackOverlay.alpha = 1f;
        yield return new WaitForSeconds(0.1f);
        yield return StartCoroutine(FadeOverlay(1f, 0f, 0.5f));
    }

    private IEnumerator FadeOverlay(float from, float to, float duration)
    {
        float elapsed = 0f;
        blackOverlay.gameObject.SetActive(true);
        while (elapsed < duration)
        {
            blackOverlay.alpha = Mathf.Lerp(from, to, elapsed / duration);
            elapsed += Time.deltaTime;
            yield return null;
        }
        blackOverlay.alpha = to;
        if (to <= 0f) blackOverlay.gameObject.SetActive(false);
    }

    private IEnumerator FadeGroup(CanvasGroup group, float from, float to, float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            group.alpha = Mathf.Lerp(from, to, elapsed / duration);
            elapsed += Time.deltaTime;
            yield return null;
        }
        group.alpha = to;
    }
}
```

**보스 방에서 트리거**:
```csharp
// BossRoom.cs
void OnPlayerEnter()
{
    StartCoroutine(CutsceneManager.Instance.PlayBossIntro(bossData.displayName));
    // 컷씬 코루틴이 끝나면 자동으로 입력 해제됨
}
```

---

### 방법 B: Unity Timeline (중급, 타이밍 정밀 제어)

Unity Timeline은 **트랙 기반 타임라인 에디터**로 오브젝트 위치, 애니메이션, 사운드, 카메라를 프레임 단위로 제어한다.

```csharp
// TimelineCutscenePlayer.cs
using UnityEngine;
using UnityEngine.Playables;

public class TimelineCutscenePlayer : MonoBehaviour
{
    [SerializeField] private PlayableDirector director;  // Timeline 에셋 연결

    public void PlayCutscene()
    {
        GameManager.Instance.SetInputEnabled(false);
        director.Play();
        director.stopped += OnCutsceneFinished;
    }

    private void OnCutsceneFinished(PlayableDirector d)
    {
        d.stopped -= OnCutsceneFinished;
        GameManager.Instance.SetInputEnabled(true);
    }
}
```

**Timeline 에디터에서 설정**:
1. `Window > Sequencing > Timeline` 열기
2. `PlayableDirector` 컴포넌트가 붙은 오브젝트 선택
3. 트랙 추가: `Animation Track`, `Audio Track`, `Activation Track`, `Cinemachine Track`
4. 각 트랙에 클립 배치 → 드래그로 타이밍 조정

---

### 방법 C: 보스별 연출 ScriptableObject (데이터 주도)

```csharp
// BossIntroData.cs
[CreateAssetMenu(menuName = "OnionCat/BossIntroData")]
public class BossIntroData : ScriptableObject
{
    public string bossName;
    public string subtitle;          // "뿌리의 수호자"
    public AudioClip introSfx;       // 등장 효과음
    public float holdDuration = 1.5f;
    public Color textColor = Color.white;
}
```

이 방식은 보스마다 별도 코드 없이 ScriptableObject 데이터만 교체해 연출을 다르게 만들 수 있다.

---

## OnionCat 적용 포인트

### 컷씬이 필요한 순간 목록

| 상황 | 컷씬 종류 | 소요 시간 |
|------|---------|---------|
| **보스 방 입장** | 검은화면 + 보스 이름 텍스트 | 2~3초 |
| **층 전환** | 페이드 아웃 → 페이드 인 | 1초 |
| **런 클리어** | 엔딩 연출 (Timeline) | 5~10초 |
| **게임 오버** | 슬로우모션 + 검은화면 | 1.5초 |
| **첫 보스 튜토리얼** | 텍스트 팝업 "적의 약점을 찾아라!" | 3초 |

### 구현 우선순위 (초보 개발자용)

1. **먼저**: `CutsceneManager` 코루틴 버전으로 페이드 인/아웃만 구현
2. **다음**: 보스 이름 텍스트 연출 추가 (TMPro 활용)
3. **나중에**: Unity Timeline으로 보스 인트로 업그레이드
4. **선택**: Cinemachine Virtual Camera로 드라마틱한 카메라 컷

### 주의 사항

- **`Time.timeScale = 0f` 금지**: 컷씬 중 시간을 멈추면 코루틴도 멈춤. `WaitForSecondsRealtime` 사용하거나 `Time.timeScale`은 게임 일시정지 전용으로 분리
- **입력 잠금 필수**: 컷씬 중 플레이어가 조작 가능하면 버그 다수 발생
- **Canvas Sort Order 관리**: 검은 오버레이 캔버스는 모든 UI보다 위에 있어야 함 (Sort Order: 999)
- **[SerializeField] 항목**: `blackOverlay`, `titleText`, `titlePanel` 은 유니티 에디터에서 드래그 앤 드롭 설정 필요

---

## 참고 링크

- Unity Timeline 공식 문서: https://docs.unity3d.com/Packages/com.unity.timeline@1.8/manual/index.html
- Cinemachine + Timeline: https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineTimeline.html
- 코루틴 기반 페이드 튜토리얼: https://www.youtube.com/watch?v=Oa7_Bsgt0w4 (검색: Unity fade screen coroutine)
- PlayableDirector API: https://docs.unity3d.com/ScriptReference/Playables.PlayableDirector.html
- CanvasGroup alpha: https://docs.unity3d.com/ScriptReference/CanvasGroup.html
