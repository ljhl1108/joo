# 발소리 / 표면 사운드 시스템 (Footstep Surface Sound System)

리서치 날짜: 2026-11-23

## 개요

캐릭터가 걸을 때 발 아래 표면 종류(돌·흙·잔디·물웅덩이 등)에 따라 다른 발소리를 재생하는 시스템. OnionCat처럼 탑다운 2D 픽셀 아트 게임에서 발소리는 체감 무게감·속도감을 크게 높이고, 방에 들어갈 때 분위기(흙바닥·돌바닥)를 소리로도 전달한다.

## Unity 구현 방법

### 1. 표면 타입 정의
```csharp
public enum SurfaceType { Stone, Dirt, Grass, Water, Wood }
```

### 2. 표면 감지 — Physics2D 레이캐스트
```csharp
// 발 위치에서 아래로 짧은 레이캐스트
RaycastHit2D hit = Physics2D.Raycast(footPosition, Vector2.down, 0.1f, groundLayer);
if (hit.collider != null) {
    SurfaceTag tag = hit.collider.GetComponent<SurfaceTag>();
    currentSurface = tag != null ? tag.surfaceType : SurfaceType.Stone;
}
```

### 3. 타일맵 기반 표면 감지 (대안)
타일맵을 쓸 경우 `Tilemap.GetTile(cellPos)` → 커스텀 `SurfaceTile : TileBase`의 `surfaceType` 필드 읽기. OnionCat은 `RoomFloor` 타일을 이미 쓰므로 이 방법이 더 깔끔하다.

### 4. SoundBank 연동
```csharp
// SfxId에 표면별 발소리 ID 추가 (예: SfxId.FootStone, SfxId.FootDirt ...)
// AnimationEvent에서 호출
public void OnFootstepEvent() {
    SfxId id = currentSurface switch {
        SurfaceType.Dirt  => SfxId.FootDirt,
        SurfaceType.Grass => SfxId.FootGrass,
        _                 => SfxId.FootStone,
    };
    Sfx.Play(id);
}
```

### 5. AnimationEvent로 타이밍 제어
Aseprite 애니메이션의 걷기 태그(walk) 프레임에 `OnFootstepEvent` 이벤트를 붙여 발이 땅에 닿는 순간에 재생. 프레임 타이밍이 맞지 않으면 미끄러지는 느낌이 난다.

### 6. 볼륨·피치 랜덤화 (SoundBank)
동일 사운드 반복을 피하려면 `SoundBank`에 `pitchVariance ±0.1`, `volumeVariance ±0.05` 설정. 같은 소리 연속 재생을 막으려면 마지막 재생 인덱스를 추적하여 다른 오디오 클립으로 순환.

## OnionCat 적용 포인트

| 적용 포인트 | 구현 위치 |
|---|---|
| 발소리 표면 구분 | `SurfaceType` enum + `SoundBank`에 발소리 추가 |
| 고양이 발소리 | `CatController`의 walk 애니메이션에 `AnimationEvent` 삽입 |
| 표면 감지 | `RoomFloor` 타일에 `SurfaceType` 필드 추가 or Physics2D 레이캐스트 |
| 발소리 등록 | `SfxId` 추가 → `Assets/Audio/SFX/foot_stone_0.ogg` 등 CC0 음원 |
| 볼륨 | 발소리는 보통 UI SFX보다 훨씬 작게 (전투음에 묻히지 않게) |

**주의**: 그려진 방(PaintedRoom)에서는 타일 대신 `Physics2D`로 Wall 레이어를 물어 표면 판정. 고양이 충돌체가 둘(몸+발)이므로 발 콜라이더 위치에서 레이캐스트해야 정확하다.

## 참고 링크

- [Unity AnimationEvent docs](https://docs.unity3d.com/Manual/animeditor-AnimationEvents.html)
- [Freesound.org footstep CC0 packs](https://freesound.org/search/?q=footstep&filter=license%3A%22Creative+Commons+0%22)
- [Sonniss GDC Audio Bundle (annual free CC0)](https://sonniss.com/gameaudiogdc)
