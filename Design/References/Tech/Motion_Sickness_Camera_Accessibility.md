# 멀미 방지 카메라 접근성 설정

리서치 날짜: 2026-11-14

## 개요

화면 흔들림(Screen Shake)·크로마틱 어버레이션·모션 블러 등 카메라 연출이 **멀미나 광과민성 발작**을 유발할 수 있음. 최근 인디 게임도 접근성 옵션을 의무화하는 추세(EU 접근성법 2025, Nintendo 가이드라인 등). OnionCat처럼 타격감을 위해 화면 흔들림을 적극 사용하는 경우 반드시 On/Off 옵션이 필요.

## 멀미를 유발하는 주요 연출

| 연출 | 설명 | 위험도 |
|------|------|--------|
| 화면 흔들림 | 카메라 위치를 빠르게 진동 | ★★★ 높음 |
| 크로마틱 어버레이션 | RGB 채널 분리 — 가장자리 색분리 | ★★☆ 중간 |
| 모션 블러 | 빠른 움직임 흔림 | ★★☆ 중간 |
| 화면 플래시 | 흰/검정 순간 전환 | ★★★ 높음 (광과민) |
| 방사형 블러 | 화면 중심에서 퍼지는 흐림 | ★★★ 높음 |
| FOV 변화 | 줌인·줌아웃 충격 | ★☆☆ 낮음 (2D엔 무관) |

## Unity 구현 방법

### 1. 접근성 설정 저장 구조

```csharp
// 설정 저장 (PlayerPrefs or 커스텀 세이브)
public static class AccessibilitySettings
{
    public static float ScreenShakeIntensity
    {
        get => PlayerPrefs.GetFloat("ShakeIntensity", 1f);
        set { PlayerPrefs.SetFloat("ShakeIntensity", value); PlayerPrefs.Save(); }
    }
    public static bool ReduceFlash
    {
        get => PlayerPrefs.GetInt("ReduceFlash", 0) == 1;
        set { PlayerPrefs.SetInt("ReduceFlash", value ? 1 : 0); PlayerPrefs.Save(); }
    }
}
```

### 2. 화면 흔들림 강도 조절

```csharp
// Cinemachine CinemachineBasicMultiChannelPerlin 활용 예시
public class ScreenShakeManager : MonoBehaviour
{
    [SerializeField] CinemachineVirtualCamera vcam;
    CinemachineBasicMultiChannelPerlin noise;

    void Awake()
    {
        noise = vcam.GetCinemachineComponent<CinemachineBasicMultiChannelPerlin>();
    }

    public void Shake(float intensity, float duration)
    {
        // 사용자 설정으로 강도 보정
        float adjusted = intensity * AccessibilitySettings.ScreenShakeIntensity;
        if (adjusted < 0.01f) return; // 꺼진 경우 조기 종료

        StartCoroutine(DoShake(adjusted, duration));
    }

    IEnumerator DoShake(float intensity, float duration)
    {
        noise.m_AmplitudeGain = intensity;
        noise.m_FrequencyGain = 2f;
        yield return new WaitForSeconds(duration);
        noise.m_AmplitudeGain = 0;
    }
}
```

### 3. UI와 월드 흔들림 분리 (중요!)

```csharp
// 카메라 흔들림 → 월드 흔들림 (카메라에 붙은 HUD도 같이 흔들림)
// → HUD는 별도 Canvas로 카메라와 독립시켜야 멀미 감소

// Canvas 설정:
// - 월드 카메라 HUD: Canvas.renderMode = ScreenSpaceOverlay
//   (카메라 흔들림에 영향 없음)
// - 월드 카메라 HUD가 World Space라면 별도 카메라 레이어로 분리
```

### 4. URP Post Processing 접근성 토글

```csharp
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class PostProcessAccessibility : MonoBehaviour
{
    [SerializeField] Volume globalVolume;

    ChromaticAberration chromatic;
    MotionBlur motionBlur;

    void Start()
    {
        globalVolume.profile.TryGet(out chromatic);
        globalVolume.profile.TryGet(out motionBlur);
        Apply();
    }

    public void Apply()
    {
        float shake = AccessibilitySettings.ScreenShakeIntensity;

        if (chromatic != null)
            chromatic.active = shake > 0.1f; // 흔들림 꺼지면 색분리도 끔

        if (motionBlur != null)
            motionBlur.active = shake > 0.5f; // 50% 이상일 때만 모션블러
    }
}
```

### 5. 화면 플래시 감소

```csharp
// 피격·폭발 흰 플래시 연출 — ReduceFlash 옵션 적용
IEnumerator FlashEffect()
{
    if (AccessibilitySettings.ReduceFlash)
    {
        // 짧고 약하게: 20% 불투명도 / 0.05초
        yield return Flash(0.2f, 0.05f);
    }
    else
    {
        // 기본: 80% 불투명도 / 0.12초
        yield return Flash(0.8f, 0.12f);
    }
}
```

### 6. 설정 메뉴 UI 구성

```
[접근성]
● 화면 흔들림
  ○ 끔   ○ 약하게   ● 보통   ○ 강하게
  (슬라이더 0% ~ 100%)

● 화면 플래시 줄이기  [OFF] ←→ [ON]

● 크로마틱 어버레이션
  ● 보통  ○ 끔
```

## OnionCat 적용 포인트

### HitFeelSettings.asset 연동
현재 `HitFeelSettings.asset`에 흔들림 강도가 저장됨.  
→ 접근성 설정 배율(`ScreenShakeIntensity` 0.0~1.0)을 `HitFeelSettings` 값에 **곱해서** 출력.  
→ `HitFeelSettings`의 절대값을 바꾸지 말 것 — 디자이너가 튜닝한 기준값이 망가짐.

```csharp
// 예시: ScreenShaker.cs 에서
float finalIntensity = hitFeel.shakeIntensity * AccessibilitySettings.ScreenShakeIntensity;
```

### 설정 화면 위치
메인 메뉴 → 설정 → **접근성** 탭 (또는 기존 설정 탭 하단)에 추가.  
→ 중간 저장(런 중)에서도 일시정지 메뉴에서 변경 가능하게 (즉시 적용).

### 광과민성 경고
게임 첫 실행 시 짧은 경고 화면: "이 게임에는 화면 플래시 연출이 포함되어 있습니다."  
→ Content_Warning_Age_Rating_Screen.md 패턴 참고.

### 2인 접근성 고려
두 플레이어 중 한 명이 멀미에 민감할 수 있음.  
→ 흔들림 설정은 개인 설정이 아니라 **게임 전체 설정** (두 플레이어 모두에게 동일하게 적용).  
→ "더 약한 쪽에 맞추는" 원칙 UI 힌트 추가 고려: "민감한 플레이어 기준으로 설정하세요."

## 참고 링크

- Game Accessibility Guidelines: https://gameaccessibilityguidelines.com/full-list/
- Can I Play That (Photosensitivity 가이드): https://caniplaythat.com/2022/08/12/photosensitivity-in-games/
- Unity Cinemachine Noise: https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineBasicMultiChannelPerlin.html
- URP Post Processing Reference: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/post-processing/post-processing-index.html
