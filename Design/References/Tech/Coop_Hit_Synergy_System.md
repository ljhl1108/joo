# Coop Hit Synergy System (협동 타격 시너지)

리서치 날짜: 2026-10-04

## 개요

두 플레이어(Cat + Onion)가 **거의 동시에** 같은 적에게 피해를 가할 때 시너지 보너스를 발동하는 시스템.
OnionCat의 핵심 협동 필러인 "혼자보다 함께가 강하다"를 게임플레이에서 즉각 피드백으로 구현한다.

### 왜 필요한가
- 두 플레이어가 각자 플레이하는 것보다 **함께 공격할 동기**를 제공
- Split Fiction의 "COMBINE!" 시스템, 많은 협동 게임의 콤보 트리거와 동일한 철학
- OnionCat의 `TakeDamage(attacker: Attacker.Cat/Onion)` 구조가 이 시스템을 자연스럽게 지원

---

## Unity 구현 방법

### 핵심 아이디어
`EnemyBase`에서 마지막 피격자(Cat/Onion)와 피격 시각을 기록.
다음 피격 시 "반대 플레이어"가 공격했고 시간 차가 임계값 이내이면 시너지 발동.

### Step 1: EnemyBase에 시너지 추적 필드 추가

```csharp
// EnemyBase.cs (기존 TakeDamage 메서드 수정)
public class EnemyBase : MonoBehaviour
{
    // 시너지 추적
    private Attacker _lastAttacker = Attacker.None;
    private float _lastHitTime = -999f;
    private const float SynergyWindow = 0.25f; // 0.25초 이내 교차 공격 = 시너지

    public void TakeDamage(float damage, Attacker attacker)
    {
        bool synergy = false;

        if (attacker != Attacker.None && attacker != _lastAttacker
            && _lastAttacker != Attacker.None
            && Time.time - _lastHitTime <= SynergyWindow)
        {
            synergy = true;
        }

        _lastAttacker = attacker;
        _lastHitTime = Time.time;

        float finalDamage = synergy
            ? damage * SynergySettings.Instance.DamageMultiplier
            : damage;

        ApplyDamage(finalDamage);

        if (synergy)
            TriggerSynergyEffect();
    }

    private void TriggerSynergyEffect()
    {
        // 이펙트, 사운드, UI 피드백
        SynergyFeedback.Instance.Play(transform.position);
        Sfx.Play(SfxId.SynergyHit);
        // 게이지 충전 (RunData 연동)
        GameManager.Instance.Run.AddSynergyCharge(SynergySettings.Instance.GaugePerSynergy);
    }
}
```

### Step 2: Attacker 열거형 확인

```csharp
// 이미 프로젝트에 존재 (CLAUDE.md 규칙)
public enum Attacker { None, Cat, Onion }
```

### Step 3: SynergySettings ScriptableObject

```csharp
[CreateAssetMenu(menuName = "OnionCat/SynergySettings")]
public class SynergySettings : ScriptableObject
{
    public static SynergySettings Instance; // Resources.Load로 로드 후 캐싱

    [SerializeField] private float _damageMultiplier = 1.5f;
    [SerializeField] private float _synergyWindow = 0.25f;
    [SerializeField] private float _gaugePerSynergy = 10f;

    public float DamageMultiplier => _damageMultiplier;
    public float SynergyWindow => _synergyWindow;
    public float GaugePerSynergy => _gaugePerSynergy;
}
```
→ `Assets/Resources/SynergySettings.asset`에 저장, `Awake`에서 `Resources.Load<SynergySettings>("SynergySettings")`

### Step 4: SynergyFeedback — 이펙트 재생

```csharp
public class SynergyFeedback : MonoBehaviour
{
    public static SynergyFeedback Instance { get; private set; }

    [SerializeField] private ParticleSystem _synergyParticle;
    [SerializeField] private SpriteRenderer _flashLabel; // "COOPERATION!" 텍스트 이미지

    private void Awake() => Instance = this;

    public void Play(Vector3 worldPos)
    {
        _synergyParticle.transform.position = worldPos;
        _synergyParticle.Play();
        StartCoroutine(ShowLabel(worldPos));
    }

    private IEnumerator ShowLabel(Vector3 pos)
    {
        _flashLabel.transform.position = pos + Vector3.up * 0.5f;
        _flashLabel.enabled = true;
        yield return new WaitForSeconds(0.6f);
        _flashLabel.enabled = false;
    }
}
```

### Step 5: 게이지 연동 (RunData)

```csharp
// RunData.cs에 추가
public float SynergyGauge { get; private set; }
private const float MaxGauge = 100f;

public void AddSynergyCharge(float amount)
{
    SynergyGauge = Mathf.Min(SynergyGauge + amount, MaxGauge);
    if (SynergyGauge >= MaxGauge)
        TriggerJointUltimate();
}

private void TriggerJointUltimate()
{
    SynergyGauge = 0f;
    GameManager.Instance.ChangeState(GameState.JointUltimate); // 합동기 발동
}
```

---

## 시너지 윈도우 튜닝 가이드

| SynergyWindow | 느낌 | 권장 상황 |
|---|---|---|
| 0.1초 | 거의 동시. 숙련자 전용 | 고난이도 모드 |
| 0.25초 | 표준. 의식하면 발동 | **기본값 권장** |
| 0.5초 | 순서만 맞으면 OK | 튜토리얼/첫 런 |

→ 런 시작 시 난이도에 따라 `SynergySettings` 변형 에셋을 적용하는 방식도 가능.

---

## OnionCat 적용 포인트

### 핵심 흐름
```
고양이 할퀴기 → (0.25초 이내) → 양파 투사체 타격
→ TakeDamage 에서 시너지 감지
→ 데미지 1.5배 + 파티클 + 사운드 + 게이지 +10
```

### 합동기(Joint Ultimate)와 연결
시너지 게이지가 100 차면 합동기 발동 (이미 설계된 `GameState.JointUltimate`에 연결).
→ 협동을 많이 할수록 합동기 쿨다운이 짧아지는 자연스러운 보상 루프 형성.

### 패시브 시너지 강화
세트 보너스로 "시너지 윈도우 +0.1초", "시너지 데미지 배수 +0.2" 등 추가 가능.
→ `PassiveHost.Recalculate()` 후 `SynergySettings`의 런타임 값을 업데이트.

### 적 디자인과 연계
특정 보스의 경우 시너지 타격만이 방어막을 깰 수 있도록 설계:
```csharp
// BossShield.cs
public override void TakeDamage(float dmg, Attacker attacker)
{
    if (!_requiresSynergy) { base.TakeDamage(dmg, attacker); return; }
    // 시너지 없이는 방어막이 안 깎임 → 협동 강제
}
```

### 디버그 확인
플레이 테스트 메뉴 `OnionCat > Debug`에 "시너지 윈도우 표시" 옵션 추가 권장.
적 주변에 SynergyWindow 시간 동안 하이라이트 표시 → 튜닝에 도움.

---

## 참고 링크

- Unity Coroutine 타이밍: https://docs.unity3d.com/Manual/Coroutines.html
- Split Fiction 협동 설계 인터뷰: https://www.gamesradar.com/games/adventure/split-fiction-interview/
- It Takes Two GDC 강연 (Hazelight 협동 철학): https://www.youtube.com/watch?v=B0u1yDucrPc
- "Co-op Game Design Patterns" (GDC 2022): https://gdcvault.com/play/1028553/
