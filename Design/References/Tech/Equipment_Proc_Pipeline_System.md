# Equipment Proc Pipeline System (장비 발동 효과 처리 파이프라인)

리서치 날짜: 2026-11-22

## 개요

**Proc** = Programmed Random Occurrence. 장비 효과가 특정 조건(피해 주기, 받기, 처치 등)에 의해 **동시에 여러 개 발동**될 때 생기는 문제를 다룬다.

OnionCat처럼 장비가 많고(163종) 세트 보너스까지 있는 로그라이크에서는 한 번의 타격으로 5~8개의 효과가 동시에 "발동" 상태가 된다. 이를 순서 없이 처리하면 다음 문제가 생긴다:
- 화면 이펙트·사운드가 동시에 터져 혼란
- 순서 의존 효과("데미지를 먼저 계산한 뒤 흡혈")가 잘못 처리됨
- 같은 효과가 중복 발동하거나 서로 취소됨

## Proc 처리 파이프라인 단계

```
이벤트 발생
    ↓
[1] 발동 조건 평가       각 GearEffect가 조건 체크 (bool)
    ↓
[2] Proc 큐 수집         발동된 효과들을 List<ProcEntry>에 모음
    ↓
[3] 우선순위 정렬         데미지 계산 > 상태 적용 > 치유 > 연출
    ↓
[4] 순차 실행             한 프레임 안에 로직 실행 (또는 큐 소화)
    ↓
[5] 연출 큐 전달          VFX·SFX는 별도 큐 → 프레임 분산 출력
```

## Unity 구현

### ProcEntry 구조체

```csharp
struct ProcEntry
{
    public GearEffect Source;
    public int Priority;      // 낮을수록 먼저 (0=데미지, 10=버프, 20=연출)
    public Action Execute;
    public VfxRequest Vfx;    // null이면 연출 없음
}
```

### 이벤트 채널 → 큐 수집

```csharp
// GearEffectHost.cs (PlayerStats 또는 RunData에 붙음)
public void RaiseDamageDealt(DamageInfo info)
{
    var procs = new List<ProcEntry>();
    foreach (var effect in _activeEffects)
        effect.TryProc(EventType.DamageDealt, info, procs);

    procs.Sort((a, b) => a.Priority.CompareTo(b.Priority));
    foreach (var p in procs) p.Execute();

    // 연출은 별도 큐 → 최대 3개만 같은 프레임에 출력
    _vfxQueue.Enqueue(procs.Where(p => p.Vfx != null)
                           .Take(3)
                           .Select(p => p.Vfx));
}
```

### VFX 큐 소화 (EffectQueuePlayer.cs)

```csharp
// 연출 큐를 1~2 프레임에 걸쳐 소화 → 한꺼번에 터지는 느낌 방지
IEnumerator DrainVfxQueue()
{
    int perFrame = 2;
    while (_vfxQueue.Count > 0)
    {
        for (int i = 0; i < perFrame && _vfxQueue.Count > 0; i++)
            PlayVfx(_vfxQueue.Dequeue());
        yield return null;
    }
}
```

### 중복 Proc 방지

```csharp
// 같은 EffectType이 같은 타겟에 중복 발동하지 않도록
HashSet<(EffectType, int targetId)> _procGuard = new();

bool TryProc(EffectType type, int targetId)
{
    if (_procGuard.Contains((type, targetId))) return false;
    _procGuard.Add((type, targetId));
    return true;
}
// 매 이벤트 사이클 끝에 _procGuard.Clear()
```

## OnionCat 적용 포인트

| 상황 | 현재 | 개선 방향 |
|------|------|---------|
| `EffectTrigger.WallCrash` 발동 시 | 단일 효과만 처리 | 복수 장비가 반응할 때 순서 보장 필요 |
| 세트 보너스 + 단일 효과 동시 발동 | `PassiveHost.Recalculate`가 정적 계산 | 런타임 프록 이벤트와 정적 세트 보너스를 같은 파이프라인으로 통합하면 버그 감소 |
| VFX 중첩 | 여러 이펙트가 겹쳐 화면이 번쩍임 | VFX 큐 소화로 최대 N개만 동시 출력 |
| 협동 콤보 판정 순서 | `Attacker.Cat / Onion`이 먼저 기록돼야 콤보 카운트 가능 | Priority=0 에 `RecordAttacker`, Priority=5 에 콤보 평가 |

### 권장 Priority 테이블

| Priority | 용도 |
|---------|------|
| 0 | 피해 계산 (배율, 취약) |
| 5 | 협동 콤보 판정 |
| 10 | 상태이상 적용 (Burn, Slow, Stun) |
| 15 | 흡혈 / 실드 회복 |
| 20 | 2차 투사체 생성 |
| 30 | VFX 연출 |
| 40 | SFX |

## 참고 링크

- [Unity Object Pool (proc 오브젝트 재사용)](https://docs.unity3d.com/Manual/object-pooling.html)
- [ScriptableObject Event Channel — 이미 연구됨: `Tech/ScriptableObject_Event_Channel.md`]
- [Coroutine Sequence System — 연출 큐 패턴: `Tech/Coroutine_Sequence_System.md`]
- [Set Bonus Aggregation Algorithm: `Tech/Set_Bonus_Aggregation_Algorithm.md`]
