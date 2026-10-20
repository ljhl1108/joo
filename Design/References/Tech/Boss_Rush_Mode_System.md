# Boss Rush Mode System (보스 러시 모드)

리서치 날짜: 2026-10-20

## 개요

보스 러시 모드는 일반 런의 탐색·수집 구간을 생략하고 **보스만 연속으로 상대**하는 대체 게임 모드다. 코어 전투 루프가 재미있는 로그라이크에서 리플레이어빌리티를 크게 높이는 저비용 고효율 기능이다.

**OnionCat 적합성**: 게임의 가장 강한 경험(보스 전투)을 즉시 반복 가능하게 → 숙련자 보상, 캐주얼 플레이어 소개용, 스피드런 기반 마련.

보스 러시를 구현한 게임 사례:
- **Hades**: God Mode 없이도 "하데스에게 도달하기"만을 위한 전투 반복 가능 (정식 보스 러시는 아니지만 단축 런 발전)
- **Hollow Knight**: Path of Pain, Pantheons (보스 러시 성격의 도전 콘텐츠)
- **Enter the Gungeon**: Duct Tape 조합 발견 이후 보스만 노리는 플레이 스타일 자연 발생
- **Dead Cells**: Boss Rush DLC (별도 판매)로 큰 호응

## Unity 구현 방법

### 전체 아키텍처

```
BossRushManager         — 보스 러시 런 상태 관리
  ├─ BossRushConfig     — ScriptableObject: 참여 보스 목록, 시작 장비, 씨앗 지급
  ├─ BossRushRoomSetup  — 일반 방 씬 재사용, 보스 스폰만 직접 실행
  └─ BossRushHUD        — 타이머, 보스 순서 표시
```

### 1. BossRushConfig (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "OnionCat/BossRushConfig")]
public class BossRushConfig : ScriptableObject
{
    [Header("참여 보스 순서")]
    public EnemyData[] bossSequence; // 기사 → 궁수 → 마법사

    [Header("시작 장비 (장비 없이 시작하면 너무 쉽거나 어려움)")]
    public GearItem[] startGear_Cat;
    public GearItem[] startGear_Crop;
    public int startSeeds = 30;

    [Header("중간 보상 (보스 하나 클리어할 때마다)")]
    public bool giveUpgradesBetweenBosses = true;
    public int cardsOffered = 2;         // 일반 런보다 적게
}
```

### 2. BossRushManager

```csharp
public class BossRushManager : MonoBehaviour
{
    public static BossRushManager Instance { get; private set; }

    [SerializeField] BossRushConfig config;

    int currentBossIndex;
    float runStartTime;
    float totalClearTime;

    public void StartBossRush()
    {
        // RunData 초기화 (일반 런과 동일하게)
        GameManager.Instance.StartNewRun(bossRushMode: true);

        // 시작 장비 지급
        ApplyStartGear();

        // 첫 보스 스폰
        currentBossIndex = 0;
        runStartTime = Time.time;
        SpawnNextBoss();
    }

    void SpawnNextBoss()
    {
        if (currentBossIndex >= config.bossSequence.Length)
        {
            OnAllBossesCleared();
            return;
        }

        var bossData = config.bossSequence[currentBossIndex];

        // Room_Special 씬 재사용 (보스 아레나로 리셋)
        // EnemyRoster.bossFirst/Middle/Last 대신 직접 스폰
        Room.Current.SpawnSpecificEnemy(bossData);

        // 보스방 BGM 재생
        Music.Play(MusicId.Boss);
    }

    public void OnBossDefeated()
    {
        // 클리어 시간 기록
        float bossTime = Time.time - runStartTime;
        BossRushResult.LogBossTime(currentBossIndex, bossTime);

        currentBossIndex++;

        if (currentBossIndex < config.bossSequence.Length)
        {
            // 중간 보상 화면 (카드 선택)
            if (config.giveUpgradesBetweenBosses)
                GameManager.Instance.ChangeState(GameState.Reward);
            else
                SpawnNextBoss();
        }
        else
        {
            OnAllBossesCleared();
        }
    }

    void OnAllBossesCleared()
    {
        totalClearTime = Time.time - runStartTime;
        GameManager.Instance.ChangeState(GameState.Victory);
        // 결과 화면에 보스별 클리어 시간 + 총 시간 표시
    }
}
```

### 3. 씬 진입점 분기 (기존 코드 최소 수정)

```csharp
// GameManager.StartNewRun 확장
public void StartNewRun(bool bossRushMode = false)
{
    RunData = new RunData();
    RunData.isBossRush = bossRushMode; // RunData에 플래그 추가

    if (bossRushMode)
    {
        DungeonManager.enabled = false; // 일반 던전 생성 비활성화
        BossRushManager.Instance.StartBossRush();
    }
    else
    {
        DungeonManager.StartRun();
    }
}
```

### 4. 보스 러시 결과 화면

```csharp
public class BossRushResult
{
    public static List<(string bossName, float clearTime)> BossTimings = new();

    public static void LogBossTime(int index, float time)
    {
        BossTimings.Add((config.bossSequence[index].displayName, time));
    }

    public static float TotalTime => BossTimings.Sum(t => t.clearTime);
}
```

결과 화면(`RunResultScreen.cs`)에서 `RunData.isBossRush`로 분기해 타이밍 표 표시.

### 5. 잠금 해제 조건

```csharp
// MetaProgress.cs에 추가
public bool bossRushUnlocked => questsCompleted >= 1; // 첫 퀘스트 완료 시 해금
```

메인 메뉴 → "보스 러시" 버튼 (조건 미달 시 회색 + 잠금 아이콘 + "퀘스트 1개 완료 후 해금" 툴팁).

### 6. 보스 러시 전용 HUD 요소

```
┌─────────────────────────────────┐
│  BOSS RUSH   [기사 ✓][궁수 ➡][마법사 ○]  │
│              00:42.3  총 시간           │
└─────────────────────────────────┘
```

- 보스 아이콘 진행도: 클리어 = ✓, 현재 = ➡, 미도달 = ○
- 현재 보스 클리어 시간 + 누적 시간
- 기존 `CoreHUD` 위에 보스 러시 배너를 오버레이로 추가

## OnionCat 적용 포인트

### 최소 구현 (MVP)

1. 메인 메뉴에 "보스 러시" 버튼 추가 (MetaProgress.bossRushUnlocked로 표시)
2. `BossRushConfig` ScriptableObject 1개 생성 (기사→궁수→마법사 순서, 기본 장비 설정)
3. `GameManager.StartNewRun(bossRushMode: true)` 분기
4. 일반 보스방 씬 재사용 + `BossRushManager.OnBossDefeated()` 연결
5. 결과 화면에 보스별 시간 표시

**예상 작업량**: 스크립트 2~3개 + 기존 코드 소수 수정 = 약 반나절

### 확장 옵션

| 기능 | 설명 | 난이도 |
|------|------|--------|
| 무제한 보스 러시 | 랜덤 보스가 계속 나옴, 처음 실패할 때까지 | ★☆☆ |
| 일일 보스 러시 랭킹 | `Daily_Challenge_Seed_System.md` 활용 | ★★☆ |
| 장비 없이 시작 | "맨몸으로" 옵션 — 극한 도전 | ★☆☆ |
| 보스 선택 러시 | 플레이어가 도전할 보스를 고름 | ★☆☆ |
| 협동 스피드런 모드 | 보스 러시 + 타이머가 랭킹에 올라감 | ★★★ |

### 주의사항

- **보스 러시 중 씨앗·장비 균형**: 보스 전투가 연속이라 일반 런보다 장비 질이 중요해짐
  - 권장: 처음에 희귀 장비 3~4개 제공 + 보스마다 카드 2장 선택
  - 너무 약하면 첫 보스에서 막힘, 너무 강하면 너무 쉬움 → 플레이 테스트 필수
- **보스 러시는 `meta.json` 퀘스트·파편에 영향 없게 처리**: `RunData.isBossRush`가 true면 `MetaProgress.OnRunCompleted` 호출 스킵
- **DungeonManager 끄는 법**: `DungeonManager.Instance.enabled = false` 대신 `DungeonManager.IsBossRush` 플래그로 내부에서 조건 분기가 더 안전

## 참고 링크
- [GDC: Designing Hades — 반복 플레이 설계 (2020)](https://www.gdcvault.com/play/1027104/)
- [Dead Cells: Boss Rush DLC 설계 인터뷰](https://www.eurogamer.net/dead-cells-boss-rush-dlc)
- [Hollow Knight Pantheons 설계 분석](https://www.reddit.com/r/HollowKnight/wiki/pantheons)
- [Unity ScriptableObject Architecture Best Practices](https://unity.com/how-to/architect-game-code-scriptable-objects)
