# 스크린샷 & 소셜 공유 시스템 (Screenshot & Social Share System)

리서치 날짜: 2026-08-23

## 개요

플레이어가 **런 클리어 화면, 강력한 조합, 재미있는 순간을 캡처하고 공유**할 수 있는 기능.
특히 로그라이크 게임에서 스크린샷 공유는 **입소문 마케팅의 핵심** 채널.
OnionCat처럼 2인 플레이 중심 게임은 "우리가 이겼어요!" 스크린샷을 유도하면
자연스러운 소셜 홍보 효과를 얻을 수 있다.

구현 난이도: ★★☆☆☆ (PC/스탠드얼론 기준)

---

## Unity 구현 방법

### 1. 기본 스크린샷 저장 (가장 단순)

```csharp
using UnityEngine;
using System.IO;

public class ScreenshotManager : MonoBehaviour
{
    public void TakeScreenshot()
    {
        string fileName = $"OnionCat_{System.DateTime.Now:yyyyMMdd_HHmmss}.png";
        string path = Path.Combine(Application.persistentDataPath, "Screenshots", fileName);

        // 폴더 없으면 생성
        Directory.CreateDirectory(Path.GetDirectoryName(path));

        ScreenCapture.CaptureScreenshot(path, 2);  // 2 = 2배 해상도(고화질)
        Debug.Log($"스크린샷 저장됨: {path}");
    }
}
```

### 2. 텍스처로 캡처 (미리보기 + UI 오버레이 포함)

런 결과 화면 같은 **특정 UI 포함 캡처**에 적합:

```csharp
using System.Collections;
using UnityEngine;

public class ScreenshotManager : MonoBehaviour
{
    private Texture2D _lastScreenshot;

    public IEnumerator CaptureWithUI(System.Action<Texture2D> onComplete)
    {
        yield return new WaitForEndOfFrame();  // UI가 렌더링된 후 캡처

        _lastScreenshot = ScreenCapture.CaptureScreenshotAsTexture();
        onComplete?.Invoke(_lastScreenshot);
    }

    public void SaveToFile(Texture2D tex)
    {
        byte[] pngData = tex.EncodeToPNG();
        string path = Path.Combine(Application.persistentDataPath, "Screenshots",
            $"OnionCat_{System.DateTime.Now:yyyyMMdd_HHmmss}.png");
        Directory.CreateDirectory(Path.GetDirectoryName(path));
        File.WriteAllBytes(path, pngData);
    }
}
```

### 3. 특정 카메라/레이어만 캡처 (HUD 제외)

UI HUD를 제외하고 **게임 화면만** 캡처:

```csharp
public IEnumerator CaptureGameOnly(Camera gameCamera, int width, int height,
    System.Action<Texture2D> onComplete)
{
    RenderTexture rt = new RenderTexture(width, height, 24);
    gameCamera.targetTexture = rt;
    gameCamera.Render();

    RenderTexture.active = rt;
    Texture2D tex = new Texture2D(width, height, TextureFormat.RGB24, false);
    tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
    tex.Apply();

    gameCamera.targetTexture = null;
    RenderTexture.active = null;
    Destroy(rt);

    yield return null;
    onComplete?.Invoke(tex);
}
```

### 4. 스크린샷 폴더 열기 (Windows)

```csharp
public void OpenScreenshotFolder()
{
#if UNITY_STANDALONE_WIN
    string path = Path.Combine(Application.persistentDataPath, "Screenshots");
    if (Directory.Exists(path))
        System.Diagnostics.Process.Start("explorer.exe", path.Replace("/", "\\"));
#endif
}
```

### 5. 런 결과 + 스크린샷 자동 캡처 흐름

```csharp
// RunResultScreen.cs
public class RunResultScreen : MonoBehaviour
{
    [SerializeField] private ScreenshotManager screenshotManager;
    [SerializeField] private GameObject shareButton;

    void Start()
    {
        // 결과 화면이 뜰 때 자동으로 캡처
        StartCoroutine(screenshotManager.CaptureWithUI(OnCaptured));
    }

    void OnCaptured(Texture2D screenshot)
    {
        // Raw Image UI에 미리보기로 표시
        // 공유 버튼 활성화
        shareButton.SetActive(true);
    }
}
```

### 6. Steam 스크린샷 API (Steamworks 배포 시)

```csharp
// Steamworks.NET 필요
#if UNITY_STANDALONE && STEAMWORKS_NET
using Steamworks;

public void TakeSteamScreenshot()
{
    SteamScreenshots.TriggerScreenshot();  // Steam 오버레이 스크린샷 (F12 동일)
}
#endif
```

### 7. 소셜 공유 URL 열기 (웹 공유)

직접 업로드 대신 **Twitter/X 미리 작성된 트윗** 열기 (외부 서비스 사용 최소화):

```csharp
public void ShareOnTwitter(string runResult)
{
    string text = Uri.EscapeUriString(
        $"OnionCat 런 완료! {runResult} #OnionCat #roguelike #indiegame"
    );
    Application.OpenURL($"https://x.com/intent/tweet?text={text}");
}
```

---

## 구현 순서 (OnionCat 권장)

1. **Phase 1 - 기본**: `TakeScreenshot()` 버튼을 일시정지 메뉴에 추가
2. **Phase 2 - 런 결과**: 런 결과 화면 진입 시 자동 캡처 + 파일 저장
3. **Phase 3 - 미리보기**: 결과 화면에 캡처된 이미지 썸네일 표시
4. **Phase 4 - 공유**: 폴더 열기 버튼 + (선택) Twitter URL 연결
5. **Phase 5 - Steam**: Steamworks 연동 후 SteamScreenshots API 교체

---

## OnionCat 적용 포인트

### 자동 캡처 타이밍 (추천)
| 타이밍 | 캡처 내용 |
|--------|----------|
| 보스 클리어 직후 | 승리 연출 + 두 캐릭터가 함께 화면에 있는 순간 |
| 런 결과 화면 진입 시 | 처치 수, 클리어 시간, 획득 업그레이드 요약 |
| 특별히 강한 시너지 조합 발동 시 | Cat + Onion 공동 공격 이펙트 |

### UX 설계
- 스크린샷 알림은 **화면 좌측 하단에 토스트로** 표시 (Toast_Notification_System.md 참고)
- "스크린샷 저장됨 — 폴더 열기" 버튼으로 원클릭 접근
- 런 결과 화면에 **"공유하기" 버튼** 배치 → Twitter 미리 작성 URL

### 코드 위치
- `Assets/Scripts/System/ScreenshotManager.cs` — 캡처/저장 로직
- `Assets/Scripts/UI/RunResultScreen.cs` — 자동 캡처 트리거
- `Assets/Scripts/UI/PauseMenu.cs` — 수동 캡처 버튼 연결

---

## 주의사항

- `ScreenCapture.CaptureScreenshotAsTexture()`는 반드시 `WaitForEndOfFrame()` 이후 호출
- 텍스처를 다 쓴 뒤 `Destroy(texture)`로 메모리 해제
- `Application.persistentDataPath`는 플랫폼마다 다름 (PC: `%AppData%\..\LocalLow\Company\`)
- WebGL에서는 파일 직접 저장 불가 → `Blob` + JavaScript interop 필요

---

## 참고 링크

- Unity 공식 - ScreenCapture: https://docs.unity3d.com/ScriptReference/ScreenCapture.html
- Unity 공식 - persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Unity Native Share Plugin (모바일): https://github.com/yasirkula/UnityNativeShare
- Steamworks.NET - Screenshots: https://steamworks.github.io/
- Twitter Intent URL 가이드: https://developer.x.com/en/docs/twitter-for-websites/tweet-button/guides/web-intent
