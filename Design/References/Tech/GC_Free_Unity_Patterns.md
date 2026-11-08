# GC-Free Unity Patterns (가비지 컬렉션 최소화 패턴)

리서치 날짜: 2026-11-08

## 개요

Unity는 C# 힙 메모리를 **GC(Garbage Collector)**가 관리한다. GC가 실행되는 순간 수 밀리초(ms)의 프레임 멈춤이 발생하는데, 액션 로그라이크에서 이 "GC Spike"는 플레이어가 체감하는 버벅임으로 직결된다.

**OnionCat의 위험 지점**: 방 입장 시 적 대량 스폰, 투사체 연사, 데미지 숫자 생성, 세트 보너스 재계산 등 짧은 시간에 많은 객체가 생성/소멸되는 패턴이 많음.

GC 최소화는 "미리 만들어두고 재사용" 전략이다.

---

## Unity 구현 방법

### 1. 오브젝트 풀링 (가장 중요)

힙에 새 객체를 생성(`new`, `Instantiate`)하지 않고, 미리 만들어둔 오브젝트를 빌리고 반납.

```csharp
// OnionCat의 PoolManager.Spawn/Despawn이 이미 이 패턴
// 적용 대상: 투사체, 데미지 숫자, 파티클, 이펙트, 적 오브젝트 전부

// ❌ 나쁜 예 — 매번 힙 할당
var bullet = Instantiate(bulletPrefab);
Destroy(bullet, 3f);

// ✅ 좋은 예 — 풀에서 꺼내고 반납
var bullet = PoolManager.Spawn(bulletPrefab, pos, rot);
// 3초 뒤:
PoolManager.Despawn(bullet);
```

### 2. 컴포넌트 Awake 캐싱

`GetComponent`는 매 호출마다 타입 비교를 하며, Update에서 호출 시 프레임마다 작은 힙 할당이 발생할 수 있다.

```csharp
// ❌ 나쁜 예
void Update() {
    GetComponent<Rigidbody2D>().velocity = ...;
}

// ✅ 좋은 예
Rigidbody2D _rb;
void Awake() { _rb = GetComponent<Rigidbody2D>(); }
void Update() { _rb.linearVelocity = ...; }
```

### 3. 문자열 연산 피하기

`string` 연결(`+`, `$""`)은 매번 새 String 객체를 힙에 생성한다. HUD나 데미지 숫자에서 매 프레임 호출되면 GC 압박이 쌓인다.

```csharp
// ❌ Update에서 절대 금지
healthText.text = "HP: " + currentHp;

// ✅ StringBuilder 재사용 or 값이 바뀔 때만 갱신
_sb.Clear();
_sb.Append("HP: ");
_sb.Append(currentHp);
healthText.SetText(_sb);

// 또는: 숫자가 바뀔 때만 갱신
if (_prevHp != currentHp) {
    healthText.SetText("HP: {0}", currentHp); // TMP 오버로드 활용
    _prevHp = currentHp;
}
```

### 4. 델리게이트 & 이벤트 캐싱

람다(`() => {}`)와 익명 함수는 호출 시마다 힙에 델리게이트 객체를 만든다.

```csharp
// ❌ 매 호출마다 새 델리게이트 생성
GameManager.OnStateChanged += (state) => OnStateChange(state);

// ✅ 메서드 참조로 고정 (한 번만 할당)
GameManager.OnStateChanged += OnStateChange; // OnEnable
GameManager.OnStateChanged -= OnStateChange; // OnDisable
```

### 5. 컬렉션 사전 할당 & 재사용

```csharp
// ❌ 매 프레임 새 List 생성
var enemies = new List<EnemyBase>();
Physics2D.OverlapCircleNonAlloc(pos, range, _hits);

// ✅ 클래스 레벨에서 미리 할당
readonly List<EnemyBase> _nearbyEnemies = new(16);
readonly Collider2D[] _hits = new Collider2D[32];

void FindEnemies() {
    _nearbyEnemies.Clear(); // 재사용
    int count = Physics2D.OverlapCircleNonAlloc(pos, range, _hits);
    for (int i = 0; i < count; i++) { ... }
}
```

### 6. LINQ 금지 (Update / 자주 호출되는 메서드)

LINQ는 편리하지만 내부적으로 열거자(Enumerator) 힙 할당이 발생한다.

```csharp
// ❌ Update 내 LINQ — 매 프레임 할당
var alive = EnemyBase.Active.Where(e => e.IsAlive).ToList();

// ✅ 직접 루프
var active = EnemyBase.Active;
for (int i = 0; i < active.Count; i++) {
    if (active[i].IsAlive) { ... }
}
```

### 7. WaitForSeconds 캐싱

코루틴에서 `new WaitForSeconds()`를 매번 생성하면 힙 할당이 쌓인다.

```csharp
// ❌ 매 호출마다 새 WaitForSeconds
yield return new WaitForSeconds(0.1f);

// ✅ 클래스 레벨에서 한 번만 생성
static readonly WaitForSeconds Wait0_1 = new(0.1f);
// 또는 WaitForSecondsRealtime 풀 클래스 만들기
yield return Wait0_1;
```

---

## OnionCat 적용 포인트

| 위험 지점 | 적용 방법 |
|-----------|----------|
| 적 스폰/처치 | `PoolManager.Spawn/Despawn` 이미 사용 중 — **OnEnable에서 초기화**, Destroy 금지 |
| 데미지 숫자 | `PoolManager`에 FloatingDamageNumber 풀 추가 (이미 있을 가능성 높음) |
| `EnemyBase.Active` 조회 | `List<EnemyBase>` 직접 순회, LINQ 사용 금지 |
| 세트 보너스 계산 (`PassiveHost.Recalculate`) | 장비 변경 시에만 호출 — 매 프레임 호출 금지 확인 |
| `GameManager.OnStateChanged` 구독 | 람다 대신 메서드 참조, OnEnable/OnDisable로 구독/해제 |
| HUD 텍스트 (씨앗 수, HP) | 값이 바뀔 때만 갱신, TMP SetText 오버로드 활용 |
| 투사체 (씨앗 탄, 적 탄) | PoolManager — OnEnable에서 방향·속도 초기화 |

**Unity Profiler 사용법**: Window > Analysis > Profiler → "GC Alloc" 열 확인. 프레임마다 수백 B 이상이면 조사 필요.

---

## 참고 링크

- Unity 공식: https://docs.unity3d.com/Manual/UnderstandingAutomaticMemoryManagement.html
- Unity Learn GC 최적화: https://learn.unity.com/tutorial/fixing-performance-problems
- Catlike Coding 풀링 튜토리얼: https://catlikecoding.com/unity/tutorials/object-pools/
- Unity 블로그 GC 모범사례: https://blog.unity.com/engine-platform/feature-preview-incremental-garbage-collection
