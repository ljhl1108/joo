# 스쿼시 앤 스트레치 런타임 효과

리서치 날짜: 2026-11-12

## 개요

스쿼시 앤 스트레치(Squash & Stretch)는 디즈니 애니메이션의 12원칙 중 첫 번째로, 물체가 힘을 받을 때 형태가 찌그러지거나 늘어나는 효과다. 게임에서는 **코드로 스프라이트 scale을 순간적으로 변형**해 타격감·무게감·생동감을 더한다.

OnionCat에서는 별도 애니메이터 없이 순수 코드로 적용할 수 있으며, `HitFeelSettings`와 연동하면 수치를 실시간으로 조절할 수 있다.

기존 Hitstop(시간 정지)이나 Secondary_Motion(흔들림 추적)과 다르게, **스케일 자체를 순간 변형**하는 것이 핵심이다.

## 발생 타이밍과 효과 방향

| 이벤트 | 스쿼시 (납작) | 스트레치 (늘임) |
|---|---|---|
| 피격 | 충격 방향으로 납작 (0.1초) | — |
| 대쉬 시작 | — | 이동 방향으로 늘임 (0.08초) |
| 착지 | 세로 납작, 가로 넓어짐 | — |
| 점프 시작 | — | 세로로 늘임 (0.06초) |
| 공격 발동 | 약간 납작 (예비 동작) | 공격 방향으로 늘임 |
| 적 처치 | 커졌다 작아짐 | — |
| 아이템 획득 | — | 위로 살짝 늘임 |

## Unity 구현 방법

### 1. 기본 Squash/Stretch 코루틴

```csharp
using System.Collections;
using UnityEngine;

public class SquashStretch : MonoBehaviour
{
    [SerializeField] private Transform spriteRoot; // 스케일 적용 대상
    private Vector3 originalScale;
    private Coroutine activeRoutine;

    void Awake()
    {
        originalScale = spriteRoot.localScale;
    }

    // 방향성 없는 단순 충격 (피격)
    public void OnHit(float squashAmount = 0.6f, float duration = 0.12f)
    {
        Play(new Vector3(1f + (1f - squashAmount) * 0.5f,
                         squashAmount,
                         1f), duration);
    }

    // 방향성 스트레치 (대쉬, 공격)
    public void OnStretch(Vector2 direction, float stretchAmount = 1.4f, float duration = 0.1f)
    {
        bool horizontal = Mathf.Abs(direction.x) > Mathf.Abs(direction.y);
        Vector3 scale = horizontal
            ? new Vector3(stretchAmount, 1f / stretchAmount, 1f)
            : new Vector3(1f / stretchAmount, stretchAmount, 1f);
        Play(scale, duration);
    }

    // 착지 (세로 납작, 가로 퍼짐)
    public void OnLand(float squash = 0.65f, float duration = 0.15f)
    {
        Play(new Vector3(1f / squash, squash, 1f), duration);
    }

    private void Play(Vector3 targetScale, float duration)
    {
        if (activeRoutine != null) StopCoroutine(activeRoutine);
        activeRoutine = StartCoroutine(DoSquashStretch(targetScale, duration));
    }

    private IEnumerator DoSquashStretch(Vector3 target, float duration)
    {
        // 순간 변형
        spriteRoot.localScale = Vector3.Scale(originalScale, target);

        // 원래대로 복원 (스프링감)
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.unscaledDeltaTime; // Hitstop과 무관하게 동작
            spriteRoot.localScale = Vector3.Lerp(
                Vector3.Scale(originalScale, target),
                originalScale,
                elapsed / duration
            );
            yield return null;
        }
        spriteRoot.localScale = originalScale;
        activeRoutine = null;
    }
}
```

### 2. DOTween 버전 (더 간결)

```csharp
using DG.Tweening;

public class SquashStretchDOTween : MonoBehaviour
{
    [SerializeField] private Transform spriteRoot;
    private Vector3 originalScale;

    void Awake() => originalScale = spriteRoot.localScale;

    public void OnHit()
    {
        spriteRoot.DOKill();
        spriteRoot.localScale = originalScale;
        spriteRoot.DOPunchScale(new Vector3(0.3f, -0.35f, 0f), 0.25f, 1, 0.5f)
                  .SetUpdate(true); // timeScale 무시
    }

    public void OnDash(Vector2 dir)
    {
        spriteRoot.DOKill();
        bool h = Mathf.Abs(dir.x) > Mathf.Abs(dir.y);
        Vector3 punch = h ? new Vector3(0.4f, -0.25f, 0f) : new Vector3(-0.25f, 0.4f, 0f);
        spriteRoot.DOPunchScale(punch, 0.15f, 1, 0.3f).SetUpdate(true);
    }
}
```

### 3. HitFeelSettings 연동

```csharp
// HitFeelSettings.asset에 추가
[Header("Squash & Stretch")]
public float hitSquash = 0.6f;          // 피격 납작 비율
public float hitDuration = 0.12f;
public float dashStretch = 1.4f;        // 대쉬 늘임 비율
public float dashDuration = 0.08f;
public float landSquash = 0.65f;        // 착지 납작
public float landDuration = 0.15f;
```

```csharp
// 호출 예시
var feel = HitFeelSettings.Instance;
squashStretch.OnHit(feel.hitSquash, feel.hitDuration);
```

### 4. 스프라이트가 여러 레이어일 때 (OnionCat의 CatArtRenderer)

OnionCat의 고양이는 body·tail·pot·soil·crop 여러 스프라이트로 구성되어 있다. 개별 스프라이트를 각각 squash하면 어색하게 분리된다.

해결: **공통 부모 오브젝트에만 스케일 적용**

```csharp
// CatBody, CatTail, FlowerPot 등의 공통 부모 Transform을 spriteRoot로 지정
// CatArtRenderer.transform이 아닌 CatArtRenderer.spriteRoot를 별도 비어있는 오브젝트로 두기
```

또는 고양이 루트의 `SquashStretch` 컴포넌트가 모든 자식을 한 번에 처리하도록 하면 된다.

### 5. Hitstop과의 조화

Hitstop(시간 정지)과 Squash Stretch를 같이 쓸 때:
- Hitstop 중에는 Squash 고정 → Hitstop 해제 후 복원 애니메이션 시작
- `Time.unscaledDeltaTime` 사용 시 Hitstop(timeScale 조작)과 무관하게 복원됨

```csharp
// Hitstop 종료 콜백에서 복원 시작
HitstopManager.OnHitstopEnd += () => squashStretch.BeginRecover();
```

## 수치 가이드라인

| 목적 | squash Y | stretch 지속 | 느낌 |
|---|---|---|---|
| 가벼운 피격 | 0.80 | 0.08s | 거의 없음 (힌트 정도) |
| 보통 피격 | 0.65 | 0.12s | 뚜렷하지만 과하지 않음 |
| 큰 피격 | 0.45 | 0.20s | 강한 충격 |
| 대쉬 시작 | 1.35 stretch | 0.08s | 순간적 가속감 |
| 착지 | 0.65 squash | 0.15s | 착지 충격 |

- **pixelart에서는 squash 0.5 미만이 되면 한 픽셀짜리 선이 돼서 이상해 보임** → 최소 0.5 유지
- **정수 픽셀 고정 (Pixel Perfect Camera)**: PPU 96이면 스케일이 미세하게 바뀌어도 픽셀 그리드에 맞춰 렌더링되므로 걱정 불필요

## OnionCat 적용 포인트

| 적용 위치 | 이벤트 | 효과 |
|---|---|---|
| 고양이 피격 | `TakeDamage()` 호출 시 | 충격 방향 squash (0.65, 0.12s) |
| 고양이 대쉬 시작 | `Dash.Begin()` | 이동 방향 stretch (1.35, 0.08s) |
| 고양이 할퀴기 | 공격 모션 시작 | 공격 방향 stretch (1.2, 0.06s) |
| 작물 패링 | 패링 성공 | 가로 squash (0.55 X, 0.15s) → 튕겨냄 느낌 |
| 적 처치 | 적 HP 0 | 커졌다 작아지며 사라짐 (1.4→0, 0.3s) |
| HUD 체력 감소 | HP bar 업데이트 | HP bar stretch (1.0→1.2→1.0) |

기존 `HitFeelSettings.asset`에 squash/stretch 수치를 추가하면 플레이 중 조절 가능.

## 참고 링크

- Unity DOTween DOPunchScale: https://dotween.demigiant.com/documentation.php
- 디즈니 12원칙 — Squash and Stretch: https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation
- Game Feel (Bob Swain 책): https://www.gamefeelbook.com/
- Vlambeer 게임 피드백 가이드: https://www.youtube.com/watch?v=AJdEqssNZ-U
