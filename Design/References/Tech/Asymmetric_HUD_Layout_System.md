# Asymmetric HUD Layout System

리서치 날짜: 2026-09-20

## 개요

두 명의 플레이어가 **서로 다른 역할**을 가진 게임에서, 각 플레이어에게 필요한 정보가 다르다.
OnionCat의 경우:
- **Cat (Player 1)**: 현재 HP, 대쉬 쿨다운
- **Onion (Player 2)**: 씨앗 탄약, 실드 쿨다운, 마우스 조준 리티클

이 두 정보를 하나의 화면에 자연스럽게 배치하면서 서로 방해하지 않는 HUD 설계가 핵심이다.

---

## 개념 설계

### 공간 분리 원칙

로컬 코업에서 비대칭 HUD를 배치하는 두 가지 전략:

#### 전략 1: 좌우 분리 (권장)
- Cat 정보: 화면 **왼쪽 하단**
- Onion 정보: 화면 **오른쪽 하단**
- 공유 정보 (층수, 공유 버프): 화면 **상단 중앙**

```
┌─────────────────────────────────────────┐
│           [Floor 2] [Shared Buffs]      │ ← 공유 UI
│                                         │
│                                         │
│                                         │
│  [Cat HP] [Dash]        [Seeds] [Shield]│ ← 각자 UI
└─────────────────────────────────────────┘
```

#### 전략 2: 캐릭터 기반 (월드 스페이스)
- 각 역할의 정보를 캐릭터 위에 표시 (월드 스페이스 Canvas)
- Cat 머리 위: HP 바
- Onion 주변: 실드 오버레이, 탄약 표시
- 단점: 화면이 복잡해짐, 가독성 낮음

→ **전략 1 (화면 좌우 분리)** 권장

---

## Unity 구현 방법

### Canvas 설정

```
Canvas (Screen Space - Overlay)
├── SharedPanel (상단 중앙)
│   ├── FloorLabel (TextMeshPro)
│   └── SharedBuffList
├── CatPanel (하단 왼쪽)
│   ├── HealthBar
│   │   ├── BarFill (Image - filled)
│   │   └── HealthText (TMP)
│   └── DashCooldown
│       ├── CooldownFill (Image - filled, radial)
│       └── DashReadyIcon
└── OnionPanel (하단 오른쪽)
    ├── SeedCounter
    │   ├── SeedIcon
    │   └── SeedCountText (TMP)
    └── ShieldCooldown
        ├── ShieldFill (Image - filled, radial)
        └── ShieldReadyIcon
```

### RectTransform 앵커 설정

```csharp
// CatPanel: 왼쪽 하단 고정
// anchorMin = (0, 0), anchorMax = (0, 0)
// pivot = (0, 0)
// anchoredPosition = (16, 16) // 16px 여백

// OnionPanel: 오른쪽 하단 고정
// anchorMin = (1, 0), anchorMax = (1, 0)
// pivot = (1, 0)
// anchoredPosition = (-16, 16)
```

### HP 바 연동

```csharp
public class CatHUDController : MonoBehaviour
{
    [SerializeField] private Image _healthFill;
    [SerializeField] private TMP_Text _healthText;
    [SerializeField] private Image _dashFill;

    private PlayerHealth _health;
    private DashAbility _dash;

    void Awake()
    {
        _health = FindFirstObjectByType<PlayerHealth>();
        _dash = FindFirstObjectByType<DashAbility>();
    }

    void Update()
    {
        if (_health == null) return;

        float ratio = (float)_health.CurrentHealth / _health.MaxHealth;
        _healthFill.fillAmount = ratio;
        _healthText.text = $"{_health.CurrentHealth}/{_health.MaxHealth}";

        _dashFill.fillAmount = _dash.IsReady ? 1f : _dash.CooldownProgress;
    }
}
```

### 쿨다운 표시 (방사형)

Image 컴포넌트:
- Image Type: **Filled**
- Fill Method: **Radial 360**
- Fill Origin: **Top**
- 100% = 준비됨, 0%→100% 채워지는 애니메이션

```csharp
// DOTween으로 쿨다운 완료 시 "팡" 효과
_dashFill.DOFillAmount(1f, _dash.CooldownDuration)
    .OnComplete(() => _dashReadyIcon.transform.DOPunchScale(Vector3.one * 0.3f, 0.2f));
```

### Onion 실드 상태 표시

실드는 3가지 상태: 준비 / 사용 중 / 쿨다운

```csharp
public class OnionHUDController : MonoBehaviour
{
    [SerializeField] private Image _shieldFill;
    [SerializeField] private Image _shieldIcon;
    [SerializeField] private Color _readyColor, _activeColor, _cooldownColor;

    void Update()
    {
        var shield = OnionShield.Instance;
        if (shield == null) return;

        switch (shield.State)
        {
            case ShieldState.Ready:
                _shieldFill.fillAmount = 1f;
                _shieldIcon.color = _readyColor;
                break;
            case ShieldState.Active:
                _shieldFill.fillAmount = shield.ActiveProgress; // 남은 지속시간
                _shieldIcon.color = _activeColor;
                break;
            case ShieldState.Cooldown:
                _shieldFill.fillAmount = shield.CooldownProgress;
                _shieldIcon.color = _cooldownColor;
                break;
        }
    }
}
```

### 씨앗(탄약) 카운터

```csharp
// 텍스트 숫자 대신 씨앗 아이콘을 나열하는 방식도 좋음
// 최대 5발이면 아이콘 5개 → 사용한 만큼 dimmed (투명도 낮춤)
for (int i = 0; i < _seedIcons.Length; i++)
{
    _seedIcons[i].color = i < _currentSeeds
        ? Color.white
        : new Color(1f, 1f, 1f, 0.2f);
}
```

---

## OnionCat 적용 포인트

### 구현 우선순위

1. **HP 바 먼저** — Cat 플레이어가 가장 먼저 확인하는 정보
2. **대쉬 쿨다운** — 대쉬는 생존기이므로 준비 여부가 중요
3. **씨앗 카운터** — 아이콘 5개 방식이 직관적
4. **실드 쿨다운** — 패리 기회 타이밍을 알아야 함

### 폰트 주의

- CLAUDE.md 규칙: **UI 문구는 영어로** (TMP 폰트에 한글 글리프 없음)
- HP: `HP: 5/8` 또는 `5 / 8`
- 대쉬: `DASH READY` / `DASH: 1.2s`
- 실드: `SHIELD` + 방사형 채우기

### 게임 상태별 가시성

```csharp
// 업그레이드 선택 중 HUD 숨기기
GameManager.OnStateChanged += state =>
{
    bool showHUD = state == GameState.Gameplay;
    _catPanel.SetActive(showHUD);
    _onionPanel.SetActive(showHUD);
    // SharedPanel은 항상 표시
};
```

### 픽셀 완벽성

- PPU 32 환경 → HUD 요소도 2의 배수 픽셀 단위로 배치
- Canvas Scaler: **Scale With Screen Size**, Reference = 640×360, Match = 0.5
- HUD 스프라이트 Import: PPU 32, Filter = Point, Compression = None

---

## 참고 링크

- [Unity Canvas - Screen Space Overlay](https://docs.unity3d.com/Manual/class-Canvas.html)
- [TextMeshPro 공식 문서](https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html)
- [Image Fill Types - Unity Manual](https://docs.unity3d.com/Manual/script-Image.html)
- [Asymmetric Coop HUD Design - Game UI Database](https://www.gameuidatabase.com/)
- [DOTween - Unity Asset Store](https://assetstore.unity.com/packages/tools/animation/dotween-hotween-v2-27676)
