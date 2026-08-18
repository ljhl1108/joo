# Enemy Elite Variant System (엘리트 변형 적 시스템)

리서치 날짜: 2026-08-18

## 개요

엘리트 변형 시스템은 기존 일반 적에 접두사(prefix) 또는 변형 모디파이어(modifier)를 부여해 강화된 "엘리트" 버전을 만드는 로그라이크의 핵심 콘텐츠 증폭 기법이다.

- Hades의 "저주받은" / "공허의" 변종, Binding of Isaac의 Champion 적이 대표 사례
- 새로운 적 타입을 만들 필요 없이 기존 적의 다양성과 위협도를 배수로 늘림
- 플레이어에게 "익숙한 적이지만 위험하다"는 긴장감 유발
- OnionCat에서는 특정 약점이 바뀌거나 두 플레이어를 동시에 압박하는 변종 설계 가능

---

## Unity 구현 방법

### 1. 데이터 구조 — EliteModifier ScriptableObject

```csharp
[CreateAssetMenu(fileName = "EliteModifier", menuName = "OnionCat/EliteModifier")]
public class EliteModifierSO : ScriptableObject
{
    public string modifierName;         // "화염", "빠른", "보호막"
    public Color tintColor;             // 시각적 구분색 (빨강/파랑/금색 등)
    public float hpMultiplier;          // 기본값 2.0f
    public float speedMultiplier;       // 기본값 1.3f
    public float damageMultiplier;      // 기본값 1.5f
    public float xpMultiplier;          // 드롭 경험치 배율
    public EliteAbility specialAbility; // 특수 행동 열거형
    public bool invertWeakness;         // true: 약점 반전 (근접약→원거리약)
}

public enum EliteAbility
{
    None,
    PeriodicShield,     // 주기적 보호막 생성
    SplitOnDeath,       // 사망 시 소형 적 분열
    TeleportBehindPlayer, // 플레이어 뒤로 순간이동
    AreaDenial,         // 지면에 위험 구역 생성
    ArmorPlating        // 전면 피해 무효
}
```

### 2. 엘리트 적용 — EnemyEliteController.cs

```csharp
public class EnemyEliteController : MonoBehaviour
{
    [SerializeField] private EnemyBase enemy;
    [SerializeField] private SpriteRenderer spriteRenderer;
    [SerializeField] private ParticleSystem eliteParticles;

    private EliteModifierSO modifier;

    public void ApplyEliteModifier(EliteModifierSO mod)
    {
        modifier = mod;

        // 스탯 적용
        enemy.MaxHP = Mathf.RoundToInt(enemy.MaxHP * mod.hpMultiplier);
        enemy.CurrentHP = enemy.MaxHP;
        enemy.MoveSpeed *= mod.speedMultiplier;
        enemy.AttackDamage = Mathf.RoundToInt(enemy.AttackDamage * mod.damageMultiplier);
        enemy.XPReward = Mathf.RoundToInt(enemy.XPReward * mod.xpMultiplier);

        // 약점 반전
        if (mod.invertWeakness)
            enemy.WeaknessType = enemy.WeaknessType == WeaponType.Melee
                ? WeaponType.Ranged : WeaponType.Melee;

        // 비주얼
        spriteRenderer.color = mod.tintColor;
        if (eliteParticles != null) eliteParticles.Play();

        // 특수 능력 초기화
        InitSpecialAbility(mod.specialAbility);
    }

    private void InitSpecialAbility(EliteAbility ability)
    {
        switch (ability)
        {
            case EliteAbility.PeriodicShield:
                StartCoroutine(PeriodicShieldRoutine());
                break;
            case EliteAbility.SplitOnDeath:
                enemy.OnDeath += SpawnSplitEnemies;
                break;
            case EliteAbility.TeleportBehindPlayer:
                StartCoroutine(TeleportRoutine());
                break;
        }
    }

    private IEnumerator PeriodicShieldRoutine()
    {
        while (true)
        {
            yield return new WaitForSeconds(8f);
            enemy.ActivateShield(3f); // 3초 무적
        }
    }

    private void SpawnSplitEnemies()
    {
        for (int i = 0; i < 2; i++)
        {
            var pos = transform.position + (Vector3)Random.insideUnitCircle * 0.5f;
            EnemySpawner.Instance.SpawnMini(enemy.EnemyType, pos);
        }
    }
}
```

### 3. 엘리트 스폰 결정 — 방 진입 시 확률 적용

```csharp
public class RoomEliteManager : MonoBehaviour
{
    [SerializeField] private EliteModifierSO[] availableModifiers;
    [Range(0f, 1f)]
    [SerializeField] private float eliteChance = 0.2f; // 20% 확률

    public void TryApplyEliteToSpawnedEnemies(List<EnemyBase> enemies)
    {
        // 방마다 최대 1~2마리만 엘리트로
        int eliteCount = Mathf.Min(2, Mathf.CeilToInt(enemies.Count * eliteChance));

        var shuffled = enemies.OrderBy(_ => Random.value).ToList();
        for (int i = 0; i < eliteCount; i++)
        {
            var eliteCtrl = shuffled[i].GetComponent<EnemyEliteController>();
            if (eliteCtrl == null) continue;
            var mod = availableModifiers[Random.Range(0, availableModifiers.Length)];
            eliteCtrl.ApplyEliteModifier(mod);
        }
    }
}
```

### 4. 시각적 구분 강화 — 크기 스케일 + 아우라

```csharp
// ApplyEliteModifier 내부에 추가
transform.localScale *= 1.25f; // 엘리트는 25% 크게

// 엘리트 아우라 오브젝트 활성화
eliteAuraObject.SetActive(true);
eliteAuraObject.GetComponent<SpriteRenderer>().color = 
    new Color(mod.tintColor.r, mod.tintColor.g, mod.tintColor.b, 0.4f);
```

---

## OnionCat 적용 포인트

### 핵심 아이디어: 협력 압박 엘리트 변종

| 변종 이름 | 효과 | OnionCat 협력 압박 |
|---|---|---|
| **분열형** (Split) | 사망 시 소형 2마리 분열 | Cat이 처리해야 하는 근접 분열체 vs Crop의 원거리 처리 |
| **약점역전** (Inverted) | 근접약 ↔ 원거리약 반전 | 기습적으로 역할 전환 강요 |
| **차폐형** (Shield-bearer) | 전면 방향 피해 무효 | Cat이 뒤로 돌아가거나 Crop이 반사탄 활용 필요 |
| **집착형** (Fixated) | 한 플레이어만 무조건 추적 | Cat이 유인, Crop이 처치하는 전술 발생 |
| **전파형** (Contagious) | 사망 시 인근 적에게 버프 전파 | 우선 처치 순서 결정 중요 |

### 구현 우선순위 (초보 개발자용)
1. **1단계**: HP/속도 배율 + 색상 변경만으로 엘리트 구현 (15분)
2. **2단계**: `SplitOnDeath` 추가 (이미 있는 스폰 시스템 재활용)
3. **3단계**: `invertWeakness`로 협력 전술 깊이 추가
4. **4단계**: 보호막, 순간이동 등 특수 행동 점진적 추가

### 엘리트 접두사 이름 예시 (한국어)
- 홍염의, 빙결된, 질주하는, 거대한, 폭발하는, 집요한, 분열하는, 무적의

---

## 참고 링크

- [Hades 챔피언 적 디자인 분석](https://www.gamedeveloper.com/design/how-supergiant-designs-around-player-mastery-in-hades)
- [Unity ScriptableObject 공식 문서](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
- [Binding of Isaac Champion 위키](https://bindingofisaacrebirth.fandom.com/wiki/Champion)
- [Enemy Modifiers 구현 패턴 (Unity Forum)](https://forum.unity.com/threads/enemy-modifier-system-design.html)
- [로그라이크 적 다양성 설계론 (GDC Vault)](https://www.gdcvault.com/play/1027126)
