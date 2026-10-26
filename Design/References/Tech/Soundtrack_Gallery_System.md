# 인게임 사운드트랙 갤러리 / 뮤직 테스트 (Soundtrack Gallery System)

리서치 날짜: 2026-10-26

## 개요

**사운드트랙 갤러리(뮤직 테스트)**는 플레이어가 메인 메뉴나 설정 화면에서 게임 내 BGM을 자유롭게 감상할 수 있는 기능이다.

닌텐도 게임(닌텐도 vs. 카프콤 시절부터), Hades, Streets of Rage 4, Shovel Knight 등 수많은 인디·AAA 게임에서 제공한다. 단순해 보이지만 다음 이유로 "완성된 게임"의 중요 표시가 된다:

- **작곡가에 대한 존중**: 배경으로만 듣던 음악을 전면에 내세울 수 있게 함
- **플레이어 재방문**: BGM 감상 자체가 게임을 다시 여는 이유가 됨
- **CC0 음악 사용 시 출처 표시**: OnionCat처럼 CC0 음악을 쓰는 경우, 갤러리에 출처를 명시하는 것이 라이선스 준수의 좋은 방법

---

## Unity 구현 방법

### 데이터 구조

```csharp
// SoundtrackEntry.cs (ScriptableObject 또는 단순 직렬화 가능 클래스)
[System.Serializable]
public class SoundtrackEntry
{
    public string trackTitle;        // "던전 전투 - Stage 1"
    public string composerCredit;    // "작곡: OGA / CC0"
    public string sourceUrl;         // "https://opengameart.org/..."
    public AudioClip clip;
    public bool unlockedFromStart;   // false면 MetaProgress에서 해금 확인
    public string unlockHint;        // 잠겼을 때 보여줄 힌트 "보스를 처치하면 해금됩니다"
}
```

### SoundBank와 연동

OnionCat은 `Assets/Resources/Audio/SoundBank.asset`에서 음악을 관리하므로, 갤러리 전용 리스트를 SoundBank에 추가하는 것이 가장 자연스럽다:

```csharp
// SoundBank.asset에 추가
[Header("Soundtrack Gallery")]
public SoundtrackEntry[] soundtrackEntries;
```

또는 별도 ScriptableObject:
```csharp
// Assets/Resources/Audio/SoundtrackGallery.asset
[CreateAssetMenu(fileName = "SoundtrackGallery", menuName = "OnionCat/Audio/Soundtrack Gallery")]
public class SoundtrackGallery : ScriptableObject
{
    public SoundtrackEntry[] tracks;
}
```

### 재생 컨트롤러

```csharp
// SoundtrackGalleryUI.cs
public class SoundtrackGalleryUI : MonoBehaviour
{
    [SerializeField] SoundtrackGallery gallery;
    [SerializeField] AudioSource previewSource;
    [SerializeField] Slider progressSlider;
    [SerializeField] TMP_Text titleText;
    [SerializeField] TMP_Text creditText;

    int _currentIndex = -1;

    public void PlayTrack(int index)
    {
        var entry = gallery.tracks[index];
        if (!IsUnlocked(entry))
            return;

        _currentIndex = index;
        previewSource.clip = entry.clip;
        previewSource.Play();
        titleText.text = entry.trackTitle;
        creditText.text = entry.composerCredit;
    }

    void Update()
    {
        if (previewSource.isPlaying && previewSource.clip != null)
            progressSlider.value = previewSource.time / previewSource.clip.length;
    }

    bool IsUnlocked(SoundtrackEntry entry)
    {
        if (entry.unlockedFromStart) return true;
        // MetaProgress 확인 로직
        return MetaProgress.Instance.IsSoundtrackUnlocked(entry.trackTitle);
    }

    public void Pause()
    {
        if (previewSource.isPlaying) previewSource.Pause();
        else previewSource.UnPause();
    }

    public void Stop()
    {
        previewSource.Stop();
        _currentIndex = -1;
    }
}
```

### UI 레이아웃 (OnionCat HUD 1920×1080 기준)

```
┌─────────────────────────────────────────┐
│  🎵 사운드트랙                           │
├─────────────────┬───────────────────────┤
│ [트랙 목록]      │ 현재 재생:             │
│ ■ 메인 테마     │ 던전 전투 - Stage 1    │
│   던전 전투 1   │ 작곡: OGA / CC0        │
│ 🔒 보스 테마    │ [출처 링크 표시]        │
│   휴식 정원     │                        │
│   ...          │ ──────────■──── 2:34   │
│                │ [◀◀] [▶/❚❚] [▶▶]      │
└─────────────────┴───────────────────────┘
```

잠긴 트랙은 자물쇠 아이콘 + 힌트 툴팁, 클릭하면 재생 불가 안내.

### 메인 메뉴 진입점

```csharp
// MainMenuUI.cs에 버튼 추가
public void OpenSoundtrackGallery()
{
    // 메인 메뉴에서만 접근 가능 (게임 중에는 현재 BGM이 있으므로)
    // 이전에 재생 중이던 Music을 정지하고 갤러리 열기
    Music.Stop();
    soundtrackGalleryPanel.SetActive(true);
}
```

---

## 해금 연동 (MetaProgress)

OnionCat의 `MetaProgress`(meta.json)와 연동해 런 진행에 따라 트랙을 해금:

```csharp
// MetaProgress.cs에 추가
public HashSet<string> unlockedSoundtracks = new();

public bool IsSoundtrackUnlocked(string trackId) =>
    unlockedSoundtracks.Contains(trackId);

public void UnlockSoundtrack(string trackId)
{
    if (unlockedSoundtracks.Add(trackId))
        Save(); // meta.json 갱신
}
```

해금 트리거 예시:
- 스테이지 1 첫 클리어 → 스테이지 1 BGM 해금
- 보스 처치 → 보스 BGM 해금
- 런 10회 → 메인 테마 해금 (원래 잠겨있을 경우)

OnionCat은 CC0 음악을 쓰므로, 처음부터 전부 해금해도 문제 없음. 해금 시스템은 선택 사항.

---

## CC0 음악 출처 표시 (OnionCat 필수)

OnionCat은 `Assets/Audio/LICENSE_AUDIO.txt`에 출처를 기록한다. 갤러리에서 이를 화면에 표시하면:

1. 라이선스 준수를 직관적으로 달성
2. 원작자에게 크레딧
3. "이 게임은 제대로 만든 게임이구나"라는 신뢰감

```csharp
// SoundtrackEntry.sourceUrl 필드를 화면에 표시
// 클릭하면 클립보드에 복사 (웹 링크 열기는 Unity Application.OpenURL 사용)
public void CopySourceUrl()
{
    GUIUtility.systemCopyBuffer = currentEntry.sourceUrl;
    // 또는: Application.OpenURL(currentEntry.sourceUrl);
}
```

---

## OnionCat 적용 포인트

1. **즉시 구현 가능** — SoundtrackGallery ScriptableObject 하나 + UI 패널 하나면 됨. `SoundBank`에 이미 AudioClip이 있으므로 자산 추가 불필요.

2. **메인 메뉴에 "음악 감상" 버튼** — 설정 메뉴 하위 항목 또는 별도 버튼. 플레이타임이 쌓인 플레이어에게 재방문 이유를 줌.

3. **CC0 출처 표시** — `LICENSE_AUDIO.txt`의 내용을 갤러리 UI에서 표시. 게임 완성도를 높이고 라이선스 준수를 사용자에게 보여줌.

4. **런 중 접근 제한** — 갤러리는 메인 메뉴 전용. 런 중 음악 변경은 `Music.Play()` API로 별도 처리.

5. **구현 우선순위** — 출시 전 "Nice to have", 초기 개발보다는 콘텐츠가 어느 정도 갖춰진 후에 추가.

---

## 참고 링크

- Unity AudioSource API: https://docs.unity3d.com/ScriptReference/AudioSource.html
- Unity AudioClip 스트리밍: https://docs.unity3d.com/ScriptReference/AudioClip.html
- OpenGameArt (CC0 음악 출처): https://opengameart.org/
- Hades 사운드트랙 갤러리 UX (YouTube): https://www.youtube.com/results?search_query=hades+music+gallery+ui
- ScriptableObject 기반 사운드 시스템: https://unity.com/kr/blog/games/three-ways-to-architect-your-game-with-scriptableobjects
