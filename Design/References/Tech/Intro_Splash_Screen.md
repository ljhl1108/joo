# 인트로 / 스플래시 화면 시스템

리서치 날짜: 2026-06-24

## 개요

게임 시작 시 가장 먼저 보이는 화면. 개발사 로고, 엔진 로고, 퍼블리셔 로고 순서로 표시 후 메인 메뉴로 이동하는 시퀀스다. OnionCat에 필요한 이유:

- 게임의 첫인상을 좌우하는 **브랜딩 기회**
- 메인 메뉴가 뜨기 전 배경 로딩 시간 활용 (비동기 로딩 병행)
- 완성도 높아 보이는 효과 (초보 개발자에게 특히 중요)
- Unity 기본 스플래시 화면 대체 가능

---

## Unity 구현 방법

### 1. Unity 빌트인 스플래시 화면 설정

`Edit → Project Settings → Player → Splash Image`
- **Splash Screen** 섹션에서 기본 Unity 로고 비활성화 가능 (Pro 라이선스 필요)
- 커스텀 로고 추가: Logos 리스트에 Sprite 드래그
- Personal 라이선스: "Made with Unity" 로고 강제 표시, 그 뒤에 커스텀 추가 가능

### 2. 커스텀 스플래시 씬 구조

```
Scenes/
  ├── SplashScene    ← 첫 번째 씬 (Build Index 0)
  ├── MainMenu       ← Build Index 1
  └── GameScene      ← Build Index 2
```

**SplashScene 오브젝트 구성:**
```
SplashCanvas (Canvas - Screen Space Overlay)
  └── LogoImage (Image) ← 로고 표시
SplashManager (SplashManager.cs)
AsyncLoader (백그라운드에서 MainMenu 로드)
```

### 3. SplashManager 구현

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class SplashManager : MonoBehaviour
{
    [SerializeField] private Image logoImage;
    [SerializeField] private SplashEntry[] splashEntries;
    [SerializeField] private string nextSceneName = "MainMenu";

    [System.Serializable]
    public struct SplashEntry
    {
        public Sprite Logo;
        public float DisplayDuration; // 로고 표시 시간
        public float FadeDuration;    // 페이드 인/아웃 시간
    }

    private AsyncOperation _preloadOp;
    private bool _skipRequested;

    private void Start()
    {
        // 다음 씬 백그라운드 미리 로드
        _preloadOp = SceneManager.LoadSceneAsync(nextSceneName);
        _preloadOp.allowSceneActivation = false;

        StartCoroutine(PlaySplashSequence());
    }

    private void Update()
    {
        // 아무 키나 누르면 스킵
        if (Input.anyKeyDown)
            _skipRequested = true;
    }

    private IEnumerator PlaySplashSequence()
    {
        foreach (var entry in splashEntries)
        {
            if (_skipRequested) break;

            logoImage.sprite = entry.Logo;
            logoImage.color = Color.clear;

            // 페이드 인
            yield return FadeLogo(0f, 1f, entry.FadeDuration);

            // 표시 유지
            float elapsed = 0f;
            while (elapsed < entry.DisplayDuration && !_skipRequested)
            {
                elapsed += Time.deltaTime;
                yield return null;
            }

            // 페이드 아웃
            yield return FadeLogo(1f, 0f, entry.FadeDuration);
        }

        // 씬 전환 허용
        _preloadOp.allowSceneActivation = true;
    }

    private IEnumerator FadeLogo(float from, float to, float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = Mathf.Clamp01(elapsed / duration);
            logoImage.color = new Color(1f, 1f, 1f, Mathf.Lerp(from, to, t));
            yield return null;
        }
        logoImage.color = new Color(1f, 1f, 1f, to);
    }
}
```

### 4. 비디오 스플래시 (선택적)

```csharp
using UnityEngine;
using UnityEngine.Video;

public class VideoSplash : MonoBehaviour
{
    [SerializeField] private VideoPlayer videoPlayer;
    [SerializeField] private string nextScene = "MainMenu";

    private void Start()
    {
        videoPlayer.loopPointReached += OnVideoEnd;
        videoPlayer.Play();
    }

    private void OnVideoEnd(VideoPlayer vp)
    {
        UnityEngine.SceneManagement.SceneManager.LoadScene(nextScene);
    }

    private void Update()
    {
        if (Input.anyKeyDown)
            UnityEngine.SceneManagement.SceneManager.LoadScene(nextScene);
    }
}
```

### 5. Build Settings에서 씬 순서 설정

`File → Build Settings → Scenes In Build`:
```
0: Scenes/SplashScene    ← 반드시 0번
1: Scenes/MainMenu
2: Scenes/GameScene
```

### 6. 전문 팁: 스플래시 중 실제 로딩 처리

```csharp
// 스플래시 표시 중 게임 에셋 미리 로드
private IEnumerator LoadAssetsWhileSplashing()
{
    // Addressables 또는 Resources 방식
    var handle = Resources.LoadAsync<GameObject>("GameManager");
    yield return handle;
    // 스플래시 끝날 때까지 대기는 PlaySplashSequence가 처리
}
```

---

## OnionCat 적용 포인트

### 권장 스플래시 시퀀스 (3단계)
```
1. [개발자 로고] "Made by [이름]" — 1.5초 페이드인/아웃
2. [OnionCat 타이틀 로고] — 2초 표시, 짧은 음악 재생
3. 메인 메뉴로 전환
```

### 최소 구현 (빠른 완성 우선)
1. `SplashScene` 씬 생성
2. 검정 배경 + 단일 이미지(OnionCat 로고 PNG) + 페이드 코루틴
3. 2초 후 MainMenu 씬 로드
4. Build Settings에서 SplashScene을 0번으로 설정

### 스킵 처리 중요성
- 반복 플레이어는 스플래시를 건너뛰고 싶어함
- `Input.anyKeyDown` 또는 `Mouse.current.leftButton.wasPressedThisFrame`으로 스킵 구현

### 로고 소재 없을 때 대안
- 텍스트만으로 구성: `TextMeshPro`로 게임 타이틀 타이핑 효과
- 간단한 픽셀 아트 로고 → Aseprite로 2시간 내 제작 가능

### [SerializeField] 설정 필요 항목
- `logoImage`: SplashCanvas 하위 Image 컴포넌트 드래그
- `splashEntries`: 인스펙터에서 원소 추가 후 각 Sprite 드래그
- `nextSceneName`: "MainMenu" 텍스트 입력 (Build Settings 씬 이름과 일치해야)

---

## 참고 링크

- [Unity 공식 스플래시 화면 설정](https://docs.unity3d.com/Manual/class-PlayerSettingsSplashScreen.html)
- [Unity VideoPlayer 컴포넌트](https://docs.unity3d.com/ScriptReference/Video.VideoPlayer.html)
- [AsyncOperation.allowSceneActivation](https://docs.unity3d.com/ScriptReference/AsyncOperation-allowSceneActivation.html)
- [Unity Learn: Scene Management](https://learn.unity.com/tutorial/scene-management)
- [YouTube: Unity Splash Screen Tutorial](https://www.youtube.com/results?search_query=unity+custom+splash+screen+tutorial)
