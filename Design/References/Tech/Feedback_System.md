# 피드백 시스템 (Hit Stop · Screen Shake · Particles · Sound)

## 개요
타격감(Game Feel)은 로그라이크의 핵심 재미 요소다. 적을 맞혔을 때 "진짜 맞은 느낌"이 나려면 시각·청각·시간 세 가지 피드백이 동시에 발동되어야 한다. OnionCat은 근접 슬래시(P1)와 원거리 투사체(P2)라는 두 가지 공격 방식이 있으므로, 각각에 맞는 피드백 조합이 필요하다.

---

## Unity 구현 방법

### 1. 히트스톱 (Hit Stop / Freeze Frame)

게임플레이를 아주 짧게(0.05~0.15초) 멈췄다가 재개하는 기법. `Time.timeScale`을 0으로 만들고 실제 시간 기반 코루틴으로 복구한다.

```csharp
// HitStop.cs
public class HitStop : MonoBehaviour
{
    public static HitStop Instance { get; private set; }

    void Awake() => Instance = this;

    public void Stop(float duration)
    {
        StartCoroutine(DoHitStop(duration));
    }

    IEnumerator DoHitStop(float duration)
    {
        Time.timeScale = 0f;
        yield return new WaitForSecondsRealtime(duration);
        Time.timeScale = 1f;
    }
}

// 공격 히트 시 호출
HitStop.Instance.Stop(0.08f);  // 근접 슬래시: 0.08초
HitStop.Instance.Stop(0.04f);  // 원거리 투사체: 0.04초
```

**주의**: `Time.timeScale = 0`이면 일반 `yield return new WaitForSeconds`도 멈춘다. 반드시 `WaitForSecondsRealtime` 사용.

---

### 2. 화면 진동 (Screen Shake) — Cinemachine Impulse

Cinemachine이 설치된 경우 가장 권장되는 방법.

```csharp
// ShakeOnHit.cs
using Cinemachine;

public class ShakeOnHit : MonoBehaviour
{
    [SerializeField] private CinemachineImpulseSource impulseSource;

    public void ShakeLight()  => impulseSource.GenerateImpulse(0.3f);
    public void ShakeHeavy()  => impulseSource.GenerateImpulse(0.8f);
}
```

**Inspector 설정 필요:**
- Virtual Camera에 `CinemachineImpulseListener` 컴포넌트 추가
- `ShakeOnHit` 오브젝트에 `CinemachineImpulseSource` 컴포넌트 추가 후 SerializeField에 드래그

**Cinemachine 미사용 시 대안 (코루틴 기반):**
```csharp
IEnumerator ShakeCamera(float duration, float magnitude)
{
    Vector3 origin = transform.localPosition;
    float elapsed = 0f;
    while (elapsed < duration)
    {
        float x = Random.Range(-1f, 1f) * magnitude;
        float y = Random.Range(-1f, 1f) * magnitude;
        transform.localPosition = origin + new Vector3(x, y, 0f);
        elapsed += Time.deltaTime;
        yield return null;
    }
    transform.localPosition = origin;
}
```

---

### 3. 파티클 이펙트 (Particle Effects)

**오브젝트 풀링과 함께 사용 권장** (런마다 수백 번 발생하므로 Instantiate/Destroy는 비효율).

```csharp
// HitEffectPool.cs
public class HitEffectPool : MonoBehaviour
{
    public static HitEffectPool Instance { get; private set; }

    [SerializeField] private ParticleSystem hitParticlePrefab;
    [SerializeField] private int poolSize = 20;

    private Queue<ParticleSystem> pool = new();

    void Awake()
    {
        Instance = this;
        for (int i = 0; i < poolSize; i++)
        {
            var ps = Instantiate(hitParticlePrefab);
            ps.gameObject.SetActive(false);
            pool.Enqueue(ps);
        }
    }

    public void Play(Vector3 position)
    {
        if (pool.Count == 0) return;
        var ps = pool.Dequeue();
        ps.transform.position = position;
        ps.gameObject.SetActive(true);
        ps.Play();
        StartCoroutine(ReturnToPool(ps));
    }

    IEnumerator ReturnToPool(ParticleSystem ps)
    {
        yield return new WaitForSeconds(ps.main.duration);
        ps.gameObject.SetActive(false);
        pool.Enqueue(ps);
    }
}
```

**파티클 설계 팁 (픽셀아트용):**
- Texture Sheet Animation 사용 → 픽셀 스프라이트 프레임을 파티클로 사용
- Max Particles: 근접 15~30개, 원거리 5~10개
- Start Speed: 2~8, 방향은 충돌 노말 방향으로 설정
- Color over Lifetime: 히트 색상 → 투명 페이드아웃

---

### 4. 사운드 트리거 (Sound Triggers)

AudioManager 싱글톤 패턴으로 중앙화.

```csharp
// AudioManager.cs
public class AudioManager : MonoBehaviour
{
    public static AudioManager Instance { get; private set; }

    [SerializeField] private AudioSource sfxSource;
    [SerializeField] private AudioClip[] meleeHitSounds;   // 근접 타격음 2~3가지
    [SerializeField] private AudioClip[] rangedHitSounds;  // 원거리 타격음 2~3가지
    [SerializeField] private AudioClip parrySound;
    [SerializeField] private AudioClip dashSound;

    void Awake() => Instance = this;

    public void PlayMeleeHit()
    {
        var clip = meleeHitSounds[Random.Range(0, meleeHitSounds.Length)];
        sfxSource.PlayOneShot(clip);
    }

    public void PlayRangedHit()
    {
        var clip = rangedHitSounds[Random.Range(0, rangedHitSounds.Length)];
        sfxSource.PlayOneShot(clip);
    }

    public void PlayParry() => sfxSource.PlayOneShot(parrySound);
    public void PlayDash()  => sfxSource.PlayOneShot(dashSound);
}
```

**랜덤 피치 변조로 반복감 제거:**
```csharp
sfxSource.pitch = Random.Range(0.9f, 1.1f);
sfxSource.PlayOneShot(clip);
sfxSource.pitch = 1f;
```

---

### 5. 전체 피드백 코디네이터

```csharp
// HitFeedback.cs  — 피드백 4가지를 한 번에 실행
public class HitFeedback : MonoBehaviour
{
    public static HitFeedback Instance { get; private set; }
    void Awake() => Instance = this;

    public void OnMeleeHit(Vector3 position)
    {
        HitStop.Instance.Stop(0.08f);
        FindObjectOfType<ShakeOnHit>().ShakeLight();
        HitEffectPool.Instance.Play(position);
        AudioManager.Instance.PlayMeleeHit();
    }

    public void OnRangedHit(Vector3 position)
    {
        HitStop.Instance.Stop(0.04f);
        HitEffectPool.Instance.Play(position);
        AudioManager.Instance.PlayRangedHit();
    }

    public void OnParry(Vector3 position)
    {
        HitStop.Instance.Stop(0.12f);
        FindObjectOfType<ShakeOnHit>().ShakeHeavy();
        HitEffectPool.Instance.Play(position);
        AudioManager.Instance.PlayParry();
    }
}
```

**Inspector 설정 필요:**
- `AudioManager`의 `sfxSource`, `meleeHitSounds`, `rangedHitSounds`, `parrySound`, `dashSound`에 에셋 드래그
- `ShakeOnHit`의 `impulseSource`에 CinemachineImpulseSource 드래그

---

## OnionCat 적용 포인트

| 상황 | 히트스톱 | 화면진동 | 파티클 | 사운드 |
|------|----------|----------|--------|--------|
| P1 근접 적 타격 | 0.08초 | ShakeLight | 불꽃 파티클 | 둔탁한 검격음 |
| P2 투사체 적 타격 | 0.04초 | 없음 | 작은 폭발 파티클 | 경쾌한 팝음 |
| P2 방패 패리 성공 | 0.12초 | ShakeHeavy | 금속 파편 파티클 | 금속 쨍 소리 |
| P1 무적 대시 | 없음 | 없음 | 잔상 이펙트 | 바람 소리 |
| 보스 피격 | 0.15초 | ShakeHeavy | 큰 임팩트 파티클 | 묵직한 타격음 |

**구현 우선순위**: 히트스톱 → 사운드 → 파티클 → 화면진동 순서로 구현. 히트스톱과 사운드만 있어도 타격감이 크게 향상됨.

---

## 참고 링크
- Unity 공식: https://docs.unity3d.com/Manual/class-ParticleSystem.html
- Cinemachine Impulse: https://docs.unity3d.com/Packages/com.unity.cinemachine@2.8/manual/CinemachineImpulse.html
- Game Feel(게임 감각) 개념: "Game Feel by Steve Swink" 검색
- 유튜브 튜토리얼: "Unity hit stop screen shake game feel tutorial"
- Board To Bits Games - "Making Your Game Feel Amazing" (유튜브)
