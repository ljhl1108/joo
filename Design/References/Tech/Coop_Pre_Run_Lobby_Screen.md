# Co-op Pre-Run Lobby Screen (협동 플레이 런 시작 전 로비 화면)

리서치 날짜: 2026-10-03

## 개요

두 명이 함께 플레이하는 게임에서 "시작 버튼 누름 → 던전 입장" 사이에 위치하는 화면.
플레이어가 각자의 역할·조작 방식을 확인하고, 게임 시작에 동의하는 순간이다.

OnionCat은 Cat(키보드/패드)과 Onion(마우스+키보드)가 한 기기에서 플레이하는 **로컬 비대칭 협동** 구조 — 역할 고정이지만, 입력 방식 확인과 "준비 완료" 의식이 필요하다.

## Unity 구현 방법

### 1. 화면의 역할과 기능

```
[Lobby Screen]
┌─────────────────────────────────────┐
│  ← PLAYER 1 (Cat)                   │
│     Input: Keyboard / Controller    │
│     Controls 미리보기 (버튼 아이콘)    │
│     [READY ✓]                        │
│                                     │
│  ← PLAYER 2 (Onion)                  │
│     Input: Mouse + Keyboard         │
│     Controls 미리보기                 │
│     [READY ✓]                        │
│                                     │
│  둘 다 READY → 5초 카운트다운 → 시작   │
└─────────────────────────────────────┘
```

### 2. PlayerReadyState 구조

```csharp
public class CoopLobbyScreen : MonoBehaviour
{
    [SerializeField] private PlayerReadyPanel _catPanel;
    [SerializeField] private PlayerReadyPanel _onionPanel;
    [SerializeField] private TMPro.TextMeshProUGUI _countdownText;

    private bool _catReady;
    private bool _onionReady;
    private Coroutine _countdownCoroutine;

    // Cat은 패드 South 또는 Space, Onion은 마우스 클릭으로 READY
    public void SetCatReady(bool ready)
    {
        _catReady = ready;
        _catPanel.SetReady(ready);
        CheckBothReady();
    }

    public void SetOnionReady(bool ready)
    {
        _onionReady = ready;
        _onionPanel.SetReady(ready);
        CheckBothReady();
    }

    private void CheckBothReady()
    {
        if (_catReady && _onionReady)
        {
            if (_countdownCoroutine == null)
                _countdownCoroutine = StartCoroutine(StartCountdown());
        }
        else
        {
            if (_countdownCoroutine != null)
            {
                StopCoroutine(_countdownCoroutine);
                _countdownCoroutine = null;
                _countdownText.gameObject.SetActive(false);
            }
        }
    }

    private IEnumerator StartCountdown()
    {
        _countdownText.gameObject.SetActive(true);
        for (int i = 3; i > 0; i--)
        {
            _countdownText.text = i.ToString();
            yield return new WaitForSecondsRealtime(1f);
            // 카운트 중 READY 취소 시 CheckBothReady에서 중단됨
        }
        GameManager.Instance.ChangeState(GameState.Loading);
    }
}
```

### 3. 컨트롤러 아이콘 동적 표시

```csharp
public class PlayerReadyPanel : MonoBehaviour
{
    [SerializeField] private Image _controllerIcon;
    [SerializeField] private Sprite _keyboardSprite;
    [SerializeField] private Sprite _gamepadSprite;

    public void SetInputScheme(string scheme)
    {
        _controllerIcon.sprite = scheme == "Gamepad" ? _gamepadSprite : _keyboardSprite;
    }

    public void SetReady(bool ready)
    {
        // 색상·체크마크 토글
        _readyIndicator.SetActive(ready);
        GetComponent<Image>().color = ready ? Color.green : Color.white;
    }
}
```

### 4. 입력 감지 — New Input System

```csharp
// Cat 플레이어의 READY 입력 (패드 South or Space)
_catReadyAction = new InputAction(binding: "<Keyboard>/space");
_catReadyAction.AddBinding("<Gamepad>/buttonSouth");
_catReadyAction.performed += _ => SetCatReady(!_catReady); // 토글

// Onion 플레이어의 READY 입력 (좌클릭)
_onionReadyAction = new InputAction(binding: "<Mouse>/leftButton");
_onionReadyAction.performed += _ => SetOnionReady(!_onionReady);
```

### 5. 씬 흐름에서 위치

```
Main Menu
  ↓ "Start Game"
Coop Lobby Screen   ← 지금 이 화면
  ↓ 둘 다 READY + 카운트다운
Run Start (첫 번째 방 로드)
  ↓ 런 종료
Coop Run Result Screen
  ↓ 재시작 or 메뉴
```

### 6. 싱글 플레이 fallback

```csharp
// 싱글 (혼자 플레이)일 때 Onion 패널을 "AI Onion" 또는 "Solo Mode"로 표시
if (GameSettings.IsSolo)
{
    _onionPanel.SetSoloMode();
    _onionReady = true; // 자동 READY
}
```

### 7. 컨트롤 미리보기 애니메이션
- 각 플레이어 패널에 작은 gif-style 스프라이트 애니메이션 (3~4프레임)
- Cat: WASD → 방향키 화살표 아이콘 깜박임 / Onion: 마우스 커서 + 클릭 아이콘
- TMPro로 "Move: WASD  Dash: Space  Slash: F" 한 줄 표시

## OnionCat 적용 포인트

### 1. 비대칭 입력 인수인계 가이드
OnionCat은 두 플레이어 입력 방식이 완전히 다르므로 Lobby 화면이 **"입력 설명서" 역할**을 한다:
- Cat 패널: WASD/패드 조작 아이콘 + "Space to Dash"
- Onion 패널: 마우스 조준 + 클릭 공격 + QWER 스킬

### 2. 컨트롤러 없으면 Cat 패드 모드 안내
`CoopInputLayout`이 패드 감지 결과를 Lobby에 전달 → 패드 없으면 키보드 모드 안내 표시.

### 3. "처음 플레이하시나요?" 링크
Lobby에 작은 "Tutorial?" 버튼 → 컨트롤 설명 팝업 or Tutorial 씬 이동.

### 4. 빠른 재시작 지원
런 종료 후 Result Screen → "Play Again?" → Lobby 건너뛰고 바로 새 런 시작 옵션 제공.
`Quick_Restart_Between_Runs.md` 참고.

### 5. READY 취소 방지용 lock
카운트다운 1초 이하에서는 READY 취소 불가 (딜레이 후 시작 방지).

## 참고 링크

- It Takes Two 로비 UX 분석: 게임 시작 전 각 캐릭터 조작 설명 방식 참고
- Unity Input System PlayerInput: https://docs.unity3d.com/Packages/com.unity.inputsystem@latest
- Deep Rock Galactic: 두 플레이어 역할 표시 + 준비 확인 UI 참고
- Lovers in a Dangerous Spacetime: 탑승 화면 → 바로 게임 시작 플로우 참고
