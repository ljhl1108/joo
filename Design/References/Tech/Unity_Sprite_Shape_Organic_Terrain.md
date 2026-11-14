# Unity Sprite Shape — 오가닉 2D 지형

리서치 날짜: 2026-11-14

## 개요

**Unity 2D Sprite Shape**(`com.unity.2d.spriteshape`)는 스플라인(곡선 경로) 기반으로 유기적인 지형과 외곽선을 만드는 공식 Unity 패키지. 타일맵 직선 격자 대신 자연스러운 곡선 지형이 필요할 때 사용.

OnionCat은 `PolygonCollider2D` + 절차 생성 메시로 곡선 벽을 구현하고 있음. Sprite Shape는 동일한 목표를 **에디터에서 직접 편집 가능한 형태**로 달성하며, 아티스트가 직접 외곽선을 조정할 수 있다는 장점이 있음.

## Unity 구현 방법

### 패키지 설치
```
Package Manager → Unity Registry → 2D Sprite Shape
```

### 기본 구성 요소
| 컴포넌트 | 역할 |
|---------|------|
| `SpriteShapeController` | 스플라인 경로 · 스프라이트 연결 · 채우기 설정 |
| `SpriteShapeProfile` (ScriptableObject) | 스프라이트 등록, 각도별 스프라이트 선택 규칙 |
| `EdgeCollider2D` / `PolygonCollider2D` | 자동 충돌체 생성 옵션 |

### SpriteShapeProfile 설정
```
Create → 2D → Sprite Shape Profile
- Open Ended / Closed Shape 선택
- Sprites 리스트에 각도별(0°~360°) 스프라이트 등록
  - Corner: 꺾임 처리 스프라이트
  - Edge: 직선 구간 반복 스프라이트
- Fill Texture: 닫힌 도형 내부 채우기 텍스처 (반복 타일링)
```

### SpriteShapeController 설정
```
Add Component → 2D → SpriteShapeController
- Profile: 위에서 만든 Profile 연결
- Corner Mode: Automatic / Manual
- Collision Settings:
    - Use Edge Collider: ON (열린 경로 — 땅 위 플랫폼)
    - Use Polygon Collider: ON (닫힌 도형 — 섬, 방 외곽)
    - Detail: 충돌체 버텍스 밀도 (높을수록 정확하나 무거움)
- Fill Pixel Per Unit: 채우기 텍스처 반복 단위
```

### 스플라인 편집 (에디터)
- Sprite Shape Controller 선택 → Scene에서 스플라인 직접 조정
- 포인트 타입: **Linear** (꺾임), **Continuous** (C1 연속 곡선), **Broken** (각도 개별 조정)
- 포인트 추가: Ctrl+클릭(에디터 커서 모드)
- Height: 각 포인트의 선 높이 조정 (벽 두께)

### 런타임에서 스플라인 수정
```csharp
using UnityEngine.U2D;

SpriteShapeController ssc = GetComponent<SpriteShapeController>();
Spline spline = ssc.spline;

// 포인트 개수 변경
spline.Clear();
spline.InsertPointAt(0, new Vector3(-5, 0, 0));
spline.InsertPointAt(1, new Vector3(0, 2, 0));
spline.InsertPointAt(2, new Vector3(5, 0, 0));

// 포인트 타입 설정
spline.SetTangentMode(0, ShapeTangentMode.Continuous);
spline.SetLeftTangent(0, new Vector3(-1, 0.5f, 0));
spline.SetRightTangent(0, new Vector3(1, 0.5f, 0));

// 렌더러 갱신 필요
ssc.BakeCollider(); // 충돌체도 함께 갱신
```

### 절차 생성 + Sprite Shape 조합
```csharp
// 외부에서 계산한 꼭짓점 배열을 스플라인에 적용
void ApplyPointsToSpline(SpriteShapeController ssc, Vector2[] points)
{
    Spline spline = ssc.spline;
    spline.Clear();
    for (int i = 0; i < points.Length; i++)
    {
        spline.InsertPointAt(i, points[i]);
        spline.SetTangentMode(i, ShapeTangentMode.Linear); // 직선 연결
    }
    // Continuous로 바꾸면 자동으로 부드러운 곡선
}
```

## OnionCat의 현재 접근 vs Sprite Shape

| 항목 | OnionCat 현재 (절차 생성 메시+PolygonCollider2D) | Sprite Shape |
|------|------------------------------------------------|--------------|
| 편집 방법 | 코드로 꼭짓점 계산 → 자동 생성 | 에디터에서 직접 드래그 조정 |
| 반복성 | 방마다 굴곡이 달라짐 (런타임) | 고정 편집된 모양 (또는 런타임 변경 가능) |
| 아트 연결 | 반복 텍스처를 메시 UV로 직접 처리 | Profile에 각도별 스프라이트 등록 |
| 성능 | 메시 직접 생성 → 프레임당 계산 없음 | Sprite Shape 렌더러 → 약간 더 무거움 |
| 그려진 방 | 판정 Soften이 PolygonCollider2D 기반 | Sprite Shape도 PolygonCollider로 충돌 생성 가능 |

**OnionCat 현재 구조와 Sprite Shape는 충돌하지 않음** — 그려진 방의 판정 경계를 추후 아티스트가 에디터에서 직접 다듬을 때 Sprite Shape 활용 가능.

## OnionCat 적용 포인트

### 고정 장소 방 외곽선 직접 편집
농장·마을·등대탑 같은 고정 장소 방은 절차 생성이 필요 없음.  
→ 아티스트가 에디터에서 Sprite Shape로 외곽선을 직접 그리면 `PaintedRoomImporter`의 자동 판정 외에  
   **에디터 편집 가능한 세밀한 외곽선** 제공 가능.

### 반복 텍스처 벽 그림 연결
현재 `RoomShape`의 `wallFace` 반복 텍스처와 Sprite Shape의 Edge 스프라이트 반복이 거의 동일한 방식.  
→ 현재 코드를 Sprite Shape 렌더러로 교체하면 에디터에서 조정이 쉬워짐.

### 자동 충돌체 생성 비교
Sprite Shape의 `EdgeCollider2D` / `PolygonCollider2D` 자동 생성을 사용하면  
현재 `RoomShape.Apply`가 하는 충돌체 생성 코드를 단순화할 수 있음.

## 참고 링크

- 공식 문서: https://docs.unity3d.com/Packages/com.unity.2d.spriteshape@10.0/manual/index.html
- Unity 2D Sprite Shape 튜토리얼 (공식): https://learn.unity.com/tutorial/introduction-to-sprite-shape
- API Reference: https://docs.unity3d.com/Packages/com.unity.2d.spriteshape@10.0/api/UnityEngine.U2D.SpriteShapeController.html
- GitHub 샘플: https://github.com/Unity-Technologies/2d-spriteshape-samples
