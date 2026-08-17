# 첫 실행 FTUE 온보딩 흐름

리서치 날짜: 2026-08-17

## 개요

FTUE(First Time User Experience)는 플레이어가 게임을 **처음 실행하는 순간부터 첫 번째 런을 시작하기까지의 전체 흐름**이다. 메인 메뉴, 튜토리얼 트리거, 컨트롤 안내, 첫 런 연출이 유기적으로 연결되어야 한다.

OnionCat처럼 조작 방식이 독특한 게임(P1 키보드 이동 + P2 마우스 조준, 공유 몸체)은 FTUE가 특히 중요하다. 컨트롤을 이해하기 전에 게임을 포기하는 플레이어를 줄이는 것이 목표.

---

## Unity 구현 방법

### 1. 첫 실행 여부 감지

```cs
// FTUEManager.cs
using UnityEngine;
using UnityEngine.SceneManagement;

public class FTUEManager : MonoBehaviour
{
    private const string FTUE_COMPLETE_KEY = "ftue_complete";
    private const string TUTORIAL_SKIP_KEY = "tutorial_skip";

    public static bool IsFirstRun => PlayerPrefs.GetInt(FTUE_COMPLETE_KEY, 0) == 0;

    public static void MarkFTUEComplete()
    {
        PlayerPrefs.SetInt(FTUE_COMPLETE_KEY, 1);
        PlayerPrefs.Save();
    }

    public static void ResetFTUE()
    {
        PlayerPrefs.DeleteKey(FTUE_COMPLETE_KEY);
        PlayerPrefs.DeleteKey(TUTORIAL_SKIP_KEY);
    }

    // 앱 시작 시 자동 호출 (Bootstrap 씬에서)
    public static void HandleFirstRun()
    {
        if (IsFirstRun)
        {
            // 첫 실행: 인트로 + 튜토리얼로 이동
            SceneManager.LoadScene("TutorialScene");
        }
        else
        {
            // 재실행: 바로 메인 메뉴
            SceneManager.LoadScene("MainMenu");
        }
    }
}
```

### 2. FTUE 흐름 상태 머신

FTUE는 여러 단계로 구성된다. 각 단계를 명시적 상태로 관리:

```cs
// FTUEFlow.cs
using UnityEngine;
using System.Collections;

public enum FTUEStep
{
    Intro,           // 게임 타이틀 + 짧은 로어 설명
    ControlIntro,    // 컨트롤 안내 (P1/P2 동시)
    MoveTest,        // P1 이동 연습
    AimTest,         // P2 마우스 조준 연습
    SharedBodyDemo,  // 공유 몸체 개념 설명
    FirstEnemyDemo,  // 첫 번째 적 처치 유도
    Complete         // FTUE 완료
}

public class FTUEFlow : MonoBehaviour
{
    [SerializeField] private FTUEStep currentStep;
    [SerializeField] private FTUEStepUI stepUI; // 각 단계 UI 참조

    private void Start()
    {
        StartCoroutine(RunFTUE());
    }

    private IEnumerator RunFTUE()
    {
        foreach (FTUEStep step in System.Enum.GetValues(typeof(FTUEStep)))
        {
            if (step == FTUEStep.Complete) break;
            currentStep = step;
            stepUI.ShowStep(step);
            yield return new WaitUntil(() => IsStepComplete(step));
            yield return new WaitForSeconds(0.5f); // 짧은 전환 딜레이
        }

        FTUEManager.MarkFTUEComplete();
        // 첫 런 시작으로 전환
        SceneTransitionManager.Instance.LoadScene("GameScene");
    }

    private bool IsStepComplete(FTUEStep step)
    {
        return step switch
        {
            FTUEStep.MoveTest => _playerMovedCount >= 10,
            FTUEStep.AimTest => _playerAimedCount >= 5,
            FTUEStep.FirstEnemyDemo => _firstEnemyKilled,
            _ => _stepConfirmed // 확인 버튼 또는 자동 진행
        };
    }

    // 이벤트 수신 (이벤트 버스와 연동)
    private int _playerMovedCount;
    private int _playerAimedCount;
    private bool _firstEnemyKilled;
    private bool _stepConfirmed;

    public void OnPlayerMoved() => _playerMovedCount++;
    public void OnPlayerAimed() => _playerAimedCount++;
    public void OnFirstEnemyKilled() => _firstEnemyKilled = true;
    public void OnStepConfirmed() => _stepConfirmed = true;
}
```

### 3. 컨트롤 안내 UI (툴팁 오버레이 방식)

```cs
// FTUEStepUI.cs — 각 단계별 UI 표시
using UnityEngine;
using TMPro;

public class FTUEStepUI : MonoBehaviour
{
    [SerializeField] private GameObject controlHintPanel;
    [SerializeField] private TextMeshProUGUI hintText;
    [SerializeField] private GameObject confirmButton;
    [SerializeField] private GameObject keyboardIcon;  // WASD 아이콘
    [SerializeField] private GameObject mouseIcon;     // 마우스 아이콘

    public void ShowStep(FTUEStep step)
    {
        // 이전 UI 초기화
        controlHintPanel.SetActive(false);
        confirmButton.SetActive(false);
        keyboardIcon.SetActive(false);
        mouseIcon.SetActive(false);

        switch (step)
        {
            case FTUEStep.ControlIntro:
                controlHintPanel.SetActive(true);
                hintText.text = "플레이어 1 (고양이): WASD로 이동\n플레이어 2 (양파): 마우스로 조준, 클릭으로 발사";
                keyboardIcon.SetActive(true);
                mouseIcon.SetActive(true);
                confirmButton.SetActive(true);
                break;

            case FTUEStep.MoveTest:
                controlHintPanel.SetActive(true);
                hintText.text = "WASD로 이동해보세요 (10번)";
                keyboardIcon.SetActive(true);
                break;

            case FTUEStep.SharedBodyDemo:
                controlHintPanel.SetActive(true);
                hintText.text = "고양이가 움직이면 양파도 함께 움직입니다!\n두 플레이어가 하나의 몸체를 공유합니다.";
                confirmButton.SetActive(true);
                break;
        }
    }
}
```

### 4. 튜토리얼 스킵 처리

```cs
// FTUESkipButton.cs
using UnityEngine;
using UnityEngine.SceneManagement;

public class FTUESkipButton : MonoBehaviour
{
    public void OnSkipPressed()
    {
        // 튜토리얼 스킵 시에도 FTUE 완료 처리 (다음 실행에서 다시 안 보임)
        FTUEManager.MarkFTUEComplete();
        PlayerPrefs.SetInt("tutorial_skip", 1);
        SceneManager.LoadScene("MainMenu");
    }
}
```

### 5. 재실행 시 FTUE 재관람 옵션 (설정 메뉴)

```cs
// 설정 메뉴의 "튜토리얼 다시 보기" 버튼
public void OnReplayTutorialPressed()
{
    FTUEManager.ResetFTUE();
    SceneManager.LoadScene("TutorialScene");
}
```

### 6. 씬 구성 제안

```
Bootstrap (씬, 맨 처음 로드)
  └─ FTUEManager.HandleFirstRun() 호출
      ├─ 첫 실행 → TutorialScene
      │     └─ FTUEFlow 완료 → GameScene (첫 런)
      └─ 재실행 → MainMenu
```

### 7. FTUE 내 미니 룸 구성

튜토리얼은 별도 씬에서 미니 룸을 제공:

```
TutorialScene 구성:
  - 단일 룸 (적 없는 안전 구역)
  - 컨트롤 안내 오버레이
  - 이동 연습 트리거 존 (특정 위치 밟으면 단계 진행)
  - 더미 적 1마리 (맞아도 반격 안 함, HP 10)
  - 명시적 "첫 런 시작!" 버튼
```

---

## OnionCat 적용 포인트

### OnionCat FTUE 특수 고려사항

1. **공유 몸체 개념 설명이 필수**
   - 일반 게임과 달리 P1이 이동하면 P2의 위치도 바뀜
   - "두 사람이 하나의 몸" 시각적 연출 필요: 화살표로 두 캐릭터가 연결됨을 보여줌

2. **P1/P2 역할 분리 안내**
   - P1(Cat): WASD 이동 + 근접 공격
   - P2(Crop): 마우스 조준 + 원거리 투사체 + 방패/패링
   - 역할이 달라서 튜토리얼도 두 파트로 구성

3. **약점 시스템 사전 안내**
   - "근접에만 약한 적" / "원거리에만 약한 적" 개념을 FTUE에서 미리 보여줌
   - 더미 적 2종류: 🗡️ 아이콘 (근접에만 피격) / 🏹 아이콘 (원거리에만 피격)

4. **권장 FTUE 단계 순서**

| 단계 | 내용 | 예상 시간 |
|------|------|----------|
| 1 | 타이틀 연출 (로고 + 배경음악) | 5초 |
| 2 | 조작 안내 화면 (P1/P2 동시) | 15초 |
| 3 | 이동 연습 (WASD, 10번) | 20초 |
| 4 | 마우스 조준 연습 (과녁 5번 클릭) | 20초 |
| 5 | 공유 몸체 시연 (애니메이션) | 10초 |
| 6 | 근접 약점 적 처치 | 30초 |
| 7 | 원거리 약점 적 처치 | 30초 |
| 8 | 첫 런 시작 연출 | 10초 |
| **총계** | | **~2분** |

5. **FTUE 건너뛰기 버튼 위치**
   - 오른쪽 상단 고정 ("건너뛰기 →")
   - 반투명 처리로 눈에 띄되 방해되지 않게

### [SerializeField] 설정 필요
- `FTUEFlow._playerMovedCount` 임계값(기본 10) Inspector에서 조정 가능하게
- `FTUEStepUI` 내 UI 오브젝트들 (controlHintPanel, hintText 등) 유니티 에디터에서 드래그 앤 드롭 설정 필요
- `FTUESkipButton`은 Canvas 위에 배치된 버튼 오브젝트에 추가

---

## 참고 링크

- [Unity Docs: PlayerPrefs](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [Unity Docs: SceneManager.LoadScene](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadScene.html)
- [게임 튜토리얼 디자인 원칙 (GDC)](https://www.gdcvault.com/play/1014981/Learning-by-Doing-Great)
- [FTUE Best Practices — Gamasutra](https://www.gamedeveloper.com/design/the-art-of-the-tutorial-teaching-the-player-without-hand-holding)
- [Unity Bootstrap Scene Pattern](https://unity.com/how-to/architect-game-code-scriptable-objects)
