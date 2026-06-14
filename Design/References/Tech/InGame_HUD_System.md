# 인게임 HUD 시스템 (In-Game HUD)

리서치 날짜: 2026-06-14

## 개요

HUD(Heads-Up Display)는 플레이어가 게임 중 항상 보는 정보 레이어다. 체력, 골드, 스킬 쿨다운, 현재 업그레이드 등을 실시간으로 표시한다. 초보 개발자가 가장 늦게 붙이는 기능이지만, 없으면 테스트 자체가 불편해지기 때문에 **게임 루프가 완성되는 시점에 바로 만들어야** 한다. OnionCat은 2인 공유 캐릭터이므로 고양이(Player1)와 작물(Player2)의 정보를 **하나의 HUD에 함께 표시**해야 한다.

---

## Unity 구현 방법

### 1. Canvas 설정

```
Canvas (Screen Space - Overlay)
├── PlayerPanel (좌하단)
│   ├── HealthBar (Slider)
│   ├── GoldText (TMP_Text)
│   └── RoomCountText
├── CatSkillPanel (좌측)
│   ├── DashCooldown (Image - fillAmount)
│   └── SlashIcon
├── CropSkillPanel (우측)
│   ├── ShieldCooldown (Image - fillAmount)
│   └── ProjectileAmmo (TMP_Text)
├── UpgradeSlots (상단 중앙)
│   ├── Slot1 (Image)
│   ├── Slot2 (Image)
│   └── Slot3 (Image)
└── BossHPBar (상단, 평소 비활성)
```

**Canvas Scaler 설정**:
- UI Scale Mode: Scale With Screen Size
- Reference Resolution: 1920 × 1080
- Match: 0.5 (Width/Height 중간)

### 2. HUD Manager

```csharp
public class HUDManager : MonoBehaviour
{
    public static HUDManager Instance { get; private set; }

    [SerializeField] private Slider healthBar;
    [SerializeField] private TMP_Text goldText;
    [SerializeField] private TMP_Text roomCountText;
    [SerializeField] private Image dashCooldownFill;  // fillAmount 방식
    [SerializeField] private Image shieldCooldownFill;
    [SerializeField] private TMP_Text projectileAmmoText;
    [SerializeField] private Image[] upgradeSlotIcons; // 3개 슬롯

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    // 체력 업데이트
    public void UpdateHealth(float current, float max)
    {
        healthBar.value = current / max;
    }

    // 골드 업데이트
    public void UpdateGold(int amount)
    {
        goldText.text = $"G {amount}";
    }

    // 쿨다운 업데이트 (0~1, 0이면 준비됨)
    public void UpdateDashCooldown(float ratio)
    {
        dashCooldownFill.fillAmount = ratio;
        dashCooldownFill.color = ratio > 0 ? Color.gray : Color.white;
    }

    public void UpdateShieldCooldown(float ratio)
    {
        shieldCooldownFill.fillAmount = ratio;
        shieldCooldownFill.color = ratio > 0 ? Color.gray : Color.white;
    }

    // 투사체 탄약 표시
    public void UpdateAmmo(int current, int max)
    {
        projectileAmmoText.text = $"{current}/{max}";
    }

    // 업그레이드 슬롯 아이콘 설정
    public void SetUpgradeSlot(int index, Sprite icon)
    {
        if (index >= upgradeSlotIcons.Length) return;
        upgradeSlotIcons[index].sprite = icon;
        upgradeSlotIcons[index].color = icon != null ? Color.white : new Color(1,1,1,0.2f);
    }

    // 방 카운터
    public void UpdateRoomCount(int current, int total)
    {
        roomCountText.text = $"Room {current}/{total}";
    }
}
```

### 3. 쿨다운 표시 (Image fillAmount 방식)

```csharp
// 스킬 컴포넌트에서 매 프레임 HUD 업데이트
public class CatDashSkill : MonoBehaviour
{
    [SerializeField] private float cooldown = 2f;
    private float remainingCooldown = 0f;

    void Update()
    {
        if (remainingCooldown > 0)
        {
            remainingCooldown -= Time.deltaTime;
            HUDManager.Instance?.UpdateDashCooldown(remainingCooldown / cooldown);
        }
        else
        {
            HUDManager.Instance?.UpdateDashCooldown(0f);
        }
    }

    public void UseDash()
    {
        if (remainingCooldown > 0) return;
        remainingCooldown = cooldown;
        // 대시 로직
    }
}
```

### 4. 피격 시 체력바 애니메이션 (흰 잔상 효과)

```csharp
// 체력바에 흰 슬라이더를 겹쳐서 잠깐 지연 후 줄어들게
public class AnimatedHealthBar : MonoBehaviour
{
    [SerializeField] private Slider mainBar;      // 빨간 (즉시 감소)
    [SerializeField] private Slider ghostBar;     // 흰색 (지연 감소)
    [SerializeField] private float ghostDecayDelay = 0.5f;
    [SerializeField] private float ghostDecaySpeed = 0.5f;

    private float ghostTarget;
    private Coroutine decayRoutine;

    public void SetHealth(float ratio)
    {
        mainBar.value = ratio;
        if (ratio < ghostBar.value)
        {
            ghostTarget = ratio;
            if (decayRoutine != null) StopCoroutine(decayRoutine);
            decayRoutine = StartCoroutine(DelayedGhostDecay());
        }
        else
        {
            ghostBar.value = ratio; // 회복 시 즉시
        }
    }

    IEnumerator DelayedGhostDecay()
    {
        yield return new WaitForSeconds(ghostDecayDelay);
        while (ghostBar.value > ghostTarget)
        {
            ghostBar.value = Mathf.MoveTowards(ghostBar.value, ghostTarget, ghostDecaySpeed * Time.deltaTime);
            yield return null;
        }
    }
}
```

### 5. 업그레이드 획득 연출

```csharp
public class UpgradeSlotUI : MonoBehaviour
{
    [SerializeField] private Image icon;
    [SerializeField] private CanvasGroup canvasGroup;

    public void ShowUpgrade(Sprite upgradeIcon)
    {
        icon.sprite = upgradeIcon;
        StartCoroutine(PopIn());
    }

    IEnumerator PopIn()
    {
        transform.localScale = Vector3.zero;
        canvasGroup.alpha = 0;
        float t = 0;
        while (t < 0.3f)
        {
            float progress = t / 0.3f;
            transform.localScale = Vector3.Lerp(Vector3.zero, Vector3.one * 1.2f, progress);
            canvasGroup.alpha = progress;
            t += Time.deltaTime;
            yield return null;
        }
        // 오버슈트 후 정착
        t = 0;
        while (t < 0.1f)
        {
            transform.localScale = Vector3.Lerp(Vector3.one * 1.2f, Vector3.one, t / 0.1f);
            t += Time.deltaTime;
            yield return null;
        }
        transform.localScale = Vector3.one;
        canvasGroup.alpha = 1f;
    }
}
```

---

## OnionCat 적용 포인트

### 2인 공유 캐릭터 HUD 레이아웃

OnionCat은 한 몸(고양이 + 작물)이므로 체력은 **공유 체력 하나**다. 단, 조작이 다른 두 플레이어의 스킬을 분리해서 보여줘야 한다:

```
[화면 좌하단]
  ❤️❤️❤️ (공유 HP)  Gold: 120  Room: 3/7

[화면 좌측 세로]
  🐱 대시 쿨다운 (원형 fill)
  🐱 슬래시 범위 표시

[화면 우측 세로]
  🌱 방패 쿨다운 (원형 fill)
  🌱 투사체 잔탄: 5/8

[화면 상단 중앙]
  [업그레이드 슬롯1] [슬롯2] [슬롯3]
```

### 개발 우선순위
1. **먼저 만들 것**: 체력바 + 방 카운터 — 없으면 테스트 불가
2. **그 다음**: 쿨다운 표시 — 스킬 추가 시 바로 붙이기
3. **나중에**: 업그레이드 슬롯 아이콘 + 획득 연출

### 픽셀아트 HUD 스타일 팁
- Canvas Scaler를 **정수 배수**로 설정 (e.g. 320×180 → 6배 → 1920×1080)
- UI 이미지는 Sprite Mode = Multiple, Filter Mode = Point (no filter), Compression = None
- 픽셀 퍼펙트 Canvas 컴포넌트 추가 시 HUD가 흐릿해지는 문제 방지

### 이벤트 기반 업데이트 (성능)
매 Update()에서 HUD를 갱신하면 성능 낭비. 체력/골드 변경 시 이벤트로만 업데이트:
```csharp
// PlayerStats에서
public event Action<float, float> OnHealthChanged; // current, max
public event Action<int> OnGoldChanged;

// HUDManager에서 구독
playerStats.OnHealthChanged += HUDManager.Instance.UpdateHealth;
playerStats.OnGoldChanged += HUDManager.Instance.UpdateGold;
```

---

## 참고 링크

- Unity UI Toolkit vs UGUI 비교: https://docs.unity3d.com/Manual/UIE-vs-UGUI-feature-list.html
- Image fillAmount 쿨다운: https://docs.unity3d.com/ScriptReference/UI.Image-fillAmount.html
- Canvas Scaler 설정 가이드: https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-CanvasScaler.html
- Pixel Perfect Camera (Unity 2D): https://docs.unity3d.com/Packages/com.unity.2d.pixel-perfect@5.0/manual/index.html
- 체력바 애니메이션 튜토리얼: https://www.youtube.com/watch?v=BLfNP4Sc_iA
