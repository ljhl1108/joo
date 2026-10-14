# URP 2D Post-Processing Game Feel System

리서치 날짜: 2026-10-14

## 개요

피격·치유·사망·보스 등장 같은 중요한 게임 이벤트에 맞춰 **화면 전체에 시각적 반응**을 주는 시스템.
Unity URP의 Post-Processing Volume, Custom 2D Renderer Feature, 그리고 간단한 Fullscreen Shader를 이용해
게임 이벤트가 "화면 전체로 울린다"는 느낌을 만든다.

OnionCat에서 필요한 이유:
- 공유 체력이 낮아질수록 화면이 위험해 보여야 한다 (빨간 비네트)
- 회복 아이템 사용 시 "좋아지는 느낌"을 즉각 전달 (초록 플래시)
- 킥 콤보·합동기 같은 하이라이트 순간이 더 임팩트 있어야 한다 (슬로모션 + 블룸)
- 보스 등장 순간 분위기 전환 (블랙아웃 → 드라마틱 등장)

---

## Unity 구현 방법

### 1. URP 2D Post-Processing Volume 설정

**패키지 확인**: Universal RP에서 Post Processing은 기본 포함. `Edit > Project Settings > Quality > URP Asset`에서 Post Processing 활성화.

```csharp
// 씬에 Global Volume 배치 후 Volume Profile에 아래 효과 추가
// - Vignette
// - Bloom
// - Color Adjustments
// - Chromatic Aberration
// - Lift Gamma Gain
```

**Volume 컴포넌트 런타임 제어**:
```csharp
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class PostProcessGameFeel : MonoBehaviour
{
    [SerializeField] private Volume _volume;
    
    private Vignette _vignette;
    private Bloom _bloom;
    private ColorAdjustments _colorAdj;
    private ChromaticAberration _chromatic;

    void Awake()
    {
        _volume.profile.TryGet(out _vignette);
        _volume.profile.TryGet(out _bloom);
        _volume.profile.TryGet(out _colorAdj);
        _volume.profile.TryGet(out _chromatic);
    }

    // HP 비율에 따라 비네트 강도 실시간 반영
    public void SetDangerLevel(float hpRatio)
    {
        // hpRatio: 1.0 = 풀HP, 0.0 = 사망직전
        if (_vignette != null)
        {
            float targetIntensity = Mathf.Lerp(0.55f, 0.0f, hpRatio);
            _vignette.intensity.Override(targetIntensity);
            _vignette.color.Override(Color.red);
        }
    }
}
```

### 2. 이벤트별 FlashEffect 코루틴

```csharp
public class PostProcessGameFeel : MonoBehaviour
{
    // 피격: 붉은 비네트 펄스
    public void OnDamageReceived()
    {
        StartCoroutine(VignettePulse(Color.red, 0.6f, 0.15f));
        StartCoroutine(ChromaticAberrationPulse(0.8f, 0.1f));
    }

    // 회복: 초록 화면 플래시
    public void OnHealReceived()
    {
        StartCoroutine(ColorGradePulse(new Color(0.5f, 1.0f, 0.5f), 0.3f, 0.25f));
    }

    // 합동기: 블룸 + 슬로모션
    public void OnJointAttack()
    {
        StartCoroutine(BloomSurge(3.0f, 0.4f));
        Time.timeScale = 0.3f;
        DOTween.To(() => Time.timeScale, x => Time.timeScale = x, 1.0f, 0.5f)
               .SetUpdate(true);
    }

    private IEnumerator VignettePulse(Color color, float intensity, float duration)
    {
        if (_vignette == null) yield break;
        _vignette.color.Override(color);
        _vignette.intensity.Override(intensity);
        yield return new WaitForSecondsRealtime(duration);
        // 기존 danger level로 복귀는 SetDangerLevel이 처리
        _vignette.intensity.Override(_currentDangerVignette);
    }

    private IEnumerator BloomSurge(float targetThreshold, float duration)
    {
        if (_bloom == null) yield break;
        float start = _bloom.threshold.value;
        float t = 0f;
        while (t < duration)
        {
            t += Time.unscaledDeltaTime;
            _bloom.threshold.Override(Mathf.Lerp(start, targetThreshold, t / duration));
            yield return null;
        }
        _bloom.threshold.Override(start);
    }

    private IEnumerator ChromaticAberrationPulse(float intensity, float duration)
    {
        if (_chromatic == null) yield break;
        _chromatic.intensity.Override(intensity);
        yield return new WaitForSecondsRealtime(duration);
        _chromatic.intensity.Override(0f);
    }

    private IEnumerator ColorGradePulse(Color tint, float intensity, float duration)
    {
        if (_colorAdj == null) yield break;
        _colorAdj.colorFilter.Override(tint);
        float t = 0f;
        while (t < duration)
        {
            t += Time.unscaledDeltaTime;
            _colorAdj.colorFilter.Override(Color.Lerp(tint, Color.white, t / duration));
            yield return null;
        }
        _colorAdj.colorFilter.Override(Color.white);
    }
}
```

### 3. 보스 등장 연출 (블랙아웃 + 드라마틱 스케일)

```csharp
// Fullscreen black panel (Canvas) + DOTween
public IEnumerator BossEntrance()
{
    // 1. 블랙아웃
    yield return blackPanel.DOFade(1f, 0.5f).WaitForCompletion();
    
    // 2. 보스 배치 (카메라 컷)
    CameraManager.Instance.MoveToBoss();
    
    // 3. 블룸 서지 + 컬러 그레이딩 (분위기 전환)
    _colorAdj.saturation.Override(-50f); // 탈색으로 긴장감
    
    // 4. 페이드인
    yield return blackPanel.DOFade(0f, 0.8f).WaitForCompletion();
    
    // 5. 보스 BGM 시작
    Music.Play(MusicId.Boss);
    
    // 6. 컬러 정상화
    DOTween.To(() => _colorAdj.saturation.value,
               x => _colorAdj.saturation.Override(x), 0f, 1.0f);
}
```

### 4. 위험 상태 실시간 비네트 (GameManager 연결)

```csharp
// HUD나 GameManager에서 HP 변화마다 호출
void OnHPChanged(int current, int max)
{
    float ratio = (float)current / max;
    postProcessFeel.SetDangerLevel(ratio);
    
    // HP 20% 이하: 심박수처럼 비네트가 맥박 침
    if (ratio < 0.2f && !_isHeartbeatActive)
        StartCoroutine(HeartbeatVignette());
}

private IEnumerator HeartbeatVignette()
{
    _isHeartbeatActive = true;
    while (PlayerHealth.HPRatio < 0.2f)
    {
        _vignette.intensity.Override(0.65f);
        yield return new WaitForSecondsRealtime(0.1f);
        _vignette.intensity.Override(0.45f);
        yield return new WaitForSecondsRealtime(0.4f);
    }
    _isHeartbeatActive = false;
}
```

### 5. Volume Profile 분리 (씬별 기본 분위기)

- `VolumeProfile_Default.asset`: 기본 게임플레이용 (낮은 비네트, 기본 컬러)
- `VolumeProfile_Boss.asset`: 보스전용 (채도 약간 낮춤, 대비 높임)
- `VolumeProfile_Shop.asset`: 상점·허브 (따뜻한 컬러 그레이딩)

```csharp
// 씬 전환 시 Volume Profile 교체
_volume.profile = newProfile;
```

---

## OnionCat 적용 포인트

### 즉시 구현 가능한 것 (우선순위 순)

1. **피격 비네트 펄스** — `OnDamageReceived()` 연결 (CoreHUD 또는 PlayerHealth)
   - 설정값: 빨간 비네트 0.6, 지속 0.15초
   - 효과: 피격이 화면 전체로 전달됨

2. **HP 비례 위험 비네트** — `OnHPChanged()` 연결
   - HP 100%: 비네트 0 / HP 0%: 비네트 0.55 (빨간)
   - HP 20% 이하: 심박수 맥박 효과
   - 설정값은 `HitFeelSettings.asset`에 추가 권장

3. **합동기 블룸 서지** — 합동기 발동 연결
   - 블룸 임계값을 0.5초간 높였다가 복귀
   - 약한 슬로모션 (0.3배, 0.5초) 추가 시 극적 효과

4. **회복 플래시** — 가방 회복 아이템 사용 연결
   - 초록 컬러 필터 0.25초 → 플레이어에게 "좋아졌다" 신호

5. **킥 콤보 Chromatic Aberration** — KICK COMBO 판정 시
   - 색수차 0.8, 0.1초 → 임팩트 강조

### 주의사항 (OnionCat 특이사항)

- `Time.timeScale`을 직접 바꾸면 안 됨 (`GameManager.ChangeState` 규칙) → 슬로모션은 `DOTween.SetUpdate(true)` + `Time.timeScale` 직접 조작 제한적 허용 (연출 목적 단기간)
- Post-processing Volume은 씬에 하나만 두고 `PostProcessGameFeel` 싱글톤이 관리
- 픽셀아트이므로 Bloom 임계값은 높게 (0.8+) 유지해야 픽셀이 뭉개지지 않음
- 모든 강도 수치는 `HitFeelSettings.asset`에서 Inspector 조절 가능하게

---

## 참고 링크

- Unity URP Post-Processing Volume 공식 문서: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/EffectList.html
- Unity URP 2D Renderer Feature 가이드: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/2DRendererData_overview.html
- DOTween 공식: http://dotween.demigiant.com/
- "Game Feel" 참고서: 《Game Feel》 by Steve Swink — 피드백 시스템 설계의 바이블
- Unity Game Feel 사례 (Unite Talk): https://www.youtube.com/watch?v=Tz0qLnkbxnc
