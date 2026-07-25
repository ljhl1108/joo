# 스프라이트 아틀라스 & 픽셀아트 임포트 설정

리서치 날짜: 2026-07-25

## 개요
픽셀아트 게임에서 스프라이트를 Unity에 올바르게 임포트하지 않으면 **블러**, **픽셀 깨짐**, **텍스처 출혈(bleeding)**, **드로우콜 낭비**가 발생한다. OnionCat의 pixel-perfect 비주얼과 성능을 동시에 잡으려면 임포트 설정과 Sprite Atlas 구성이 핵심이다.

---

## Unity 임포트 설정 (픽셀아트 필수 체크리스트)

### 1. Texture Type
```
Texture Type: Sprite (2D and UI)
Sprite Mode: Single (단일 스프라이트) 또는 Multiple (스프라이트 시트)
```

### 2. Pixels Per Unit (PPU)
**모든 스프라이트 PPU를 통일하는 것이 가장 중요.**

```
PPU 계산 공식:
PPU = 스프라이트 기준 픽셀 크기 / 원하는 유니티 단위 크기

예시:
- 캐릭터 스프라이트가 16픽셀 높이, 유니티에서 1유닛 높이 → PPU = 16
- 타일맵 타일이 32픽셀, 1유닛 → PPU = 32
```

PPU가 스프라이트마다 다르면 캐릭터와 배경 크기 비율이 어긋남.
OnionCat: 캐릭터 16px = 1 unit → PPU = 16 전체 통일

### 3. Filter Mode — 가장 중요
```
Filter Mode: Point (no filter)    ← 픽셀아트 필수
```
- **Bilinear / Trilinear**: 부드럽게 보간 → 픽셀아트가 흐릿해짐 (절대 금지)
- **Point**: 보간 없이 픽셀 그대로 → 선명한 픽셀아트

### 4. Compression
```
Compression: None    ← 픽셀아트 권장
또는
Format: RGBA 32 bit  (Format Override로 플랫폼별 명시)
```
- 압축 알고리즘(DXT, ETC2)은 픽셀아트에서 색상 번짐 발생
- 파일 크기 vs 품질 트레이드오프 → 픽셀아트는 원본 크기가 작아 None으로 해도 무방

### 5. Generate Mip Maps
```
Generate Mip Maps: 체크 해제 (false)
```
- Mip Map은 원거리 텍스처 자동 축소용 → 2D 픽셀아트에서 불필요하며 오히려 블러 유발

### 6. Max Texture Size
```
Max Texture Size: 2048 이상 (스프라이트 시트 기준)
```
- 스프라이트 시트가 잘리지 않도록 충분히 설정

---

## 자동화: Preset으로 설정 저장

모든 픽셀아트 스프라이트에 매번 설정하는 수고를 줄이려면 **Import Preset** 사용:

1. 스프라이트 임포트 설정을 원하는 대로 완성
2. Inspector 오른쪽 상단 "Preset" 아이콘 클릭 → "Save Current to..."
3. `Assets/Editor/Presets/PixelArtSprite.preset` 저장
4. 이후 새 스프라이트 선택 → Preset에서 적용

### Editor 스크립트로 자동 적용 (고급)
```csharp
// Assets/Editor/PixelArtImporter.cs
using UnityEditor;
using UnityEngine;

public class PixelArtImporter : AssetPostprocessor
{
    void OnPreprocessTexture()
    {
        // Sprites 폴더 하위 텍스처에만 자동 적용
        if (!assetPath.Contains("/Sprites/")) return;

        TextureImporter importer = (TextureImporter)assetImporter;
        importer.textureType = TextureImporterType.Sprite;
        importer.filterMode = FilterMode.Point;
        importer.mipmapEnabled = false;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.spritePixelsPerUnit = 16f;
    }
}
```
이 스크립트를 `Assets/Editor/` 폴더에 두면 `Assets/Sprites/` 하위 텍스처 임포트 시 자동 설정.

---

## Sprite Atlas 설정 및 활용

### 왜 Sprite Atlas를 써야 하나
**드로우콜**: Unity는 텍스처가 다를 때마다 별도 드로우콜 발생. 스프라이트 100개가 각각 다른 텍스처 = 드로우콜 100개.
**Sprite Atlas**: 여러 스프라이트를 하나의 텍스처 아틀라스로 병합 → 드로우콜 1개

```
예시:
고양이 스프라이트 8장 + 양파 스프라이트 8장 = 드로우콜 16개
→ Sprite Atlas 사용 시 드로우콜 1개
```

### Sprite Atlas 생성 방법

1. **Project 창** → 우클릭 → Create → 2D → Sprite Atlas
2. Inspector 설정:

```
Type: Master
Include in Build: 체크 (빌드에 포함)
Allow Rotation: 체크 해제    ← 픽셀아트 회전 시 블러 방지
Tight Packing: 체크 해제     ← 픽셀아트는 사각형 패킹이 안전
Padding: 4                   ← 스프라이트 간 여백 (출혈 방지)
```

3. **Objects for Packing** 항목에 스프라이트 폴더 또는 개별 스프라이트 드래그

### Sprite Atlas + Filter Mode 주의사항
Sprite Atlas 자체의 Filter Mode도 Point로 설정해야 함:
- Atlas Inspector → Filter Mode → Point (no filter)
- 개별 스프라이트 설정은 Atlas가 생성한 아틀라스 텍스처에 덮어쓰기됨

### 아틀라스 구성 전략
```
PlayerAtlas       ← Cat + Crop 모든 애니메이션 프레임
EnemyAtlas_01     ← 1챕터 적 스프라이트
EnemyAtlas_02     ← 2챕터 적 스프라이트
UIAtlas           ← UI 아이콘, 버튼
TilesAtlas        ← 환경 타일셋
FXAtlas           ← 파티클, 이펙트 스프라이트
```

플레이어 관련은 항상 메모리에 로드되므로 별도 아틀라스, 챕터별 적은 씬 전환 시 언로드.

---

## Pixel Perfect Camera 설정 (URP)

픽셀아트 게임에서 카메라 배율이 맞지 않으면 스프라이트가 서브픽셀 위치에 렌더링되어 흔들림 발생.

```
Camera 오브젝트에 Pixel Perfect Camera 컴포넌트 추가:

Asset Pixels Per Unit: 16  (PPU와 동일하게)
Reference Resolution: 320x180  (목표 해상도)
Crop Frame: None
Grid Snapping: Pixel Snap  ← 서브픽셀 흔들림 방지
```

URP에서는 `UniversalRenderPipelineAsset`의 **Anti Aliasing (MSAA)** 를 **Disabled**로 설정해야 픽셀아트가 흐릿해지지 않음.

---

## 스프라이트 슬라이싱 (Sprite Editor)

스프라이트 시트(여러 프레임이 한 이미지) 분리:

1. 스프라이트 선택 → Inspector → Sprite Mode: **Multiple**
2. **Sprite Editor** 버튼 클릭
3. Slice 메뉴:
   - Type: **Grid By Cell Size** (프레임 크기가 고정된 경우)
   - Pixel Size X/Y: 프레임 가로/세로 픽셀 입력
   - Method: **Delete Existing**
4. Apply

**Aseprite 연동**: Aseprite에서 Export > Export Sprite Sheet 시 JSON Data도 함께 저장하면 Unity Sprite Editor의 Automatic Slice로 자동 인식 가능.

---

## OnionCat 적용 포인트

### 즉시 적용 가능한 설정 리스트
```
[ ] Assets/Sprites/ 폴더 생성
[ ] 모든 스프라이트 PPU = 16 통일
[ ] Filter Mode = Point (no filter)
[ ] Mip Maps = false
[ ] Compression = None
[ ] Editor/PixelArtImporter.cs 자동화 스크립트 추가
[ ] PlayerAtlas, EnemyAtlas, UIAtlas 생성
[ ] Pixel Perfect Camera 컴포넌트 설정
[ ] MSAA 비활성화
```

### 중요 고려사항
- Cat(고양이)과 Crop(양파)는 **한 몸**이므로 스프라이트 피벗(pivot)을 Cat의 발 중심에 맞추는 것이 물리 계산에 유리
- 감자 화분은 Cat 스프라이트에 포함해 하나의 스프라이트로 렌더링하거나, 분리해서 Cat 위에 오프셋 렌더링 → 달리기/대시 애니메이션에서 자연스럽게 흔들림 표현 가능

---

## 참고 링크
- Unity 공식 - Sprite Editor: https://docs.unity3d.com/Manual/SpriteEditor.html
- Unity 공식 - Sprite Atlas: https://docs.unity3d.com/Manual/class-SpriteAtlas.html
- Unity 공식 - Pixel Perfect Camera: https://docs.unity3d.com/Packages/com.unity.2d.pixel-perfect@5.0/manual/index.html
- 픽셀아트 임포트 가이드 (Unity Blog): https://blog.unity.com/games/2d-pixel-perfect-how-to-set-up-your-unity-project-for-retro-8-bits-games
- Aseprite to Unity 워크플로우: https://www.youtube.com/results?search_query=aseprite+unity+animation+workflow
