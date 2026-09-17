# Pixel Font & TextMeshPro System (픽셀 폰트 & TextMeshPro 시스템)

리서치 날짜: 2026-09-17

## 개요

픽셀아트 게임에서 텍스트가 흐릿하게 보이거나 안티앨리어싱이 적용되면 전체적인 픽셀 아트 감성이 깨진다. Unity의 TextMeshPro(TMP)는 SDF(Signed Distance Field) 방식을 기본으로 사용하는데, 픽셀 폰트에는 이 방식이 오히려 흐릿함을 만든다. 올바른 임포트 및 렌더링 설정이 필수다.

OnionCat에서 중요한 이유:
- 데미지 숫자, HUD 텍스트, 업그레이드 카드 이름이 모두 픽셀 폰트를 사용해야 일관성 유지
- 해상도가 작은 게임 뷰(예: 320×180)에서 텍스트가 선명하게 보여야 함
- 한국어/영어 두 언어 모두 지원 시 폰트 세팅이 달라짐

---

## 핵심 개념

### SDF vs Bitmap 렌더링
| 방식 | 특징 | 픽셀아트 적합성 |
|------|------|----------------|
| SDF (기본 TMP) | 어떤 크기에서도 선명, 아웃라인·그림자 지원 | **부적합** (흐릿한 가장자리) |
| Bitmap (Raster) | 지정 크기에서만 선명, 픽셀 완벽 | **적합** (픽셀 폰트 전용) |

### 픽셀 폰트 임포트 방식
Unity TMP에서 픽셀 폰트를 선명하게 사용하는 방법:
1. **TMP Font Asset을 Bitmap 모드로 생성** (SDF 비활성화)
2. **Atlas Rendering Mode**: Raster (SDF 아닌 비트맵 아틀라스)
3. **폰트 크기를 작게 고정** (예: 8px 또는 16px 폰트면 그대로 사용)
4. **Point 샘플링** 텍스처 필터 사용

---

## Unity 구현 방법

### 1. 픽셀 폰트 임포트 설정

**추천 무료 픽셀 폰트 (영문)**
- Press Start 2P (Google Fonts)
- VT323 (Google Fonts)
- Pixel Operator (dafont.com)

**추천 픽셀 폰트 (한국어 포함)**
- 둥근모꼴 (Rounded Mplus) — 한글 포함 픽셀 폰트
- NeoDunggeunmo Pro — 한국어 픽셀 폰트
- Galmuri11 — 오픈소스 한국어 픽셀 비트맵 폰트 (GitHub)

**TTF/OTF 폰트 임포트 설정 (Inspector)**
```
Font Size: 8 (또는 16)
Character: Custom
Rendering Mode: Raster  ← 반드시 이 설정
Atlas Width: 256 (또는 512, 한글은 1024 이상)
Atlas Height: 256
```

### 2. TMP Font Asset Creator 설정

Window → TextMeshPro → Font Asset Creator 에서:
```
Source Font File: [임포트한 TTF]
Sampling Point Size: 8  (폰트 원본 픽셀 크기)
Padding: 0              (SDF 패딩 불필요)
Packing Method: Optimum
Atlas Resolution: 256x256
Character Set: Custom Range (필요한 문자만)
Render Mode: RASTER      ← 핵심 설정
```

**주의**: 한국어 포함 시 Character Set에 한글 가나다라... 전체 추가 필요
- Custom Range: 44032-55203 (한글 완성형 전체)
- Atlas Resolution: 최소 2048×2048 필요

### 3. 텍스처 필터 설정 (필수)

생성된 Font Atlas 텍스처 선택 → Inspector:
```
Filter Mode: Point (no filter)  ← 픽셀 완벽 렌더링
Compression: None
```

### 4. TMP 컴포넌트 설정

```csharp
// 런타임에서 TMP 텍스트 픽셀 선명도 보장
using TMPro;
using UnityEngine;

[RequireComponent(typeof(TextMeshPro))]
public class PixelTextSetup : MonoBehaviour
{
    private void Awake()
    {
        var tmp = GetComponent<TextMeshPro>();
        // 폰트 크기가 원본 픽셀 크기의 배수여야 선명
        // 예: 8px 폰트면 8, 16, 24, 32 등으로만 설정
        tmp.fontSize = 8f;
        tmp.enableAutoSizing = false;
        tmp.overflowMode = TextOverflowModes.Overflow;
    }
}
```

### 5. Canvas & Camera 설정 (픽셀 퍼펙트 UI)

```
Canvas 설정:
- Render Mode: Screen Space - Camera
- Pixel Perfect: ✓ (체크)

Camera 설정 (UI Camera):
- Orthographic
- Size: 게임 해상도의 절반 (예: 180/2 = 90)
```

### 6. 아웃라인 없이 가독성 높이기

픽셀 폰트는 아웃라인 대신 **배경 박스** 방식 추천:

```csharp
// 데미지 숫자, 툴팁 등에 사용하는 배경 박스 방식
public class PixelTextBox : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI label;
    [SerializeField] private UnityEngine.UI.Image background;
    [SerializeField] private int paddingPixels = 2;

    private void Update()
    {
        // 텍스트 크기에 맞춰 배경 자동 조절
        Vector2 textSize = label.GetPreferredValues();
        background.rectTransform.sizeDelta = textSize + 
            Vector2.one * (paddingPixels * 2);
    }
}
```

### 7. Floating Damage Numbers에 픽셀 폰트 적용

```csharp
// FloatingDamageNumber.cs 수정 예시
public class FloatingDamageNumber : MonoBehaviour
{
    [SerializeField] private TextMeshPro tmp;

    public void Setup(float damage, DamageSource source)
    {
        // 공격 타입별 색상
        tmp.color = source switch {
            DamageSource.Melee  => new Color32(255, 200, 50, 255),   // 황금
            DamageSource.Ranged => new Color32(100, 200, 255, 255),  // 하늘
            DamageSource.Parry  => new Color32(255, 50, 150, 255),   // 핑크
            _ => Color.white
        };
        
        // 픽셀 폰트는 8의 배수 크기만 선명
        tmp.fontSize = damage > 50 ? 16 : 8;
        tmp.text = Mathf.RoundToInt(damage).ToString();
    }
}
```

### 8. 한국어/영어 다국어 폰트 전환

```csharp
// LocalizationFontSwitcher.cs
public class LocalizationFontSwitcher : MonoBehaviour
{
    [SerializeField] private TMP_FontAsset englishPixelFont;
    [SerializeField] private TMP_FontAsset koreanPixelFont;

    private void Start()
    {
        // 현재 언어 설정에 따라 기본 폰트 전환
        string lang = PlayerPrefs.GetString("Language", "ko");
        TMP_FontAsset target = lang == "ko" ? koreanPixelFont : englishPixelFont;
        
        // 씬 내 모든 TMP에 적용
        foreach (var tmp in FindObjectsByType<TextMeshProUGUI>(FindObjectsSortMode.None))
        {
            tmp.font = target;
        }
    }
}
```

---

## OnionCat 적용 포인트

### 텍스트 사용 위치별 권장 설정
| 위치 | 폰트 크기 | 색상 | 비고 |
|------|-----------|------|------|
| 데미지 숫자 | 8px | 공격 타입별 | Floating, 풀링으로 재사용 |
| HUD (HP, 쿨다운) | 8px | 흰색/빨강 | 항상 선명하게 |
| 업그레이드 카드 이름 | 16px | 흰색 | 배경 박스 필수 |
| 보스 이름 | 16px | 노랑 | 화면 상단 표시 |
| 메인 메뉴 타이틀 | 32px | 그라디언트 가능 | SDF 폰트 허용 |

### 즉시 구현 우선순위
1. **데미지 숫자 픽셀 폰트** → 전투 피드백에 즉각적 영향
2. **HUD 텍스트 (HP, 쿨다운)** → 플레이어가 항상 보는 정보
3. **업그레이드 카드** → 선택 화면의 가독성
4. 한국어 폰트는 개발 후기에 추가해도 됨 (영문 먼저 구현)

### 주의 사항
- `FindObjectsByType`은 Awake/Start에서만 사용 (Update 금지)
- 픽셀 폰트는 UI Scale과 Camera Orthographic Size가 맞아야 선명함
- **해상도 변경 시** Canvas Scaler가 "Scale With Screen Size"로 설정되어야 픽셀 깨짐 방지
- 한국어 폰트 아틀라스는 용량이 크므로 Addressables로 지연 로딩 고려

---

## 참고 링크

- [Galmuri11 한국어 픽셀 폰트 (GitHub)](https://github.com/quiple/galmuri)
- [TextMeshPro 공식 문서](https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html)
- [Unity Pixel Perfect 카메라 설정](https://docs.unity3d.com/Packages/com.unity.2d.pixel-perfect@5.0/manual/index.html)
- [Press Start 2P 폰트 (Google Fonts)](https://fonts.google.com/specimen/Press+Start+2P)
- [TMP Bitmap Font Setup Tutorial (Unity Forum)](https://discussions.unity.com/t/how-to-use-bitmap-fonts-with-textmeshpro/729254)
- [Pixel Art Text Rendering Best Practices (itch.io devlog)](https://itch.io/)
