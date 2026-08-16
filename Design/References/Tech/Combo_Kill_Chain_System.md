# Combo Kill Chain System (콤보 킬 체인 시스템)

리서치 날짜: 2026-08-16

## 개요

콤보 킬 체인 시스템은 **일정 시간 내에 연속으로 적을 처치할 때 콤보 카운트를 누적하고, 높은 콤보에 따라 보상(골드 배율, 스코어, 특수 이펙트)을 제공**하는 시스템이다.

로그라이크에서 콤보 시스템의 가치:
- 전투 리듬감과 박진감 향상
- "효율적인 플레이"에 대한 즉각적인 피드백
- 협동 게임에서 **두 플레이어가 함께 처치에 기여할 때 보너스**를 주면 협동을 보상으로 유도

OnionCat에서는 **P1 근접 + P2 원거리가 함께 적을 처치하면 "협동 콤보"로 더 높은 카운트**를 주는 형태로 응용 가능.

---

## Unity 구현 방법

### 핵심 데이터 구조

```csharp
using UnityEngine;

[CreateAssetMenu(menuName = "OnionCat/ComboConfig")]
public class ComboConfig : ScriptableObject
{
    [Tooltip("콤보 유지 시간 (초)")]
    public float comboWindow = 2.5f;

    [Tooltip("콤보 단계별 골드 배율")]
    public float[] goldMultipliers = { 1f, 1.2f, 1.5f, 2f, 3f };

    [Tooltip("콤보 단계 임계값 (처치 수)")]
    public int[] comboThresholds = { 0, 3, 6, 10, 15 };

    [Tooltip("협동 처치 시 콤보 가산량")]
    public int coopKillBonus = 2;
}
```

---

### 콤보 매니저

```csharp
using UnityEngine;
using System;

public class ComboKillChainManager : MonoBehaviour
{
    public static ComboKillChainManager Instance { get; private set; }

    [SerializeField] private ComboConfig config;

    private int currentCombo = 0;
    private float comboTimer = 0f;
    private bool comboActive = false;

    public event Action<int> OnComboUpdated;   // 콤보 숫자 변경 시
    public event Action OnComboReset;           // 콤보 초기화 시
    public event Action<int> OnComboTierReached; // 특정 단계 돌파 시

    void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
    }

    void Update()
    {
        if (!comboActive) return;
        comboTimer -= Time.deltaTime;
        if (comboTimer <= 0f) ResetCombo();
    }

    // 일반 처치 (P1 단독 or P2 단독)
    public void RegisterKill()
    {
        AddToCombo(1);
    }

    // 협동 처치 (P1 + P2 공동 기여)
    public void RegisterCoopKill()
    {
        AddToCombo(config.coopKillBonus);
    }

    private void AddToCombo(int amount)
    {
        int previousTier = GetCurrentTier();

        currentCombo += amount;
        comboTimer = config.comboWindow;
        comboActive = true;

        OnComboUpdated?.Invoke(currentCombo);

        int newTier = GetCurrentTier();
        if (newTier > previousTier)
            OnComboTierReached?.Invoke(newTier);
    }

    public void ResetCombo()
    {
        currentCombo = 0;
        comboActive = false;
        OnComboReset?.Invoke();
    }

    public int GetCurrentTier()
    {
        for (int i = config.comboThresholds.Length - 1; i >= 0; i--)
        {
            if (currentCombo >= config.comboThresholds[i])
                return i;
        }
        return 0;
    }

    public float GetCurrentGoldMultiplier()
    {
        int tier = GetCurrentTier();
        return config.goldMultipliers[tier];
    }

    public int GetCurrentCombo() => currentCombo;
    public float GetTimerRatio() => comboActive ? comboTimer / config.comboWindow : 0f;
}
```

---

### 협동 처치 감지 (EnemyHealth 연동)

```csharp
// EnemyHealth.cs에 추가할 처치 기여 추적 로직
public class EnemyHealth : MonoBehaviour
{
    private bool wasHitByP1 = false;
    private bool wasHitByP2 = false;
    private float coopWindowTimer = 0f;
    private const float COOP_WINDOW = 1.5f; // 협동 판정 시간 창

    public void TakeDamage(int damage, PlayerRole attacker)
    {
        // 공격자 기록
        if (attacker == PlayerRole.P1) wasHitByP1 = true;
        if (attacker == PlayerRole.P2) wasHitByP2 = true;
        coopWindowTimer = COOP_WINDOW;

        currentHP -= damage;
        if (currentHP <= 0) OnDeath();
    }

    void Update()
    {
        if (coopWindowTimer > 0)
        {
            coopWindowTimer -= Time.deltaTime;
            if (coopWindowTimer <= 0)
            {
                // 창 만료 시 초기화
                wasHitByP1 = false;
                wasHitByP2 = false;
            }
        }
    }

    private void OnDeath()
    {
        bool isCoopKill = wasHitByP1 && wasHitByP2;

        if (isCoopKill)
            ComboKillChainManager.Instance.RegisterCoopKill();
        else
            ComboKillChainManager.Instance.RegisterKill();

        // 골드 드롭 시 배율 적용
        float multiplier = ComboKillChainManager.Instance.GetCurrentGoldMultiplier();
        DropGold(Mathf.RoundToInt(baseGoldDrop * multiplier));

        Destroy(gameObject);
    }
}
```

---

### 콤보 UI

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using DG.Tweening;

public class ComboUI : MonoBehaviour
{
    [SerializeField] private GameObject comboPanel;
    [SerializeField] private TextMeshProUGUI comboText;
    [SerializeField] private Image timerBar;          // 콤보 유지 타이머 바
    [SerializeField] private TextMeshProUGUI tierLabel;

    private readonly string[] tierNames = { "", "GOOD!", "GREAT!", "AMAZING!", "LEGENDARY!" };

    void OnEnable()
    {
        ComboKillChainManager.Instance.OnComboUpdated += UpdateComboDisplay;
        ComboKillChainManager.Instance.OnComboReset += HideComboPanel;
        ComboKillChainManager.Instance.OnComboTierReached += ShowTierEffect;
    }

    void OnDisable()
    {
        if (ComboKillChainManager.Instance == null) return;
        ComboKillChainManager.Instance.OnComboUpdated -= UpdateComboDisplay;
        ComboKillChainManager.Instance.OnComboReset -= HideComboPanel;
        ComboKillChainManager.Instance.OnComboTierReached -= ShowTierEffect;
    }

    void Update()
    {
        // 타이머 바 실시간 갱신
        if (comboPanel.activeSelf)
            timerBar.fillAmount = ComboKillChainManager.Instance.GetTimerRatio();
    }

    private void UpdateComboDisplay(int combo)
    {
        comboPanel.SetActive(true);
        comboText.text = $"×{combo}";
        comboText.transform.DOKill();
        comboText.transform.localScale = Vector3.one;
        comboText.transform.DOPunchScale(Vector3.one * 0.3f, 0.2f, 5, 0.5f);
    }

    private void HideComboPanel()
    {
        comboPanel.SetActive(false);
    }

    private void ShowTierEffect(int tier)
    {
        if (tier <= 0 || tier >= tierNames.Length) return;
        tierLabel.text = tierNames[tier];
        tierLabel.transform.DOKill();
        tierLabel.color = new Color(1, 1, 0, 1);
        tierLabel.transform.DOScale(1.5f, 0.1f).SetLoops(2, LoopType.Yoyo);
        tierLabel.DOFade(0, 0.8f).SetDelay(0.5f);
    }
}
```

---

### 드롭 아이템에 배율 적용

```csharp
public class GoldDrop : MonoBehaviour
{
    [SerializeField] private int baseAmount = 10;

    public void Initialize(float multiplier)
    {
        int finalAmount = Mathf.RoundToInt(baseAmount * multiplier);
        // 금화 표시 및 실제 지급
        GetComponent<TextMeshPro>().text = $"+{finalAmount}G";
        // PlayerStats.Instance.AddGold(finalAmount);
    }
}
```

---

## OnionCat 적용 포인트

### 1. 협동 콤보가 핵심 보상 루프
- P1 단독 처치 → 콤보 +1
- P2 단독 처치 → 콤보 +1
- **P1 + P2 공동 처치 (1.5초 내 둘 다 피격) → 콤보 +2** (협동 콤보)
- 협동 콤보는 골드 배율뿐 아니라 특수 이펙트(빛 폭발 + 사운드)로 강조 → "잘 협동했다!" 즉각 피드백

### 2. 구현 순서 (초보자용)
1. `ComboConfig` ScriptableObject 생성 (값 조정 편하게)
2. `ComboKillChainManager` 싱글턴 배치 (씬에 빈 오브젝트)
3. `EnemyHealth.OnDeath()` 내에 `RegisterKill()` / `RegisterCoopKill()` 호출 추가
4. `ComboUI` 프리팹 만들어 HUD 씬에 배치
5. DOTween 없이 먼저 숫자만 표시하고 나중에 애니메이션 추가

### 3. 콤보 배율 초기 밸런스
| 콤보 단계 | 처치 수 | 골드 배율 |
|---------|--------|---------|
| 0 (없음) | 0 | ×1.0 |
| 1 (GOOD) | 3 | ×1.2 |
| 2 (GREAT) | 6 | ×1.5 |
| 3 (AMAZING) | 10 | ×2.0 |
| 4 (LEGENDARY) | 15 | ×3.0 |

### 4. 콤보 유지 시간 조정
- 적이 많고 빠른 방: 2초도 충분
- 적이 적고 방어적인 방: 3~4초로 늘려야 자연스러운 콤보 형성
- 방 타입별 `ComboConfig` 다르게 적용 가능 (ScriptableObject 교체)

---

## 참고 링크

- Unity DOTween 공식: http://dotween.demigiant.com/
- 콤보 시스템 디자인 패턴: https://www.gamedeveloper.com/design/the-combo-system-an-underused-but-valuable-mechanic
- ScriptableObject 활용: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unity Event 시스템 패턴: https://docs.unity3d.com/ScriptReference/Events.UnityEvent.html
