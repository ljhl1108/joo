# Weapon Feel Tuning System (무기 타격감 종합 튜닝)

리서치 날짜: 2026-09-11

## 개요

"게임 주스(Game Juice)"라고도 불리는 무기 타격감은 단일 시스템이 아닌, **히트스톱 + 화면 흔들림 + 사운드 + 파티클 + 이동 반응**이 동기화되어 나타나는 복합 효과다.

OnionCat에서 Cat의 180도 슬래시와 Onion의 투사체가 각각 다른 "감촉"으로 느껴져야 협동의 시너지가 살아난다. 이 문서는 각 요소를 통합 튜닝하는 방법을 다룬다.

---

## Unity 구현 방법

### 1. 타격감의 5요소 동기화 타이밍

타격 감지(`OnTriggerEnter2D`) 순간부터 모든 요소가 **같은 프레임에** 시작해야 한다:

```
[타격 발생 Frame 0]
  ├─ HitStop: Time.timeScale = 0.05f (3~5프레임)
  ├─ CameraTrauma: trauma += 0.4f
  ├─ SFX: PlayOneShot(hitSound, 랜덤 피치)
  ├─ VFX: SpawnParticle(hitSpark, hitPoint)
  └─ Knockback: rb.AddForce(knockDir * force)
```

### 2. 히트스톱 (HitStop) 구현

```csharp
public class HitStopManager : MonoBehaviour
{
    private Coroutine _stopRoutine;

    public void DoHitStop(float duration, float timeScale = 0.05f)
    {
        if (_stopRoutine != null) StopCoroutine(_stopRoutine);
        _stopRoutine = StartCoroutine(HitStopRoutine(duration, timeScale));
    }

    private IEnumerator HitStopRoutine(float duration, float timeScale)
    {
        Time.timeScale = timeScale;
        yield return new WaitForSecondsRealtime(duration);
        Time.timeScale = 1f;
        _stopRoutine = null;
    }
}
```

**권장 수치 (픽셀아트 기준)**:
| 공격 종류 | 히트스톱 시간 | timeScale |
|-----------|--------------|-----------|
| Cat 슬래시 (일반 적) | 0.05초 | 0.08f |
| Cat 슬래시 (보스) | 0.08초 | 0.05f |
| Onion 투사체 | 0.03초 | 0.15f |
| 패리 성공 | 0.12초 | 0.02f |

### 3. 카메라 트라우마 쉐이크

단순 sin 진동보다 **트라우마(trauma)** 방식이 자연스럽다:

```csharp
public class CameraShakeController : MonoBehaviour
{
    [SerializeField] private float traumaDecay = 1.8f;
    [SerializeField] private float maxOffsetX = 0.15f;
    [SerializeField] private float maxOffsetY = 0.15f;
    [SerializeField] private float maxRoll = 1.5f;
    [SerializeField] private float shakeFrequency = 25f;

    private float _trauma;
    private float _seed;

    private void Awake() => _seed = Random.value * 100f;

    public void AddTrauma(float amount) => _trauma = Mathf.Min(1f, _trauma + amount);

    private void Update()
    {
        if (_trauma <= 0f) return;

        float shake = _trauma * _trauma; // 제곱으로 감쇠 곡선
        float t = Time.time * shakeFrequency;
        float offsetX = maxOffsetX * shake * (Mathf.PerlinNoise(_seed, t) * 2f - 1f);
        float offsetY = maxOffsetY * shake * (Mathf.PerlinNoise(_seed + 1f, t) * 2f - 1f);
        float roll = maxRoll * shake * (Mathf.PerlinNoise(_seed + 2f, t) * 2f - 1f);

        transform.localPosition = new Vector3(offsetX, offsetY, 0f);
        transform.localRotation = Quaternion.Euler(0f, 0f, roll);

        _trauma -= traumaDecay * Time.deltaTime;
        if (_trauma < 0f) _trauma = 0f;
    }
}
```

**권장 트라우마 수치**:
| 이벤트 | trauma 증가량 |
|--------|--------------|
| Cat 슬래시 명중 | 0.15f |
| Onion 투사체 명중 | 0.10f |
| 패리 성공 | 0.30f |
| 플레이어 피격 | 0.40f |
| 보스 사망 | 0.60f |

### 4. 히트 사운드 랜덤 피치

```csharp
public class WeaponSFX : MonoBehaviour
{
    [SerializeField] private AudioSource audioSource;
    [SerializeField] private AudioClip[] meleeHitClips;
    [SerializeField] private AudioClip[] rangedHitClips;

    [Range(0.85f, 1f)] [SerializeField] private float pitchMin = 0.9f;
    [Range(1f, 1.15f)] [SerializeField] private float pitchMax = 1.1f;

    public void PlayMeleeHit()
    {
        audioSource.pitch = Random.Range(pitchMin, pitchMax);
        audioSource.PlayOneShot(meleeHitClips[Random.Range(0, meleeHitClips.Length)]);
    }

    public void PlayRangedHit()
    {
        audioSource.pitch = Random.Range(pitchMin, pitchMax);
        audioSource.PlayOneShot(rangedHitClips[Random.Range(0, rangedHitClips.Length)]);
    }
}
```

### 5. 파티클 스폰 (Object Pool 연계)

```csharp
// 타격 위치에 방향성 있는 스파크 파티클 스폰
public void SpawnHitSpark(Vector2 hitPoint, Vector2 attackDirection)
{
    var spark = ObjectPool.Instance.Get(hitSparkPrefab, hitPoint, Quaternion.identity);
    var ps = spark.GetComponent<ParticleSystem>();
    var main = ps.main;
    main.startRotation = Mathf.Atan2(attackDirection.y, attackDirection.x);
    ps.Play();
}
```

### 6. 통합 WeaponFeel 매니저

```csharp
public class WeaponFeelManager : MonoBehaviour
{
    public static WeaponFeelManager Instance { get; private set; }

    [SerializeField] private HitStopManager hitStop;
    [SerializeField] private CameraShakeController cameraShake;
    [SerializeField] private WeaponSFX weaponSFX;

    private void Awake() => Instance = this;

    public void OnMeleeHit(Vector2 hitPoint, Vector2 attackDir)
    {
        hitStop.DoHitStop(0.05f, 0.08f);
        cameraShake.AddTrauma(0.15f);
        weaponSFX.PlayMeleeHit();
        SpawnHitSpark(hitPoint, attackDir);
    }

    public void OnRangedHit(Vector2 hitPoint, Vector2 attackDir)
    {
        hitStop.DoHitStop(0.03f, 0.15f);
        cameraShake.AddTrauma(0.10f);
        weaponSFX.PlayRangedHit();
        SpawnHitSpark(hitPoint, attackDir);
    }

    public void OnParrySuccess(Vector2 hitPoint)
    {
        hitStop.DoHitStop(0.12f, 0.02f);
        cameraShake.AddTrauma(0.30f);
        // 패리 전용 이펙트 추가
    }
}
```

---

## OnionCat 적용 포인트

### Cat(P1) vs Onion(P2) 차별화 타격감

두 캐릭터의 타격감이 달라야 협동의 역할 분담이 감각적으로 전달됨:

| 요소 | Cat (근접 슬래시) | Onion (원거리 투사체) |
|------|-------------------|----------------------|
| 히트스톱 | 0.05초, 강한 | 0.03초, 짧고 빠름 |
| 카메라 쉐이크 | trauma 0.15, 넓게 | trauma 0.10, 빠르게 |
| 사운드 | 둔탁하고 묵직한 금속음 | 가볍고 날카로운 팝음 |
| 파티클 | 큰 오렌지 스파크 | 작은 흰색/파란 점들 |
| 넉백 | 큰 넉백 (적이 밀림) | 작은 넉백 + 상태이상 |

### 구현 우선순위 (초보자 권장 순서)
1. **히트스톱만 먼저** → 즉각적 타격감 개선
2. **사운드 랜덤 피치** → 단조로움 제거
3. **파티클 스폰** → 시각 피드백
4. **카메라 트라우마** → 게임이 "살아있는" 느낌
5. **전체 동기화 튜닝** → 수치 조정으로 완성도

---

## 참고 링크

- Game Maker's Toolkit - "Game Feel": https://www.youtube.com/watch?v=216_5nu4aVQ
- Vlambeer - "The Art of Screenshake" (GDC 2013): 가장 중요한 타격감 강연
- "Camera Trauma System" by Martin Magnusson: https://www.martinmagnusson.com/ 검색
- Brackeys "Screen Shake Effect in Unity": YouTube에서 직접 검색
- Unity Cinemachine Impulse vs. Manual Shake 비교 공식 문서: https://docs.unity3d.com/Packages/com.unity.cinemachine@2.9/
