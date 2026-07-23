# 트랩 & 위험 요소 시스템 (Trap & Environmental Hazard System)

리서치 날짜: 2026-07-23

## 개요

던전 방 안에 배치되는 환경적 위험 요소(함정, 장해물, 위험 지형)를 구현하는 시스템. 로그라이크 게임에서 트랩은 단순히 데미지를 주는 것 이상으로, **방의 전투 공간을 제한하고 긴박감을 높이며 코옵 협력 상황을 만드는 핵심 디자인 도구**다. OnionCat처럼 근접+원거리 역할이 분리된 게임에서 트랩은 역할 활용을 강제하는 중요한 장치가 된다.

---

## Unity 구현 방법

### 1. 기본 데미지 트랩 (Damage Trigger)

```csharp
// TrapBase.cs - 모든 트랩의 기반 클래스
public abstract class TrapBase : MonoBehaviour
{
    [SerializeField] private float damage = 10f;
    [SerializeField] private float cooldown = 0.5f;    // 같은 대상에 재적용 대기 시간
    [SerializeField] private LayerMask playerLayer;

    private Dictionary<Collider2D, float> lastHitTime = new();

    protected virtual void OnTriggerEnter2D(Collider2D other)
    {
        if (!IsInLayerMask(other.gameObject, playerLayer)) return;
        ApplyDamage(other);
    }

    protected virtual void OnTriggerStay2D(Collider2D other)
    {
        if (!IsInLayerMask(other.gameObject, playerLayer)) return;
        if (!lastHitTime.TryGetValue(other, out float last) || Time.time - last >= cooldown)
        {
            lastHitTime[other] = Time.time;
            ApplyDamage(other);
        }
    }

    private void ApplyDamage(Collider2D target)
    {
        if (target.TryGetComponent<IDamageable>(out var damageable))
            damageable.TakeDamage(damage, DamageType.Environmental);
    }

    private bool IsInLayerMask(GameObject obj, LayerMask mask)
        => (mask.value & (1 << obj.layer)) != 0;
}
```

### 2. 스파이크 트랩 (Spike Trap) — 주기적 ON/OFF

```csharp
// SpikeTrap.cs
public class SpikeTrap : TrapBase
{
    [SerializeField] private float retractTime = 1.5f;   // 스파이크 내려가 있는 시간
    [SerializeField] private float extendTime = 1.0f;    // 스파이크 올라와 있는 시간
    [SerializeField] private float warningTime = 0.3f;   // 올라오기 전 경고 시간

    private Collider2D col;
    private SpriteRenderer sr;
    private static readonly Color warningColor = new Color(1f, 0.5f, 0f, 1f);

    void Awake()
    {
        col = GetComponent<Collider2D>();
        sr = GetComponent<SpriteRenderer>();
    }

    void Start() => StartCoroutine(SpikeCycle());

    IEnumerator SpikeCycle()
    {
        while (true)
        {
            // 안전 구간
            col.enabled = false;
            sr.color = Color.white;
            yield return new WaitForSeconds(retractTime - warningTime);

            // 경고 구간 (색 변경)
            sr.color = warningColor;
            yield return new WaitForSeconds(warningTime);

            // 위험 구간
            col.enabled = true;
            // 스파이크 애니메이션 트리거
            yield return new WaitForSeconds(extendTime);
        }
    }
}
```

### 3. 이동 크러셔 (Moving Crusher / Crusher Wall)

```csharp
// CrusherTrap.cs — 왕복 이동하며 플레이어를 밀어내는 오브젝트
public class CrusherTrap : TrapBase
{
    [SerializeField] private Vector2 moveDirection = Vector2.right;
    [SerializeField] private float moveDistance = 3f;
    [SerializeField] private float speed = 2f;

    private Vector2 startPos;
    private Vector2 endPos;

    void Start()
    {
        startPos = transform.position;
        endPos = startPos + moveDirection.normalized * moveDistance;
        StartCoroutine(CrusherMove());
    }

    IEnumerator CrusherMove()
    {
        while (true)
        {
            yield return MoveTo(endPos);
            yield return new WaitForSeconds(0.5f);
            yield return MoveTo(startPos);
            yield return new WaitForSeconds(0.5f);
        }
    }

    IEnumerator MoveTo(Vector2 target)
    {
        while (Vector2.Distance(transform.position, target) > 0.05f)
        {
            transform.position = Vector2.MoveTowards(transform.position, target, speed * Time.deltaTime);
            yield return null;
        }
        transform.position = target;
    }

    // OnTriggerStay2D는 TrapBase에서 처리됨
    // 크러셔는 추가로 플레이어를 밀어내는 힘도 적용 가능
    protected override void OnTriggerEnter2D(Collider2D other)
    {
        base.OnTriggerEnter2D(other);
        if (other.TryGetComponent<Rigidbody2D>(out var rb))
        {
            Vector2 knockback = moveDirection.normalized * 10f;
            rb.AddForce(knockback, ForceMode2D.Impulse);
        }
    }
}
```

### 4. 낙하 구덩이 (Pit / Void)

```csharp
// PitTrap.cs — 즉사 또는 큰 데미지 + 방 시작 지점으로 리스폰
public class PitTrap : MonoBehaviour
{
    [SerializeField] private float fallDamage = 9999f;   // 즉사용 큰 값, 또는 HP 비례로 조정
    [SerializeField] private Transform respawnPoint;      // [SerializeField] — 유니티 에디터에서 드래그 앤 드롭 설정 필요

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.TryGetComponent<PlayerController>(out var player))
        {
            if (other.TryGetComponent<IDamageable>(out var damageable))
                damageable.TakeDamage(fallDamage, DamageType.InstantKill);

            // 리스폰 처리 (코루틴으로 딜레이)
            StartCoroutine(RespawnAfterDelay(player, 1.0f));
        }
    }

    IEnumerator RespawnAfterDelay(PlayerController player, float delay)
    {
        // 사망 이펙트 재생 대기
        yield return new WaitForSeconds(delay);
        if (respawnPoint != null)
            player.transform.position = respawnPoint.position;
    }
}
```

### 5. 화염/독 지형 (Area Effect Hazard)

```csharp
// AreaHazard.cs — 지속 데미지 및 상태이상 지형
public class AreaHazard : TrapBase
{
    [SerializeField] private StatusEffectType statusEffect;  // Burning, Poisoned 등
    [SerializeField] private ParticleSystem hazardParticles; // [SerializeField] — 에디터 설정 필요

    protected override void OnTriggerEnter2D(Collider2D other)
    {
        base.OnTriggerEnter2D(other);   // 즉시 데미지
        // 상태이상 적용
        if (other.TryGetComponent<StatusEffectReceiver>(out var receiver))
            receiver.Apply(statusEffect);
    }
}
```

### 6. 트랩 경고 시각화 패턴

```csharp
// TrapWarningVisual.cs — 트랩 발동 전 바닥에 경고 표시
public class TrapWarningVisual : MonoBehaviour
{
    [SerializeField] private GameObject warningIndicator;    // 반투명 빨간 영역 프리팹
    [SerializeField] private float warningDuration = 0.5f;

    public IEnumerator ShowWarning()
    {
        warningIndicator.SetActive(true);
        // 깜빡임 효과
        var sr = warningIndicator.GetComponent<SpriteRenderer>();
        float timer = 0;
        while (timer < warningDuration)
        {
            sr.color = new Color(1, 0, 0, Mathf.PingPong(timer * 6, 1) * 0.5f + 0.2f);
            timer += Time.deltaTime;
            yield return null;
        }
        warningIndicator.SetActive(false);
    }
}
```

### 7. 레이어 설정

```
Layer Matrix 권장 설정:
- Traps 레이어: 플레이어(Player)와만 충돌 설정
- Enemy는 트랩에 영향받지 않도록 (Player 전용 위험 요소)
- Physics2D Settings → Layer Collision Matrix에서 Traps-Enemy 충돌 해제
```

---

## OnionCat 적용 포인트

### 코옵 역할 강제 트랩 설계

OnionCat의 특수성(Cat=근접, Crop=원거리)을 활용한 트랩 기획:

| 트랩 유형 | 역할 강제 방식 |
|-----------|----------------|
| **실드 벽 트랩** | 특정 색상 방어막만 관통 가능 (Crop 원거리 투사체만 파괴) |
| **근접 감지 지뢰** | Cat이 일정 거리 이내 접근하면 폭발 → Crop이 원거리로 먼저 처리 |
| **레이저 통로** | 좁은 통로에 레이저 배치 → 타이밍에 맞춰 대시(Cat)로만 통과 가능 |
| **독 구름** | Crop 실드로만 차단 가능, Cat은 독 구름 속에서 지속 데미지 |

### 코옵 함정 디자인 패턴

```
기본 원칙: "한 명이 처리 중일 때 다른 한 명이 위험에 빠지는" 상황 만들기

예시:
1. Cat이 스파이크 트랩을 피해 적에게 접근하는 동안
   Crop이 등 뒤 원거리 적을 처리해야 하는 동시 압박 상황
2. Crop이 집중 조준 중(이동 불가)일 때
   Cat이 크러셔 트랩을 막아서 Crop 보호
3. 낙하 구덩이 앞에서 Cat이 점프할 타이밍에
   Crop이 실드로 날아오는 투사체 막아주기
```

### 트랩 밸런싱 기준

```
픽셀아트 로그라이크 기준:
- 경고 시간: 최소 0.3~0.5초 (공정성 확보)
- 데미지: 전체 HP의 20~30% (즉사 지양, 위험감 유지)
- 쿨다운: 0.5초 (같은 프레임에 중복 적용 방지)
- 트랩 밀도: 방당 1~3개 (4개 이상은 전투 공간 과도 제한)
```

---

## 참고 링크

- Unity 공식 문서 Collider2D: https://docs.unity3d.com/Manual/Collider2D.html
- OnTriggerEnter2D 활용법: https://docs.unity3d.com/ScriptReference/MonoBehaviour.OnTriggerEnter2D.html
- Coroutine 기반 트랩 구현: https://docs.unity3d.com/Manual/Coroutines.html
- 참고 GDC 강연: "Level Design in a Day: Traps as Design Tools" (YouTube GDC 채널)
- Enter the Gungeon 트랩 디자인 분석: https://www.gamedeveloper.com/design/how-enter-the-gungeon-builds-tension
