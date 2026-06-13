# 빌드 및 배포 (Build & Deploy)

리서치 날짜: 2026-06-13

## 개요

게임 완성의 마지막 단계. Unity에서 Windows 실행파일(.exe), WebGL(브라우저 실행), Android APK 등으로 빌드하고 itch.io 같은 플랫폼에 배포하는 과정. 초보 개발자가 "게임이 완성됐는데 어떻게 남에게 보여주지?"라는 벽을 마주치는 지점이므로 미리 알아두면 큰 도움이 된다. OnionCat은 로컬 2인 협력 게임이므로 PC 빌드(Windows/Mac)와 WebGL 데모를 우선 목표로 한다.

---

## Unity 구현 방법

### Step 1: Build Settings 기본 설정

1. **File → Build Settings** 열기
2. **Scenes In Build** 패널에 씬 추가
   - 씬 순서 = Build Index: 0번이 첫 로드 씬 (메인 메뉴)
   - 드래그 앤 드롭 또는 "Add Open Scenes" 버튼
3. **Platform 선택** → 처음엔 PC, Mac & Linux Standalone 권장

```
Build Settings
├── Scenes In Build
│   ├── 0: Scenes/MainMenu
│   ├── 1: Scenes/GameScene
│   └── 2: Scenes/GameOver
├── Platform: PC, Mac & Linux Standalone
├── Target Platform: Windows
└── Architecture: x86_64
```

### Step 2: Player Settings 구성

**File → Build Settings → Player Settings** 또는 **Edit → Project Settings → Player**

| 항목 | 권장값 | 이유 |
|------|--------|------|
| Company Name | 본인 이름/팀명 | 앱 식별자 |
| Product Name | OnionCat | 실행파일명 |
| Version | 0.1.0 | 시맨틱 버저닝 |
| Default Icon | 게임 아이콘 설정 | 실행파일 아이콘 |
| Default Cursor | 커스텀 커서 (선택) | 픽셀아트 커서 |
| Fullscreen Mode | Windowed or Fullscreen Window | 입력 문제 방지 |
| Default Screen Width/Height | 1280 × 720 | 16:9 기본값 |
| Run in Background | ✓ 체크 | 2인 플레이 시 포커스 이탈 대응 |

### Step 3: Windows PC 빌드

```
1. Build Settings → Platform: PC, Mac & Linux Standalone
2. Target Platform: Windows / Architecture: x86_64
3. "Build" 클릭 → 출력 폴더 선택
4. 결과물:
   OnionCat.exe
   OnionCat_Data/
   UnityPlayer.dll
   → 이 폴더 전체를 ZIP으로 묶어 배포
```

**중요**: `OnionCat_Data` 폴더와 `UnityPlayer.dll` 없이 `.exe`만 보내면 실행 안 됨.

### Step 4: WebGL 빌드 (itch.io 데모용)

```
1. Build Settings → Platform: WebGL
2. Player Settings → WebGL
   - Compression Format: Gzip (기본) or Disabled (호환성 우선)
   - Memory Size: 256MB (소규모 게임)
3. "Build" 클릭
4. 결과물:
   index.html
   Build/
   TemplateData/
```

**itch.io 업로드 방법**:
1. itch.io 계정 생성 → "Upload new project"
2. Kind of project: HTML
3. 결과물 폴더 전체를 ZIP → 업로드
4. "This file will be played in the browser" 체크
5. 뷰포트 크기: 960 × 540 (또는 1280 × 720)

### Step 5: WebGL 주의사항

```csharp
// WebGL에서 멀티스레드, File I/O 제한 있음
// PlayerPrefs는 WebGL에서도 작동 (로컬스토리지 사용)
// 파일 시스템(System.IO) 접근 불가 → JSON 저장 시 PlayerPrefs 사용 권장

// WebGL 빌드 체크리스트:
// ✅ Audio: WebGL은 자동재생 정책으로 첫 클릭 후 오디오 시작
// ✅ New Input System: WebGL에서도 작동하지만 게임패드 지원 제한
// ✅ 텍스처 압축: WebGL은 DXT 아닌 ETC2 or ASTC 사용
```

### Step 6: 빌드 크기 최적화

```
Edit → Project Settings → Player → Other Settings:
- Scripting Backend: IL2CPP (더 빠르고 작음, 빌드 시간 길어짐)
- Api Compatibility Level: .NET Standard 2.1

Edit → Project Settings → Graphics:
- Shader Stripping: 불필요한 셰이더 제거

Window → Asset Management → Addressables (고급):
- 에셋 번들로 동적 로딩 (필요 시만)
```

**빠른 크기 줄이기**:
1. 미사용 에셋 삭제
2. 텍스처 Compression 설정 확인 (Inspector → Texture Type)
3. Audio Import Settings: Load Type = "Streaming" (큰 음악 파일)
4. **Edit → Project Settings → Quality** → 불필요한 Quality Level 제거

### Step 7: 버전 관리 & 빌드 자동화 (선택)

```csharp
// 빌드 넘버 자동 증가 스크립트 (에디터 스크립트)
// Assets/Editor/BuildScript.cs
#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.Build.Reporting;

public class BuildScript
{
    [MenuItem("Tools/Build Windows")]
    public static void BuildWindows()
    {
        string[] scenes = { "Assets/Scenes/MainMenu.unity", "Assets/Scenes/GameScene.unity" };
        string path = "Builds/Windows/OnionCat.exe";

        BuildPlayerOptions opts = new BuildPlayerOptions
        {
            scenes = scenes,
            locationPathName = path,
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.None
        };

        BuildReport report = BuildPipeline.BuildPlayer(opts);
        if (report.summary.result == BuildResult.Succeeded)
            UnityEngine.Debug.Log("Build succeeded: " + path);
        else
            UnityEngine.Debug.LogError("Build failed");
    }
}
#endif
```

### Step 8: 배포 플랫폼 비교

| 플랫폼 | 장점 | 단점 | 권장 시점 |
|--------|------|------|----------|
| **itch.io** | 무료, 즉시 배포, WebGL 지원 | 노출 적음 | 초기 데모, 플레이테스트 |
| **Steam** | 최대 노출, 도전과제/클라우드 | $100 수수료, 심사 시간 | 정식 출시 |
| **GitHub Releases** | 무료, 개발자 친화적 | 일반 유저 접근성 낮음 | 알파 테스트 배포 |
| **Game Jolt** | 무료, 커뮤니티 있음 | itch.io보다 작은 규모 | 선택적 |

---

## OnionCat 적용 포인트

### 1. 권장 배포 로드맵
```
Phase 1 (지금~첫 플레이테스트):
  → itch.io WebGL 비공개 링크로 지인 테스트
  → 2인 협력 핵심 루프가 동작하는지 검증

Phase 2 (알파):
  → itch.io PC(Windows) 빌드 공개
  → itch.io 페이지: 스크린샷, 짧은 설명, 조작법 안내

Phase 3 (정식):
  → Steam 등록 고려 (게임 규모 보고 결정)
```

### 2. 2인 협력 WebGL 주의사항
- WebGL에서 게임패드(Controller) 지원: Chrome 기준 xinput 컨트롤러 작동하나 불안정
- 2인 게임 특성상 **PC 빌드 우선 권장** (게임패드 두 개 연결 안정성)
- WebGL 데모는 키보드/마우스 조작으로만 테스트 가능하도록 설계

### 3. 빌드 전 체크리스트 (OnionCat 전용)
```
[ ] 모든 씬이 Build Settings에 추가됨
[ ] 메인 메뉴 씬이 Index 0번
[ ] 게임 아이콘 설정 (16×16, 32×32, 48×48, 128×128 픽셀아트 고양이)
[ ] 해상도: 1280×720 기본, 전체화면 토글 지원
[ ] 오디오: WebGL 자동재생 정책 대응 (첫 입력 후 BGM 시작)
[ ] Run in Background: ON (2인 플레이 시 창 포커스 이탈 방지)
[ ] Input System: 빌드 타깃에서 게임패드 인식 테스트
[ ] 첫 씬 로드 시 null reference 없는지 확인
```

### 4. itch.io 페이지 작성 팁
- **제목**: OnionCat — 고양이와 양파의 협력 로그라이크
- **장르 태그**: roguelike, co-op, pixel art, top-down, 2-player
- **스크린샷 최소 3장**: 전투 씬, 업그레이드 선택 씬, 메인 메뉴
- **조작법 명시**: "Player 1: WASD+Space / Player 2: Mouse+RMB"

---

## 참고 링크

- Unity 공식 Build Settings 문서: https://docs.unity3d.com/Manual/BuildSettings.html
- Unity WebGL 빌드 가이드: https://docs.unity3d.com/Manual/webgl-building.html
- Unity WebGL 제약사항: https://docs.unity3d.com/Manual/webgl-browsercompatibility.html
- itch.io HTML5 게임 업로드 가이드: https://itch.io/docs/creators/html5
- Unity IL2CPP vs Mono 비교: https://docs.unity3d.com/Manual/scripting-backends.html
- Brackeys - How to PUBLISH your game: https://www.youtube.com/watch?v=BQ1EjVZRRiY
