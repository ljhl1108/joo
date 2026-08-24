# 캐릭터 가짜 그림자 시스템 (Blob Shadow)

리서치 날짜: 2026-08-24

## 개요

탑다운 2D 픽셀아트 게임에서 캐릭터 아래에 타원형 그림자를 렌더링해 **공간감·입체감**을 부여하는 기법.
Unity의 URP 2D 조명 없이도 저렴하게 구현 가능하며, 점프/공중 적에게도 적용돼 플레이어가 위치를 직관적으로 파악하게 돕는다.

OnionCat에서는 고양이 캐릭터(몸)와 적들 아래에 이 그림자를 추가하면 **픽셀아트 특유의 평면감을 깨고 공간 깊이감** 을 줄 수 있다.

---

## Unity 구현 방법

### 방법 1: 정적 자식 스프라이트 (가장 간단)

```csharp
// 아무 스크립트 필요 없음 — Inspector 설정만으로 완성

// 1. 타원형 반투명 스프라이트 에셋 준비
//    - 흰색 타원(원) PNG, 텍스처 크기 32x16 또는 64x32
//    - Color: 검정(#000000), 알파: 0.3~0.4

// 2. 캐릭터 프리팹에 빈 GameObject "Shadow" 자식 추가
// 3. Shadow에 SpriteRenderer 붙이고 타원 스프라이트 할당
// 4. Sorting Layer: "Shadow" (Character보다 아래)
// 5. Shadow의 로컬 Y 위치를 캐릭터 발 위치로 맞춤 (예: -0.3)
// 6. 스케일: (1.2, 0.5, 1) 정도로 납작하게
```

**Sorting Layer 설정 필수:**
- Project Settings → Tags and Layers → Sorting Layers에 "Shadow" 레이어 추가
- SpriteRenderer.sortingLayerName = "Shadow"

---

### 방법 2: 스크립트로 공중 높이에 따라 그림자 크기/알파 조절

```csharp
using UnityEngine;

public class BlobShadow : MonoBehaviour
{
    [SerializeField] private SpriteRenderer shadowRenderer;
    [SerializeField] private Transform characterTransform;
    [SerializeField] private float groundY = 0f;          // 바닥 Y 좌표
    [SerializeField] private float maxHeight = 3f;        // 이 높이 이상이면 최소 크기
    [SerializeField] private Vector3 baseScale = new Vector3(1.2f, 0.5f, 1f);
    [SerializeField] private float minAlpha = 0.1f;
    [SerializeField] private float maxAlpha = 0.4f;

    private void LateUpdate()
    {
        float height = characterTransform.position.y - groundY;
        float t = Mathf.Clamp01(height / maxHeight);

        // 높을수록 그림자 작아지고 흐려짐
        transform.localScale = Vector3.Lerp(baseScale, baseScale * 0.4f, t);
        Color c = shadowRenderer.color;
        c.a = Mathf.Lerp(maxAlpha, minAlpha, t);
        shadowRenderer.color = c;

        // 그림자는 항상 바닥 Y에 고정
        Vector3 pos = characterTransform.position;
        pos.y = groundY;
        transform.position = pos;
    }
}
```

**유니티 에디터에서 드래그 앤 드롭 설정 필요:**
- `shadowRenderer`: Shadow 자식 오브젝트의 SpriteRenderer
- `characterTransform`: 부모 캐릭터의 Transform

---

### 방법 3: URP 2D Shadow Caster (실제 광원 그림자)

더 현실적이지만 **성능 비용이 크고 픽셀아트 스타일과 어울리지 않을 수 있음** → 보통 Blob Shadow 방법 1~2를 권장.

```
설정 방법 (참고용):
1. 씬에 Global Light 2D 또는 Point Light 2D 추가
2. 캐릭터 스프라이트에 Shadow Caster 2D 컴포넌트 추가
3. Light의 "Shadow Type"을 "Sprite" 또는 "Interior"로 설정
→ 동적 그림자 렌더링됨 (성능 주의)
```

---

### 그림자 스프라이트 만들기 (별도 에셋 없이)

Unity에서 Circle 스프라이트를 사용해도 되고, 아래처럼 8x4픽셀 타원 PNG를 만들면 충분:

```
PNG 예시 (8x4, 알파):
⬛⬛⬛⬛⬛⬛⬛⬛
⬛⬜⬜⬜⬜⬜⬜⬛
⬛⬜⬜⬜⬜⬜⬜⬛
⬛⬛⬛⬛⬛⬛⬛⬛
(흰색 = 불투명 검정, 검정 테두리 = 투명)
Import Settings: Sprite, Filter Mode = Point, PPU = 8
```

---

## OnionCat 적용 포인트

### 고양이 캐릭터
- 고양이는 화분(파)을 등에 지고 있어 **몸 중심이 높음** → 그림자를 약간 뒤쪽(Y -0.4)으로 오프셋
- 대시 중: 그림자 알파 0.15로 감소 (공중에 뜬 느낌)
- 스크립트에서 `DashState`일 때 `overrideAlpha`를 적용

### 적 캐릭터
- **모든 적 프리팹**에 Shadow 자식 추가 → 적이 플레이어 위/아래에 있을 때 위치 판단 도움
- 날아다니는 적(원거리 포격형): `height`를 1.5f 정도로 고정 → 항상 작은 그림자

### 투사체
- 날아가는 투사체에도 바닥 그림자 추가 시 **탄막 회피 게임성** 향상
- 그림자만 보고 발아래를 피해야 하는 디자인 가능 (Enter the Gungeon 스타일)

### Sorting Layer 구성 권장
```
Background → Shadow → Ground → Character → Enemy → Projectile → UI
```

---

## 참고 링크

- Unity Docs - Sprite Renderer: https://docs.unity3d.com/Manual/class-SpriteRenderer.html
- Unity Docs - Shadow Caster 2D (URP): https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@14.0/manual/2DShadowCasters.html
- YouTube "Blob Shadow Unity 2D" 검색
- Brackeys "2D Shadows in Unity" 튜토리얼
