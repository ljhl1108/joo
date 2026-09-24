# GameJam / Demo Build Configuration

리서치 날짜: 2026-09-24

## 개요

게임잼 또는 데모 배포용 빌드를 빠르게 준비하는 방법. 완성된 릴리즈와 달리 데모는
**짧은 시간 안에 핵심 경험만 전달**하는 것이 목표. 빌드 설정, 콘텐츠 제한, 피드백 수집까지 포함.

---

## 데모 빌드의 목표

1. **Core Loop 전달**: 플레이어가 1~3회 런만에 게임의 핵심 재미를 느끼게
2. **크래시 최소화**: 미완성 기능을 보여주지 않는 것이 안 보여주는 것보다 낫다
3. **플레이타임 제한**: 보통 20~30분 분량 (게임잼은 5~10분)
4. **피드백 수집**: itch.io 댓글, 설문 링크, 인앱 피드백 버튼

---

## Unity 구현 방법

### 1. Build Symbols로 데모/릴리즈 분기

**Player Settings > Other Settings > Scripting Define Symbols**에 `DEMO_BUILD` 추가.

```csharp
// DemoGate.cs — 데모에서 콘텐츠 잠금
public static class DemoGate {
#if DEMO_BUILD
    public const int MAX_RUNS = 3;
    public const bool FINAL_BOSS_ENABLED = false;
    public const string END_MESSAGE = "Thanks for playing the demo!\nFull game coming soon.";
#else
    public const int MAX_RUNS = int.MaxValue;
    public const bool FINAL_BOSS_ENABLED = true;
    public const string END_MESSAGE = "";
#endif
}
```

```csharp
// GameManager.cs — 런 횟수 체크
void OnRunEnd() {
#if DEMO_BUILD
    if (Run.totalRunCount >= DemoGate.MAX_RUNS) {
        ShowDemoEndScreen();
        return;
    }
#endif
    StartNewRun();
}
```

### 2. 데모 종료 화면 씬

별도 `DemoEnd` 씬을 만들어 감사 메시지, 소셜 링크, 피드백 URL 표시:

```csharp
public class DemoEndScreen : MonoBehaviour {
    [SerializeField] private string feedbackUrl = "https://forms.gle/xxxxx";
    [SerializeField] private string storePage = "https://itch.io/game/onioncat";

    public void OpenFeedback() => Application.OpenURL(feedbackUrl);
    public void OpenStore()    => Application.OpenURL(storePage);
    public void Restart()      => SceneManager.LoadScene("MainMenu");
}
```

### 3. Build Configuration 스크립트 (Editor)

빌드할 때마다 수동으로 설정 변경하는 실수를 방지하는 에디터 메뉴:

```csharp
using UnityEditor;
using UnityEditor.Build.Reporting;

public class DemoBuildMenu {
    const string DEMO_SYMBOL = "DEMO_BUILD";

    [MenuItem("Build/Build Demo (Windows)")]
    static void BuildDemo() {
        // Define Symbol 추가
        string current = PlayerSettings.GetScriptingDefineSymbolsForGroup(
            BuildTargetGroup.Standalone);
        if (!current.Contains(DEMO_SYMBOL))
            PlayerSettings.SetScriptingDefineSymbolsForGroup(
                BuildTargetGroup.Standalone, current + ";" + DEMO_SYMBOL);

        // 빌드 씬 목록 (데모용)
        string[] scenes = {
            "Assets/Scenes/Splash.unity",
            "Assets/Scenes/MainMenu.unity",
            "Assets/Scenes/Game.unity",
            "Assets/Scenes/DemoEnd.unity",
        };

        var opts = new BuildPlayerOptions {
            scenes = scenes,
            locationPathName = "Builds/Demo/OnionCat_Demo.exe",
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.None
        };

        var report = BuildPipeline.BuildPlayer(opts);
        Debug.Log($"Demo build: {report.summary.result}");
    }

    [MenuItem("Build/Remove Demo Symbol")]
    static void RemoveDemoSymbol() {
        string current = PlayerSettings.GetScriptingDefineSymbolsForGroup(
            BuildTargetGroup.Standalone);
        PlayerSettings.SetScriptingDefineSymbolsForGroup(
            BuildTargetGroup.Standalone,
            current.Replace(DEMO_SYMBOL, "").Replace(";;", ";").Trim(';'));
    }
}
```

### 4. 데모 전용 세이브 파일 분리

데모 플레이 데이터가 릴리즈 세이브에 섞이지 않게:

```csharp
string savePath = Application.persistentDataPath + 
#if DEMO_BUILD
    "/save_demo.json";
#else
    "/save.json";
#endif
```

### 5. 게임잼 타임리밋 데이터 초기화

게임잼 제출 전 PlayerPrefs / 세이브 데이터 초기화 메뉴:

```csharp
[MenuItem("Debug/Reset All Save Data")]
static void ResetSave() {
    PlayerPrefs.DeleteAll();
    string path = Application.persistentDataPath + "/save.json";
    if (File.Exists(path)) File.Delete(path);
    Debug.Log("Save data cleared.");
}
```

---

## 데모 빌드 체크리스트

```
[ ] DEMO_BUILD 심볼 추가 확인
[ ] 런 횟수 제한 테스트 (MAX_RUNS 번 플레이 후 DemoEnd 씬 나오는지)
[ ] 미완성 씬/기능 씬 목록에서 제외
[ ] 데모 종료 화면 피드백 URL/소셜 링크 정확한지 확인
[ ] 크레딧 또는 "데모 버전" 라벨 메인 메뉴에 표시
[ ] 빌드 폴더 이름에 날짜/버전 포함 (OnionCat_Demo_v0.3_2026-09-24)
[ ] Windows 방화벽 경고 없는지 테스트 (다른 PC에서 실행)
[ ] 해상도/창모드 기본값이 적절한지 확인
[ ] 게임잼 제출 전 세이브 데이터 초기화
[ ] README.txt 또는 Controls.txt 동봉 (키 안내)
```

---

## OnionCat 적용 포인트

### 데모 콘텐츠 범위 제안
- **런 1**: 튜토리얼 방 + 기본 적 2종(근접 약점 / 원거리 약점) + 협력 유도
- **런 2**: 업그레이드 선택 등장, 적 다양성 증가
- **런 3**: 미니 보스 or 층 클리어 → DemoEnd 씬

이 구조면 플레이타임 15~25분, 핵심 협동 메카닉을 모두 체험 가능.

### 싱글 플레이어도 지원 고려
데모는 2인 플레이 가능한 세팅이 없는 환경에서도 플레이할 수 있어야 함.  
Onion 파트를 간단한 AI나 자동 방어 모드로 대체하는 싱글 플레이어 모드를 데모에 포함하면 접근성 ↑.

---

## 참고 링크

- Unity Manual — Scripting Define Symbols: https://docs.unity3d.com/Manual/CustomScriptingSymbols.html
- Unity Manual — BuildPlayerOptions: https://docs.unity3d.com/ScriptReference/BuildPlayerOptions.html
- itch.io 게임잼 제출 가이드: https://itch.io/docs/creators/game-jams
- Game Jams Best Practices (GDC 2018): https://www.gdcvault.com/play/1025289
