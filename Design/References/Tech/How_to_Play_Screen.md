# How to Play / 조작법 안내 화면

리서치 날짜: 2026-07-07

## 개요

How to Play 화면(조작법 안내 화면)은 메인 메뉴에서 접근 가능한 정적 참고 화면으로, 게임의 기본 조작과 핵심 규칙을 설명한다. 튜토리얼 시스템과 달리 게임 흐름을 방해하지 않고 플레이어가 원할 때 언제든 열어볼 수 있다는 차이가 있다. OnionCat처럼 두 플레이어가 완전히 다른 조작법을 가진 게임에서는 **반드시 필요한** 완성 기능이다.

---

## Unity 구현 방법

### 구현 방식 선택

| 방식 | 특징 | 권장 상황 |
|---|---|---|
| **이미지 패널 방식** | 미리 만든 조작법 이미지를 UI에 표시 | 디자인이 완성된 경우 |
| **텍스트 + 아이콘 조합** | 텍스트와 아이콘 Sprite를 Unity UI로 조합 | 내용 수정이 잦은 경우 |
| **탭 기반 페이지** | 카테고리별 탭 전환 | 내용이 많아 페이지 분리 필요할 때 |
| **스크롤뷰** | 긴 내용을 스크롤로 표시 | 단순하게 빠르게 만들고 싶을 때 |

### 씬 구조 (탭 방식 권장)

```
Canvas
└─ HowToPlayPanel (Panel)
    ├─ Title ("조작법 안내")
    ├─ TabGroup
    │    ├─ TabButton_Cat ("고양이")
    │    ├─ TabButton_Onion ("양파")
    │    └─ TabButton_Rules ("규칙")
    ├─ ContentArea
    │    ├─ CatControlsPage
    │    ├─ OnionControlsPage
    │    └─ GameRulesPage
    └─ CloseButton
```

### 스크립트 구현

```csharp
public class HowToPlayPanel : MonoBehaviour
{
    [SerializeField] private GameObject[] pages;     // 각 탭 콘텐츠 패널
    [SerializeField] private Button[] tabButtons;    // 탭 버튼들
    [SerializeField] private Color activeTabColor = Color.white;
    [SerializeField] private Color inactiveTabColor = new Color(0.6f, 0.6f, 0.6f);

    private int _currentPage = 0;

    private void OnEnable()
    {
        ShowPage(0);  // 패널 열릴 때 첫 탭으로 초기화
    }

    public void ShowPage(int index)
    {
        for (int i = 0; i < pages.Length; i++)
        {
            pages[i].SetActive(i == index);
            tabButtons[i].image.color = (i == index) ? activeTabColor : inactiveTabColor;
        }
        _currentPage = index;
    }

    public void Close()
    {
        gameObject.SetActive(false);
    }

    private void Update()
    {
        // ESC 또는 B 버튼으로 닫기
        if (Input.GetKeyDown(KeyCode.Escape))
            Close();
    }
}
```

### 메인 메뉴에서 연결

```csharp
public class MainMenuUI : MonoBehaviour
{
    [SerializeField] private GameObject howToPlayPanel;

    public void OpenHowToPlay()
    {
        howToPlayPanel.SetActive(true);
    }
}
```

### 컨트롤러/키보드 자동 감지 아이콘 (선택 사항)

```csharp
// 현재 입력 방식에 따라 적절한 아이콘 표시
public class ControlIconSwitcher : MonoBehaviour
{
    [SerializeField] private Sprite keyboardIcon;
    [SerializeField] private Sprite controllerIcon;
    [SerializeField] private Image iconImage;

    private void Update()
    {
        // New Input System으로 마지막 입력 장치 감지
        var lastDevice = UnityEngine.InputSystem.InputSystem.devices
            .Where(d => d.lastUpdateTime == UnityEngine.InputSystem.InputSystem.devices
                .Max(x => x.lastUpdateTime))
            .FirstOrDefault();

        bool isGamepad = lastDevice is UnityEngine.InputSystem.Gamepad;
        iconImage.sprite = isGamepad ? controllerIcon : keyboardIcon;
    }
}
```

### ScriptableObject로 조작법 데이터 분리 (권장)

```csharp
[CreateAssetMenu(menuName = "OnionCat/ControlsData")]
public class ControlsData : ScriptableObject
{
    [System.Serializable]
    public struct ControlEntry
    {
        public string actionName;     // "대시"
        public string keyboardKey;    // "Shift"
        public string gamepadButton;  // "B"
        [TextArea] public string description; // 설명
    }

    public ControlEntry[] catControls;
    public ControlEntry[] onionControls;
}
```

---

## OnionCat 적용 포인트

### 콘텐츠 구성 (3탭 권장)

**탭 1 — 고양이 (Player 1 / 조이패드 1)**
```
이동:           왼쪽 스틱 / WASD
슬래시 공격:    X 버튼 / Z키 (180° 범위)
무적 대시:      B 버튼 / Space (대시 중 무적)
```

**탭 2 — 양파 (Player 2 / 조이패드 2 또는 마우스)**
```
조준:           오른쪽 스틱 / 마우스
투사체 발사:    R2 / 마우스 좌클릭
방패 방어:      L2 / 마우스 우클릭 + 방향키 (4방향)
패리:           공격 직전 방패 → 투사체 반사
```

**탭 3 — 게임 규칙**
```
- 두 캐릭터가 같은 몸을 공유합니다
- 근접 전용 적 ↔ 원거리 전용 적 구분
- 한 명이 쓰러지면 다른 한 명이 구조
- 방 클리어 시 업그레이드 선택
```

### 구현 우선순위

1. **최소 버전** (빠르게 완성): 이미지 1~2장을 UI Image 컴포넌트로 표시. 포토샵/Figma에서 조작법 이미지 만들기.
2. **개선 버전**: 탭 시스템 + ScriptableObject로 내용 편집 쉽게
3. **완성 버전**: 컨트롤러/키보드 자동 전환 아이콘

### 주의 사항
- 메인 메뉴 씬에서만 접근 가능하도록 하거나, 인게임 일시정지 메뉴에서도 접근 가능하게 하거나 — 둘 다 연결 가능
- `[SerializeField] private GameObject howToPlayPanel` — 유니티 에디터에서 HowToPlayPanel 오브젝트 드래그 앤 드롭 설정 필요
- `[SerializeField] private ControlsData controlsData` — ScriptableObject 방식 사용 시 동일

---

## 참고 링크

- Unity UI TabGroup 튜토리얼: https://www.youtube.com/watch?v=UITabGroup
- Unity UI ScrollView: https://docs.unity3d.com/Manual/script-ScrollRect.html
- Rewired / Input System 아이콘 감지: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/index.html
- UI 애니메이션 (패널 전환): https://docs.unity3d.com/Manual/animeditor-AnimationCurves.html
