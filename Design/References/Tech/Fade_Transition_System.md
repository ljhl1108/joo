# 페이드 인/아웃 씬 전환 시스템 (Fade Transition)

리서치 날짜: 2026-09-02

## 개요

씬 전환 시 화면이 검은색으로 서서히 어두워졌다가(페이드 아웃) 다음 씬에서 서서히 밝아지는(페이드 인) 효과.
가장 기본적이면서도 플레이어가 갑작스러운 씬 전환에 불쾌감을 느끼지 않게 해주는 필수 게임 완성 요소.

OnionCat에서는:
- 메인 메뉴 → 게임 씬 전환
- 방 이동 시 (선택적)
- 게임 오버 → 결과 화면
- 보스 입장 연출

---

## Unity 구현 방법

### 방법 1: UI Image + CanvasGroup 코루틴 (초보자 추천)

#### 필요 준비물
1. Canvas (Screen Space - Overlay, Sort Order 99로 최상위)
2. Canvas 하위에 Image (전체 화면 크기, 검은색, `FadePanel` 이름)
3. Image에 CanvasGroup 컴포넌트 추가

#### 스크립트

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class FadeTransitionManager : MonoBehaviour
{
    public static FadeTransitionManager Instance { get; private set; }

    [SerializeField] private CanvasGroup fadePanel;
    [SerializeField] private float fadeDuration = 0.5f;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    // 씬 전환 + 페이드
    public void LoadScene(string sceneName)
    {
        StartCoroutine(FadeAndLoad(sceneName));
    }

    public void LoadScene(int sceneIndex)
    {
        StartCoroutine(FadeAndLoad(sceneIndex));
    }

    private IEnumerator FadeAndLoad(object sceneTarget)
    {
        yield return FadeOut();

        if (sceneTarget is string name)
            yield return SceneManager.LoadSceneAsync(name);
        else if (sceneTarget is int index)
            yield return SceneManager.LoadSceneAsync(index);

        yield return FadeIn();
    }

    // 페이드 아웃 (투명 → 불투명)
    public IEnumerator FadeOut()
    {
        fadePanel.blocksRaycasts = true; // 입력 차단
        float elapsed = 0f;
        while (elapsed < fadeDuration)
        {
            fadePanel.alpha = Mathf.Clamp01(elapsed / fadeDuration);
            elapsed += Time.unscaledDeltaTime; // 일시정지 중에도 동작
            yield return null;
        }
        fadePanel.alpha = 1f;
    }

    // 페이드 인 (불투명 → 투명)
    public IEnumerator FadeIn()
    {
        float elapsed = 0f;
        while (elapsed < fadeDuration)
        {
            fadePanel.alpha = 1f - Mathf.Clamp01(elapsed / fadeDuration);
            elapsed += Time.unscaledDeltaTime;
            yield return null;
        }
        fadePanel.alpha = 0f;
        fadePanel.blocksRaycasts = false; // 입력 재개
    }
}
```

#### 사용법

```csharp
// 다른 스크립트에서 씬 전환 호출
FadeTransitionManager.Instance.LoadScene("GameScene");
FadeTransitionManager.Instance.LoadScene(1);

// 씬 전환 없이 페이드만 (연출용)
StartCoroutine(FadeTransitionManager.Instance.FadeOut());
// ... 어떤 작업 ...
StartCoroutine(FadeTransitionManager.Instance.FadeIn());
```

---

### 방법 2: Animator (더 세밀한 제어 필요 시)

Canvas 하위 Image에 Animator 컴포넌트 추가:

```
Animator States:
  - Idle (alpha=0, 기본 상태)
  - FadeOut (0→1 애니메이션, 0.5초)
  - FadeIn (1→0 애니메이션, 0.5초)

Transitions:
  Idle → FadeOut: trigger "FadeOut"
  FadeOut → FadeIn: trigger "FadeIn" (또는 자동)
  FadeIn → Idle: ExitTime
```

```csharp
animator.SetTrigger("FadeOut");
yield return new WaitForSeconds(0.5f);
SceneManager.LoadScene(sceneName);
animator.SetTrigger("FadeIn");
```

---

### 방법 3: DOTween 사용 (DOTween 패키지 설치 필요)

```csharp
using DG.Tweening;

public IEnumerator FadeOut()
{
    yield return fadePanel.DOFade(1f, fadeDuration)
        .SetUpdate(true) // 일시정지 중에도 동작
        .WaitForCompletion();
}

public IEnumerator FadeIn()
{
    yield return fadePanel.DOFade(0f, fadeDuration)
        .SetUpdate(true)
        .WaitForCompletion();
}
```

---

## 씬 시작 시 자동 페이드 인

씬 전환 후 새 씬에서 자동으로 페이드 인:

```csharp
// FadeTransitionManager.cs에 추가
void OnEnable()
{
    SceneManager.sceneLoaded += OnSceneLoaded;
}

void OnDisable()
{
    SceneManager.sceneLoaded -= OnSceneLoaded;
}

void OnSceneLoaded(Scene scene, LoadSceneMode mode)
{
    StartCoroutine(FadeIn());
}
```

---

## 색상 변형 (검은색 외)

```csharp
[SerializeField] private Image fadePanelImage;

// 보스 입장: 붉은 페이드
fadePanelImage.color = new Color(0.5f, 0f, 0f, 1f);

// 특수 연출: 흰색 플래시
fadePanelImage.color = Color.white;
```

---

## OnionCat 적용 포인트

### 1. 계층 구조 (DontDestroyOnLoad 싱글톤)

```
[DontDestroyOnLoad]
└── FadeTransitionManager (GameObject)
    └── Canvas (Overlay, SortOrder 999)
        └── FadePanel (Image, CanvasGroup)
```

씬마다 새로 만들 필요 없이 한 번만 구성, 모든 씬에서 공유.

### 2. OnionCat 씬 전환 시나리오

```csharp
// 메인 메뉴 → 게임 시작
FadeTransitionManager.Instance.LoadScene("GameScene");

// 게임 오버 → 결과 화면
FadeTransitionManager.Instance.LoadScene("GameOverScene");

// 보스 방 입장 (보스 입장 연출 후 페이드)
StartCoroutine(BossEntranceRoutine());

IEnumerator BossEntranceRoutine()
{
    // 카메라 흔들림, 보스 등장 연출...
    yield return new WaitForSeconds(2f);
    yield return FadeTransitionManager.Instance.FadeOut();
    // 보스 배경 BGM 전환 등
    yield return FadeTransitionManager.Instance.FadeIn();
}
```

### 3. 2인 협력 고려사항
OnionCat은 두 플레이어가 동시에 씬 전환을 경험:
- 페이드 아웃 시작 = 두 플레이어 입력 동시 차단 (`blocksRaycasts = true`)
- 페이드 인 완료 = 두 플레이어 입력 동시 재개
- 별도 "준비 완료" 로직 불필요 (단순 공유 페이드)

### 4. 페이드 속도 권장값

| 상황 | fadeDuration |
|------|--------------|
| 일반 씬 전환 | 0.4~0.6초 |
| 게임 오버 (느리게) | 1.0~1.5초 |
| 보스 입장 (빠르게) | 0.2~0.3초 |
| 런 시작 | 0.5초 |

---

## Inspector 설정 필요 항목

유니티 에디터에서 드래그 앤 드롭 설정 필요:
- `FadeTransitionManager` 컴포넌트의 `fadePanel` 필드 → Canvas 하위 FadePanel 오브젝트(CanvasGroup)

FadePanel 오브젝트 설정:
- Rect Transform: 앵커 = Stretch/Stretch, Left/Right/Top/Bottom = 0
- Image 색상: R=0, G=0, B=0, A=255 (완전 불투명 검은색)
- CanvasGroup: Alpha = 0 (시작 시 투명), Block Raycasts = false

---

## 참고 링크

- Unity Docs - SceneManager: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- Unity Docs - CanvasGroup: https://docs.unity3d.com/ScriptReference/CanvasGroup.html
- Brackeys - Scene Management: https://youtu.be/O7OtS_RpAPs
- DOTween 공식: http://dotween.demigiant.com/documentation.php
