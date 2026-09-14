# 게임 버전 표시 & 빌드 정보 UI

리서치 날짜: 2026-09-14

## 개요

게임 메뉴 하단에 버전 번호(예: `v0.1.3`)를 표시하고, 빌드 시점 정보를 관리하는 기능. 작게 보이지만 실제로는:
- 버그 리포트 시 플레이어가 어떤 버전을 쓰는지 즉시 파악 가능
- 개발 중 테스트 빌드와 릴리즈 빌드 구분
- 플레이테스트 피드백과 버전 연계

초보 개발자가 출시를 준비할 때 빠뜨리기 쉬운 기능이며, 구현 난이도는 낮다.

---

## Unity 구현 방법

### 1. Player Settings에서 버전 관리

**Edit → Project Settings → Player → Version** 필드에 버전 문자열 입력.

- 형식 권장: **Semantic Versioning** — `MAJOR.MINOR.PATCH` (예: `0.3.1`)
  - `0.x.x`: 미출시 개발 버전
  - `1.0.0`: 첫 공개 출시
  - PATCH: 버그 수정, MINOR: 새 기능, MAJOR: 큰 변경

**C#에서 읽기**:
```csharp
string version = Application.version; // Player Settings의 Version 필드 값
```

---

### 2. 메인 메뉴에 버전 텍스트 표시

```csharp
using UnityEngine;
using TMPro;

public class VersionDisplay : MonoBehaviour
{
    [SerializeField] private TMP_Text versionText;

    private void Awake()
    {
        string displayText = $"v{Application.version}";

#if DEVELOPMENT_BUILD || UNITY_EDITOR
        // 개발 빌드에서만 추가 정보 표시
        displayText += $"  [DEV]  {GetBuildDate()}";
#endif

        versionText.text = displayText;
    }

    private string GetBuildDate()
    {
        // BuildInfo.cs에서 자동 생성된 날짜 읽기 (아래 방법 참고)
        return BuildInfo.BuildDate;
    }
}
```

**UI 배치**: 메인 메뉴 캔버스 → 오른쪽 하단 고정
```
Canvas
 └─ VersionText (TMP_Text)
      Anchor: bottom-right
      Pivot: (1, 0)
      Font Size: 12~14
      Color: 흰색 α 0.5 (눈에 덜 띄게)
      Text: v0.1.0
```

---

### 3. 빌드 날짜 자동 기록 (BuildInfo 자동 생성)

#### 방법 A: Pre-Build Script (빌드할 때마다 자동 갱신)

```csharp
// Editor/BuildDateInjector.cs
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using System.IO;
using System;

public class BuildDateInjector : IPreprocessBuildWithReport
{
    public int callbackOrder => 0;

    public void OnPreprocessBuild(BuildReport report)
    {
        string date = DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm UTC");
        string content = $"public static class BuildInfo\n{{\n    public static readonly string BuildDate = \"{date}\";\n}}";
        File.WriteAllText("Assets/Scripts/BuildInfo.cs", content);
        AssetDatabase.Refresh();
    }
}
```

이 스크립트를 추가하면 빌드할 때마다 `BuildInfo.cs`가 자동 생성됨.

#### 방법 B: 단순 수동 관리 (초보자 권장)

```csharp
// Assets/Scripts/BuildInfo.cs (수동으로 수정)
public static class BuildInfo
{
    public static readonly string BuildDate = "2026-09-14";
    public static readonly string BuildNote = "alpha";
}
```

---

### 4. 개발 빌드 vs 릴리즈 빌드 구분

```csharp
private void Awake()
{
    string ver = $"v{Application.version}";

    if (Debug.isDebugBuild)
        ver += " [DEBUG]";
    else if (Application.genuine == false)
        ver += " [TAMPERED]"; // 파일이 조작된 경우

    versionText.text = ver;
}
```

**Unity 빌드 설정**:
- **File → Build Settings → Development Build** 체크 시 `Debug.isDebugBuild == true`
- 릴리즈 빌드: 체크 해제 → `[DEBUG]` 텍스트 미표시

---

### 5. 빌드 번호 (Build Number) 자동 증가

```csharp
// Editor/BuildNumberIncrementer.cs
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

public class BuildNumberIncrementer : IPreprocessBuildWithReport
{
    public int callbackOrder => -1; // BuildDateInjector 전에 실행

    public void OnPreprocessBuild(BuildReport report)
    {
        // iOS/Android의 bundleVersionCode를 자동 증가
        int buildNumber;
        if (int.TryParse(PlayerSettings.iOS.buildNumber, out buildNumber))
            PlayerSettings.iOS.buildNumber = (buildNumber + 1).ToString();
        
        PlayerSettings.Android.bundleVersionCode++;
    }
}
```

---

### 6. 크래시/버그 리포트에 버전 포함

```csharp
// 게임 시작 시 한 번 실행
private void Start()
{
    Debug.Log($"[Session Start] v{Application.version} | {SystemInfo.operatingSystem} | {SystemInfo.graphicsDeviceName}");
}
```

로그를 파일에 저장하면 버그 리포트 시 환경 정보 즉시 확인 가능.

---

## OnionCat 적용 포인트

### A. 메인 메뉴 즉시 적용
- `MainMenu` 씬에 `VersionDisplay` 컴포넌트 추가 → TMP_Text 연결
- Player Settings에서 버전 `v0.1.0`으로 설정
- 오른쪽 하단, 반투명 흰색 소문자로 표시 → 픽셀아트 스타일과 잘 어울림

### B. 플레이테스터 피드백 연계
- 지인 테스트 시 "어떤 버전 했어?"를 버전 텍스트로 즉시 확인 가능
- 버전 올릴 때마다 Player Settings → Version 한 줄 수정으로 끝

### C. 개발 빌드 경고
- `#if DEVELOPMENT_BUILD` 조건으로 개발 빌드에는 `[DEV]` 표시
- 실수로 개발 빌드를 배포하는 것 방지

### D. 구현 우선순위
- 지금 당장: `VersionDisplay.cs` + `Application.version` (30분)
- 알파 테스트 전: `BuildInfo.cs` 수동 날짜 기록
- 베타 이후: `IPreprocessBuildWithReport`로 자동화

---

## 구현 순서 (초보자용)

1. `Player Settings → Version`에 `0.1.0` 입력
2. 메인 메뉴 캔버스에 TMP_Text 추가 → 우하단 앵커
3. `VersionDisplay.cs` 작성 → Awake에서 `Application.version` 읽어 표시
4. 빌드 후 버전 텍스트 확인

> **시간**: 30분 이내. 지금 당장 해도 되는 수준.

---

## 참고 링크

- [Unity Docs - Application.version](https://docs.unity3d.com/ScriptReference/Application-version.html)
- [Unity Docs - PlayerSettings](https://docs.unity3d.com/ScriptReference/PlayerSettings.html)
- [Unity Docs - IPreprocessBuildWithReport](https://docs.unity3d.com/ScriptReference/Build.IPreprocessBuildWithReport.html)
- [Semantic Versioning](https://semver.org/lang/ko/)
- [Unity Build Version Number Tips - Forum](https://forum.unity.com/threads/auto-increment-version-number.476459/)
