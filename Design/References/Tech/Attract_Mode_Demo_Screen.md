# Attract Mode / 자동 데모 화면 시스템

리서치 날짜: 2026-11-01

## 개요

**Attract Mode**는 플레이어가 메인 메뉴에서 일정 시간 아무 입력도 하지 않을 때 자동으로 시작되는 데모 화면이다. 아케이드 시대부터 이어진 컨벤션으로, 게임이 전시 부스·스트리밍 대기 중·Sleep 화면 대신 켜져 있을 때 게임의 핵심 볼거리를 보여준다. 현대 인디 게임에서는 다음 목적으로 활용된다:

- **Steam Next Fest / 전시 부스**: 아무도 잡고 있지 않을 때 자동으로 게임을 소개
- **스트리머 편의**: 방송 전 대기 중에 화면이 정적이지 않게
- **신규 플레이어 훅**: 메뉴에서 게임 화면을 처음 보고 흥미를 가짐

OnionCat은 2인 협동이 핵심 차별점이므로, 자동 데모에서 고양이+양파의 협동 장면을 보여주면 게임 컨셉을 즉각 전달할 수 있다.

## Unity 구현 방법

### 방법 1: 미리 녹화된 Timeline 재생 (권장 — 간단)

```csharp
// AttractModeManager.cs
public class AttractModeManager : MonoBehaviour {
    [SerializeField] float idleTimeout = 30f;
    [SerializeField] PlayableDirector demoTimeline;
    [SerializeField] CanvasGroup uiGroup;

    float idleTimer;
    bool isPlaying;

    void Update() {
        if (AnyInputThisFrame()) {
            idleTimer = 0f;
            if (isPlaying) StopAttract();
            return;
        }
        idleTimer += Time.deltaTime;
        if (!isPlaying && idleTimer >= idleTimeout)
            StartAttract();
    }

    bool AnyInputThisFrame() =>
        UnityEngine.InputSystem.Keyboard.current?.anyKey.wasPressedThisFrame == true ||
        UnityEngine.InputSystem.Gamepad.current?.wasUpdatedThisFrame == true ||
        UnityEngine.InputSystem.Mouse.current?.delta.ReadValue().sqrMagnitude > 0.1f;

    void StartAttract() {
        isPlaying = true;
        demoTimeline.Play();
        // 메뉴 UI 페이드아웃 (선택)
        StartCoroutine(FadeUI(uiGroup, 1f, 0f, 0.5f));
    }

    void StopAttract() {
        isPlaying = false;
        demoTimeline.Stop();
        idleTimer = 0f;
        StartCoroutine(FadeUI(uiGroup, 0f, 1f, 0.3f));
    }

    IEnumerator FadeUI(CanvasGroup cg, float from, float to, float dur) {
        float t = 0f;
        while (t < dur) {
            cg.alpha = Mathf.Lerp(from, to, t / dur);
            t += Time.deltaTime;
            yield return null;
        }
        cg.alpha = to;
    }
}
```

Timeline에 넣을 것:
- 씬 전환 애니메이션 (Cinemachine 카메라 이동)
- 적과 싸우는 장면 (사전 녹화한 미리 찍기용 씬 or 현재 씬 카메라 조작)
- 타이틀 로고 재등장

### 방법 2: AI 제어 데모 런 (복잡하지만 항상 최신)

```csharp
// DemoAIController.cs — 미리 녹화된 입력 재생 방식
public class DemoAIController : MonoBehaviour {
    [SerializeField] TextAsset recordedInputJson;
    List<DemoFrame> frames;
    int frameIndex;

    void StartPlayback() {
        frames = JsonUtility.FromJson<DemoFrameList>(recordedInputJson.text).frames;
        frameIndex = 0;
        StartCoroutine(PlaybackLoop());
    }

    IEnumerator PlaybackLoop() {
        foreach (var frame in frames) {
            // 녹화된 입력을 PlayerInput에 주입
            SimulateInput(frame);
            yield return null; // 1 fixed update
        }
    }
}

// 입력 녹화 시스템 (개발자 모드에서만)
[Serializable] struct DemoFrame {
    public Vector2 move;
    public bool slash, dash, shoot;
    public Vector2 aimDir;
}
```

### 방법 3: 단순 영상 재생 (가장 간단)

```csharp
// 사전 제작한 MP4 게임플레이 영상을 VideoPlayer로 재생
// Unity VideoPlayer + RenderTexture → RawImage로 전체 화면 오버레이
public class AttractVideoPlayer : MonoBehaviour {
    [SerializeField] VideoPlayer player;
    [SerializeField] float idleTimeout = 20f;
    // ... (방법 1의 idleTimer 로직 동일)
}
```

WebGL/Switch 등 VideoPlayer 지원이 제한된 플랫폼에서는 사용 불가.

### 메인 메뉴 씬 통합

```csharp
// MainMenuScene.cs 에 추가
void Awake() {
    var attract = gameObject.AddComponent<AttractModeManager>();
    attract.idleTimeout = 25f;
    // 또는 인스펙터에서 프리팹으로 배치
}

// 입력 발생 시 Attract 중지 → 메인 메뉴로 복귀
// 키보드/패드 Any Key 감지
```

### 개발 워크플로우

1. **Timeline 씬 별도 제작**: MainMenu 씬 내에 비활성화 오브젝트로 AttractTimeline 보관
2. **카메라 경로 설정**: Cinemachine으로 방 돌아다니는 경로 설정
3. **캐릭터 애니메이션 재생**: Animator.Play()로 idle/walk 애니 연결
4. **자막/설명 텍스트**: TMP로 "고양이와 양파의 협동 탈출" 같은 짧은 소개 문구 표시
5. **루프 설정**: Timeline 끝에서 자동 재시작 (PlayableDirector.extrapolationMode = Hold → 수동 재시작)

## OnionCat 적용 포인트

### 전시용 Attract Mode
- Steam Next Fest, 게임 전시회에서 부스를 비울 때 활용
- **30초 루프**: 고양이 이동 → 적 등장(예고 표시) → 작물 씨앗 발사 → 협동 콤보 COMBO! → 보상 선택 → 반복
- "두 명이서 한 캐릭터" 컨셉이 시각적으로 바로 보이도록 구성

### OnionCat 특화 어트랙트 내용
1. 화분이 고양이 등에 올라탄 모습 (게임 컨셉 즉시 전달)
2. 마우스 커서가 화면에 보이며 씨앗탄 발사 (P2 독립 조작 강조)
3. 협동 콤보 "COMBO!" 금색 텍스트
4. 보상 선택 화면 (고양이·양파 동시에 카드 고르는 장면)

### 구현 난이도
- **방법 1 (Timeline)**: 난이도 낮음, 가장 빠른 구현. 씬 콘텐츠 변경 시 다시 녹화 불필요 (카메라 경로만 유지)
- **방법 2 (AI 제어)**: 난이도 높음. 런타임 게임플레이라 항상 최신 상태. 입력 녹화 툴 별도 제작 필요
- **방법 3 (영상)**: 가장 쉬움. 빌드마다 영상 교체 필요, 용량 주의

**권장**: 방법 1 (Timeline)으로 30초 어트랙트 시퀀스 제작 → 전시 전에 촬영 새로 해서 교체

### 구현 시점
출시/전시 직전에 추가해도 충분한 기능. 게임플레이 완성 후 폴리싱 단계에서 작업.
`Design/07_StoryMeta.md`의 메인 메뉴 씬 완성 후 자연스럽게 붙임.

## 참고 링크
- Unity Docs — Timeline: https://docs.unity3d.com/Packages/com.unity.timeline@1.7/manual/index.html
- Unity Docs — PlayableDirector: https://docs.unity3d.com/ScriptReference/Playables.PlayableDirector.html
- Unity Docs — VideoPlayer: https://docs.unity3d.com/Manual/class-VideoPlayer.html
- GDC 아케이드 게임 어트랙트 모드 역사: https://www.gdcvault.com (검색: attract mode design)
