# 적/방 난이도 스케일링 시스템 (Floor Difficulty Scaling)

리서치 날짜: 2026-09-28

## 개요

로그라이크에서 플레이어가 깊이(층/방 번호)를 진행할수록 적이 강해지는 공식 설계.
고정 수치 대신 **커브**와 **배율**로 관리하면 밸런싱이 훨씬 쉬워진다.

OnionCat은 방 단위로 층이 올라가는 구조이므로, 방 번호(roomIndex)를 스케일링 입력으로 사용한다.

---

## Unity 구현 방법

### 1. ScriptableObject로 커브 정의

```csharp
// DifficultyConfig.asset
[CreateAssetMenu(menuName = "OnionCat/DifficultyConfig")]
public class DifficultyConfig : ScriptableObject
{
    [Header("Enemy Stat Multipliers per Room")]
    public AnimationCurve hpCurve;      // x=roomIndex, y=배율(1.0 = 기본)
    public AnimationCurve damageCurve;
    public AnimationCurve speedCurve;

    [Header("Encounter Budget")]
    public AnimationCurve encounterBudgetCurve; // 방 1개에 스폰 가능한 포인트 합계

    public float GetHpMultiplier(int roomIndex)    => hpCurve.Evaluate(roomIndex);
    public float GetDamageMultiplier(int roomIndex) => damageCurve.Evaluate(roomIndex);
    public float GetSpeedMultiplier(int roomIndex)  => speedCurve.Evaluate(roomIndex);
    public int   GetBudget(int roomIndex)           => (int)encounterBudgetCurve.Evaluate(roomIndex);
}
```

- Inspector에서 곡선을 직접 그릴 수 있어 수치 튜닝이 직관적
- 선형/지수/계단형 등 다양한 모양 지원

### 2. EnemyStats에 배율 적용

```csharp
public class EnemyStats : MonoBehaviour
{
    [SerializeField] private float baseHp     = 30f;
    [SerializeField] private float baseDamage = 8f;
    [SerializeField] private float baseSpeed  = 2f;

    public float MaxHp     { get; private set; }
    public float Damage    { get; private set; }
    public float MoveSpeed { get; private set; }

    public void Initialize(int roomIndex, DifficultyConfig cfg)
    {
        MaxHp     = baseHp     * cfg.GetHpMultiplier(roomIndex);
        Damage    = baseDamage * cfg.GetDamageMultiplier(roomIndex);
        MoveSpeed = baseSpeed  * cfg.GetSpeedMultiplier(roomIndex);
    }
}
```

### 3. 룸 스폰 매니저에서 적용

```csharp
public class RoomSpawner : MonoBehaviour
{
    [SerializeField] private DifficultyConfig diffConfig;
    [SerializeField] private EnemySpawnEntry[] spawnTable; // 적 종류 + 비용

    public void SpawnEnemies(int roomIndex)
    {
        int budget = diffConfig.GetBudget(roomIndex);
        while (budget > 0)
        {
            var entry = PickAffordable(budget);
            if (entry == null) break;

            var enemy = PoolManager.Spawn(entry.prefab, RandomPosition());
            enemy.GetComponent<EnemyStats>().Initialize(roomIndex, diffConfig);
            budget -= entry.cost;
        }
    }
}
```

### 4. 커브 설계 가이드라인

| 구간 | 권장 배율 | 설명 |
|------|-----------|------|
| 방 1–5 | HP 1.0–1.3, 데미지 1.0 | 입문. 플레이어가 시스템 파악 |
| 방 6–10 | HP 1.3–2.0, 데미지 1.2 | 중반. 협력 필요성 증가 |
| 방 11+ | HP 2.0–3.5, 데미지 1.5–2.0 | 후반. 업그레이드 없으면 벅차게 |

- 속도 배율은 0.8–1.3 사이로 제한 (너무 빠르면 불쾌)
- 보스방은 별도 보너스 배율 (×1.5 등)

### 5. 런 진행도와 분리 (GameManager 연동)

```csharp
// GameManager.Run.RoomIndex 를 스케일링 입력으로 사용
int currentRoom = GameManager.Instance.Run.RoomIndex;
enemy.GetComponent<EnemyStats>().Initialize(currentRoom, diffConfig);
```

---

## OnionCat 적용 포인트

### 방 번호 소스

- `GameManager.Instance.Run.RoomIndex` 사용 (기존 RunData 구조 활용)
- 보스방 진입 시 `isBossRoom` 플래그로 추가 배율 적용

### 원거리 전용·근거리 전용 적 조합

- Encounter Budget으로 "근거리 전용 적 2마리 + 원거리 전용 적 1마리" 같은 조합 제어
- 비용 테이블: 근거리 1마리=1, 원거리 1마리=2, 엘리트=4 → 예산 4이면 [1+1+2] 또는 [4] 조합

### 초반 집중 튜닝

- 1–3번 방은 배율을 1.0 고정 → 조작 익히는 시간 보장
- 4번 방부터 슬금슬금 올리기 (일반 플레이어 체감 시작점)

### 밸런싱 워크플로우

1. `DifficultyConfig.asset` 하나만 수정 → 전체 게임 난이도 변경
2. Inspector 커브 조작 → 플레이 → 커브 재조정 (20분 이내 반복 가능)
3. 나중에 "이지/노말/하드" 모드 추가 시 `DifficultyConfig` 에셋을 3개 만들어 런 시작 시 선택

---

## 참고 링크

- [Unity AnimationCurve 공식 문서](https://docs.unity3d.com/ScriptReference/AnimationCurve.html)
- [Game Balance Concepts - Dan Cook](https://lostgarden.home.blog/2011/07/21/the-core-mechanics-of-games/)
- [Roguelike Design Patterns: Scaling Difficulty](https://www.gamedeveloper.com/design/roguelike-scaling-difficulty)
- [Hades Encounter Design GDC Talk](https://www.youtube.com/watch?v=bTd4IfATfJY)
