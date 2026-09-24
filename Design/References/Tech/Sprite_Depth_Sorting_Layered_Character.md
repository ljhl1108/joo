# Sprite Depth Sorting — 레이어드 캐릭터 시스템

리서치 날짜: 2026-09-24

## 개요

픽셀아트 탑뷰 게임에서 여러 파트로 구성된 캐릭터(예: OnionCat — 고양이 + 화분 + 양파)를
올바른 깊이로 렌더링하는 기법. 스프라이트 레이어 충돌, 오버랩 아티팩트, z-fighting을 막는 것이 핵심.

---

## Unity 2D 렌더링 순서 기초

Unity 2D에서 렌더링 순서는 3단계 우선순위:
1. **Sorting Layer** — 가장 큰 단위 (Background / Default / Player / UI 등)
2. **Order in Layer** — 같은 Sorting Layer 내 세부 순서 (숫자 낮을수록 뒤)
3. **Z Position** — Orthographic 카메라에서는 기본 무시되지만 설정에 따라 사용 가능

```
카메라 → Sorting Layer 순서 → Order in Layer 순서 → Z Position (Transparent 정렬 설정 시)
```

### Transparent Sort Axis 설정
Project Settings > Graphics > Transparency Sort Mode = **Custom Axis**  
Transparency Sort Axis = **(0, 1, 0)** (Y축 기준)

탑뷰에서 Y값이 낮을수록(아래에 있을수록) 더 앞에 그려짐:

```csharp
// 런타임에 Y값으로 Order 동적 갱신 (성능 비용 있음)
void Update() {
    spriteRenderer.sortingOrder = Mathf.RoundToInt(-transform.position.y * 100);
}
```

---

## Unity 구현 방법

### 방법 1: SortingGroup (권장)

여러 SpriteRenderer를 하나의 유닛으로 묶어 내부 순서를 보존하면서 외부에서는 하나로 정렬.

```csharp
// 캐릭터 루트에 SortingGroup 컴포넌트 추가
// 각 파트에는 SortingGroup 내부 Order in Layer만 지정

// Inspector 설정:
// Root (SortingGroup: Layer="Player", Order=0) ← Y값에 따라 동적 갱신
//   ├─ Shadow (SpriteRenderer: Layer="Player", Order=-1)
//   ├─ CatBody (SpriteRenderer: Layer="Player", Order=0)
//   ├─ Pot (SpriteRenderer: Layer="Player", Order=1)
//   └─ Onion (SpriteRenderer: Layer="Player", Order=2)
```

```csharp
using UnityEngine;
using UnityEngine.Rendering;

[RequireComponent(typeof(SortingGroup))]
public class YSortedEntity : MonoBehaviour {
    SortingGroup _sg;

    void Awake() => _sg = GetComponent<SortingGroup>();

    void LateUpdate() {
        _sg.sortingOrder = Mathf.RoundToInt(-transform.position.y * 10);
    }
}
```

`LateUpdate`에서 갱신해야 물리/애니메이션 이후 최종 위치 기준으로 정렬됨.

---

### 방법 2: Sprite Renderer의 Sprite Sort Point

캐릭터 스프라이트의 **Sprite Sort Point**를 Bottom(발 위치)으로 설정:

```
Sprite Import Settings > Sprite > Sprite Sort Point = Bottom
```

이렇게 하면 pivot이 가운데여도 정렬 기준점은 발 부분. Y-sort와 함께 쓸 때 효과적.

---

### 방법 3: Composite Sprite (분리 파트 없이)

성능이 중요하면 애니메이션 파트를 하나의 스프라이트로 합성하고, 하나의 SpriteRenderer만 사용. Aseprite에서 레이어를 합쳐서 내보내면 됨.

---

## OnionCat 적용 포인트

### 레이어 구조 설계

OnionCat은 고양이 등에 화분이 얹혀 있고, 화분 위에 양파가 있음:

```
PlayerRoot (SortingGroup, Layer="Player")
├─ CatShadow        Order = -2  (항상 맨 뒤)
├─ CatBody          Order =  0  (고양이 몸통)
├─ CatTail          Order =  1  (꼬리 — 화분 뒤에 있어야 할 때)
├─ Pot              Order =  2  (화분)
├─ PotSoil          Order =  3  (흙)
└─ OnionBody        Order =  4  (양파 몸통 — 항상 가장 앞)
```

### 주의: 캐릭터가 방향 전환할 때

좌우 뒤집기 시 Order가 뒤집히지 않도록 주의:
- `SpriteRenderer.flipX = true`를 쓰면 Order가 그대로 유지됨 (권장)
- 루트를 `transform.localScale.x = -1`로 뒤집으면 SortingGroup 내부 Order도 정상이지만
  의도치 않은 Collider 뒤집힘 주의

```csharp
// 방향 전환 시 — flipX 방식 (권장)
[SerializeField] private SpriteRenderer[] _allParts;

public void SetFacing(bool facingRight) {
    foreach (var sr in _allParts)
        sr.flipX = !facingRight;
}
```

### 화분 / 양파가 별개 플레이어일 때

P2(Onion)가 독립적인 Input을 가지지만 같은 GameObject에 있으므로:
- Onion 애니메이션만 따로 Animator에 연결
- Onion의 SpriteRenderer만 선택적으로 숨기거나 색 변경 가능 (쉴드 활성화 시 빛나게 등)

```csharp
// Onion Shield 활성화 시 빛나는 효과
_onionSpriteRenderer.material = shieldMaterial;
_onionSpriteRenderer.color = Color.cyan;
```

### 성능 팁

- 방 당 적이 많을 경우 매 프레임 `sortingOrder` 갱신은 비용이 있음
- 해결책: **Dirty Flag** — 위치가 변하지 않으면 갱신 건너뜀

```csharp
void LateUpdate() {
    int newOrder = Mathf.RoundToInt(-transform.position.y * 10);
    if (newOrder != _sg.sortingOrder)
        _sg.sortingOrder = newOrder;
}
```

---

## 참고 링크

- Unity Manual — Sorting Layers: https://docs.unity3d.com/Manual/2DSorting.html
- Unity Manual — SortingGroup: https://docs.unity3d.com/Manual/class-SortingGroup.html
- Unity Manual — Transparency Sort Mode: https://docs.unity3d.com/Manual/TransparencySortMode.html
- Unity Forum — Y-sort best practices (2D): https://forum.unity.com/threads/y-sorting.html
- Sprite Sort Point 설명: https://docs.unity3d.com/Manual/SpriteSortPoint.html
