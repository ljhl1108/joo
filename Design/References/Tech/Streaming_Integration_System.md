# Streaming Integration System

리서치 날짜: 2026-10-05

## 개요

인디 게임의 성장에서 스트리밍(Twitch, YouTube Live, SOOP 등)은 핵심 마케팅 채널이다. "스트리머 친화적" 게임이 되려면 단순히 "재미있어 보이는 것" 이상이 필요하다. Twitch Extensions, 채팅 투표 연동, 자동 클립 추천 구간 등을 설계 단계에서 고려하면 유기적 홍보 효과가 크다.

OnionCat은 2인 협동 로그라이크 — 스트리머 + 시청자 투표로 업그레이드를 선택하거나, 시청자가 적을 소환하는 등 인터랙티브 방식으로 확장 가능하다.

## 핵심 개념

### 1. 스트리머 친화적 설계 (Streamer Mode)
코드 없이도 가능한 최소한의 배려:
- **스포일러 없는 로딩 화면**: 스트리머가 씬 전환 중 해설할 시간
- **사망 시 BGM 컷 없이 자연스럽게 fade**: 클립 구간에서 DMCA 위험 최소화
- **승리/패배 리플레이 화면**: "클립 구간" 제공 (Run_Result_Screen)
- **화면 비율 대응**: 21:9 울트라와이드, 스트림덱 4:3에서 UI가 안 잘림 (Multi_Resolution_UI_System)

### 2. Twitch Channel Points / Predictions 연동
**WebSocket 기반 접근** (OAuth 없이 채팅 읽기):

```
채팅 → IRC over WebSocket → 게임 내 이벤트
wss://irc-ws.chat.twitch.tv:443
```

기본 흐름:
1. 스트리머가 Twitch 채팅 명령어 설정 (예: !vote A, !vote B)
2. 게임이 WebSocket으로 채팅 메시지 수신
3. 업그레이드 선택 화면에서 투표 결과 반영

### 3. Twitch Extensions (심화)
실제 오버레이로 구현하려면 Twitch Developer Console에 앱 등록 필요:
- Extensions는 HTML/JS iframe — Unity와는 HTTP API로 통신
- Unity 게임 서버 → Twitch EBS(Extension Backend Service) → Extensions UI
- 복잡도 높음 → 인디 단계에서는 채팅 IRC 접근으로 충분

## Unity 구현 방법

### 기본 Twitch 채팅 연결

```csharp
using System.Net.WebSockets;
using System.Threading;
using UnityEngine;

public class TwitchChatListener : MonoBehaviour {
    [SerializeField] string channelName = "your_channel";
    ClientWebSocket _ws;
    CancellationTokenSource _cts;

    async void Start() {
        _ws = new ClientWebSocket();
        _cts = new CancellationTokenSource();
        var uri = new System.Uri("wss://irc-ws.chat.twitch.tv:443");
        await _ws.ConnectAsync(uri, _cts.Token);

        // 익명 로그인 (채팅 읽기 전용)
        await Send("PASS oauth:justinfan12345");
        await Send("NICK justinfan12345");
        await Send($"JOIN #{channelName.ToLower()}");

        _ = ListenLoop();
    }

    async System.Threading.Tasks.Task ListenLoop() {
        var buffer = new byte[4096];
        while (_ws.State == WebSocketState.Open) {
            var result = await _ws.ReceiveAsync(buffer, _cts.Token);
            string msg = System.Text.Encoding.UTF8.GetString(buffer, 0, result.Count);
            if (msg.StartsWith("PING")) await Send("PONG :tmi.twitch.tv");
            ParseChat(msg);
        }
    }

    void ParseChat(string raw) {
        // 형식: ":user!user@user.tmi.twitch.tv PRIVMSG #channel :message"
        if (!raw.Contains("PRIVMSG")) return;
        int msgStart = raw.IndexOf(" :", raw.IndexOf("PRIVMSG")) + 2;
        string message = raw.Substring(msgStart).Trim();
        // 투표 처리
        if (message == "!1" || message == "!A") VoteManager.Instance.Vote(0);
        else if (message == "!2" || message == "!B") VoteManager.Instance.Vote(1);
        else if (message == "!3" || message == "!C") VoteManager.Instance.Vote(2);
    }

    async System.Threading.Tasks.Task Send(string text) {
        var bytes = System.Text.Encoding.UTF8.GetBytes(text + "\r\n");
        await _ws.SendAsync(bytes, WebSocketMessageType.Text, true, _cts.Token);
    }

    void OnDestroy() {
        _cts?.Cancel();
        _ws?.Dispose();
    }
}
```

### 투표 관리자

```csharp
public class VoteManager : MonoBehaviour {
    public static VoteManager Instance;
    int[] votes = new int[3];
    bool voting;

    void Awake() => Instance = this;

    public void StartVote() {
        votes = new int[3];
        voting = true;
    }

    public void Vote(int index) {
        if (!voting || index >= votes.Length) return;
        votes[index]++;
        OnVoteUpdated?.Invoke(votes); // UI 갱신
    }

    public int EndVoteAndGetWinner() {
        voting = false;
        int maxIdx = 0;
        for (int i = 1; i < votes.Length; i++)
            if (votes[i] > votes[maxIdx]) maxIdx = i;
        return maxIdx;
    }

    public event System.Action<int[]> OnVoteUpdated;
}
```

### 업그레이드 선택 화면 연동

```csharp
// UpgradeSelectUI.cs 에 추가
void ShowUpgradeChoices(List<BaseReward> choices) {
    // ... 기존 카드 표시 코드 ...

    if (TwitchChatListener 존재) {
        VoteManager.Instance.StartVote();
        timerCoroutine = StartCoroutine(VoteTimer(15f, choices));
        // 화면에 "채팅에 !1 !2 !3 입력으로 투표!" 표시
    }
}

IEnumerator VoteTimer(float seconds, List<BaseReward> choices) {
    yield return new WaitForSeconds(seconds);
    int winner = VoteManager.Instance.EndVoteAndGetWinner();
    SelectReward(choices[winner]);
}
```

### OBS WebSocket 연동 (선택)
OBS 4.x: obs-websocket 플러그인  
OBS 28+: WebSocket 내장 (포트 4455, 기본 비밀번호 없음)

```csharp
// 게임 클리어 시 자동으로 "하이라이트 마커" 추가
async Task SetObsMarker(string name) {
    // OBS WebSocket JSON-RPC
    string payload = $"{{\"op\":6,\"d\":{{\"requestType\":\"CreateSceneItem\",\"requestId\":\"1\",...}}}}";
    await obsWs.SendAsync(payload); // 보스 처치, 런 클리어 등 주요 이벤트에 마커
}
```

## OnionCat 적용 포인트

### 즉시 적용 가능 (코드 없이)

1. **스트리머 모드 ON/OFF 설정 옵션** 추가 (Settings_Menu)
   - "시청자 투표 업그레이드": UpgradeSelectUI에 15초 타이머 + 투표 UI
   - "채팅 소환": 처치 시 일정 확률로 채팅에서 이름 딴 적 등장 (이름 TMP 텍스트로 표시)

2. **DMCA 세이프 모드**: 배경음악 볼륨을 0으로 내리는 단축키 (Music.SetVolume)
   - Audio_System.md의 AudioMixer Group 볼륨 제어 활용

3. **"Clip This!" 알림 구간 설계**: 보스 처치, 협동 콤보 성공 시 화면 테두리 플래시 (시청자가 알아보기 쉽게)

### 중기 구현 (v1.1 이후)

4. **Twitch IRC 투표 업그레이드**: 위 코드 기반, UpgradeSelectUI에 투표 수 표시
5. **시청자 참여 이벤트**: "100명 응원 시 보스 체력 -10%" 같은 임시 이벤트
6. **스트림 오버레이 URL**: 게임 내 상태를 로컬 HTTP(localhost:port)로 노출 → OBS 브라우저 소스로 표시

### 한국 스트리밍 플랫폼 (SOOP, 치지직)
- **치지직 (Chzzk)**: NAVER 제공, API 비공개(비공식 라이브러리 존재)
- **SOOP (구 아프리카)**: IRC 프로토콜 없음, REST API 있음
- 초기에는 Twitch IRC만 지원, 나중에 플랫폼별 어댑터 패턴으로 확장

```csharp
// 어댑터 패턴 예시
public interface IStreamingPlatform {
    void Connect(string channel);
    event System.Action<string> OnChatMessage;
}
public class TwitchPlatform : IStreamingPlatform { ... }
public class ChzzkPlatform : IStreamingPlatform { ... } // 나중에
```

## 스트리머 친화 체크리스트

- [ ] 설정에서 "스트리머 모드" ON/OFF
- [ ] 런 시작 시 3초 카운트다운 (카메라가 준비되는 시간)
- [ ] 보스 처치 / 런 클리어 애니메이션 충분히 긺 (5~8초)
- [ ] 런 결과 화면에 통계 수치 표시 (처치 수, 클리어 시간 → "클립 캡션" 역할)
- [ ] 21:9 해상도에서 UI 잘리지 않음
- [ ] 음악 저작권 확인 완료 (현재 CC0 음원 사용 중 — 안전)
- [ ] 게임 제목 + 개발사 로고가 화면에 항상 보임 (스트리머가 제목 묻는 질문에 자동 답변)

## 참고 링크

- [Twitch IRC Guide](https://dev.twitch.tv/docs/irc/)
- [OBS WebSocket Protocol](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md)
- [Unity WebSocket (NativeWebSocket)](https://github.com/endel/NativeWebSocket)
- [치지직 비공식 API](https://github.com/kimcore/chzzk)
- [Making Your Game Streamer Friendly - GDC 2019](https://www.gdcvault.com/)
