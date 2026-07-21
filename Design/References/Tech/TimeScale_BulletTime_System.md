# TimeScale / Bullet Time System

리서치 날짜: 2026-07-21

## 개요

게임 내 시간을 일시적으로 느리게(또는 빠르게) 만드는 시스템. Unity의 `Time.timeScale`을 제어하며, 보스 피격 순간의 극적 연출, 죽음 슬로모, 패링 성공 연출, 히트스톱 확장 등에 활용된다.

OnionCat에서는 협공 성공(`Synergy Break`) 연출, 보스 처치 슬로모, 패링 타이밍 시각화에 활용할 수 있다.

## Unity 구현 방법

### 기본 원리
```csharp
// Time.timeScale: 0 = 완전 정지, 1 = 정상, 0.3 = 슬로모
// Time.unscaledDeltaTime: timeScale에 영향 받지 않는 실제 시간 (UI, 효과음에 사용)
Time.timeScale = 0.3f;
Time.fixedDeltaTime = 0.02f * Time.timeScale; // 물리 시뮬레이션도 맞춰야 함
```

### TimeScaleManager (싱글톤)
```csharp
public class TimeScaleManager : MonoBehaviour
{
    public static TimeScaleManager Instance { get; private set; }

    private float _defaultTimeScale = 1f;
    private Coroutine _currentRoutine;

    void Awake() => Instance = this;

    // 슬로모 진입 후 자동 복구
    public void SlowMotion(float scale, float duration)
    {
        if (_currentRoutine != null) StopCoroutine(_currentRoutine);
        _currentRoutine = StartCoroutine(SlowRoutine(scale, duration));
    }

    // 히트스톱 (완전 정지 후 즉시 복구)
    public void HitStop(float duration)
    {
        if (_currentRoutine != null) StopCoroutine(_currentRoutine);
        _currentRoutine = StartCoroutine(HitStopRoutine(duration));
    }

    private IEnumerator SlowRoutine(float scale, float duration)
    {
        Time.timeScale = scale;
        Time.fixedDeltaTime = 0.02f * scale;
        yield return new WaitForSecondsRealtime(duration); // unscaled 시간 기다림
        RestoreTimeScale();
    }

    private IEnumerator HitStopRoutine(float duration)
    {
        Time.timeScale = 0f;
        Time.fixedDeltaTime = 0f;
        yield return new WaitForSecondsRealtime(duration);
        RestoreTimeScale();
    }

    private void RestoreTimeScale()
    {
        Time.timeScale = _defaultTimeScale;
        Time.fixedDeltaTime = 0.02f * _defaultTimeScale;
        _currentRoutine = null;
    }
}
```

### 사용 예시
```csharp
// 패링 성공 시
TimeScaleManager.Instance.SlowMotion(0.15f, 0.12f);

// 보스 처치 시 드라마틱 슬로모
TimeScaleManager.Instance.SlowMotion(0.05f, 0.8f);

// 협공 Break 연출
TimeScaleManager.Instance.SlowMotion(0.2f, 0.15f);

// 피격 히트스톱 (0.05초 완전 정지)
TimeScaleManager.Instance.HitStop(0.05f);
```

### UI가 slowed되지 않게 하기
```csharp
// Animator가 timeScale을 따라가지 않게 설정 (UI 애니메이터)
animator.updateMode = AnimatorUpdateMode.UnscaledTime;

// UnscaledTime으로 트위닝 (DOTween)
DOTween.To(() => canvasGroup.alpha, x => canvasGroup.alpha = x, 1f, 0.3f)
       .SetUpdate(true); // SetUpdate(true) = unscaled time 사용
```

### 우선순위 충돌 방지
여러 이펙트가 동시에 timeScale을 바꾸려 할 때 스택 기반 관리:
```csharp
private readonly Stack<float> _scaleStack = new();

public void PushTimeScale(float scale)
{
    _scaleStack.Push(Time.timeScale);
    Time.timeScale = scale;
    Time.fixedDeltaTime = 0.02f * scale;
}

public void PopTimeScale()
{
    if (_scaleStack.Count > 0)
    {
        float prev = _scaleStack.Pop();
        Time.timeScale = prev;
        Time.fixedDeltaTime = 0.02f * prev;
    }
}
```

## OnionCat 적용 포인트

| 상황 | TimeScale | 지속시간 | 비고 |
|------|-----------|---------|------|
| 패링 성공(Crop) | 0.15 | 0.1s | Crop 효과음은 unscaled |
| 협공 Break | 0.2 | 0.15s | 파티클 동시 재생 |
| 보스 처치 | 0.05 | 0.8s | 카메라 줌인 + 슬로모 |
| Cat 피격 히트스톱 | 0.0 | 0.04s | 진동 피드백과 동시 |
| 게임오버 | 0.1 (점진적 감소) | 1.5s | 서서히 느려지다 정지 |

**주의 사항**:
- `WaitForSeconds` 는 timeScale의 영향을 받으므로 슬로모 중 Coroutine에는 반드시 `WaitForSecondsRealtime` 사용
- `AudioSource`의 `pitch`를 timeScale에 연동하면 슬로모 사운드 효과 (선택)
- `Time.fixedDeltaTime`을 timeScale과 함께 조정하지 않으면 물리 연산이 느려져 버그 발생

## 참고 링크

- Unity 공식 - Time.timeScale: https://docs.unity3d.com/ScriptReference/Time-timeScale.html
- Unity 공식 - Time.fixedDeltaTime: https://docs.unity3d.com/ScriptReference/Time-fixedDeltaTime.html
- Game Feel - Hit Stop 설계: https://www.gamedeveloper.com/design/making-hit-stop-feel-right-in-your-game
- DOTween SetUpdate 문서: http://dotween.demigiant.com/documentation.php
