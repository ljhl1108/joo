# 에너미 월드 스페이스 HP바 시스템 (Enemy World-Space HP Bar)

리서치 날짜: 2026-07-28

## 개요

일반 적 캐릭터의 머리 위에 HP바를 실시간으로 표시하는 시스템이다. Boss_Health_Bar_UI.md에서 다루는 보스 HP바(화면 상단 고정 UI)와는 달리, 이 시스템은 **월드 공간에 떠있는 HP바**로, 각 적 개별적으로 붙어다닌다. 타격 시에만 나타났다가 일정 시간 후 사라지는 패턴이 일반적이다.

---

## 설계 결정: Screen Space vs World Space

| 방식 | 장점 | 단점 |
|------|------|------|
| **Screen Space Overlay** | 항상 일정 크기, 카메라 영향 없음 | 적 위치와 별도 계산 필요 |
| **World Space Canvas** | 적과 함께 자동 이동, 자연스러움 | 카메라 줌에 따라 크기 변함 |
| **Billboard Quad (Shader)** | 가장 퍼포먼스 효율적 | 구현 복잡도 높음 |

**OnionCat 권장**: World Space Canvas 방식 (보스는 Screen Space, 일반 적은 World Space로 구분)

---

## Unity 구현 방법

### 1. HP바 프리팹 구조

```
Enemy_HPBar (Canvas - World Space)
  └─ Background (Image - 검정 배경)
  └─ Fill (Image - Image Type: Filled, Fill Method: Horizontal)
  └─ [Optional] DamageFlash (Image - 흰색, 타격 잔상 효과)
```

Canvas 설정:
- Render Mode: **World Space**
- Canvas Scaler 비활성화
- Order In Layer: UI (적 스프라이트보다 위에 표시)

### 2. EnemyHPBar 컴포넌트

```csharp
using UnityEngine;
using UnityEngine.UI;

public class EnemyHPBar : MonoBehaviour
{
    [SerializeField] private Image fillImage;
    [SerializeField] private Image flashImage;
    [SerializeField] private CanvasGroup canvasGroup;

    [SerializeField] private float hideDelay = 2f;
    [SerializeField] private float fadeSpeed = 3f;
    [SerializeField] private float flashDuration = 0.1f;

    private float hideTimer;
    private bool isVisible;
    private Coroutine flashCoroutine;

    void Awake()
    {
        canvasGroup.alpha = 0f;
        isVisible = false;
    }

    void Update()
    {
        // 카메라를 항상 바라보도록 (Billboard)
        transform.rotation = Camera.main.transform.rotation;

        if (isVisible)
        {
            hideTimer -= Time.deltaTime;
            if (hideTimer <= 0f)
            {
                isVisible = false;
            }
        }

        float targetAlpha = isVisible ? 1f : 0f;
        canvasGroup.alpha = Mathf.MoveTowards(
            canvasGroup.alpha, targetAlpha, fadeSpeed * Time.deltaTime);
    }

    public void UpdateHP(float current, float max)
    {
        float ratio = Mathf.Clamp01(current / max);
        fillImage.fillAmount = ratio;

        // 색상: HP 비율에 따라 초록→노랑→빨강
        fillImage.color = Color.Lerp(Color.red, Color.green, ratio);

        ShowBar();
        PlayFlash();
    }

    private void ShowBar()
    {
        isVisible = true;
        hideTimer = hideDelay;
    }

    private void PlayFlash()
    {
        if (flashCoroutine != null) StopCoroutine(flashCoroutine);
        flashCoroutine = StartCoroutine(FlashRoutine());
    }

    private IEnumerator FlashRoutine()
    {
        flashImage.enabled = true;
        yield return new WaitForSeconds(flashDuration);
        flashImage.enabled = false;
    }
}
```

### 3. Enemy에 HP바 연결

```csharp
// EnemyHealth.cs
public class EnemyHealth : MonoBehaviour
{
    [SerializeField] private float maxHP = 100f;
    [SerializeField] private EnemyHPBar hpBar;  // 유니티 에디터에서 드래그 앤 드롭 설정 필요

    private float currentHP;

    void Awake()
    {
        currentHP = maxHP;
    }

    public void TakeDamage(float amount)
    {
        currentHP = Mathf.Max(0f, currentHP - amount);
        hpBar.UpdateHP(currentHP, maxHP);

        if (currentHP <= 0f)
            Die();
    }

    private void Die()
    {
        // 적 사망 처리
        Destroy(gameObject);
    }
}
```

### 4. HP바 위치 오프셋 설정

```csharp
// EnemyHPBar가 붙은 Canvas의 RectTransform 오프셋
// Awake()에서 적 스프라이트 크기에 따라 동적 설정 가능

void SetOffset(float enemyHeight)
{
    transform.localPosition = new Vector3(0f, enemyHeight * 0.6f, 0f);
}
```

### 5. 오브젝트 풀링과 통합 (선택)

적 수가 많아질 경우 HP바 Canvas 자체를 풀링:

```csharp
// HP바를 미리 풀에 생성하고, 적 스폰 시 대여 / 사망 시 반환
HPBarPool.Instance.Get(enemy.transform);
HPBarPool.Instance.Return(hpBar);
```

---

## OnionCat 적용 포인트

### 적 타입별 HP바 표시 정책
- **일반 적**: 타격 시에만 HP바 표시, 2초 후 자동 소멸
- **엘리트 적**: 항상 HP바 표시 (중요 타겟임을 어필)
- **보스**: 별도 화면 하단 보스 HP바 (Boss_Health_Bar_UI.md 참조)

### 약점 시스템과 시각적 연계
- 양파(Player 2)의 공격이 효과적일 때: HP바 파란색 테두리 표시
- 고양이(Player 1)의 공격이 효과적일 때: HP바 빨간색 테두리 표시
- 면역(데미지 없음): HP바 회색, "IMMUNE" 텍스트 플래시

```csharp
public void ShowWeaknessIndicator(DamageType type)
{
    outlineImage.color = type == DamageType.Ranged ? Color.blue : Color.red;
    outlineImage.enabled = true;
}
```

### 퍼포먼스 주의사항
- 방당 최대 적 수를 고려해 Canvas 수가 과하지 않도록
- `Camera.main` 캐싱 필수 (Update에서 매번 호출 금지)

```csharp
private Camera mainCam;
void Awake() { mainCam = Camera.main; }
void Update() { transform.rotation = mainCam.transform.rotation; }
```

---

## 참고 링크

- [Unity Docs - Canvas Render Mode: World Space](https://docs.unity3d.com/Manual/UICanvas.html)
- [Unity Tutorial: Health Bars in Unity (Brackeys)](https://www.youtube.com/watch?v=BLfNP4Sc_iA)
- [Enemy HP Bar World Space Tutorial](https://www.youtube.com/watch?v=0tDPxNB4lRs)
- [Unity Image FillAmount 문서](https://docs.unity3d.com/ScriptReference/UI.Image-fillAmount.html)
- [CanvasGroup Alpha 제어](https://docs.unity3d.com/ScriptReference/CanvasGroup-alpha.html)
