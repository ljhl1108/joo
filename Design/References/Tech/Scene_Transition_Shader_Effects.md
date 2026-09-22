# Scene Transition Shader Effects (씬 전환 셰이더 효과)

리서치 날짜: 2026-09-22

## 개요

기본 페이드 인/아웃 대신 픽셀아트 로그라이크에 어울리는 셰이더 기반 전환 효과.
OnionCat의 룸 이동, 층 클리어, 게임오버, 런 시작 등 각 시점마다 다른 연출을 줄 수 있다.
Unity URP 2D + Shader Graph 또는 커스텀 HLSL로 구현.

---

## 주요 전환 효과 종류

| 효과 | 사용 시점 | 구현 난이도 |
|------|----------|-----------|
| 픽셀 디졸브 (Pixel Dissolve) | 룸 이동 | ★★☆ |
| 아이리스 와이프 (Iris Wipe) | 게임오버 / 씬 시작 | ★★☆ |
| 픽셀 박살 (Pixel Shatter) | 보스 처치 후 | ★★★ |
| 수평 스윕 (Horizontal Sweep) | 층 전환 | ★☆☆ |
| 화이트아웃 플래시 | 데미지 피격 | ★☆☆ |

---

## Unity 구현 방법

### 방법 A: Full-Screen Pass Renderer Feature (URP 권장)

URP에서 전체화면 셰이더를 적용하려면 `Full Screen Pass Renderer Feature`를 사용.

**1. Renderer Feature 추가**
- Project Settings → Graphics → URP Asset → Renderer
- Add Renderer Feature → "Full Screen Pass Renderer Feature"
- Material: 전환 셰이더 머티리얼 할당

**2. 디졸브 셰이더 (Shader Graph)**
```
- Time 노드 → Lerp 노드 → Alpha Clip
- Noise Texture (퍼린 노이즈) → Step → Alpha
- _Progress 파라미터 (0→1): C#에서 제어
```

**3. C# 전환 컨트롤러**

```csharp
public class TransitionController : MonoBehaviour {
    [SerializeField] private Material transitionMaterial;
    private static readonly int ProgressId = Shader.PropertyToID("_Progress");

    public IEnumerator PlayTransition(float duration = 0.4f) {
        float t = 0;
        while (t < 1f) {
            t += Time.unscaledDeltaTime / duration;
            transitionMaterial.SetFloat(ProgressId, t);
            yield return null;
        }
        transitionMaterial.SetFloat(ProgressId, 1f);
    }

    public IEnumerator ReverseTransition(float duration = 0.4f) {
        float t = 1f;
        while (t > 0f) {
            t -= Time.unscaledDeltaTime / duration;
            transitionMaterial.SetFloat(ProgressId, t);
            yield return null;
        }
        transitionMaterial.SetFloat(ProgressId, 0f);
    }
}
```

### 방법 B: UI RawImage (간단한 대안, URP Blit 불필요)

화면 위에 Canvas → RawImage를 덮어씌우고, 해당 Image의 머티리얼에 셰이더 적용.
- Canvas Sort Order: 최상위
- RawImage → Material: 전환 셰이더
- Alpha 대신 `_Progress` 파라미터로 제어

```csharp
public class UITransitionOverlay : MonoBehaviour {
    [SerializeField] private RawImage overlay;
    private Material mat;

    void Awake() {
        mat = overlay.material = Instantiate(overlay.material);
    }

    public IEnumerator FadeOut(float dur = 0.3f) {
        float t = 0;
        while (t < 1f) {
            t += Time.unscaledDeltaTime / dur;
            mat.SetFloat("_Progress", t);
            yield return null;
        }
    }
}
```

### 아이리스 와이프 셰이더 (HLSL 핵심 로직)

```hlsl
// iris_wipe.hlsl
float2 uv = IN.texcoord - 0.5;          // 화면 중앙 기준
float dist = length(uv);                 // 중심에서 거리
float radius = lerp(1.0, 0.0, _Progress); // 0→1로 좁아짐
float mask = step(dist, radius);         // 원 안 = 1, 밖 = 0
// mask == 0인 픽셀을 검정으로 치환
```

### 픽셀 디졸브 셰이더 핵심

```hlsl
// pixel_dissolve.hlsl
float2 pixelUV = floor(IN.texcoord * _PixelCount) / _PixelCount;
float noise = tex2D(_NoiseTex, pixelUV).r;  // 노이즈 텍스처
clip(noise - _Progress);                     // _Progress 이하 픽셀 잘라냄
```

---

## OnionCat 적용 포인트

### 시점별 효과 매핑

| 게임 이벤트 | 권장 효과 | 파라미터 |
|-----------|----------|---------|
| 방 이동 | 픽셀 디졸브 | duration: 0.3s |
| 층 클리어 / 다음 층 | 수평 스윕 | duration: 0.5s |
| 게임오버 | 아이리스 와이프 (닫힘) | duration: 0.8s |
| 런 시작 | 아이리스 와이프 (열림) | duration: 0.5s |
| 보스 처치 | 화이트 플래시 → 페이드아웃 | 0.1s + 0.5s |

### GameManager와 연동

```csharp
// GameManager.cs의 ChangeState() 내부에서 호출
async void ChangeState(GameState next) {
    if (ShouldPlayTransition(next)) {
        await transitionCtrl.PlayTransition();
    }
    currentState = next;
    OnStateChanged?.Invoke(next);
    // ...씬 전환 등 실행...
    await transitionCtrl.ReverseTransition();
}
```

### 픽셀아트와 어울리는 설정
- 노이즈 텍스처는 **저해상도 (64×64) Bayer 디더** 패턴 사용 → 픽셀아트 느낌
- Filter Mode: **Point (No Filter)** 필수
- PPU 32에 맞게 `_PixelCount = Screen.height / 32` 계산

### Time.unscaledDeltaTime 필수
일시정지(Time.timeScale=0) 중에도 전환 애니메이션이 재생되어야 하므로 반드시
`Time.unscaledDeltaTime` 사용.

---

## 참고 링크

- URP Full Screen Pass Renderer Feature: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@17.0/manual/renderer-features/renderer-feature-full-screen-pass.html
- Unity Shader Graph 공식: https://docs.unity3d.com/Manual/com.unity.shadergraph.html
- Iris Wipe 튜토리얼: YouTube "Unity iris wipe shader" 검색
- 픽셀아트 디졸브: YouTube "Unity pixel dissolve transition" 검색
- Bayer Dither 패턴 생성: https://en.wikipedia.org/wiki/Ordered_dithering
