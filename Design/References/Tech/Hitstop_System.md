# 히트스톱 (Hit Stop) 구현 시스템

리서치 날짜: 2026-09-08

## 개요

히트스톱(Hit Stop, 히트프리즈)은 공격이 적중하는 순간 **게임을 아주 짧은 시간(0.03~0.12초) 동안 멈추거나 극단적으로 느리게 만드는 기법**이다. 이 짧은 정지 덕분에 타격감이 물리적으로 '무겁게' 느껴진다. Hades, Dead Cells, Enter the Gungeon 등 거의 모든 최상위 액션 로그라이크가 이 기법을 사용한다.

히트스톱 없이 피드백만 추가(파티클·사운드)해도 전투가 '가볍게' 느껴지는 이유는 여기에 있다. 시각·청각 피드백보다 시간의 일시 정지가 타격감에 가장 강하게 기여한다.

---

## Unity 구현 방법

### 방법 1: Time.timeScale 기반 (전통적, 가장 단순)

```csharp
public class HitstopManager : MonoBehaviour
{
    private static HitstopManager _instance;
    public static HitstopManager Instance => _instance;

    private Coroutine _currentHitstop;

    void Awake()
    {
        if (_instance != null) { Destroy(gameObject); return; }
        _instance = this;
    }

    // 호출: HitstopManager.Instance.Trigger(0.05f, 0.0f);
    // duration: 히트스톱 지속 시간(초, 리얼타임), scale: 해당 시간 동안의 TimeScale
    public void Trigger(float duration, float scale = 0f)
    {
        if (_currentHitstop != null) StopCoroutine(_currentHitstop);
        _currentHitstop = StartCoroutine(DoHitstop(duration, scale));
    }

    private IEnumerator DoHitstop(float duration, float scale)
    {
        Time.timeScale = scale;
        yield return new WaitForSecondsRealtime(duration);
        Time.timeScale = 1f;
        _currentHitstop = null;
    }
}
```

**주의사항:**
- `WaitForSeconds` 대신 반드시 `WaitForSecondsRealtime` 사용 → TimeScale=0일 때도 실제 시간 기준으로 대기
- `Time.fixedDeltaTime = Time.timeScale * 0.02f` 설정하면 물리 연산도 같이 멈춤 (권장)
- 히트스톱 중 CinemachineImpulse(화면 흔들림) 발동 금지 → 흔들림이 동결됨. 히트스톱 해제 후 발동

---

### 방법 2: 개별 오브젝트 timeScale 기반 (OnionCat 권장)

TimeScale 전역 조작은 UI 애니메이션, 오디오 피치 등에 부작용이 생길 수 있다. 대신 피격 대상 오브젝트만 개별적으로 멈추는 방식이 더 안전하다.

```csharp
// Animator 기반 개별 히트스톱
public class EnemyHitstop : MonoBehaviour
{
    [SerializeField] private Animator _animator;
    private Coroutine _hitstopRoutine;

    public void TriggerHitstop(float duration)
    {
        if (_hitstopRoutine != null) StopCoroutine(_hitstopRoutine);
        _hitstopRoutine = StartCoroutine(DoHitstop(duration));
    }

    private IEnumerator DoHitstop(float duration)
    {
        _animator.speed = 0f;
        yield return new WaitForSecondsRealtime(duration);
        _animator.speed = 1f;
    }
}
```

장점: TimeScale은 1로 유지 → UI, 오디오, 파티클 영향 없음  
단점: 피격자마다 컴포넌트 필요, 대형 적 다수 동시 히트 시 관리 복잡

---

### 방법 3: 하이브리드 (실전 권장 구조)

```
근접 타격(P1 슬래시) → 전역 HitstopManager.Trigger(0.06f, 0f)
원거리 타격(P2 투사체) → EnemyHitstop.TriggerHitstop(0.03f)
보스 처치 → HitstopManager.Trigger(0.15f, 0f)
```

근접 타격은 강한 전신 충격이므로 전역 정지, 원거리 투사체는 경쾌한 느낌이므로 부분 정지로 차별화.

---

### 히트스톱 지속 시간 가이드

| 상황 | 권장 시간 | 비고 |
|------|-----------|------|
| 일반 근접 공격 | 0.05~0.06초 | 빠른 타격감 |
| 강 공격 / 차지 | 0.09~0.12초 | 무게감 |
| 원거리 투사체 히트 | 0.03~0.04초 | 가볍고 경쾌 |
| 패리 성공 | 0.1~0.15초 | 강렬한 반전 표현 |
| 보스 처치 | 0.15~0.2초 | 극적 연출 |
| 피해 없음 (방어됨) | 0~0.02초 | 거의 없음 → "튕긴" 느낌 |

---

### 히트스톱 발동 순서 (반드시 지켜야 할 순서)

```
1. 히트 판정 → Damage 처리
2. SFX 재생 (TimeScale 영향 없는 AudioSource.PlayClipAtPoint)
3. HitstopManager.Trigger() 호출 → TimeScale = 0
4. WaitForSecondsRealtime 대기
5. TimeScale = 1 복원
6. CinemachineImpulse (화면 흔들림) 발동
7. 파티클 이펙트 Instantiate
8. 넉백 처리
```

**⚠ 6번 화면 흔들림을 3번보다 앞에 두면 TimeScale=0 동안 Cinemachine이 업데이트를 멈춰 흔들림이 동결되는 버그 발생.**

---

### 히트스톱과 오디오 피치 유지

```csharp
// AudioSource가 TimeScale을 따라가면 소리가 느려짐. 이를 방지:
audioSource.pitch = 1f / Time.timeScale; // hitstop 중에도 정상 피치 유지
```

또는 `AudioSource.ignoreListenerPause = true` 설정으로 글로벌 Pause 영향 차단.

---

## OnionCat 적용 포인트

### P1(고양이) 슬래시 — 전역 히트스톱

```csharp
// CatSlashAttack.cs의 OnHit에서 호출
HitstopManager.Instance.Trigger(
    duration: 0.06f,
    scale: 0f
);
```

근접 전용 약점 적을 정확하게 타격했을 때만 히트스톱을 더 길게(0.1초) → "약점을 제대로 찾았다"는 촉각 피드백.

### P2(양파) 투사체 — 개별 히트스톱

```csharp
// Projectile.cs의 OnTriggerEnter2D에서:
enemy.GetComponent<EnemyHitstop>()?.TriggerHitstop(0.03f);
```

### 패리 성공 — 강한 히트스톱 + 방향성 흔들림

```csharp
// ParryShieldController.cs:
IEnumerator ParrySuccess(Vector2 incomingDir)
{
    HitstopManager.Instance.Trigger(0.12f, 0f);
    yield return new WaitForSecondsRealtime(0.12f);
    _impulseSource.GenerateImpulse(-incomingDir * 1.5f); // 흔들림은 히트스톱 후
}
```

### 접근성 고려

- 설정 메뉴에 "타격 효과 강도" 슬라이더 0/50/100% 추가
- `HitstopManager.durationMultiplier` 필드를 PlayerPrefs와 연동
- 멀미 민감 사용자를 위한 히트스톱 강도 조절 옵션

---

## 참고 링크

- [Game Feel — Steve Swink 저 (게임 느낌의 교과서)](https://www.google.com/search?q=game+feel+steve+swink)
- [Unity Time.timeScale 공식 문서](https://docs.unity3d.com/ScriptReference/Time-timeScale.html)
- [GDC: The Art of Screenshake (Jan Willem Nijman)](https://www.youtube.com/watch?v=AJdEqssNZ-U)
- [Hitstop in Unity Tutorial — Game Dev Guide](https://www.youtube.com/results?search_query=unity+hitstop+tutorial)
- [Dead Cells 개발자 GDC 토크 — 게임 느낌 설계](https://www.gdcvault.com/play/1025463)
