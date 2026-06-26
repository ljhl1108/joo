# 패리 & 방어막 시스템 (Parry & Shield System)

리서치 날짜: 2026-06-26

## 개요

패리(Parry)와 방어막(Shield)은 액션 게임의 깊이를 결정짓는 핵심 방어 메카닉이다.  
단순한 피격 회피를 넘어 **공격 → 방어 → 반격**의 리듬을 만들어 전투를 두뇌 게임으로 변환한다.  
OnionCat에서는 Player 2(Crop/Onion)의 **방향성 방어막 + 패리 시스템**이 핵심 정체성이므로, 올바른 구현이 게임 전체 플레이감을 결정한다.

---

## 핵심 개념 정리

### 패리 (Parry)
- **정의**: 적의 공격이 닿는 순간 정확한 타이밍에 방어를 발동해 공격을 무효화(혹은 흡수)하는 것
- **성공 시 보상**: 경직(스턴), 반사 대미지, 무적 프레임, 에너지 획득 등
- **실패 시 패널티**: 일반 피격보다 더 큰 대미지, 경직, 쿨다운 등

### 블록 / 방어막 (Block / Shield)
- **정의**: 일정 방향에서 오는 공격을 지속적으로 감쇄 또는 차단
- **방향성(Directional)**: 특정 방향에서 오는 공격만 차단 (OnionCat의 경우)
- **소모형**: 방어막 HP가 존재해 일정 피격 후 파괴

---

## Unity 구현 방법

### 1. 방어막 방향성 판정

마우스 방향으로 조준하는 Crop의 방어막은 입력 방향과 피격 방향을 비교한다.

```csharp
public class ShieldController : MonoBehaviour
{
    [SerializeField] private float shieldAngle = 120f; // 방어 커버 각도
    [SerializeField] private Transform shieldVisual;
    
    private Vector2 _aimDirection;
    
    void Update()
    {
        // 마우스 방향을 월드 좌표로 변환
        Vector3 mouseWorld = Camera.main.ScreenToWorldPoint(Mouse.current.position.ReadValue());
        _aimDirection = (mouseWorld - transform.position).normalized;
        
        // 방어막 시각 회전
        float angle = Mathf.Atan2(_aimDirection.y, _aimDirection.x) * Mathf.Rad2Deg;
        shieldVisual.rotation = Quaternion.Euler(0, 0, angle);
    }
    
    // 공격이 방어막 방향 안에 있는지 판정
    public bool IsBlocking(Vector2 attackDirection)
    {
        // attackDirection: 공격이 날아오는 방향 (공격자 → 수비자)
        Vector2 incomingDir = -attackDirection.normalized; // 피격 방향 반전
        float angle = Vector2.Angle(_aimDirection, incomingDir);
        return angle <= shieldAngle * 0.5f;
    }
}
```

### 2. 패리 타이밍 윈도우

```csharp
public class ParrySystem : MonoBehaviour
{
    [SerializeField] private float parryWindowSeconds = 0.15f; // 패리 유효 시간
    [SerializeField] private float parryCooldown = 0.8f;
    
    private bool _isParryActive = false;
    private float _parryCooldownTimer = 0f;
    
    void Update()
    {
        if (_parryCooldownTimer > 0f)
            _parryCooldownTimer -= Time.deltaTime;
    }
    
    public void TryActivateParry()
    {
        if (_parryCooldownTimer > 0f) return;
        StartCoroutine(ParryWindow());
    }
    
    private IEnumerator ParryWindow()
    {
        _isParryActive = true;
        yield return new WaitForSeconds(parryWindowSeconds);
        _isParryActive = false;
        _parryCooldownTimer = parryCooldown;
    }
    
    // 피격 처리 시 호출
    public bool TryParry(Vector2 attackDirection, ShieldController shield)
    {
        if (!_isParryActive) return false;
        if (!shield.IsBlocking(attackDirection)) return false;
        
        // 패리 성공!
        OnParrySuccess(attackDirection);
        return true;
    }
    
    private void OnParrySuccess(Vector2 attackDirection)
    {
        // 반사: 투사체를 역방향으로 돌려보내기
        // 스턴: 공격한 적에게 경직
        // 피드백: 히트스톱 + 사운드 + 파티클
        Debug.Log("패리 성공!");
    }
}
```

### 3. 투사체 반사 (Reflect)

패리 성공 시 투사체를 돌려보내는 로직:

```csharp
public class Projectile : MonoBehaviour
{
    [SerializeField] private float speed = 10f;
    private Vector2 _direction;
    private bool _isReflected = false;
    
    public void Initialize(Vector2 direction)
    {
        _direction = direction.normalized;
    }
    
    public void Reflect(Vector2 newDirection)
    {
        _isReflected = true;
        _direction = newDirection.normalized;
        // 대미지 증폭, 피어싱 등 추가 효과 가능
    }
    
    void Update()
    {
        transform.Translate(_direction * speed * Time.deltaTime);
    }
    
    void OnTriggerEnter2D(Collider2D other)
    {
        if (!_isReflected && other.CompareTag("Shield"))
        {
            // ShieldController에 위임
            ShieldController shield = other.GetComponentInParent<ShieldController>();
            ParrySystem parry = other.GetComponentInParent<ParrySystem>();
            
            Vector2 incomingDir = _direction;
            
            if (parry != null && parry.TryParry(incomingDir, shield))
            {
                // 반사 방향: 패리어 방향 기준으로 반전
                Vector2 reflectDir = Vector2.Reflect(_direction, shield.AimDirection);
                Reflect(reflectDir);
                return;
            }
            
            if (shield != null && shield.IsBlocking(incomingDir))
            {
                // 블록 성공 (패리는 실패) → 투사체 흡수
                Destroy(gameObject);
                return;
            }
        }
        
        // 피격 처리
        if (other.CompareTag("Player") || other.CompareTag("Enemy"))
        {
            // 대미지 적용
            Destroy(gameObject);
        }
    }
}
```

### 4. 히트스톱 + 시각 피드백

패리 성공의 "느낌"은 피드백에서 결정된다:

```csharp
public class HitStopManager : MonoBehaviour
{
    private static HitStopManager _instance;
    public static HitStopManager Instance => _instance;
    
    void Awake() => _instance = this;
    
    public void TriggerHitStop(float duration, float timeScale = 0f)
    {
        StartCoroutine(HitStopCoroutine(duration, timeScale));
    }
    
    private IEnumerator HitStopCoroutine(float duration, float timeScale)
    {
        Time.timeScale = timeScale;
        yield return new WaitForSecondsRealtime(duration);
        Time.timeScale = 1f;
    }
}

// 패리 성공 시:
// HitStopManager.Instance.TriggerHitStop(0.1f, 0f); // 0.1초 정지
// CinemachineImpulse로 화면 진동
// 파티클 이펙트 재생 (스파크)
// 사운드 재생 (금속 충돌음)
```

### 5. 완전한 입력 처리 흐름 (New Input System)

```csharp
// PlayerInput Actions에서:
// - ShieldHold: 버튼 홀드 → 방어막 ON
// - ParryPress: 버튼 눌림 → 패리 윈도우 활성화

public class CropInputHandler : MonoBehaviour
{
    [SerializeField] private ShieldController shieldController;
    [SerializeField] private ParrySystem parrySystem;
    
    private PlayerInput _input;
    private InputAction _shieldAction;
    private InputAction _parryAction;
    
    void Awake()
    {
        _input = GetComponent<PlayerInput>();
        _shieldAction = _input.actions["Shield"];
        _parryAction = _input.actions["Parry"];
    }
    
    void OnEnable()
    {
        _shieldAction.performed += OnShieldHeld;
        _shieldAction.canceled += OnShieldReleased;
        _parryAction.performed += OnParryPressed;
    }
    
    void OnDisable()
    {
        _shieldAction.performed -= OnShieldHeld;
        _shieldAction.canceled -= OnShieldReleased;
        _parryAction.performed -= OnParryPressed;
    }
    
    private void OnShieldHeld(InputAction.CallbackContext ctx)
        => shieldController.SetShieldActive(true);
    
    private void OnShieldReleased(InputAction.CallbackContext ctx)
        => shieldController.SetShieldActive(false);
    
    private void OnParryPressed(InputAction.CallbackContext ctx)
        => parrySystem.TryActivateParry();
}
```

---

## OnionCat 적용 포인트

### 방어막 설계 방향
- **Crop(Player 2)**의 방어막은 마우스 방향으로 조준 → 방향성 차단
- 방어 각도: 120~150°로 설정하면 "실력 필요하지만 가능한" 밸런스
- 방어막 ON 상태에서는 Crop의 투사체 발사 불가 (방어 vs 공격 선택 강요)

### 패리 설계 방향
- 패리 윈도우: **0.1~0.2초** — 너무 쉬우면 의미 없고, 너무 어려우면 좌절감
- 패리 성공 보상 계층화:
  1. **투사체 패리**: 해당 투사체를 적에게 반사 (중간 보상)
  2. **근접 패리**: 공격한 적을 잠깐 경직 + 공격 기회 창 열림 (높은 보상)
  3. **특수 패리**: 보스 특수기 패리 → 대미지 보너스 또는 특수 효과 (최고 보상)

### 협동 시너지
- Cat이 적을 유인 → Crop이 패리로 투사체 반사 → Cat이 경직된 적 공격
- 이 루프가 게임의 핵심 협동 패턴이 되도록 설계

### 적 설계와 연동
- 패리 가능한 공격은 시각적으로 **표시** 필요 (예: 노란 투사체 = 반사 가능)
- 패리 불가능한 공격은 다른 색상 (예: 빨간 투사체 = 회피 필요)
- 이 코딩으로 Cat/Crop 역할 명확성 증가

---

## 참고 링크

- Unity 공식 2D Physics Colliders: https://docs.unity3d.com/Manual/Collider2D.html
- New Input System 액션 처리: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/Actions.html
- Celeste의 패리 분석 (GDC): https://www.gdcvault.com/play/1025394
- Hollow Knight 방어막 디자인: https://www.teamcherry.com.au/dev-blog
- "게임 패리 시스템 설계" 참고 유튜브: "How Parry Systems Work in Games" 검색 권장
