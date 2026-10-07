# 보스 다단계 페이즈 전환 구현 (Boss Multi-Phase Transition)

리서치 날짜: 2026-10-07

## 개요

로그라이크 보스 전투의 핵심은 **단계(페이즈) 전환**이다. HP 임계값에 따라 보스의 공격 패턴·면역·외형이 바뀌며, 플레이어에게 "다른 도전"을 제시한다. OnionCat에서는 Cat(근접)과 Onion(원거리)의 강제 협력을 유도하는 핵심 도구가 된다.

---

## Unity 구현 방법

### 1. 데이터 구조 (ScriptableObject)

```csharp
// BossPhaseData.cs
[CreateAssetMenu(fileName = "BossPhaseData", menuName = "OnionCat/Boss/Phase")]
public class BossPhaseData : ScriptableObject
{
    [Range(0f, 1f)] public float healthThreshold; // 페이즈 전환 HP 비율 (예: 0.5 = 50%)
    public float transitionDuration = 2f;          // 전환 연출 시간
    public GameObject phaseVFX;                    // 전환 이펙트 프리팹
    public AttackPatternBase[] attackPatterns;     // 이 페이즈에 활성화할 패턴 목록
    public bool immuneToMelee;                     // Cat 공격 무효 여부
    public bool immuneToRanged;                    // Onion 공격 무효 여부
    public Color spriteColorTint;                  // 외형 색상 (시각적 피드백)
}
```

### 2. 보스 페이즈 컨트롤러

```csharp
// BossPhaseController.cs
public class BossPhaseController : MonoBehaviour
{
    [SerializeField] private BossPhaseData[] phases; // Inspector에서 순서대로 등록
    
    private int currentPhaseIndex = -1;
    private EnemyBase enemyBase;
    private SpriteRenderer sr;
    private bool isTransitioning;

    void Awake()
    {
        enemyBase = GetComponent<EnemyBase>();
        sr = GetComponent<SpriteRenderer>();
    }

    void Start()
    {
        enemyBase.OnHealthChanged += OnHealthChanged;
        // 첫 페이즈 초기화 (threshold = 1.0f인 것)
        ActivatePhase(0, instant: true);
    }

    void OnHealthChanged(float currentHp, float maxHp)
    {
        if (isTransitioning) return;

        float ratio = currentHp / maxHp;
        int nextPhase = currentPhaseIndex + 1;

        if (nextPhase < phases.Length && ratio <= phases[nextPhase].healthThreshold)
            StartCoroutine(TransitionToPhase(nextPhase));
    }

    IEnumerator TransitionToPhase(int phaseIndex)
    {
        isTransitioning = true;
        var phase = phases[phaseIndex];

        // 1) 무적 + 이동 정지
        enemyBase.SetInvincible(true);
        enemyBase.SetMovementEnabled(false);

        // 2) 전환 VFX 재생
        if (phase.phaseVFX != null)
            PoolManager.Spawn(phase.phaseVFX, transform.position, Quaternion.identity);

        // 3) 색상 변화 (트위닝)
        float t = 0f;
        Color startColor = sr.color;
        while (t < phase.transitionDuration)
        {
            t += Time.deltaTime;
            sr.color = Color.Lerp(startColor, phase.spriteColorTint, t / phase.transitionDuration);
            yield return null;
        }

        // 4) 실제 페이즈 활성화
        ActivatePhase(phaseIndex, instant: false);

        // 5) 무적 해제
        enemyBase.SetMovementEnabled(true);
        enemyBase.SetInvincible(false);
        isTransitioning = false;
    }

    void ActivatePhase(int phaseIndex, bool instant)
    {
        currentPhaseIndex = phaseIndex;
        var phase = phases[phaseIndex];

        // 이전 패턴 비활성화
        if (!instant && phaseIndex > 0)
            foreach (var p in phases[phaseIndex - 1].attackPatterns)
                p.Deactivate();

        // 새 패턴 활성화
        foreach (var p in phase.attackPatterns)
            p.Activate();

        // 면역 설정 (DamageSystem과 연동)
        enemyBase.SetImmunity(melee: phase.immuneToMelee, ranged: phase.immuneToRanged);
    }

    void OnDestroy()
    {
        if (enemyBase != null)
            enemyBase.OnHealthChanged -= OnHealthChanged;
    }
}
```

### 3. EnemyBase 확장 — 면역 처리

```csharp
// EnemyBase.cs에 추가
private bool immuneToMelee;
private bool immuneToRanged;

public void SetImmunity(bool melee, bool ranged)
{
    immuneToMelee = melee;
    immuneToRanged = ranged;
}

public override void TakeDamage(float damage, Attacker attacker)
{
    if (attacker == Attacker.Cat && immuneToMelee) 
    {
        ShowImmuneVFX(); // "막혔다" 연출
        return;
    }
    if (attacker == Attacker.Onion && immuneToRanged)
    {
        ShowImmuneVFX();
        return;
    }
    base.TakeDamage(damage, attacker);
}
```

### 4. 보스 HP 바 페이즈 마커 (UI 연동)

```csharp
// BossHealthBarUI.cs에 추가
void DrawPhaseMarkers(BossPhaseData[] phases, float barWidth)
{
    foreach (var phase in phases)
    {
        float xPos = barWidth * phase.healthThreshold;
        // HP 바 위에 세로선 마커 표시
        DrawVerticalMarker(xPos);
    }
}
```

---

## OnionCat 적용 포인트

### 보스 페이즈 = 협력 강요 장치

OnionCat 보스를 3페이즈로 설계하면:

| 페이즈 | HP 구간 | 면역 | 필요 역할 |
|--------|---------|------|----------|
| 1페이즈 | 100~66% | 없음 | Cat + Onion 모두 유효 |
| 2페이즈 | 65~33% | 근접 면역 | **Onion 필수** (원거리만 통함) |
| 3페이즈 | 32~0% | 원거리 면역 | **Cat 필수** (근접만 통함) |

2페이즈에서 Onion이 딜을 담당하는 동안 Cat은 적 제거/방어에 집중. 3페이즈에서 역할 역전. 두 플레이어 모두 **"내가 필요한 순간"**을 반드시 경험한다.

### 구현 순서 (OnionCat 기준)

1. `BossPhaseData` ScriptableObject 생성 → `Assets/Data/Boss/` 저장
2. 기존 보스 프리팹에 `BossPhaseController` 컴포넌트 추가
3. `EnemyBase.TakeDamage`에 `immuneToMelee/Ranged` 분기 추가
4. `Boss_Health_Bar_UI`에 페이즈 마커 연동
5. 전환 VFX는 기존 파티클 재활용 (새 제작 불필요)

### 주의사항

- **면역 시각 피드백 필수**: 막혔을 때 플레이어가 "왜 안 들어가지?"를 알아야 함 → 피격 이펙트 색상 변경 (빨강 → 회색)
- **전환 시 무적은 짧게**: 너무 길면 전투 흐름이 끊김. 1~2초가 적절
- **HP 바에 페이즈 구분선 표시**: 플레이어가 임계값을 예측할 수 있어야 함
- **보스 `kickInterruptsTelegraph = false`** 확인: 페이즈 전환 연출 중 kick으로 끊기면 안 됨

---

## 참고 링크

- Unity 공식 — Coroutines: https://docs.unity3d.com/Manual/Coroutines.html
- YouTube: "Unity Boss Battle Multi Phase Tutorial" — various
- 실제 구현 참고 게임: Hades(보스 페이즈 + 대사), Dead Cells(면역 시각화), Enter the Gungeon(색상 변화)
