# Runtime Palette Swap System (런타임 팔레트 스왑)

리서치 날짜: 2026-08-31

## 개요

픽셀 아트 게임에서 스프라이트의 색상 팔레트를 런타임에 교체하는 기법.  
스프라이트 텍스처를 복사하지 않고 셰이더로 색상 LUT(Look-Up Table)을 교체해 메모리를 절약하면서 다양한 시각 변형을 표현.

**OnionCat에서의 필요성:**
- 업그레이드 획득 시 캐릭터 색상 변화로 강화 상태 표현
- 독/화염 등 상태이상 시 색조 변화 (빨간 틴트, 초록 틴트 등)
- 적 엘리트 변형 → 색상만 바꿔 재활용
- P1(고양이)와 P2(작물) 각각 독립 팔레트 운영

---

## Unity 구현 방법

### 방법 1: Custom URP Shader + MaterialPropertyBlock (권장)

**원리**: 스프라이트 원본 색상 (R, G, B)을 키로 사용해 교체 색상 LUT 텍스처를 샘플링.

#### 1단계 — 팔레트 LUT 텍스처 제작
- 1×N 픽셀 텍스처 (N = 팔레트 색상 수, 보통 4~16)
- 원본 팔레트와 교체 팔레트를 두 행으로 구성
- Filter Mode: **Point** (Pixel art 필수), Compression: **None**

#### 2단계 — URP 2D Shader Graph / HLSL Shader 작성

```hlsl
// PaletteSwap.shader (Sprite Unlit 기반)
Shader "OnionCat/PaletteSwap"
{
    Properties
    {
        _MainTex ("Sprite", 2D) = "white" {}
        _PaletteTex ("Palette LUT", 2D) = "white" {}
        _PaletteRow ("Palette Row (0=original, 1=swap)", Float) = 0
        _PaletteCount ("Total Rows", Float) = 2
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend SrcAlpha OneMinusSrcAlpha
        Cull Off ZWrite Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            struct Varyings { float4 positionHCS : SV_POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };

            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            TEXTURE2D(_PaletteTex); SAMPLER(sampler_PaletteTex);
            float _PaletteRow;
            float _PaletteCount;

            Varyings vert(Attributes IN)
            {
                Varyings OUT;
                OUT.positionHCS = TransformObjectToHClip(IN.positionOS.xyz);
                OUT.uv = IN.uv;
                OUT.color = IN.color;
                return OUT;
            }

            half4 frag(Varyings IN) : SV_Target
            {
                half4 col = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, IN.uv);
                if (col.a < 0.01) return col;

                // R 채널을 팔레트 인덱스로 사용 (0~1 범위)
                float idx = col.r;
                float2 lutUV = float2(idx, (_PaletteRow + 0.5) / _PaletteCount);
                half4 swapped = SAMPLE_TEXTURE2D(_PaletteTex, sampler_PaletteTex, lutUV);
                swapped.a = col.a;
                return swapped * IN.color;
            }
            ENDHLSL
        }
    }
}
```

#### 3단계 — C# 제어 스크립트

```csharp
using UnityEngine;

[RequireComponent(typeof(SpriteRenderer))]
public class PaletteSwapController : MonoBehaviour
{
    [SerializeField] private Texture2D paletteLUT;
    [SerializeField] private int defaultRow = 0;

    private SpriteRenderer _sr;
    private MaterialPropertyBlock _mpb;

    private static readonly int PaletteTex = Shader.PropertyToID("_PaletteTex");
    private static readonly int PaletteRow = Shader.PropertyToID("_PaletteRow");

    void Awake()
    {
        _sr = GetComponent<SpriteRenderer>();
        _mpb = new MaterialPropertyBlock();
        ApplyPalette(defaultRow);
    }

    public void ApplyPalette(int row)
    {
        _sr.GetPropertyBlock(_mpb);
        _mpb.SetTexture(PaletteTex, paletteLUT);
        _mpb.SetFloat(PaletteRow, row);
        _sr.SetPropertyBlock(_mpb);
    }

    // 상태이상 팔레트 (0=기본, 1=독, 2=화염, 3=업그레이드)
    public void SetPoisoned(bool on) => ApplyPalette(on ? 1 : 0);
    public void SetOnFire(bool on) => ApplyPalette(on ? 2 : 0);
    public void SetUpgraded() => ApplyPalette(3);
}
```

> **중요**: `MaterialPropertyBlock`을 사용하면 재질 인스턴스를 생성하지 않아 드로우콜 배칭 유지. `material.SetXxx()` 대신 이걸 써야 함.

---

### 방법 2: 단순 색조 오버레이 (Sprite Color)

팔레트 교체 없이 단순 색조 변경만 필요하면 `SpriteRenderer.color`로 충분:

```csharp
// 독 상태 — 초록 틴트
_sr.color = new Color(0.4f, 1f, 0.4f, 1f);

// 피격 플래시 — 흰색 틴트
_sr.color = Color.white;
```

단, 섬세한 픽셀아트 팔레트 제어에는 부적합.

---

### 방법 3: SpriteAtlas + 별도 텍스처

팔레트 변형 수가 적을 때 (2~3개), 텍스처 자체를 미리 여러 장 준비해두고 `Sprite` 교체.  
메모리 비용이 있지만 구현이 단순함.

---

## OnionCat 적용 포인트

### 팔레트 행 기획 (권장 구성)

| Row | 용도 | 트리거 |
|-----|------|--------|
| 0 | 기본 팔레트 | 평상시 |
| 1 | 피격 플래시 | 피해 받을 때 0.1초 |
| 2 | 독/저주 상태 | StatusEffect 활성 중 |
| 3 | 업그레이드 Tier 1 | 1회 강화 획득 후 |
| 4 | 업그레이드 Tier 2 | 2회 강화 획득 후 |
| 5 | 사망 직전 (HP 1) | 체력 임계값 도달 |

### 적 엘리트 변형에 재사용
`Enemy_Elite_Variant_System.md` 와 연계: 엘리트 적은 별도 스프라이트 없이 팔레트 Row 교체만으로 금색/은색/붉은 변형 표현. 메모리 절약 + 제작 공수 절감.

### P1(고양이) / P2(작물) 독립 팔레트
두 캐릭터가 하나의 GameObject를 공유하므로, 각각의 `SpriteRenderer`에 독립 `PaletteSwapController` 부착. P2 독 상태와 P1 강화 상태가 동시에 다른 색으로 표현 가능.

### Sprite 준비 규칙 (아티스트 가이드)
- 스프라이트 원본: **R 채널 = 팔레트 인덱스** (0~255를 색상 수로 나눈 값)
- 픽셀아트 색상을 4~8개로 제한하면 LUT 크기 최소화
- Import 설정: Filter Mode = **Point**, Compression = **None**, Generate Mip Maps = **Off**

---

## 주의사항

- `[SerializeField]` 변수: `paletteLUT` (Texture2D) → 유니티 에디터에서 드래그 앤 드롭 설정 필요
- 셰이더 교체 시 SpriteAtlas 배칭이 깨질 수 있음 → `MaterialPropertyBlock`으로 완화하지만 완전 방지 불가
- URP 2D Renderer 에서 `Sprite-Lit-Default` 기반으로 만들면 2D 조명 시스템과 호환

---

## 참고 링크

- Unity MaterialPropertyBlock 공식 문서: https://docs.unity3d.com/ScriptReference/MaterialPropertyBlock.html
- URP Shader Graph Custom Lit: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest
- 팔레트 스왑 Unity 튜토리얼 (Freya Holmér 기법): https://twitter.com/FreyaHolmer/status/1505944766891036675
- Palette Swapping in Unity (게임 개발 블로그): https://www.alanzucconi.com/2019/06/05/palette-swapping/
