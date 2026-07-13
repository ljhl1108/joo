# BGM 씬 전환 매니저 (BGM Scene Transition Manager)

리서치 날짜: 2026-07-13

## 개요

배경음악(BGM)이 씬/방 전환 시 뚝 끊기거나, 같은 트랙이 재시작되거나, 
이미 재생 중인 음악이 무한 중첩되는 문제는 완성도를 크게 낮춘다.
OnionCat처럼 메인 메뉴 → 던전 → 방마다 분위기가 달라지는 게임에서는
씬 전환에 맞춘 **BGM 크로스페이드(교차 페이드)** 와 **싱글톤 오디오 매니저** 가 필수다.

---

## Unity 구현 방법

### A. 싱글톤 BGM 매니저 (DontDestroyOnLoad)

씬이 바뀌어도 오디오 소스가 파괴되지 않도록 싱글톤으로 관리.

```csharp
using System.Collections;
using UnityEngine;

public class BGMManager : MonoBehaviour
{
    public static BGMManager Instance { get; private set; }

    [SerializeField] private AudioSource sourceA;
    [SerializeField] private AudioSource sourceB;
    [SerializeField] private float fadeDuration = 1.0f;

    private AudioSource _active;
    private AudioSource _inactive;
    private Coroutine _fadeCoroutine;

    private void Awake()
    {
        if (Instance != null)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);

        _active = sourceA;
        _inactive = sourceB;
    }

    // 즉시 재생 (씬 전환 없이 같은 트랙 확인 포함)
    public void Play(AudioClip clip, float volume = 1f)
    {
        if (_active.clip == clip && _active.isPlaying) return;  // 이미 재생 중이면 무시

        if (_fadeCoroutine != null) StopCoroutine(_fadeCoroutine);
        _fadeCoroutine = StartCoroutine(CrossFade(clip, volume));
    }

    public void Stop(float fadeOut = 1f)
    {
        if (_fadeCoroutine != null) StopCoroutine(_fadeCoroutine);
        _fadeCoroutine = StartCoroutine(FadeOut(_active, fadeOut));
    }

    private IEnumerator CrossFade(AudioClip newClip, float targetVolume)
    {
        // inactive 소스에 새 클립 세팅 후 음소거 상태로 시작
        _inactive.clip = newClip;
        _inactive.volume = 0f;
        _inactive.Play();

        float elapsed = 0f;
        float startVolume = _active.volume;

        while (elapsed < fadeDuration)
        {
            elapsed += Time.unscaledDeltaTime;   // 일시정지 중에도 페이드
            float t = elapsed / fadeDuration;
            _active.volume = Mathf.Lerp(startVolume, 0f, t);
            _inactive.volume = Mathf.Lerp(0f, targetVolume, t);
            yield return null;
        }

        _active.Stop();
        _active.clip = null;

        // active와 inactive 교체
        (_active, _inactive) = (_inactive, _active);
        _fadeCoroutine = null;
    }

    private IEnumerator FadeOut(AudioSource source, float duration)
    {
        float startVolume = source.volume;
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.unscaledDeltaTime;
            source.volume = Mathf.Lerp(startVolume, 0f, elapsed / duration);
            yield return null;
        }
        source.Stop();
    }
}
```

> **두 AudioSource 크로스페이드**: 기존 트랙을 페이드 아웃하면서 동시에 새 트랙을 페이드 인.  
> 한 소스만 쓰면 공백이 생기거나 즉각 전환됨.

### B. BGMTrackDatabase (ScriptableObject)

씬/상황별 클립을 하드코딩 없이 관리.

```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "BGMDatabase", menuName = "OnionCat/BGM Database")]
public class BGMDatabase : ScriptableObject
{
    public AudioClip mainMenu;
    public AudioClip dungeon_Floor1;
    public AudioClip dungeon_Floor2;
    public AudioClip dungeon_Floor3;
    public AudioClip bossRoom;
    public AudioClip shopRoom;
    public AudioClip gameOver;
    public AudioClip runClear;
}
```

### C. 씬 로드 시 자동 BGM 전환

각 씬의 초기화 오브젝트(SceneInitializer 등)에서 호출.

```csharp
[SerializeField] private BGMDatabase bgmDB;

private void Start()
{
    BGMManager.Instance.Play(bgmDB.dungeon_Floor1, volume: 0.7f);
}
```

### D. 방(Room) 이벤트 기반 전환

```csharp
// RoomManager 또는 방 전환 이벤트에서
public void OnEnterBossRoom()
{
    BGMManager.Instance.Play(bgmDB.bossRoom);
}

public void OnExitBossRoom()
{
    BGMManager.Instance.Play(bgmDB.dungeon_Floor2);  // 이전 던전 음악으로 복귀
}
```

### E. 볼륨 설정 연동

```csharp
// 설정 메뉴에서 호출
public void SetMasterVolume(float value)
{
    // AudioMixer 사용 시
    audioMixer.SetFloat("BGMVolume", Mathf.Log10(Mathf.Max(value, 0.0001f)) * 20f);
}
```

AudioMixer를 사용하면 BGM, SFX, 마스터 볼륨을 독립 조절 가능.  
`PlayerPrefs.SetFloat("BGMVolume", value)` 로 설정 저장 후 게임 시작 시 로드.

---

## OnionCat 적용 포인트

### 1. 씬별 BGM 흐름
```
메인 메뉴         → mainMenu (잔잔한 픽셀아트 테마)
런 시작 직전      → dungeon_Floor1 (긴장감 상승)
일반 방 진입      → 현재 층 BGM 유지 (재시작 없음)
보스 방 진입      → bossRoom (강렬한 테마) ← 이벤트로 트리거
보스 처치         → 짧은 승리 스팅 후 다음 층 BGM으로 크로스페이드
게임 오버         → gameOver 후 자동 페이드아웃
런 클리어         → runClear (엔딩 테마)
```

### 2. 보스 전투 중 "저체력 음악 가속"
- 보스가 50% HP 이하로 내려가면 동일 트랙을 더 빠른 피치(pitch)로 재생
- `AudioSource.pitch = 1.2f` 로 간단히 구현 가능

```csharp
// 보스 체력 변화 시 호출
public void OnBossHealthPhase2()
{
    BGMManager.Instance.SetPitch(1.15f);
}
```

### 3. 방 전환 중 BGM 처리
- 방 전환 페이드 아웃 시작 → BGM 볼륨도 약간 덕킹(살짝 낮춤) → 새 방 로드 완료 후 복귀
- 같은 층이면 동일 BGM 유지 (재생 위치 그대로)

### 4. 협동 보너스 이벤트 연출
- 두 플레이어 동시 필살기 사용 시 → 0.5초간 BGM 피치 올라갔다 내려오는 연출
- `Time.unscaledDeltaTime` 사용 → 히트스톱(Time.timeScale=0) 중에도 BGM 자연스럽게 유지

---

## 완성도 체크리스트

- [ ] 씬 간 BGM 크로스페이드 (공백 없음)
- [ ] 같은 트랙 재요청 시 재시작 방지
- [ ] DontDestroyOnLoad 싱글톤 중복 방지
- [ ] AudioMixer 연동으로 볼륨 세분 조절
- [ ] Time.unscaledDeltaTime 사용 (일시정지 중 페이드 정상 동작)
- [ ] 보스 방 전환 이벤트 연결
- [ ] PlayerPrefs 볼륨 저장/로드

---

## 참고 링크

- [Unity 공식 - AudioSource](https://docs.unity3d.com/Manual/class-AudioSource.html)
- [Unity 공식 - AudioMixer](https://docs.unity3d.com/Manual/AudioMixer.html)
- [Unity 공식 - DontDestroyOnLoad](https://docs.unity3d.com/ScriptReference/Object.DontDestroyOnLoad.html)
- [Brackeys - Audio Manager in Unity (YouTube)](https://www.youtube.com/watch?v=6OT43pvUyfY)
- [Game Dev Guide - Music Crossfade (YouTube)](https://www.youtube.com/watch?v=SXLB6_lPeT4)
