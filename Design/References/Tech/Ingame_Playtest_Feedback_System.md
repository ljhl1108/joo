# 인게임 플레이테스트 피드백 수집 시스템

리서치 날짜: 2026-10-23

## 개요

플레이어(또는 플레이테스터)가 게임을 하는 도중·직후에 **게임 안에서 직접 피드백을 남길 수 있는 시스템**.  
별도 설문 도구(Google Forms 등)로 이동하지 않고 인게임 팝업으로 처리하는 것이 요점.

인디 개발자가 스팀 출시 전 폐쇄 베타·Next Fest 데모 기간에 특히 유용하다.  
OnionCat은 현재 직접 지인 플레이테스트 단계인데, 플레이가 끝난 직후에 "어땠어요?" 팝업 하나만 있어도 수집 품질이 크게 달라진다.

---

## Unity 구현 방법

### 1. 피드백 데이터 구조

```csharp
[System.Serializable]
public class PlaytestFeedback
{
    public string sessionId;        // GUID (플레이어 식별용)
    public string version;          // Application.version
    public long timestamp;          // DateTimeOffset.UtcNow.ToUnixTimeSeconds()
    public int runResult;           // 0=죽음, 1=클리어, 2=중단
    public int overallRating;       // 1~5
    public int difficultyRating;    // 1=너무 쉬움, 5=너무 어려움
    public string freeText;         // 자유 의견 (최대 500자)
    public string lastRoomReached;  // DungeonManager.currentRoom
}
```

---

### 2. 팝업 트리거 조건

```csharp
public class FeedbackTrigger : MonoBehaviour
{
    private void OnEnable()
    {
        GameManager.OnStateChanged += OnStateChanged;
    }
    private void OnDisable()
    {
        GameManager.OnStateChanged -= OnStateChanged;
    }

    private void OnStateChanged(GameState state)
    {
        // 런이 끝난 직후(사망·클리어)에 피드백 팝업
        if (state == GameState.GameOver || state == GameState.Victory)
        {
            // 매번 뜨지 않게: 오늘 이미 보냈으면 스킵
            if (!HasSubmittedToday())
                FeedbackUI.Instance.Show();
        }
    }

    private bool HasSubmittedToday()
    {
        string key = "feedback_date";
        string saved = PlayerPrefs.GetString(key, "");
        return saved == DateTime.Today.ToString("yyyy-MM-dd");
    }
}
```

---

### 3. 피드백 UI (Canvas Overlay)

```csharp
public class FeedbackUI : MonoBehaviour
{
    [SerializeField] private Slider overallSlider;
    [SerializeField] private Slider difficultySlider;
    [SerializeField] private TMP_InputField freeTextField;
    [SerializeField] private Button submitBtn;
    [SerializeField] private Button skipBtn;

    public void Show()
    {
        gameObject.SetActive(true);
        Time.timeScale = 0f; // 게임 정지 (피드백 읽는 동안)
    }

    public void Submit()
    {
        var data = new PlaytestFeedback
        {
            sessionId = GetOrCreateSessionId(),
            version = Application.version,
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
            overallRating = (int)overallSlider.value,
            difficultyRating = (int)difficultySlider.value,
            freeText = freeTextField.text.Substring(0, Mathf.Min(500, freeTextField.text.Length))
        };

        FeedbackSender.Send(data);
        MarkSubmittedToday();
        Hide();
    }
}
```

---

### 4. 데이터 저장 및 전송

#### 4-a. 로컬 JSON 저장 (오프라인 / 빌드 테스트용)

```csharp
public static class FeedbackSender
{
    public static void Send(PlaytestFeedback data)
    {
        string json = JsonUtility.ToJson(data, prettyPrint: true);
        string path = Path.Combine(Application.persistentDataPath,
            $"feedback_{data.timestamp}.json");
        File.WriteAllText(path, json);
    }
}
```

`Application.persistentDataPath` 위치 (Windows): `%AppData%\..\LocalLow\[Company]\[Game]\`

#### 4-b. 웹훅 전송 (Discord / Google Sheets)

```csharp
public static IEnumerator SendToWebhook(PlaytestFeedback data, string webhookUrl)
{
    string json = JsonUtility.ToJson(data);
    byte[] body = System.Text.Encoding.UTF8.GetBytes(json);
    
    using var req = new UnityWebRequest(webhookUrl, "POST");
    req.uploadHandler = new UploadHandlerRaw(body);
    req.downloadHandler = new DownloadHandlerBuffer();
    req.SetRequestHeader("Content-Type", "application/json");
    
    yield return req.SendWebRequest();
    // 전송 실패 시 로컬 파일로 폴백
    if (req.result != UnityWebRequest.Result.Success)
        FeedbackSender.Send(data);
}
```

**Discord 웹훅**이 가장 간편: Webhook URL 하나만 있으면 `#feedback` 채널로 바로 쌓인다.

```json
// Discord 웹훅용 payload 형태
{
  "content": "⭐ 4/5 | 난이도 3/5 | v0.8.1",
  "embeds": [{
    "description": "2스테이지까지 갔는데 보스가 너무 강함. 패링 타이밍 더 길었으면",
    "footer": { "text": "2026-10-23 | session:abc123" }
  }]
}
```

---

### 5. 수집 데이터 분석

로컬 JSON이 여러 개 쌓이면 Python으로 집계:

```python
import json, glob
feedbacks = [json.load(open(f)) for f in glob.glob("feedback_*.json")]
avg_rating = sum(f["overallRating"] for f in feedbacks) / len(feedbacks)
print(f"평균 평점: {avg_rating:.1f}")
# freeText만 모아서 텍스트 분석
texts = [f["freeText"] for f in feedbacks if f["freeText"]]
```

---

## OnionCat 적용 포인트

### 즉시 적용 가능한 최소 구현

1. **런 종료 시 팝업** (GameState.GameOver/Victory 이벤트)
2. **평점 슬라이더** (전체 재미 1~5 + 난이도 1~5, 두 가지만)
3. **자유 의견 한 줄** (TMP_InputField, 최대 200자)
4. **로컬 JSON 저장** (플레이테스터의 `persistentDataPath`에 자동 저장)

### 플레이테스트에서 수집하면 좋은 항목

| 항목 | 질문 예시 | 측정 목적 |
|------|-----------|-----------|
| 전체 재미 | "재미는 몇 점?" (1~5) | 전반적 만족도 |
| 난이도 | "난이도는?" (1=너무 쉬움 ~ 5=너무 어려움) | 밸런스 |
| 협동 만족도 | "둘이 하는 재미가 있었나요?" (1~5) | 코옵 핵심 가치 |
| 어디까지 갔는지 | 자동 기록 (`DungeonManager.stagePlan` 진행도) | 이탈 지점 파악 |
| 자유 의견 | "불편한 점 / 기억에 남는 순간" | 정성 데이터 |

### 발동 조건 권장

| 조건 | 팝업 시점 | 이유 |
|------|-----------|------|
| 첫 런 종료 | GameOver / Victory | 첫인상이 가장 중요한 데이터 |
| 5번째 런마다 | 런 종료 시 | 반복 플레이 후 인식 변화 |
| 보스 첫 처치 | Victory 직후 | 주요 마일스톤 이후 감정이 살아있을 때 |
| 빌드 다운로드 후 처음 1시간 | 시간 기반 | 데모 기간 피드백 집중 수집 |

### 개발자용 피드백 뷰어 (선택)

```csharp
[MenuItem("OnionCat/Open Feedback Folder")]
static void OpenFeedbackFolder()
{
    Application.OpenURL(Application.persistentDataPath);
}
```

Unity 에디터 메뉴에서 바로 폴더를 열어 JSON을 확인.

### 주의사항

- **개인정보 없는 수집**: 이름·이메일은 수집하지 않음. `sessionId`는 게임이 자동 생성한 GUID
- **팝업 강제 아님**: 반드시 "건너뛰기" 버튼 제공. 강제 피드백은 데이터 품질 저하
- **버전 태그 필수**: `Application.version` 을 항상 포함 → 버전별 점수 변화 추적 가능

---

## 참고 링크

- Unity persistentDataPath 문서: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Discord 웹훅 가이드: https://discord.com/developers/docs/resources/webhook
- Google Sheets Apps Script 수신 예제: https://developers.google.com/apps-script/guides/web
- UnityWebRequest POST: https://docs.unity3d.com/ScriptReference/Networking.UnityWebRequest.Post.html
- 인디 플레이테스트 피드백 설계 글: https://howtomarketagame.com/2021/01/25/how-to-run-a-great-playtest/
