# 동적 난이도 조정 시스템 (Dynamic Difficulty Adjustment)

리서치 날짜: 2026-07-17

## 개요

동적 난이도 조정(DDA, Dynamic Difficulty Adjustment)은 플레이어의 실시간 퍼포먼스를 측정해 게임의 난이도를 자동으로 올리거나 낮추는 시스템이다.

OnionCat에서 이 시스템이 필요한 이유:
- 2인 협력 게임 → 두 플레이어의 숙련도 차이가 클 때 한 명이 짐이 되는 문제
- 초보 플레이어(개발자 포함)가 초반 몇 방에서 포기하지 않도록
- 로그라이크 특성상 강한 빌드와 약한 빌드의 격차를 보정

### 대표 사례
- **Resident Evil 4**: 적 체력·공격력·숫자를 사망 횟수에 따라 실시간 조정
- **Left 4 Dead**: AI Director — 좀비 밀도와 물자를 플레이어 스트레스에 따라 조절
- **Super Mario Galaxy**: 사망 5회 이후 스타 큐브(무적 도우미) 제공
- **Celeste**: Assist Mode (속도, 대시 횟수 등 수동 조정)

---

## Unity 구현 방법

### Step 1: 퍼포먼스 지표 수집기

```csharp
[System.Serializable]
public class PerformanceMetrics
{
    public int deathCount;           // 런 내 총 사망 횟수
    public float avgRoomClearTime;   // 방 평균 클리어 시간 (초)
    public float damageTakenRatio;   // 받은 피해 / 최대 체력 비율
    public int missedParryCount;     // 파리 실패 횟수 (Onion)
    public float hitRate;            // Cat 슬래시 히트율
}

public class PerformanceTracker : MonoBehaviour
{
    public static PerformanceTracker Instance { get; private set; }

    public PerformanceMetrics Current { get; private set; } = new();

    private float _roomStartTime;
    private int _roomCount;
    private float _totalClearTime;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    public void OnRoomEnter() => _roomStartTime = Time.time;

    public void OnRoomClear()
    {
        float elapsed = Time.time - _roomStartTime;
        _roomCount++;
        _totalClearTime += elapsed;
        Current.avgRoomClearTime = _totalClearTime / _roomCount;
        EvaluateDifficulty();
    }

    public void OnPlayerDeath() => Current.deathCount++;

    public void OnDamageTaken(int amount, int maxHp)
    {
        // 누적 피해 비율 업데이트
        Current.damageTakenRatio = Mathf.Clamp01(
            Current.damageTakenRatio + (float)amount / maxHp * 0.1f);
    }

    public void OnParryFailed() => Current.missedParryCount++;

    private void EvaluateDifficulty()
    {
        DifficultyController.Instance?.UpdateDifficulty(Current);
    }
}
```

### Step 2: 난이도 파라미터 ScriptableObject

```csharp
[CreateAssetMenu(menuName = "OnionCat/DifficultyPreset")]
public class DifficultyPreset : ScriptableObject
{
    [Header("적 스탯 배율")]
    [Range(0.5f, 2f)] public float enemyHealthMultiplier = 1f;
    [Range(0.5f, 2f)] public float enemySpeedMultiplier = 1f;
    [Range(0.5f, 2f)] public float enemyDamageMultiplier = 1f;
    [Range(0.5f, 1.5f)] public float bulletSpeedMultiplier = 1f;

    [Header("플레이어 보조")]
    public bool enableGhostRevive = false;  // 사망 후 유령 상태로 부활 가능
    [Range(0f, 50f)] public float passiveHpRegen = 0f;  // 방 클리어 시 회복량
    public int bonusUpgradeCardCount = 0;   // 업그레이드 선택지 +N장

    [Header("탄막 조정")]
    [Range(1, 12)] public int maxBulletsPerPattern = 8;
    public float bulletPatternDelay = 0f;   // 탄막 발사 전 추가 딜레이
}
```

### Step 3: 동적 난이도 조정 컨트롤러

```csharp
public class DifficultyController : MonoBehaviour
{
    public static DifficultyController Instance { get; private set; }

    [SerializeField] private DifficultyPreset easyPreset;
    [SerializeField] private DifficultyPreset normalPreset;
    [SerializeField] private DifficultyPreset hardPreset;

    // 현재 적용 중인 배율 (런타임에 부드럽게 변화)
    public float CurrentEnemyHpMult { get; private set; } = 1f;
    public float CurrentEnemySpeedMult { get; private set; } = 1f;
    public float CurrentBulletSpeedMult { get; private set; } = 1f;
    public bool GhostReviveEnabled { get; private set; } = false;

    private float _targetHpMult = 1f;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        ApplyPreset(normalPreset);
    }

    void Update()
    {
        // 목표 배율로 부드럽게 보간 (급격한 변화 방지)
        CurrentEnemyHpMult = Mathf.Lerp(CurrentEnemyHpMult, _targetHpMult,
                                         Time.deltaTime * 0.5f);
    }

    public void UpdateDifficulty(PerformanceMetrics metrics)
    {
        float stress = CalculateStressScore(metrics);

        if (stress > 0.7f)       // 힘들어하는 중
            ApplyPreset(easyPreset);
        else if (stress < 0.3f)  // 너무 쉽게 클리어
            ApplyPreset(hardPreset);
        else
            ApplyPreset(normalPreset);
    }

    // 스트레스 점수 0(쉬움)~1(힘듦) 계산
    private float CalculateStressScore(PerformanceMetrics m)
    {
        float deathScore = Mathf.Clamp01(m.deathCount / 5f);  // 사망 5회 = max
        float timeScore  = m.avgRoomClearTime > 60f ? 1f : m.avgRoomClearTime / 60f;
        float dmgScore   = m.damageTakenRatio;

        // 가중 평균
        return deathScore * 0.5f + dmgScore * 0.3f + timeScore * 0.2f;
    }

    private void ApplyPreset(DifficultyPreset preset)
    {
        _targetHpMult = preset.enemyHealthMultiplier;
        CurrentEnemySpeedMult = preset.enemySpeedMultiplier;
        CurrentBulletSpeedMult = preset.bulletSpeedMultiplier;
        GhostReviveEnabled = preset.enableGhostRevive;
    }
}
```

### Step 4: 적 생성 시 배율 적용

```csharp
public class EnemySpawner : MonoBehaviour
{
    private void ConfigureEnemy(EnemyBase enemy)
    {
        var dc = DifficultyController.Instance;
        if (dc == null) return;

        // 적 스탯에 동적 배율 적용
        enemy.MaxHealth = Mathf.RoundToInt(enemy.MaxHealth * dc.CurrentEnemyHpMult);
        enemy.MoveSpeed *= dc.CurrentEnemySpeedMult;

        // 탄막 패턴에도 적용
        var shooter = enemy.GetComponent<EnemyShooter>();
        if (shooter != null)
            shooter.BulletSpeedMultiplier = dc.CurrentBulletSpeedMult;
    }
}
```

### Step 5: 유령 부활 시스템 (쉬움 모드 보조)

```csharp
// 사망 후 유령 상태 — 파트너가 부활시킬 수 있음
public class GhostReviveSystem : MonoBehaviour
{
    [SerializeField] private float reviveRadius = 2f;
    [SerializeField] private float reviveTime = 3f; // 파트너가 3초 옆에 있으면 부활

    private bool _isDead;
    private float _reviveProgress;
    private Transform _partner;

    public void OnDeath()
    {
        if (!DifficultyController.Instance.GhostReviveEnabled) return;
        _isDead = true;
        // 유령 상태 이펙트 활성화
        GetComponent<SpriteRenderer>().color = new Color(1, 1, 1, 0.4f);
        GetComponent<Collider2D>().enabled = false;
        // 느리게 이동 가능 (유령)
    }

    void Update()
    {
        if (!_isDead || _partner == null) return;

        if (Vector2.Distance(transform.position, _partner.position) < reviveRadius)
        {
            _reviveProgress += Time.deltaTime;
            // UI에 진행도 표시
            if (_reviveProgress >= reviveTime)
                Revive();
        }
        else
        {
            _reviveProgress = Mathf.Max(0, _reviveProgress - Time.deltaTime);
        }
    }

    private void Revive()
    {
        _isDead = false;
        _reviveProgress = 0;
        GetComponent<SpriteRenderer>().color = Color.white;
        GetComponent<Collider2D>().enabled = true;
        // HP 50% 로 부활
        GetComponent<PlayerHealth>().SetHealth(GetComponent<PlayerHealth>().MaxHealth / 2);
    }
}
```

---

## 설계 주의사항

### 투명성 vs 은밀성

| 방식 | 장점 | 단점 | 추천 |
|------|------|------|------|
| 숨겨진 DDA | 플레이어가 "내 실력" 착각 못 함 | 발각 시 불쾌감 | 적 스탯 조정에 적합 |
| 명시적 어시스트 | 자존심 보호 가능, 선택권 부여 | 사용 꺼려할 수 있음 | 부활/보조 기능에 적합 |

**OnionCat 권장**: 적 스탯 조정은 숨기고, 부활/보조 기능은 명시적 옵션으로 제공

### 조정 빈도 제한
- 방 클리어마다 평가하되, 실제 배율 변경은 **다음 방 시작 시**에만
- 방 중간에 배율 바뀌면 혼란스러움
- 스트레스 점수가 임계치 초과 → 즉시 변경 X, 2회 연속 초과 시 변경

### 2인 협력 특수 처리

```csharp
// 2인 게임에서 스트레스 점수 계산
private float CalculateCombinedStress(PerformanceMetrics p1, PerformanceMetrics p2)
{
    float p1Stress = CalculateStressScore(p1);
    float p2Stress = CalculateStressScore(p2);
    // 더 힘든 플레이어 기준으로 조정 (약한 플레이어 보호)
    return Mathf.Max(p1Stress, p2Stress) * 0.7f + Mathf.Min(p1Stress, p2Stress) * 0.3f;
}
```

---

## OnionCat 적용 포인트

### A. 레이어드 DDA 설계
1. **Layer 0 (항상 활성)**: 적 체력 ±20% 조정 — 플레이어 모름
2. **Layer 1 (사망 3회)**: 방 클리어 시 HP 5 회복 추가
3. **Layer 2 (사망 5회)**: 유령 부활 시스템 활성화
4. **Layer 3 (사망 7회)**: "어시스트 모드" 팝업 제안 → 플레이어 선택

### B. Onion 파리 실패율 활용
- 파리 실패 3회 이상 → 방패 판정 범위 미세 확대 (모름)
- 파리 성공 → 게임 리듬 빠르게 → 탄막 패턴 심화

### C. Cat 슬래시 히트율 활용
- 히트율 40% 미만 → 근접 전용 적 비율 감소, 원거리 적 증가
- 히트율 80% 이상 → 근접 전용 적 증가, 이동 패턴 복잡해짐

### D. 완전 실패 방지 안전망
- HP 1이 되면 10초간 무적 포함 쿨다운 필드 (Resident Evil 4 레드 화면)
- 두 플레이어 모두 동시 사망 시에만 게임 오버 (한 명 유령 상태)

---

## 구현 순서 (초보 개발자용)

1. `PerformanceTracker` 싱글톤 작성, 사망/방클리어 이벤트 연결
2. `DifficultyPreset` ScriptableObject 3개 생성 (Easy/Normal/Hard)
3. `DifficultyController` 작성, `UpdateDifficulty()` 테스트
4. `EnemySpawner`에서 배율 적용 연결
5. 유령 부활은 기본 시스템 완성 후 추가 기능으로 붙이기

---

## 참고 링크

- GDC: Left 4 Dead AI Director 강연: https://www.gdcvault.com/play/1211/The-AI-Systems-of
- 동적 난이도 연구 논문: https://game.stanford.edu/publications/dynamic-difficulty-adjustment
- Resident Evil 4 DDA 분석: https://www.gamedeveloper.com/design/re4-difficulty
- Unity ScriptableObject 공식 문서: https://docs.unity3d.com/Manual/class-ScriptableObject.html
