# Error Log & Crash Report System (오류 로그 및 크래시 처리 시스템)

리서치 날짜: 2026-09-30

## 개요

인디 게임을 출시할 때 플레이어 머신에서 발생하는 예외/크래시를 파악하는 시스템.
개발 중에는 Unity Console로 충분하지만, **빌드 배포 후에는 직접 로그를 수집해야** 버그를 잡을 수 있다.

OnionCat처럼 2인 협동이 있는 게임은 특히 입력 분기에서 NullRef가 자주 터지므로,
빌드에서도 예외를 파일로 기록하는 최소 시스템을 갖춰두면 QA 비용이 크게 줄어든다.

## Unity 구현 방법

### 1. Application.logMessageReceived 후킹

Unity는 빌드 환경에서도 `Application.logMessageReceived` 이벤트를 제공한다.
이를 이용해 Error / Exception 레벨 로그를 파일로 저장한다.

```csharp
// GameLogger.cs — Bootstrap 씬에서 Awake에 등록, DontDestroyOnLoad
using System;
using System.IO;
using UnityEngine;

public class GameLogger : MonoBehaviour
{
    private static string logPath;
    private static StreamWriter writer;

    void Awake()
    {
        logPath = Path.Combine(Application.persistentDataPath, "game_log.txt");
        writer = new StreamWriter(logPath, append: false);  // 매 실행마다 덮어씀
        writer.AutoFlush = true;

        writer.WriteLine($"=== OnionCat v{Application.version} ===");
        writer.WriteLine($"시작 시각: {DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        writer.WriteLine($"OS: {SystemInfo.operatingSystem}");
        writer.WriteLine($"GPU: {SystemInfo.graphicsDeviceName}");
        writer.WriteLine("---");

        Application.logMessageReceived += OnLog;
    }

    void OnDestroy()
    {
        Application.logMessageReceived -= OnLog;
        writer?.Close();
    }

    private static void OnLog(string condition, string stackTrace, LogType type)
    {
        if (type == LogType.Error || type == LogType.Exception || type == LogType.Assert)
        {
            writer.WriteLine($"[{DateTime.Now:HH:mm:ss}] [{type}] {condition}");
            if (!string.IsNullOrEmpty(stackTrace))
                writer.WriteLine(stackTrace);
            writer.WriteLine("---");
        }
    }
}
```

**저장 위치**: `Application.persistentDataPath`
- Windows: `C:/Users/<User>/AppData/LocalLow/<CompanyName>/<ProductName>/`
- Mac: `~/Library/Application Support/<CompanyName>/<ProductName>/`

### 2. 개발 빌드에서만 상세 로그

```csharp
private static void OnLog(string condition, string stackTrace, LogType type)
{
    bool isError = type == LogType.Error || type == LogType.Exception;
    bool isDebug = type == LogType.Log || type == LogType.Warning;

    if (isError)
    {
        writer.WriteLine($"[{type.ToString().ToUpper()}] {condition}\n{stackTrace}");
    }
    else if (Debug.isDebugBuild && isDebug)
    {
        writer.WriteLine($"[{type}] {condition}");
    }
}
```

릴리스 빌드에서는 Error/Exception만, 개발 빌드에서는 Log/Warning도 기록.

### 3. 크래시 감지 — Application.quitting + CrashReport

```csharp
void Awake()
{
    Application.quitting += OnQuit;

    // 이전 실행의 크래시 보고서 확인 (Unity CrashReport API)
    if (CrashReport.reports.Length > 0)
    {
        var last = CrashReport.reports[CrashReport.reports.Length - 1];
        writer.WriteLine($"[이전 크래시 감지] {last.time}: {last.text}");
        CrashReport.RemoveAll();
    }
}

private void OnQuit()
{
    writer.WriteLine($"[정상 종료] {DateTime.Now:HH:mm:ss}");
}
```

앱이 크래시로 종료됐으면 `OnQuit`이 안 불리므로, 다음 실행에 `CrashReport`를 확인하면 비정상 종료를 감지할 수 있다.

### 4. 게임 내 "버그 신고" 단축키 (개발/Beta 빌드 전용)

```csharp
// DebugReportTrigger.cs
void Update()
{
    // F12 누르면 현재 씬 상태 + 로그 파일 경로를 화면에 표시
    if (Keyboard.current != null && Keyboard.current.f12Key.wasPressedThisFrame)
    {
        Debug.Log($"로그 파일: {logPath}");
        GameUI.ShowToast($"Log saved to:\n{logPath}");
    }
}
```

베타 테스터가 버그 재현 시 로그 파일 위치를 쉽게 알 수 있도록.

### 5. 빌드 설정 최적화

**Player Settings > Other Settings**:
- `Stack Trace Logging`: Exception → Full (릴리스엔 ScriptOnly)
- `Allow 'unsafe' Code`: 필요 시만 켜기

**Development Build**: 릴리스 전 QA 단계에서 `Development Build` 체크 + `Script Debugging` 켜면 더 상세한 스택 트레이스 수집 가능.

### 6. 로그 파일 외부 전송 (선택 — 무료 티어)

Firebase Crashlytics Unity SDK를 쓰면 크래시를 자동으로 Firebase 대시보드에 수집:
```
com.google.firebase.crashlytics
```
무료 Spark 플랜으로 충분하며, 패키지 설치 후 `Crashlytics.ReportUncaughtExceptionsAsFatal = true` 한 줄로 설정 완료.

## OnionCat 적용 포인트

### 우선순위 1: 로컬 파일 로깅 (지금 당장 적용)
Bootstrap 씬의 `App_Boot_Sequence` 오브젝트에 `GameLogger` 컴포넌트 추가.
코드 10줄 정도로 빌드 후 플레이어 버그 재현 시 로그 파일을 공유받을 수 있음.

### 우선순위 2: 공식 출시 전 Firebase 연동
이티치오(itch.io) 베타 배포 단계에서 Firebase Crashlytics 연결.
다양한 Windows 환경(GPU, OS 버전)에서 발생하는 예외를 원격으로 수집.

### 2인 협동 특유의 버그 패턴

가장 자주 터지는 NullRef 지점:
```csharp
// 입력 시스템: 플레이어 2가 없는데 양파 입력 처리될 때
// 대쉬 중 피격 판정이 남아있을 때
// 방 전환 중 적 AI가 null GameManager에 접근할 때
```

로그에 씬 이름 + `GameManager.Instance.State`를 함께 기록하면 재현에 도움:

```csharp
private static void OnLog(string condition, string stackTrace, LogType type)
{
    if (type == LogType.Error || type == LogType.Exception)
    {
        string scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;
        string state = GameManager.Instance != null
            ? GameManager.Instance.State.ToString() : "null";
        writer.WriteLine($"[{type}] Scene={scene} State={state}");
        writer.WriteLine(condition);
        writer.WriteLine(stackTrace);
        writer.WriteLine("---");
    }
}
```

### 로그 순환 (용량 초과 방지)

장시간 플레이 시 로그 파일이 커질 수 있으므로, 앱 시작 시 `append: false`로 덮어쓰거나,
날짜별 파일 분리(`game_log_2026-09-30.txt`) 후 7일 초과 파일 삭제:

```csharp
// 7일 이상 된 로그 파일 삭제
foreach (var file in Directory.GetFiles(Application.persistentDataPath, "game_log_*.txt"))
{
    if ((DateTime.Now - File.GetLastWriteTime(file)).TotalDays > 7)
        File.Delete(file);
}
```

## 참고 링크
- [Unity Docs - Application.logMessageReceived](https://docs.unity3d.com/ScriptReference/Application-logMessageReceived.html)
- [Unity Docs - CrashReport](https://docs.unity3d.com/ScriptReference/CrashReport.html)
- [Unity Docs - Application.persistentDataPath](https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html)
- [Firebase Crashlytics for Unity](https://firebase.google.com/docs/crashlytics/get-started?platform=unity)
- [Firebase Unity Codelab](https://firebase.google.com/codelabs/understand-unity-games-crashes-using-advanced-crashlytics)
