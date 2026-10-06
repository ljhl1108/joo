# Aseprite → Unity 애니메이션 파이프라인

리서치 날짜: 2026-10-06

## 개요
Aseprite로 그린 픽셀아트 스프라이트를 Unity에서 자동으로 애니메이션 클립으로 만드는 전체 워크플로우.
`com.unity.2d.aseprite` 패키지(Unity 공식)를 사용하면 `.aseprite` 파일을 Assets에 넣는 것만으로
Sprite Sheet + Animation Clip + Animator Controller 초안이 자동 생성된다.
OnionCat은 PPU 32, URP 2D 기반이므로 임포터 설정이 정확해야 픽셀이 흐려지지 않는다.

---

## Unity 구현 방법

### 1. 패키지 설치
```
Package Manager → Unity Registry → "2D Aseprite Importer" (com.unity.2d.aseprite) → Install
Unity 6 기준 버전: 3.0.x
```

### 2. Aseprite에서 태그 규칙 정하기
```
태그 이름 = Unity AnimationClip 이름
권장 네이밍 (OnionCat 기준):
  idle       → Idle 클립
  walk       → Walk 클립
  attack     → Attack 클립
  attack2    → Attack2 클립 (추가 공격)
  dash       → Dash 클립
  hurt       → Hurt 클립
  die        → Die 클립

주의: 태그 없는 프레임은 "Default" 클립 하나로 묶임
```

### 3. .aseprite 파일 임포트 설정
Assets에 .aseprite 파일을 드래그 후 Inspector:

```
Texture Type: Sprite (2D and UI)
Pixels Per Unit: 32          ← OnionCat PPU 와 일치 필수
Filter Mode: Point (no filter)  ← 픽셀아트는 Point 필수
Compression: None             ← 픽셀 정확도 유지
Generate Physics Shape: OFF  ← 필요 없음
Pivot: Custom 또는 Bottom     ← 캐릭터는 Bottom이 YSort 기준

Sprite Mode: Multiple (자동)
Animation: Generate → "Animator Controller and Animator" 선택
```

### 4. 생성되는 에셋 구조
```
Assets/
  Characters/
    Cat.aseprite          ← 원본 (편집은 Aseprite에서)
    Cat_idle.anim         ← 자동 생성 AnimationClip (태그별)
    Cat_walk.anim
    Cat_attack.anim
    ...
    Cat_Sprite_0.png      ← 자동 생성 atlas (편집 금지)
    Cat.controller        ← 자동 생성 AnimatorController (초안)
```

### 5. AnimatorController 수동 연결
자동 생성된 `.controller`는 초안 — 실제 게임 로직은 직접 구성:
```
Animator States:
  Idle  (Cat_idle.anim)
  Walk  (Cat_walk.anim)  
  Attack (Cat_attack.anim)
  Hurt  (Cat_hurt.anim)
  Die   (Cat_die.anim)

Transition 조건 (Parameter 예시):
  float Speed   → Idle ↔ Walk (Speed > 0.1)
  trigger Attack → any → Attack → Idle
  trigger Hurt   → any → Hurt → Idle
  bool  IsDead   → any → Die (no exit)
```

### 6. AnimationEvent 활용
Unity AnimationEvent를 클립 특정 프레임에 삽입:
```csharp
// Animation window에서 이벤트 추가 → 스크립트 메서드 호출
public void OnAttackHitboxActive()   // 히트박스 활성화
public void OnAttackHitboxDeactivate()  // 히트박스 비활성화
public void OnFootstepSound()         // 발소리 SFX
public void OnDustParticle()          // 먼지 파티클
```
```
// 타이밍 예시 (Cat idle 8프레임 기준):
프레임 3: OnAttackHitboxActive()
프레임 7: OnAttackHitboxDeactivate()
```

### 7. 파일 업데이트 워크플로우
1. Aseprite에서 `.aseprite` 수정 (프레임 추가/태그 변경)
2. 파일 저장
3. Unity가 자동 reimport → 클립/atlas 재생성
4. `.controller`는 유지됨 (새 태그가 생기면 새 클립 파일 추가)
5. `git diff` 확인 — Sprite atlas가 바뀌었는지 확인

### 8. 주의: Sprite Border (9-slice)
CLAUDE.md에 명시됨:
```csharp
// TextureImporter.spriteBorder가 Unity 6에서 안 먹힘
// SpriteDataProviderFactories 사용 필요 (Sprite Editor 경유)
```
캐릭터 스프라이트에는 보통 border 불필요 — UI 요소에만 적용.

### 9. CLI로 Aseprite 정보 조회
```bash
A="/d/SteamLibrary/steamapps/common/Aseprite/Aseprite.exe"
"$A" --batch --list-tags <파일.aseprite>    # 태그 목록 (클립 이름 확인)
"$A" --batch --list-layers <파일.aseprite>  # 레이어 구조 확인
"$A" --batch --list-slices <파일.aseprite>  # 슬라이스 확인
```

---

## OnionCat 적용 포인트

### 고양이 (Cat) 애니메이션 목록
```
idle       8프레임  — 꼬리 흔들기, 귀 움직임
walk       6프레임  — 4방향 대신 단방향 + 좌우 flip
dash       4프레임  — 납작해지는 이징
attack     8프레임  — 3~6프레임에 히트박스 활성
attack_air 6프레임  — 공중 할퀴기 (점프 없이 상단 에임)
hurt       4프레임  — 피격 노출
die        12프레임 — 쓰러지기
```

### 양파 (Onion) 애니메이션 목록
```
idle_front   6프레임  — 화분 위 흔들림
idle_back    6프레임  — 뒤 에임 (고양이 이동 방향 기준)
shoot        8프레임  — 1~4프레임 차징, 5~8프레임 발사
shield_up    4프레임  — 방패 올리기
shield_loop  2프레임  — 방패 유지 루프
shield_down  4프레임  — 방패 내리기
parry        6프레임  — 패리 성공 연출
hurt         4프레임  — 화분 흔들림
```

### 공유 바디 아키텍처에서 주의사항
OnionCat은 고양이가 바디를 가지고 양파는 오버레이:
```
Sorting Order:
  Cat sprite:   0   (YSort 처리)
  Onion sprite: 2   (Cat 위에 항상 렌더링)
  HitEffect:    100 (항상 최상위)

Pivot:
  Cat:   Bottom (발 기준 YSort)
  Onion: Bottom of flowerpot (고양이 등 위치 기준)
```

### 파일 경로 규칙 (Unity 프로젝트)
```
Assets/
  Art/
    Characters/
      Cat/
        Cat.aseprite          ← 원본
        Cat_idle.anim         ← 자동 생성
        Cat.controller        ← 수동 관리
      Onion/
        Onion.aseprite
        Onion_idle.anim
        Onion.controller
```

### 런타임 컴파일 없이 클립 교체 (ClawStyle)
OnionCat `ClawStyle` 업그레이드 시 attack 애니메이션 교체 필요:
```csharp
// AnimatorOverrideController 사용
var overrideCtrl = new AnimatorOverrideController(catAnimator.runtimeAnimatorController);
overrideCtrl["attack"] = clawStyle.attackClip;  // 런타임 클립 교체
catAnimator.runtimeAnimatorController = overrideCtrl;
```
→ `Animator_Override_Controller.md` 참고

---

## 참고 링크

- Unity 2D Aseprite Importer 공식 문서: https://docs.unity3d.com/Packages/com.unity.2d.aseprite@3.0/manual/index.html
- Aseprite CLI 참고: https://www.aseprite.org/docs/cli/
- Unity AnimationEvent 공식: https://docs.unity3d.com/Manual/AnimationEventsOnImportedClips.html
- AnimatorOverrideController 공식: https://docs.unity3d.com/ScriptReference/AnimatorOverrideController.html
- 픽셀아트 Unity 임포트 설정 가이드: https://docs.unity3d.com/Manual/PixelPerfectSetup.html
- Aseprite Tags + Unity 튜토리얼: https://www.youtube.com/watch?v=HusvGeEDgAo
