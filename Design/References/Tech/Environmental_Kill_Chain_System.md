# Environmental Kill Chain System

리서치 날짜: 2026-10-16

## 개요

적을 발사하여 벽·구덩이·다른 적·폭탄 등 환경 요소와 충돌시켜 피해 또는 즉사를 일으키는 시스템.
OnionCat의 **걷어차기(Kick)** 핵심 피드백 루프 — "날리기 → 부딪히기 → 연쇄" — 를 코드로 구현하는 방법.

게임 예시: Nuclear Throne(벽 튕기기), Enter the Gungeon(날림), Anger Foot(환경 파괴), OnionCat(CRASH·낙사·KICK COMBO).

---

## Unity 구현 방법

### 1. 발사 상태 표시

날아가고 있는 적과 그냥 이동 중인 적을 구분해야 충돌 이벤트에서 CRASH를 판별할 수 있다.

```csharp
// EnemyBase.cs (일부)
public bool IsLaunched { get; private set; }
private float _launchSpeed;  // 발사 당시 속력 캐시

public void Launch(Vector2 direction, float force, bool interruptTelegraph = false)
{
    IsLaunched = true;
    _launchSpeed = force;
    _rb.linearVelocity = direction.normalized * force;
    if (interruptTelegraph) CancelTelegraph();
    StartCoroutine(LaunchTimeout(2f)); // 최대 2초 후 상태 해제 (벽에 안 닿았을 때 대비)
}

private IEnumerator LaunchTimeout(float seconds)
{
    yield return new WaitForSeconds(seconds);
    IsLaunched = false;
}
```

### 2. 벽 충돌 — CRASH 판정

`EnemyBase.OnCollisionEnter2D`에서 Wall 레이어 충돌 + IsLaunched + 속력 임계값으로 CRASH를 판정한다.

```csharp
void OnCollisionEnter2D(Collision2D col)
{
    if (!IsLaunched) return;

    float impactSpeed = col.relativeVelocity.magnitude;
    bool hitWall = col.gameObject.layer == LayerMask.NameToLayer("Wall");
    bool hitEnemy = col.collider.TryGetComponent<EnemyBase>(out var other);

    if (hitWall && impactSpeed > crashSpeedThreshold)
    {
        TriggerCrash(impactSpeed);
    }
    else if (hitEnemy && impactSpeed > hitChainThreshold)
    {
        TriggerKickCombo(other, col.relativeVelocity);
    }

    IsLaunched = false;
}

private void TriggerCrash(float speed)
{
    float damage = Mathf.Lerp(crashDamageMin, crashDamageMax,
                              (speed - crashSpeedThreshold) / crashSpeedRange);
    TakeDamage(damage, DamageType.Physical, Attacker.Cat);
    Stun(crashStunDuration);
    // 히트스톱, VFX, 사운드
    Sfx.Play(SfxId.EnemyCrash);
    SpawnCrashVFX(transform.position);
}
```

### 3. 적끼리 충돌 — KICK COMBO

날아간 적이 다른 적에게 부딪히면 KICK COMBO 발동.
연쇄 반응을 방지하기 위해 **발사된 적(IsLaunched=true)만 COMBO를 유발**하고, 2차로 맞은 적은 IsLaunched 없이 짧은 넉백만 받는다.

```csharp
private void TriggerKickCombo(EnemyBase victim, Vector2 impactVelocity)
{
    float damage = kickComboDamage;
    victim.TakeDamage(damage, DamageType.Physical, Attacker.Cat);
    // 피해를 준 적에게도 반발 충격
    TakeDamage(kickSelfImpactDamage, DamageType.Physical, Attacker.Cat);
    // 연쇄 넉백 (IsLaunched 없이)
    victim.ApplyKnockback(impactVelocity.normalized * kickChainPush);

    HUD.ShowLabel("KICK COMBO!", transform.position, Color.yellow);
    GameManager.Instance.Run.JointGauge += 15;
    Sfx.Play(SfxId.KickCombo);
}
```

### 4. 구덩이 — 낙사 판정

구덩이는 `Pit` 태그의 트리거 콜라이더. `IsLaunched` 적이 트리거에 진입하면 즉사.

```csharp
// EnemyBase.cs
void OnTriggerEnter2D(Collider2D col)
{
    if (!col.CompareTag("Pit")) return;
    if (!IsLaunched) return; // 일반 이동 중인 적은 통과
    if (immuneToPits) return; // 보스 등 낙사 면역

    StartCoroutine(PitDeath());
}

private IEnumerator PitDeath()
{
    IsLaunched = false;
    // 애니메이션: 적이 구덩이 안으로 사라지는 효과
    yield return PlayPitFallAnimation();
    Die(Attacker.Cat, isDrown: true);
}
```

### 5. 폭탄 연쇄 — KICK COMBO 변형

날아간 적이 심긴 박(BouncingBomb)에 닿으면 폭탄 폭발 트리거.

```csharp
// BouncingBomb.cs
void OnTriggerEnter2D(Collider2D col)
{
    if (!col.TryGetComponent<EnemyBase>(out var enemy)) return;
    if (!enemy.IsLaunched) return;  // 킥으로 날아온 적만
    Explode();
}

void Explode()
{
    // 반경 내 모든 적에게 피해
    var hits = Physics2D.OverlapCircleAll(transform.position, explodeRadius,
                                          LayerMask.GetMask("Enemy"));
    foreach (var h in hits)
        h.GetComponent<EnemyBase>()?.TakeDamage(explosionDamage, DamageType.Fire, Attacker.Onion);

    HUD.ShowLabel("KICK COMBO!", transform.position, Color.yellow);
    GameManager.Instance.Run.JointGauge += 15;
    Sfx.Play(SfxId.BombExplode);
    Destroy(gameObject);
}
```

### 6. 속도 임계값 튜닝 포인트

`HitFeelSettings.asset`에 다음 항목 추가:

| 항목 | 기본값 | 역할 |
|------|--------|------|
| `crashSpeedThreshold` | 8f | 이 속력 미만이면 CRASH 미발동 |
| `crashDamageMin` | 15f | 임계값 직후 피해 |
| `crashDamageMax` | 60f | 최대 속력 시 피해 |
| `crashSpeedRange` | 20f | min→max 범위 |
| `crashStunDuration` | 0.6f | CRASH 후 기절 |
| `kickChainPush` | 5f | 연쇄 넉백 힘 |
| `kickComboDamage` | 25f | 적끼리 충돌 피해 |
| `hitChainThreshold` | 5f | 적끼리 충돌 최소 속력 |

---

## OnionCat 적용 포인트

### 현재 구현 상태 (2026-10-15 기준)
- `EnemyBase`에 `IsLaunched` 개념 구현됨
- `KickAttack` 컴포넌트에서 `Launch(direction, force, interruptTelegraph)` 호출
- 벽 충돌 CRASH, 구덩이 낙사, 박 폭발 KICK COMBO 모두 동작 중

### 개선 가능한 방향
1. **속력 기반 피해 스케일링** — 현재 고정 피해인지 확인 필요. 충돌 속력을 `col.relativeVelocity.magnitude`로 읽어 CRASH 피해에 반영하면 강하게 차면 더 아프다는 물리적 쾌감이 강화됨
2. **연쇄 CRASH 카운터** — 1번 CRASH → 2번 KICK COMBO → 벽 CRASH 같은 연쇄가 일어날 때 CRASH 횟수를 누적해 보여주는 "CHAIN ×N" 레이블 (Anger Foot 참고)
3. **구덩이 낙사 연출 개선** — 구덩이에 빠지는 적이 즉시 사라지지 않고 0.2초 동안 축소+낙하 트윈 후 사라지면 더 명확한 피드백
4. **적 간 충돌 각도에 따른 분산 넉백** — 날아온 적이 두 번째 적에게 비스듬히 부딪힐 때 두 번째 적이 충돌 각도에 맞게 튕겨나가면 당구공 연출. `col.relativeVelocity`에서 반사벡터 계산
5. **보스 킥 방해 예외** — `kickInterruptsTelegraph = false`인 보스에게 KICK COMBO가 발동해도 예고가 끊기지 않아야 함. `Launch()` 내부에서 체크됨; 레이아웃 변경 시 주의

### 발사 관련 장비 효과 확장 아이디어
- 고양이 무기: "CRASH 후 추가 충격파 생성" → `OnCrash` 이벤트 훅 필요
- 패시브: "낙사 시 씨앗 3개 추가 획득" → `OnPitDeath` 이벤트 훅
- 스킬: "발사된 적이 벽에 닿으면 폭발" → `GearEffect` 발동 조건 `OnCrash`

---

## 참고 링크
- Unity Rigidbody2D.velocity + OnCollisionEnter2D: https://docs.unity3d.com/ScriptReference/Rigidbody2D-linearVelocity.html
- Collision2D.relativeVelocity: https://docs.unity3d.com/ScriptReference/Collision2D-relativeVelocity.html
- Physics2D.OverlapCircleAll: https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircleAll.html
- Anger Foot(킥 체인) GDC 포스트모템: https://store.steampowered.com/app/1326630/Anger_Foot/ (Steam 페이지 참고)
