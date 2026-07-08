# Dash / I-Frame System (무적 대시)

리서치 날짜: 2026-07-08

## 개요

대시(Dash)는 캐릭터가 빠르게 짧은 거리를 이동하는 이동 기술이며, I-Frame(Invincibility Frame)은 대시 중 모든 피해를 무효화하는 무적 프레임이다. OnionCat에서 Cat의 핵심 능력으로 "무적 대시"가 설계되어 있기 때문에, 이 두 시스템을 올바르게 구현하는 것이 전투 게임플레이의 핵심 기반이 된다.

**왜 중요한가**: I-Frame 없는 대시는 그냥 이동이다. I-Frame이 붙는 순간 대시는 "리스크 회피 기술"이 되어 전투 깊이가 생긴다. Hades, Dead Cells, Enter the Gungeon 모두 이 원리를 사용한다.

---

## Unity 구현 방법

### 방법 1: Physics2D Layer 전환 (권장 — OnionCat 적합)

대시 중 캐릭터 레이어를 "적 공격이 닿지 않는 레이어"로 임시 전환한다.

```csharp
public class CatDash : MonoBehaviour
{
    [SerializeField] private float dashSpeed = 20f;
    [SerializeField] private float dashDuration = 0.15f;
    [SerializeField] private float dashCooldown = 0.8f;

    private Rigidbody2D rb;
    private bool isDashing;
    private float cooldownTimer;
    
    // 레이어 인덱스 (Inspector에서 설정)
    [SerializeField] private int normalLayer;      // "Player" 레이어
    [SerializeField] private int iFrameLayer;      // "PlayerIFrame" 레이어

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void Update()
    {
        cooldownTimer -= Time.deltaTime;
        
        // 대시 입력 — New Input System에서 호출되는 메서드
        // InputAction.performed 콜백에서 TryDash() 호출
    }

    public void TryDash(Vector2 moveDir)
    {
        if (isDashing || cooldownTimer > 0f) return;
        
        // 이동 방향이 없으면 현재 facing 방향으로 대시
        Vector2 dashDir = moveDir.sqrMagnitude > 0.01f 
            ? moveDir.normalized 
            : transform.right;
        
        StartCoroutine(DashCoroutine(dashDir));
    }

    private IEnumerator DashCoroutine(Vector2 dir)
    {
        isDashing = true;
        cooldownTimer = dashCooldown;
        
        // I-Frame 활성화 — 레이어 전환
        gameObject.layer = iFrameLayer;
        
        // 대시 이동
        rb.linearVelocity = dir * dashSpeed;
        
        // 대시 지속 시간 대기
        yield return new WaitForSeconds(dashDuration);
        
        // 속도 리셋 및 레이어 복원
        rb.linearVelocity = Vector2.zero;
        gameObject.layer = normalLayer;
        isDashing = false;
    }
}
```

**Physics2D 레이어 충돌 매트릭스 설정**:
- Edit → Project Settings → Physics 2D → Layer Collision Matrix
- `PlayerIFrame` 레이어와 `EnemyProjectile`, `EnemyHitbox` 레이어의 충돌 체크를 **해제**
- `PlayerIFrame`은 `Wall`, `Ground`와는 여전히 충돌 (벽 통과 안 됨)

### 방법 2: bool 플래그 + 데미지 시스템 통합 (단순 대안)

레이어 전환 없이 데미지 수신 함수에서 플래그를 체크하는 방식.

```csharp
public class PlayerHealth : MonoBehaviour
{
    public bool IsInvincible { get; set; }
    
    public void TakeDamage(int amount)
    {
        if (IsInvincible) return;  // I-Frame 중 무시
        // ... 데미지 처리
    }
}
```

대시 코루틴에서 `playerHealth.IsInvincible = true/false`로 제어. 단순하지만 콜라이더가 여전히 반응하므로 물리 밀침 등의 부작용 처리 필요.

### 방법 3: 애니메이션 이벤트 기반 I-Frame

Animator에 `DashStart` / `DashEnd` 이벤트를 심고 이벤트 콜백에서 I-Frame을 제어한다. 애니메이션 타이밍과 정확히 동기화된다는 장점이 있으나, 애니메이션이 준비된 후에만 적용 가능하다.

---

## 시각 피드백 (필수)

대시 중 무적임을 플레이어가 인지해야 한다. 방법:

```csharp
private IEnumerator DashCoroutine(Vector2 dir)
{
    isDashing = true;
    gameObject.layer = iFrameLayer;
    
    // 스프라이트 깜빡임 효과 (반투명)
    var spriteRenderer = GetComponent<SpriteRenderer>();
    spriteRenderer.color = new Color(1f, 1f, 1f, 0.5f);
    
    // (선택) 잔상 이펙트: AfterImage 스크립트 활성화
    // afterImageEffect.enabled = true;
    
    rb.linearVelocity = dir * dashSpeed;
    yield return new WaitForSeconds(dashDuration);
    
    rb.linearVelocity = Vector2.zero;
    spriteRenderer.color = Color.white;
    gameObject.layer = normalLayer;
    isDashing = false;
    
    // 쿨다운 UI 업데이트
    // dashCooldownUI.StartCooldown(dashCooldown);
}
```

**잔상(After Image) 구현** — 대시 경로를 따라 반투명 스프라이트를 남기는 이펙트:
```csharp
// 별도 AfterImage 스크립트: 대시 중 일정 간격으로 현재 스프라이트 복사본 생성
// 복사본은 0.1~0.2초에 걸쳐 알파값 0으로 Lerp
```

---

## 쿨다운 UI

대시 쿨다운을 플레이어에게 표시하는 방법 (원형 쿨다운 이미지):

```csharp
// Image 컴포넌트의 fillAmount를 0→1로 채워서 쿨다운 표현
// Image.type = Filled, FillMethod = Radial360
dashCooldownImage.fillAmount = 1f - (cooldownTimer / dashCooldown);
```

---

## OnionCat 적용 포인트

### 핵심 설계 결정

| 항목 | 권장 선택 | 이유 |
|---|---|---|
| I-Frame 구현 방식 | **레이어 전환 방식** | 콜라이더 자체를 비활성화하므로 물리 밀침 등 부작용 없음 |
| 대시 방향 | **8방향 (입력 방향 기반)** | New Input System Vector2 입력값 사용 |
| 대시 거리 | 속도 × 지속시간 조합 | dashSpeed(20) + dashDuration(0.15s) → 약 3타일 이동 |
| 쿨다운 | 0.7~1.0초 | 연속 대시 방지, 리스크-리워드 판단 필요 |

### OnionCat 특수 고려사항

1. **Cat + Onion이 한 몸** → Cat이 대시하면 Onion도 함께 이동. Onion의 조준(마우스 방향)은 대시 중에도 유지되어야 함.
2. **대시 중 Onion 투사체 발사 가능 여부** → 발사 허용 시 대시 중 안전하게 원거리 딜 가능 (강력하지만 기술적 난이도 상승). 초기에는 발사 불가로 단순화 권장.
3. **적 약점 시스템 연동** → 일부 적은 Cat의 대시 자체를 약점으로 설정 가능 (대시로 적 통과 시 데미지 판정 추가).

### 레이어 구성 권장

```
Player          → 기본 플레이어 레이어 (EnemyProjectile과 충돌 O)
PlayerIFrame    → 대시 중 레이어 (EnemyProjectile과 충돌 X)
EnemyProjectile → 적 투사체
EnemyHitbox     → 적 근접 공격 판정
Wall            → 벽 (모든 플레이어 레이어와 충돌)
```

**[SerializeField] 변수 설정 필요**: `normalLayer`와 `iFrameLayer`에 위 레이어 인덱스를 유니티 에디터에서 드래그 앤 드롭 또는 숫자로 설정 필요.

---

## 참고 링크

- Unity 공식 - Physics2D.IgnoreLayerCollision: https://docs.unity3d.com/ScriptReference/Physics2D.IgnoreLayerCollision.html
- Unity 공식 - Layer Collision Matrix: https://docs.unity3d.com/Manual/LayerBasedCollision.html
- Brackeys "2D Movement in Unity" (대시 구현 포함): https://youtu.be/dwcT-Dch0bA
- Game Dev Beginner - "How to make a Dash in Unity 2D": https://gamedevbeginner.com/how-to-make-a-dash-in-unity/
- 잔상 이펙트 튜토리얼: https://youtu.be/mRHjUYeJxVg
