# Enemy Charge Attack Pattern (적 돌진 공격 패턴)

리서치 날짜: 2026-08-05

## 개요

적이 플레이어를 향해 **텔레그래프(예고) → 돌진 → 후딜(회복)** 세 단계로 공격하는 패턴. 액션 로그라이크의 핵심 적 디자인으로, 플레이어에게 "보고 반응할 시간"을 주면서도 긴장감을 유지시킴. OnionCat에서는 Cat의 대시(무적)와 Crop의 방향 쉴드가 돌진 공격에 대응하는 핵심 도구가 되어 협력을 자연스럽게 유도함.

---

## Unity 구현 방법

### 전체 상태 구조

```
Idle → Chase → [Telegraph] → [Charge] → [Recovery] → Idle
```

Enemy_AI_StateMachine.md의 상태머신 구조 위에 3개 서브 상태 추가.

---

### Step 1: 텔레그래프 (Telegraph) 상태

```csharp
public class ChargeEnemy : MonoBehaviour
{
    [SerializeField] private float telegraphDuration = 1.0f;
    [SerializeField] private float chargeDuration = 0.35f;
    [SerializeField] private float recoveryDuration = 0.6f;
    [SerializeField] private float chargeSpeed = 18f;
    [SerializeField] private LayerMask wallLayer;

    private Vector2 chargeDirection;
    private Rigidbody2D rb;
    private SpriteRenderer spriteRenderer;

    private void StartTelegraph()
    {
        currentState = EnemyState.Telegraph;
        // 공격 방향을 이 시점에서 확정 (이후 플레이어가 이동해도 방향 고정)
        chargeDirection = ((Vector2)player.position - (Vector2)transform.position).normalized;
        StartCoroutine(TelegraphCoroutine());
    }

    private IEnumerator TelegraphCoroutine()
    {
        float elapsed = 0f;
        while (elapsed < telegraphDuration)
        {
            // 스프라이트 빠른 점멸 (위험 신호)
            float flashSpeed = Mathf.Lerp(4f, 12f, elapsed / telegraphDuration);
            spriteRenderer.color = Mathf.Sin(elapsed * flashSpeed * Mathf.PI) > 0f
                ? Color.red : Color.white;
            elapsed += Time.deltaTime;
            yield return null;
        }
        spriteRenderer.color = Color.white;
        StartCharge();
    }
```

**텔레그래프 시각 연출 추가 옵션:**
```csharp
// LineRenderer로 돌진 예정 경로 미리 표시
private LineRenderer chargePreviewLine;

private void ShowChargeLine()
{
    chargePreviewLine.enabled = true;
    chargePreviewLine.SetPosition(0, transform.position);
    // 벽 감지해서 충돌 지점까지 미리보기
    RaycastHit2D hit = Physics2D.Raycast(transform.position, chargeDirection, 20f, wallLayer);
    Vector3 endPoint = hit.collider != null ? hit.point : (Vector2)transform.position + chargeDirection * 20f;
    chargePreviewLine.SetPosition(1, endPoint);
}
```

---

### Step 2: 돌진 (Charge) 상태

```csharp
    private void StartCharge()
    {
        currentState = EnemyState.Charge;
        rb.linearVelocity = chargeDirection * chargeSpeed;
        StartCoroutine(ChargeCoroutine());
    }

    private IEnumerator ChargeCoroutine()
    {
        float elapsed = 0f;
        while (elapsed < chargeDuration)
        {
            // 돌진 중 벽 충돌 감지
            RaycastHit2D hit = Physics2D.Raycast(transform.position,
                rb.linearVelocity.normalized, 0.5f, wallLayer);
            if (hit.collider != null)
            {
                OnWallHit();
                yield break;
            }
            elapsed += Time.deltaTime;
            yield return null;
        }
        StartRecovery();
    }

    private void OnWallHit()
    {
        rb.linearVelocity = Vector2.zero;
        // 벽 충돌 이펙트 (파티클, 사운드)
        Instantiate(wallHitVFX, transform.position, Quaternion.identity);
        // 더 긴 경직 (벽에 박은 경우 패널티)
        StartCoroutine(RecoveryCoroutine(recoveryDuration * 1.5f));
    }
```

---

### Step 3: 후딜 (Recovery) 상태 — 플레이어 반격 창

```csharp
    private void StartRecovery()
    {
        rb.linearVelocity = Vector2.zero;
        currentState = EnemyState.Recovery;
        StartCoroutine(RecoveryCoroutine(recoveryDuration));
    }

    private IEnumerator RecoveryCoroutine(float duration)
    {
        // 시각적으로 경직 상태 표시 (스프라이트 색상 변환)
        spriteRenderer.color = new Color(0.5f, 0.5f, 1f); // 파란색 = 경직
        yield return new WaitForSeconds(duration);
        spriteRenderer.color = Color.white;
        currentState = EnemyState.Chase;
    }
```

---

### 데미지 충돌 처리

```csharp
// 돌진 중에만 데미지 히트박스 활성화
private Collider2D chargeHitbox;

private void SetChargeHitboxActive(bool active)
{
    chargeHitbox.enabled = active;
}

// ChargeCoroutine 시작 시 SetChargeHitboxActive(true)
// ChargeCoroutine 종료 또는 벽 충돌 시 SetChargeHitboxActive(false)
```

---

### 패리 연동 (Crop 쉴드)

```csharp
// 돌진 중 Crop의 방향 쉴드에 닿으면 리바운드
private void OnTriggerEnter2D(Collider2D other)
{
    if (currentState != EnemyState.Charge) return;

    if (other.CompareTag("CropShield"))
    {
        // 반대 방향으로 튕김 → 더 긴 경직
        rb.linearVelocity = -chargeDirection * (chargeSpeed * 0.5f);
        StartCoroutine(RecoveryCoroutine(recoveryDuration * 2f));
        // 패리 피드백 (CinemachineImpulse, SFX)
        FindObjectOfType<CameraShaker>().Shake(0.3f, 0.2f);
    }
}
```

---

## OnionCat 적용 포인트

### Cat의 대시 무적 활용 유도
텔레그래프 구간(1.0초)이 Cat 대시 타이밍과 정확히 맞물리도록 설계:
- 텔레그래프 1초 → 플레이어가 대시 준비 가능
- 돌진 0.35초 → Cat 대시(무적 프레임) 사용 시 피해 없음
- 후딜 0.6초 → Cat이 뒤에서 슬래시 반격

### Crop 방향 쉴드 + 패리 유도
돌진 방향이 예측 가능(텔레그래프 라인)하므로, Crop 플레이어가 쉴드를 돌진 방향에 맞추면 패리 성공 → 경직 2배. 두 플레이어 간 "대시로 피해? 쉴드로 패리해?" 즉흥 소통 발생.

### 돌진 적 위험도 분류
- **기본형**: 직선 돌진, 1회
- **반사형**: 벽에 닿으면 반사 후 재돌진 (최대 2회)
- **광역형**: 돌진 경로에 파동 이펙트 범위 데미지
- 3종 모두 Enemy ScriptableObject에 `ChargeType` enum으로 구분

### 구현 순서 (초보자용)
1. Enemy_AI_StateMachine.md의 Chase 상태 구현 확인
2. Telegraph 코루틴 + 스프라이트 점멸 추가
3. Rigidbody2D velocity 기반 Charge 이동 구현
4. Recovery 상태 + 경직 색상 표시
5. 벽 충돌 레이캐스트 추가
6. Crop 쉴드 패리 연동 (마지막에)

---

## 참고 링크

- Unity Coroutine 공식 문서: https://docs.unity3d.com/Manual/Coroutines.html
- Physics2D.Raycast: https://docs.unity3d.com/ScriptReference/Physics2D.Raycast.html
- 히트스톱 구현 참고: https://www.gamedeveloper.com/design/the-art-of-screen-shake
- Enemy Design 원칙 (GDC): https://www.gdcvault.com/play/1023302
- Vlambeer Nuclear Throne 전투 피드백: https://www.youtube.com/watch?v=AJdEqssNZ-U
