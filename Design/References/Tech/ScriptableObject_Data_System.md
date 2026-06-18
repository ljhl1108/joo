# ScriptableObject 기반 데이터 시스템

리서치 날짜: 2026-06-18

## 개요

ScriptableObject는 Unity에서 씬/게임오브젝트에 종속되지 않고 독립적으로 존재하는 데이터 에셋이다. 로그라이크 게임에서 수십~수백 개의 적, 아이템, 업그레이드, 방 설정을 코드 수정 없이 에디터에서 관리할 수 있게 해주는 핵심 패턴이다. OnionCat처럼 적 타입, 업그레이드 카드, 투사체 종류가 다양해질 때 ScriptableObject 없이는 코드가 폭발한다.

---

## Unity 구현 방법

### 1. 기본 ScriptableObject 정의

```csharp
[CreateAssetMenu(fileName = "NewEnemyData", menuName = "OnionCat/Enemy Data")]
public class EnemyData : ScriptableObject
{
    [Header("기본 정보")]
    public string enemyName;
    public Sprite sprite;
    public GameObject prefab;

    [Header("스탯")]
    public float maxHealth = 10f;
    public float moveSpeed = 3f;
    public float damage = 2f;
    public float attackRange = 1.5f;
    public float attackCooldown = 1.5f;

    [Header("약점 설정")]
    public bool weakToMelee = false;   // 캣 공격만 피해
    public bool weakToRanged = false;  // 어니언 공격만 피해

    [Header("드롭")]
    [Range(0f, 1f)] public float dropChance = 0.3f;
    public UpgradeCardData[] possibleDrops;
}
```

에디터 메뉴: `우클릭 → Create → OnionCat → Enemy Data` 로 새 에셋 생성.

### 2. 업그레이드 카드 데이터

```csharp
[CreateAssetMenu(fileName = "NewUpgradeCard", menuName = "OnionCat/Upgrade Card")]
public class UpgradeCardData : ScriptableObject
{
    public string cardName;
    [TextArea] public string description;
    public Sprite icon;
    public CardTarget target;   // Cat, Onion, Shared

    // 효과는 enum + float 조합으로 범용화
    public UpgradeEffectType effectType;
    public float effectValue;
}

public enum CardTarget { Cat, Onion, Shared }
public enum UpgradeEffectType
{
    DamageMultiplier, SpeedMultiplier, MaxHealthBonus,
    DashCooldownReduction, ProjectileCount, ShieldDuration
}
```

### 3. 런타임에서 ScriptableObject 사용

```csharp
public class EnemyController : MonoBehaviour
{
    [SerializeField] private EnemyData data;

    private float currentHealth;

    private void Awake()
    {
        currentHealth = data.maxHealth;
    }

    public void TakeDamage(float amount, DamageType type)
    {
        // 약점 체크
        if (data.weakToMelee && type != DamageType.Melee) return;
        if (data.weakToRanged && type != DamageType.Ranged) return;

        currentHealth -= amount;
        if (currentHealth <= 0) Die();
    }
}
```

**주의**: ScriptableObject는 공유 에셋이므로 런타임에서 `data.currentHealth` 같은 형태로 직접 수정하면 모든 인스턴스에 영향을 미침 → 항상 로컬 변수에 복사해서 사용.

### 4. 업그레이드 선택 화면에서 ScriptableObject 활용

```csharp
public class UpgradeManager : MonoBehaviour
{
    [SerializeField] private UpgradeCardData[] allCards;  // 모든 카드 풀

    public UpgradeCardData[] GetRandomUpgradeChoices(int count = 3)
    {
        // 섞어서 앞에서 count개 반환
        var shuffled = allCards.OrderBy(_ => Random.value).ToArray();
        return shuffled.Take(count).ToArray();
    }

    public void ApplyUpgrade(UpgradeCardData card, PlayerStats stats)
    {
        switch (card.effectType)
        {
            case UpgradeEffectType.DamageMultiplier:
                stats.damageMultiplier *= card.effectValue;
                break;
            case UpgradeEffectType.SpeedMultiplier:
                stats.moveSpeed *= card.effectValue;
                break;
            // ...
        }
    }
}
```

### 5. 방 배치를 위한 ScriptableObject

```csharp
[CreateAssetMenu(fileName = "NewRoomConfig", menuName = "OnionCat/Room Config")]
public class RoomConfig : ScriptableObject
{
    public RoomType roomType;  // Normal, Elite, Boss, Shop, Rest
    public EnemyData[] possibleEnemies;
    public int minEnemyCount = 2;
    public int maxEnemyCount = 5;
    [Range(0f, 1f)] public float eliteChance = 0.1f;
}
```

### 6. Database 패턴 (전체 게임 데이터 관리자)

```csharp
[CreateAssetMenu(fileName = "GameDatabase", menuName = "OnionCat/Game Database")]
public class GameDatabase : ScriptableObject
{
    public EnemyData[] allEnemies;
    public UpgradeCardData[] allUpgradeCards;
    public RoomConfig[] allRoomConfigs;

    public EnemyData GetEnemy(string name)
        => System.Array.Find(allEnemies, e => e.enemyName == name);
}
```

싱글톤 매니저가 이 하나의 에셋을 참조하면 게임 전체 데이터에 단일 진입점 확보.

---

## OnionCat 적용 포인트

### 필수 ScriptableObject 목록
| 이름 | 설명 | 유니티 에디터에서 |
|------|------|-----------------|
| `EnemyData` | 적 스탯 + 약점 설정 | 적마다 에셋 1개 생성 |
| `UpgradeCardData` | 업그레이드 카드 효과 | 카드마다 에셋 1개 |
| `ProjectileData` | 투사체 속도·범위·시각 | 투사체 종류마다 |
| `RoomConfig` | 방 적 구성·조건 | 방 타입마다 |
| `GameDatabase` | 전체 에셋 참조 목록 | 프로젝트당 1개 |

### 핵심 설계 원칙
- **약점 시스템**: `EnemyData.weakToMelee / weakToRanged` 플래그로 협동 강요 구현
- **카드 풀 관리**: `UpgradeCardData[]` 배열을 `GameDatabase`에서 중앙 관리
- **코드 수정 없는 밸런싱**: 디자이너(또는 개발자 본인)가 에디터에서 수치만 조정
- **런타임 수정 금지**: ScriptableObject 필드는 Awake/Start에서 지역변수로 복사 후 사용

---

## 참고 링크

- Unity 공식 ScriptableObject 문서: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unite Austin 2017 - ScriptableObject 활용: https://www.youtube.com/watch?v=raQ3iHhE_Kk
- Ryan Hipple - Game Architecture with ScriptableObjects: https://www.youtube.com/watch?v=raQ3iHhE_Kk
- Unity Learn - ScriptableObject 튜토리얼: https://learn.unity.com/tutorial/introduction-to-scriptable-objects
