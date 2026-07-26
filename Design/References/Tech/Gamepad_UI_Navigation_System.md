# 게임패드 UI 탐색 시스템 (Gamepad UI Navigation)

리서치 날짜: 2026-07-26

## 개요

로컬 2인 코업 게임에서 메뉴를 게임패드로 탐색할 수 있어야 한다.
Unity의 New Input System과 UI Toolkit/UGUI(EventSystem)를 연동하면 키보드·마우스 없이도
버튼 선택, 슬라이더 조작, 메뉴 이동이 가능하다.
OnionCat은 2P 로컬 코업이므로 **최소 한 명은 컨트롤러 사용** → 게임패드 UI 탐색은 필수.

---

## Unity 구현 방법

### 1. Input System 패키지 설정

```
Package Manager → com.unity.inputsystem 설치
Player Settings → Active Input Handling → "Input System Package (New)" 선택
```

`EventSystem` 게임오브젝트에 있는 기본 `StandaloneInputModule` → 제거 후
`InputSystemUIInputModule` (New Input System 제공) 추가.

---

### 2. PlayerInput + UI 연동

```csharp
// PlayerInput 컴포넌트 → Actions 에셋에 UI Action Map 추가
// Default Input Actions에는 이미 "UI" Action Map 내장

// Navigate: 방향키 / 왼쪽 스틱
// Submit: South 버튼 (A/X) → Button 클릭
// Cancel: East 버튼 (B/Circle) → 뒤로
// ScrollWheel: 우측 스틱 → 스크롤
```

**Inspector 설정**:
- `EventSystem` → `InputSystemUIInputModule` → Actions 에셋 연결
- UI 요소들이 `Selectable` 컴포넌트를 가지면 자동으로 탐색 가능

---

### 3. 첫 선택 항목 지정 (First Selected)

씬 로드 시 자동으로 첫 버튼을 선택 상태로:

```csharp
public class MenuController : MonoBehaviour
{
    [SerializeField] private GameObject firstSelected;

    void OnEnable()
    {
        EventSystem.current.SetSelectedGameObject(null);
        EventSystem.current.SetSelectedGameObject(firstSelected);
    }
}
```

**주의**: `SetSelectedGameObject(null)` 후 다시 설정해야 이미 선택된 경우에도 갱신됨.

---

### 4. 커스텀 선택 강조 (Selection Highlight)

게임패드로 선택된 버튼을 시각적으로 표현:

```csharp
// Button 컴포넌트 → Navigation 설정
// Colors → Normal/Highlighted/Selected/Pressed 색상 설정

// 또는 코드로 커스텀 처리
public class SelectableHighlight : MonoBehaviour, ISelectHandler, IDeselectHandler
{
    [SerializeField] private Image outline;

    public void OnSelect(BaseEventData eventData)
    {
        outline.enabled = true;
    }

    public void OnDeselect(BaseEventData eventData)
    {
        outline.enabled = false;
    }
}
```

---

### 5. 2인 컨트롤러 → 메뉴는 1명만 조작

로컬 2P 환경에서 메뉴 탐색은 1번 플레이어(또는 먼저 입력한 플레이어)만 담당:

```csharp
public class MenuInputHandler : MonoBehaviour
{
    private PlayerInput _p1Input;

    void Start()
    {
        // P1 PlayerInput만 UI Action Map으로 전환
        _p1Input = FindObjectOfType<PlayerInput>();
        _p1Input.SwitchCurrentActionMap("UI");
    }

    public void OnReturnToGameplay()
    {
        _p1Input.SwitchCurrentActionMap("Player");
    }
}
```

또는 `InputSystemUIInputModule`에 특정 PlayerInput 연결 설정.

---

### 6. 슬라이더·토글 게임패드 조작

볼륨 슬라이더 등을 게임패드 좌우로 조작:

```csharp
public class SliderGamepadHandler : MonoBehaviour, IMoveHandler
{
    [SerializeField] private Slider slider;
    [SerializeField] private float step = 0.1f;

    public void OnMove(AxisEventData eventData)
    {
        if (eventData.moveDir == MoveDirection.Left)
            slider.value -= step;
        else if (eventData.moveDir == MoveDirection.Right)
            slider.value += step;
    }
}
```

---

### 7. 화면 전환 시 선택 초기화

씬·패널 전환 시마다 선택 상태를 리셋:

```csharp
public class PanelManager : MonoBehaviour
{
    [SerializeField] private GameObject[] panels;
    [SerializeField] private GameObject[] defaultSelections; // 패널별 첫 버튼

    public void SwitchPanel(int index)
    {
        for (int i = 0; i < panels.Length; i++)
            panels[i].SetActive(i == index);

        StartCoroutine(SetSelectionNextFrame(defaultSelections[index]));
    }

    IEnumerator SetSelectionNextFrame(GameObject target)
    {
        yield return null; // 한 프레임 대기 (UI 활성화 완료 후)
        EventSystem.current.SetSelectedGameObject(null);
        EventSystem.current.SetSelectedGameObject(target);
    }
}
```

---

### 8. Navigation 설정 (방향 탐색 경로)

각 Selectable UI 요소에서 Inspector → Navigation:
- `Automatic`: Unity가 거리 기반으로 자동 연결
- `Explicit`: 위/아래/좌/우 각각 연결할 오브젝트 지정
- `None`: 방향 탐색 비활성화 (슬라이더 내부 등)

**권장**: 복잡한 레이아웃은 `Explicit` 사용. 단순 세로 메뉴는 `Automatic`.

---

### 9. 게임패드 커서 숨기기

게임패드 입력 감지 시 마우스 커서 숨기기:

```csharp
public class InputDeviceDetector : MonoBehaviour
{
    void Update()
    {
        if (Gamepad.current != null && Gamepad.current.wasUpdatedThisFrame)
            Cursor.visible = false;

        if (Mouse.current != null && Mouse.current.delta.ReadValue().magnitude > 0.1f)
            Cursor.visible = true;
    }
}
```

---

## OnionCat 적용 포인트

### 메뉴 계층
```
메인 메뉴 → [시작, 설정, 종료]
  └ 설정   → [음량, 해상도, 전체화면, 뒤로]
  └ 캐릭터 선택 → (1P Cat / 2P Onion 자동)
일시정지 → [재개, 재시작, 메뉴로]
업그레이드 선택 → [3개 카드 중 1개 선택]
```

### 구현 우선순위 (개발 단계별)
1. **업그레이드 선택 화면** — 게임 중 가장 자주 쓰이는 UI, 게임패드 필수
2. **일시정지 메뉴** — ESC/Start 버튼으로 열기
3. **메인 메뉴** — 게임패드로 바로 시작 가능하게
4. **설정 슬라이더** — 마지막에 추가

### 1P(Cat) vs 2P(Onion) 메뉴 조작 분리
- 메뉴는 1P(Cat 조이스틱/키보드)가 조작
- 2P(Onion 마우스)는 메뉴에서 대기
- 업그레이드 선택 시 **두 플레이어가 동시에 투표** → 다수결 채택 방식도 고려 (재미 요소)

### 업그레이드 카드 선택 구현
```csharp
// 3개 카드에 Selectable + Explicit Navigation 설정
// 좌우 방향키로 이동, Submit(A)으로 선택
// 선택 즉시 나머지 카드 비활성화 + 씬 재개
```

---

## 참고 링크

- [Unity Docs: Input System UI Support](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/UISupport.html)
- [Unity Docs: Selectable Navigation](https://docs.unity3d.com/Manual/nav-NavigationControls.html)
- [Unity Docs: EventSystem](https://docs.unity3d.com/Manual/EventSystem.html)
- [Brackeys: Controller Input in Unity (New Input System)](https://www.youtube.com/watch?v=p-3S73MaDP8)
- [Game Dev Guide: UI Navigation with New Input System](https://www.youtube.com/watch?v=MmE_JsHPAcc)
- [Unity Forum: First Selected Button not working](https://forum.unity.com/threads/eventsystem-setselectedgameobject-not-working.903021/)
