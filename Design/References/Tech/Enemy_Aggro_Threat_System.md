# 적 어그로 & 위협 타겟 시스템

리서치 날짜: 2026-08-13

## 개요

멀티플레이어 게임에서 적이 **어떤 플레이어를 공격할지** 결정하는 시스템.
OnionCat은 한 몸(P1 고양이 + P2 파)이지만, 각 플레이어가 독립적으로 행동하는 구조이므로 "적이 누구에게 반응하는가"가 전투 다양성에 직결된다.

적이 무작위로 타겟을 바꾸면 전략이 없어지고, 항상 같은 플레이어만 타겟하면 한쪽이 지루해진다. **위협값(Threat)** 기반 타겟 선택이 이 균형을 잡는다.

---

## 위협값(Threat) 계산 원칙

### 기본 공식
```
Threat(player) = 거리 가중치 + 데미지 가중치 + 특수 상황 보너스
```

### 요소별 설명

| 요소 | 기여 방식 | 예시 |
|---|---|---|
| 거리 | 가까울수록 위협값 ↑ | 거리 2 → Threat +50, 거리 10 → Threat +5 |
| 최근 피해량 | 직전 2초 내 입힌 피해량 | 100 데미지 → Threat +30 |
| 타입 약점 매칭 | 현재 약점에 맞는 플레이어 | 근접 약점 적 ↔ P1이 근처 → Threat +40 |
| 마지막 공격자 | 가장 마지막으로 때린 플레이어 | "누가 때렸지?" 기억 2초 유지 |
| 의도적 도발 | 특정 아이템/스킬 효과 | 도발 아이템 → Threat +100 일시적 |

---

## Unity 구현 방법

### 1. ThreatTracker 컴포넌트 (적에 부착)

```csharp
using System.Collections.Generic;
using UnityEngine;

public class ThreatTracker : MonoBehaviour
{
    [SerializeField] private float threatDecayRate = 10f;   // 초당 감소량
    [SerializeField] private float distanceWeight = 20f;
    [SerializeField] private float damageWeight = 0.3f;     // 데미지 1당 위협값

    // 플레이어 인덱스(0=P1, 1=P2) → 위협값
    private readonly Dictionary<int, float> threatValues = new();
    private readonly Dictionary<int, float> lastDamageTimes = new();

    private void Update()
    {
        // 시간에 따른 위협값 감소 (기억이 희미해짐)
        foreach (var key in new List<int>(threatValues.Keys))
        {
            threatValues[key] = Mathf.Max(0f, threatValues[key] - threatDecayRate * Time.deltaTime);
        }
    }

    /// <summary>적이 데미지를 받을 때 호출</summary>
    public void RegisterDamage(int playerIndex, float damage)
    {
        if (!threatValues.ContainsKey(playerIndex)) threatValues[playerIndex] = 0f;
        threatValues[playerIndex] += damage * damageWeight;
        lastDamageTimes[playerIndex] = Time.time;
    }

    /// <summary>현재 가장 높은 위협값의 플레이어 Transform 반환</summary>
    public Transform GetHighestThreatTarget(Transform[] playerTransforms)
    {
        int bestIndex = 0;
        float bestThreat = -1f;

        for (int i = 0; i < playerTransforms.Length; i++)
        {
            float dist = Vector2.Distance(transform.position, playerTransforms[i].position);
            float distThreat = distanceWeight / Mathf.Max(dist, 0.1f);
            float total = distThreat + (threatValues.ContainsKey(i) ? threatValues[i] : 0f);

            if (total > bestThreat)
            {
                bestThreat = total;
                bestIndex = i;
            }
        }

        return playerTransforms[bestIndex];
    }
}
```

### 2. 적 AI에서 ThreatTracker 사용

```csharp
public class EnemyAI : MonoBehaviour
{
    private ThreatTracker threatTracker;
    private Transform[] playerTransforms;
    private Transform currentTarget;

    [SerializeField] private float targetUpdateInterval = 0.5f; // 0.5초마다 타겟 재평가
    private float targetUpdateTimer;

    private void Awake()
    {
        threatTracker = GetComponent<ThreatTracker>();
    }

    private void Start()
    {
        // GameManager 등에서 플레이어 배열 가져오기
        playerTransforms = GameManager.Instance.GetPlayerTransforms();
    }

    private void Update()
    {
        targetUpdateTimer -= Time.deltaTime;
        if (targetUpdateTimer <= 0f)
        {
            currentTarget = threatTracker.GetHighestThreatTarget(playerTransforms);
            targetUpdateTimer = targetUpdateInterval;
        }

        // currentTarget을 향해 이동/공격
    }

    // 이 적이 피해를 받을 때 (EnemyHealth 등에서 호출)
    public void OnTakeDamage(int attackerPlayerIndex, float damage)
    {
        threatTracker.RegisterDamage(attackerPlayerIndex, damage);
    }
}
```

### 3. 타입 약점 기반 어그로 보너스

```csharp
public class TypeWeaknessAggro : MonoBehaviour
{
    [SerializeField] private AttackType weakness; // Melee or Ranged
    [SerializeField] private float weaknessThreatBonus = 40f;

    public float GetTypeThreatBonus(PlayerType playerType)
    {
        // 약점 타입 플레이어가 가까이 있으면 자동으로 그 플레이어를 향해 감
        return (playerType.attackType == weakness) ? weaknessThreatBonus : 0f;
    }
}
```

---

## OnionCat 적용 포인트

### 적 타입별 어그로 행동 설계

| 적 타입 | 기본 어그로 | 특이사항 |
|---|---|---|
| **근접형 적** (일반 몬스터) | 가장 가까운 플레이어 | OnionCat는 한 몸 → 사실상 항상 P1 위치 = P2 위치 |
| **원거리형 적** (궁수, 마법사) | 마지막으로 때린 플레이어 | P2 투사체가 원거리에서 때리면 P2 쪽으로 조준 → P1이 뒤통수 공격 기회 |
| **근접 약점 적** | P1이 근접하면 P1으로 어그로 전환 | P1이 유인 → P2 원거리 공격 구도 유도 |
| **원거리 약점 적** | P2 마우스 조준 중이면 P2 쪽 피하려 함 | 방패로 P2 조준 방해 → P1 근접 필요 |

### OnionCat 특수 상황: 한 몸 두 플레이어
P1과 P2는 같은 위치이므로 "거리 기반" 어그로는 항상 동점.
→ **마지막 공격자 기준 + 약점 타입 매칭**이 핵심 차별화 요소.

```csharp
// OnionCat 전용: 약점 타입 + 최근 피해 통합 위협 계산
float GetOnionCatThreat(int playerIndex, AttackType playerAttackType)
{
    float base = threatValues.ContainsKey(playerIndex) ? threatValues[playerIndex] : 0f;
    float typeBonus = (playerAttackType == this.weakness) ? 40f : 0f;
    return base + typeBonus;
}
```

### 위협 시각화 (옵션)
적의 "주의 방향" 아이콘(느낌표, 화살표)을 Enemy_Awareness_Alert_Visual.md와 결합하면
플레이어가 어그로 상태를 직관적으로 파악 가능.

---

## 참고 링크

- Unity Forum — 멀티플레이어 적 어그로 토론: https://forum.unity.com/threads/enemy-aggro-system-multiplayer.html
- GDC Talk — Designing Enemy AI for Co-op (Larian): https://www.gdcvault.com/play/1026349/
- Game AI Pro — Threat Management Systems: https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter17_Threat_Assessment.pdf
- 실제 구현 예제 (GitHub): https://github.com/Brackeys/2D-Character-Controller (기초 참고용)
- Ruiner 적 AI 분석 영상: https://www.youtube.com/watch?v=ZJNiNl7a5mg
