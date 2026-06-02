# 메인 메뉴 씬 (Main Menu Scene)

## 개요

메인 메뉴는 플레이어가 게임을 처음 경험하는 화면이다.
OnionCat에서는 타이틀 로고, 시작 버튼, 종료 버튼, 선택적으로 설정 버튼을 포함한다.
씬 전환(SceneManager), UI Canvas, 페이드 인/아웃이 핵심 구현 요소다.

---

## Unity 구현 방법

### 1. 씬 구성

```
MainMenu (Scene)
├── Canvas (Screen Space - Overlay)
│   ├── BackgroundImage      ← 타이틀 배경 픽셀아트
│   ├── LogoImage            ← "OnionCat" 로고
│   ├── ButtonPlay           ← 시작 버튼
│   ├── ButtonSettings       ← 설정 버튼 (옵션)
│   └── ButtonQuit           ← 종료 버튼
└── FadePanel (Image, black, alpha 0)   ← 페이드용 전체 덮개
```

### 2. Build Settings 등록

`File → Build Settings → Add Open Scenes`

| Index | Scene |
|-------|-------|
| 0 | MainMenu |
| 1 | GameScene |
| 2 | GameOver |

### 3. MainMenuManager.cs

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;

public class MainMenuManager : MonoBehaviour
{
    [SerializeField] private CanvasGroup fadeGroup;
    [SerializeField] private float       fadeDuration = 0.5f;

    private void Start()
    {
        // 시작 시 페이드 인
        StartCoroutine(FadeIn());
    }

    // ── 버튼 연결 메서드 ──────────────────────────

    public void OnPlayButton()
    {
        StartCoroutine(FadeAndLoad(1)); // GameScene (index 1)
    }

    public void OnQuitButton()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }

    // ── 페이드 코루틴 ──────────────────────────────

    private IEnumerator FadeIn()
    {
        fadeGroup.alpha = 1f;
        float t = 0;
        while (t < fadeDuration)
        {
            t += Time.deltaTime;
            fadeGroup.alpha = 1f - (t / fadeDuration);
            yield return null;
        }
        fadeGroup.alpha = 0f;
    }

    private IEnumerator FadeAndLoad(int sceneIndex)
    {
        // 버튼 중복 클릭 방지
        fadeGroup.interactable   = false;
        fadeGroup.blocksRaycasts = true;

        float t = 0;
        while (t < fadeDuration)
        {
            t += Time.deltaTime;
            fadeGroup.alpha = t / fadeDuration;
            yield return null;
        }
        fadeGroup.alpha = 1f;

        SceneManager.LoadScene(sceneIndex);
    }
}
```

### 4. Inspector 연결 순서

1. `MainMenuManager` 스크립트를 빈 GameObject(이름: `MenuManager`)에 추가
2. `FadeGroup` 필드 → `FadePanel`의 `CanvasGroup` 컴포넌트를 드래그 앤 드롭
3. ButtonPlay → `OnClick()` + → `MenuManager` 드래그 → `OnPlayButton` 선택
4. ButtonQuit → `OnClick()` + → `MenuManager` 드래그 → `OnQuitButton` 선택

> **유니티 에디터에서 드래그 앤 드롭 설정 필요**:
> - `MenuManager` 오브젝트의 `FadeGroup` 필드에 FadePanel의 CanvasGroup을 연결
> - 각 버튼의 OnClick 이벤트에 위 메서드 연결

### 5. 선택: 배경 애니메이션 (간단 버전)

```csharp
// 로고 흔들림 효과 — 고급 없이 간단하게
[SerializeField] private RectTransform logo;
private float baseY;

private void Start()
{
    baseY = logo.anchoredPosition.y;
}

private void Update()
{
    float y = baseY + Mathf.Sin(Time.time * 1.5f) * 6f;
    logo.anchoredPosition = new Vector2(logo.anchoredPosition.x, y);
}
```

### 6. 씬 전환 — 게임 오버에서 메인 메뉴 복귀

```csharp
// GameOverManager.cs
public void OnMainMenuButton()
{
    SceneManager.LoadScene(0); // MainMenu (index 0)
}
```

---

## OnionCat 적용 포인트

### 구현 우선순위 (초보 개발자 권장 순서)
1. MainMenu 씬 생성 → Build Settings 등록
2. Canvas + 버튼 UI 배치 (픽셀아트 폰트 적용)
3. `MainMenuManager.cs` 작성 → 버튼 연결
4. FadePanel(`CanvasGroup`) 추가 → 페이드 코루틴 연결
5. 로고 흔들림 등 폴리시 추가

### 주의사항
- `SceneManager.LoadScene()` 사용 전 **반드시 Build Settings에 씬 등록** → 등록 안 하면 런타임 에러
- `Application.Quit()`은 **에디터에선 동작 안 함** → `#if UNITY_EDITOR` 분기 필수
- `CanvasGroup.blocksRaycasts = true` 설정으로 페이드 중 버튼 중복 클릭 방지
- **2인 협력 시작 화면**: 씬 로드 전 P1(키보드/패드), P2(마우스) 입력 장치 확인 로직 추가 권장

### OnionCat 메인 메뉴 구성안
```
[OnionCat 타이틀 로고]
    고양이 + 양파 픽셀아트 애니메이션

[시작하기]   [설정]   [종료]

"P1: WASD + Space  |  P2: Mouse + RMB"  ← 컨트롤 안내
```

---

## 참고 링크

- Unity Learn — Scene Flow: https://learn.unity.com/pathway/junior-programmer/unit/manage-scene-flow-and-data/tutorial/create-a-scene-flow
- GameDev Academy — Start Menu Tutorial: https://gamedevacademy.org/unity-start-menu-tutorial/
- Unity Docs — SceneManager: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- Unity Docs — CanvasGroup: https://docs.unity3d.com/Manual/class-CanvasGroup.html
