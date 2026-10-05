# Roguelike Economy Design

리서치 날짜: 2026-10-05

## 개요

로그라이크의 "경제"란 재화(골드, 파편, 소울 등)의 획득-소비 흐름과 업그레이드 선택의 **가치 함수**를 말한다. 경제가 망가지면 플레이어가 "항상 같은 것만 산다"거나 "골드가 남아돌아 의미가 없다"는 느낌을 받는다. OnionCat처럼 퍼런 아이템 선택 화면이 있는 로그라이크에서 균형 잡힌 경제는 재플레이 가치의 핵심이다.

## 핵심 이론

### 1. 기대값 균형 (Expected Value)
업그레이드/아이템 각각이 플레이어에게 주는 **평균적 기대 이익**이 비교 가능해야 한다.

```
선택 A 기대값 = (효과 크기) × (발동 빈도) × (조합 승수)
```

예:
- "공격력 +10%" (StatUpgrade): 발동 항상, 효과 작음
- "처치 시 25% 확률로 체력 1 회복" (Passive): 발동 가끔, 지속성 있음

**두 카드가 비슷한 상황에서 체감이 비슷하면** 선택에 의미가 생긴다.

### 2. 복리 vs 단리 성장
- **단리 (Additive)**: +10% 공격력 5장 = 총 +50% → 안전하지만 후반 파워 약함
- **복리 (Multiplicative)**: ×1.1 공격력 5장 = ×1.61 → 후반 폭발적

로그라이크에서 보통 **단리 합산 후 복리 최종 적용** 구조가 안정적:
```csharp
float finalDamage = baseDamage
    * (1 + sumOfAdditiveMods)   // StatUpgrade
    * productOfMultMods;         // 세트 보너스, ClawStyle
```

### 3. 재화 흐름 설계 원칙

| 단계 | 재화 수입 | 재화 지출 | 설계 목표 |
|------|---------|---------|---------|
| 초반 방 (1~3) | 적 처치, 방 클리어 | 첫 업그레이드 | 약간 부족 → 선택 긴장감 |
| 중반 방 (4~6) | 증가, 엘리트 드롭 | 중형 업그레이드 | 균형 → 2~3개 선택 가능 |
| 후반 방 (7~) | 많음, 보너스 | 고급 카드/아이템 | 여유 → 플레이 방향성 확정 |

### 4. 쓸모없는 재화 방지 (Sink 설계)
재화가 남아돌면 선택의 의미가 없어진다. **재화 흡수처(Sink)**가 필요:
- 상점에서 재화로 카드 구매
- 방 도전 보상 (위험 vs 보상 선택)
- 재료 업그레이드 비용
- 단기적 소모 (한 방에서만 쓰는 버프 구매 등)

### 5. 피티 시스템 (Pity)
연속으로 안 좋은 카드만 나오면 플레이어가 포기한다. 보장 장치 필요:

```csharp
// 가중치 누적 피티 예시
int badPickCount = 0;

WeightedItem PickCard() {
    float pityBonus = badPickCount * 0.15f; // 연속 평범 카드마다 +15% 확률
    WeightedItem result = WeightedRoll(pityBonus);
    if (result.tier == Tier.Rare || result.tier == Tier.Epic)
        badPickCount = 0;
    else
        badPickCount++;
    return result;
}
```

## Unity 구현 방법

### 카드 가중치 테이블
```csharp
[CreateAssetMenu]
public class RewardTable : ScriptableObject {
    [Serializable]
    public struct Entry {
        public BaseReward reward;
        [Range(0f, 100f)] public float weight;
        public RewardAxis axis;          // StatUpgrade, Passive, OnionSkill, ClawStyle
    }
    public List<Entry> entries;

    public BaseReward Roll(RewardAxis axis, System.Random rng) {
        var pool = entries.Where(e => e.axis == axis).ToList();
        float total = pool.Sum(e => e.weight);
        float r = (float)rng.NextDouble() * total;
        float acc = 0;
        foreach (var e in pool) {
            acc += e.weight;
            if (r <= acc) return e.reward;
        }
        return pool.Last().reward;
    }
}
```

### 아이템 값 비교 디버그 도구
```csharp
// 에디터 메뉴: 카드별 "DPS 환산 기대값" 출력
#if UNITY_EDITOR
[MenuItem("OnionCat/Debug/Print Card EV")]
static void PrintCardExpectedValues() {
    foreach (var entry in Resources.Load<RewardTable>("RewardTable").entries) {
        float ev = entry.reward.EstimateEV();  // 각 카드에 EstimateEV() 구현
        Debug.Log($"{entry.reward.name}: EV={ev:F2} weight={entry.weight}");
    }
}
#endif
```

### 경제 밸런스 스프레드시트 연동
기본 흐름:
1. 방별 평균 드롭 재화량을 Google Sheets에 기입
2. 평균 카드 비용을 입력
3. "7방 클리어 시 몇 개 카드를 살 수 있나?" 시뮬레이션

직접 시뮬레이터 없이 빠른 접근:
- 5회 런 플레이 후 "골드 남음"이 0에 가까우면 균형
- 첫 방에서 부족 → 3번 방에서 첫 구매 → 보스 방 전 3~4장 보유

## OnionCat 적용 포인트

### 현재 시스템과의 연계
OnionCat은 재화 대신 **카드 선택 횟수(방 클리어 시 직접 선택)** 방식이므로 "쓸모없는 재화" 문제가 덜하다. 하지만 카드 풀 가중치 설계는 동일하게 중요하다.

### 카드 EV 균형 체크리스트
- [ ] StatUpgrade 카드들은 서로 체감이 비슷한가? (공격력+% vs 체력+% vs 속도+%)
- [ ] Passive 세트 카드는 단독으로도 가치가 있는가?
- [ ] ClawStyle/OnionSkill은 운이 나빠도 "일단 괜찮은 것"이 나오는가?
- [ ] 피티 시스템: 같은 축(Axis) 카드를 2회 연속 별로인 것 뽑으면 3번째는 보장 필요

### 권장 가중치 초기값 (조정 필요)
| 등급 | 가중치 예시 | 설명 |
|------|----------|------|
| 평범 (Common) | 60 | 항상 무난하게 쓸 수 있음 |
| 희귀 (Rare) | 30 | 특정 상황에 강함 |
| 서사 (Epic) | 10 | 빌드를 바꾸는 강력한 효과 |

초반(방 1~3) → Common 80 / Rare 18 / Epic 2  
중반(방 4~6) → Common 60 / Rare 30 / Epic 10  
후반(방 7+) → Common 40 / Rare 40 / Epic 20

```csharp
// 방 번호별 가중치 보정
float GetTierBonus(int roomIndex, RewardTier tier) {
    float progress = Mathf.Clamp01(roomIndex / 10f); // 10방 기준
    return tier switch {
        RewardTier.Common => Mathf.Lerp(80, 40, progress),
        RewardTier.Rare   => Mathf.Lerp(18, 40, progress),
        RewardTier.Epic   => Mathf.Lerp(2,  20, progress),
        _ => 0
    };
}
```

## 참고 링크

- [Game Balance Concepts (free course)](https://gamebalanceconcepts.wordpress.com/)
- [Roguelike Economy Design - GDC Vault](https://www.gdcvault.com/)
- [Hades Economy Breakdown - YouTube (NathIRL)](https://www.youtube.com/watch?v=6R8H_zQViz8)
- [Unity Weighted Random Selection](https://docs.unity3d.com/ScriptReference/Random.Range.html)
- [Probability Theory for Game Designers](https://en.wikipedia.org/wiki/Probability_theory)
