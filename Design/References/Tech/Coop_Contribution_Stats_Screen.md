# 협동 기여도 통계 & 런 종료 P1/P2 비교 화면 (Coop Contribution Stats Screen)

리서치 날짜: 2026-10-08

## 개요

로그라이크 런 종료 시 **두 플레이어 각자의 기여도를 비교 표시하는 화면**.  
OnionCat에서 중요한 이유:
- 비대칭 협동(고양이=근접/양파=원거리)이므로 기여도가 성격이 달라 단순 비교 불가
- **"누가 더 잘했나"보다 "두 사람이 함께 이만큼 했다"**는 프레이밍이 협동 게임에 어울림
- 재플레이 동기: 내 기여도 수치를 보면 "다음엔 더 잘하고 싶다" 욕구 자극
- 런 복기: 어느 방에서 얼마나 맞았는지, 어느 적이 어려웠는지 파악

---

## 수집할 통계 항목

### 고양이 전용
| 항목 | 설명 |
|------|------|
| `catMeleeHits` | 근접 공격 적중 횟수 |
| `catDashCount` | 대쉬 사용 횟수 |
| `catDamageDone` | 근접으로 입힌 총 피해 |
| `catDamageTaken` | 받은 총 피해 |
| `catDeathCount` | 사망 횟수 (부활 제외) |
| `catClawStyleUsed` | 할퀴기/걷어차기 사용 횟수 |

### 양파 전용
| 항목 | 설명 |
|------|------|
| `onionShotsFired` | 발사 횟수 |
| `onionShotsHit` | 명중 횟수 |
| `onionDamageDone` | 원거리로 입힌 총 피해 |
| `onionShieldRaised` | 방패 올린 횟수 |
| `onionParrySuccess` | 패링 성공 횟수 |
| `onionSkillUsed` | 스킬 사용 횟수 |

### 공유
| 항목 | 설명 |
|------|------|
| `totalEnemiesKilled` | 처치한 적 수 |
| `bossesDefeated` | 보스 처치 수 |
| `roomsCleared` | 클리어한 방 수 |
| `runDurationSeconds` | 런 총 시간 |
| `coopComboCount` | 협동 콤보 발동 횟수 |
| `upgradesSelected` | 선택한 업그레이드 총 수 |

---

## Unity 구현 방법

### 1. RunData에 통계 추가

```csharp
// RunData.cs (ScriptableObject — 이미 존재하는 런 상태 객체에 추가)
[System.Serializable]
public class CombatStats {
    // Cat
    public int catMeleeHits;
    public int catDashCount;
    public int catDamageDone;
    public int catDamageTaken;
    public int catDeathCount;
    public int catClawStyleUsed;

    // Onion
    public int onionShotsFired;
    public int onionShotsHit;
    public int onionDamageDone;
    public int onionShieldRaised;
    public int onionParrySuccess;
    public int onionSkillUsed;

    // Shared
    public int totalEnemiesKilled;
    public int bossesDefeated;
    public int roomsCleared;
    public float runDurationSeconds;
    public int coopComboCount;
}

// RunData 내부
public CombatStats Stats = new CombatStats();
```

### 2. 이벤트 구독으로 통계 수집 (기존 시스템 비침습)

새 스크립트 `RunStatsTracker.cs` 를 만들어 기존 이벤트에 붙이는 방식. 기존 시스템 코드를 수정하지 않음.

```csharp
public class RunStatsTracker : MonoBehaviour {
    private RunData _run;

    void OnEnable() {
        GameManager.OnStateChanged += HandleStateChanged;
        // 각 시스템의 이벤트 구독
        CatMeleeCombat.OnHit += OnCatMeleeHit;
        OnionShooter.OnShotFired += OnOnionShot;
        OnionShooter.OnShotHit += OnOnionShotHit;
        OnionShield.OnShieldRaised += OnShieldRaised;
        OnionShield.OnParrySuccess += OnParrySuccess;
        EnemyBase.OnEnemyDied += OnEnemyKilled;
        PlayerHealth.OnPlayerDied += OnPlayerDied;
    }

    void OnDisable() {
        GameManager.OnStateChanged -= HandleStateChanged;
        CatMeleeCombat.OnHit -= OnCatMeleeHit;
        OnionShooter.OnShotFired -= OnOnionShot;
        // ... 나머지 구독 해제
    }

    private void OnCatMeleeHit(int damage) {
        _run.Stats.catMeleeHits++;
        _run.Stats.catDamageDone += damage;
    }

    private void OnEnemyKilled(EnemyBase enemy) {
        _run.Stats.totalEnemiesKilled++;
        if (enemy is BossBase) _run.Stats.bossesDefeated++;
    }
    // ...
}
```

**각 시스템에 static 이벤트 추가**:
```csharp
// CatMeleeCombat.cs 내 피해를 입히는 곳에
public static event System.Action<int> OnHit;
// ...
OnHit?.Invoke(damage);
```

### 3. 결과 화면 UI 구조

```
RunResultScreen (Canvas)
├── Background (Panel)
├── TitleLabel ("Run Over" / "Victory!")
├── RunTimeLabel ("03:47")
├── SharedStatsPanel
│   ├── EnemiesKilledLabel
│   ├── RoomsLabel
│   └── CoopComboLabel
├── ComparisonPanel
│   ├── CatColumn
│   │   ├── CatIcon
│   │   ├── DamageDoneBar (진행 바)
│   │   ├── HitsLabel
│   │   └── MvpBadge (조건부 활성)
│   └── OnionColumn
│       ├── OnionIcon
│       ├── DamageDoneBar
│       ├── AccuracyLabel (명중률%)
│       └── MvpBadge
├── HighlightPanel ("Best Parry!", "First Boss Kill!")
└── ButtonRow (Restart / Menu)
```

### 4. 기여도 바(Bar) 애니메이션

```csharp
IEnumerator AnimateBars() {
    int totalDamage = stats.catDamageDone + stats.onionDamageDone;
    float catRatio = totalDamage > 0 ? (float)stats.catDamageDone / totalDamage : 0.5f;

    float elapsed = 0f;
    float duration = 0.8f;
    while (elapsed < duration) {
        elapsed += Time.unscaledDeltaTime;
        float t = Mathf.SmoothStep(0f, 1f, elapsed / duration);
        _catBar.fillAmount = catRatio * t;
        _onionBar.fillAmount = (1f - catRatio) * t;
        yield return null;
    }
}
```

### 5. 하이라이트 생성 (특이한 기록 강조)

```csharp
string GetHighlight(CombatStats s) {
    if (s.onionParrySuccess >= 5) return "Parry Master! (x{s.onionParrySuccess})";
    if (s.coopComboCount >= 10) return "Combo Addicts! (x{s.coopComboCount})";
    if (s.catDeathCount == 0) return "Untouchable Cat!";
    if (s.onionShotsHit > 0 && (float)s.onionShotsHit / s.onionShotsFired > 0.9f) return "Sharpshooter Onion!";
    return string.Empty;
}
```

### 6. 런 종료 흐름 연결

```csharp
// GameManager.cs OnStateChanged 핸들러에서
case GameState.RunOver:
case GameState.Victory:
    StartCoroutine(ShowResultAfterDelay(1.5f));
    break;

IEnumerator ShowResultAfterDelay(float delay) {
    yield return new WaitForSecondsRealtime(delay);
    SceneManager.LoadScene(SceneNames.Result);
    // 또는 오버레이 패널로 현재 씬에서 표시
}
```

---

## OnionCat 적용 포인트

### 비대칭 비교 UI 설계 원칙
- 같은 수치로 비교하면 안 됨 (고양이는 명중률이 의미 없고, 양파는 대쉬 횟수가 없음)
- 각 플레이어의 **역할에 맞는 지표**를 골라 표시
  - 고양이: 총 피해, 대쉬 횟수, 할퀴기 사용
  - 양파: 명중률(%), 패링 성공, 스킬 사용
- 공유 지표(처치 수, 협동 콤보)는 중앙에 배치 — "우리가 함께" 프레이밍

### MVP 배지
- 고양이 피해 > 양파 피해 → "Cat MVP" 배지
- 단, 패링 성공 3회 이상이면 양파에게 별도 "Shield Hero" 배지 → MVP는 고양이여도 양파가 인정받음
- **둘 다 MVP는 없음** → 경쟁이 아닌 역할 인정

### RunData 저장 시점
- 런 도중: `GameManager.Instance.Run.Stats` 에 실시간 누적
- 씬 전환 시 RunData는 DontDestroyOnLoad 또는 ScriptableObject이므로 유지됨
- 런 완전 종료 후: 통계를 `PlayerPrefs` 또는 JSON에 누적 저장 (메타 통계)

### 영구 통계 (런간)
- `LifetimeStats`: 총 런 횟수, 총 처치 수, 최장 클리어 시간 등
- `Achievement_Stats_System.md` 와 연동: 특정 조건 달성 시 도전과제 해금

---

## 주의 사항

- **Time.timeScale = 0인 상태에서 표시**: 결과 화면은 게임이 멈춘 상태이므로 `Time.unscaledDeltaTime` 사용
- **단독 플레이 모드가 없는 경우**: OnionCat은 항상 2인이므로 P1/P2 분리 가정이 안전하지만, 추후 AI 파트너 모드 추가 시 `isAI` 플래그로 분기
- **이벤트 누수 방지**: RunStatsTracker는 런 시작 시 활성화, 런 종료 시 비활성화
- **UI 텍스트는 영어로**: TMP 폰트에 한글 글리프 없음 (CLAUDE.md 규칙)

---

## 참고 링크

- [Unity Docs — SceneManager.LoadScene](https://docs.unity3d.com/ScriptReference/SceneManager.LoadScene.html)
- [Unity Docs — Image.fillAmount (기여도 바 구현)](https://docs.unity3d.com/ScriptReference/UI.Image-fillAmount.html)
- [GDC: Returnal Postmortem — Player Stats & Feedback Loops]
- Coop_Run_Result_Screen.md — 기본 런 결과 화면 구조 참고
- Achievement_Stats_System.md — 영구 통계 & 도전과제 연동
- InRun_Data_Persistence_System.md — RunData 구조 참고
