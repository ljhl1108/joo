# Enemy Hearing & Sound Detection System (소리 기반 적 감지 시스템)

리서치 날짜: 2026-11-24

## 개요

시야각(FOV) 감지와 짝을 이루는 **청각 기반 감지** 시스템. 플레이어의 행동(발소리, 공격, 착지 충격)이 소리를 발생시키고, 그 소리 반경 안에 있는 적이 경각 상태로 전환된다. OnionCat에서는 플레이어가 한 명이 소리를 내면 근처 적 전체가 반응하는 상황(예: 양파 씨앗 폭발 소리 → 반대편 적도 주목)을 처리할 때 유용하다.

---

## Unity 구현 방법

### 1. SoundEvent 데이터 구조

```csharp
public struct SoundEvent
{
    public Vector2 origin;
    public float radius;         // 소리가 들리는 최대 거리
    public SoundType type;       // Footstep / Attack / Explosion / Ambient
    public float volume;         // 0~1, 반경 안에서 거리에 따라 감쇠
}

public enum SoundType
{
    Footstep,       // 약함 — 아주 가까운 적만 반응
    Attack,         // 중간 — 콤보 소리, 칼바람 소리
    Explosion,      // 강함 — 씨앗 폭탄, 보스 충격파
    Special,        // 특수 — 에너지 방출, 고유 이벤트
}
```

### 2. SoundEventBus (전역 싱글턴)

```csharp
public static class SoundEventBus
{
    // 소리를 발생시키는 쪽이 여기에 등록
    public static event Action<SoundEvent> OnSoundEmitted;

    public static void Emit(Vector2 origin, float radius, SoundType type, float volume = 1f)
    {
        OnSoundEmitted?.Invoke(new SoundEvent
        {
            origin = origin,
            radius = radius,
            type = type,
            volume = volume
        });
    }
}
```

### 3. EnemyHearing 컴포넌트 (각 적에 부착)

```csharp
public class EnemyHearing : MonoBehaviour
{
    [SerializeField] private float hearingMultiplier = 1f; // 종류별 조정
    [SerializeField] private SoundType minAudibleType = SoundType.Footstep;

    private EnemyBase enemy;

    private void OnEnable()
    {
        enemy = GetComponent<EnemyBase>();
        SoundEventBus.OnSoundEmitted += OnSoundReceived;
    }

    private void OnDisable()
    {
        SoundEventBus.OnSoundEmitted -= OnSoundReceived;
    }

    private void OnSoundReceived(SoundEvent se)
    {
        if (se.type < minAudibleType) return;  // 너무 약한 소리는 무시
        if (enemy.Status.isStunned) return;

        float dist = Vector2.Distance(transform.position, se.origin);
        float effectiveRadius = se.radius * hearingMultiplier;

        if (dist <= effectiveRadius)
        {
            // 거리에 따른 감쇠: 가까울수록 강한 반응
            float intensity = Mathf.Clamp01(1f - (dist / effectiveRadius));
            enemy.OnSoundAlert(se.origin, intensity);
        }
    }
}
```

### 4. EnemyBase에 청각 반응 추가

```csharp
// EnemyBase.cs에 추가
public void OnSoundAlert(Vector2 soundOrigin, float intensity)
{
    // 이미 플레이어를 추적 중이면 무시
    if (currentState == EnemyState.Chase) return;

    if (intensity > 0.6f)
    {
        // 큰 소리 → 소리 발원지로 직접 이동 (조사)
        investigateTarget = soundOrigin;
        ChangeState(EnemyState.Investigate);
    }
    else if (intensity > 0.3f)
    {
        // 중간 소리 → 그 방향 바라보기
        LookToward(soundOrigin);
        ChangeState(EnemyState.Alert);
    }
    // 작은 소리는 무시 (너무 민감하면 게임이 불편해짐)
}
```

### 5. 플레이어 행동별 소리 발생 — 발생 지점에서 Emit

```csharp
// CatController.cs — 착지 시
private void OnLanded()
{
    float fallHeight = prevAirY - transform.position.y;
    if (fallHeight > 1.5f)
    {
        float radius = Mathf.Lerp(2f, 6f, fallHeight / 5f);
        SoundEventBus.Emit(transform.position, radius, SoundType.Attack);
    }
}

// CatAttack.cs — 슬래시 시
public void OnClawAttack()
{
    SoundEventBus.Emit(transform.position, 3f, SoundType.Attack);
}

// SeedProjectile.cs — 폭탄 씨앗 폭발
private void OnExplode()
{
    SoundEventBus.Emit(transform.position, explodeRadius * 1.5f, SoundType.Explosion);
}
```

### 6. 장애물 차단 (선택 사항)

```csharp
// 벽이 소리를 차단하는 고급 옵션
private bool HasLineOfHearing(Vector2 from, Vector2 to)
{
    // Wall 레이어 레이캐스트 — 차단 시 소리 감쇠
    var hit = Physics2D.Linecast(from, to, LayerMask.GetMask("Wall"));
    return hit.collider == null;  // 벽 없으면 들림
}
```

---

## OnionCat 적용 포인트

### OnionCat에서 청각 감지가 필요한 이유
- **양파의 씨앗 폭탄**: 고양이가 없는 쪽에서 폭발 → 그쪽 적이 반응하는 게 자연스러움
- **걷어차기 삭제 이후 환경킬**: `Launch` → `WallCrash` 충격 소리 → 근처 적 경각
- **방 입장 연출**: 플레이어가 방에 들어올 때 발소리로 적이 먼저 반응 가능

### 구현 우선순위 제안

```
1단계 (MVP): 폭발(Explosion) 타입만 구현
   → 씨앗 폭탄 + 보스 충격파에만 반응
   → 반응: Chase 상태로 직접 전환

2단계: Attack 타입 추가
   → 콤보 충격음에 주변 적 경각

3단계: Footstep + 차단 처리
   → 스텔스 요소 추가 가능 (필요 시)
```

### 성능 고려
- `SoundEventBus`는 C# event → 적이 많아도 O(n) 순회, 충분히 빠름
- 프레임마다 체크가 아니라 "소리 발생 시에만" 처리 → 오버헤드 없음
- 적이 100마리 이상이면 `EnemyHearing`의 반응 로직에 JobSystem 고려

### EnemyBase.Active와 연동

```csharp
// 비활성 적(EnemyBase.Active 미포함)은 소리에 반응 불가
// EnemyHearing의 OnEnable/OnDisable에서 자동 처리됨
```

### 조정 파라미터 (HitFeelSettings.asset에 추가 추천)

```
explosionSoundRadius: 6.0f      // 씨앗 폭발 반응 반경
attackSoundRadius: 3.0f         // 일반 공격 소리 반경
alertDecayTime: 2.0f            // Alert 상태 유지 후 복귀 시간
enableSoundDetection: true       // 디버그용 전체 토글
```

---

## 참고 링크

- Unity Physics2D.OverlapCircle: https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircle.html
- Unity C# events (소리버스 패턴): https://docs.microsoft.com/en-us/dotnet/csharp/programming-guide/events/
- 청각 감지 AI 설계 개요: https://www.gamedeveloper.com/design/ai-perception-systems-hearing
- Stealth game sound design: https://www.gdcvault.com/play/1025296
