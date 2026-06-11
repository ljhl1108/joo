# 크레딧 화면 (Credits Screen)

리서치 날짜: 2026-06-11

## 개요
게임 완성의 마지막 터치. 엔딩 클리어 후 또는 메인 메뉴에서 접근하는 제작진 소개 화면.
스크롤 크레딧은 게임의 성의와 완성도를 보여주는 상징적 요소 — 단 30분 투자로 구현 가능.

---

## Unity 구현 방법

### 방법 1: RectTransform 애니메이션 (권장 — 초보자 친화적)

**씬 구조:**
```
Credits (Scene)
└── Canvas (Screen Space - Overlay)
    ├── Background (Image, fullscreen, 검정 또는 그라디언트)
    ├── CreditsContainer (Empty GameObject)
    │   └── CreditsText (TextMeshProUGUI, Auto Size ON)
    └── SkipHint (Text: "ESC - 건너뛰기")
```

**설정 단계:**
1. `File > New Scene` → "Credits" 씬 생성, Build Settings에 추가
2. Canvas 생성 → Render Mode: Screen Space - Overlay
3. 검정 Background Image (fullscreen) 추가
4. `CreditsContainer` Empty GameObject 생성
5. 자식으로 TextMeshProUGUI 추가 → 크레딧 텍스트 입력
6. `Window > Animation > Animation` 열기
7. `CreditsContainer` 선택 → Animation 창에서 `Create` → `CreditsScroll.anim` 저장
8. 키프레임 설정:
   - `0:00` → `CreditsContainer.RectTransform.anchoredPosition.y = -700` (화면 아래)
   - `0:20` → `CreditsContainer.RectTransform.anchoredPosition.y = +1500` (화면 위)
9. 루프 끄기: Animation 클립 선택 → Inspector에서 `Loop Time` 체크 해제

**C# 스크립트 (CreditsManager.cs):**
```csharp
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.InputSystem;

public class CreditsManager : MonoBehaviour
{
    [SerializeField] private float creditsDuration = 20f;
    [SerializeField] private string mainMenuScene = "MainMenu";
    private float _timer;

    void Update()
    {
        _timer += Time.deltaTime;

        // New Input System 방식 ESC 스킵
        if (_timer >= creditsDuration ||
            Keyboard.current.escapeKey.wasPressedThisFrame)
        {
            ReturnToMenu();
        }
    }

    public void ReturnToMenu()
    {
        SceneManager.LoadScene(mainMenuScene);
    }
}
```

---

### 방법 2: C# 스크립트 직접 스크롤 (코드 중심)

애니메이션 없이 순수 코드로 스크롤 속도 조절 가능. 런타임 속도 변경 유리.

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.InputSystem;

public class CreditsScroller : MonoBehaviour
{
    [SerializeField] private RectTransform creditsContent;
    [SerializeField] private float scrollSpeed = 60f;       // px/sec
    [SerializeField] private string mainMenuScene = "MainMenu";

    void Update()
    {
        creditsContent.anchoredPosition += Vector2.up * scrollSpeed * Time.deltaTime;

        if (Keyboard.current.escapeKey.wasPressedThisFrame)
            SceneManager.LoadScene(mainMenuScene);

        // 텍스트가 모두 올라갔을 때 자동 복귀
        if (creditsContent.anchoredPosition.y > creditsContent.rect.height + 200f)
            SceneManager.LoadScene(mainMenuScene);
    }
}
```

---

### 방법 3: Unity Timeline (고급 — 영상 연출 수준)

`Window > Sequencing > Timeline` 활용.
텍스트 오브젝트별 등장/퇴장 타이밍, 배경음악 동기화까지 세밀하게 제어 가능.
구현 난이도 높음 — 엔딩 연출에 시간 투자할 수 있을 때 사용.

---

### 크레딧 텍스트 구성 예시 (TextMeshPro Rich Text 활용)

```
<size=36><b>OnionCat</b></size>
<size=24>고양이와 작물의 여정</size>


<size=28><b>개발</b></size>
<size=22>ljhl1108</size>


<size=28><b>사용 에셋</b></size>
<size=20>Unity URP 2D
New Input System
TextMeshPro</size>


<size=28><b>참고 게임</b></size>
<size=20>Hades, Enter the Gungeon
Binding of Isaac, Tiny Rogues</size>


<size=28><b>감사합니다</b></size>
```

---

### 씬 전환 연결

```csharp
// 메인 메뉴 버튼에서:
public void OpenCredits()
{
    SceneManager.LoadScene("Credits");
}

// 페이드 효과 활용 시 (SceneTransitionManager가 있다면):
SceneTransitionManager.Instance.LoadScene("Credits");
```

**Build Settings 필수 확인**: `File > Build Settings`에 Credits 씬 추가.

---

## OnionCat 적용 포인트

1. **두 가지 진입 경로**:
   - 메인 메뉴 "크레딧" 버튼
   - 보스 클리어(엔딩) 후 자동 전환 → 엔딩 BGM과 함께 자연스럽게 이어지기

2. **New Input System 사용**: ESC 스킵은 `Keyboard.current.escapeKey.wasPressedThisFrame` 사용 (Legacy `Input.GetKeyDown` 금지)

3. **내용 구성 항목**: 개발자(본인 닉네임), 사용 Unity 패키지/에셋, 참고 게임 목록, 제작 기간

4. **배경음악 연동**: 크레딧 씬 시작 시 엔딩 BGM 페이드인 → 감정적 마무리 효과

5. **구현 우선순위**: 방법 1(애니메이션)이 코딩 최소화로 30분 내 완성 가능 → 다른 기능 완성 후 마지막에 작업 권장

---

## 참고 링크
- [Unity 크레딧 씬 튜토리얼 (Jimmy Vegas, YouTube)](https://www.youtube.com/watch?v=cj6hwCjiVZE)
- [Brian Severa: Creating Scrolling Credits in Unity](https://medium.com/@briansevera/creating-a-scrolling-credits-screen-in-unity-6009d1a8669b)
- [Timeline 활용 크레딧 씬 (Geek Culture)](https://medium.com/geekculture/make-a-credits-scene-using-timeline-in-unity-598fd2a4349b)
- [Unity SceneManager 공식 문서](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html)
- [Unity ScrollRect 공식 문서](https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-ScrollRect.html)
