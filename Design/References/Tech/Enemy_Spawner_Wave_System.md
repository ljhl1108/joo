# 적 스포너 & 웨이브 시스템 (Enemy Spawner & Wave System)

리서치 날짜: 2026-06-22

## 개요

적 스포너/웨이브 시스템은 로그라이크 게임에서 **방 진입 시 적을 소환하고, 전멸 시 방을 클리어 처리하는** 핵심 인프라다. OnionCat에서는 각 방마다 적 그룹을 정의하고 방 클리어 조건(모든 적 사망)을 감지해야 하며, 이 시스템이 방 잠금/잠금 해제 + 문 개방과도 연결된다.

---

## Unity 구현 방법

### 아키텍처 개요

```
RoomController
  └─ EnemySpawner (Component)
       ├─ SpawnPoint[] (빈 GameObject 위치)
       ├─ WaveData[] (ScriptableObject 배열)
       └─ 현재 살아있는 적 카운팅 → 0되면 방 클리어 이벤트
```

### Step 1 — WaveData ScriptableObject 정의

```csharp
[CreateAssetMenu(menuName = "OnionCat/WaveData")]
public class WaveData : ScriptableObject
{
    [System.Serializable]
    public struct EnemySpawnEntry
    {
        public GameObject prefab;
        public int count;
    }

    public EnemySpawnEntry[] entries;
    public float delayBetweenSpawns = 0.3f;
}
```

> 에디터에서 드래그 앤 드롭으로 방마다 다른 WaveData 할당 가능

### Step 2 — EnemySpawner 핵심 코드

```csharp
public class EnemySpawner : MonoBehaviour
{
    [SerializeField] private WaveData[] waves;
    [SerializeField] private Transform[] spawnPoints;

    private int _aliveCount;
    public event System.Action OnRoomCleared;

    public void StartSpawning()
    {
        StartCoroutine(SpawnAllWaves());
    }

    private IEnumerator SpawnAllWaves()
    {
        foreach (var wave in waves)
        {
            yield return StartCoroutine(SpawnWave(wave));
            // 웨이브 간 딜레이 (선택적)
            yield return new WaitForSeconds(1f);
        }
    }

    private IEnumerator SpawnWave(WaveData wave)
    {
        foreach (var entry in wave.entries)
        {
            for (int i = 0; i < entry.count; i++)
            {
                var point = spawnPoints[Random.Range(0, spawnPoints.Length)];
                var enemy = Instantiate(entry.prefab, point.position, Quaternion.identity);
                enemy.GetComponent<EnemyHealth>().OnDeath += HandleEnemyDeath;
                _aliveCount++;
                yield return new WaitForSeconds(wave.delayBetweenSpawns);
            }
        }
    }

    private void HandleEnemyDeath()
    {
        _aliveCount--;
        if (_aliveCount <= 0)
            OnRoomCleared?.Invoke();
    }
}
```

### Step 3 — RoomController 연결

```csharp
public class RoomController : MonoBehaviour
{
    [SerializeField] private EnemySpawner spawner;
    [SerializeField] private DoorController[] doors;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player") && !_activated)
        {
            _activated = true;
            LockDoors();
            spawner.StartSpawning();
            spawner.OnRoomCleared += UnlockDoors;
        }
    }

    private void LockDoors() { foreach (var d in doors) d.SetLocked(true); }
    private void UnlockDoors() { foreach (var d in doors) d.SetLocked(false); }
}
```

### Step 4 — 오브젝트 풀링 적용 (성능 최적화)

적이 많아지면 `Instantiate/Destroy` 대신 Pool 사용:

```csharp
// Unity 내장 오브젝트 풀 (Unity 2021+)
using UnityEngine.Pool;

public class EnemyPool : MonoBehaviour
{
    [SerializeField] private GameObject enemyPrefab;
    private ObjectPool<GameObject> _pool;

    private void Awake()
    {
        _pool = new ObjectPool<GameObject>(
            createFunc: () => Instantiate(enemyPrefab),
            actionOnGet: obj => obj.SetActive(true),
            actionOnRelease: obj => obj.SetActive(false),
            actionOnDestroy: obj => Destroy(obj),
            defaultCapacity: 10
        );
    }

    public GameObject Get(Vector3 position)
    {
        var obj = _pool.Get();
        obj.transform.position = position;
        return obj;
    }

    public void Release(GameObject obj) => _pool.Release(obj);
}
```

### Step 5 — 방 클리어 감지 패턴

**이벤트 기반** (권장): 각 적이 사망 시 `OnDeath` 이벤트 → 스포너가 카운트 관리

**Poll 방식** (간단하지만 비효율): `InvokeRepeating`으로 주기적으로 적 수 체크  
→ 이벤트 방식이 명확하고 성능 좋음

---

## OnionCat 적용 포인트

### 방별 웨이브 설계

- **일반 방**: WaveData 1개 (적 3~5마리, 단발 소환)
- **엘리트 방**: WaveData 2개 (1파: 잡몹, 2파: 강화 적)
- **보스 방**: EnemySpawner 대신 BossController 직접 제어

### 근접 전용 / 원거리 전용 적 조합

```
WaveData 설계 예시:
- 방 A: MeleeOnlyEnemy × 3  → Crop(원거리) 무효 → Cat 필수
- 방 B: RangedOnlyEnemy × 3 → Cat(근접) 닿기 전 죽음 → Crop 필수
- 방 C: Mixed × 4           → 두 플레이어 역할 분담
```

WaveData ScriptableObject를 Room 프리팹에 어사인하면 에디터에서 방 난이도 조정 용이.

### 스폰 위치 설계

- SpawnPoint를 방 4구석 + 중앙에 배치 (5개)
- 스포너가 랜덤 선택 → 플레이어 위치와 최소 거리 체크 권장

```csharp
private Transform GetSafeSpawnPoint(Vector3 playerPos)
{
    return spawnPoints
        .OrderByDescending(p => Vector3.Distance(p.position, playerPos))
        .First();
}
```

---

## 참고 링크

- Unity ObjectPool 공식 문서: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- Unity 2D Game Kit Enemy Spawner: https://unity3d.com/learn/tutorials/projects/2d-game-kit/enemy-spawner
- Medium 웨이브 시스템 튜토리얼: https://medium.com/@austinjy13/creating-a-wave-system-for-enemy-spawning-in-unity-6a2fca61dbd0
- Level Up Coding 구현 가이드: https://levelup.gitconnected.com/how-to-create-an-enemy-wave-system-in-unity-49c5328564e7
