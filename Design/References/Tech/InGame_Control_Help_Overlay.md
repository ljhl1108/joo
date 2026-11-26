# 인게임 조작 도움말 오버레이

리서치 날짜: 2026-11-26

## 개요

게임을 종료하거나 메뉴로 가지 않고도, **플레이 중에 조작법을 빠르게 확인**할 수 있는 반투명 오버레이. How_to_Play_Screen(전용 메뉴 화면)과 달리 게임 화면 위에 얹혀서 1~2초 만에 보고 닫는 방식이다.

OnionCat에 필요한 이유:
- 고양이·양파의 조작이 **비대칭**이라 새 플레이어가 헷갈림 (특히 패드 없을 때 고양이 단축키가 많음)
- 처음 몇 판은 "어? 합동기가 뭐였지?" 하고 멈추는 순간이 자주 생김
- 일시정지 메뉴는 무겁고, 별도 화면은 멀리 있음 → 가볍게 꺼내볼 수 있는 카드 한 장

---

## 설계 원칙

### 1. 토글 방식 (Toggle, not Hold)
- 단일 키(기본: **Tab** 또는 **F1**)로 열고 닫기
- **Hold 방식은 금지**: 조작법을 보는 동안 계속 버튼을 누르고 있어야 하면 한 손이 묶임
- 오버레이가 열린 동안에는 게임을 **자동 일시정지** (Game.IsPaused = true)
  → 보는 사이에 적에게 맞는 불편함 방지

### 2. 2개 탭 (고양이 / 양파)
OnionCat처럼 비대칭 조작이면 **탭 분리**가 필수:
```
[ 고양이 (P1) ]  [ 양파 (P2) ]
(현재 패드 연결 여부에 따라 자동으로 올바른 탭을 먼저 보여줌)
```
- 열릴 때 P1 입력 디바이스가 패드면 → 고양이(패드 아이콘) 탭 먼저
- 패드 없으면 → 고양이(키보드 아이콘) 탭 먼저

### 3. 아이콘 + 텍스트
- 버튼 아이콘(패드: Xbox 버튼, 키보드: 키 그림)을 먼저 보여주고 옆에 한 줄 설명
- `Controller_Prompt_Icon_System.md` 참고 — 런타임에 연결 디바이스에 맞는 아이콘 자동 선택
- 최대 8줄 (한 화면에 다 보이게)

### 4. 가볍고 빠른 열기
- 오버레이 애니메이션: 페이드인 0.1초 (복잡한 슬라이드 불필요)
- 닫기: 같은 키 or Esc or 아무 게임 버튼이나 누르면 닫힘
- 오버레이가 떠 있는 동안에는 게임 입력 무시

---

## Unity 구현 방법

### 1. 오버레이 프리팹 구조

```
ControlHelpOverlay (Canvas, 월드 위 별도 캔버스 or HUD 캔버스 최상단)
├── Background (Panel, alpha 0.85 검정)
├── TabGroup
│   ├── TabButton_Cat (Button)
│   └── TabButton_Onion (Button)
├── CatControlPanel (보여지는 패널)
│   ├── KeyRow × 8 (아이콘 + 텍스트)
└── OnionControlPanel (숨겨진 패널)
    └── KeyRow × 8
```

### 2. 오버레이 열기/닫기

```csharp
// ControlHelpOverlay.cs
public class ControlHelpOverlay : MonoBehaviour
{
    [SerializeField] private GameObject _root;
    [SerializeField] private CanvasGroup _canvasGroup;

    private bool _isOpen;
    private float _fadeSpeed = 10f;

    void Update()
    {
        // 입력은 항상 New Input System의 HelpAction으로
        // InputAction "ShowHelp" (Tab / F1 / Select 버튼)
    }

    public void Toggle()
    {
        _isOpen = !_isOpen;
        GameManager.Instance.SetOverlayPause(_isOpen);
        StopAllCoroutines();
        StartCoroutine(_isOpen ? FadeIn() : FadeOut());
    }

    IEnumerator FadeIn()
    {
        _root.SetActive(true);
        while (_canvasGroup.alpha < 1f)
        {
            _canvasGroup.alpha += Time.unscaledDeltaTime * _fadeSpeed;
            yield return null;
        }
        _canvasGroup.alpha = 1f;
    }

    IEnumerator FadeOut()
    {
        while (_canvasGroup.alpha > 0f)
        {
            _canvasGroup.alpha -= Time.unscaledDeltaTime * _fadeSpeed;
            yield return null;
        }
        _root.SetActive(false);
        _isOpen = false;
    }
}
```

### 3. 디바이스별 탭 자동 선택

```csharp
void OnEnable()
{
    // 패드 연결 여부에 따라 탭 자동 선택
    bool padConnected = Gamepad.all.Count > 0;
    ShowTab(padConnected ? CatPadPanel : CatKeyboardPanel);
}
```

### 4. InputAction 등록

```
// InputActions에 "UI/ShowHelp" 추가
// Binding: Tab (Keyboard) + Select (Gamepad) + F1 (Keyboard)
// 주의: 이 액션은 GameplayActive 여부와 무관하게 항상 활성화
```

### 5. Time.timeScale vs unscaledTime 주의

오버레이가 뜬 동안 `Time.timeScale = 0`이면:
- 모든 애니메이션 멈춤 (파티클, 적 움직임)
- **UI 애니메이션도 멈춤 → `Time.unscaledDeltaTime` 사용**

```csharp
// GameManager.cs
public void SetOverlayPause(bool paused)
{
    // 직접 timeScale 건드리지 않음 — CLAUDE.md 규칙
    // 대신 GameState를 Paused로 (Pause 메뉴와 같은 상태 사용)
    if (paused) ChangeState(GameState.Paused);
    else        ChangeState(prevState);
}
```

---

## OnionCat 적용 포인트

### 고양이 탭 내용 (패드 없는 경우)
```
WASD          이동
Space         대쉬 (충전식)
Shift(왼쪽)   할퀴기
Ctrl(왼쪽)    특수 공격 (야성 게이지)
Q             씨앗 던지기
E             합동기 (양파도 동시 입력)
Z / X         가방 순환
```

### 양파 탭 내용
```
마우스 이동    조준
마우스 LBT    발사
마우스 RBT    방패 / 패리
Q/W/E/R       스킬 1~4
1~5           가방 슬롯
Space         합동기 (고양이도 동시 입력)
```

### 오버레이를 여는 추천 위치
HUD 왼쪽 상단 구석에 **반투명 "?" 아이콘** 배치:
- 처음 플레이하는 사람이 "여기 누르면 조작법 나온다"는 걸 발견
- 2회 이후는 단축키(Tab)로 더 빠르게

### 처음 실행 시 자동 힌트
런 첫 번째 방에서 **Tab 버튼이 깜빡이는 토스트** 1회 표시:
```
"조작법이 헷갈리면 Tab을 눌러보세요"  (3초 후 사라짐)
```
`Tutorial_Seen_State_Persistence_System.md` 패턴 활용 — 한 번 보면 다시 안 나타남.

---

## 참고 링크
- [Unity New Input System: InputAction](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.8/manual/Actions.html)
- [Unity CanvasGroup API](https://docs.unity3d.com/ScriptReference/CanvasGroup.html)
- [Time.unscaledDeltaTime 주의사항](https://docs.unity3d.com/ScriptReference/Time-unscaledDeltaTime.html)
- 연관 파일: `Controller_Prompt_Icon_System.md`, `Asymmetric_HUD_Layout_System.md`, `Tutorial_Seen_State_Persistence_System.md`
