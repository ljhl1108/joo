# Asymmetric Co-op Tutorial Design (비대칭 코-옵 튜토리얼 설계)

리서치 날짜: 2026-11-22

## 개요

비대칭 코-옵 = 두 플레이어가 **다른 역할**을 맡는 협동 게임.
OnionCat처럼 "한 몸 두 조종"이면 더욱 특수하다:
- P1(고양이): 이동·근접 — 패드
- P2(작물): 조준·스킬 — 마우스+키보드
- 패드 없을 때: 고양이도 키보드

표준 단일 플레이어 튜토리얼 설계(한 화면에 하나의 역할만 가르침)는 여기에 맞지 않는다.
두 역할을 **동시에, 간섭 없이, 각자 적절한 타이밍에** 가르쳐야 한다.

## 비대칭 튜토리얼의 3대 원칙

### 1. 역할 분리 학습 (Isolated Role Introduction)
각 플레이어는 **상대방이 조용한 동안** 자기 조작을 배운다.

```
단계 1: 고양이만 움직이기 — 작물은 쏘지 않음 (스스로 목표 없음)
단계 2: 작물만 쏘기 — 고양이는 가만히 서 있는 적 앞에서 대기
단계 3: 둘이 동시 — 위협 수준을 낮게 유지
```

### 2. 화면 내 단서 분리 (Split Visual Cues)
두 플레이어가 같은 화면을 보는 싱글 스크린에서 **누구에게 가르치는지** 명확히 해야 한다.

- 고양이에 관한 튜토리얼 팝업 = 고양이에게 붙어 다니는 말풍선 or 아이콘
- 작물에 관한 팁 = 화분 위 말풍선, 별도 색
- **동시에 두 튜토리얼 팝업을 화면에 띄우지 않는다** → 한 번에 하나

### 3. 협동 시연 먼저, 개인 연습 나중 (Demo then Practice)
처음 접하는 플레이어는 "내가 무엇을 해야 하는지"보다 "우리가 함께 무엇을 하는 건지"를 먼저 이해해야 한다.

- 오프닝: 짧은 연출로 "고양이가 뛰고, 작물이 쏘고, 함께 적을 처치"를 보여줌
- 그 다음 플레이어가 직접 따라 함

## OnionCat 튜토리얼 단계 설계 (제안)

### 방 1 — 고양이 이동

| 목표 | 조건 | 대사 |
|------|------|------|
| WASD / 패드로 이동 | 플레이어가 움직임 | 책: "첫발을 내딛어 봐." |
| 대쉬 | 대쉬 1회 | 책: "빠르게 이동하고 싶을 땐—" |
| 할퀴기로 풀 오브젝트 처치 | 적 없음, 허수아비 등 | 책: "발톱이 날카롭군." |

### 방 2 — 작물 사격

| 목표 | 조건 | 대사 |
|------|------|------|
| 마우스 조준 | 조준선 나타남 | 책: "마우스로 겨냥해봐." |
| 씨앗 발사 | 적 1마리 고정 | 책: "쏴!" |
| 고양이가 근처에 있으면 씨앗이 더 강해지는 콤보 | 연속 타격 감지 | 책: "같이 맞추면 더 아프단 말이지." |

### 방 3 — 첫 번째 전투

- 슬라임 2마리 등장 (기동력 없음, 느린 돌진)
- 여기서 처음으로 패시브 실드를 가르침 (맞고 나서 "방금 실드가 막아줬어")
- 처치 후 첫 번째 장비 보상 선택 → 각자 고르는 흐름 처음 경험

## 솔로 플레이 (패드 없을 때) 처리

OnionCat은 솔로도 가능 (고양이 = 키보드 이동+할퀴기, 작물 = 마우스):
- 솔로 감지 조건: 패드 없이 시작
- 솔로 튜토리얼은 "한 사람이 두 가지를 배움" → 역할 순서 교육이 더 중요
- 추천 흐름: 고양이 조작 먼저 → 작물 조작 → 동시 사용

## Unity 구현 패턴

```csharp
// TutorialStep.cs
public enum TutorialOwner { Cat, Crop, Both }

[System.Serializable]
public class TutorialStep
{
    public TutorialOwner owner;
    public string speechBubbleText;
    public Func<bool> completionCondition;
}

// 말풍선 위치 — owner에 따라 고양이 머리 위 or 화분 위
Transform GetAnchor(TutorialOwner owner) =>
    owner == TutorialOwner.Cat ? _catHead :
    owner == TutorialOwner.Crop ? _cropPot : _centerHUD;
```

### 튜토리얼 스킵 처리

```csharp
// 첫 런에만 보임 — MetaProgress.tutorialDone으로 추적
if (MetaProgress.data.tutorialDone)
{
    SkipTutorial();
    return;
}
// 완료 후 MetaProgress.data.tutorialDone = true; Save();
```

### 완료 조건 예시

```csharp
// 대쉬 1회 완료 조건
() => InputAction("Dash").WasPerformedThisFrame()

// 협동 콤보 1회 — RunData에서 확인
() => GameManager.Instance.Run.coopComboCount >= 1
```

## OnionCat 적용 포인트

| 항목 | 적용 방법 |
|------|---------|
| 말풍선 Dialogue 시스템 | 이미 구현된 `Dialogue.Say(transform, name, text, color)` 사용. 고양이 앵커 / 화분 앵커로 owner 분리 |
| 첫 런 감지 | `MetaProgress.data.tutorialDone == false` 조건 |
| 솔로/코-옵 분기 | `CoopInputLayout` 또는 패드 연결 감지 → 튜토리얼 스텝 세트 전환 |
| 튜토리얼 방 | 별도 씬 대신 **농장 시작 방에 TutorialOverlay 컴포넌트** 추가 — 방이 끝나면 비활성화 |
| 스킵 버튼 | 두 플레이어 중 하나가 Escape / Start 를 누르면 → "둘 다 괜찮으면 넘어가?" 확인 (Coop_Pause_Menu_System.md 패턴 재사용) |

## 참고 링크

- [It Takes Two — 비대칭 협동 튜토리얼 설계 사례: `Game/It_Takes_Two.md`]
- [Coop Game Session Flow: `Tech/Coop_Game_Session_Flow.md`]
- [Hybrid Split Input Onboarding: `Tech/Hybrid_SplitInput_Onboarding_Screen.md`]
- [First Run FTUE Onboarding: `Tech/First_Run_FTUE_Onboarding.md`]
- [Speech Bubble UI System: `Tech/Speech_Bubble_UI_System.md`]
