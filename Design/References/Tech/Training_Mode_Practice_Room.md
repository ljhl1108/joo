# Training Mode / Practice Room (트레이닝 모드 — 연습 방)

리서치 날짜: 2026-10-12

## 개요

플레이어가 **런 압박 없이 조작·빌드·적 패턴을 연습**할 수 있는 별도 게임 모드. 격투 게임 트레이닝 룸, Hades의 "무기 시험 방", Dead Cells의 "동작 연습 방"에서 사용된 패턴.

OnionCat에서 특히 필요한 이유:
1. 2인 조작 특성상 첫 플레이 진입 장벽이 높음 — 고양이+양파 동시 조작을 런 전에 익힐 기회 필요
2. 새 장비·마법서 효과를 직접 써본 뒤 빌드를 결정하고 싶은 플레이어 니즈
3. QA/개발 도중 보스 패턴·히트박스 확인 시간 단축

---

## Unity 구현 방법

### 1. 씬 구조

```
Scene: Training_Room
├── Room (벽·바닥 타일 — 기존 RoomLayout 재사용, 단일 방)
├── SpawnZone (적 소환 위치 마커 배열)
├── DummyTarget (체력 999999, 피격 수치 표시 전용)
├── TrainingUI (Canvas)
│   ├── SpawnPanel     — 적 종류·수량 선택
│   ├── GearPanel      — 장비 즉시 변경
│   ├── StatPanel      — 현재 스탯·세트 현황
│   └── ResetButton    — HP·쿨다운·식물 초기화
└── TrainingManager (MonoBehaviour)
```

### 2. TrainingManager 핵심 로직

```csharp
public class TrainingManager : MonoBehaviour
{
    [SerializeField] EnemyBase[] spawnPrefabs;
    [SerializeField] Transform[] spawnPoints;

    // 적 소환 — PoolManager 그대로 사용
    public void SpawnEnemy(int index, int count)
    {
        for (int i = 0; i < count; i++)
        {
            var pos = spawnPoints[i % spawnPoints.Length].position;
            PoolManager.Spawn(spawnPrefabs[index], pos, Quaternion.identity);
        }
    }

    // 전체 초기화
    public void ResetRoom()
    {
        // 모든 적 제거
        foreach (var e in EnemyBase.Active.ToArray())
            PoolManager.Despawn(e.gameObject);

        // 식물 제거
        foreach (var p in FindObjectsByType<PlantBase>(FindObjectsSortMode.None))
            PoolManager.Despawn(p.gameObject);

        // 플레이어 HP·쿨다운 초기화
        var hp = Object.FindFirstObjectByType<PlayerHealth>();
        hp.FullHeal();

        var onion = Object.FindFirstObjectByType<OnionController>();
        onion.ResetAllCooldowns();
    }

    // 장비 즉시 교체 (런 밖이므로 RunData 직접 조작)
    public void EquipGear(GearItem gear)
    {
        GameManager.Instance.Run.EquipDirectly(gear);
        // 세트·스탯 재계산
        Object.FindFirstObjectByType<PassiveHost>()?.Recalculate();
        Object.FindFirstObjectByType<PlayerStats>()?.Refresh();
    }
}
```

### 3. DummyTarget — 히트 수치 표시

```csharp
public class DummyTarget : MonoBehaviour, IDamageable
{
    [SerializeField] FloatingNumberSpawner floatingNumbers;

    public void TakeDamage(int amount, Attacker attacker, Vector2 hitDir)
    {
        // HP 소비 없음 — 수치만 표시
        floatingNumbers.Show(amount, attacker == Attacker.Cat ? Color.yellow : Color.cyan);

        // 최근 5타 DPS 계산
        dpsTracker.Record(amount);
    }
}
```

### 4. 메인 메뉴에서 진입

```csharp
// MainMenu.cs
public void OpenTrainingRoom()
{
    // RunData를 최대 장비 프리셋으로 초기화하거나, 현재 저장 상태 유지
    GameManager.Instance.StartTrainingRun();
    SceneManager.LoadScene("Training_Room");
}
```

### 5. 장비 선택 UI — 런 바깥에서 모든 장비 열람

```csharp
// 트레이닝 전용: 잠금 해제 조건 무시하고 전체 GearItem 표시
var allGear = Resources.LoadAll<GearItem>("Data/Gear");
// 카테고리별 그리드 표시 (기존 GearScreen 프리팹 재활용)
```

---

## OnionCat 적용 포인트

### 진입 위치
- **메인 메뉴 → TRAINING** 버튼 (런 중 접근 불가 — 별도 씬)
- 혹은 런 종료 결과 화면에서 "연습 방으로" 단축 버튼

### 필수 기능 (v1)
| 기능 | 설명 |
|---|---|
| 더미 타겟 소환 | 고정·이동 더미, 피해 수치·DPS 표시 |
| 적 소환 | 슬라임·원거리·방패병·보스 선택 소환 |
| 장비 즉시 교체 | 모든 장비 열람 + 장착 (세트 효과 즉시 반영) |
| 초기화 | HP 100, 쿨다운 0, 식물 제거, 적 제거 |
| 무적 토글 | 히트 확인하되 피해는 없애고 싶을 때 |

### 유용한 확장 기능 (나중에)
- **콤보 카운터 오버레이**: 협동 콤보 횟수·합동 게이지 축적 속도 시각화
- **히트박스 시각화**: `OnDrawGizmos`를 런타임에도 표시
- **슬로우 모션**: `Time.timeScale 0.25` 토글 — 보스 패턴 분석용
- **입력 기록**: 마지막 10초 입력 재생 (연습 구간 반복)

### 개발 부하 최소화 전략
1. `Room_Special` 씬을 기반으로 배경만 교체 — 새 씬 빌드 불필요
2. 장비 슬롯 UI는 `GearScreen` 프리팹을 그대로 embed
3. 적 소환은 기존 `PoolManager.Spawn` + `EnemySpawner` 재사용
4. Debug 메뉴(`OnionCat > Debug`)와 같은 버튼 집합을 인게임 UI로 이식하는 방식

---

## 참고 링크

- Hades 수련 방 GDC 슬라이드: https://www.gdcvault.com/play/1027335
- Dead Cells 훈련 모드 설계: https://dead-cells.fandom.com/wiki/Training_Room
- Unity SceneManager: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- 격투 게임 트레이닝 모드 UX 분석: https://www.gamedeveloper.com/design/the-importance-of-a-great-training-mode
