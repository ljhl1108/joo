# Tilemap Composite Collider 최적화

리서치 날짜: 2026-11-01

## 개요

Unity 2D에서 타일맵 충돌을 처리할 때 `TilemapCollider2D` 하나만 쓰면 **타일 하나당 개별 폴리곤 콜라이더**가 생성된다. 40×20 방에 벽 타일이 200개라면 200개의 콜라이더가 물리 연산에 등록된다. `CompositeCollider2D`를 추가하면 인접 타일들이 하나의 큰 메시로 병합되어 **콜라이더 수가 90% 이상 감소**한다. OnionCat처럼 방마다 타일맵을 교체하는 게임에서 런타임 성능과 로드 시간에 직접 영향을 준다.

## Unity 구현 방법

### 기본 설정 (Static Composite)

```csharp
// Wall Tilemap GameObject에 다음 3개 컴포넌트를 추가:
// 1. TilemapCollider2D
// 2. CompositeCollider2D
// 3. Rigidbody2D (필수 중개자)
```

Inspector 설정 단계:
1. `TilemapCollider2D` → **Used By Composite** 체크 ✓
2. `Rigidbody2D` → **Body Type: Static** (타일맵은 움직이지 않음)
3. `CompositeCollider2D` → **Geometry Type** 선택:
   - `Outlines` : 속이 빈 외곽선 — 벽 모서리, 얇은 선형 장벽
   - `Polygons` : 채워진 다각형 — 일반 벽, 플랫폼

### GeometryType 선택 가이드

```
Outlines: 
  pros  — 더 단순한 메시, 더 빠른 처리
  cons  — 물체가 안으로 파고들 수 있음 (터널링)
  use   — 얇은 경계선 벽

Polygons (권장):
  pros  — 안전한 충돌, SubdivisionLevel로 정밀도 조절
  cons  — Outlines보다 약간 무거움
  use   — OnionCat 벽 타일맵 (Wall 레이어)
```

### 런타임 타일맵 변경 시 (OnionCat Room Reset)

타일을 런타임에 추가/제거하면 Composite가 자동 갱신되지 않는다:

```csharp
// 타일 변경 후 반드시 호출
compositeCollider.GenerateGeometry();
```

또는 `CompositeCollider2D` → **Generation Type: Synchronous** 설정 (자동 갱신, 성능 주의).

### 레이어 분리 (OnionCat 구조 최적화)

OnionCat은 Wall/Floor/Props 타일맵이 분리되어 있다.
벽에만 Composite를 적용하면 된다:

```
Tilemaps/
  Floor    — TilemapRenderer만 (충돌 없음)
  Wall     — TilemapCollider2D + CompositeCollider2D + Rigidbody2D(Static)
  Props    — 개별 오브젝트라면 TilemapCollider2D만 (CompositeCollider 불필요)
```

### Physics 2D Settings 추가 최적화

```
Project Settings → Physics 2D:
  Sleeping Mode: Start Awake (충돌 시작 전 Sleep)
  Default Contact Offset: 0.01 (기본 0.01, 낮출수록 정밀하지만 느림)
  Velocity Iterations: 8 (기본값 유지)
  Position Iterations: 3 (기본값 유지)
```

### 콜라이더 수 확인 (디버그)

```csharp
void OnValidate() {
    var tc = GetComponent<TilemapCollider2D>();
    var cc = GetComponent<CompositeCollider2D>();
    Debug.Log($"Tile colliders: {tc?.pathCount}, Composite paths: {cc?.pathCount}");
}
```

Unity Profiler의 **Physics 2D** 섹션에서 `Collider2D count`를 런 전후로 비교.

## OnionCat 적용 포인트

### 현재 구조와의 연결
OnionCat의 방은 `RoomLayouts/*.asset` 글자 지도 → 메뉴 **Apply Room Layouts** → 씬 Layout 자식에 타일 배치 구조다. Wall 타일맵에 CompositeCollider2D를 설정하면 방 로드 시 콜라이더 병합이 자동으로 일어난다.

### 적용 우선순위
1. **Wall 타일맵** (레이어 8) — 가장 중요. 이 타일맵의 충돌 수를 줄이면 투사체 `Physics2D.CircleCastAll` 호출 비용이 낮아짐
2. **Pit 타일맵** (Props 레이어) — 구덩이는 Trigger로만 쓰므로 이미 가볍다
3. **Floor** — 충돌 없음, 적용 불필요

### Room Reset 시 주의
`Room.ResetForReuse` 안에서 타일을 변경한다면 이후에 `compositeCollider.GenerateGeometry()` 한 번 호출이 필요하다. 빠진다면 이전 방 타일의 콜라이더가 남아 보이지 않는 벽이 생길 수 있다.

### 타일 추가 효과 (런타임 장애물)
물음표 이벤트나 장애물 등으로 런타임에 타일을 추가/제거한다면 `GenerateGeometry: Synchronous`로 설정해두거나, 변경 직후 수동 호출.

## 성능 수치 참고

| 설정 | 콜라이더 수(예) | 충돌 처리 시간 |
|------|----------------|---------------|
| TilemapCollider2D 단독 (200 타일) | 200개 | 기준 100% |
| + CompositeCollider2D (Polygons) | 4~8개 | 약 15~25% |

실제 수치는 방 형태에 따라 다르지만, 일반적으로 80% 이상 감소.

## 참고 링크
- Unity Docs — TilemapCollider2D: https://docs.unity3d.com/Manual/class-TilemapCollider2D.html
- Unity Docs — CompositeCollider2D: https://docs.unity3d.com/Manual/class-CompositeCollider2D.html
- Unity Learn — 2D Tilemap Extra: https://learn.unity.com/tutorial/introduction-to-tilemaps
- Unity Forum — Composite Collider2D performance thread: https://forum.unity.com/threads/compositecollider2d-performance.html
