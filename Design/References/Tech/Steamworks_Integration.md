# Steamworks 기초 연동 (Steam SDK Integration)

리서치 날짜: 2026-07-18

## 개요

Steam에 게임을 출시할 계획이라면 **Steamworks SDK**를 Unity에 연동해야 한다. 업적(Achievement), 통계(Stats), 클라우드 세이브(Cloud Save), Steam 입력(Steam Input) 등 Steam 플랫폼 기능을 게임에 추가할 수 있다. 초심자 기준으로는 **Steamworks.NET** 래퍼 패키지가 가장 접근하기 쉽다.

OnionCat 기준: 스팀 출시를 목표로 할 때 업적 시스템, 기본 통계 저장, 클라우드 세이브를 연동하는 것이 최소 요구 사항.

---

## 준비 사항

1. **Steamworks 개발자 계정**: https://partner.steamgames.com/ (등록비 $100 USD)
2. **AppID 발급**: Steamworks 대시보드에서 앱 생성 후 AppID 받기
3. **steam_appid.txt**: 프로젝트 루트에 AppID를 적은 텍스트 파일 (테스트용)
4. **Steamworks.NET 설치**: https://github.com/rlabrecque/Steamworks.NET

---

## Unity 구현 방법

### Step 1: Steamworks.NET 설치

**방법 A — Package Manager (권장)**
```
Window > Package Manager > Add package from git URL
https://github.com/rlabrecque/Steamworks.NET.git?path=/com.rlabrecque.steamworks.net
```

**방법 B — unitypackage 직접 다운로드**
- https://github.com/rlabrecque/Steamworks.NET/releases 에서 최신 `.unitypackage` 다운로드 후 임포트

---

### Step 2: SteamManager 설정 (자동 제공 스크립트 활용)

Steamworks.NET은 `SteamManager.cs` 예제를 제공한다. 이것을 씬의 빈 오브젝트에 부착.

```csharp
// SteamManager는 Steamworks.NET 패키지에 포함된 예제 스크립트
// Samples/ 폴더에서 가져옴
// DontDestroyOnLoad로 씬 전환에도 유지됨
```

`steam_appid.txt`를 Unity 프로젝트 루트(Assets 폴더 옆)에 생성:
```
480
```
(480은 Valve의 테스트 AppID — 실제 출시 시 본인 AppID로 교체)

---

### Step 3: SteamAPI 초기화 확인

```csharp
using Steamworks;

public class GameManager : MonoBehaviour
{
    private void Start()
    {
        if (!SteamAPI.Init())
        {
            Debug.LogError("Steam API 초기화 실패. Steam 클라이언트가 실행 중인지 확인하세요.");
            // 스팀 없이도 게임이 돌아가도록 graceful fallback 처리
        }
        else
        {
            Debug.Log($"Steam 연결 성공. 유저: {SteamFriends.GetPersonaName()}");
        }
    }

    private void OnDestroy()
    {
        SteamAPI.Shutdown();
    }
}
```

---

### Step 4: 업적(Achievement) 구현

```csharp
public static class SteamAchievements
{
    // Steamworks 대시보드에서 설정한 업적 API 이름
    private const string ACH_FIRST_RUN   = "ACH_FIRST_RUN";
    private const string ACH_KILL_100    = "ACH_KILL_100";
    private const string ACH_CLEAR_RUN   = "ACH_CLEAR_RUN";

    public static void UnlockAchievement(string achievementId)
    {
        if (!SteamManager.Initialized) return;

        SteamUserStats.SetAchievement(achievementId);
        SteamUserStats.StoreStats(); // 반드시 StoreStats() 호출해야 서버에 저장
        Debug.Log($"업적 해금: {achievementId}");
    }

    public static bool IsAchievementUnlocked(string id)
    {
        if (!SteamManager.Initialized) return false;
        SteamUserStats.GetAchievement(id, out bool achieved);
        return achieved;
    }
}

// 사용 예시
// 첫 런 시작 시:
SteamAchievements.UnlockAchievement("ACH_FIRST_RUN");
```

---

### Step 5: 통계(Stats) 저장

```csharp
public static class SteamStats
{
    public static void AddKillCount(int kills)
    {
        if (!SteamManager.Initialized) return;
        SteamUserStats.GetStat("total_kills", out int current);
        SteamUserStats.SetStat("total_kills", current + kills);
        SteamUserStats.StoreStats();
    }

    public static void AddRunCount()
    {
        if (!SteamManager.Initialized) return;
        SteamUserStats.GetStat("total_runs", out int current);
        SteamUserStats.SetStat("total_runs", current + 1);
        SteamUserStats.StoreStats();
    }
}
```

---

### Step 6: 클라우드 세이브 (Steam Cloud)

Steamworks 대시보드에서 Cloud Save를 활성화하면, `Application.persistentDataPath`에 저장된 파일이 자동으로 동기화된다. 별도 코드 필요 없음.

수동 동기화가 필요한 경우:
```csharp
// 파일 쓰기
using var file = SteamRemoteStorage.FileWrite("save.json");
file.Write(System.Text.Encoding.UTF8.GetBytes(jsonData));

// 파일 읽기
if (SteamRemoteStorage.FileExists("save.json"))
{
    int size = SteamRemoteStorage.GetFileSize("save.json");
    byte[] buffer = new byte[size];
    SteamRemoteStorage.FileRead("save.json", buffer, size);
    string json = System.Text.Encoding.UTF8.GetString(buffer);
}
```

---

### Step 7: 스팀 오버레이 (Steam Overlay)

Steam 오버레이(Shift+Tab)는 자동으로 활성화됨. 오버레이 안에서 UI 표시 방지:

```csharp
// 오버레이 열림/닫힘 콜백
private Callback<GameOverlayActivated_t> _overlayCallback;

private void Start()
{
    _overlayCallback = Callback<GameOverlayActivated_t>.Create(OnOverlayActivated);
}

private void OnOverlayActivated(GameOverlayActivated_t pCallback)
{
    bool isOpen = pCallback.m_bActive != 0;
    Time.timeScale = isOpen ? 0f : 1f; // 오버레이 열리면 일시정지
}
```

---

### Step 8: 빌드 시 주의사항

1. `steam_appid.txt`를 빌드 폴더에 함께 복사 (빌드 후 자동 복사 안 됨)
2. `steam_api64.dll` / `libsteam_api.so` 가 빌드에 포함되어야 함 (Steamworks.NET이 자동 처리)
3. **Steam 클라이언트가 실행 중**이어야 테스트 가능
4. 실제 AppID로 교체 후 Steamworks 대시보드에서 업적/통계 API 이름 설정 필요

---

## OnionCat 적용 포인트

### 최소 구현 (출시 기준)

| 기능 | 구현 내용 | 우선순위 |
|------|-----------|---------|
| SteamAPI.Init() | 게임 시작 시 초기화 | 필수 |
| 업적 5~10개 | 첫 런, 첫 클리어, 적 100마리 처치, 2인 플레이 완료 등 | 필수 |
| 통계 저장 | 총 처치 수, 런 횟수, 총 플레이 시간 | 권장 |
| Steam Cloud | persistentDataPath 자동 동기화 | 권장 |
| 오버레이 일시정지 | Shift+Tab 시 게임 멈춤 | 권장 |

### OnionCat 업적 아이디어

```
ACH_FIRST_RUN        — 첫 번째 런 시작
ACH_FIRST_CLEAR      — 첫 번째 런 클리어
ACH_COOP_CLEAR       — 2인 협력으로 클리어
ACH_MELEE_ONLY_ROOM  — 근접만으로 방 클리어
ACH_RANGE_ONLY_ROOM  — 원거리만으로 방 클리어
ACH_KILL_100         — 처치 수 100
ACH_KILL_1000        — 처치 수 1000
ACH_PARRY_10         — 패리 10회 성공
ACH_DASH_BOSS        — 보스에게 대시로 무적 통과
ACH_NO_HIT_RUN       — 피격 없이 첫 층 클리어
```

### 구현 순서 추천 (초심자)

1. Steamworks.NET 설치 + SteamManager.cs 씬 추가
2. `steam_appid.txt` (480) 로 테스트
3. 업적 2~3개 코드 연동 테스트
4. Steamworks 대시보드에서 실제 AppID + 업적 설정
5. Cloud Save 활성화 (대시보드 체크박스)
6. 빌드 후 Steam에 업로드 (Steamcmd 또는 Steamworks 웹 업로드)

### Steam 없이도 게임이 동작해야 함

```csharp
// Steam 연동 실패해도 게임 진행 가능하도록
if (SteamManager.Initialized)
    SteamAchievements.UnlockAchievement("ACH_FIRST_RUN");
// 실패해도 예외 던지지 않음
```

---

## 참고 링크

- Steamworks.NET 공식: https://steamworks.github.io/
- Steamworks.NET GitHub: https://github.com/rlabrecque/Steamworks.NET
- Steamworks 개발자 문서: https://partner.steamgames.com/doc/sdk
- 업적 설계 가이드: https://partner.steamgames.com/doc/features/achievements
- Unity + Steam 튜토리얼 (Dawnosaur): https://www.youtube.com/watch?v=TnHuMWeTKMQ
- Steamworks 업적 Unity 예제: https://partner.steamgames.com/doc/features/achievements/ach_howto
