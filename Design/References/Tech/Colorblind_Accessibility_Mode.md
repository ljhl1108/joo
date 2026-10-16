# Colorblind Accessibility Mode

리서치 날짜: 2026-10-16

## 개요

색맹·색약 플레이어를 위한 접근성 옵션. 전 세계 남성의 약 8%, 여성의 약 0.5%가 색각 이상을 가짐.
픽셀아트 게임에서 색으로만 구분하는 정보(등급 색, 세트 색, 상태이상 색)를 모양·패턴·아이콘으로 보조 표시하면 전체 플레이어 경험이 향상됨.

OnionCat에서 색이 핵심인 정보:
- 장비 등급 (흰색·파랑·보라·주황)
- 세트 10종 색 구분 (Sun·Wind·…)
- 상태이상 아이콘 (화상·둔화·감전·냉기·독)
- 대미지 숫자 색 (일반·크리티컬·딜러 구분)
- 예고 신호 (노랑=막기·빨강=회피)

---

## 색각 이상 유형

| 유형 | 비율(남) | 특징 |
|------|----------|------|
| Deuteranopia/Deuteranomaly | ~5% | 빨강-초록 구분 어려움 (가장 흔함) |
| Protanopia/Protanomaly | ~1.5% | 빨강 지각 저하 |
| Tritanopia/Tritanomaly | ~0.01% | 파랑-노랑 구분 어려움 |
| Achromatopsia | 매우 드묾 | 완전 흑백 지각 |

실용적 목표: **Deuteranopia(적-녹)** 대응이 최우선. Tritanopia는 파랑-노랑 색쌍을 피하면 자연히 해결됨.

---

## Unity 구현 방법

### 방법 A: 포스트프로세싱 색 변환 LUT (가장 포괄적)

색맹 시뮬레이션 LUT를 두 개 준비해두고 설정 메뉴에서 전환한다.

```csharp
// ColorblindPostProcess.cs
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class ColorblindPostProcess : MonoBehaviour
{
    [SerializeField] private Volume _volume;
    [SerializeField] private VolumeProfile _profileNormal;
    [SerializeField] private VolumeProfile _profileDeuteranopia;
    [SerializeField] private VolumeProfile _profileProtanopia;

    public void Apply(ColorblindMode mode)
    {
        _volume.profile = mode switch
        {
            ColorblindMode.Deuteranopia => _profileDeuteranopia,
            ColorblindMode.Protanopia   => _profileProtanopia,
            _                           => _profileNormal,
        };
    }
}
```

Unity URP에서 LUT 기반 Color Lookup 볼륨 컴포넌트를 사용하거나, 커스텀 FullScreenPassRendererFeature로 색 변환 행렬을 적용.

색 변환 행렬 예 (Deuteranopia 근사):
```glsl
// 셰이더 내부
mat3 deuteranopia = mat3(
    0.367, 0.280, -0.012,
    0.861, 0.673,  0.043,
   -0.228, 0.047,  0.969
);
float3 corrected = mul(deuteranopia, color.rgb);
```

### 방법 B: 색 + 보조 모양/아이콘 (픽셀아트에 더 적합)

포스트프로세스 없이, 색이 정보를 전달하는 모든 UI 요소에 **보조 모양이나 기호**를 추가한다.
픽셀아트 게임에서는 색 변환이 의도한 팔레트를 깨드릴 수 있으므로, 아이콘·패턴·테두리 모양으로 대응하는 것이 더 안전하다.

#### 장비 등급 구분
```
일반(흰):  테두리 없음       → 아이콘 없음
희귀(파랑): 파란 테두리       → 아이콘에 ★ 1개
에픽(보라): 보라 테두리       → 아이콘에 ★★ 또는 마름모
전설(주황): 주황+빛 테두리    → 아이콘에 왕관
```

```csharp
// ItemSlotUI.cs
public void SetRarity(GearRarity rarity)
{
    _border.color = RarityColor(rarity);
    _rarityIcon.sprite = _rarityIcons[(int)rarity]; // ★ 개수 스프라이트
    _rarityIcon.enabled = rarity != GearRarity.Common; // 일반은 아이콘 없음
}
```

#### 상태이상 아이콘
각 상태이상에 고유 **모양 아이콘**을 배정해 색에 의존하지 않게 한다.

| 상태이상 | 색 | 아이콘 모양 |
|---------|-----|------------|
| 화상 | 빨강 | 🔥 불꽃 |
| 둔화 | 파랑 | ❄ 결정 |
| 감전 | 노랑 | ⚡ 번개 |
| 냉기 | 연파랑 | ❄ 눈송이 |
| 독 | 초록 | ☠ 해골·물방울 |
| 기절 | 흰색 | ★ 별 |

#### 예고 신호 (Telegraph)
- 노랑(막기 가능): 점선 테두리 또는 물음표 아이콘 포함
- 빨강(피해야 함): 실선 테두리 + X 아이콘 포함

### 방법 C: 색맹 모드 팔레트 교체 (픽셀아트 전용)

스프라이트·UI에서 특정 색 조합을 교체하는 색 팔레트 런타임 스왑.

```csharp
// RuntimePaletteSwap.cs 예
// R: 위험 빨강을 색맹 모드에서 분홍+사선 패턴으로 교체
// G: 안전 초록을 색맹 모드에서 파랑+점 패턴으로 교체
// 단: 스프라이트에 팔레트 인덱스가 있어야 구현 가능

// URP 2D에서는 Sprite Renderer의 Material Property Block으로
// 팔레트 텍스처를 런타임에 교체할 수 있음
var mpb = new MaterialPropertyBlock();
mpb.SetTexture("_PaletteTex", colorblindPalette);
_spriteRenderer.SetPropertyBlock(mpb);
```

---

## 설정 메뉴 UI

```
[시각 접근성]
  색각 이상 보조:  [일반]  [적·녹 구분 어려움]  [청·황 구분 어려움]
  등급 아이콘 표시: [○] (색약 모드와 무관하게 항상 켜기 가능)
  예고 신호 추가 아이콘: [○]
  대미지 숫자 테두리 강화: [○]
```

설정값은 `PlayerPrefs` 또는 게임 설정 저장 파일에 지속 저장.

```csharp
public enum ColorblindMode { Normal, Deuteranopia, Protanopia }

// 설정 저장/로드
PlayerPrefs.SetInt("ColorblindMode", (int)mode);
var loaded = (ColorblindMode)PlayerPrefs.GetInt("ColorblindMode", 0);
```

---

## OnionCat 적용 포인트

### 즉시 적용 가능한 것 (방법 B 우선)

1. **장비 등급 아이콘**: `GearScreen`·`UpgradeSelectUI`·`ItemTooltip`의 등급 표시에 별/마름모/왕관 아이콘 추가. 스프라이트 4개만 만들면 구현 완료
2. **상태이상 아이콘 통일**: 현재 색으로만 구분되는 상태이상 아이콘에 고유 형태 부여 — 픽셀 6×6짜리 아이콘이면 충분
3. **예고 패턴 추가**: 빨간 예고 영역에 사선 패턴 오버레이를 추가하면 패턴만으로도 "여기는 위험" 인식 가능

### 나중에 추가 (설정 메뉴 구현 시)
4. **색약 모드 토글**: `Settings_Menu`의 시각 접근성 섹션에 1~2가지 옵션 추가
5. **포스트프로세스 LUT** (선택): 색 변환 행렬 적용 시, 전체 화면의 팔레트가 영향을 받아 픽셀아트 분위기가 달라질 수 있음 → 방법 B(아이콘)와 병행하면 보완 가능

### 게임 내 색 설계 원칙 (지금부터 적용)
- **빨강과 초록을 동시에 "중요 정보"에 쓰지 않는다**: 예) 빨강=위험 / 초록=안전 쌍은 Deuteranopia에서 구분 불가. 대신 빨강=위험 / 파랑=안전 쌍을 사용
- **정보는 색+모양+위치** 세 가지 중 두 가지 이상으로 전달한다
- **대비 비율 4.5:1 이상 유지**: 텍스트·아이콘의 전경색과 배경색 명도 대비를 높게 유지 (WCAG AA 기준)

---

## 참고 링크
- WCAG 2.1 색 대비 기준: https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html
- 색맹 시뮬레이션 툴: https://www.color-blindness.com/coblis-color-blindness-simulator/
- Unity URP Color Lookup (LUT): https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/Post-Processing-Color-Lookup.html
- FullScreenPassRendererFeature (URP): https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/renderer-features/renderer-feature-full-screen-pass.html
- 인디 게임 접근성 체크리스트 (Game Accessibility Guidelines): https://gameaccessibilityguidelines.com
