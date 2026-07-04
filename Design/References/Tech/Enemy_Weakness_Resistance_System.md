# 적 약점/내성 시스템 (Enemy Weakness & Resistance System)

리서치 날짜: 2026-07-04

## 개요

OnionCat의 **핵심 협동 메카닉**: "근접에만 약한 적 vs 원거리에만 약한 적"을 구현하는 시스템. 플레이어 1(Cat, 근접)과 플레이어 2(Crop, 원거리)가 반드시 소통·협력해야 하는 근본적인 이유를 게임플레이 레벨에서 강제한다.

- **왜 중요한가**: 약점 없이 둘 다 모든 적을 때릴 수 있으면 협동 의미가 사라진다
- **무엇을 만드는가**: 데미지 타입 판별 → 배율 적용 → 시각/청각 피드백의 전체 파이프라인

---

## Unity 구현 방법

### 1단계: 데미지 타입 정의

```csharp
// DamageType.cs
public enum DamageType
{
    Melee,   // Cat의 근접 공격
    Ranged,  // Crop의 원거리 공격
    True     // 약점 무시 (罠, 환경 데미지 등)
}
```

### 2단계: ScriptableObject로 적 약점 데이터 정의

```csharp
// EnemyData.cs
using UnityEngine;

[CreateAssetMenu(menuName = "OnionCat/EnemyData")]
public class EnemyData : ScriptableObject
{
    public string enemyName;

    [Header("Weakness / Resistance")]
    [Tooltip("이 타입으로 공격 시 데미지 배율")]
    public DamageMultiplierEntry[] damageMultipliers;

    [System.Serializable]
    public struct DamageMultiplierEntry
    {
        public DamageType type;
        [Range(0f, 5f)] public float multiplier; // 0 = 면역, 1 = 보통, 2 = 약점
    }

    // 편의 메서드
    public float GetMultiplier(DamageType type)
    {
        foreach (var entry in damageMultipliers)
            if (entry.type == type)
                return entry.multiplier;
        return 1f; // 기본값: 보통 데미지
    }
}
```

**EnemyData 설정 예시 (Inspector)**:
| 적 이름 | Melee 배율 | Ranged 배율 |
|---------|-----------|------------|
| 갑각 슬라임 | 0.0 (면역) | 2.0 (약점) |
| 비행 씨앗 | 2.0 (약점) | 0.0 (면역) |
| 뿌리 골렘 | 1.0 | 1.0 |
| 폭발 버섯 | 1.0 (처치 가능) | 3.0 (즉시 폭발!) |

### 3단계: Enemy에서 데미지 처리

```csharp
// Enemy.cs (발췌)
public class Enemy : MonoBehaviour
{
    [SerializeField] private EnemyData data;
    [SerializeField] private float maxHp = 100f;
    private float currentHp;

    public void TakeDamage(float amount, DamageType type)
    {
        float multiplier = data.GetMultiplier(type);

        if (multiplier <= 0f)
        {
            PlayImmuneEffect();   // 튕기는 이펙트
            return;
        }

        float finalDamage = amount * multiplier;
        currentHp -= finalDamage;

        // 약점/보통/면역에 따라 다른 피드백
        if (multiplier >= 2f)
            PlayWeakHitEffect(finalDamage);   // 강조 피드백
        else
            PlayNormalHitEffect(finalDamage);

        if (currentHp <= 0f)
            Die();
    }

    private void PlayImmuneEffect()
    {
        // 회색 '!' 이펙트, 방어막 튕김 사운드
    }

    private void PlayWeakHitEffect(float damage)
    {
        // 노란/빨간 큰 숫자, 히트스톱 2프레임, 강한 사운드
    }

    private void PlayNormalHitEffect(float damage)
    {
        // 흰색 숫자, 히트스톱 1프레임, 보통 사운드
    }
}
```

### 4단계: 공격 스크립트에서 DamageType 전달

```csharp
// CatMeleeAttack.cs (Cat 근접 공격)
void OnTriggerEnter2D(Collider2D other)
{
    if (other.TryGetComponent<Enemy>(out var enemy))
        enemy.TakeDamage(attackPower, DamageType.Melee);
}

// CropProjectile.cs (Crop 원거리 발사체)
void OnTriggerEnter2D(Collider2D other)
{
    if (other.TryGetComponent<Enemy>(out var enemy))
        enemy.TakeDamage(projectileDamage, DamageType.Ranged);
}
```

### 5단계: 약점 아이콘 표시 (선택)

```csharp
// EnemyWeaknessIndicator.cs
// 적 머리 위 작은 아이콘으로 약점 타입 표시
// 첫 조우 시 "?" → 처치 후 BestiaryManager에서 해금

[SerializeField] private SpriteRenderer weaknessIcon;
[SerializeField] private Sprite meleeIcon;    // 칼 아이콘
[SerializeField] private Sprite rangedIcon;   // 씨앗 아이콘
[SerializeField] private Sprite unknownIcon;  // 물음표

void Start()
{
    bool discovered = BestiaryManager.Instance.IsDiscovered(data.enemyName);
    if (!discovered)
    {
        weaknessIcon.sprite = unknownIcon;
        return;
    }

    // 주요 약점 타입 표시
    DamageType mainWeak = GetMainWeakness();
    weaknessIcon.sprite = mainWeak == DamageType.Melee ? meleeIcon : rangedIcon;
}
```

---

## OnionCat 적용 포인트

### 적 타입 분류 (4가지)

| 타입 | 근접 배율 | 원거리 배율 | 설명 | 협동 요구 |
|------|---------|-----------|------|---------|
| **Cat Only** | 2.0 | 0.0 | 원거리 면역 (방어막 or 반사) | Cat 전담, Crop은 지원 |
| **Crop Only** | 0.0 | 2.0 | 근접 면역 (가시 or 전기장) | Crop 전담, Cat은 이동 |
| **양쪽 약점** | 1.5 | 1.5 | 올바른 플레이어가 때릴수록 이득 | 적극 협동 보상 |
| **일반 잡몹** | 1.0 | 1.0 | 누구든 OK | 연습/열혈 몹 |

### 시각 피드백 설계

```
올바른 공격:  노란/주황 숫자 + 별 파티클 + 강한 히트스톱(2프레임)
보통 공격:   흰색 숫자 + 일반 히트스톱(1프레임)
면역(튕김):  회색 "IMMUNE" 텍스트 + 방어막 리플 이펙트 + 경고음
```

### 주의 사항

- **True 데미지 타입** 필수: 환경 피해(가시, 구덩이), 보스의 즉사 공격 등은 약점 무시여야 함
- **Melee/Ranged만 2종류로 시작**: 나중에 마법, 폭발 등 타입을 추가하고 싶어도 초반엔 2가지만 유지
- **면역(0.0) vs 저항(0.5)의 차이**: 로그라이크에서는 아예 0보다 0.5(저항)가 더 유연한 설계
- **데미지 숫자 UI**: 약점 타입 공격 시 숫자가 크게 표시되어야 플레이어가 "뭔가 달라!"를 느낌

---

## 참고 링크

- Unity ScriptableObject 공식: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- 데미지 타입 시스템 구현 예제: https://www.youtube.com/watch?v=_lEXZgUuMtM (Brackeys - damage system)
- Hades 약점 시스템 분석: https://gamedeveloper.com/design/hades-design-retrospective
- Nuclear Throne 타입 데미지: https://nuclear-throne.fandom.com/wiki/Damage_Types
- Enter the Gungeon 적 갑옷 시스템: https://enterthegungeon.fandom.com/wiki/Enemies
