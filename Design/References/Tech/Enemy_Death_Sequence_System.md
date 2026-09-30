# Enemy Death Sequence System (적 사망 연출 시스템)

리서치 날짜: 2026-09-30

## 개요

적이 HP 0에 도달한 순간부터 오브젝트가 풀로 반환되기까지의 전체 시퀀스.
단순히 "Destroy()" 하나가 아니라 히트스톱 → VFX → 점수/숫자 팝업 → 아이템 드롭 → 풀 반환이 연달아 일어나는 파이프라인이다.

OnionCat에서는 Instantiate/Destroy 대신 `PoolManager.Spawn/Despawn`을 쓰므로,
"오브젝트를 없애는 것"이 아니라 "풀로 돌려보내기 전에 연출을 끝내는 것"이 목표다.

## Unity 구현 방법

### 1. 사망 트리거 (EnemyHealth.cs)

```csharp
public void TakeDamage(float amount)
{
    currentHP -= amount;
    if (currentHP <= 0 && !isDying)
        StartCoroutine(DeathSequence());
}

private bool isDying;

private IEnumerator DeathSequence()
{
    isDying = true;
    // 콜라이더 끄기 — 죽는 중에 추가 피격 방지
    GetComponent<Collider2D>().enabled = false;

    // ① 히트스톱 (선택)
    Time.timeScale = 0f;
    yield return new WaitForSecondsRealtime(0.05f);
    Time.timeScale = 1f;

    // ② 사망 애니메이션 트리거
    animator.SetTrigger("Death");
    yield return new WaitForSeconds(deathAnimDuration); // 보통 0.3~0.5초

    // ③ VFX 스폰 (풀 사용)
    PoolManager.Spawn(deathVFXPrefab, transform.position, Quaternion.identity);

    // ④ 점수/킬 이벤트
    GameManager.Instance.Run.AddKill();
    FloatingTextManager.Spawn(transform.position, scoreText);

    // ⑤ 아이템 드롭
    itemDropper?.Drop(transform.position);

    // ⑥ 적 오브젝트를 풀로 반환
    PoolManager.Despawn(gameObject);
}
```

### 2. 사망 VFX — Particle System 풀 연동

VFX 프리팹은 ParticleSystem + 자동 반환 스크립트를 세트로 구성:

```csharp
// AutoDespawnParticle.cs — VFX 프리팹에 붙임
public class AutoDespawnParticle : MonoBehaviour
{
    private ParticleSystem ps;

    void Awake() => ps = GetComponent<ParticleSystem>();

    void OnEnable() => StartCoroutine(WaitAndDespawn());

    private IEnumerator WaitAndDespawn()
    {
        yield return new WaitWhile(() => ps.IsAlive(true));
        PoolManager.Despawn(gameObject);
    }
}
```

핵심: `ps.IsAlive(true)` — 자식 파티클까지 포함해 모두 끝날 때까지 기다림.

### 3. 사망 애니메이션 길이 읽기

애니메이션 클립 길이를 하드코딩하지 않고 Animator로 읽는 법:

```csharp
float deathAnimDuration = 0f;

void Awake()
{
    foreach (var clip in animator.runtimeAnimatorController.animationClips)
    {
        if (clip.name.Contains("Death"))
        {
            deathAnimDuration = clip.length;
            break;
        }
    }
}
```

### 4. 상태머신 연동 패턴

DeathState를 따로 만드는 경우:

```csharp
// EnemyStateMachine이 있는 구조
public class DeathState : IEnemyState
{
    public void Enter(EnemyController enemy)
    {
        enemy.StartCoroutine(enemy.PlayDeathSequence());
    }

    public void Update(EnemyController enemy) { }  // 죽는 중 갱신 없음

    public void Exit(EnemyController enemy) { }
}
```

### 5. ScriptableObject로 사망 연출 설정값 분리

```csharp
[CreateAssetMenu(menuName = "OnionCat/EnemyDeathConfig")]
public class EnemyDeathConfig : ScriptableObject
{
    public GameObject deathVFXPrefab;
    public float hitstopDuration = 0.05f;
    public float deathAnimDuration = 0.4f;
    public float[] dropWeights;          // 아이템 드롭 확률
    public int scoreValue;
}
```

적 프리팹마다 다른 Config를 연결하면 슬라임 / 보스 / 날벌레 사망 연출을 개별 조정 가능.

### 6. OnEnable 초기화 주의사항 (풀 사용 시)

풀에서 Spawn될 때마다 `OnEnable`이 호출됨 → 반드시 초기화:

```csharp
void OnEnable()
{
    isDying = false;
    currentHP = maxHP;
    GetComponent<Collider2D>().enabled = true;
    animator.Rebind();
    animator.Update(0f);
}
```

## OnionCat 적용 포인트

### 적 타입별 사망 연출 차별화
- **슬라임** (근접 약점): 터지면서 초록 점액 파티클 → `Slime_DeathVFX`
- **날벌레** (원거리 약점): 추락하며 날개 깃털 파티클 → `Fly_DeathVFX`
- **방패 기사** (근접 필수): 방패 부서지는 스프라이트 교체 후 소멸

각 타입은 `EnemyDeathConfig` ScriptableObject 하나씩 가짐.

### 히트스톱 타이밍
- 일반 잡몹: 0.03~0.05초 (빠른 타격감)
- 엘리트 적: 0.08~0.10초 (묵직한 처치감)
- 보스: 0.15초 + 카메라 흔들림 (`CinemachineImpulse`)
→ `HitFeelSettings.asset`에서 조절 (기존 HitFeelSettings 연동)

### 풀 반환 순서
```
HP 0 감지
  → isDying = true (중복 실행 방지)
  → Collider 비활성화 (유령 상태)
  → 히트스톱 (Time.timeScale = 0)
  → 사망 애니메이션 재생
  → VFX 풀 스폰
  → 킬 카운트 / 점수 이벤트 발행
  → 아이템 드롭
  → PoolManager.Despawn(gameObject)
```

### 협동 플레이 킬 인정
고양이와 양파가 동시에 딜을 넣다가 죽을 경우 "라스트 힛" 판정 없이 팀 킬로 처리:

```csharp
GameManager.Instance.Run.AddKill();  // RunData에 합산
```

`AddKill()` 내부에서 GameManager가 어떤 플레이어가 마지막 공격을 했는지 기록 가능 (통계용).

## 참고 링크
- [Unity Docs - Object Pooling](https://docs.unity3d.com/Manual/performance-optimizing-code-managed-memory.html)
- [Unity Docs - ParticleSystem.IsAlive](https://docs.unity3d.com/ScriptReference/ParticleSystem.IsAlive.html)
- [Unity Object Pool API](https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html)
- [Game Dev TV - Death FX Discussion](https://community.gamedev.tv/t/enemies-wont-activate-deathfx/187293)
- [Codefinity - Particle System for Enemy Explosion](https://codefinity.com/courses/v2/f1cc5b74-bc21-4ef5-856a-70580181cb35/ebca18d9-a3eb-4eca-a2b6-5e03cb4f7c66/a842472f-4ce0-48d4-ab95-4ef4dd3b69f6)
