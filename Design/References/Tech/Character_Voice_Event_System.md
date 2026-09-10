# 캐릭터 보이스 이벤트 시스템 (Character Voice Event System)

리서치 날짜: 2026-09-10

## 개요

캐릭터 보이스 이벤트 시스템이란, 게임 내 특정 상황(피격, 업그레이드 획득, 방 클리어, 체력 위기 등)에서 짧은 캐릭터 대사/감탄사가 자동으로 재생되는 시스템이다. Hades가 가장 잘 구현한 사례로, 전투 중 캐릭터들이 실시간으로 서로 반응하는 대사를 나눠 세계관 몰입도를 크게 높인다. OnionCat에서는 Cat(고양이 울음)과 Onion(식물 신음)의 독특한 보이스 반응이 캐릭터 개성과 감정적 연결감을 만들어낼 핵심 시스템이다.

---

## Unity 구현 방법

### 1. 보이스 이벤트 정의 (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "OnionCat/VoiceEventData")]
public class VoiceEventData : ScriptableObject
{
    public VoiceEventType eventType;
    public AudioClip[] clips;          // 랜덤 선택
    [Range(0f, 1f)] public float volume = 0.8f;
    public float cooldown = 3f;        // 같은 이벤트 재사용 금지 시간
    public bool interruptCurrentVoice; // 현재 재생 중인 보이스 끊을지
}

public enum VoiceEventType
{
    Hit,
    Death,
    UpgradeObtained,
    RoomCleared,
    LowHealth,      // HP 25% 이하
    DashUsed,
    ParrySuccess,
    BossEncounter,
    HealthPickup,
    SynergyActivated,
}
```

### 2. 보이스 이벤트 매니저

```csharp
public class VoiceEventManager : MonoBehaviour
{
    public static VoiceEventManager Instance { get; private set; }

    [SerializeField] private VoiceEventData[] _catVoices;
    [SerializeField] private VoiceEventData[] _onionVoices;

    private AudioSource _catSource;
    private AudioSource _onionSource;
    private Dictionary<VoiceEventType, float> _lastPlayTimes = new();

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        _catSource = gameObject.AddComponent<AudioSource>();
        _onionSource = gameObject.AddComponent<AudioSource>();
    }

    public void TriggerVoice(CharacterType character, VoiceEventType eventType)
    {
        VoiceEventData[] voices = character == CharacterType.Cat ? _catVoices : _onionVoices;
        VoiceEventData data = Array.Find(voices, v => v.eventType == eventType);
        if (data == null) return;

        // 쿨다운 체크
        if (_lastPlayTimes.TryGetValue(eventType, out float lastTime))
            if (Time.time - lastTime < data.cooldown) return;

        AudioSource src = character == CharacterType.Cat ? _catSource : _onionSource;
        if (data.interruptCurrentVoice) src.Stop();
        if (src.isPlaying) return; // 이미 말하는 중이면 무시

        AudioClip clip = data.clips[Random.Range(0, data.clips.Length)];
        src.PlayOneShot(clip, data.volume);
        _lastPlayTimes[eventType] = Time.time;
    }
}
```

### 3. 이벤트 트리거 연결

```csharp
// HealthSystem.cs에서
public void TakeDamage(int amount)
{
    _hp -= amount;
    VoiceEventManager.Instance.TriggerVoice(CharacterType.Cat, VoiceEventType.Hit);
    if (_hp <= _maxHp * 0.25f)
        VoiceEventManager.Instance.TriggerVoice(CharacterType.Cat, VoiceEventType.LowHealth);
    if (_hp <= 0)
        VoiceEventManager.Instance.TriggerVoice(CharacterType.Cat, VoiceEventType.Death);
}

// UpgradeSystem.cs에서
public void OnUpgradeSelected(UpgradeData upgrade)
{
    VoiceEventManager.Instance.TriggerVoice(CharacterType.Cat, VoiceEventType.UpgradeObtained);
    // Onion은 1초 후 반응 (캐릭터 대화 느낌)
    StartCoroutine(DelayedOnionVoice(VoiceEventType.UpgradeObtained, 1.0f));
}
```

### 4. 두 캐릭터 간 대화 시스템 (대화형 반응)
특정 이벤트에서 Cat과 Onion이 짧게 주고받는 대화 형식:

```csharp
public class VoiceDialogue
{
    public VoiceEventType trigger;
    public AudioClip catLine;
    public AudioClip onionResponse;
    public float responseDelay = 0.8f; // Cat 대사 후 Onion 반응까지 딜레이
}

// 예시: 보스 방 진입 시
// Cat: "냐아..." (긴장)
// (0.8초 후)
// Onion: "바스락..." (파들파들 떨림)
```

### 5. 배경음악과 믹싱
보이스가 BGM을 압도하지 않도록 AudioMixer 설정:
```
AudioMixer Groups:
- Master
  - BGM (Volume: -3dB)
  - SFX
    - Voices (Volume: 0dB, Ducking: BGM -6dB when active)
    - Combat SFX
```

```csharp
// 보이스 재생 시 BGM 살짝 줄이기
_mixer.SetFloat("BGMVolume", -9f); // Duck
StartCoroutine(RestoreBGMAfterVoice(clip.length));
```

---

## OnionCat 적용 포인트

### 언어 없는 보이스 철학
OnionCat의 캐릭터(고양이 + 채소)는 실제 언어를 사용하지 않는다. 대신:
- **Cat**: `냥`, `끄아`, `야옹`, `냥냥` 등 고양이 감탄사
- **Onion**: `바스락`, `스르륵`, `으윽`, `꺄아` 등 식물/채소 의인화 소리
- 이 보이스들이 감정을 전달하면서도 귀엽고 세계관에 맞음

### 핵심 트리거 우선순위 (OnionCat v1.0 기준)
| 우선순위 | 이벤트 | Cat 보이스 | Onion 보이스 |
|---------|--------|-----------|-------------|
| 1 | 사망 | 길고 서글픈 야옹 | 시든 소리 |
| 2 | 보스 조우 | 긴장한 냥 | 파들파들 잎 소리 |
| 3 | 피격 | 짧은 끄아 | 흙 흘리는 소리 |
| 4 | 업그레이드 획득 | 기쁜 냥냥 | 생기있는 잎 소리 |
| 5 | 패리 성공 | 자신있는 냥 | 방패 소리 |
| 6 | 체력 위기 | 헐떡이는 소리 | 시들어가는 소리 |
| 7 | 방 클리어 | 짧고 밝은 냥 | 작은 기쁨 소리 |

### 쿨다운 권장 설정
- 피격: 1.5초 (빠른 전투에서 너무 자주 나오면 지침)
- 업그레이드: 0초 (항상 재생)
- 체력 위기: 10초 (계속 나오면 스트레스)
- 방 클리어: 0초 (항상 재생)

### 구현 순서 (최소 viable)
1. `AudioSource` 두 개 (Cat, Onion 각각) 세팅
2. 피격/사망 보이스 먼저 연결 (가장 자주 발생)
3. `VoiceEventManager` 싱글턴 생성
4. `[SerializeField]` AudioClip 배열에 에디터에서 드래그 앤 드롭 설정 필요
5. 업그레이드/보스 이벤트 차례로 연결

---

## 참고 링크

- Hades 보이스 시스템 분석: https://www.gamedeveloper.com/audio/how-hades-uses-voice-lines-to-create-the-illusion-of-a-living-world
- Unity AudioMixer Ducking: https://docs.unity3d.com/Manual/AudioMixer.html
- GameAudioGDC - Reactive Dialogue: https://www.gdcvault.com/play/1024710/Reactive-Dialogue-Systems
- 게임 사운드 디자인 입문: https://www.youtube.com/watch?v=Ejr4f0SX5Rk
