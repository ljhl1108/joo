# 픽셀아트 렌더링 셋업 (Pixel Art Rendering Setup)

리서치 날짜: 2026-06-16

## 개요

Unity에서 픽셀아트 게임을 만들 때 기본 설정을 잘못하면 스프라이트가 흐릿하게 보이거나, 카메라 이동 시 픽셀이 흔들리는 "서브픽셀 지터" 현상이 발생한다. OnionCat은 픽셀아트 스타일이므로 프로젝트 초기에 올바른 렌더링 설정을 구축하는 것이 필수다.

---

## Unity 구현 방법

### 1. 스프라이트 임포트 설정

스프라이트를 임포트할 때 Inspector에서 반드시:
- **Filter Mode**: `Point (no filter)` — 흐릿함 방지
- **Compression**: `None` — 픽셀아트는 압축 금지
- **Pixels Per Unit (PPU)**: 스프라이트 해상도에 맞게 설정 (예: 16x16 스프라이트 → PPU=16)
- **Format**: `RGBA 32 bit` (투명도 포함 스프라이트)

```
// 에디터 자동화: Assets > Create > Preset으로 임포트 프리셋 저장 가능
// 폴더별 프리셋 적용 → 새 스프라이트 자동으로 올바른 설정 적용
```

### 2. Pixel Perfect Camera 설정

`2D Pixel Perfect` 패키지 설치 후 Main Camera에 `Pixel Perfect Camera` 컴포넌트 추가:

```
Assets Per Unit (APU): 스프라이트 PPU와 동일하게
Reference Resolution: 게임의 기준 해상도 (예: 320x180 = 16:9 픽셀아트)
Crop Frame: X, Y 체크 (해상도 비율 유지)
Stretch Fill: 해제 (픽셀 정수 배율만 사용)
```

**핵심 원리**: Pixel Perfect Camera는 카메라 위치를 자동으로 픽셀 그리드에 스냅해서 서브픽셀 지터를 제거한다.

### 3. URP(Universal Render Pipeline) 픽셀아트 설정

`UniversalRenderPipelineAsset`에서:
- **Render Scale**: `1.0` (낮추면 블러 발생)
- **Anti-aliasing**: 비활성화 (픽셀아트에선 MSAA 불필요)
- **Post Processing**: 활성화하되 Bloom/DOF는 픽셀 느낌 해칠 수 있으므로 신중하게

**URP로 픽셀 느낌 강화하는 포스트 프로세싱**:
```
// Volume 컴포넌트 → Add Override
- Color Adjustments: Contrast +20, Saturation +10 (채도 강조)
- Vignette: 약하게 → 화면 가장자리 어둡게
- Bloom은 끄거나 Threshold 매우 높게 (1.5 이상)
```

### 4. 카메라 해상도 전략

픽셀아트 게임의 두 가지 해상도 전략:

**전략 A: 저해상도 렌더 → 업스케일**
```
// RenderTexture 생성 (예: 320x180)
// Camera → Output → Target Texture = 위 텍스처
// UI Canvas (Screen Space - Camera)에 Raw Image로 표시 후 확대
장점: 완벽한 픽셀 일관성
단점: UI 설정 복잡
```

**전략 B: Pixel Perfect Camera 사용 (권장)**
```
// 2D Pixel Perfect 패키지 → Pixel Perfect Camera 컴포넌트
// 간단하고 Unity 공식 지원
// Cinemachine과 호환됨
```

### 5. Sorting Layer & Order 설정

```
Sorting Layer 예시 (아래에서 위 순서로 렌더):
1. Background      (배경 타일)
2. BackDecoration  (배경 소품)
3. Ground          (바닥 위 오브젝트)
4. Player          (플레이어)
5. Enemy           (적)
6. Projectile      (투사체)
7. Effect          (이펙트/파티클)
8. UI              (게임 내 UI)
```

### 6. 히트 플래시 / 색상 변경 효과

픽셀아트에서 피격 시 흰색 깜빡임 구현:

```csharp
// SpriteRenderer의 Material을 교체하는 방식
public class HitFlash : MonoBehaviour
{
    [SerializeField] private Material flashMaterial;  // "Sprites/Flash" 셰이더
    [SerializeField] private float flashDuration = 0.1f;
    
    private SpriteRenderer sr;
    private Material originalMaterial;
    
    private void Awake()
    {
        sr = GetComponent<SpriteRenderer>();
        originalMaterial = sr.material;
    }
    
    public void Flash()
    {
        StartCoroutine(FlashCoroutine());
    }
    
    private IEnumerator FlashCoroutine()
    {
        sr.material = flashMaterial;
        yield return new WaitForSeconds(flashDuration);
        sr.material = originalMaterial;
    }
}
```

**Flash Material 만들기**: Assets > Create > Material → Shader를 `Sprites/Flash` (커스텀 셰이더) 또는 `Sprites/Default`에서 Color를 흰색으로 설정.

### 7. 픽셀아트 전용 셰이더 (선택)

간단한 아웃라인 셰이더 (외곽선 표시, 선택된 적 강조 등):
```
// ShaderGraph 사용:
// SampleTexture2D → Alpha → Step(0.5) → 외곽 4방향 샘플링 → 합산
// 단순하게는 Material Property '_OutlineColor' 설정으로 구현
```

---

## OnionCat 적용 포인트

### 1. 프로젝트 초기 설정 체크리스트
- [ ] `2D Pixel Perfect` 패키지 설치 (Package Manager)
- [ ] Main Camera에 `Pixel Perfect Camera` 추가
- [ ] 기준 해상도 결정 (권장: **320×180** — 인디 픽셀아트 표준)
- [ ] 모든 스프라이트 PPU 통일 (권장: **16PPU** for 16px 타일)
- [ ] 스프라이트 임포트 프리셋 생성 (Filter Mode: Point, Compression: None)

### 2. Cat + Onion 스프라이트 일관성
- Cat과 Onion이 같은 바디를 공유 → 두 캐릭터의 PPU를 반드시 동일하게 설정
- 플레이어 레이어 위에 Onion(화분) 렌더링: `Player` 레이어보다 `Order in Layer` +1

### 3. 피격 피드백
- Cat 피격 시 Cat 스프라이트 히트 플래시
- Onion 피격 시 화분+양파 스프라이트 히트 플래시
- 두 레이어가 별도 SpriteRenderer이므로 독립적으로 Flash 적용 가능

### 4. 기준 해상도 권장
```
320 × 180 (16:9) — 1080p에서 6배 배율로 정확히 맞음
256 × 144 (16:9) — 더 복고적인 느낌, 7.5배
480 × 270 (16:9) — 좀 더 넓은 화면 (4배 배율 at 1080p)
```

---

## 참고 링크

- Unity Pixel Perfect Camera 공식 문서: https://docs.unity3d.com/Packages/com.unity.2d.pixel-perfect@5.0/manual/index.html
- Unity 2D Pixel Perfect 패키지: https://docs.unity3d.com/Manual/com.unity.2d.pixel-perfect.html
- Brackeys - How to make a Pixel Art game in Unity: https://www.youtube.com/watch?v=whzomFgjT50
- 픽셀아트 해상도 가이드: https://www.pixelprospector.com/the-big-list-of-indie-game-marketing/#pixelart
