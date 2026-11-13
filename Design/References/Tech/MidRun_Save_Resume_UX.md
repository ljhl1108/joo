# 런 중간 나가기 & 이어하기 UX 흐름

리서치 날짜: 2026-11-13

## 개요

로그라이크에서 중간 저장(mid-run save)은 단순히 데이터를 파일에 쓰는 것이 아니다. **"지금 나가면 어떻게 되나요?"**에 대한 플레이어의 불안을 해소하는 UX 흐름 전체가 중요하다. 특히 2인 협동 게임에서는 한 명이 나가고 싶을 때, 다른 한 명은 계속하고 싶을 때를 처리해야 한다. OnionCat은 이미 중간 저장을 구현했으므로 이 파일은 UX 흐름 개선에 초점을 맞춘다.

---

## 중간 나가기 UX 패턴 분석

### 패턴 1: 명시적 "런 저장 후 종료" (Hades, Rogue Legacy 2)
- 일시정지 메뉴에 **"저장 후 메인 메뉴로"** 버튼이 별도 존재
- 이 버튼을 누르면 "현재 진행이 저장됩니다. 다음 실행 시 이어서 플레이할 수 있습니다." 확인 대화상자
- **단, 같은 세이브 슬롯에 하나의 런만 존재** — 이미 중간 저장이 있으면 덮어씀

```
[ 저장 후 종료 ] → "현재 런을 저장하고 종료합니까? (저장 1건만 유지)" → [확인] [취소]
```

### 패턴 2: 자동 저장 + 출구 도착 시 체크포인트 (Dead Cells, Hades)
- 방 사이 이동할 때마다 자동 저장 → 플레이어가 신경 쓰지 않아도 됨
- 갑자기 꺼도 마지막 방 입장 시점부터 재개
- 주의: 방 안에서 꺼지면 방 초기 상태로 돌아가야 하므로 적 상태는 저장 안 함

### 패턴 3: 2인 협동 "합의 종료" (It Takes Two, Children of Morta)
- 한 명이 나가기를 요청하면 다른 한 명에게 알림
- 양쪽 모두 확인하면 저장 후 종료
- **한 명만 확인하면 타임아웃(10~30초) 후 호스트 판단**
- 중요: "런 버리고 나가기"와 "런 저장 후 나가기"를 명확히 구분

---

## Unity 구현 흐름 (OnionCat 기준)

### 1. 일시정지 메뉴에서 나가기 흐름

```csharp
// PauseMenu.cs
void OnExitButtonPressed() {
    if (IsMidRun()) {
        // 2인 합의가 필요하면: CoopExitVoteUI 열기
        // 1인 모드라면: 바로 확인 대화상자
        ShowSaveAndExitConfirmation();
    } else {
        // 런 없으면 그냥 메인 메뉴
        SceneManager.LoadScene(SceneNames.MainMenu);
    }
}

void ShowSaveAndExitConfirmation() {
    DialogueUI.Show(
        message: "현재 런을 저장하고 나가시겠습니까?",
        confirm: SaveAndGoToMainMenu,
        confirmLabel: "저장 후 나가기",
        cancel: null,
        cancelLabel: "계속하기",
        danger: "런 버리고 나가기",   // 빨간 텍스트
        dangerAction: AbandonAndExit
    );
}
```

### 2. 런 저장 데이터 구조 (최소한으로)

```csharp
[Serializable]
public class MidRunSaveData {
    public string stagePlan;          // 남은 방 순서 (DungeonManager.stagePlan)
    public int currentRoomIndex;
    public RunData runData;           // 장비·스킬·게이지 등
    public float sharedHp;
    public float sharedShieldCount;
    public long savedAtTick;          // DateTime.Ticks — 세이브 시각
}

// 저장
string json = JsonUtility.ToJson(saveData);
File.WriteAllText(MidRunSavePath, json);

// 세이브 경로: 방 사이에서만 저장 (방 안은 저장 안 함)
static string MidRunSavePath => 
    Path.Combine(Application.persistentDataPath, "midrun.json");
```

### 3. 게임 시작 시 이어하기 감지

```csharp
// MainMenu.cs
void Start() {
    if (File.Exists(MidRunSavePath)) {
        // "이어하기" 버튼 활성화 + 세이브 정보 표시
        ShowContinuePrompt(LoadMidRunInfo());
    }
}

void ShowContinuePrompt(MidRunSaveData info) {
    // "저장된 런이 있습니다 — 스테이지 2, 방 4/8, 7일 전"
    continueButton.gameObject.SetActive(true);
    continueLabel.text = $"이어하기 — 스테이지 {info.stageNumber}, {TimeSince(info.savedAtTick)} 전";
}
```

### 4. "런 버리고 나가기" 처리

```csharp
void AbandonAndExit() {
    // 1. 세이브 파일 삭제 (이어하기 없음)
    if (File.Exists(MidRunSavePath))
        File.Delete(MidRunSavePath);
    
    // 2. 메타 진행도는 유지 (온실 해금 등은 사라지지 않음)
    // 3. 메인 메뉴로
    GameManager.Instance.ChangeState(GameState.MainMenu);
}
```

### 5. 2인 합의 종료 UI (CoopExitVote)

```
상태: P1(고양이)가 나가기 요청 → P2(양파)에게 "P1이 나가길 원합니다" 표시
P2: [같이 저장하고 나가기] [계속하기]
타임아웃 10초: 응답 없으면 P1(호스트) 판단으로 저장 종료
```

```csharp
IEnumerator CoopExitVote() {
    ShowVoteUI(); // 양파 플레이어 화면에 투표 UI
    float elapsed = 0;
    while (elapsed < 10f) {
        if (_p2AcceptedExit) { yield return SaveAndExit(); yield break; }
        if (_p2DeclinedExit) { HideVoteUI(); yield break; }
        elapsed += Time.unscaledDeltaTime;
        yield return null;
    }
    // 타임아웃: P1(호스트) 결정 그대로
    yield return SaveAndExit();
}
```

---

## UX 디자인 원칙 체크리스트

```
[ ] "저장 후 나가기"와 "런 버리기"를 항상 구분 — 버려도 괜찮다는 걸 명확히 안내
[ ] 저장 중 로딩 스피너 표시 (0.5초라도) — "저장됐다"는 확신을 줌
[ ] 이어하기 버튼에 세이브 정보(언제, 어디까지) 표시
[ ] 세이브 파일이 손상됐을 때 복구 불가 메시지 + 삭제 옵션
[ ] 런 중간에 앱 종료(Alt+F4, 배터리 사망)되면: 방 사이 자동 저장 덕에 마지막 방 초기 상태로 복구
[ ] 메타 진행도(온실 해금, MetaProgress)는 런 결과와 무관하게 별도 파일에 즉시 저장
```

---

## OnionCat 현재 구현 대비 개선 포인트

| 항목 | 현재 | 개선 아이디어 |
|------|------|--------------|
| 저장 시점 | 중간 저장 있음 (10-10 구현) | 방 입장마다 자동 저장으로 개선 가능 |
| 나가기 UI | 미확인 | "런 버리기 / 저장 후 나가기" 2단계 버튼 추가 |
| 이어하기 화면 | 미확인 | 메인 메뉴에 세이브 정보 표시 |
| 2인 합의 | 미확인 | 로컬 2인이라 1인 결정으로 단순화해도 무방 |

---

## 참고 링크
- Hades 세이브 시스템 분석 (How Hades Handles Mid-Run Save): https://www.gamedeveloper.com/design/how-hades-handles-saves
- Unity Application.persistentDataPath 공식 문서: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Game UX Research - Save/Load Patterns: https://uxplanet.org/game-ux-the-importance-of-save-game-ux-9f2a3c58a9f1
- JSON 직렬화 (JsonUtility): https://docs.unity3d.com/ScriptReference/JsonUtility.html
