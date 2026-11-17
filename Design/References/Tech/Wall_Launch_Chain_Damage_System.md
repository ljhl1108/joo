# Wall Launch & Environmental Chain Damage System

리서치 날짜: 2026-11-17

## 개요

적을 강한 공격으로 날려 보낸 뒤, 적이 벽·다른 적·구덩이에 충돌할 때 추가 피해나 특수 효과를 발생시키는 시스템. OnionCat에서는 `EnemyBase.Launch()` → `EffectTrigger.WallCrash`로 구현되어 있으며, 걷어차기가 삭제된 현재는 **강타(heavy hit)·특수 공격·특정 장비 효과**가 적을 날려 보낼 수 있는 유일한 수단이다. 이 시스템이 잘 동작하면 "날려서 처치" 플레이가 카타르시스를 주고 협동 콤보의 목표 행동이 된다.

---

## 핵심 개념

### 발사(Launch)와 충돌(Crash) 분리
- **Launch**: 적에게 초기 속도를 주는 단계. 발사 방향, 속도, 지속 시간을 결정
- **Crash**: 날아가던 적이 충분한 속도로 고정 물체에 부딪히는 단계. 피해·기절·이펙트 발동

### 충돌 대상
1. **Wall** (레이어 8): 벽에 부딪힘 → `WallCrash` 이펙트 발동, 추가 피해
2. **Enemy** (레이어 12): 다른 적에 부딪힘 → 양쪽에 충격 피해, 연쇄 넉백 가능
3. **Pit** (Props 레이어): 구덩이에 떨어짐 → 보스가 아니면 즉사 (`immuneToPits` 예외)
4. **Props** (레이어 14): 소품에 충돌 → 소품 파괴 이펙트 (선택 사항)

### 최소 속도 임계값
모든 충돌이 `Crash`를 발동시키면 너무 많은 이펙트가 생긴다. **최소 속도 임계값(minCrashSpeed)**을 넘어야만 `Crash` 판정 → 약하게 밀린 경우엔 발동 안 함.

---

## Unity 구현 방법

### 1. EnemyBase에 Launch 추가

```csharp
public class EnemyBase : MonoBehaviour {
    [SerializeField] private float minCrashSpeed = 4f;
    private bool _isLaunched;
    private Rigidbody2D _rb;

    public void Launch(Vector2 direction, float speed, float duration = 0.5f) {
        _isLaunched = true;
        _rb.linearVelocity = direction.normalized * speed;
        StartCoroutine(EndLaunchAfter(duration));
    }

    private IEnumerator EndLaunchAfter(float t) {
        yield return new WaitForSeconds(t);
        _isLaunched = false;
        _rb.linearVelocity = Vector2.zero;
    }

    private void OnCollisionEnter2D(Collision2D col) {
        if (!_isLaunched) return;
        float impactSpeed = col.relativeVelocity.magnitude;
        if (impactSpeed < minCrashSpeed) return;

        int layer = col.gameObject.layer;
        if (layer == LayerMask.NameToLayer("Wall") || col.gameObject.CompareTag("Wall")) {
            TriggerWallCrash(col.contacts[0].point, impactSpeed);
        } else if (layer == LayerMask.NameToLayer("Enemy")) {
            TriggerEnemyCrash(col.gameObject, impactSpeed);
        }
    }
}
```

### 2. WallCrash 이펙트

```csharp
private void TriggerWallCrash(Vector2 point, float speed) {
    float bonus = Mathf.Lerp(0f, 20f, (speed - minCrashSpeed) / 10f);
    TakeDamage(bonus, Attacker.Cat);  // 발사한 플레이어가 Cat이라는 가정

    // 파티클·사운드·히트스톱
    FeedbackManager.WallCrash(point);
    Sfx.Play(SfxId.WallCrash);
    HitstopManager.Apply(0.08f, 0.3f);

    // 주변 적에게도 충격파 (선택 사항)
    Collider2D[] nearby = Physics2D.OverlapCircleAll(point, 1.5f, enemyMask);
    foreach (var c in nearby) {
        if (c.gameObject != gameObject)
            c.GetComponent<EnemyBase>()?.TakeDamage(bonus * 0.5f, Attacker.Cat);
    }

    _isLaunched = false;
}
```

### 3. Enemy-to-Enemy 충돌 처리

```csharp
private void TriggerEnemyCrash(GameObject other, float speed) {
    float dmg = speed * 1.5f;
    // 맞은 적
    other.GetComponent<EnemyBase>()?.TakeDamage(dmg, Attacker.Cat);
    other.GetComponent<EnemyBase>()?.ApplyStun(0.5f);
    // 날아간 적 자신도 충격
    TakeDamage(dmg * 0.5f, Attacker.Cat);
    _isLaunched = false;
}
```

### 4. Pit 처리 (기존 Pit 컴포넌트 연동)

```csharp
// Pit.cs (기존 코드에 추가)
private void OnTriggerEnter2D(Collider2D col) {
    var enemy = col.GetComponent<EnemyBase>();
    if (enemy == null) return;
    if (enemy.immuneToPits) return;
    enemy.Die(causeId: DeathCause.Pit);  // 즉사
}
```

### 5. Launch 방향 계산 (공격 방향 → 날아가는 방향)

```csharp
// 공격한 플레이어 위치에서 적까지의 방향으로 날아감
Vector2 launchDir = (enemy.transform.position - attackerPos).normalized;
// 아래로 약간 꺾어 구덩이에 떨어질 확률 높이기
launchDir += Vector2.down * 0.3f;
launchDir.Normalize();

enemy.Launch(launchDir, speed: 8f, duration: 0.6f);
```

---

## 느낌을 살리는 디테일

| 항목 | 구현 방법 | 수치 예 |
|------|----------|---------|
| **히트스톱** | 충돌 순간 0.05~0.1초 멈춤 | `HitstopManager.Apply(0.07f, 0.25f)` |
| **카메라 흔들림** | 충돌 위치로 충격파 | `CinemachineImpulse.GenerateImpulse()` |
| **파티클** | 별 모양 / 충격파 링 | `WallCrashVFX` 풀에서 Spawn |
| **데미지 숫자** | 충격 위치에 큰 숫자 | `FloatingText.Show("CRASH!", yellow)` |
| **속도 궤적** | 날아가는 동안 Trail Renderer | 색 = 발사한 플레이어 색 (고양이=주황) |

---

## OnionCat 적용 포인트

### 현재 아키텍처와의 연결

OnionCat에 이미 존재하는 코드:
- `EnemyBase.Launch(direction, speed)` — 날리기 메서드
- `EffectTrigger.WallCrash` — 벽꽝 발동 트리거
- `EnemyBase.ApplyStun/ApplySlow/ApplyBurn` — 상태이상
- `PoolManager.Spawn/Despawn` — VFX 풀링
- `Sfx.Play(SfxId.WallCrash)` — 효과음

새로 추가할 것:
1. `OnCollisionEnter2D` 내 속도 임계값 체크 (`minCrashSpeed`)
2. 적-적 충돌 시 체인 피해 계산
3. 충돌 세기에 비례한 추가 피해 (`speed * multiplier`)

### 발동 조건 체크리스트

새 장비 효과가 Launch를 사용할 때 확인:
- [ ] `Attacker.Cat / Onion`이 올바르게 전달되는가 (협동 콤보 판정 기준)
- [ ] 보스는 발사 거리를 줄이거나 발사 불가 처리 (`immuneToLaunch` 필드)
- [ ] `EnemyBase.Active`에 있는 적만 대상으로 (소환물 주의)
- [ ] 플레이 테스트 메뉴 `OnionCat > Debug > Launch Test`로 각도·속도 확인

### 협동 콤보 연계
- Onion이 씨앗 탄으로 적을 둔화시키고 → Cat 특수 공격으로 날리기 → 벽꽝
- 이 3단계를 "표준 협동 콤보 흐름"으로 가르치면 자연스러운 협동 유도

### 위험 요소
- 보스가 벽꽝 받으면 불공평하게 느껴질 수 있음 → 보스는 `Launch` 거리 1/3로 제한하되 충격은 받음
- 체인 충돌이 무한히 이어지지 않도록 한 번 Crash된 적에겐 2초 쿨다운

---

## 참고 링크

- Unity Rigidbody2D.velocity: https://docs.unity3d.com/ScriptReference/Rigidbody2D-velocity.html
- OnCollisionEnter2D: https://docs.unity3d.com/ScriptReference/MonoBehaviour.OnCollisionEnter2D.html
- Hades launch mechanic analysis: https://gdcvault.com/play/1026375/ (GDC 2020 Supergiant)
- Enter the Gungeon: enemy knockback feel: https://www.gamedeveloper.com/design/the-art-of-game-feel-in-enter-the-gungeon
