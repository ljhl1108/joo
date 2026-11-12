# 게임 내 플레이어 설문 시스템

리서치 날짜: 2026-11-12

## 개요

인디 게임 출시 전/후에 플레이어의 경험을 수치로 모으는 시스템. 게임을 종료하고 별도 설문 도구로 가는 대신, **런 종료·게임오버·처음 엔딩 도달 등의 자연스러운 타이밍에 게임 안에서 질문**을 띄운다.

OnionCat에서는 로컬 파일에만 저장하는 단순 버전으로 충분하다. 얼리 액세스·데모 버전에서 "이 방이 너무 어려웠나요?", "어느 보스에서 막혔나요?" 같은 질문으로 밸런스 데이터를 모을 수 있다.

기존 `Ingame_Playtest_Feedback`(세션 로그 자동 기록)과의 차이:
- 세션 로그 → 자동, 개발자가 직접 분석
- 플레이어 설문 → 플레이어가 직접 답변, 감정·의도 파악 가능

## 타이밍 설계

| 타이밍 | 질문 종류 | 주의 |
|---|---|---|
| 게임오버 화면 | "어디서 막히셨나요?" (보스/방/구간) | 좌절한 직후이므로 1문항 이하 |
| 엔딩 첫 클리어 | "전체 경험 점수 1~5" + 자유 텍스트 | 감정이 살아있을 때 |
| 런 종료 (클리어 or 사망) | "이번 런 난이도는?" (너무 쉬움/적당/어려움) | 매번이 아니라 N번 중 1번만 |
| 특정 기능 첫 사용 후 | "패링이 헷갈렸나요?" | 기능 튜토리얼 후 한 번만 |
| 플레이 N분 후 | NPS (0~10, 추천 의향) | 세션 시작 15분 이후 한 번만 |

**원칙**: 같은 플레이어에게 같은 질문은 한 번만. 단답형·선택형만 (텍스트 입력은 PC에서만).

## Unity 구현 방법

### 1. 데이터 구조

```csharp
[System.Serializable]
public class SurveyQuestion
{
    public string id;           // "run_difficulty", "boss_stuck" 등 고유 ID
    public string questionText; // 화면에 표시할 질문
    public SurveyType type;     // Rating5 / YesNo / MultiChoice / NPS
    public string[] choices;    // MultiChoice일 때
}

public enum SurveyType { Rating5, YesNo, MultiChoice, NPS }

[System.Serializable]
public class SurveyResponse
{
    public string questionId;
    public int answer;          // Rating5=1~5, YesNo=0/1, MultiChoice=선택 인덱스, NPS=0~10
    public string sessionId;    // 런 ID or 세션 ID
    public string timestamp;
}
```

### 2. 질문 ScriptableObject

```csharp
[CreateAssetMenu(menuName = "OnionCat/Survey/Question")]
public class SurveyQuestionAsset : ScriptableObject
{
    public SurveyQuestion question;
    [Header("표시 조건")]
    public int showAfterRunCount = 0;   // N번 런 이후부터 표시
    public bool showOncePerInstall = true;
    public string triggerEvent = "";    // "FirstClear", "GameOver", "RunEnd"
}
```

### 3. SurveyManager (싱글턴)

```csharp
public class SurveyManager : MonoBehaviour
{
    public static SurveyManager Instance { get; private set; }

    [SerializeField] private SurveyQuestionAsset[] questions;
    [SerializeField] private SurveyUI uiPrefab;

    private HashSet<string> answeredIds = new();
    private List<SurveyResponse> pendingResponses = new();
    private const string SaveKey = "survey_answered";

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        LoadAnswered();
    }

    public void TriggerEvent(string eventName)
    {
        foreach (var q in questions)
        {
            if (q.question.id != null
                && q.triggerEvent == eventName
                && !IsAnswered(q.question.id)
                && MetaProgress.Instance.TotalRunCount >= q.showAfterRunCount)
            {
                ShowQuestion(q.question);
                return; // 한 번에 한 질문만
            }
        }
    }

    private void ShowQuestion(SurveyQuestion q)
    {
        var ui = Instantiate(uiPrefab);
        ui.Setup(q, answer =>
        {
            var response = new SurveyResponse
            {
                questionId = q.id,
                answer = answer,
                sessionId = GameManager.Instance.Run.RunId,
                timestamp = System.DateTime.UtcNow.ToString("O")
            };
            pendingResponses.Add(response);
            MarkAnswered(q.id);
            SaveResponses();
        });
    }

    private bool IsAnswered(string id) => answeredIds.Contains(id);

    private void MarkAnswered(string id)
    {
        answeredIds.Add(id);
        PlayerPrefs.SetString(SaveKey, string.Join(",", answeredIds));
    }

    private void LoadAnswered()
    {
        var saved = PlayerPrefs.GetString(SaveKey, "");
        if (!string.IsNullOrEmpty(saved))
            answeredIds = new HashSet<string>(saved.Split(','));
    }

    private void SaveResponses()
    {
        // %AppData%/OnionCat/survey_responses.json에 저장
        var path = System.IO.Path.Combine(
            Application.persistentDataPath, "survey_responses.json");
        var json = JsonUtility.ToJson(new ResponseList { items = pendingResponses }, true);
        System.IO.File.WriteAllText(path, json);
    }
}
```

### 4. SurveyUI (간단한 팝업)

```csharp
public class SurveyUI : MonoBehaviour
{
    [SerializeField] private TMP_Text questionText;
    [SerializeField] private Button[] choiceButtons; // 1~5 또는 선택지 버튼

    private System.Action<int> onAnswer;

    public void Setup(SurveyQuestion q, System.Action<int> callback)
    {
        onAnswer = callback;
        questionText.text = q.questionText;

        // 버튼 세팅 (Rating5 기준)
        for (int i = 0; i < choiceButtons.Length; i++)
        {
            int idx = i;
            choiceButtons[i].gameObject.SetActive(true);
            choiceButtons[i].onClick.AddListener(() => Submit(idx + 1));
        }
    }

    private void Submit(int answer)
    {
        onAnswer?.Invoke(answer);
        Destroy(gameObject);
    }
}
```

### 5. 호출 위치

```csharp
// GameManager 또는 RunResult 화면에서
void OnRunEnd(bool cleared)
{
    string trigger = cleared ? "FirstClear" : "GameOver";
    SurveyManager.Instance.TriggerEvent(trigger);
    SurveyManager.Instance.TriggerEvent("RunEnd"); // 항상 체크
}
```

### 6. 응답 파일 읽기 (개발자용)

```python
# survey_read.py — 플레이테스트 후 결과 집계
import json, collections, glob, pathlib

files = glob.glob(str(pathlib.Path.home() / "AppData/LocalLow/*/OnionCat/survey_responses.json"))
all_responses = []
for f in files:
    data = json.load(open(f))
    all_responses.extend(data["items"])

by_question = collections.defaultdict(list)
for r in all_responses:
    by_question[r["questionId"]].append(r["answer"])

for qid, answers in by_question.items():
    avg = sum(answers) / len(answers)
    print(f"{qid}: 평균 {avg:.1f} (n={len(answers)})")
```

## OnionCat 적용 포인트

### 추천 질문 목록

| ID | 트리거 | 질문 | 타입 |
|---|---|---|---|
| `run_difficulty` | RunEnd (3런 이후, 3번 중 1번) | "이번 런 난이도는 어땠나요?" | MultiChoice (너무 쉬움/적당/어려움/너무 어려움) |
| `boss_wall` | GameOver (보스방에서 사망 시) | "보스가 너무 어려웠나요?" | YesNo |
| `coop_feel` | FirstClear | "두 명이 함께 조종하는 느낌이 재미있었나요?" | Rating5 |
| `nps` | FirstClear or 20분 플레이 | "이 게임을 친구에게 추천하시겠어요? (0~10)" | NPS |
| `parry_confusion` | 패링 첫 성공 후 3분 뒤 | "패링(반사)이 처음에 헷갈렸나요?" | YesNo |

### 주의점

- **게임오버 직후는 감정이 예민함** → 길거나 복잡한 설문 금지, 최대 1문항
- **한 세션에 최대 2개 설문** → 플레이 흐름 방해 금지
- **설문 UI는 게임 일시정지 후** (BGM 낮추기, 시간 멈추기)
- **거절 버튼 필수** ("나중에" 또는 "X" — 강제 응답 금지)
- 응답 데이터는 개발자 PC에만 저장 (외부 서버 전송 없음 → 개인정보 문제 없음)

## 참고 링크

- NPS (Net Promoter Score) 개념: https://www.netpromoter.com/know/
- 인디 게임 플레이테스트 방법: https://lostgarden.home.blog/2015/01/14/playtest-driven-development/
- Unity PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
