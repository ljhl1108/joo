# Coroutine 기반 시퀀스 & 이벤트 타이밍 제어

리서치 날짜: 2026-07-05

## 개요

Unity Coroutine은 `IEnumerator`를 반환하는 함수로, 한 프레임에 다 실행하지 않고 여러 프레임에 걸쳐 실행을 분산할 수 있는 메커니즘이다.

OnionCat에서 Coroutine이 필요한 상황:
- 적 공격 패턴 (전조 → 0.5초 딜레이 → 실제 타격)
- 피격 후 무적 시간 + 깜빡임 효과
- 방 클리어 후 문 열림 + 카메라 이동 + 업그레이드 창 출현 순서
- 보스 등장 연출 (이름 표시 → 0.5초 → 등장 애니메이션 → 공격 시작)
- 사망 연출 (히트스톱 → 슬로우 → 폭발 파티클 → 검은 화면)

`Update()`로 타이밍을 제어하면 bool 플래그 + 타이머 변수가 폭발적으로 늘어난다. Coroutine을 쓰면 읽기 쉬운 선형 코드로 작성 가능하다.

---

## Unity 구현 방법

### 기본 문법

```csharp
void Start()
{
    StartCoroutine(AttackSequence());
}

IEnumerator AttackSequence()
{
    // 1단계: 전조 모션
    animator.SetTrigger("WindUp");
    yield return new WaitForSeconds(0.4f);  // 0.4초 대기

    // 2단계: 실제 공격
    hitbox.enabled = true;
    animator.SetTrigger("Attack");
    yield return new WaitForSeconds(0.1f);  // 히트박스 활성화 0.1초 유지

    // 3단계: 히트박스 끄기
    hitbox.enabled = false;
    yield return new WaitForSeconds(0.3f);  // 후딜레이

    // 4단계: 다시 Idle
    animator.SetTrigger("Idle");
}
```

### 자주 쓰는 yield 명령어

| 명령어 | 동작 |
|--------|------|
| `yield return null` | 다음 프레임까지 대기 |
| `yield return new WaitForSeconds(t)` | t초 대기 (TimeScale 영향 받음) |
| `yield return new WaitForSecondsRealtime(t)` | t초 대기 (TimeScale 무시 — 일시정지 중에도 진행) |
| `yield return new WaitUntil(() => condition)` | 조건이 true될 때까지 대기 |
| `yield return new WaitForEndOfFrame()` | 렌더링 완료 후 실행 |
| `yield return StartCoroutine(OtherCoroutine())` | 다른 코루틴 완료 후 진행 |

### Coroutine 중단 & 관리

```csharp
// 코루틴 참조 저장 → 중단 가능
Coroutine _attackCoroutine;

void StartAttack()
{
    // 이미 실행 중이면 중단 후 재시작
    if (_attackCoroutine != null)
        StopCoroutine(_attackCoroutine);
    _attackCoroutine = StartCoroutine(AttackSequence());
}

void OnDeath()
{
    // 죽었을 때 모든 코루틴 중단
    StopAllCoroutines();
    StartCoroutine(DeathSequence());
}
```

### 피격 무적 + 깜빡임 패턴

```csharp
[SerializeField] private SpriteRenderer spriteRenderer;
[SerializeField] private float invincibleDuration = 1.5f;
[SerializeField] private float blinkInterval = 0.1f;

bool _isInvincible = false;

public void TakeDamage(int amount)
{
    if (_isInvincible) return;
    
    health -= amount;
    StartCoroutine(InvincibilityCoroutine());
}

IEnumerator InvincibilityCoroutine()
{
    _isInvincible = true;
    
    float elapsed = 0f;
    while (elapsed < invincibleDuration)
    {
        spriteRenderer.enabled = !spriteRenderer.enabled;  // 깜빡임
        yield return new WaitForSeconds(blinkInterval);
        elapsed += blinkInterval;
    }
    
    spriteRenderer.enabled = true;
    _isInvincible = false;
}
```

### 히트스톱 (Hit Stop) 패턴

```csharp
IEnumerator HitStop(float duration)
{
    Time.timeScale = 0.05f;  // 거의 멈춤
    yield return new WaitForSecondsRealtime(duration);  // RealTime 필수!
    Time.timeScale = 1f;
}

// 적 처치 시 호출
public void OnKillEnemy()
{
    StartCoroutine(HitStop(0.06f));  // 60ms 히트스톱
}
```

### 방 클리어 연출 시퀀스

```csharp
IEnumerator RoomClearSequence()
{
    // 1. 문 열림 이펙트
    foreach (var door in roomDoors)
        door.Open();
    
    yield return new WaitForSeconds(0.3f);
    
    // 2. 화면 텍스트 "Room Clear!"
    uiManager.ShowRoomClearText();
    yield return new WaitForSeconds(0.5f);
    
    // 3. 아이템 드롭 스폰
    itemSpawner.SpawnReward(transform.position);
    yield return new WaitForSeconds(0.2f);
    
    // 4. UI 텍스트 숨김
    uiManager.HideRoomClearText();
}
```

### 보스 등장 연출

```csharp
IEnumerator BossIntroSequence()
{
    // 카메라 이동 & 화면 어둡게
    cameraController.FocusOnBoss();
    screenFader.FadeOut(0.3f);
    yield return new WaitForSeconds(0.5f);
    
    // 보스 이름 표시
    bossNameUI.Show(bossData.bossName);
    yield return new WaitForSeconds(1.5f);
    
    // 보스 등장 애니메이션
    boss.PlayEntranceAnimation();
    yield return new WaitUntil(() => boss.IsEntranceDone);
    
    // 전투 시작
    boss.EnterCombatPhase();
    screenFader.FadeIn(0.3f);
    cameraController.ReturnToPlayer();
}
```

### 코루틴 캐싱 (GC 최적화)

```csharp
// WaitForSeconds 매번 new 하지 말고 캐싱
private static readonly WaitForSeconds Wait01 = new WaitForSeconds(0.1f);
private static readonly WaitForSeconds Wait05 = new WaitForSeconds(0.5f);

IEnumerator BlinkEffect()
{
    spriteRenderer.enabled = false;
    yield return Wait01;  // 캐싱된 인스턴스 재사용
    spriteRenderer.enabled = true;
    yield return Wait05;
}
```

---

## OnionCat 적용 포인트

### Cat 대시 무적 시퀀스

```csharp
IEnumerator DashSequence(Vector2 direction)
{
    // 1. 무적 ON + 이동
    _isInvincible = true;
    rb.velocity = direction * dashSpeed;
    
    // 2. 잔상 이펙트 (여러 프레임)
    for (int i = 0; i < 5; i++)
    {
        SpawnAfterimage(transform.position);
        yield return null;  // 다음 프레임
    }
    
    // 3. 감속
    yield return new WaitForSeconds(dashDuration);
    rb.velocity = Vector2.zero;
    
    // 4. 무적 OFF + 쿨다운
    _isInvincible = false;
    yield return new WaitForSeconds(dashCooldown);
    _canDash = true;
}
```

### Onion 패리 성공 연출

```csharp
IEnumerator ParrySuccessSequence()
{
    // 히트스톱
    yield return StartCoroutine(HitStop(0.08f));
    
    // 파티클 + 사운드
    parryEffect.Play();
    audioSource.PlayOneShot(parryClip);
    
    // 잠시 슬로우
    Time.timeScale = 0.3f;
    yield return new WaitForSecondsRealtime(0.15f);
    Time.timeScale = 1f;
}
```

### 주의: GameObject 비활성화 시 코루틴 자동 중단

- `gameObject.SetActive(false)` 호출 시 해당 오브젝트의 모든 코루틴이 즉시 중단됨
- 해결법 1: 비활성화 대신 SpriteRenderer 끄기만 하기
- 해결법 2: 코루틴을 GameManager 같은 항상 활성화된 오브젝트에서 실행

---

## 참고 링크

- [Unity 공식 - Coroutines 문서](https://docs.unity3d.com/Manual/Coroutines.html)
- [Unity 공식 - WaitForSeconds API](https://docs.unity3d.com/ScriptReference/WaitForSeconds.html)
- [Brackeys - How to use Coroutines in Unity (YouTube)](https://www.youtube.com/watch?v=qolENyOgEns)
- [Jason Weimann - Unity Coroutines Best Practices](https://unity3d.college/2017/09/09/unity-tips-coroutines/)
- [Unity Learn - Introduction to Coroutines](https://learn.unity.com/tutorial/coroutines)
