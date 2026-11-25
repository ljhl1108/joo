# 2D Sprite 실루엣 / 오클루전 시스템

리서치 날짜: 2026-11-25

## 개요

탑다운 2D 게임에서 플레이어나 중요 오브젝트가 벽·장애물 뒤에 숨었을 때, 단색 실루엣(silhouette)으로 위치를 표시하는 시스템.

**OnionCat에 필요한 이유**:
- 그려진 방(PaintedRoom)에서 큰 소품·벽 뒤로 고양이가 완전히 가려질 수 있음
- "지금 고양이가 어디 있는지" 항상 알아야 하는 협동 게임에서 필수 UX
- 적이 장애물 뒤에 숨어도 위치 파악 가능 → 긴장감 + 편의성 균형

## 동작 원리

```
[렌더링 순서]
1. 먼저 벽/오브젝트를 스텐실 버퍼에 마킹
2. 캐릭터를 정상 렌더링
3. 가려진 부분(스텐실 테스트 실패)만 실루엣 쉐이더로 재렌더링
```

## Unity URP 구현 방법

### 방법 A: URP Render Objects Feature (권장)

**개념**: 카메라 렌더 패스를 두 번 — 1회차는 정상 렌더, 2회차는 ZTest Greater로 겹친 부분만

**설정 단계**:

1. **실루엣 머티리얼 만들기** (Shader Graph)
```
Unlit 그래프 → Base Color = 고정 색(예: 반투명 흰색)
Surface Type: Transparent, Blend Mode: Alpha
Render Face: Both
```

2. **URP Renderer에 Render Objects Feature 추가** x2
```
패스 1 (캐릭터 정상 렌더):
  Layer Mask: Character
  Event: AfterRenderingOpaques
  Override Depth: ZWrite On, ZTest LessEqual

패스 2 (실루엣 — 가려진 부분만):
  Layer Mask: Character  
  Event: AfterRenderingOpaques
  Override Material: 실루엣 머티리얼
  Override Depth: ZWrite Off, ZTest Greater
```

3. **캐릭터 레이어 분리**
```
캐릭터 SpriteRenderer → Sorting Layer: "Character"
벽/장애물 SpriteRenderer → Sorting Layer: "Wall" (Character보다 앞)
```

### 방법 B: SpriteMask 컴포넌트 (간단, 2D 전용)

```csharp
// 벽 오브젝트에 SpriteMask 추가
// 캐릭터 SpriteRenderer → Mask Interaction = Visible Outside Mask
// 실루엣 SpriteRenderer(자식) → Mask Interaction = Visible Inside Mask
```

**장점**: 코드 거의 불필요
**단점**: 마스크 형태가 고정, 복잡한 오클루더에 부적합

### 방법 C: 스텐실 버퍼 직접 사용

```hlsl
// 벽 쉐이더: 스텐실 버퍼에 1 쓰기
Stencil {
    Ref 1
    Comp Always
    Pass Replace
}

// 실루엣 쉐이더: 스텐실이 1인 픽셀에만 그리기
Stencil {
    Ref 1
    Comp Equal
}
// ZTest Greater → 벽 뒤에 있는 픽셀만
ZTest Greater
ZWrite Off
```

## 실용적 구현 팁

### 색상 선택
```
// 플레이어 실루엣: 반투명 흰색 (0.9 alpha)
// 적 실루엣: 반투명 빨간색 (0.5 alpha)
// 너무 진하면 UI처럼 보임 → 50~70% 투명도 권장
```

### 애니메이션 호환
- SpriteRenderer의 Sprite가 바뀌어도 쉐이더는 따라감 → 별도 처리 불필요
- **SortingGroup을 사용하는 고양이** (몸+꼬리+화분 파츠): 그룹 전체가 같이 실루엣되어야 함
  - 모든 파츠에 동일 레이어 적용

### 성능
- Render Objects Feature 패스 1회 추가 = 드로우콜 소량 증가
- 캐릭터 수가 2명뿐인 OnionCat에서는 무시 가능한 수준
- 필요 시 `IsOccluded` bool로 실루엣 활성화 여부를 코드로 토글

## OnionCat 적용 포인트

### 구현 우선순위
1. 고양이 실루엣 — 큰 소품·문 뒤에서도 흰색 실루엣으로 위치 표시
2. 적 실루엣 — 벽 뒤 적 위치 힌트 (적색, 더 흐릿하게)
3. 양파(HUD가 아닌 월드) — 고양이에 붙어 있으므로 고양이와 함께 처리됨

### 그려진 방(PaintedRoom)에서의 주의점
- 그려진 방의 판정은 `PolygonCollider2D`(Wall 레이어)를 씀
- 실루엣 오클루더도 Wall 레이어 오브젝트를 기준으로 하면 판정·시각이 일치
- Front 레이어(전경) 스프라이트만 오클루더로 사용 — Back은 배경이므로 제외

### SortingGroup 고려사항
- 고양이는 `SortingGroup`으로 묶여 있음 (CLAUDE.md 참고)
- Render Objects Feature는 SpriteRenderer 단위로 작동 → SortingGroup 내부 순서는 유지
- 만약 파츠가 따로 실루엣되면 `OverrideSortingGroup`으로 그룹 전체를 하나의 레이어로

## 참고 링크
- [Unity URP Render Objects 공식 문서 (Unity 6)](https://docs.unity3d.com/Manual/urp/renderer-features/how-to-custom-effect-render-objects.html)
- [Unity URP Render Objects 예시 (12.1)](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@12.1/manual/containers/how-to-custom-effect-render-objects.html)
- [Unity 포럼: Stencil Puzzle / Occlusion](https://discussions.unity.com/t/lost-in-urp-stencil-puzzle-problem-occlusion-with-invisible-walls/930515)
- [GraphicsCat Occlusion Vision 패키지](https://graphicscat.gitbook.io/graphicscat/documentation/occlusion-vision)
- [2D Sprite 실루엣 포럼 스레드](https://discussions.unity.com/t/shader-make-2d-sprite-visible-through-walls/765078)
