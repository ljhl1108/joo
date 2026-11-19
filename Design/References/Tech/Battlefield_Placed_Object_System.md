# Battlefield Placed Object System (전장 설치 오브젝트 시스템)

리서치 날짜: 2026-11-19

## 개요

전투 중 플레이어가 필드 위에 오브젝트를 직접 배치하는 시스템.
OnionCat에서 작물(P2)의 R 키 고유기 — "매운 양파 심기(주변 적 공격 지연)"나 해바라기의 "햇빛 기둥" 같이 고양이가 걸어다니는 필드 위 고정 위치에 효과 오브젝트를 세우는 메커니즘.

로그라이크에서 자주 등장: Rogue Legacy 2의 덩굴 罠, Noita의 연금술 조합, Enter the Gungeon의 폭탄·함정,
Rotwood의 환경 위험물, HoloCure의 소환형 무기 Collab 등이 모두 같은 패턴.

---

## Unity 구현 방법

### 1. 데이터 구조 — PlacedObjectData (ScriptableObject)

```csharp
[CreateAssetMenu]
public class PlacedObjectData : ScriptableObject
{
    public GameObject prefab;
    public float cooldown;         // 재사용 대기
    public int maxActive;          // 동시 존재 최대 수 (0=무제한)
    public float radius;           // 배치 범위 (고양이 발 위치 기준)
    public bool requiresFloor;     // 바닥 위에만 배치
}
```

### 2. 배치 위치 결정 — 세 가지 전략

**A. 고양이 발 위치 즉시 배치** (OnionCat 현재 방식)
```csharp
Vector2 pos = cat.FootPosition;
Spawn(prefab, pos);
```

**B. 조준 커서 위치 배치** (마우스 커서 or 조이스틱 조준)
```csharp
Vector2 pos = onionAimPosition; // P2의 마우스 월드 좌표
```

**C. 타겟 적 위치 배치** (가장 가까운 적 발 아래)
```csharp
EnemyBase nearest = EnemyBase.Active.OrderBy(e =>
    Vector2.Distance(e.transform.position, cat.Position)).First();
Vector2 pos = nearest.FootPosition;
```

### 3. 오브젝트 풀링 연동
```csharp
public class FieldObjectSpawner : MonoBehaviour
{
    [SerializeField] PlacedObjectData data;
    private List<GameObject> _active = new();
    private float _nextReady;

    public bool TryPlace(Vector2 pos)
    {
        if (Time.time < _nextReady) return false;
        if (data.maxActive > 0 && _active.Count >= data.maxActive)
            RemoveOldest(); // 가장 오래된 것 제거

        var obj = PoolManager.Spawn(data.prefab, pos, Quaternion.identity);
        _active.Add(obj);
        _nextReady = Time.time + data.cooldown;
        return true;
    }

    private void RemoveOldest()
    {
        var oldest = _active[0];
        _active.RemoveAt(0);
        PoolManager.Despawn(oldest);
    }
}
```

### 4. 배치 오브젝트 자체 — 세 가지 행동 패턴

**A. 존재 기간 후 소멸 (매운 양파)**
```csharp
public class FieldObject_Timed : MonoBehaviour
{
    [SerializeField] float lifetime = 4f;
    private float _spawnTime;

    void OnEnable() { _spawnTime = Time.time; }

    void Update()
    {
        if (Time.time - _spawnTime >= lifetime)
            PoolManager.Despawn(gameObject);
    }
}
```

**B. 적 접촉 시 발동 후 소멸 (폭탄형)**
```csharp
public class FieldObject_Trigger : MonoBehaviour
{
    void OnTriggerEnter2D(Collider2D other)
    {
        if (!other.CompareTag("Enemy")) return;
        DoEffect(other);
        PoolManager.Despawn(gameObject);
    }
}
```

**C. 범위 지속 효과 (햇빛 기둥 — 범위 내 주기적 힐)**
```csharp
public class FieldObject_Zone : MonoBehaviour
{
    [SerializeField] float interval = 0.5f;
    [SerializeField] float healAmount = 5f;
    private float _nextTick;

    void Update()
    {
        if (Time.time < _nextTick) return;
        _nextTick = Time.time + interval;
        // 반경 내 고양이 체력 회복
        if (Vector2.Distance(transform.position, cat.Position) < radius)
            GameManager.Instance.HealPlayer(healAmount);
    }
}
```

### 5. 시각적 배치 프리뷰 (선택 사항)
배치 버튼을 누르기 전 고양이 발 아래에 반투명 미리보기 표시:
```csharp
void Update()
{
    bool inputHeld = /* R 키 Hold 감지 */;
    previewGhost.SetActive(inputHeld && cooldownReady);
    previewGhost.transform.position = cat.FootPosition;
}
```

### 6. 쿨다운 HUD 연동
배치 쿨다운은 P2 HUD의 R 키 아이콘 아래 채움 바로 표현:
```csharp
float ratio = Mathf.Clamp01((Time.time - lastPlaceTime) / data.cooldown);
cooldownBar.fillAmount = ratio;
```

---

## OnionCat 적용 포인트

### 작물별 R 고유기의 배치 오브젝트화
- **양파** — `FieldObject_Zone`: 배치 후 4초간 주변 적에게 공격 지연(Slow) 디버프 범위
- **해바라기** — `FieldObject_Zone`: 배치 후 고양이가 범위 안에 있으면 주기적 체력 회복
- **푸른 버섯** — `FieldObject_Trigger`: 적이 밟으면 독 포자 폭발

### 최대 개수 제한으로 운영 감각 추가
`maxActive = 2`로 설정하면 "양파 2개를 최적 위치에 배치하는" 운영 고민이 생김.
3개 이상 배치하려면 가장 오래된 것이 사라짐 → 자연스러운 갱신 사이클.

### 장비 효과로 배치 오브젝트 강화
장비 세트 본으로 배치 오브젝트를 강화하는 경로가 있으면 P2 플레이어가 세트 본을 직접 체감:
- "양파 세트 2": 양파 범위 +50%
- "양파 세트 3": 양파 위에서 적이 죽으면 체력 회복

### 적이 배치 오브젝트를 인식
고급 적은 배치된 오브젝트를 피해가거나 파괴하려 할 수 있음:
```csharp
// EnemyAI에서 FieldObject 감지 반경 계산
Collider2D[] hazards = Physics2D.OverlapCircleAll(pos, 2f, fieldObjectLayer);
if (hazards.Length > 0) SteerAround(hazards[0].transform.position);
```

---

## 참고 링크

- [Unity Object Pool API](https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html)
- [Unity Trigger & Collision 2D](https://docs.unity3d.com/Manual/Collision2D.html)
- [ScriptableObject-based design](https://unity.com/how-to/architect-game-code-scriptable-objects)
- Rotwood의 환경 오브젝트 배치 — 적이 필드 오브젝트를 피하거나 이용하는 AI 패턴 참고
- HoloCure의 소환형 Collab(예: BL Book, Spider Cooking) — 필드 위 고정 오브젝트가 주기적으로 공격하는 패턴
