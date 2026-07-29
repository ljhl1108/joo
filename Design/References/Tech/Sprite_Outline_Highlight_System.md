# Sprite Outline / Highlight Shader System (스프라이트 아웃라인 강조 시스템)

리서치 날짜: 2026-07-29

## 개요

스프라이트 주변에 테두리(아웃라인)를 그리는 시각 효과 시스템. 2D 액션 게임에서 거의 필수적으로 사용된다.

**OnionCat에서 필요한 이유:**
- 플레이어(Cat+Crop)가 복잡한 배경에서도 눈에 띄어야 함
- Crop의 방패 활성화 → 방패 방향 하이라이트 피드백
- 근접 약점 적 vs 원거리 약점 적을 색깔 아웃라인으로 구분
- 상호작용 가능한 오브젝트(아이템, 문) 근처 접근 시 강조
- Cat의 패리 성공 시 번쩍이는 흰색 아웃라인 피드백

---

## Unity 구현 방법

### 방법 1: URP 2D Renderer Feature + Custom Shader (권장)

**원리:**
스프라이트 텍스처의 알파 채널을 8방향으로 약간 offset하여 샘플링 → 원본 픽셀과 비교 → 차이가 생기는 경계 부분에 색상 채움

**1단계: 아웃라인 셰이더 생성**

`Assets/Shaders/SpriteOutline.shader` 생성:

```hlsl
Shader "Custom/SpriteOutline"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _OutlineColor ("Outline Color", Color) = (1,1,1,1)
        _OutlineSize ("Outline Size", Float) = 1.0
        _OutlineEnabled ("Outline Enabled", Float) = 1.0
    }
    
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha
        
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            
            sampler2D _MainTex;
            float4 _MainTex_ST;
            float4 _MainTex_TexelSize;
            float4 _OutlineColor;
            float _OutlineSize;
            float _OutlineEnabled;
            
            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            struct v2f { float4 vertex : SV_POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            
            v2f vert(appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.color = v.color;
                return o;
            }
            
            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv) * i.color;
                
                if (_OutlineEnabled < 0.5) return col;
                
                // 8방향 샘플링으로 아웃라인 감지
                float2 offset = _MainTex_TexelSize.xy * _OutlineSize;
                float alpha = col.a;
                alpha = max(alpha, tex2D(_MainTex, i.uv + float2( offset.x, 0)).a);
                alpha = max(alpha, tex2D(_MainTex, i.uv + float2(-offset.x, 0)).a);
                alpha = max(alpha, tex2D(_MainTex, i.uv + float2(0,  offset.y)).a);
                alpha = max(alpha, tex2D(_MainTex, i.uv + float2(0, -offset.y)).a);
                alpha = max(alpha, tex2D(_MainTex, i.uv + float2( offset.x,  offset.y)).a);
                alpha = max(alpha, tex2D(_MainTex, i.uv + float2(-offset.x,  offset.y)).a);
                alpha = max(alpha, tex2D(_MainTex, i.uv + float2( offset.x, -offset.y)).a);
                alpha = max(alpha, tex2D(_MainTex, i.uv + float2(-offset.x, -offset.y)).a);
                
                // 아웃라인 영역(원본 알파=0, 확장 알파>0)에 색 채우기
                if (col.a < 0.01 && alpha > 0.01)
                    return float4(_OutlineColor.rgb, _OutlineColor.a);
                
                return col;
            }
            ENDHLSL
        }
    }
}
```

**2단계: Material 생성**
1. `Assets/Materials/` 폴더에 Material 생성
2. Shader를 `Custom/SpriteOutline`으로 지정
3. SpriteRenderer의 Material을 이 Material로 교체

**3단계: 런타임 제어 스크립트**

```csharp
using UnityEngine;

public class SpriteOutlineController : MonoBehaviour
{
    [SerializeField] private SpriteRenderer spriteRenderer;
    [SerializeField] private Color defaultOutlineColor = Color.white;
    
    private Material material;
    private static readonly int OutlineColor = Shader.PropertyToID("_OutlineColor");
    private static readonly int OutlineEnabled = Shader.PropertyToID("_OutlineEnabled");
    private static readonly int OutlineSize = Shader.PropertyToID("_OutlineSize");
    
    private void Awake()
    {
        if (spriteRenderer == null) spriteRenderer = GetComponent<SpriteRenderer>();
        // MaterialPropertyBlock으로 인스턴스별 제어 (드로우콜 공유 유지)
        material = spriteRenderer.material; // 인스턴스 복사
    }
    
    public void ShowOutline(Color color, float size = 1f)
    {
        material.SetFloat(OutlineEnabled, 1f);
        material.SetColor(OutlineColor, color);
        material.SetFloat(OutlineSize, size);
    }
    
    public void HideOutline()
    {
        material.SetFloat(OutlineEnabled, 0f);
    }
    
    public void FlashOutline(Color color, float duration)
    {
        StartCoroutine(FlashRoutine(color, duration));
    }
    
    private System.Collections.IEnumerator FlashRoutine(Color color, float duration)
    {
        ShowOutline(color);
        yield return new WaitForSeconds(duration);
        HideOutline();
    }
}
```

---

### 방법 2: MaterialPropertyBlock (성능 최적화 버전)

위 방법에서 `spriteRenderer.material`은 Material을 복사해 드로우콜이 늘어난다.
적이 많을 때는 `MaterialPropertyBlock` 사용:

```csharp
private MaterialPropertyBlock mpb;

private void Awake()
{
    mpb = new MaterialPropertyBlock();
}

public void ShowOutline(Color color)
{
    spriteRenderer.GetPropertyBlock(mpb);
    mpb.SetFloat(OutlineEnabled, 1f);
    mpb.SetColor(OutlineColor, color);
    spriteRenderer.SetPropertyBlock(mpb);
}
```

> ⚠️ `MaterialPropertyBlock`은 같은 Material이면 배칭이 깨지지 않아 드로우콜 절약. 적이 5~6마리 이상이라면 반드시 이 방식 사용.

---

### 방법 3: URP 2D Renderer Feature (전체 오브젝트 외곽선)

캐릭터/적 주변을 스프라이트 텍스처 경계가 아닌 **오브젝트 실루엣** 기준으로 그릴 때.

1. URP 2D Renderer 에셋 선택 → Renderer Features 탭
2. `Add Renderer Feature` → `2D Light` 또는 커스텀 ScriptableRendererFeature 추가
3. 스텐실 버퍼를 이용해 오브젝트를 마스킹 → 주변에 팽창된 컬러 렌더링

---

## OnionCat 적용 포인트

### Cat/Crop 기본 하이라이트
- **Cat**: 기본 흰색 아웃라인 → 배경과 분리
- **Crop**: 기본 연두색/파란색 아웃라인 → 두 캐릭터 시각 구분

### 파리/패리 성공 피드백
```csharp
// Crop의 패리 성공 시
outlineController.FlashOutline(Color.yellow, 0.15f);
// Cat의 대시 무적 구간
outlineController.ShowOutline(new Color(0.5f, 0.5f, 1f, 0.8f));
```

### 적 약점 표시
```csharp
public enum EnemyWeakness { Melee, Ranged, None }

void UpdateOutlineByWeakness(EnemyWeakness weakness)
{
    switch (weakness)
    {
        case EnemyWeakness.Melee:  outlineController.ShowOutline(Color.red);    break;  // Cat 타깃
        case EnemyWeakness.Ranged: outlineController.ShowOutline(Color.cyan);   break;  // Crop 타깃
        case EnemyWeakness.None:   outlineController.HideOutline();             break;
    }
}
```

### 아이템/상호작용 오브젝트 접근 감지
```csharp
// 아이템에 부착, Cat이 일정 거리 이내로 접근 시
void OnTriggerEnter2D(Collider2D col)
{
    if (col.CompareTag("Player"))
        outlineController.ShowOutline(Color.yellow, 1.5f);  // 굵은 노란 아웃라인
}

void OnTriggerExit2D(Collider2D col)
{
    if (col.CompareTag("Player"))
        outlineController.HideOutline();
}
```

---

## 참고 링크

- Unity 공식 URP Shader Graph 가이드: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest
- YouTube: "Unity 2D Outline Shader Tutorial" (Brackeys, Mix and Jam 등 다수)
- Unity Forum: https://forum.unity.com/threads/2d-sprite-outline-shader.html
- MaterialPropertyBlock 공식 문서: https://docs.unity3d.com/ScriptReference/MaterialPropertyBlock.html
- Sprite Outline Asset (유료 대안): Unity Asset Store "Sprite Outline" 검색
