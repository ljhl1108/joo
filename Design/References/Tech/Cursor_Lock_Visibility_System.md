# Cursor Lock & Visibility System (커서 잠금 & 가시성 관리)

리서치 날짜: 2026-09-13

## 개요

Unity에서 마우스 커서의 **표시 여부(visible)** 와 **잠금 상태(lockState)** 를 상황에 따라 동적으로 제어하는 시스템이다.

OnionCat에서 이것이 특히 중요한 이유:
- **P2(Onion)는 마우스로 조준** → 게임플레이 중 커서가 게임 창 안에서 자유롭게 움직여야 함
- **메뉴/일시정지** → 커서가 UI 버튼 위로 이동해야 함
- **씬 전환 중** → 커서가 화면에 보이면 연출이 어색함
- 커서를 잘못 관리하면: 커서가 창 밖으로 나가거나, 메뉴에서 클릭이 안 되거나, 게임 화면에 OS 화살표가 보임

---

## Unity 커서 제어 기본

### Unity API

```csharp
// 커서 잠금 상태
Cursor.lockState = CursorLockMode.None;      // 자유 이동, 화면 밖 가능
Cursor.lockState = CursorLockMode.Confined;  // 게임 창 안에 제한
Cursor.lockState = CursorLockMode.Locked;    // 화면 중앙 고정 (FPS용, 조준 불가)

// 커서 표시 여부
Cursor.visible = true;
Cursor.visible = false;
```

### OnionCat에서의 상태별 설정

| 게임 상태 | lockState | visible | 이유 |
|-----------|-----------|---------|------|
| 게임플레이 중 | Confined | true | P2 마우스 조준, 창 밖 이탈 방지 |
| 일시정지 메뉴 | None | true | UI 버튼 클릭 가능 |
| 게임 오버 화면 | None | true | 재시작/메뉴 버튼 클릭 |
| 메인 메뉴 | None | true | 일반 UI 탐색 |
| 씬 전환 중 | Confined | false | 전환 연출 중 커서 숨김 |

---

## Unity 구현 방법

### CursorManager 싱글턴

```csharp
public class CursorManager : MonoBehaviour
{
    public static CursorManager Instance { get; private set; }

    [SerializeField] private Texture2D gameplayCursor;       // P2 조준 커서 이미지
    [SerializeField] private Vector2 cursorHotspot = new Vector2(16, 16); // 클릭 기준점

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void SetGameplayCursor()
    {
        Cursor.lockState = CursorLockMode.Confined;
        Cursor.visible = true;
        if (gameplayCursor != null)
            Cursor.SetCursor(gameplayCursor, cursorHotspot, CursorMode.Auto);
    }

    public void SetMenuCursor()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
        Cursor.SetCursor(null, Vector2.zero, CursorMode.Auto); // 기본 OS 커서
    }

    public void SetTransitionCursor()
    {
        Cursor.lockState = CursorLockMode.Confined;
        Cursor.visible = false;
    }

    public void RestoreCursorState()
    {
        if (GameStateManager.Instance != null && GameStateManager.Instance.IsGameplay)
            SetGameplayCursor();
        else
            SetMenuCursor();
    }

    private void OnApplicationFocus(bool hasFocus)
    {
        if (hasFocus)
            RestoreCursorState();
        else
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
    }
}
```

### ESC 일시정지와 커서 연동

```csharp
// PauseMenuController.cs
public void Pause()
{
    Time.timeScale = 0f;
    CursorManager.Instance.SetMenuCursor();
    pauseMenuPanel.SetActive(true);
}

public void Resume()
{
    pauseMenuPanel.SetActive(false);
    Time.timeScale = 1f;
    CursorManager.Instance.SetGameplayCursor();
}
```

### 씬 전환 시 자동 커서 설정

```csharp
// SceneLoader.cs
private IEnumerator LoadSceneAsync(string sceneName)
{
    CursorManager.Instance.SetTransitionCursor(); // 전환 중 커서 숨김
    yield return StartCoroutine(FadeOut());

    AsyncOperation op = SceneManager.LoadSceneAsync(sceneName);
    while (!op.isDone) yield return null;

    if (sceneName == "MainMenu" || sceneName == "GameOver")
        CursorManager.Instance.SetMenuCursor();
    else
        CursorManager.Instance.SetGameplayCursor();

    yield return StartCoroutine(FadeIn());
}
```

### 커스텀 커서 임포트 설정 (유니티 에디터에서 설정 필요)
1. Project에 커서용 PNG 임포트 (권장 크기: 32×32 또는 64×64)
2. Inspector에서 Texture Type → **Cursor** 로 변경
3. Apply
4. `CursorManager` 컴포넌트의 `gameplayCursor` 필드에 드래그 앤 드롭

### 풀스크린 전환 후 커서 재적용

```csharp
// SettingsMenu.cs
public void ToggleFullscreen()
{
    Screen.fullScreen = !Screen.fullScreen;
    StartCoroutine(ReapplyCursorNextFrame());
}

private IEnumerator ReapplyCursorNextFrame()
{
    yield return null; // 1프레임 대기 후 재적용
    CursorManager.Instance.RestoreCursorState();
}
```

---

## OnionCat 적용 포인트

### 1. P2 조준 커서 = 게임의 얼굴
P2의 마우스 커서가 항상 화면에 보임. 기본 OS 화살표 커서 대신 **Onion 식물 테마 커서** (씨앗 모양 또는 십자선+새싹 디자인)로 커스터마이징 → 게임 분위기와 일체감.

### 2. Confined vs Locked 선택
OnionCat은 P2가 화면 내 자유롭게 조준해야 하므로 **반드시 `Confined`**. `Locked`는 FPS용으로 마우스 조준이 불가능해짐.

### 3. 업그레이드로 커서 모양 변경
Onion 업그레이드 "정밀 조준" 획득 시 커서가 십자선에서 원형 조준경으로 변경:
```csharp
CursorManager.Instance.SetGameplayCursor(upgradedCursorTexture);
```
인벤토리 UI 없이 커서 모양만으로 업그레이드 상태 시각화.

### 4. 대비 확보 (접근성)
커스텀 커서가 배경에 묻히지 않도록: 커서 이미지에 얇은 흰색 테두리 + 어두운 안쪽 (어떤 배경에서도 항상 보임).

---

## 유의 사항

- **Mac 빌드**: `CursorLockMode.Confined`가 macOS에서 지원되지 않을 수 있음. Mac 타겟 시 테스트 필요
- **에디터 vs 빌드**: 에디터에서 `Confined`는 에디터 창 전체에 적용됨. 빌드 테스트로 실제 동작 확인 필수
- **WebGL**: 브라우저 보안 정책에 따라 커서 제어가 제한될 수 있음

---

## 참고 링크

- Unity Docs - Cursor class: https://docs.unity3d.com/ScriptReference/Cursor.html
- Unity Docs - CursorLockMode: https://docs.unity3d.com/ScriptReference/CursorLockMode.html
- Unity Docs - Cursor.SetCursor: https://docs.unity3d.com/ScriptReference/Cursor.SetCursor.html
- Custom Cursor Tutorial: YouTube 검색 "unity custom cursor 2d"
