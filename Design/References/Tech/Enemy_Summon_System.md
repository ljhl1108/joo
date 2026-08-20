# Enemy Summon System (적 소환 패턴 시스템)

리서치 날짜: 2026-08-20

## 개요

보스 또는 특수 일반 적이 **전투 중 하위 적을 소환**하는 시스템. 로그라이크에서 전투 복잡도를 높이고 "처치 우선순위 판단"을 플레이어에게 요구하는 핵심 메카닉. Enter the Gungeon의 보스(Bullet Kin 소환), Hades의 Exalted적, Binding of Isaac의 소환 보스 등에서 보편적으로 사용됨.

OnionCat에서는 **소환된 적의 취약점(근접 전용 vs 원거리 전용)을 섞어서** Cat과 Onion이 각자의 역할을 동시에 수행해야 하는 극한의 협력 상황을 만들 수 있음.

---

## Unity 구현 방법

### 1. 기본 구조 — 소환자(Summoner) 컴포넌트

```csharp
public class EnemySummoner : MonoBehaviour
{
    [SerializeField] private GameObject[] summonPrefabs;  // 소환할 적 프리팹 배열
    [SerializeField] private Transform[] spawnPoints;     // 소환 위치들
    [SerializeField] private float summonInterval = 5f;   // 소환 주기 (초)
    [SerializeField] private int maxActiveMinions = 4;    // 동시 최대 하수인 수

    private List<GameObject> _activeMinions = new();
    private float _timer;

    private void Update()
    {
        _timer += Time.deltaTime;
        if (_timer >= summonInterval && _activeMinions.Count < maxActiveMinions)
        {
            _timer = 0f;
            SummonMinion();
        }
    }

    private void SummonMinion()
    {
        // 죽은 하수인 정리
        _activeMinions.RemoveAll(m => m == null);

        if (_activeMinions.Count >= maxActiveMinions) return;

        Transform spawnPoint = spawnPoints[Random.Range(0, spawnPoints.Length)];
        GameObject prefab = summonPrefabs[Random.Range(0, summonPrefabs.Length)];

        GameObject minion = Instantiate(prefab, spawnPoint.position, Quaternion.identity);
        _activeMinions.Add(minion);

        // 소환 이펙트 (VFX 연출)
        StartCoroutine(SummonAnimation(minion, spawnPoint.position));
    }

    private IEnumerator SummonAnimation(GameObject minion, Vector3 pos)
    {
        // 소환 중 잠시 비활성화 → 이펙트 재생 → 활성화
        minion.SetActive(false);
        // TODO: 소환 파티클 재생 (SummonVFX prefab)
        yield return new WaitForSeconds(0.5f);
        minion.SetActive(true);
    }
}
```

### 2. HP 연동 소환 (체력 트리거 소환)

```csharp
public class BossWithSummon : MonoBehaviour
{
    [SerializeField] private EnemySummoner summoner;
    [SerializeField] private HealthSystem healthSystem;
    [SerializeField] private float[] summonThresholds = { 0.75f, 0.5f, 0.25f }; // HP 비율

    private HashSet<float> _triggeredThresholds = new();

    private void Start()
    {
        healthSystem.OnHpChanged += CheckSummonTrigger;
    }

    private void CheckSummonTrigger(float currentHp, float maxHp)
    {
        float ratio = currentHp / maxHp;
        foreach (float threshold in summonThresholds)
        {
            if (ratio <= threshold && !_triggeredThresholds.Contains(threshold))
            {
                _triggeredThresholds.Add(threshold);
                summoner.ForceSummon(); // 즉각 소환
                PlaySummonAnnounce();   // 연출 (화면 흔들림, 경고음)
            }
        }
    }
}
```

### 3. 오브젝트 풀링으로 최적화

소환이 잦으면 Instantiate/Destroy 비용이 커짐 → `Unity_Object_Pool_API.md` 참고.

```csharp
// ObjectPool 활용 버전
private void SummonMinion()
{
    _activeMinions.RemoveAll(m => m == null);
    if (_activeMinions.Count >= maxActiveMinions) return;

    Transform spawnPoint = spawnPoints[Random.Range(0, spawnPoints.Length)];
    
    // ObjectPool에서 꺼내기
    GameObject minion = EnemyPool.Instance.Get(summonPrefabKey);
    minion.transform.position = spawnPoint.position;
    minion.SetActive(true);
    _activeMinions.Add(minion);
}

// 하수인이 죽을 때 → 풀로 반환
public void OnMinionDeath(GameObject minion)
{
    _activeMinions.Remove(minion);
    EnemyPool.Instance.Release(summonPrefabKey, minion);
}
```

### 4. 소환 예고 (Telegraph)

소환 직전 경고 이펙트 → 플레이어가 반응할 시간 부여 (Enemy_Telegraph_System.md 참고).

```csharp
private IEnumerator SummonWithTelegraph(Transform spawnPoint)
{
    // 1. 경고 마크 생성 (빨간 원/별 등)
    GameObject warning = Instantiate(warningPrefab, spawnPoint.position, Quaternion.identity);
    
    yield return new WaitForSeconds(1.0f); // 1초 예고
    
    Destroy(warning);
    
    // 2. 실제 소환
    SummonMinion();
}
```

---

## OnionCat 적용 포인트

### 협력 강요 소환 설계

소환 패턴을 **Cat(근접)과 Onion(원거리)의 역할을 동시에 요구**하도록 설계:

| 소환 시나리오 | Cat 역할 | Onion 역할 |
|-------------|---------|----------|
| 보스 소환: 갑옷 병사 (근접 전용 취약) | 슬래시로 처치 | 보스에게 지속 딜 |
| 보스 소환: 원거리 전용 저격수 | 보스 견제/막기 | 저격수 처치 |
| 보스 소환: 폭탄 병사 (빠른 처치 필요) | 빠르게 돌진 슬래시 | Onion 쉴드로 보호 |
| 보스 소환: 쉴드 병사 (뒤에서만 처치) | 정면 어그로 유인 | 뒤에서 씨앗 발사 |

### 소환 한도 = 협력 압박 강도 조절 노브
- `maxActiveMinions = 4`: 난이도 보통
- 난이도 높은 층에서 소환 속도를 줄이거나 한도를 높이면 즉각 난이도 상승.
- `summonInterval`을 `GameDifficulty.current`에 따라 동적 조정 가능.

### OnionCat 전용 소환 보스 아이디어
- **양파밭 마녀 (Onion Field Witch)**: 매 체력 25%마다 소환. 50%에서 근접 전용, 25%에서 원거리 전용 소환 → 두 플레이어 모두 동시에 바빠짐.
- **고양이 사냥꾼 (Cat Hunter)**: Cat을 집중 추적하는 하수인을 소환 → Onion이 하수인을 처치해야 Cat이 자유롭게 보스 공격 가능.

### 구현 순서 (초보 개발자용)
1. `EnemySummoner.cs` 작성, 씬에 빈 GameObject에 컴포넌트 추가
2. `spawnPoints` 배열에 Spawn Point 빈 오브젝트 드래그 앤 드롭
3. `summonPrefabs` 배열에 소환할 적 프리팹 드래그 앤 드롭
4. `summonInterval` = 5f로 시작, 테스트 후 조정
5. 보스 GameObject에 `BossWithSummon.cs` 추가, `HealthSystem` 참조 연결

> **유니티 에디터에서 드래그 앤 드롭 설정 필요**: `spawnPoints`, `summonPrefabs`, `healthSystem`, `summoner` 참조 모두 Inspector에서 연결 필요.

---

## 참고 링크

- Unity 공식 — ObjectPool: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- Unity 공식 — UnityEvents: https://docs.unity3d.com/Manual/UnityEvents.html
- Game Maker's Toolkit — "Why Boss Fights Work": https://www.youtube.com/watch?v=fw7R0UQJkjQ
- Enemy Spawner 참고: `Design/References/Tech/Enemy_Spawner_Wave_System.md`
- Object Pooling 참고: `Design/References/Tech/Object_Pooling_System.md`
- Enemy AI 참고: `Design/References/Tech/Enemy_AI_StateMachine.md`
