# Solo Co-op Fallback System (1인 플레이 모드)

리서치 날짜: 2026-11-07

## 개요

2인 협동 게임에서 한 명이 혼자 플레이하려 할 때 어떻게 처리할 것인가. OnionCat은 "고양이 등에 양파 화분"이라는 공유 몸체 구조로, 본질적으로 2인용 게임이다.

**선택지**:
1. **봇 AI 파트너**: 2P가 AI로 대신 조작
2. **단일 플레이어 모드**: 한 명이 두 캐릭터를 모두 조작
3. **자동화 보조**: 2P가 자동으로 쏘거나 단순 패턴만 수행
4. **완전 1인용 모드 차단**: "2인 필수" 명시, 솔로 미지원

OnionCat에 가장 적합한 접근: **"자동화 보조(Auto-Onion)" + "단일 플레이어 모드" 선택지 제공**

---

## Unity 구현 방법

### 1. 세션 시작 시 플레이어 수 감지

```csharp
// CoopSessionManager.cs
public enum PlayMode { Solo, Coop }

public class CoopSessionManager : MonoBehaviour
{
    public static PlayMode CurrentMode { get; private set; }

    void Awake()
    {
        // 패드 연결 감지 (New Input System)
        bool gamepadConnected = Gamepad.all.Count > 0;
        
        // 사용자 선택 (런 시작 화면에서)
        CurrentMode = GamepadConnected ? PlayMode.Coop : PlayMode.Solo;
    }
}
```

### 2. Auto-Onion (AI 보조 양파)

2P 입력 없이 양파가 자동으로 행동하는 가장 단순한 솔로 모드:

```csharp
// AutoOnionController.cs
public class AutoOnionController : MonoBehaviour
{
    [SerializeField] private OnionShooter shooter;
    [SerializeField] private float autoAimRange = 8f;
    [SerializeField] private float shootInterval = 0.8f;
    
    private float _shootTimer;

    void Update()
    {
        if (CoopSessionManager.CurrentMode != PlayMode.Solo) return;
        
        _shootTimer += Time.deltaTime;
        if (_shootTimer < shootInterval) return;
        
        // 가장 가까운 적을 향해 자동 발사
        EnemyBase nearest = FindNearestEnemy();
        if (nearest != null)
        {
            Vector2 dir = (nearest.transform.position - transform.position).normalized;
            shooter.Shoot(dir);
            _shootTimer = 0f;
        }
    }
    
    EnemyBase FindNearestEnemy()
    {
        EnemyBase best = null;
        float bestDist = autoAimRange;
        foreach (var e in EnemyBase.Active)
        {
            float d = Vector2.Distance(transform.position, e.transform.position);
            if (d < bestDist) { best = e; bestDist = d; }
        }
        return best;
    }
}
```

### 3. 단일 플레이어 모드 — 키보드로 양파 직접 조작

```csharp
// SoloModeInputHandler.cs
// 1인이 고양이(패드/WASD)와 양파(마우스+Q~R)를 모두 조작
// OnionCat의 기존 키 레이아웃이 이미 이 분리를 지원!
// → "양파 키보드 키는 페어링과 무관한 독립 InputAction(OnionInputKeys)"이므로
//    패드 없이 키보드만으로 플레이가 이미 절반은 구현되어 있음

public class SoloModeInputHandler : MonoBehaviour
{
    void Awake()
    {
        if (CoopSessionManager.CurrentMode == PlayMode.Solo)
        {
            // 고양이를 키보드 WASD로 조작
            // 양파를 마우스+숫자키로 조작
            // → 기존 CoopInputLayout이 처리하므로 추가 코드 최소화
        }
    }
}
```

### 4. 솔로 모드 난이도 조정

2인 기준으로 설계된 적 HP/피해를 솔로 시 보정:

```csharp
// DifficultyScaler.cs
public static class DifficultyScaler
{
    public static float EnemyHpMultiplier =>
        CoopSessionManager.CurrentMode == PlayMode.Solo ? 0.7f : 1.0f;
    
    public static float EnemyDamageMultiplier =>
        CoopSessionManager.CurrentMode == PlayMode.Solo ? 0.8f : 1.0f;
}
```

```csharp
// EnemyBase.cs 에서
void Start()
{
    _maxHp = Mathf.RoundToInt(baseHp * DifficultyScaler.EnemyHpMultiplier);
    CurrentHp = _maxHp;
}
```

### 5. 솔로 모드 UI 표시

```csharp
// SoloModeHUDPatch.cs
// 솔로 모드에서는 2P 조작 힌트를 숨기거나 "자동" 표시
void Start()
{
    if (CoopSessionManager.CurrentMode == PlayMode.Solo)
    {
        p2HintText.text = "AUTO";
        p2HintText.color = Color.gray;
    }
}
```

### 6. 런 시작 화면 솔로/코업 선택

```csharp
// RunStartScreen.cs
public void OnSoloButtonPressed()
{
    CoopSessionManager.SetMode(PlayMode.Solo);
    // Auto-Onion 활성화 여부 선택 (고급 선택지)
    StartRun();
}

public void OnCoopButtonPressed()
{
    CoopSessionManager.SetMode(PlayMode.Coop);
    StartRun();
}
```

---

## OnionCat 적용 포인트

### 왜 OnionCat에 솔로 모드가 필요한가
1. **혼자 테스트하고 싶을 때**: 개발자 본인이 2명 없이 테스트 가능
2. **플레이어 접근성**: "친구 없이도 즐길 수 있나?" 질문이 반드시 나옴
3. **스팀 출시 시 솔로 플레이 태그**: 없으면 구매 고려에서 제외됨

### 추천 구현 순서

**1단계 (최소 구현, 개발 편의)**:
- `CoopSessionManager`로 솔로 모드 플래그만 추가
- 솔로 모드 시 양파가 자동으로 가장 가까운 적을 향해 기본 탄 발사 (스킬 없음)
- 적 HP 70% 적용

**2단계 (출시 전 완성도)**:
- 런 시작 화면에 솔로/코업 선택 버튼 추가
- 솔로 모드에서 Auto-Onion 행동 약간 개선 (방어막 자동 사용 등)
- HUD에 솔로 모드 표시

**3단계 (옵션)**:
- 혼자서 양파도 직접 조작하는 "원맨 밴드" 모드
- 고난이도 버전 (솔로인데 적 HP 100%)

### Auto-Onion 행동 패턴 아이디어
단순히 가장 가까운 적을 쏘는 것 외에:
- 체력 50% 이하 시 방어막 자동 사용
- 프리즈 탄 보유 시 보스에게 자동 사용
- 화분 R 능력: 가장 많은 적이 모인 위치에 자동 배치

### 주의점
- **솔로 모드가 코업보다 너무 쉬워지면 안 됨**: Auto-Onion은 고양이의 가장 중요한 콤보(야성 게이지, 협동 콤보)를 채워주지 않아야 함
- **세이브 슬롯 분리 고려**: 솔로 런과 코업 런의 메타 진행을 분리할지 공유할지 결정 필요
- **실제 게임 느낌 테스트**: Auto-Onion이 "있으나마나한 보조"가 되지 않도록 튜닝 필요

---

## 참고 링크

- It Takes Two(소파 협동) 솔로 모드 미지원 사례 분석: https://www.ign.com/articles/it-takes-two-review
- Lovers in a Dangerous Spacetime 솔로 모드 구현 사례: https://www.gamedeveloper.com/design/game-design-deep-dive-auto-companion-ai-in-lovers-in-a-dangerous-spacetime
- Unity Input System 멀티 디바이스 감지: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html
- Phogs! 솔로 모드 (1인 2역) 사례: GDC 2021 "Designing a Co-op Game You Can Play Alone"
