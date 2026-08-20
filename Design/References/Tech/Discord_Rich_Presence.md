# Discord Rich Presence Integration (디스코드 리치 프레전스)

리서치 날짜: 2026-08-20

## 개요

Discord Rich Presence는 플레이어의 Discord 상태창에 현재 게임 상황을 실시간으로 표시하는 기능. "OnionCat - 던전 3층 (공동 플레이)" 같은 상태가 친구 목록에 표시됨.

OnionCat에 적용하면:
- 협력 플레이 중임을 자동으로 Discord에 표시 → 친구들이 합류 유도
- 현재 런 상태(층수, 생존 시간, 사망 횟수) 공유 → 커뮤니티 참여 유도
- 인디 게임의 무료 홍보 효과 (스트리머/유튜버가 실시간 상태 표시 → 노출)

---

## Unity 구현 방법

### 방법 1: discord-gamesdk (공식 Discord Game SDK) — 권장

Discord 공식 C# SDK. 무료, MIT 라이선스.

#### 설정 단계

1. **Discord 개발자 포털에서 앱 생성**
   - https://discord.com/developers/applications
   - "New Application" → 게임 이름 입력 → Application ID 복사 (필요)
   - "Rich Presence" → Art Assets에 게임 아이콘/이미지 업로드 (key 이름 기록)

2. **SDK 다운로드 및 Unity에 임포트**
   - https://discord.com/developers/docs/game-sdk/sdk-starter-guide
   - `discord-game-sdk.zip` 다운로드 → `discord_game_sdk.dll` 및 `Discord.cs` 등을 `Assets/Plugins/` 폴더에 복사

3. **DiscordManager.cs 작성**

```csharp
using Discord;
using UnityEngine;

public class DiscordManager : MonoBehaviour
{
    private static DiscordManager _instance;
    public static DiscordManager Instance => _instance;

    private Discord.Discord _discord;
    private ActivityManager _activityManager;

    private const long APP_ID = 1234567890123456789L; // Discord 개발자 포털 Application ID로 교체

    private void Awake()
    {
        if (_instance != null) { Destroy(gameObject); return; }
        _instance = this;
        DontDestroyOnLoad(gameObject);

        InitDiscord();
    }

    private void InitDiscord()
    {
        try
        {
            _discord = new Discord.Discord(APP_ID, (ulong)CreateFlags.NoRequireDiscord);
            _activityManager = _discord.GetActivityManager();
        }
        catch (System.Exception e)
        {
            Debug.LogWarning($"[Discord] 초기화 실패 (Discord 미설치 가능): {e.Message}");
            _discord = null;
        }
    }

    private void Update()
    {
        _discord?.RunCallbacks(); // 매 프레임 필수 호출
    }

    private void OnDestroy()
    {
        _discord?.Dispose();
    }

    public void UpdateActivity(string details, string state, string largeImageKey = "onioncat_logo")
    {
        if (_discord == null) return;

        var activity = new Activity
        {
            Details = details,         // 메인 텍스트 (예: "던전 3층 탐험 중")
            State = state,             // 서브 텍스트 (예: "Cat & Onion | 협력 플레이")
            Assets =
            {
                LargeImage = largeImageKey,    // 개발자 포털에 업로드한 이미지 key
                LargeText = "OnionCat",
            },
            Timestamps =
            {
                Start = DateTimeOffset.UtcNow.ToUnixTimeSeconds() // 런 시작 시간
            }
        };

        _activityManager.UpdateActivity(activity, result =>
        {
            if (result != Result.Ok)
                Debug.LogWarning($"[Discord] Activity 업데이트 실패: {result}");
        });
    }

    public void ClearActivity()
    {
        if (_discord == null) return;
        _activityManager.ClearActivity(_ => { });
    }
}
```

4. **게임 상태 변경 시 호출**

```csharp
// 메인 메뉴
DiscordManager.Instance.UpdateActivity("메인 메뉴", "OnionCat");

// 런 시작
DiscordManager.Instance.UpdateActivity(
    $"던전 1층 탐험 중",
    "Cat & Onion | 협력 플레이"
);

// 층 이동
DiscordManager.Instance.UpdateActivity(
    $"던전 {currentFloor}층 탐험 중",
    $"생존 시간: {FormatTime(runTime)} | 처치: {killCount}"
);

// 게임 오버
DiscordManager.Instance.UpdateActivity("게임 오버", $"{currentFloor}층에서 쓰러짐");

// 게임 종료 or 씬 언로드 시
DiscordManager.Instance.ClearActivity();
```

---

### 방법 2: 경량 래퍼 라이브러리 (discord-rpc-csharp)

Discord 공식 SDK보다 간단한 구버전 RPC 방식. 기능은 적지만 설정이 쉬움.

- GitHub: https://github.com/Lachee/discord-rpc-csharp
- NuGet 또는 Unity Package로 임포트 가능
- 주의: 공식 Game SDK보다 오래됐고, 일부 기능 미지원

---

### 방법 3: 없어도 됨 (선택 사항)

Discord Rich Presence는 완성도 기능 → MVP에는 없어도 됨. 게임이 어느 정도 완성된 후 추가 권장.

---

## OnionCat 적용 포인트

### 표시할 상태 설계

| 게임 상태 | details (메인) | state (서브) |
|---------|--------------|-------------|
| 메인 메뉴 | "메인 메뉴" | "OnionCat" |
| 캐릭터 선택 | "캐릭터 선택 중" | "탐험을 준비 중..." |
| 던전 탐험 | "던전 {층}층 탐험 중" | "처치: {kill} / 시간: {time}" |
| 보스전 | "보스 도전 중!" | "{boss_name}과 전투" |
| 업그레이드 선택 | "업그레이드 선택" | "새 능력을 고르는 중" |
| 게임 클리어 | "클리어!" | "총 시간: {time} / 처치: {kill}" |
| 게임 오버 | "게임 오버" | "{층}층에서 쓰러짐" |

### 구현 우선순위 (초보 개발자)
1. **1순위**: 던전 탐험 중 상태만 표시 (한 줄이면 충분)
2. **2순위**: 메인 메뉴 / 게임 오버 상태 추가
3. **3순위**: 보스전, 클리어 등 세부 상태 추가

### 에러 방지
- Discord가 설치 안 된 환경에서도 게임이 정상 실행되어야 함.
- `try-catch`로 초기화 실패 시 `_discord = null` 처리 후 이후 Update에서 `_discord?.RunCallbacks()` null 체크로 안전하게 건너뜀.
- 빌드 전 Discord SDK DLL이 `Assets/Plugins/` 안에 있는지 확인 (x86/x86_64 구분 주의).

### 씬 전환 시 상태 업데이트
- `SceneManager.sceneLoaded` 이벤트에 구독 → 씬 변경마다 자동 업데이트 가능.

```csharp
private void Start()
{
    SceneManager.sceneLoaded += OnSceneLoaded;
}

private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
{
    switch (scene.name)
    {
        case "MainMenu": UpdateActivity("메인 메뉴", "OnionCat"); break;
        case "Dungeon": UpdateActivity("던전 탐험 중", "Cat & Onion"); break;
    }
}
```

---

## 참고 링크

- Discord 개발자 포털: https://discord.com/developers/applications
- Discord Game SDK 공식 문서: https://discord.com/developers/docs/game-sdk/sdk-starter-guide
- Discord Game SDK C# 예제: https://github.com/discord/discord-api-docs/tree/main/examples
- discord-rpc-csharp (경량 버전): https://github.com/Lachee/discord-rpc-csharp
- Unity에서 Discord SDK 연동 튜토리얼: "Unity Discord Rich Presence tutorial" YouTube 검색
