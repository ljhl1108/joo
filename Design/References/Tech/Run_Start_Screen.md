# 런 시작 화면 (Run Start Screen)

리서치 날짜: 2026-08-10

## 개요

"New Run" 버튼을 눌렀을 때 첫 번째 방에 진입하기 직전까지의 전환 화면. 단순한 씬 전환이 아니라 **플레이어가 이번 런을 시작하는 의식(ritual)** 을 경험하게 하는 UI/연출 시퀀스다.

OnionCat에서는 두 플레이어가 조이스틱과 마우스를 각각 잡는 순간, "우리가 지금 뭘 하는 게임인지"를 다시 상기시켜 주는 역할이 핵심이다.

### 왜 중요한가

- 메인 메뉴 → 첫 방이 즉시 로드되면 플레이어가 심리적 준비 없이 전투에 투입됨
- 런마다 반복되는 "의식"이 로그라이크의 긴장감을 만드는 핵심 감정 아크
- 협동 게임에서는 두 플레이어가 서로 준비됐는지 확인하는 "Ready Check" 기회

---

## Unity 구현 방법

### 씬 구성 옵션

**옵션 A: 오버레이 UI 패널 (권장 — 씬 전환 없음)**

메인 메뉴 씬 위에 Canvas를 얹어 Run Start Screen을 표시하고, 확인 후 게임플레이 씬을 비동기 로드:

```
[MainMenu Scene]
  └── Canvas (RunStartOverlay, alpha=0)
       ├── BackgroundDim (Image, black semi-transparent)
       ├── CharacterPanel (Cat + Crop 스프라이트)
       ├── FlavorText ("제 1대 양파고양이의 모험이 시작됩니다...")
       ├── RunModifierPanel (난이도, 커스텀 설정 등)
       └── BeginRunButton
```

**옵션 B: 별도 씬 (독립성 높음)**

`RunStart.unity` 씬을 분리해 LoadSceneAsync로 전환 후, 완료 시 다음 씬 활성화.

---

### 구현 코드

```csharp
// RunStartScreenManager.cs
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class RunStartScreenManager : MonoBehaviour
{
    [SerializeField] CanvasGroup _panelGroup;
    [SerializeField] string _gameplaySceneName = "Gameplay";
    [SerializeField] float _fadeDuration = 0.4f;

    AsyncOperation _loadOp;

    void Start()
    {
        // 배경에서 게임플레이 씬 미리 로드 (allowSceneActivation = false)
        _loadOp = SceneManager.LoadSceneAsync(_gameplaySceneName);
        _loadOp.allowSceneActivation = false;

        StartCoroutine(FadeIn());
    }

    IEnumerator FadeIn()
    {
        _panelGroup.alpha = 0f;
        float t = 0f;
        while (t < _fadeDuration) {
            t += Time.deltaTime;
            _panelGroup.alpha = t / _fadeDuration;
            yield return null;
        }
        _panelGroup.alpha = 1f;
    }

    public void OnBeginRunPressed()
    {
        StartCoroutine(StartRun());
    }

    IEnumerator StartRun()
    {
        // 페이드 아웃
        float t = _fadeDuration;
        while (t > 0) {
            t -= Time.deltaTime;
            _panelGroup.alpha = t / _fadeDuration;
            yield return null;
        }

        // 미리 로드된 씬 활성화
        _loadOp.allowSceneActivation = true;
    }
}
```

---

### 협동 Ready Check (두 플레이어 동시 확인)

OnionCat은 2인 협동이므로 양쪽 플레이어가 준비됐는지 확인:

```csharp
// CoopReadyCheck.cs
public class CoopReadyCheck : MonoBehaviour
{
    bool _p1Ready, _p2Ready;
    [SerializeField] GameObject _p1ReadyIcon;
    [SerializeField] GameObject _p2ReadyIcon;
    [SerializeField] Button _beginButton;

    // Input System 콜백으로 연결
    public void OnP1Ready() { _p1Ready = true; _p1ReadyIcon.SetActive(true); CheckBothReady(); }
    public void OnP2Ready() { _p2Ready = true; _p2ReadyIcon.SetActive(true); CheckBothReady(); }

    void CheckBothReady()
    {
        _beginButton.interactable = _p1Ready && _p2Ready;
    }
}
```

---

### 플레이버 텍스트 랜덤 선택

런마다 다른 짧은 문구로 분위기 조성:

```csharp
// RunFlavorText.cs
public class RunFlavorText : MonoBehaviour
{
    [SerializeField] Text _textLabel;

    static readonly string[] Flavors = {
        "양파와 고양이의 모험이 시작됩니다.",
        "오늘도 함께라면 두렵지 않다.",
        "조심해, 저 밖엔 우리보다 강한 것들이 있어.",
        "실패해도 괜찮아. 다시 시작하면 되니까.",
        "고양이는 발소리를 죽이고, 양파는 시야를 넓힌다."
    };

    void Start()
    {
        _textLabel.text = Flavors[Random.Range(0, Flavors.Length)];
    }
}
```

---

### 연출 시퀀스 (DOTween 사용)

```csharp
// 캐릭터 등장 연출 (DOTween)
void PlayCharacterIntro()
{
    catSprite.transform.localPosition = new Vector3(-300f, 0, 0);
    cropSprite.transform.localPosition = new Vector3(300f, 0, 0);

    catSprite.transform.DOLocalMoveX(-80f, 0.5f).SetEase(Ease.OutBack);
    cropSprite.transform.DOLocalMoveX(80f, 0.5f).SetEase(Ease.OutBack).SetDelay(0.1f);
}
```

---

## OnionCat 적용 포인트

### 최소 구현 (MVP)

1. 검정 페이드 인 → Cat+Crop 스프라이트 표시 → "시작" 버튼 → 페이드 아웃 → 게임플레이 씬 활성화
2. 백그라운드에서 `LoadSceneAsync`로 씬을 미리 로드해 대기 시간 숨기기
3. 플레이버 텍스트 5~10개로 런마다 변화 느낌

### 심화 구현

- P1(Cat) + P2(Crop) 각각 "준비 완료" 입력 → 양쪽 아이콘 체크 후 자동 시작
- 런 번호 표시: "제 N대 양파고양이" (SaveData에서 런 카운트 읽어옴)
- 최고 기록 힌트: "이전 최고 기록: 3층 27처치" — 이번 런 동기부여 부여
- 첫 번째 런에만 "조작 방법 보기" 버튼 표시 (Tutorial_System과 연동)

### 구현 순서

1. `RunStartOverlay` Canvas 오브젝트 생성 (Main Menu 씬에 추가)
2. `RunStartScreenManager.cs` 작성, `_gameplaySceneName` = "Gameplay" 설정
3. `Begin Run` 버튼 OnClick → `OnBeginRunPressed()` 연결 (유니티 에디터에서 드래그 앤 드롭 설정 필요)
4. 플레이버 텍스트 + 캐릭터 등장 연출 추가
5. (심화) `CoopReadyCheck.cs` 추가해 P1/P2 입력 대기 구현

---

## 참고 링크

- SceneManager.LoadSceneAsync: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadSceneAsync.html
- DOTween 공식: http://dotween.demigiant.com/documentation.php
- CanvasGroup 페이드 패턴: https://docs.unity3d.com/ScriptReference/CanvasGroup.html
- Unity Learn — Scene Management Best Practices: https://learn.unity.com/tutorial/scene-management-best-practices
- 참고 게임 런 시작 연출: Hades(사당 연출), Dead Cells(감방 출발), Enter the Gungeon(엘리베이터 하강)
