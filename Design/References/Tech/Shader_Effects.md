# Shader Effects (Hit Flash & Outline)

리서치 날짜: 2026-06-23

## 개요
2D 픽셀아트 게임에서 타격감과 시각 피드백을 전달하는 핵심 셰이더 효과 3종:
- **Hit Flash**: 피격 순간 흰색/색상 번쩍임 → 타격감의 70%를 담당
- **Outline Shader**: 캐릭터 윤곽선 → 무적/파리 상태 강조
- **Dissolve Effect**: 사망 시 용해 → 자연스러운 제거 연출

OnionCat처럼 피드백이 전투 재미의 핵심인 게임에서는 셰이더 품질이 게임 느낌을 결정한다.

---

## Unity 구현 방법

### 사전 준비 (URP 2D 환경)
- URP 프로젝트 기준 (2D Renderer 사용)
- Window > Package Manager에서 **Shader Graph** 설치 확인
- 픽셀아트용 머티리얼: `Filter Mode = Point (no filter)`, `Compression = None`

---

### 1. Hit Flash Shader

#### Shader Graph 구성 (URP Sprite Lit / Sprite Unlit)
1. Create > Shader Graph > URP > **Sprite Lit Shader Graph** 생성
2. 노드 구성:
   ```
   [Texture 2D Property: _MainTex]
        ↓
   [Sample Texture 2D]
        ↓ (RGBA)
   [Lerp] ← [Float Property: _FlashAmount (0~1)]
        ↑
   [Color Property: _FlashColor (White)]
        ↓
   [Sprite Lit Master > Base Color]
   [Sample Texture 2D A] → [Sprite Lit Master > Alpha]
   ```
3. Save Asset → 머티리얼 생성 → SpriteRenderer에 적용

#### C# 제어 코드
```csharp
// HitFlashController.cs
public class HitFlashController : MonoBehaviour {
    [SerializeField] private SpriteRenderer spriteRenderer;
    [SerializeField] private float flashDuration = 0.1f;
    
    private static readonly int FlashAmountID = Shader.PropertyToID("_FlashAmount");
    private MaterialPropertyBlock mpb;
    
    private void Awake() {
        mpb = new MaterialPropertyBlock();
    }
    
    public void TriggerFlash() {
        StopAllCoroutines();
        StartCoroutine(FlashCoroutine());
    }
    
    private IEnumerator FlashCoroutine() {
        SetFlash(1f);
        yield return new WaitForSeconds(flashDuration);
        SetFlash(0f);
    }
    
    private void SetFlash(float value) {
        spriteRenderer.GetPropertyBlock(mpb);
        mpb.SetFloat(FlashAmountID, value);
        spriteRenderer.SetPropertyBlock(mpb);
    }
}
```

**MaterialPropertyBlock 사용 이유**: 같은 머티리얼을 공유하는 여러 스프라이트가 각자 독립된 플래시 타이밍을 가질 수 있음. `material.SetFloat`는 인스턴싱 방지로 드로우콜 증가.

---

### 2. Outline Shader (픽셀아트 윤곽선)

픽셀아트 윤곽선은 4방향(상하좌우) UV 오프셋 샘플링으로 구현.

#### Shader Graph 핵심 로직
```
// UV 오프셋 계산
float2 pixelSize = 1.0 / _MainTex_TexelSize.xy;  // 1픽셀 크기

// 4방향 샘플링 → 알파 합산
float up    = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv + float2(0, pixelSize.y)).a;
float down  = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv - float2(0, pixelSize.y)).a;
float left  = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv - float2(pixelSize.x, 0)).a;
float right = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv + float2(pixelSize.x, 0)).a;

float neighborAlpha = saturate(up + down + left + right);
float outline = step(0.1, neighborAlpha) * (1.0 - selfAlpha);  // 자신 외곽에만 적용

float4 finalColor = lerp(originalColor, _OutlineColor, outline * _OutlineEnabled);
```

#### Custom Function 노드 활용 (Shader Graph 내)
- Add Node > Custom Function > 위 HLSL 코드 삽입
- `_OutlineEnabled` (0 or 1), `_OutlineColor` 프로퍼티로 ON/OFF 제어

---

### 3. Dissolve Effect (사망 용해)

노이즈 텍스처의 값과 시간 기반 임계값 비교로 알파 컷오프.

```csharp
// DissolveController.cs
public class DissolveController : MonoBehaviour {
    [SerializeField] private SpriteRenderer spriteRenderer;
    [SerializeField] private float dissolveDuration = 0.8f;
    private static readonly int DissolveAmountID = Shader.PropertyToID("_DissolveAmount");
    private MaterialPropertyBlock mpb;
    
    private void Awake() => mpb = new MaterialPropertyBlock();
    
    public void StartDissolve(System.Action onComplete = null) {
        StartCoroutine(DissolveCoroutine(onComplete));
    }
    
    private IEnumerator DissolveCoroutine(System.Action onComplete) {
        float elapsed = 0f;
        while (elapsed < dissolveDuration) {
            elapsed += Time.deltaTime;
            float t = elapsed / dissolveDuration;
            spriteRenderer.GetPropertyBlock(mpb);
            mpb.SetFloat(DissolveAmountID, t);
            spriteRenderer.SetPropertyBlock(mpb);
            yield return null;
        }
        onComplete?.Invoke();
        gameObject.SetActive(false);
    }
}
```

Shader Graph에서:
1. Noise 텍스처(Gradient Noise 또는 심플 노이즈) 샘플링
2. `Step(noiseValue, _DissolveAmount)` → 0이 되는 픽셀은 알파 0
3. 경계선 근처에 발광색(Emission) 추가 시 더 화려한 효과

---

### 통합 예시: 피격 시 자동 처리
```csharp
// EnemyDamageable.cs
public void TakeDamage(int amount) {
    hp -= amount;
    hitFlash.TriggerFlash();  // 즉시 플래시
    
    if (hp <= 0) {
        dissolve.StartDissolve(() => Destroy(gameObject));
    }
}
```

---

## OnionCat 적용 포인트

1. **Cat vs Crop 피격 색상 구분**
   - Cat 피격: 빨간 플래시 → 물리적 위험감
   - Crop 피격: 파란 플래시 → 다른 캐릭터임을 직관적으로 인식

2. **Crop 패리 성공 연출**
   - 패리 성공 → 흰색 플래시 + 1프레임 아웃라인 Glow → 강렬한 보상감
   - `_FlashColor`를 황금색으로 → 성공 피드백 구분

3. **Cat 대시 무적 상태 표시**
   - 대시 중: `_OutlineEnabled = 1`, 반투명(`SpriteRenderer.color.a = 0.6f`) 조합
   - 무적 종료 시 아웃라인 즉시 OFF

4. **적 사망 연출 통일**
   - 모든 적에 Dissolve 적용 → 죽음이 명확히 보임 (픽셀아트에서 즉사 사라짐은 허전함)

5. **성능 고려**
   - `MaterialPropertyBlock` 반드시 사용 → SpriteRenderer 배칭 유지
   - Dissolve용 Noise 텍스처는 1개 공유 (머티리얼 프로퍼티로)

---

## 참고 링크
- Unity Shader Graph 공식: https://docs.unity3d.com/Packages/com.unity.shadergraph@latest
- URP 2D Renderer 문서: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest
- MaterialPropertyBlock 문서: https://docs.unity3d.com/ScriptReference/MaterialPropertyBlock.html
- Brackeys - Hit Flash Tutorial: https://www.youtube.com/watch?v=LnAoD7hgDxw
- Unity Learn - Shader Graph 2D: https://learn.unity.com/tutorial/introduction-to-shader-graph
