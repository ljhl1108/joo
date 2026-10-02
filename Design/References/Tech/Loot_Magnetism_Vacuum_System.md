# Loot Magnetism & Auto-Vacuum System

리서치 날짜: 2026-10-02

## 개요

전투 중 드롭되는 아이템(골드, 경험치 구슬, HP 회복)이 플레이어 근처에서 자동으로 끌려오는 시스템.
Vampire Survivors, Brotato, Risk of Rain 2 등 많은 로그라이트에서 핵심 피드백 루프로 사용한다.

**OnionCat에서 중요한 이유**: 두 플레이어(Cat+Onion)가 한 몸이라 아이템을 직접 밟으러 가는 동선이 제한적.
자동 흡수 없으면 위험한 곳에 뛰어들어야 하는 나쁜 UX가 생긴다.

---

## Unity 구현 방법

### 기본 구조: Trigger 감지 + Lerp 이동

```csharp
// LootItem.cs
public class LootItem : MonoBehaviour
{
    [SerializeField] private float magnetRadius = 4f;
    [SerializeField] private float attractSpeed = 8f;
    [SerializeField] private float pickupRadius = 0.3f;

    private Transform target;
    private bool isAttracting;
    private Rigidbody2D rb;

    void Awake() => rb = GetComponent<Rigidbody2D>();

    void Update()
    {
        if (!isAttracting) return;

        Vector2 dir = (Vector2)target.position - rb.position;
        float dist = dir.magnitude;

        if (dist < pickupRadius)
        {
            Collect();
            return;
        }

        // 가까울수록 빨라지는 곡선 속도
        float speed = attractSpeed * Mathf.Lerp(1f, 4f, 1f - (dist / magnetRadius));
        rb.MovePosition(rb.position + dir.normalized * speed * Time.deltaTime);
    }

    // 플레이어 자석 범위 감지
    void OnTriggerEnter2D(Collider2D col)
    {
        if (!col.CompareTag("Player")) return;
        target = col.transform;
        isAttracting = true;
        rb.bodyType = RigidbodyType2D.Kinematic; // 물리 끄고 코드로만 이동
    }

    void Collect()
    {
        // 실제 효과 적용
        GameManager.Instance.AddGold(goldValue);
        PoolManager.Despawn(gameObject);
    }
}
```

### 자석 범위 Trigger 설정 (플레이어 쪽)

```csharp
// PlayerLootMagnet.cs  — Cat 오브젝트에 부착
public class PlayerLootMagnet : MonoBehaviour
{
    [SerializeField] private float baseRadius = 4f;
    private CircleCollider2D magnetTrigger;

    void Awake()
    {
        // 별도 자식 오브젝트에 IsTrigger=true 콜라이더
        magnetTrigger = GetComponent<CircleCollider2D>();
        magnetTrigger.isTrigger = true;
        magnetTrigger.radius = baseRadius;
    }

    // 업그레이드로 반지름 조절
    public void SetRadius(float radius) => magnetTrigger.radius = radius;
}
```

### 오브젝트 풀링과 연동

```csharp
// LootDropper.cs
public class LootDropper : MonoBehaviour
{
    [SerializeField] private GameObject goldPrefab;
    [SerializeField] private int goldAmount = 3;

    public void DropLoot(Vector2 position)
    {
        for (int i = 0; i < goldAmount; i++)
        {
            // PoolManager 사용 (CLAUDE.md 규칙: Instantiate 금지)
            var loot = PoolManager.Spawn(goldPrefab, position, Quaternion.identity);
            
            // 드롭 시 살짝 튕겨나가는 이펙트
            var rb = loot.GetComponent<Rigidbody2D>();
            Vector2 scatter = Random.insideUnitCircle * 2f;
            rb.bodyType = RigidbodyType2D.Dynamic;
            rb.AddForce(scatter, ForceMode2D.Impulse);
        }
    }
}
```

### 드롭 후 튕김 → 자석 전환 타이밍

```csharp
// LootItem.cs 수정: 드롭 직후 잠깐 물리 적용
IEnumerator EnableMagnetAfterDelay()
{
    yield return new WaitForSeconds(0.3f); // 튕기는 물리 연출 후
    rb.bodyType = RigidbodyType2D.Kinematic;
    canAttract = true; // 이제 자석 감지 활성화
}

void OnEnable()  // 풀에서 꺼낼 때
{
    isAttracting = false;
    canAttract = false;
    rb.bodyType = RigidbodyType2D.Dynamic;
    StartCoroutine(EnableMagnetAfterDelay());
}
```

### 레이어 설정

```
Physics2D Layer Matrix:
- Loot 레이어 (새로 추가, index 15)
- Loot ↔ Player 레이어: Trigger 감지 ON
- Loot ↔ Enemy: OFF (적이 밟아도 반응 없음)
- Loot ↔ Wall: ON (벽 통과 안 함, 드롭 물리용)
```

---

## OnionCat 적용 포인트

### 1. 자석 범위 업그레이드
`StatType.LootRadius` 추가 → `PlayerStats.Current.lootRadius`로 `PlayerLootMagnet.SetRadius()` 호출.
업그레이드 아이템 하나로 구현 완료.

### 2. 두 플레이어 중 Cat에 자석 부착
Cat이 몸을 담당하니 Cat Transform 기준으로 수집.
Onion(마우스 플레이어)이 특정 업그레이드 선택 시 추가 자석 반경 확장 효과 부여 가능.

### 3. HP 아이템은 자석 범위 절반
회복 아이템은 의도적으로 밟으러 가야 하는 긴장감 유지:
```csharp
if (lootType == LootType.Health)
    magnetRadius = baseRadius * 0.5f;
```

### 4. "진공 업그레이드" 아이템
일시적으로 화면 전체 아이템 흡수:
```csharp
// 업그레이드 효과 발동 시
FindObjectsByType<LootItem>(FindObjectsSortMode.None)
    .Where(l => !l.isAttracting)
    .ToList().ForEach(l => l.ForceMagnet(playerTransform));
```

### 5. 아이템 수집 시각 피드백
- 골드 수집: 화면 상단 골드 UI 숫자 +N 팝업 (Floating_Damage_Numbers 참고)
- HP 수집: 하트 아이콘 bounce 애니메이션
- 수집 사운드: 가볍고 밝은 SFX, 연속 수집 시 음정이 조금씩 올라가는 체인 사운드

---

## 참고 링크

- Unity Physics2D Layers: https://docs.unity3d.com/Manual/LayerBasedCollision.html
- Rigidbody2D.MovePosition: https://docs.unity3d.com/ScriptReference/Rigidbody2D.MovePosition.html
- Vampire Survivors 아이템 흡수 분석: https://www.youtube.com/watch?v=lDGmXqd3Ous (검색: "vampire survivors magnet mechanic")
- Risk of Rain 2 아이템 수집 UX: https://riskofrain2.fandom.com/wiki/Items (피드백 철학 참고)
- Brotato loot design analysis: https://store.steampowered.com/app/1942280/Brotato/ (Steam 리뷰 UX 섹션)
