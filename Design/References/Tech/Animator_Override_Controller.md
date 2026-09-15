# Animator Override Controller

리서치 날짜: 2026-09-15

## 개요

Unity의 **AnimatorOverrideController**는 기존 AnimatorController의 상태머신(StateMachine) 구조를 그대로 유지하면서, 특정 **AnimationClip만 런타임에 교체**할 수 있는 기능이다.

캐릭터 외형 변화(스킨, 무기 교체), 적 변형(강화형), 환경별 애니메이션 세트 전환 등에 활용한다.

**OnionCat 적용 이유**:
- Cat이 업그레이드를 획득하면 슬래시 모션이 바뀌어야 한다
- Crop이 특수 투사체 발사 아이템을 들면 발사 모션이 달라진다
- 같은 상태머신으로 여러 외형/무기 애니메이션을 처리 → 중복 AnimatorController 불필요

---

## Unity 구현 방법

### 1. 에셋 구성

```
Assets/
├── Animations/
│   ├── Cat_Base.controller          ← 기준 AnimatorController
│   ├── Cat_OverrideA.overrideController   ← Override용 에셋
│   └── Clips/
│       ├── Cat_Slash_Default.anim
│       ├── Cat_Slash_Upgraded.anim
│       └── Cat_Dash_Default.anim
```

Inspector에서: **Create → Animation → Animator Override Controller** 생성 후  
`Controller` 필드에 기준 AnimatorController를 드래그.

### 2. 에셋 레벨 설정 (Inspector)

AnimatorOverrideController 에셋 선택 시, 기준 Controller의 모든 클립 목록이 표시됨.  
교체할 클립만 오른쪽 슬롯에 대체 클립을 드래그하면 됨. 비워두면 원본 유지.

### 3. 런타임 전환 (C#)

```csharp
using UnityEngine;
using System.Collections.Generic;

public class CatAnimationSwapper : MonoBehaviour
{
    [SerializeField] private Animator animator;
    [SerializeField] private AnimatorOverrideController upgradeOverride;

    private RuntimeAnimatorController _baseController;

    private void Awake()
    {
        _baseController = animator.runtimeAnimatorController;
    }

    // 업그레이드 획득 시 호출
    public void ApplyUpgradeAnimation()
    {
        animator.runtimeAnimatorController = upgradeOverride;
    }

    // 원래로 되돌릴 때
    public void ResetToDefault()
    {
        animator.runtimeAnimatorController = _baseController;
    }
}
```

> [SerializeField] 변수가 있으므로 **유니티 에디터에서 Animator, OverrideController를 드래그 앤 드롭 설정 필요**

### 4. 런타임으로 클립 동적 교체

에셋 없이 코드로도 특정 클립만 바꿀 수 있다.

```csharp
public void SwapClipAtRuntime(AnimatorController baseController, AnimationClip original, AnimationClip replacement)
{
    var overrideController = new AnimatorOverrideController(baseController);

    var overrides = new List<KeyValuePair<AnimationClip, AnimationClip>>();
    overrideController.GetOverrides(overrides);

    for (int i = 0; i < overrides.Count; i++)
    {
        if (overrides[i].Key == original)
        {
            overrides[i] = new KeyValuePair<AnimationClip, AnimationClip>(original, replacement);
            break;
        }
    }

    overrideController.ApplyOverrides(overrides);
    animator.runtimeAnimatorController = overrideController;
}
```

**주의**: `new AnimatorOverrideController()`는 힙 할당 발생 → 런 시작 시나 업그레이드 획득 시 1회만 호출. Update()에서 호출 금지.

### 5. 현재 어떤 Controller인지 확인

```csharp
bool isUsingOverride = animator.runtimeAnimatorController is AnimatorOverrideController;
```

---

## OnionCat 적용 포인트

### Cat 슬래시 업그레이드 시각 피드백
```csharp
// UpgradeManager에서 호출
public void OnSlashUpgradeAcquired(SlashUpgradeSO upgrade)
{
    if (upgrade.overrideController != null)
        catAnimSwapper.ApplyUpgradeAnimation(upgrade.overrideController);
}
```
- 업그레이드 전: `Cat_Slash_Default.anim` (단순 모션)
- 업그레이드 후: `Cat_Slash_Wide.anim` (180도 넓은 궤적) 으로 자동 전환
- 상태머신은 그대로 → Idle/Walk/Slash 전환 로직 재작성 불필요

### Crop 발사 모션 분기
- 기본 투사체 → `Crop_Fire_Default.anim`
- 확산 샷 업그레이드 획득 → `Crop_Fire_Spread.anim`으로 Override
- 발사 위치나 파티클 이펙트도 AnimationEvent와 조합해 분기 가능

### 런 시작 시 초기화 패턴
```csharp
private void Start()
{
    // 런 시작 시 항상 기본 컨트롤러로 초기화
    animator.runtimeAnimatorController = _baseController;
}
```
퍼머데스 게임에서 런 재시작 시 이전 Override 상태가 남지 않도록 초기화 필수.

### 코드 아키텍처 제안
```
CharacterAnimationManager.cs
├── [SerializeField] Animator animator
├── [SerializeField] AnimatorOverrideController[] upgradeOverrides
├── ApplyOverride(int index)
└── ResetOverride()
```
ScriptableObject 기반 업그레이드 데이터에 `AnimatorOverrideController overrideController` 필드 추가.

---

## 참고 링크

- [Unity 공식 - AnimatorOverrideController](https://docs.unity3d.com/ScriptReference/AnimatorOverrideController.html)
- [Unity 공식 - Animator Override Controller 에셋](https://docs.unity3d.com/Manual/AnimatorOverrideController.html)
- [Unity Forum - RuntimeAnimatorController swap patterns](https://discussions.unity.com/t/how-to-use-animatoroverridecontroller-at-runtime/810)
- [Brackeys - Character Customization with Animator Override](https://www.youtube.com/watch?v=eXIuizGzY2A)
