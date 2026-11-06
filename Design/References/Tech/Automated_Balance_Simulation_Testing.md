# 자동화 밸런스 시뮬레이션 테스트

리서치 날짜: 2026-11-06

## 개요

스크립트 기반 "봇"이 게임을 대신 플레이해 밸런스 데이터를 자동 수집하는 기법.  
로그라이크에서는 장비 조합·적 체력·보상 가중치가 복잡하게 얽혀 손으로 테스트하기 어렵다.  
봇 시뮬레이션을 돌리면 **"어떤 장비가 너무 강한가", "어떤 방이 너무 오래 걸리는가"** 같은 질문에 데이터로 답할 수 있다.

---

## Unity 구현 방법

### Step 1: 전투 결과 로거 만들기

```csharp
// 런 결과를 JSON으로 기록하는 컴포넌트
[System.Serializable]
public class BotRunRecord
{
    public int runIndex;
    public string[] equippedGear;
    public int roomsCleared;
    public float finalHpPercent;
    public float totalRunTimeSeconds;
    public int totalDamageTaken;
    public int totalDamageDealt;
    public bool cleared; // 보스 처치 여부
    public Dictionary<string, int> gearUsageCount; // 어떤 효과가 발동됐나
}
```

### Step 2: 봇 AI 작성 (최소 구현)

단순 "항상 가장 가까운 적을 향해 이동 + 주기적으로 공격" 봇으로 충분.  
밸런스 테스트의 목적은 "사람이 잘 플레이했을 때"가 아니라 **"평균적인 플레이에서 편차"를 보는 것**.

```csharp
public class BotPlayerCat : MonoBehaviour
{
    [SerializeField] float attackInterval = 0.5f;
    float attackTimer;

    void Update()
    {
        if (!GameManager.IsGameplayActive) return;
        
        // 가장 가까운 적으로 이동
        var nearest = FindNearestEnemy();
        if (nearest != null)
        {
            var dir = (nearest.transform.position - transform.position).normalized;
            movement.Move(dir);
            
            attackTimer -= Time.deltaTime;
            if (attackTimer <= 0f)
            {
                attack.TriggerSlash();
                attackTimer = attackInterval;
            }
        }
        
        // 대쉬: 맞는 순간 랜덤 방향으로
        if (justGotHit) dash.TriggerDash(Random.insideUnitCircle.normalized);
    }
    
    EnemyBase FindNearestEnemy() =>
        EnemyBase.Active.OrderBy(e => Vector2.Distance(transform.position, e.transform.position))
                        .FirstOrDefault();
}
```

### Step 3: 에디터 메뉴에서 N회 반복 실행

```csharp
#if UNITY_EDITOR
[MenuItem("OnionCat/Debug/Run Balance Simulation")]
static async void RunBalanceSimulation()
{
    int runs = 100;
    var records = new List<BotRunRecord>();

    for (int i = 0; i < runs; i++)
    {
        // 런 초기화
        GameManager.Instance.StartNewRun(botMode: true);
        
        // 완료까지 대기 (Coroutine 또는 Task)
        await WaitForRunEnd();
        
        // 결과 수집
        records.Add(CollectRunRecord(i));
        
        EditorUtility.DisplayProgressBar("시뮬레이션", $"{i+1}/{runs}", (float)i/runs);
    }
    
    EditorUtility.ClearProgressBar();
    ExportToCsv(records, "Assets/Simulation/balance_results.csv");
    Debug.Log($"시뮬레이션 완료: {runs}회, 클리어율 {records.Count(r => r.cleared) * 100 / runs}%");
}
#endif
```

### Step 4: 결과 분석

생성된 CSV를 보면:
- **클리어율 (cleared rate)** : 평균 60~70% 목표, 90% 이상이면 너무 쉬움
- **장비별 클리어율 차이** : 특정 장비가 클리어율을 10%p 이상 높이면 과강
- **방별 평균 대미지** : 체력 100 기준 20 이상이면 그 방이 너무 가혹
- **런 소요 시간** : 평균 목표 시간(60분)에서 ±15분 벗어나면 조절 필요

```python
# Design/Data/analyze_simulation.py (간단한 분석 스크립트)
import pandas as pd

df = pd.read_csv("balance_results.csv")
print(f"클리어율: {df['cleared'].mean()*100:.1f}%")
print(f"평균 체력 잔량: {df['finalHpPercent'].mean()*100:.1f}%")
print(f"평균 런 시간: {df['totalRunTimeSeconds'].mean()/60:.1f}분")

# 장비별 클리어율
for gear in df['equippedGear'].explode().unique():
    runs_with = df[df['equippedGear'].apply(lambda g: gear in g)]
    print(f"{gear}: 클리어율 {runs_with['cleared'].mean()*100:.1f}% (n={len(runs_with)})")
```

---

## OnionCat 적용 포인트

### 현재 아키텍처와 연결
- `GameManager.StartNewRun()` 이미 존재 → `botMode: true` 플래그 하나 추가하면 봇 플레이어 활성화
- `RunData` 클래스에 모든 런 상태가 있음 → 로거가 가져가기 쉬운 구조
- `EnemyBase.Active` 리스트가 존재 → 봇의 타겟 찾기 간단

### 구체 활용 시나리오
1. **새 장비 추가 시**: 100회 시뮬레이션 → 그 장비 조합의 클리어율 확인
2. **새 적 추가 시**: 그 방이 포함된 런의 대미지 평균 확인 → 너무 높으면 체력 조절
3. **보상 테이블 조정 시**: 가중치 바꾸기 전·후 클리어율 비교
4. **출시 전 종합 체크**: 1000회 시뮬레이션 → "어떤 장비 조합이 OP인가" 발견

### 봇의 한계와 보완
- 봇은 패링·협동 콤보를 거의 안 함 → 실제 플레이보다 낮은 클리어율 나옴 → **기준값(baseline)** 으로 쓰고 절대값보다 **상대 비교**에 활용
- 고양이 봇과 양파 봇을 함께 돌릴 때 협동 콤보 판정 가중치 (0%)로 설정 → "패링 없는 최악 플레이"의 하한선 측정 가능

### 구현 우선순위
1. **즉시**: 런 종료 시 `Debug.Log`로 HP%, 클리어 여부, 소요 시간 출력 (2~3줄)
2. **단기**: 에디터 메뉴에서 10회 자동 반복 버튼 + CSV 출력
3. **장기**: 장비 조합 망라 시뮬레이션 + Python 분석 스크립트

---

## 참고 링크
- [Unity Test Runner 공식 문서](https://docs.unity3d.com/Manual/testing-editortestsrunner.html)
- [GDC Talk: Automated Testing in Games (YouTube 검색)](https://gdcvault.com)
- [Unity의 에디터 테스트 & PlayMode 테스트 활용](https://docs.unity3d.com/Packages/com.unity.test-framework@1.1/manual/index.html)
- [Monte Carlo Simulation for Game Balance (Gamedeveloper.com 검색어)](https://gamedeveloper.com)
