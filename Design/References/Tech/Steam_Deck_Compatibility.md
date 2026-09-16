# Steam Deck 호환성 (Steam Deck Compatibility)

리서치 날짜: 2026-09-16

## 개요

Steam Deck은 Valve의 휴대용 PC 게임기로, 2024년 기준 인디 게임의 주요 플랫폼 중 하나.
"Steam Deck Verified" 배지를 받으면 Steam 페이지에 표시되어 판매에 직접 영향을 줌.
OnionCat은 로컬 2인 협력 게임이므로 Deck에서의 2인 플레이 경험도 고려 필요.

### 왜 중요한가?
- 인디 로그라이크 장르에서 Steam Deck 유저 비율이 높음 (Hades, Dead Cells 모두 Deck에서 인기)
- "Verified" 배지만으로도 가시성 증가
- 컨트롤러 전용 설계를 강제하므로 UI/UX 수준이 올라감

---

## Unity 구현 방법

### 1. 해상도 및 UI 스케일링

```csharp
// Steam Deck 네이티브 해상도: 1280×800 (16:10)
// 일반 PC는 1920×1080 (16:9)
// Canvas Scaler 설정:

// Canvas Scaler 컴포넌트:
// - UI Scale Mode: Scale With Screen Size
// - Reference Resolution: 1920×1080
// - Screen Match Mode: Match Width or Height
// - Match: 0.5 (너비와 높이 중간값)

// 코드로 해상도 확인:
void Start()
{
    Debug.Log($"Screen: {Screen.width}x{Screen.height}");
    Debug.Log($"DPI: {Screen.dpi}");
    // Deck: 1280×800 @ 800p
}
```

### 2. 컨트롤러 전용 UI 네비게이션

Steam Deck은 마우스 없음 → 모든 UI가 게임패드로 탐색 가능해야 함.

```csharp
// EventSystem 설정
// - StandaloneInputModule 대신 InputSystemUIInputModule 사용
// - Navigation: 모든 Button, Slider에 Explicit Navigation 설정

// 메뉴 예시: 버튼 간 Navigation 연결
public class MenuNavigationSetup : MonoBehaviour
{
    [SerializeField] private Button startButton;
    [SerializeField] private Button settingsButton;
    [SerializeField] private Button quitButton;

    private void Start()
    {
        // 위아래 방향키로 버튼 이동
        var startNav = startButton.navigation;
        startNav.mode = Navigation.Mode.Explicit;
        startNav.selectOnDown = settingsButton;
        startButton.navigation = startNav;

        var settingsNav = settingsButton.navigation;
        settingsNav.mode = Navigation.Mode.Explicit;
        settingsNav.selectOnUp = startButton;
        settingsNav.selectOnDown = quitButton;
        settingsButton.navigation = settingsNav;
        
        // 첫 번째 버튼 자동 선택
        EventSystem.current.SetSelectedGameObject(startButton.gameObject);
    }
}
```

### 3. 컨트롤러 프롬프트 아이콘

```csharp
// Deck은 PS 배치(×=확인, ○=취소) vs Xbox 배치(A=확인, B=취소)
// InputSystem의 lastUsedDevice로 감지

public class ControllerPromptDisplay : MonoBehaviour
{
    [SerializeField] private Sprite xboxASprite;
    [SerializeField] private Sprite deckCrossSprite;
    [SerializeField] private Image confirmIcon;

    private void Update()
    {
        if (Gamepad.current != null)
        {
            // Steam Deck은 XInput 또는 SDL로 잡힘
            // 실용적으로는 항상 Xbox 레이아웃 표시 (Deck도 Xbox 버튼 배치)
            confirmIcon.sprite = xboxASprite;
        }
    }
}
```

### 4. 성능 목표

```
Steam Deck 스펙:
- GPU: AMD RDNA 2 (8 CU, ~1.6 TFLOPS)
- RAM: 16GB LPDDR5
- 목표 FPS: 60fps @ 1280×800

Unity 최적화 체크리스트:
□ Sprite Atlas 사용 (Draw Call 감소)
□ 2D Physics Layer Matrix 설정 (불필요한 충돌 계산 제거)
□ Object Pooling (Instantiate/Destroy 최소화)
□ Camera Culling Mask (불필요한 레이어 렌더링 제외)
□ Audio Mixer: Compressed In Memory (메모리 절약)
□ Quality Settings: Medium 이하에서 60fps 확인
```

### 5. Proton 호환성 (Linux)

```
Steam Deck은 Linux (SteamOS) + Proton 레이어로 Windows 게임 실행.
Unity 게임 대부분 Proton에서 잘 동작하지만 주의사항:

- 파일 경로: 대소문자 구분 (Linux는 case-sensitive)
  → "Assets/Sprites/Cat.png" ≠ "assets/sprites/cat.png"
  → 프로젝트 내 모든 경로를 일관성 있게 유지

- 저장 경로: Application.persistentDataPath 사용 (크로스플랫폼 안전)
  → Windows: C:\Users\[User]\AppData\LocalLow\[Company]\[Product]
  → Linux/Deck: /home/deck/.config/unity3d/[Company]/[Product]

- 외부 DLL: Steamworks.NET은 Proton에서 정상 동작
```

### 6. Steam Deck Verified 조건 (Valve 공식)

```
4가지 카테고리 모두 Verified 등급 받아야 배지 획득:

1. 입력 (Input)
   ✅ 컨트롤러만으로 완전히 플레이 가능
   ✅ 게임 내 컨트롤러 아이콘 표시 (Xbox/Steam Deck 버튼)

2. 디스플레이 (Display)  
   ✅ 1280×800 지원 (기본 Deck 해상도)
   ✅ UI가 잘림 없이 표시됨

3. 원활한 실행 (Seamlessness)
   ✅ Steam Overlay 정상 동작
   ✅ 절전 모드 복귀 시 크래시 없음
   ✅ 마우스·키보드 관련 팝업 없음

4. 시스템 지원 (System Support)
   ✅ 기본 Proton으로 실행 가능 (또는 Linux 네이티브 빌드)
   ✅ 안티치트가 Linux 지원 (VAC/EAC 미사용이면 문제없음)
```

---

## OnionCat 적용 포인트

### 로컬 2인 협력 on Steam Deck

```
시나리오: 두 사람이 Steam Deck 화면을 같이 봄 (화면 공유)
→ 1280×800 해상도에서 두 플레이어의 UI 모두 잘 보여야 함
→ 폰트 크기 최소 16px (Deck 작은 화면에서 가독성)
→ 컨트롤러 2개 연결: Deck 자체 조이스틱(Player 1) + 외부 컨트롤러(Player 2)

// PlayerInput 2개 또는 SharedBodyInputRouter에서 Device 할당
// Deck 내장 컨트롤러 Device ID와 외부 컨트롤러 Device ID를 분리
```

### 개발 우선순위 체크리스트

```
1단계 (필수):
  □ Canvas Scaler: Scale with Screen Size, Match 0.5
  □ 1280×800 해상도 테스트 (Game View에서 직접 설정 가능)
  □ 모든 메뉴 버튼에 Explicit Navigation 연결
  □ Application.persistentDataPath로 세이브 경로 설정
  □ 파일 경로 대소문자 일관성 확인

2단계 (Verified 목표):
  □ 게임 내 Xbox/Deck 버튼 아이콘 표시
  □ 마우스 없이 완전 플레이 테스트 (터치패드도 가능)
  □ 60fps @ 1280×800 퍼포먼스 확인
  □ Steam Overlay (Shift+Tab) 동작 확인

3단계 (폴리시):
  □ 절전 모드 복귀 테스트 (OnApplicationFocus 처리)
  □ 한국어/영어 텍스트 Deck 화면 가독성 확인
```

---

## 참고 링크

- Steam Deck 개발자 가이드: https://partner.steamgames.com/doc/steamdeck
- Steam Deck Verified 기준: https://store.steampowered.com/steamdeck/verified
- Unity용 Steam Deck 최적화: https://docs.unity3d.com/Manual/SteamDeck.html
- Proton 호환성 DB: https://www.protondb.com/
- Unity Canvas Scaler 공식 문서: https://docs.unity3d.com/Manual/script-CanvasScaler.html
