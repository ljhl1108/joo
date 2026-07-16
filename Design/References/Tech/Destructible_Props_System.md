# Destructible Props System (파괴 가능한 환경 오브젝트 시스템)

리서치 날짜: 2026-07-16

## 개요

로그라이크 게임 방 안에 배치되는 파괴 가능한 소품(배럴, 상자, 항아리, 묘비 등)의 구현 방법.
- 공격 시 시각적 파괴 연출 + 아이템 드롭
- 방 구석 배치로 탐색 유도 / 적 뒤 숨기 전략 유도
- 진행 피드백: 방이 "살아있는 공간"처럼 느껴짐
- OnionCat에서는 Cat 슬래시와 Onion 투사체 모두로 파괴 가능하게 설계

---

## Unity 구현 방법

### 구조 설계 (컴포넌트 구성)

```
DestructibleProp (GameObject)
├── SpriteRenderer          ← 현재 상태 스프라이트 표시
├── Collider2D (Box/Polygon) ← 공격 감지용 Trigger
├── PropBreaker.cs          ← 파괴 로직 컴포넌트
└── (Optional) Rigidbody2D  ← 타격 시 물리 반응 원할 경우
```

### 핵심 스크립트

```csharp
public class PropBreaker : MonoBehaviour
{
    [SerializeField] private int maxHP = 1;
    [SerializeField] private GameObject breakEffect;  // 파티클 프리팹
    [SerializeField] private GameObject[] possibleDrops;  // 드롭 아이템 목록
    [SerializeField] private float dropChance = 0.4f;
    [SerializeField] private Sprite[] damageSprites;  // HP 단계별 스프라이트

    private int currentHP;
    private SpriteRenderer spriteRenderer;

    private void Awake()
    {
        currentHP = maxHP;
        spriteRenderer = GetComponent<SpriteRenderer>();
    }

    public void TakeDamage(int amount)
    {
        currentHP -= amount;
        UpdateSprite();
        if (currentHP <= 0) Break();
    }

    private void UpdateSprite()
    {
        if (damageSprites == null || damageSprites.Length == 0) return;
        int index = Mathf.Clamp(
            maxHP - currentHP,
            0,
            damageSprites.Length - 1
        );
        spriteRenderer.sprite = damageSprites[index];
    }

    private void Break()
    {
        if (breakEffect != null)
            Instantiate(breakEffect, transform.position, Quaternion.identity);

        TryDropItem();
        gameObject.SetActive(false);  // 또는 Destroy(gameObject)
    }

    private void TryDropItem()
    {
        if (possibleDrops.Length == 0) return;
        if (Random.value <= dropChance)
        {
            int idx = Random.Range(0, possibleDrops.Length);
            Instantiate(possibleDrops[idx], transform.position, Quaternion.identity);
        }
    }
}
```

### 공격 감지 방식 2가지

#### 방법 A: Trigger 방식 (권장 — 가볍고 간단)
```csharp
// PropBreaker.cs에 추가
private void OnTriggerEnter2D(Collider2D other)
{
    if (other.CompareTag("PlayerAttack"))
    {
        // 공격 오브젝트에서 데미지 가져오기
        if (other.TryGetComponent<DamageSource>(out var dmg))
            TakeDamage(dmg.damage);
        else
            TakeDamage(1);
    }
}
```

#### 방법 B: 공격 오브젝트가 직접 호출 (더 명시적)
```csharp
// 슬래시/투사체 스크립트에서
private void OnTriggerEnter2D(Collider2D other)
{
    if (other.TryGetComponent<PropBreaker>(out var prop))
        prop.TakeDamage(damage);
}
```

### 스프라이트 파괴 애니메이션 (Animator 없이)

```csharp
// 파괴 시 간단한 스케일 펑 연출
private IEnumerator BreakAnimation()
{
    Vector3 original = transform.localScale;
    transform.localScale = original * 1.3f;
    yield return new WaitForSeconds(0.05f);
    transform.localScale = original;
    yield return new WaitForSeconds(0.05f);
    // 여기서 실제 파괴
    Break();
}
```

### 풀링 연동 (Pool Manager 사용 시)

```csharp
private void Break()
{
    if (breakEffect != null)
        ObjectPool.Instance.Spawn(breakEffect, transform.position);  // 파티클도 풀링

    TryDropItem();
    ObjectPool.Instance.Return(gameObject);  // Destroy 대신 풀에 반납
}
```

### 파괴 파티클 설정 요령 (Particle System)

- **Shape**: Box 또는 Sphere, 반경 = 소품 크기
- **Start Lifetime**: 0.3 ~ 0.6초
- **Start Speed**: 2 ~ 5 (랜덤 범위)
- **Gravity Modifier**: 1.5 (아래로 떨어지게)
- **Color over Lifetime**: 투명도 점점 감소
- **Renderer → Sorting Layer**: 소품 레이어와 동일 또는 위

---

## 레이어 & 태그 설정

| 항목 | 권장값 |
|------|--------|
| Prop 레이어 | `Environment` 또는 `Props` |
| 플레이어 공격 레이어 | `PlayerAttack` |
| Physics Matrix | Props ↔ PlayerAttack = Trigger Only |
| 적 공격과 Props | 설계에 따라 선택 (적도 파괴 가능 여부) |

**Physics Matrix 설정 (Edit → Project Settings → Physics 2D)**:
- `Environment` ↔ `PlayerAttack`: 체크 (충돌 감지)
- `Environment` ↔ `EnemyAttack`: 게임 디자인에 따라 설정

---

## ScriptableObject로 Prop 데이터 관리

```csharp
[CreateAssetMenu(menuName = "OnionCat/PropData")]
public class PropData : ScriptableObject
{
    public string propName;
    public int maxHP;
    public Sprite[] damageSprites;
    public GameObject breakEffectPrefab;
    public GameObject[] possibleDrops;
    [Range(0f, 1f)] public float dropChance;
}
```

```csharp
// PropBreaker에서 데이터 참조
[SerializeField] private PropData data;
private void Awake() { currentHP = data.maxHP; }
```

---

## 파괴 불가 장애물과의 구분

| 타입 | 설명 | 구현 |
|------|------|------|
| 완전 파괴 | 공격으로 제거됨 | PropBreaker.cs |
| 데미지 상태 | 시각적 손상, 파괴 안됨 | 스프라이트 교체만 |
| 파괴 불가 | 총알 막기용 엄폐물 | 일반 Collider, 스크립트 없음 |
| 폭발 반응 | 폭발에만 파괴 | `damageType` 필터 추가 |

---

## OnionCat 적용 포인트

### 1. Cat 슬래시 vs Onion 투사체 모두 파괴 가능
- `DamageSource` 컴포넌트에 `attackerType` (Melee/Ranged) 포함
- 특정 소품은 근접 전용 파괴, 다른 소품은 원거리 전용 → 협력 필요성 강화

```csharp
public enum AttackType { Melee, Ranged, Any }

public class DamageSource : MonoBehaviour
{
    public int damage = 1;
    public AttackType type = AttackType.Any;
}
```

```csharp
// PropBreaker에 추가
[SerializeField] private AttackType vulnerableTo = AttackType.Any;

private void OnTriggerEnter2D(Collider2D other)
{
    if (!other.TryGetComponent<DamageSource>(out var dmg)) return;
    if (vulnerableTo != AttackType.Any && dmg.type != vulnerableTo) return;
    TakeDamage(dmg.damage);
}
```

### 2. 방 생성 시 Prop 자동 배치
```csharp
// RoomGenerator에서 Props 스폰
private void SpawnProps(RoomData room)
{
    foreach (var spawnPoint in room.propSpawnPoints)
    {
        if (Random.value < propSpawnChance)
        {
            PropData data = propPool[Random.Range(0, propPool.Length)];
            var prop = Instantiate(propPrefab, spawnPoint.position, Quaternion.identity);
            prop.GetComponent<PropBreaker>().Initialize(data);
        }
    }
}
```

### 3. 소품 파괴 시 전략적 가치 부여
- **배럴(근접 전용 파괴)**: 내부에서 적 스폰 → Cat이 먼저 처리해야 함
- **항아리(원거리 전용)**: 상처받은 NPC가 숨어있음 → Onion이 구출
- **상자(모두 파괴 가능)**: 업그레이드 아이템 드롭 → 보상형 소품

### 4. 파괴 소품 체인 리액션
- 폭발 배럴: 파괴 시 주변 PropBreaker에도 데미지
- 향후 폭발 시스템과 연동 가능

---

## 참고 링크

- [Unity 공식: Collider2D Trigger](https://docs.unity3d.com/Manual/CollidersOverview.html)
- [Unity 공식: Particle System](https://docs.unity3d.com/Manual/ParticleSystems.html)
- [Unity 공식: ScriptableObject](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
- [Brackeys: Object Pooling Tutorial](https://www.youtube.com/watch?v=tdSmKaJvCoA)
- [Game Dev Guide: Destructible Objects in 2D](https://www.youtube.com/c/GameDevGuide)
