# AnimationEvent 심화

리서치 날짜: 2026-09-05

## 개요

Unity의 **AnimationEvent**는 애니메이션 타임라인의 특정 프레임에 C# 함수를 자동 호출하는 기능이다. 픽셀아트 액션게임에서 다음 문제를 해결한다:

- 슬래시 애니메이션의 **몇 번째 프레임**에 히트박스를 켜야 하는가?
- 발소리 SFX를 **발이 닿는 프레임**에 정확히 재생하려면?
- 파티클 이펙트를 **공격 임팩트 순간**에만 스폰하려면?

Update()에서 타이머로 관리하면 프레임 레이트 의존적 오류가 생긴다. AnimationEvent는 애니메이터가 직접 호출 타이밍을 제어하므로 **애니메이션과 로직이 항상 동기화**된다.

---

## Unity 구현 방법

### 1. Animation 창에서 이벤트 추가

1. **Window → Animation → Animation** 창 열기
2. 캐릭터 오브젝트 선택 후 이벤트를 추가할 클립 선택
3. 타임라인 원하는 프레임에 커서 이동
4. **이벤트 버튼(깃발 아이콘)** 클릭 → 이벤트 마커 생성
5. Inspector에서 호출할 **함수명** 입력

```
[Function] EnableHitbox
[Float]    0       ← 필요 시 파라미터 전달
[Int]      0
[String]   ""
[Object]   None
```

> 주의: 함수는 반드시 해당 오브젝트에 붙은 MonoBehaviour에 존재해야 함

### 2. 받는 C# 함수 작성

```csharp
public class CatAttack : MonoBehaviour
{
    [SerializeField] private GameObject slashHitbox;
    [SerializeField] private ParticleSystem slashVFX;
    [SerializeField] private AudioSource audioSource;
    [SerializeField] private AudioClip slashSFX;

    // AnimationEvent에서 호출 — 공격 히트박스 활성
    private void EnableHitbox()
    {
        slashHitbox.SetActive(true);
    }

    // AnimationEvent에서 호출 — 히트박스 비활성
    private void DisableHitbox()
    {
        slashHitbox.SetActive(false);
    }

    // AnimationEvent에서 호출 — 슬래시 VFX + SFX
    private void PlaySlashEffect()
    {
        slashVFX.Play();
        audioSource.PlayOneShot(slashSFX);
    }
}
```

### 3. 파라미터 전달 패턴

AnimationEvent는 함수에 **하나의 파라미터** 전달 가능:

```csharp
// int 파라미터 받기 — 발소리 타입 구분
private void PlayFootstep(int surfaceType)
{
    AudioClip clip = surfaceType == 0 ? grassClip : stoneClip;
    audioSource.PlayOneShot(clip);
}

// string 파라미터 받기 — 범용 이벤트 발행
private void BroadcastAnimEvent(string eventName)
{
    // 예: "onAttackStart", "onRoll", "onLand"
    onAnimationEvent?.Invoke(eventName);
}
```

### 4. AnimationEvent 오브젝트 직접 사용

함수 시그니처에 `AnimationEvent` 타입을 받으면 모든 필드에 접근:

```csharp
private void OnAnimEvent(AnimationEvent evt)
{
    Debug.Log($"프레임: {evt.time}, intParam: {evt.intParameter}");
    if (evt.intParameter == 1) EnableHitbox();
    else DisableHitbox();
}
```

### 5. Script로 AnimationEvent 코드 추가 (런타임)

```csharp
// 런타임에 동적으로 이벤트 추가 (편집기용, 게임 내 잘 안 씀)
AnimationClip clip = /* 클립 참조 */;
AnimationEvent evt = new AnimationEvent();
evt.functionName = "EnableHitbox";
evt.time = 0.15f; // 초 단위
clip.AddEvent(evt);
```

---

## 픽셀아트 히트박스 타이밍 실전 가이드

### Cat 슬래시 애니메이션 예시 (8프레임, 12fps)

```
프레임:  0    1    2    3    4    5    6    7
상태:   준비  준비  스윙  스윙  임팩  임팩  복귀  복귀
히트박스:  X    X    X    O    O    X    X    X
VFX:       X    X    X    X    O    X    X    X
SFX:       X    X    X    O    X    X    X    X
```

이벤트 배치:
- 프레임 3 → `EnableHitbox()` 호출
- 프레임 3 → `PlaySlashSFX()` 호출
- 프레임 4 → `PlaySlashVFX()` 호출
- 프레임 5 → `DisableHitbox()` 호출

### 중요: "너그러운 히트박스" + AnimationEvent

히트박스를 프레임 정확도로 켜고 끄면 판정이 너무 짧아질 수 있다. 실제 느낌을 위해:
- **히트박스 활성 구간을 1~2프레임 더** 유지
- 대신 **적의 피격 무적(invincibility frames)** 0.2~0.5초로 다중 히트 방지

---

## OnionCat 적용 포인트

### Cat의 180° 슬래시
```
이벤트 타이밍:
- frame 2: EnableMeleeHitbox()   ← 부채꼴 콜라이더 ON
- frame 4: SpawnSlashVFX()       ← 파티클 스폰
- frame 5: DisableMeleeHitbox()  ← 콜라이더 OFF
```

### Onion의 투사체 발사
```
- frame 3: FireProjectile()  ← 실제 투사체 인스턴스화
- frame 6: ReturnToIdle()    ← 조준 UI 숨기기
```

### Onion의 방어막 패리 윈도우
```
- frame 0: EnableParryWindow()   ← Trigger 콜라이더 ON
- frame 2: DisableParryWindow()  ← Trigger 콜라이더 OFF (좁은 패리 타이밍)
- frame 3: EnableBlockWindow()   ← 일반 방어 시작
- frame 8: DisableBlockWindow()  ← 방어 종료
```

### 공통 발걸음 SFX
Cat 걷기/달리기 애니메이션에:
- 발이 땅에 닿는 프레임마다 `PlayFootstep(int surfaceType)` 이벤트 → 바닥 타일 타입에 맞는 SFX 재생

---

## 주의사항 & 함정

| 상황 | 문제 | 해결 |
|------|------|------|
| 이벤트 함수 없음 | 경고 없이 이벤트 무시됨 | 정확한 함수명 확인, private도 동작함 |
| 오브젝트 비활성 | 컴포넌트 비활성 시 이벤트 미도착 | `enabled = false`가 아닌 `gameObject.SetActive`는 OK |
| 애니메이터 전환 중 이벤트 | 클립 전환 직전 이벤트 소실 가능 | Exit Time + 이벤트 타이밍 여유 확보 |
| 멀티플레이어 공유 클립 | 같은 클립의 이벤트가 모든 인스턴스에 발생 | 각 인스턴스에 컴포넌트가 있으면 자동으로 각자 발생 (정상) |

---

## 참고 링크

- Unity 공식 문서: https://docs.unity3d.com/Manual/AnimationEventsOnImportedClips.html
- Unity Learn - Animation Events: https://learn.unity.com/tutorial/working-with-animation-events
- 커뮤니티 가이드 (Brackeys 스타일): "Unity Animation Events explained" 검색
- 픽셀아트 히트박스 타이밍 실전: https://www.youtube.com/watch?v=wuMbAb_MHTE (GameMaker's Toolkit - "How Celeste Feels So Good to Play")
