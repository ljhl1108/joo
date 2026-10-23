# 런타임 보상 풀 동적 필터링 시스템

리서치 날짜: 2026-10-23

## 개요

로그라이크에서 보상(장비·스킬·패시브) 목록을 보여줄 때, 런 상태에 따라 **실시간으로 제외 / 가중치 조정**하는 시스템.  
단순히 "랜덤 3개 뽑기"에 그치지 않고, 현재 플레이어 상태를 반영해 의미 있는 선택지만 노출한다.

OnionCat에서는 이미 온실 해금(`GearItem.UnlockCost > 0`이면 풀에서 제외), 장비 칸 가득 참, 동일 장비 레벨업 처리 등이 구현돼 있다.  
이 문서는 그 기반을 확장하는 패턴과 OnionCat에 바로 적용 가능한 규칙을 정리한다.

---

## Unity 구현 방법

### 1. 필터 체인 패턴 (Filter Chain / Predicate Pipeline)

```csharp
// 필터 함수 목록을 파이프라인으로 연결
public class RewardPool
{
    private List<Func<GearItem, RunData, bool>> _filters = new();

    public void AddFilter(Func<GearItem, RunData, bool> filter)
        => _filters.Add(filter);

    public List<GearItem> GetFiltered(IEnumerable<GearItem> source, RunData run)
    {
        return source.Where(item =>
            _filters.All(f => f(item, run))
        ).ToList();
    }
}
```

사용 예:
```csharp
pool.AddFilter((item, run) => item.UnlockCost == 0 || run.meta.IsUnlocked(item));
pool.AddFilter((item, run) => !run.IsMaxLevel(item)); // 이미 만렙인 장비 제외
pool.AddFilter((item, run) => item.Owner == Owner.Any || item.Owner == run.phase); // 역할 필터
```

---

### 2. 가중치 조정자 (Weight Modifier)

단순 include/exclude 외에, 드롭 확률에 보정치를 곱하는 방식.

```csharp
public class WeightedPool
{
    private List<Func<GearItem, RunData, float>> _modifiers = new();

    public float GetWeight(GearItem item, RunData run)
    {
        float w = item.baseWeight;
        foreach (var mod in _modifiers)
            w *= mod(item, run);
        return Mathf.Max(0, w);
    }
}
```

가중치 조정 규칙 예시:
```csharp
// 이미 보유 중인 세트의 다음 장비를 상향
modifiers.Add((item, run) => {
    int setCount = run.CountSetItems(item.setId);
    return setCount > 0 ? 1f + setCount * 0.3f : 1f; // 세트 장비 많을수록 확률 상승
});

// 같은 효과 계열(불꽃 속성)이 이미 3개 이상이면 하향
modifiers.Add((item, run) => {
    int fireItems = run.CountByElement(Element.Fire);
    return fireItems >= 3 ? 0.5f : 1f;
});
```

---

### 3. 보상 드래프트 실행 (Draft Draw)

```csharp
public List<GearItem> DrawRewards(RunData run, int count = 3)
{
    var filtered = GetFiltered(allItems, run);
    
    // 가중치 기반 중복 없는 추출
    var drawn = new List<GearItem>();
    var pool = new List<(GearItem item, float weight)>(
        filtered.Select(i => (i, GetWeight(i, run)))
    );

    for (int i = 0; i < count && pool.Count > 0; i++)
    {
        float total = pool.Sum(p => p.weight);
        float roll = Random.value * total;
        float acc = 0;
        for (int j = 0; j < pool.Count; j++)
        {
            acc += pool[j].weight;
            if (roll <= acc)
            {
                drawn.Add(pool[j].item);
                pool.RemoveAt(j);
                break;
            }
        }
    }
    return drawn;
}
```

---

### 4. ScriptableObject 기반 필터 규칙 (데이터 주도)

코드가 아니라 에셋에서 필터 규칙을 정의하는 방식. 레벨 디자이너가 Unity Editor에서 설정 가능.

```csharp
[CreateAssetMenu(menuName = "OnionCat/Reward Filter Rule")]
public class RewardFilterRule : ScriptableObject
{
    public Rarity minRarity;          // 최소 등급 이상만 드롭
    public bool excludeOwned;         // 이미 장착 중인 장비 제외
    public bool boostSetCompletion;   // 세트 완성 방향 상향
    public float epicMultiplier = 1f; // 에픽 등급 가중치 배율
}
```

보물방 vs 상점 vs 엘리트방마다 다른 `RewardFilterRule` 에셋 적용 가능.

---

### 5. 전용 RNG 시드 분리

보상 풀 드로우는 별도 `System.Random` 인스턴스를 써서 시드 재현이 가능하게 한다.  
(메인 Random.value를 쓰면 다른 로직 실행 순서에 따라 같은 시드에서 결과가 달라짐)

```csharp
private System.Random _rewardRng;

void InitRng(RunData run)
{
    _rewardRng = new System.Random(run.seed ^ 0xDEAD_BEEF);
}
```

---

## OnionCat 적용 포인트

### 현재 구현 상태

- `RewardTable.Pool`이 `GearItem.UnlockCost > 0`이면 해당 장비를 제외 (온실 해금 전)
- `UpgradeSelectUI`가 고양이·양파 각자 3장 드로우

### 바로 적용 가능한 추가 필터 규칙

| 규칙 | 설명 | 구현 위치 |
|------|------|-----------|
| **세트 완성 상향** | 현재 세트 장비가 2개 이상이면 같은 세트 다음 단계 장비 가중치 ×1.5 | `RewardTable.DrawFor(owner, run)` |
| **슬롯 포화 시 제외** | 패시브 6칸이 꽉 차면 공용 패시브 제외, 대신 장비 확률 상승 | 필터 체인 |
| **최근 본 장비 제외** | 직전 2~3번 보상에서 등장한 장비는 이번 드로우에서 제외 | `RunData.recentRewards` 큐 |
| **레어리티 보정** | 방 번호가 높을수록 에픽 이상 확률 점진적 상승 | `epicMultiplier = 1 + roomIndex * 0.05f` |
| **역할 전용 보정** | 보물방에서는 양파 장비 / 고양이 장비를 번갈아 우선 배치 | 방 유형별 `RewardFilterRule` |
| **첫 런 튜토리얼** | 첫 번째 런에서는 필수 기본 장비(발톱 무기 · 씨앗 무기)가 반드시 등장 | `run.isFirstRun` 분기 |

### 우선 추천 구현 순서

1. **세트 완성 상향** (가중치 조정) → 빌드 방향이 자연스럽게 생기는 효과
2. **최근 보상 제외 큐** → 3개 보상에서 같은 장비만 계속 나오는 답답함 해소
3. **방 번호 기반 레어리티 보정** → 런 후반부 긴장감 증가

---

## 참고 링크

- Unity 공식 WeightedRandom 예시: https://docs.unity3d.com/Manual/RandomNumbers.html
- Hades GDC 발표 (보상 드래프트 설계): https://www.gdcvault.com/play/1026857/
- Slay the Spire 보상 드래프트 분석: https://steamcommunity.com/sharedfiles/filedetails/?id=1796196719
- 가중치 드로우 알고리즘 (Alias Method): https://www.keithschwarz.com/darts-dice-coins/
