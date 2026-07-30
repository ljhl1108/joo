# 협동 부활/임계 상태 시스템 (Co-op Revival & Critical State System)

리서치 날짜: 2026-07-30

## 개요
2인 협동 게임에서 한 플레이어가 쓰러졌을 때 다른 플레이어가 살려내는 메카닉. 일반 co-op에서는 "쓰러짐 → 파트너 터치 → 부활" 구조를 사용하지만, OnionCat은 공유 몸체/공유 HP이므로 **임계 상태(Critical State)** 설계로 변형 적용.

참고 사례: Guacamelee! (소울 부활), Hades (Death Defiance 토큰), Darkest Dungeon (데스 도어), Enter the Gungeon (블랭크/체력 아이템).

## Unity 구현 방법

### 일반 Co-op 부활 시스템 (독립 HP 구조)
```csharp
public enum PlayerState { Alive, Downed, Dead }

public class CoopRevivalSystem : MonoBehaviour
{
    [SerializeField] private float reviveTime = 3f;
    [SerializeField] private float downedDuration = 10f;

    private PlayerState _state = PlayerState.Alive;
    private float _downedTimer;
    private float _reviveProgress;
    private bool _beingRevived;

    public void OnDowned()
    {
        _state = PlayerState.Downed;
        _downedTimer = downedDuration;
        _reviveProgress = 0f;
    }

    private void Update()
    {
        if (_state != PlayerState.Downed) return;

        _downedTimer -= Time.deltaTime;
        if (_downedTimer <= 0f)
        {
            _state = PlayerState.Dead;
            OnDeadFinal();
            return;
        }

        if (_beingRevived)
        {
            _reviveProgress += Time.deltaTime / reviveTime;
            if (_reviveProgress >= 1f) Revive();
        }
        else
        {
            _reviveProgress = Mathf.Max(0f, _reviveProgress - Time.deltaTime);
        }
    }

    public void StartRevive() => _beingRevived = true;
    public void StopRevive()  => _beingRevived = false;

    private void Revive()
    {
        _state = PlayerState.Alive;
        _reviveProgress = 0f;
        // HP를 최대치의 30%로 회복
    }

    private void OnDeadFinal()
    {
        // 게임오버 처리 또는 EventBus.Emit(GameOverEvent)
    }
}
```

### OnionCat 전용: 임계 상태 (Critical State)
공유 HP가 0에 가까워질 때 즉사 대신 짧은 유예 시간을 부여하는 구조:

```csharp
public class CriticalStateHandler : MonoBehaviour
{
    [SerializeField] private float criticalHpRatio = 0.15f; // HP 15% 이하 진입 조건
    [SerializeField] private float criticalDuration = 3f;   // 무적 유예 시간
    [SerializeField] private float healOnKill = 5f;         // 임계 중 처치 시 회복량

    private SharedBodyHP _hp;
    private bool _inCritical;
    private DashIFrameSystem _dash;

    private void Awake()
    {
        _hp = GetComponent<SharedBodyHP>();
        _dash = GetComponent<DashIFrameSystem>();
    }

    private void Update()
    {
        if (_inCritical) return;
        if ((float)_hp.Current / _hp.Max <= criticalHpRatio)
            StartCoroutine(CriticalStateRoutine());
    }

    private IEnumerator CriticalStateRoutine()
    {
        _inCritical = true;
        _dash.ForceInvincible(criticalDuration); // 무적 활성화
        // 화면 레드 비네트 이펙트 활성화
        // "CRITICAL!" UI 표시

        yield return new WaitForSeconds(criticalDuration);

        _inCritical = false;
        // 비네트/UI 비활성화
        // 이후 다음 피격 시 즉사
    }

    public void OnEnemyKilledDuringCritical()
    {
        if (!_inCritical) return;
        _hp.Heal(healOnKill); // 임계 중 처치 시 소량 회복
    }
}
```

### Death Defiance 토큰 (Hades 참고)
```csharp
public class DeathDefianceToken : MonoBehaviour
{
    [SerializeField] private int tokenCount = 1;
    [SerializeField] private float reviveHpRatio = 0.5f;

    private SharedBodyHP _hp;

    private void Awake() => _hp = GetComponent<SharedBodyHP>();

    // HP가 0이 되려는 시점에 호출
    public bool TryConsume()
    {
        if (tokenCount <= 0) return false;
        tokenCount--;
        _hp.SetHp(Mathf.RoundToInt(_hp.Max * reviveHpRatio));
        // 황금빛 부활 이펙트 재생
        return true;
    }
}
```

SharedBodyHP의 TakeDamage에서:
```csharp
if (currentHp <= 0)
{
    if (!_deathDefianceToken.TryConsume())
        GameOver();
}
```

### 부활 진행률 UI (CircleProgressBar)
```csharp
public class ReviveProgressUI : MonoBehaviour
{
    [SerializeField] private Image fillImage;

    public void UpdateProgress(float t) // t: 0~1
    {
        fillImage.fillAmount = t;
        gameObject.SetActive(t > 0f);
    }
}
```
Image Type을 **Filled**, Fill Method를 **Radial 360**으로 설정.

## OnionCat 적용 포인트

### 1. 임계 상태 (Critical State) — 핵심 생존 메카닉
- HP 15% 이하 진입 시 3초 무적 + 화면 레드 비네트
- 이 시간 동안 Cat이 적 처치 → HP 5 회복
- 임계 상태 종료 후 다음 피격 = 사망 → 긴장감 유지

### 2. "고양이 목숨" 아이템 (런 내 획득)
| 아이템명 | 효과 |
|---------|------|
| 고양이 목숨 | 이번 런 1회 즉사 방지, HP 50% 회복 |
| 고양이 9목숨 | 이번 런 3회 즉사 방지, HP 25% 회복 |
| 부활의 씨앗 | 즉사 방지 1회 + 임계 상태 지속 5초로 연장 |

고양이 발바닥 아이콘을 HUD에 표시해 남은 횟수를 직관적으로 보여줌.

### 3. 패리 연동 — 임계 상태 연장
Onion의 패리 성공 시 임계 상태 타이머 +1초 연장하는 업그레이드 → 방어(P2)가 생존과 직결.

### 4. 임계 상태 중 Cat 분노 버프
HP 15% 이하 진입 시 Cat의 베기 대미지 1.5배 + 빨간 잔상 이펙트 → 위기를 역전 기회로.

### 5. 임계 상태 독백 대사
진입 시 Cat의 짧은 대사 출력 ("포기하지 마...!") → 텍스트 팝업으로 가볍게 감정 몰입 유도.

## 참고 링크
- Hades Death Defiance 분석: https://www.gamedeveloper.com/design/hades-design-lessons
- Unity Image Fill (Radial): https://docs.unity3d.com/Manual/script-Image.html
- Unity Coroutine: https://docs.unity3d.com/Manual/Coroutines.html
- Darkest Dungeon 데스 도어 시스템: 유튜브에서 "Darkest Dungeon death's door mechanic" 검색
