# 보스 패턴 설계 (Boss Pattern Design)

리서치 날짜: 2026-06-14

## 개요

로그라이크에서 보스는 구역의 클라이맥스다. 단순한 "체력 많은 적"이 아니라 **플레이어가 배워야 하는 퍼즐**이다. 좋은 보스는 ① 학습 가능한 패턴, ② 위기감을 주는 연출, ③ 클리어했을 때의 쾌감을 모두 갖춘다. OnionCat에서는 추가로 **고양이(근접) + 작물(원거리) 협동을 강제하는 보스**가 핵심 설계 목표다.

---

## Unity 구현 방법

### 1. 페이즈 기반 보스 구조 (State Machine)

```csharp
public enum BossPhase { Phase1, Phase2, Phase3, Dead }

public class BossController : MonoBehaviour
{
    [SerializeField] private float phase2HealthThreshold = 0.6f; // 체력 60% 이하
    [SerializeField] private float phase3HealthThreshold = 0.3f; // 체력 30% 이하

    private BossPhase currentPhase = BossPhase.Phase1;
    private BossHealthSystem health;

    void Awake()
    {
        health = GetComponent<BossHealthSystem>();
        health.OnHealthChanged += CheckPhaseTransition;
    }

    void CheckPhaseTransition(float ratio)
    {
        if (ratio <= phase3HealthThreshold && currentPhase < BossPhase.Phase3)
            TransitionToPhase(BossPhase.Phase3);
        else if (ratio <= phase2HealthThreshold && currentPhase < BossPhase.Phase2)
            TransitionToPhase(BossPhase.Phase2);
    }

    void TransitionToPhase(BossPhase next)
    {
        currentPhase = next;
        StopAllCoroutines();           // 현재 패턴 중단
        StartCoroutine(PhaseTransitionCutscene(next)); // 연출 후 새 패턴 시작
    }

    IEnumerator PhaseTransitionCutscene(BossPhase next)
    {
        // 히트스톱 + 이펙트
        Time.timeScale = 0.1f;
        yield return new WaitForSecondsRealtime(0.5f);
        Time.timeScale = 1f;

        // 새 패턴 코루틴 시작
        switch (next)
        {
            case BossPhase.Phase2: StartCoroutine(Phase2Pattern()); break;
            case BossPhase.Phase3: StartCoroutine(Phase3Pattern()); break;
        }
    }
}
```

### 2. 패턴 코루틴 구조

```csharp
// Phase1: 기본 패턴 — 근접 돌진만
IEnumerator Phase1Pattern()
{
    while (currentPhase == BossPhase.Phase1)
    {
        yield return StartCoroutine(ChargeAttack());    // 근접 돌진
        yield return new WaitForSeconds(2f);
        yield return StartCoroutine(GroundSlam());     // 지면 충격파
        yield return new WaitForSeconds(1.5f);
    }
}

// Phase2: 근접 + 원거리 혼합 → 협동 강제
IEnumerator Phase2Pattern()
{
    while (currentPhase == BossPhase.Phase2)
    {
        yield return StartCoroutine(ChargeAttack());
        yield return StartCoroutine(BulletSpread(5));  // 5방향 탄막
        yield return new WaitForSeconds(1f);
        yield return StartCoroutine(SummonMinions());  // 미니언 소환
        yield return new WaitForSeconds(2f);
    }
}

// Phase3: 광란 패턴 — 빠른 템포
IEnumerator Phase3Pattern()
{
    float attackInterval = 0.8f; // 더 짧은 간격
    while (currentPhase == BossPhase.Phase3)
    {
        yield return StartCoroutine(BulletCircle(12)); // 12방향 원형 탄막
        yield return new WaitForSeconds(attackInterval);
        yield return StartCoroutine(ChargeAttack());
        yield return new WaitForSeconds(attackInterval);
    }
}
```

### 3. 투사체 패턴 유틸리티

```csharp
public class BossProjectileUtil : MonoBehaviour
{
    [SerializeField] private GameObject bulletPrefab;

    // N방향 균등 분산 발사
    public void FireSpread(int count, float speed)
    {
        float angleStep = 360f / count;
        for (int i = 0; i < count; i++)
        {
            float angle = i * angleStep;
            Vector2 dir = new Vector2(
                Mathf.Cos(angle * Mathf.Deg2Rad),
                Mathf.Sin(angle * Mathf.Deg2Rad)
            );
            var bullet = Instantiate(bulletPrefab, transform.position, Quaternion.identity);
            bullet.GetComponent<Rigidbody2D>().linearVelocity = dir * speed;
        }
    }

    // 플레이어 조준 발사
    public void FireAimed(Transform target, float speed)
    {
        Vector2 dir = (target.position - transform.position).normalized;
        var bullet = Instantiate(bulletPrefab, transform.position, Quaternion.identity);
        bullet.GetComponent<Rigidbody2D>().linearVelocity = dir * speed;
    }
}
```

### 4. 보스 아레나 — 플레이어 경계 제한

```csharp
// 보스 방에 들어오면 카메라 고정 + 문 잠금
public class BossArena : MonoBehaviour
{
    [SerializeField] private GameObject[] doors;

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
            LockArena();
    }

    void LockArena()
    {
        foreach (var door in doors)
            door.SetActive(true); // 문 닫기
        // 보스 BGM 전환
        AudioManager.Instance.PlayBossBGM();
        // 보스 입장 연출
        GetComponentInChildren<BossController>().StartBossFight();
    }

    public void UnlockArena()
    {
        foreach (var door in doors)
            door.SetActive(false);
        AudioManager.Instance.PlayNormalBGM();
    }
}
```

### 5. 보스 HP 바 UI

```csharp
// Canvas - Screen Space Overlay에 별도 보스 HP 바 배치
public class BossHPBar : MonoBehaviour
{
    [SerializeField] private Slider hpSlider;
    [SerializeField] private TMP_Text bossNameText;
    [SerializeField] private CanvasGroup canvasGroup;

    public void Show(string bossName, BossHealthSystem health)
    {
        bossNameText.text = bossName;
        hpSlider.value = 1f;
        health.OnHealthChanged += ratio => hpSlider.value = ratio;
        StartCoroutine(FadeIn());
    }

    IEnumerator FadeIn()
    {
        float t = 0;
        while (t < 0.5f)
        {
            canvasGroup.alpha = t / 0.5f;
            t += Time.deltaTime;
            yield return null;
        }
        canvasGroup.alpha = 1f;
    }
}
```

---

## OnionCat 적용 포인트

### 협동 강제 보스 설계 원칙

| 보스 패턴 | 고양이(근접) 역할 | 작물(원거리) 역할 |
|-----------|-----------------|-----------------|
| 방어막 생성 | 방어막 파괴 (근접 필수) | 본체 딜 |
| 원거리 탄막 | 회피/대시 | 파리 패리 or 방패 막기 |
| 돌진 공격 | 무적 대시로 관통 후 백어택 | 원거리에서 약점 조준 |
| 미니언 소환 | 근접 미니언 처리 | 원거리 미니언 처리 |

### 권장 보스 수 (초기 버전)
- **구역 1 보스**: 단순 패턴 2개 (근접 돌진 + 탄막)
- **구역 2 보스**: 방어막 + 미니언 소환 (협동 필수)
- **구역 3 최종 보스**: 3페이즈, 각 페이즈마다 역할 전환 요구

### 시각적 약점 표시
보스 몸에 아이콘을 표시해 현재 어느 공격 타입이 유효한지 알려주기:
```csharp
[SerializeField] private GameObject meleeWeakIcon;    // 고양이 아이콘
[SerializeField] private GameObject rangedWeakIcon;   // 작물 아이콘

public void SetWeakness(bool melee, bool ranged)
{
    meleeWeakIcon.SetActive(melee);
    rangedWeakIcon.SetActive(ranged);
}
```

### 페이즈 전환 연출 체크리스트
- [ ] 히트스톱 (Time.timeScale 0.1 → 0.5초)
- [ ] 화면 진동 (CinemachineImpulse)
- [ ] 보스 무적 시간 (전환 애니메이션 중)
- [ ] BGM 전환 (Phase2/3에서 더 긴박하게)
- [ ] 파티클 이펙트 (분노 이펙트)

---

## 참고 링크

- Unity 코루틴 패턴: https://docs.unity3d.com/Manual/Coroutines.html
- Boss Design GDC (Hades 보스 철학): https://www.youtube.com/watch?v=bSuNm3-K6Us
- Brackeys 보스 튜토리얼: https://www.youtube.com/watch?v=BmKp3eMTPNs
- Unity State Machine 패턴: https://refactoring.guru/design-patterns/state
- 탄막 패턴 레퍼런스 (Danmaku): https://en.wikipedia.org/wiki/Bullet_hell
