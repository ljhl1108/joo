# URP 2D Lighting System

리서치 날짜: 2026-07-10

## 개요

Unity의 **Universal Render Pipeline(URP) 2D Renderer**에 내장된 실시간 2D 조명 시스템. 스프라이트에 노멀맵을 적용하거나 포인트 라이트를 배치해 픽셀아트 던전에 분위기 있는 조명 효과를 줄 수 있다. OnionCat의 어두운 던전 배경과 적 공격 예고, 아이템 강조에 핵심적으로 활용 가능하다.

---

## Unity 구현 방법

### 1. URP 2D Renderer 설정

```
1. Package Manager → Universal RP 설치
2. Assets → Create → Rendering → URP Asset (with 2D Renderer)
3. Project Settings → Graphics → Scriptable Render Pipeline Settings에 위 에셋 할당
4. URP Asset 인스펙터에서 Renderer List → 2D Renderer Data 선택 확인
```

### 2. 라이트 종류 (Light 2D 컴포넌트)

| 라이트 타입 | 용도 | 주요 속성 |
|---|---|---|
| **Global Light 2D** | 씬 전체 환경광 (앰비언트) | Intensity로 밝기 조절 |
| **Point Light 2D** | 원형 빛 (횃불, 마법구, 발광 이펙트) | Radius, Inner/Outer Radius |
| **Spot Light 2D** | 방향성 원뿔 빛 (플래시라이트) | Inner/Outer Angle |
| **Freeform Light 2D** | 자유 다각형 형태의 빛 | 편집 가능한 폴리곤 |

### 3. 스프라이트에 조명 적용

```
1. 스프라이트의 Sprite Renderer → Material을 "Sprite-Lit-Default"로 변경
   (기본 Sprite-Unlit-Default는 조명을 무시함)
2. 씬에 Light 2D 오브젝트 배치
3. Light 2D의 Target Sorting Layers에 조명을 받을 레이어 추가
```

### 4. 노멀맵(Normal Map) 적용 (선택)

```
1. 스프라이트 텍스처 옆에 "_n" 접미사 노멀맵 텍스처 준비
   예: "wall.png" → "wall_n.png"
2. 노멀맵 텍스처 임포트 설정: Texture Type → Normal Map
3. Sprite Renderer → Material에서 "Sprite-Lit-Default" 사용 시 노멀맵 자동 인식
   또는 커스텀 Lit 쉐이더에서 _NormalMap 파라미터에 할당
```
> 픽셀아트에 노멀맵을 쓰면 작은 스프라이트에도 입체감이 생기지만, 노멀맵 제작 툴(Sprite DLight, SpriteIlluminator 등)이 필요함.

### 5. Shadow Caster 2D (그림자)

```csharp
// 오브젝트에 ShadowCaster2D 컴포넌트 추가
// Light 2D에서 "Use Normal Map" 및 "Cast Shadows" 활성화
// ShadowCaster2D → Edit Shape로 그림자 영역 다각형 편집
```

### 6. 런타임 조명 제어 (C# 예시)

```csharp
using UnityEngine.Rendering.Universal;

public class EnemyAttackTelegraph : MonoBehaviour
{
    [SerializeField] private Light2D attackLight;
    
    public IEnumerator FlashWarning(float duration)
    {
        float elapsed = 0f;
        Color originalColor = attackLight.color;
        attackLight.color = Color.red;
        
        while (elapsed < duration)
        {
            attackLight.intensity = Mathf.PingPong(elapsed * 4f, 1f);
            elapsed += Time.deltaTime;
            yield return null;
        }
        
        attackLight.color = originalColor;
        attackLight.intensity = 1f;
    }
}
```

### 7. 퍼포먼스 고려사항

- **Light Blending Layer**: 조명을 받는 레이어를 최소화
- **Quality 설정**: Light 2D의 Light Quality → "Fast" (저품질, 고성능) vs "Accurate" 선택
- 모바일/저사양 기기: Global Light만 사용하고 포인트 라이트 개수 제한 (씬당 8~16개 이하)
- 조명을 애니메이션 대신 **Coroutine**으로 제어해 Update 오버헤드 감소

---

## OnionCat 적용 포인트

### 던전 분위기 (Ambient Setup)
```
Global Light 2D:
  - Intensity: 0.1 ~ 0.2 (매우 어두운 기본 환경광)
  - Color: 딥 퍼플 계열 (#1A0A2E)

방 내부 토치/마법진:
  - Point Light 2D x 2~4개
  - Radius: 3~5 (방 크기에 맞게)
  - Color: 주황/청록 계열 (분위기 지정)
```

### 적 공격 예고 (Telegraph)
- 적이 공격 준비 시 해당 적 주변 `Point Light 2D.color = Color.red`, Intensity 펄스
- 코루틴으로 0.5~1초 깜빡임 → 플레이어에게 시각 경고
- 고양이/양파 플레이어 모두 즉시 인식 가능

### 플레이어 표시
- 고양이 캐릭터에 작은 Point Light 2D 부착 (Radius: 1.0)
- Color: 따뜻한 노란색 → "우리가 여기 있다"는 감각
- 어두운 방에서 플레이어 위치를 직관적으로 파악

### 아이템 및 업그레이드 강조
- 업그레이드 카드 박스에 노란/금색 Point Light 2D
- Intensity 0.8 ~ 1.2 사이를 천천히 왔다갔다 (Mathf.PingPong)
- 탄막이 많은 상황에서도 아이템 위치 즉시 파악

### 보스 Phase 전환
- Phase 1 → Phase 2: `Global Light 2D.color` 급격히 빨강으로 변경
- CinemachineImpulse + 조명 색 변경 동시 발동 → 강렬한 연출

---

## 참고 링크

- Unity 공식 문서 – 2D Lights Overview: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/2DLighting/intro-to-2d-lights-overview.html
- Unity 공식 문서 – Light2D 컴포넌트: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/2DLighting/light-types/light-2d-component-reference.html
- Unity 공식 문서 – Shadow Caster 2D: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/2DLighting/ShadowCaster2D.html
- Unity Learn – 2D Game Art, Animation, and Lighting for Artists (includes 2D lighting): https://learn.unity.com/course/2d-game-art-animation-and-lighting-for-artists
- Brackeys YouTube – 2D Lights in Unity (URP): https://www.youtube.com/c/Brackeys (검색: "Unity 2D lights URP")
- Unity Forum – URP 2D Renderer Performance Tips: https://forum.unity.com (검색: "URP 2D renderer performance optimization")
