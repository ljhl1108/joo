# Sprite Hit Flash System (스프라이트 피격 플래시)

리서치 날짜: 2026-08-07

## 개요

피격 시 적이나 플레이어의 스프라이트가 순간적으로 흰색(또는 빨간색)으로 번쩍이는 효과.
로그라이크/액션 게임에서 "맞았다"는 것을 시각적으로 전달하는 가장 기본이자 강력한 피드백 중 하나.

Hades, Dead Cells, Binding of Isaac 등 거의 모든 상업 로그라이크에 필수로 사용.
OnionCat의 경우 적 피격, 플레이어 피격, 패리 성공 등 다양한 상황에 적용할 수 있다.

---

## Unity 구현 방법

### 방법 1: MaterialPropertyBlock (권장 — 인스턴싱 보존)

MaterialPropertyBlock을 사용하면 머터리얼 자체를 교체하지 않아 **GPU 인스턴싱과 배칭을 유지**한다.
퍼포먼스에 가장 유리.

```csharp
using UnityEngine;
using System.Collections;

[RequireComponent(typeof(SpriteRenderer))]
public class HitFlashEffect : MonoBehaviour
{
    [SerializeField] private float flashDuration = 0.1f;
    [SerializeField] private Color flashColor = Color.white;

    private SpriteRenderer _spriteRenderer;
    private MaterialPropertyBlock _mpb;
    private static readonly int FlashColorID = Shader.PropertyToID("_FlashColor");
    private static readonly int FlashAmountID = Shader.PropertyToID("_FlashAmount");

    private Coroutine _flashCoroutine;

    void Awake()
    {
        _spriteRenderer = GetComponent<SpriteRenderer>();
        _mpb = new MaterialPropertyBlock();
    }

    public void TriggerFlash()
    {
        if (_flashCoroutine != null)
            StopCoroutine(_flashCoroutine);
        _flashCoroutine = StartCoroutine(FlashRoutine());
    }

    private IEnumerator FlashRoutine()
    {
        SetFlash(1f);
        yield return new WaitForSeconds(flashDuration);
        SetFlash(0f);
        _flashCoroutine = null;
    }

    private void SetFlash(float amount)
    {
        _spriteRenderer.GetPropertyBlock(_mpb);
        _mpb.SetColor(FlashColorID, flashColor);
        _mpb.SetFloat(FlashAmountID, amount);
        _spriteRenderer.SetPropertyBlock(_mpb);
    }
}
```

### 필요한 셰이더 설정

기본 Sprite-Lit-Default 셰이더는 `_FlashAmount` 프로퍼티가 없으므로 커스텀 셰이더 필요.
**Shader Graph (URP)** 사용 시:

1. `Window → Shader Graph → New → Sprite Lit` 생성
2. 기존 Main Texture 샘플 노드 뒤에 `Lerp` 노드 추가
   - A: 원본 색상, B: `_FlashColor` 파라미터, T: `_FlashAmount` 파라미터
3. 결과를 Fragment의 Base Color에 연결
4. Shader Graph에서 `_FlashColor`와 `_FlashAmount`를 `Exposed` 속성으로 노출

또는 **셰이더 없이 간단하게** SpriteRenderer.color 이용:

```csharp
// 더 단순한 방법 — 인스턴싱 안됨, 소규모 프로젝트에서는 충분
IEnumerator FlashRoutine()
{
    _spriteRenderer.color = flashColor;
    yield return new WaitForSeconds(flashDuration);
    _spriteRenderer.color = Color.white;
}
```

### 방법 2: 머터리얼 교체 방식

원본 머터리얼 ↔ 흰색 머터리얼 전환. 구현이 직관적이지만 드로우콜이 늘어남.

```csharp
[SerializeField] private Material normalMaterial;
[SerializeField] private Material flashMaterial;  // 순수 흰색 머터리얼

IEnumerator FlashRoutine()
{
    _spriteRenderer.material = flashMaterial;
    yield return new WaitForSeconds(flashDuration);
    _spriteRenderer.material = normalMaterial;
}
```

---

## 응용: 피격 유형별 플래시 색상

| 상황 | 색상 | Duration |
|------|------|----------|
| 적 피격 (일반) | 흰색 (1,1,1,1) | 0.08초 |
| 적 피격 (크리티컬) | 노랑 (1,0.9,0,1) | 0.12초 |
| 플레이어 피격 | 빨강 (1,0.2,0.2,1) | 0.15초 |
| 패리 성공 | 파랑/시안 (0,0.9,1,1) | 0.2초 |
| 무적 상태 (IFrame) 플리커 | 교번 흰→원본 | IFrame 지속 시간 동안 |

---

## 무적 IFrame 깜박임 구현

```csharp
IEnumerator InvincibilityFlicker(float duration, float flickerRate = 0.05f)
{
    float elapsed = 0f;
    while (elapsed < duration)
    {
        _spriteRenderer.enabled = !_spriteRenderer.enabled;
        yield return new WaitForSeconds(flickerRate);
        elapsed += flickerRate;
    }
    _spriteRenderer.enabled = true;
}
```

---

## OnionCat 적용 포인트

### 상황별 적용

```
Cat 대시 중 (무적):
  → InvincibilityFlicker (0.05초 간격 깜박임)

Cat 피격:
  → 빨강 플래시 0.15초 + 히트스톱 0.05초 (Time.timeScale)

적 피격 (Cat 베기):
  → 흰색 플래시 0.08초

적 피격 (Crop 투사체):
  → 흰색 플래시 0.08초

Crop 패리 성공:
  → 시안 플래시 0.2초 + 화면 흔들림 추가

약점 공격 (근접 전용 적에 Cat 베기):
  → 노랑 플래시 0.12초 + "CRITICAL" 텍스트 팝업
```

### 컴포넌트 배치

```
Enemy (GameObject)
├── SpriteRenderer
├── HitFlashEffect     ← 이 컴포넌트 부착
└── EnemyHealth        ← TakeDamage()에서 hitFlash.TriggerFlash() 호출
```

### EnemyHealth 연동 예시

```csharp
public class EnemyHealth : MonoBehaviour
{
    [SerializeField] private HitFlashEffect hitFlash;

    public void TakeDamage(int amount, DamageType type)
    {
        currentHP -= amount;

        // 데미지 타입에 따라 다른 플래시
        Color fc = type == DamageType.Critical ? Color.yellow : Color.white;
        hitFlash.TriggerFlash(fc, 0.08f);

        if (currentHP <= 0) Die();
    }
}
```

---

## 참고 링크

- Unity MaterialPropertyBlock 공식 문서: https://docs.unity3d.com/ScriptReference/MaterialPropertyBlock.html
- Shader Graph Hit Flash 튜토리얼 (Brackeys): https://www.youtube.com/watch?v=LnAoD7hgDxw
- Sprite Lit Custom Shader URP: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/ShaderGraph.html
- 인디 게임 피격 피드백 분석: https://www.gamedeveloper.com/design/the-art-of-game-feel-juicing-your-hits
