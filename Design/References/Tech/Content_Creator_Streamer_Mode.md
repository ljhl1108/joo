# 콘텐츠 크리에이터 / 스트리머 모드

리서치 날짜: 2026-10-25

## 개요

스트리머 모드(Streamer Mode)는 게임을 방송하는 콘텐츠 크리에이터를 위한 선택적 기능 묶음이다. 방송 중 개인 정보 노출, 저작권 BGM 문제, 스포일러 노출, OBS/스트리밍 소프트웨어와의 충돌 등 스트리머가 겪는 문제를 게임 내에서 해결한다. 소규모 인디 게임에서도 이 기능 하나로 인기 스트리머에게 방송하기 좋은 게임이라는 입소문이 날 수 있으며, Steam 도달 범위를 늘리는 실용적 마케팅 수단이다.

---

## 핵심 기능 목록

### 필수 (스트리밍 직접 방해하는 것)

| 기능 | 설명 |
|------|------|
| **저작권 BGM 비활성화** | 스트리밍 플랫폼이 저작권 음악을 자동 소거하므로, 인게임 BGM을 대체 무저작권 트랙으로 교체하거나 일부 채널만 뮤트 |
| **개인 정보 마스킹** | 유저 이름, 계정 ID, 저장 파일 경로 등이 화면에 표시되는 경우 *** 또는 가명으로 대체 |

### 권장 (방송 경험 향상)

| 기능 | 설명 |
|------|------|
| **스포일러 화면 경고** | 엔딩, 보스 첫 등장, 스토리 반전 직전 "스포일러 포함" 경고 + 선택적 블랙아웃 |
| **HUD 정보 조정** | 스트리머가 원하는 HUD 요소만 표시 (초보 시청자에게 복잡한 정보를 숨기는 옵션) |
| **캡처 최적화 모드** | CPU/GPU 점유를 스트리밍 여유분에 맞게 낮추는 프리셋 (해상도·그림자·후처리 자동 조절) |

### 선택 (유쾌한 추가 기능)

| 기능 | 설명 |
|------|------|
| **스트리밍 화면 오버레이** | OBS에 게임 정보(HP, 진행 방 수, 협동 콤보 수)를 자동으로 표시할 수 있는 JSON/WebSocket 출력 |
| **챗봇 트리거** | 채팅 명령어로 게임 내 상태 변경 (예: `!buff` → 일시적 디버그 아이템 지급) — 트위치 채널 포인트 연동 |
| **하이라이트 마커** | 플레이어가 버튼으로 "이 순간 하이라이트" 플래그 → `session_highlight_timestamps.txt`에 저장 |

---

## Unity 구현 방법

### 1. 스트리머 모드 설정 구조

```csharp
[System.Serializable]
public class StreamerSettings
{
    public bool enabled;
    public bool muteIngameBgm;       // 저작권 BGM 대체
    public bool maskPersonalInfo;    // 이름 마스킹
    public bool showSpoilerWarning;  // 스포일러 경고
    public bool reducedVisualFx;     // 퍼포먼스 프리셋
}
```

Settings 메뉴에 "스트리머 모드" 토글 추가. `PlayerPrefs` 또는 기존 `settings.json`에 함께 저장.

### 2. BGM 저작권 대체 — AudioMixer 채널 분리

```csharp
// BGM과 환경음을 별도 AudioMixerGroup으로 분리
// 스트리머 모드에서 "BGM" 그룹만 볼륨 0 또는 대체 트랙으로 교체
public void ApplyStreamerAudio(bool streamerMode)
{
    float bgmVolume = streamerMode ? -80f : 0f; // dB
    audioMixer.SetFloat("BGMVolume", bgmVolume);
    
    if (streamerMode && alternativeBgm != null)
        Music.Play(MusicId.StreamerSafe); // CC0 대체 트랙
}
```

OnionCat은 이미 `Sfx`/`Music` 분리 구조 → BGM MixerGroup만 하나 더 추가하면 됨.

### 3. 개인 정보 마스킹 — TextMeshPro 유틸

개인 정보가 화면에 표시되는 곳이 거의 없는 게임(OnionCat 등)에서는 단순히 플레이어 이름을 "고양이 · 양파" 같은 인게임 이름으로 고정 표시하는 것으로 충분.

### 4. 스포일러 경고 화면

```csharp
public IEnumerator ShowSpoilerWarning(string sceneName, System.Action onConfirm)
{
    if (!StreamerSettings.showSpoilerWarning) { onConfirm?.Invoke(); yield break; }
    
    spoilerWarningPanel.SetActive(true);
    spoilerLabel.text = $"{sceneName} — 스포일러 포함 장면입니다";
    
    yield return new WaitUntil(() => confirmPressed);
    spoilerWarningPanel.SetActive(false);
    onConfirm?.Invoke();
}
```

보스 첫 등장 씬 시작 직전, `DungeonManager`의 스테이지 전환 후 트리거.

### 5. 하이라이트 마커 (선택 구현)

```csharp
void Update()
{
    if (Input.GetKeyDown(KeyCode.F12) && StreamerSettings.enabled)
    {
        string timestamp = System.DateTime.Now.ToString("HH:mm:ss");
        string entry = $"[{timestamp}] {GameManager.Instance.CurrentRoom} — 하이라이트 마커\n";
        File.AppendAllText(highlightLogPath, entry);
        ShowToast("🎬 하이라이트 저장됨");
    }
}
```

### 6. 설정 메뉴 UI 추가

```
[ 스트리머 모드 ]  [ON / OFF]

  ✓ BGM 대체 트랙 사용 (저작권 안전)
  ✓ 스포일러 경고 표시
  □ 시각 효과 줄이기 (스트리밍 CPU 절약)
  □ 하이라이트 마커 활성화 (F12)
```

---

## OnionCat 적용 포인트

### 1. BGM 저작권 문제가 없다면 스킵 가능
- OnionCat의 BGM은 칩튠 5곡 — 직접 만든 곡이면 저작권 문제 없음
- 단, 사용 중인 CC0 오디오 중 스트리밍 플랫폼에서 문제가 되는 것이 있는지 `Assets/Audio/LICENSE_AUDIO.txt`로 확인
- 예방책: 스트리머 모드에서 BGM 볼륨 조절 옵션만 제공해도 충분

### 2. 스포일러 경고 — 엔딩 + 최종 보스
- 현재 온실 해금 퀘스트와 엔딩 화면이 있으므로 **최종 보스(현자 마법사) 방 입장 전** 경고 한 줄이면 충분
- `DungeonManager`에서 마지막 스테이지 보스방 입장 시 `GameFeatures.SpoilerWarningSeen` 플래그 확인 + 한 번만 표시

### 3. 가장 쉬운 스트리머 친화 기능 — F12 하이라이트 마커
- 구현 비용: 30분 이내
- 효과: 스트리머가 "이 보스 패턴 대박" 순간에 F12 → 나중에 편집이 쉬워짐
- `IdeaPool`에서 진짜 채택할 만한 빠른 구현 후보

### 4. HUD 정리 옵션 — 초보 시청자를 위한 "HUD 심플 모드"
- OnionCat HUD는 정보가 많음 (합동 게이지, 씨앗 수, 세트 진행도, 야성 게이지 등)
- 스트리머 모드에서 세트 진행도·야성 게이지만 숨기는 "단순 HUD" 옵션 추가
- 시청자 혼란 줄이기 + 화면이 깔끔해져 방송 화질 체감 향상

### 5. 스팀 출시 전 스트리머 키 배포와 연계
- 스트리머 모드 구현 후 → 인디 게임 전문 스트리머들에게 키 배포 + "스트리머 친화 모드 있음" 한 줄 강조
- 한국 인디 게임 유튜버(개발자 채널, 로그라이트 리뷰 채널)에 키 배포 시 이 기능이 허들을 낮춤

### 6. 구현 우선순위

```
즉시 (30분): F12 하이라이트 마커
빠름 (2시간): 스포일러 경고 (보스방 1개)
보통 (반나절): BGM 대체 설정 + 스트리머 모드 토글
선택 (1일+): HUD 심플 모드, OBS WebSocket 출력
```

---

## 참고 링크

- [Chord Progressions 개발로그: 스트리머 모드 도입기](https://chordprogressions.itch.io/chord-progressions/devlog/948034/introducing-streamer-mode)
- [Phantomware 핫픽스: 스트리머 모드 추가](https://eiryudev.itch.io/phantomware/devlog/987294/hotfix-v041)
- [itch.io 개발자 포럼: 스포일러 블랙아웃 구현 토론](https://itch.io/post/1981187)
- [Unity Content Transparency Center (스트리밍 정책 참고)](https://unity.com/unity-content-transparency-center)
