# Debug vs Release Build Configuration (디버그/릴리즈 빌드 설정)

리서치 날짜: 2026-10-01

## 개요

게임을 플레이어에게 공개하기 전, 개발용(Debug) 빌드와 배포용(Release) 빌드를 구분해야 한다.
Unity의 Debug.Log는 릴리즈에서도 실행되어 성능을 저하시키고, 치트 키와 개발자 UI가 
공개 빌드에 포함되면 게임 경험이 망가진다.

OnionCat 관련성: itch.io 첫 공개 빌드, 게임 잼 제출, Early Access 출시 시 반드시 필요.

---

## Unity 구현 방법

### 1. 조건부 컴파일 심볼 (Scripting Define Symbols)

**Player Settings → Other Settings → Scripting Define Symbols** 또는 코드에서:

```csharp
// 빌드 타입 판별 — Unity 내장 상수
#if UNITY_EDITOR
    // 에디터 전용 코드
#endif

#if DEVELOPMENT_BUILD
    // Unity Build Settings에서 "Development Build" 체크 시 활성화
    // 디버거 연결, Profiler 사용 가능
#endif

// 커스텀 심볼 (Project Settings에서 설정)
#if ONIONCAT_DEBUG
    // 치트 키, 개발자 UI 등
#endif
```

**설정 방법**:
1. Edit → Project Settings → Player → Other Settings
2. Scripting Define Symbols에 `ONIONCAT_DEBUG` 추가 (개발 중)
3. 배포 전 이 심볼을 **제거**하면 관련 코드 전체가 빌드에서 제외됨

---

### 2. Debug.Log 성능 문제와 해결

Debug.Log는 빌드에서도 **조건 없이 실행**된다. 로그 문자열 생성만으로 GC 압력이 발생.

#### 방법 1: Conditional 어트리뷰트 (권장)
```csharp
public static class DebugUtil
{
    [System.Diagnostics.Conditional("ONIONCAT_DEBUG")]
    public static void Log(string msg) => Debug.Log(msg);

    [System.Diagnostics.Conditional("ONIONCAT_DEBUG")]
    public static void LogWarning(string msg) => Debug.LogWarning(msg);

    [System.Diagnostics.Conditional("ONIONCAT_DEBUG")]
    public static void LogError(string msg) => Debug.LogError(msg);
}

// 사용:
DebugUtil.Log("Enemy spawned"); // ONIONCAT_DEBUG 없으면 호출 자체가 제거됨
```

#### 방법 2: Debug.unityLogger 비활성화 (빠른 방법)
```csharp
// Awake (GameManager 또는 Bootstrap):
#if !DEVELOPMENT_BUILD && !UNITY_EDITOR
    Debug.unityLogger.logEnabled = false;
#endif
```

---

### 3. 빌드 설정 체크리스트

#### File → Build Settings

| 항목 | Debug | Release |
|------|-------|---------|
| Development Build | ✅ 체크 | ❌ 해제 |
| Autoconnect Profiler | ✅ 필요 시 | ❌ 해제 |
| Deep Profiling | 필요 시 | ❌ 해제 |
| Script Debugging | ✅ | ❌ |

#### Player Settings → Other Settings

| 항목 | 권장값 | 이유 |
|------|--------|------|
| Scripting Backend | IL2CPP | 릴리즈 성능 + 코드 난독화 |
| Api Compatibility Level | .NET Standard 2.1 | 빌드 크기 감소 |
| Managed Stripping Level | Medium (릴리즈) | 미사용 코드 제거 |
| Allow 'unsafe' Code | 필요 시만 | 불필요하면 해제 |

#### Player Settings → Publishing Settings (Windows)

```
Build Type: IL2CPP
Architecture: x86_64 (64비트만 지원, 현재 표준)
Compression Method: LZ4HC (릴리즈)
```

---

### 4. 치트/개발자 기능 격리

```csharp
// DebugCheatSystem.cs
public class DebugCheatSystem : MonoBehaviour
{
#if ONIONCAT_DEBUG
    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.F1))
        {
            GameManager.Instance.GodMode = !GameManager.Instance.GodMode;
            DebugUtil.Log("GodMode: " + GameManager.Instance.GodMode);
        }

        if (Input.GetKeyDown(KeyCode.F2))
            GameManager.Instance.ChangeState(GameState.Victory);

        if (Input.GetKeyDown(KeyCode.F3))
            PlayerStats.Current.AddGold(999);
    }
#endif
}
```

`#if ONIONCAT_DEBUG` 블록 안의 코드는 심볼이 없으면 **컴파일조차 안 됨** → 빌드에 흔적 없음.

---

### 5. 개발자 UI 오버레이 격리

```csharp
// DebugOverlayUI.cs
public class DebugOverlayUI : MonoBehaviour
{
#if ONIONCAT_DEBUG
    private void OnGUI()
    {
        GUI.Label(new Rect(10, 10, 300, 20), $"FPS: {1f / Time.deltaTime:F0}");
        GUI.Label(new Rect(10, 30, 300, 20), $"State: {GameManager.Instance.State}");
        GUI.Label(new Rect(10, 50, 300, 20), $"Room: {RoomManager.Instance.CurrentRoom}");
    }
#endif
}
```

또는 GameObject를 통째로 비활성화:
```csharp
// Bootstrap.cs
[SerializeField] private GameObject debugOverlay;

private void Awake()
{
#if !ONIONCAT_DEBUG
    if (debugOverlay != null)
        Destroy(debugOverlay);
#endif
}
```

---

### 6. 빌드 버전 정보 자동화

```csharp
// 게임 버전을 코드에서 읽기
public static class BuildInfo
{
    public static string Version => Application.version;  // Player Settings에서 설정
    public static string Platform => Application.platform.ToString();

#if DEVELOPMENT_BUILD
    public static string BuildType => "DEV";
#else
    public static string BuildType => "RELEASE";
#endif

    public static string FullVersion => $"v{Version} ({BuildType})";
}

// UI에서: versionText.text = BuildInfo.FullVersion;
// 릴리즈 빌드: "v0.1.0 (RELEASE)"
// 개발 빌드: "v0.1.0 (DEV)"
```

---

### 7. itch.io 업로드용 빌드 절차

```
1. Project Settings → Player
   - Company Name, Product Name 확인
   - Version 번호 업데이트 (예: 0.1.0)
   - Default Screen Width/Height 설정

2. Build Settings
   - Development Build: ❌ 해제
   - Target Platform: Windows (x86_64), WebGL, 또는 둘 다

3. Build 폴더 구조 (Windows)
   OnionCat_v0.1.0/
   ├── OnionCat.exe
   ├── OnionCat_Data/
   └── UnityCrashHandler64.exe

4. zip으로 압축: OnionCat_v0.1.0_win.zip
5. itch.io 대시보드에서 업로드
```

#### WebGL 빌드 특이사항
```
Player Settings → WebGL
  - Compression Format: Brotli (itch.io 지원)
  - Memory Size: 256MB (기본값, 필요 시 512MB)
  - Exception Support: None (릴리즈) → 빌드 크기 대폭 감소
```

---

### 8. 빌드 스크립트 자동화 (선택사항)

```csharp
// BuildScript.cs (Editor 폴더에)
using UnityEditor;
using UnityEditor.Build.Reporting;

public class BuildScript
{
    [MenuItem("Build/Release Windows")]
    public static void BuildWindows()
    {
        var options = new BuildPlayerOptions
        {
            scenes = EditorBuildSettings.scenes
                .Where(s => s.enabled)
                .Select(s => s.path)
                .ToArray(),
            locationPathName = "Builds/Windows/OnionCat.exe",
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.None  // Development Build 없음
        };

        var report = BuildPipeline.BuildPlayer(options);
        if (report.summary.result == BuildResult.Succeeded)
            Debug.Log($"Build succeeded: {report.summary.totalSize / 1024 / 1024}MB");
        else
            Debug.LogError("Build FAILED");
    }
}
```

---

## OnionCat 적용 포인트

### 즉시 해야 할 것
1. `DebugUtil.cs` 유틸리티 클래스 만들기 → 기존 `Debug.Log` 전부 교체
2. `DebugCheatSystem.cs`의 치트 코드를 `#if ONIONCAT_DEBUG` 블록 안으로
3. Player Settings에서 `ONIONCAT_DEBUG` 심볼 현재 추가, 배포 전 제거

### 첫 공개 빌드 전 필수 확인
```
[ ] Development Build 체크 해제
[ ] ONIONCAT_DEBUG 심볼 제거
[ ] 버전 번호 설정 (Major.Minor.Patch)
[ ] 화면 해상도 기본값 설정 (1280×720 권장)
[ ] DebugOverlay GameObject 비활성화 확인
[ ] 콘솔 에러 없음 확인
[ ] IL2CPP 빌드 테스트 (IL2CPP는 Mono와 다른 버그가 생길 수 있음)
```

### OnionCat 버전 관리 제안
```
Alpha 0.1.x: 게임 잼 / 내부 테스트
Beta 0.2.x: itch.io Early Access
v1.0.0: 정식 출시
```

---

## 참고 링크

- Unity Build Settings 공식: https://docs.unity3d.com/Manual/BuildSettings.html
- Unity Conditional Compilation: https://docs.unity3d.com/Manual/PlatformDependentCompilation.html
- Unity IL2CPP 소개: https://docs.unity3d.com/Manual/IL2CPP.html
- itch.io Upload Guide: https://itch.io/docs/creators/uploads
- Game Maker's Toolkit - "Should You Launch On Early Access?": https://youtu.be/HRRMmgGSZS0
