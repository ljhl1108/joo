# 픽셀아트 애니메이션 프레임 타이밍

리서치 날짜: 2026-10-25

## 개요

픽셀아트 애니메이션에서 "몇 프레임을 그리냐"보다 **"각 프레임을 얼마나 보여주냐"** (타이밍)가 타격감과 무게감을 결정한다. 프레임을 균등하게 배치하면 움직임이 기계적으로 보이고, 타이밍에 강약을 주면 적은 프레임으로도 생동감 있는 애니메이션이 완성된다. OnionCat처럼 전투가 핵심인 게임에서 공격 애니메이션의 타이밍은 "맞는 느낌"의 50%를 담당한다.

---

## 핵심 원칙

### 1. 균등 배치 = 죽은 애니메이션

모든 프레임을 같은 간격(예: 전부 100ms)으로 놓으면 움직임이 로봇처럼 보인다. **변화 있는 타이밍**이 생동감의 핵심이다.

### 2. 프레임 속도 기준선

| 목적 | 권장 fps |
|------|----------|
| 캐릭터 걸음·대기 | **8fps** (프레임당 약 120ms) |
| 공격·스킬 | **12fps** (프레임당 약 80ms), 히트 순간은 연장 |
| 파티클·스플래시 효과 | **24fps** 까지 올려도 자연스러움 |
| 픽셀아트 일반 시작점 | **12fps** — 여기서 타이밍 조정으로 느낌 결정 |

> Unity에서 프레임 수 = 고정, 각 프레임의 `Sample` 시간으로 타이밍 조정. Aseprite에서는 프레임 하단의 ms 숫자를 직접 편집.

### 3. 홀드 프레임 (Hold Frame)

주변 프레임보다 **오래 화면에 머무는 프레임** — 관객의 눈이 거기에 오래 머물며 "무게"를 느낀다.

공격 애니메이션 4프레임 예시 (12fps 기준):

```
[예비 동작]  60ms  ← 빠르게 스치듯 지나감
[찌르기]     40ms  ← 가장 빠름 (순간적인 동작)
[임팩트]    180ms  ← 홀드! 플레이어 눈이 여기 머묾
[복귀]      100ms  ← 자연스럽게 돌아옴
합계: 380ms (≈ 2.6fps 평균이지만 느낌은 훨씬 빠름)
```

### 4. 예비 동작 (Anticipation)

공격 직전 **반대 방향으로 살짝 당기는** 프레임 — 홀드를 짧게, 빠르게 지나가면서 "뭔가 온다"는 신호를 준다.

```
대기 → [예비: 뒤로 당김, 50ms] → [찌르기, 40ms] → [임팩트 홀드, 180ms] → 복귀
```

### 5. 스쿼시 & 스트레치 (저해상도 적용)

16×16 ~ 32×32 픽셀 스프라이트에서도 1~3픽셀 변형으로 충분히 표현 가능:

- **스트레치**: 빠른 이동 방향으로 1~2픽셀 늘리기 (달리기, 돌진)
- **스쿼시**: 착지·충격 순간 수직으로 1~2픽셀 납작하게
- 변형량은 속도에 비례 — 느린 동작은 작게, 폭발적 동작은 크게
- 너무 많은 변형은 오히려 부자연스럽다 (최대 픽셀 수의 10~15% 이내)

### 6. 느린 것 옆의 빠른 것

빠른 동작은 **느린 장면 옆에 있을 때만** 빠르게 보인다. 모든 동작이 빠르면 아무것도 빠르게 느껴지지 않는다.

- 대기 애니메이션은 느리고 부드럽게 (8fps)
- 공격 직전 예비 동작은 느리게 홀드
- 공격 순간만 폭발적으로 빠르게
- 이 대비가 "타격감"의 핵심

---

## Unity/Aseprite 구현 방법

### Aseprite에서 프레임 타이밍 설정

1. 각 프레임 하단의 ms 숫자 클릭 → 직접 입력
2. 여러 프레임 선택 후 우클릭 → Frame Properties로 일괄 변경
3. 태그(Tag) 단위로 애니메이션 확인: Tag 이름이 Unity 클립 이름이 되므로 `idle`, `attack`, `dash` 명확히

```lua
-- Aseprite Lua로 프레임 타이밍 일괄 조정 예시
local sprite = app.activeSprite
for i, frame in ipairs(sprite.frames) do
    if i == 3 then -- 임팩트 프레임
        frame.duration = 0.18 -- 180ms
    else
        frame.duration = 0.08 -- 80ms
    end
end
app.refresh()
```

### Unity Animator에서 프레임 타이밍 확인

- Animation 창에서 클립을 열면 프레임별 Sprite 전환 시점 확인 가능
- `Sample Rate`를 올리면 더 세밀한 타이밍 조정 가능 (기본 60)
- Aseprite importer (`com.unity.2d.aseprite`)가 ms 정보를 그대로 읽어와 자동으로 클립에 반영

### 런타임 타이밍 조정 — AnimationEvent 활용

```csharp
// AnimationEvent로 임팩트 프레임에 히트박스 활성화
// 공격 클립의 임팩트 프레임에 이벤트 삽입
public void OnAttackHit()
{
    hitbox.SetActive(true);
    Sfx.Play(SfxId.CatSlash);
    // HitFeelSettings의 히트스톱 발동
}

public void OnAttackEnd()
{
    hitbox.SetActive(false);
}
```

---

## OnionCat 적용 포인트

### 1. 고양이 할퀴기 임팩트 프레임

현재 할퀴기 애니메이션에 임팩트 홀드 프레임이 있는지 확인. 없다면:
- `attack` 클립에서 부채꼴 최대 펼침 프레임을 **150~200ms 홀드**로 설정
- 이 타이밍에 히트박스 활성화 + `SfxId.CatSlash` 재생
- `HitFeelSettings`의 히트스톱(맞은 적만 정지)과 맞물리면 체감 타격감 2배

### 2. 양파 씨앗 발사 "예비 동작"

현재 발사 애니메이션 앞에 **20~30ms짜리 예비 프레임** 1개 추가:
- 화분이 발사 방향 반대로 살짝 기우는 모션
- 이후 발사 → 복귀가 훨씬 생동감 있게 느껴짐
- 짧아서 발사 딜레이 체감 거의 없음

### 3. 대쉬 스트레치

대쉬 시작 1프레임: 이동 방향으로 **2픽셀 스트레치** → 빠른 이동감 강조
- `dash` 클립 첫 프레임에서 고양이를 수평 방향으로 2픽셀 늘린 스프라이트 삽입
- 프레임 하나라서 Aseprite 작업 5분 이내

### 4. 슬라임 돌진 예비 동작 강화

슬라임 돌진 예고(노란 선) 직전 프레임에 **몸을 반대 방향으로 당기는 예비 동작** 추가:
- 현재 텔레그래프가 색상(노란→빨간)으로만 구분됨
- 예비 동작 추가 시 시각적 직관성 향상 + 피하기 타이밍 힌트

### 5. 임팩트 프레임 ↔ 히트스톱 타이밍 맞추기

`HitFeelSettings`의 히트스톱 시간(맞은 적이 정지하는 시간)과 공격 애니메이션의 임팩트 홀드 프레임 시간을 맞추면:
- 히트스톱 동안 임팩트 프레임이 유지 → 시각적·물리적 피드백 동기화
- `HitFeelSettings.hitStopDurationMedium` ≈ 공격 애니메이션 임팩트 홀드 ms

---

## 참고 링크

- [Sprite AI: 90년된 애니메이션 이론이 왜 픽셀아트에도 통하나](https://www.sprite-ai.art/guides/animation-principles)
- [Wayline: Sprite Animation 강좌](https://www.wayline.io/learn/sprite-animation)
- [Divoom Blog: 픽셀아트 애니메이션 FPS 비교](https://divoom.com/blogs/setup-ideas/pixel-art-animation-frame-rate)
- [PixelJoint Forum: 타이밍 심화 토론](https://pixeljoint.com/Forum/printer_friendly_posts.asp?TID=27150)
- [Sprite AI Blog: 프레임 수 결정하기](https://www.sprite-ai.art/blog/sprite-animation-frames)
