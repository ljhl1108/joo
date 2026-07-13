# 스프라이트 정렬 레이어 시스템 (Sprite Sorting Layer System)

리서치 날짜: 2026-07-13

## 개요

탑다운 픽셀아트 게임에서 오브젝트가 "앞/뒤" 올바르게 겹쳐 보이지 않으면 즉각 어색함이 드러난다.
Unity 2D의 Sprite Renderer는 Sorting Layer + Order in Layer + Z 위치를 조합해 렌더링 순서를 결정한다.
OnionCat처럼 고양이가 꽃화분을 등에 짊어지고 다양한 환경 오브젝트와 상호작용하는 게임에서는
**동적 정렬(Y축 기반 정렬)** 이 필수다.

---

## Unity 정렬 원리 3가지

### 1. Sorting Layer
`Edit → Project Settings → Tags and Layers → Sorting Layers` 에서 순서 정의.
순서가 높은 레이어가 위에 그려진다.

권장 OnionCat 레이어 구성 (아래 = 뒤, 위 = 앞):
```
Background      ← 배경 타일 (바닥, 벽 장식)
Shadows         ← 오브젝트 그림자 (선택)
Default         ← 일반 게임플레이 오브젝트
Characters      ← 플레이어, 적
Projectiles     ← 투사체
VFX             ← 파티클, 이펙트
UI_World        ← 월드 공간 체력바, 데미지 숫자
```

### 2. Order in Layer
같은 Sorting Layer 내 세부 정렬. 정수값; 클수록 위에 그려진다.
벽, 바닥, 아이템 등 고정 오브젝트는 Inspector에서 직접 설정.

### 3. Sprite Renderer → Sprite Sort Point
`Transform` 기준 또는 `Pivot` 기준으로 정렬 기준점 선택.
탑다운에서는 `Pivot`(스프라이트 하단 중앙)을 기준점으로 쓰는 것이 자연스럽다.

---

## Unity 구현 방법

### A. 카메라 Transparency Sort Mode 설정 (필수)

```
Edit → Project Settings → Graphics → Camera Settings
→ Transparency Sort Mode: Custom Axis
→ Transparency Sort Axis: X=0, Y=1, Z=0
```

이 설정 후 같은 Sorting Layer 내 오브젝트는 Y 위치가 낮을수록(화면 아래쪽) 앞에 그려진다.
고정 오브젝트(나무, 상자 등)는 추가 코드 없이 자동으로 올바른 정렬.

### B. 동적 Y 정렬 컴포넌트 (움직이는 오브젝트)

플레이어, 적처럼 Y가 바뀌는 오브젝트는 매 프레임 Order in Layer를 갱신해야 한다.

```csharp
using UnityEngine;

[RequireComponent(typeof(SpriteRenderer))]
public class YSortedRenderer : MonoBehaviour
{
    [SerializeField] private float baseY = 0f;   // 피벗 오프셋 (보통 0)
    private SpriteRenderer _sr;

    private void Awake()
    {
        _sr = GetComponent<SpriteRenderer>();
    }

    private void LateUpdate()
    {
        // Y가 낮을수록(화면 아래) Order가 높아야 앞에 그려짐
        // 10000을 곱해 소수점 차이도 반영 (int 변환 손실 최소화)
        _sr.sortingOrder = Mathf.RoundToInt(-(transform.position.y + baseY) * 100);
    }
}
```

> `LateUpdate()`를 쓰는 이유: 이동 코드가 `Update()`에서 실행된 뒤 정렬을 적용해야 한 프레임 지연 없음.

### C. Sorting Group 컴포넌트 (복합 스프라이트)

고양이 + 꽃화분처럼 여러 Sprite Renderer가 하나의 캐릭터를 구성할 때:
- 각 부위의 Order in Layer가 따로 놀면 다른 캐릭터와 섞임
- `Sorting Group` 컴포넌트를 루트에 추가하면 **그룹 전체를 하나의 유닛으로 정렬**

```
GameObject (YSortedRenderer + SortingGroup)
├── Body_Sprite (SpriteRenderer, Order: 0)
├── FlowerPot_Sprite (SpriteRenderer, Order: 1)  ← 몸 위에 그려짐
└── Shadow_Sprite (SpriteRenderer, Order: -1)    ← 몸 뒤에
```

`SortingGroup`의 Sorting Layer와 Order in Layer가 그룹 전체의 외부 정렬을 결정.
내부 Order in Layer는 그룹 내부 상대 순서만 결정.

### D. 레이어 매트릭스 설정

```
Edit → Project Settings → Physics 2D → Layer Collision Matrix
```

렌더링 레이어와는 별개지만 혼동하지 않도록 이름을 통일하면 관리가 쉬움.

---

## OnionCat 적용 포인트

### 1. 플레이어 구조
```
PlayerRoot (YSortedRenderer + SortingGroup)  ← 이것이 Y 정렬 기준
├── CatBody (SpriteRenderer, Order: 1)
├── FlowerPot (SpriteRenderer, Order: 2)     ← 항상 고양이 위
├── Crop_P2 (SpriteRenderer, Order: 3)       ← 화분 위
└── Shadow (SpriteRenderer, Order: 0, Sorting Layer: Shadows)
```

### 2. 환경 오브젝트 (나무, 바위)
Transparency Sort Mode를 커스텀 Y축으로 설정한 뒤 Order in Layer 고정값 사용.
나무처럼 상단과 하단이 모두 있는 오브젝트:
- 뿌리/하단: Order 0 (캐릭터 앞뒤 교차)
- 왕관/상단: Sorting Layer `Foreground` (항상 캐릭터 앞)로 분리

### 3. 투사체 & VFX
`Projectiles` 레이어에 배치 → 캐릭터보다 항상 앞. 지면 이펙트(먼지)는 `Background` 또는 별도 `GroundVFX` 레이어.

### 4. 방 전환 시 주의
방 전환 애니메이션 중 Order 갱신 코드가 실행되면 깜빡임 발생 가능.
전환 시작 시 `YSortedRenderer` 컴포넌트 비활성화 → 완료 후 재활성화.

---

## 흔한 실수

| 실수 | 증상 | 해결 |
|------|------|------|
| Transparency Sort Mode 미설정 | Y 기반 정렬이 안 됨 | Custom Axis Y=1 설정 |
| Z 위치 혼용 | 오브젝트가 완전히 안 보이거나 항상 뒤에 | Z는 0으로 고정, 정렬은 Sorting Layer/Order만 사용 |
| SortingGroup 없이 복합 스프라이트 | 캐릭터 부위가 다른 캐릭터와 섞임 | 루트에 SortingGroup 추가 |
| Update()에서 갱신 | 이동 직후 한 프레임 틀린 정렬 | LateUpdate()로 이동 |

---

## 참고 링크

- [Unity 공식 - Sorting Layers](https://docs.unity3d.com/Manual/class-TagManager.html)
- [Unity 공식 - Sorting Group](https://docs.unity3d.com/Manual/class-SortingGroup.html)
- [Unity 공식 - Transparency Sort Mode](https://docs.unity3d.com/ScriptReference/TransparencySortMode.html)
- [Brackeys - 2D 정렬 유튜브 튜토리얼](https://www.youtube.com/watch?v=rnqF6S7PfFA)
- [Unity Forum - Y-Sorting Best Practices](https://forum.unity.com)
