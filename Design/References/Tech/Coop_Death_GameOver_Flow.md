# 협동 게임 사망 & 게임오버 흐름

리서치 날짜: 2026-08-13

## 개요

로컬 협동 로그라이크에서 "플레이어 사망 → 게임오버" 전환은 단순한 씬 전환이 아니다.
사망 순간의 **연출(느린 화면, 카메라 떨림, 효과음)** 이 "죽음의 무게감"을 만들고,
통계 화면으로의 **부드러운 전환**이 "또 도전하고 싶다"는 의욕을 유지시킨다.

OnionCat은 한 몸이므로 "둘 중 하나 사망 = 즉시 게임오버" 구조.
→ 사망 연출이 길면 답답하고, 너무 짧으면 허무함. **1.5~2초 내에 완결** 되어야 함.

---

## 사망 흐름 설계

### OnionCat 권장 타임라인 (총 1.8초)

```
[Frame 0]   HP 0 도달
[0.00s]     히트스톱 (0.15초 Time.timeScale = 0)
[0.15s]     사망 애니메이션 시작 + 화면 진동
[0.15s]     BGM 피치 저하 시작 (1.0 → 0.3)
[0.45s]     슬로우모션 (timeScale 1.0 → 0.1, 0.5초)
[0.95s]     화면 서서히 어두워짐 (페이드 아웃, 0.5초)
[1.45s]     완전 암전 + GameOverScreen 씬 로드
[1.80s]     페이드 인 → 게임오버 화면 완전 표시
```

---

## Unity 구현 방법

### 1. DeathSequenceManager (싱글톤 또는 GameManager에 통합)

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

public class DeathSequenceManager : MonoBehaviour
{
    [Header("타이밍")]
    [SerializeField] private float hitStopDuration = 0.15f;
    [SerializeField] private float slowMoDuration = 0.5f;
    [SerializeField] private float slowMoScale = 0.1f;
    [SerializeField] private float fadeOutDuration = 0.5f;

    [Header("참조")]
    [SerializeField] private CanvasGroup fadeOverlay;   // 유니티 에디터에서 드래그 앤 드롭 설정 필요
    [SerializeField] private AudioSource bgmSource;     // 유니티 에디터에서 드래그 앤 드롭 설정 필요

    private bool isDeathSequencePlaying = false;

    public void TriggerDeathSequence(RunStats stats)
    {
        if (isDeathSequencePlaying) return;
        isDeathSequencePlaying = true;
        RunDataHolder.Instance.SaveStats(stats);
        StartCoroutine(DeathSequenceCoroutine());
    }

    private IEnumerator DeathSequenceCoroutine()
    {
        // 1. 히트스톱
        Time.timeScale = 0f;
        yield return new WaitForSecondsRealtime(hitStopDuration);

        // 2. 사망 애니메이션 트리거 (PlayerAnimator에 이벤트 발행)
        GameEvents.OnPlayerDeath?.Invoke();

        // 3. BGM 피치 저하 (비동기)
        StartCoroutine(FadeBGMPitch(1.0f, 0.3f, 0.8f));

        // 4. 슬로우모션
        Time.timeScale = slowMoScale;
        yield return new WaitForSecondsRealtime(slowMoDuration);

        // 5. 페이드 아웃
        yield return StartCoroutine(FadeOut(fadeOutDuration));

        // 6. 타임스케일 복구 후 씬 전환
        Time.timeScale = 1f;
        SceneManager.LoadScene("GameOverScene");
    }

    private IEnumerator FadeOut(float duration)
    {
        float t = 0f;
        while (t < duration)
        {
            t += Time.unscaledDeltaTime;
            fadeOverlay.alpha = Mathf.Lerp(0f, 1f, t / duration);
            yield return null;
        }
        fadeOverlay.alpha = 1f;
    }

    private IEnumerator FadeBGMPitch(float from, float to, float duration)
    {
        float t = 0f;
        while (t < duration)
        {
            t += Time.unscaledDeltaTime;
            bgmSource.pitch = Mathf.Lerp(from, to, t / duration);
            yield return null;
        }
    }
}
```

### 2. RunStats 데이터 모델

```csharp
[System.Serializable]
public class RunStats
{
    public int killCount;
    public float survivalTimeSeconds;
    public int floorsCleared;
    public List<string> upgradesObtained = new();
    public string causeOfDeath;       // 예: "Spear Goblin", "Poison Cloud"
    public System.DateTime runEndTime;
}
```

### 3. RunDataHolder (씬 간 데이터 전달)

```csharp
public class RunDataHolder : MonoBehaviour
{
    public static RunDataHolder Instance { get; private set; }
    public RunStats LastRunStats { get; private set; }

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void SaveStats(RunStats stats)
    {
        LastRunStats = stats;
        stats.runEndTime = System.DateTime.Now;
    }
}
```

### 4. 카메라 흔들림 연계 (CinemachineImpulse)

```csharp
// DeathSequenceManager 내부 추가
[SerializeField] private CinemachineImpulseSource deathImpulse;

private void TriggerDeathShake()
{
    // 강하고 느린 충격 — "무너지는 느낌"
    deathImpulse.GenerateImpulseWithVelocity(new Vector3(0.3f, -0.5f, 0f) * 2f);
}
```

---

## OnionCat 적용 포인트

### 한 몸 사망의 특수성

OnionCat는 한 몸이므로 "어떤 플레이어가 죽었는가"보다 "어떻게 죽었는가"가 연출 핵심.

```
P1(근접) 과실 사망: 적에 포위되어 HP 소진
→ 사망 애니메이션: 고양이가 앞으로 쓰러짐, 파가 화분째 옆으로 넘어짐

P2(원거리) 과실 사망: 원거리 적 공격에 맞아 HP 소진
→ 사망 애니메이션: 화분이 먼저 박살남 (파 기절), 고양이도 쓰러짐
```

### 사망 원인 기록 → 게임오버 화면 활용
```csharp
// 사망 원인을 RunStats에 저장 — GameOverScreen에서 표시
stats.causeOfDeath = lastDamagingEnemy?.enemyName ?? "Unknown";
```

### 부활 유예 시간 (선택 사항)
```csharp
// HP 0 시 즉시 사망 대신 5초 유예 → 협동 긴장감
[SerializeField] private float reviveWindowSeconds = 5f;
// → Coop_Revival_System.md 참고
// OnionCat는 한 몸이므로 부활 조건을 "일정 시간 적 처치 없음"으로 대체 가능
```

### 사망 연출 길이 권장값

| 상황 | 권장 길이 | 이유 |
|---|---|---|
| 일반 방 전투 중 사망 | 1.8초 | 적당한 무게감, 재시도 의욕 유지 |
| 보스 전투 중 사망 | 2.5초 | 보스의 위압감을 마지막에 한번 더 강조 |
| 디버그/테스트 모드 | 0.5초 | 개발 중 반복 테스트 편의 |

```csharp
// Debug 모드에서 빠른 사망 처리
if (Debug.isDebugBuild)
    hitStopDuration = slowMoDuration = fadeOutDuration = 0.1f;
```

---

## 씬 구조 요약

```
[InGame Scene]
    └─ DeathSequenceManager
         ├─ HP 0 감지 (PlayerHealth 이벤트)
         ├─ DeathSequenceCoroutine 실행
         └─ SceneManager.LoadScene("GameOverScene")

[GameOverScene]
    └─ GameOverScreen (GameOver_Screen.md 참고)
         ├─ RunDataHolder.Instance.LastRunStats 읽기
         ├─ 결과 표시 (처치수, 생존 시간, 사인)
         └─ 재시작 / 메인 메뉴 버튼
```

---

## 참고 링크

- Unity 공식 — SceneManager.LoadScene: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadScene.html
- Unity 공식 — Time.timeScale: https://docs.unity3d.com/ScriptReference/Time-timeScale.html
- CinemachineImpulse 문서: https://docs.unity3d.com/Packages/com.unity.cinemachine@2.8/manual/CinemachineImpulse.html
- 게임 사망 연출 디자인 분석 (GDC): https://www.gdcvault.com/play/1015512/
- 히트스톱 구현 레퍼런스: https://www.youtube.com/watch?v=V1EMwCIb_XE (Brackeys hit stop tutorial)
- Hades 사망 연출 분석: https://blog.hyperdash.io/hades-death-sequence-breakdown
