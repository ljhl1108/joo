# Dynamic Adaptive Music System (동적 적응형 BGM 시스템)

리서치 날짜: 2026-08-06

## 개요

**적응형 BGM 시스템**은 게임의 현재 상태(탐색/전투/보스/위기)에 따라 배경음악이 자연스럽게 전환되는 시스템이다. 단순히 씬 전환마다 음악을 바꾸는 것과 달리, 전투가 시작되면 조용한 탐색 음악이 긴장감 있는 전투 음악으로 **크로스페이드**된다.

로그라이크에서 이 시스템은 특히 중요하다. 방에 진입할 때마다 적과 마주치는지 여부, 보스 방인지 여부에 따라 분위기가 달라져야 플레이어가 상황의 긴박함을 음악으로 직감할 수 있다.

OnionCat은 2인 협력 게임이므로 "이제 Crop이 쉴드를 쓸 차례다"는 느낌을 BGM으로도 전달 가능하다.

---

## Unity 구현 방법

### 핵심 도구: AudioMixer + Snapshot

Unity의 **AudioMixer Snapshot** 기능이 핵심이다. 각 게임 상태를 스냅샷으로 정의하고 상태 전환 시 `TransitionToSnapshots()`를 호출하면 파라미터가 부드럽게 보간된다.

#### Step 1: AudioMixer 구조 설정
```
AudioMixer: GameMusic
├── Master Group
│   ├── BGM_Exploration (탐색 음악 트랙)
│   ├── BGM_Combat      (전투 음악 트랙)
│   ├── BGM_Boss        (보스 음악 트랙)
│   └── BGM_Ambient     (환경음 — 항상 낮게 재생)
```

#### Step 2: 스냅샷 생성
AudioMixer에서 우클릭 → Add Snapshot:
- `Snapshot_Exploration`: BGM_Exploration=0dB, BGM_Combat=-80dB, BGM_Boss=-80dB
- `Snapshot_Combat`: BGM_Exploration=-10dB, BGM_Combat=0dB, BGM_Boss=-80dB  
- `Snapshot_Boss`: BGM_Exploration=-80dB, BGM_Combat=-20dB, BGM_Boss=0dB
- `Snapshot_Safe`: BGM_Exploration=0dB, BGM_Combat=-80dB, BGM_Boss=-80dB (상점/쉼터)

#### Step 3: 스냅샷 전환 코드
```csharp
using UnityEngine;
using UnityEngine.Audio;

public class AdaptiveMusicManager : MonoBehaviour {
    [SerializeField] private AudioMixer _mixer;
    [SerializeField] private AudioMixerSnapshot _exploration;
    [SerializeField] private AudioMixerSnapshot _combat;
    [SerializeField] private AudioMixerSnapshot _boss;
    [SerializeField] private AudioMixerSnapshot _safe;

    [SerializeField] private float _transitionTime = 1.5f;

    public void SetState(MusicState state) {
        AudioMixerSnapshot target = state switch {
            MusicState.Exploration => _exploration,
            MusicState.Combat      => _combat,
            MusicState.Boss        => _boss,
            MusicState.Safe        => _safe,
            _                     => _exploration
        };
        target.TransitionTo(_transitionTime);
    }
}

public enum MusicState { Exploration, Combat, Boss, Safe }
```

#### Step 4: AudioSource 설정 (각 트랙 오디오 소스)
```csharp
public class MusicTrackPlayer : MonoBehaviour {
    [SerializeField] private AudioSource _explorationSource;
    [SerializeField] private AudioSource _combatSource;
    [SerializeField] private AudioSource _bossSource;

    private void Start() {
        // 모든 트랙을 처음부터 동시에 재생 (루프) — 볼륨은 Mixer가 제어
        _explorationSource.loop = true;
        _combatSource.loop = true;
        _bossSource.loop = true;

        _explorationSource.Play();
        _combatSource.Play();
        _bossSource.Play();
    }
}
```

> 핵심: 모든 음악 트랙을 **동시에 재생**하되, **Mixer 볼륨**으로 어떤 트랙이 들리는지 제어한다. 이렇게 해야 트랙 간 박자가 어긋나지 않는다.

---

### Step 5: 게임 상태와 연동

#### 방 진입 시 적 유무로 자동 전환
```csharp
public class RoomController : MonoBehaviour {
    [SerializeField] private AdaptiveMusicManager _musicManager;
    private List<Enemy> _enemies;

    private void OnEnemyDied(Enemy e) {
        _enemies.Remove(e);
        if (_enemies.Count == 0) {
            _musicManager.SetState(MusicState.Exploration);  // 전투 종료
        }
    }

    public void OnRoomEntered() {
        if (_enemies.Count > 0) {
            _musicManager.SetState(MusicState.Combat);       // 전투 시작
        }
    }

    public void OnBossRoomEntered() {
        _musicManager.SetState(MusicState.Boss);
    }
}
```

---

### 레이어드 음악 (Layered / Stacked Music) — 고급 방법

단일 트랙 교체 대신, **같은 멜로디를 여러 악기 레이어로 분리**하여 전환:
- 탐색: 피아노 + 약한 드럼
- 전투 시작: 드럼 세기 증가, 전기기타 레이어 추가
- 보스: 오케스트라 풀 레이어

```
Track: piano.wav     → 항상 재생
Track: light_drum.wav → 탐색 + 전투
Track: heavy_drum.wav → 전투 + 보스만
Track: boss_lead.wav  → 보스만
```

스냅샷에서 각 레이어 볼륨을 조절하면 자연스러운 강약 조절이 된다.

---

### 보스 체력 연동 (상급)
```csharp
// 보스 체력 50% 이하 → 더 긴박한 음악
public class BossController : MonoBehaviour {
    [SerializeField] private AdaptiveMusicManager _musicManager;
    [SerializeField] private AudioMixerSnapshot _bossPhase2;

    private void OnHealthChanged(float hp, float maxHp) {
        if (hp / maxHp < 0.5f) {
            _bossPhase2.TransitionTo(2.0f);  // 2초에 걸쳐 2페이즈 음악으로
        }
    }
}
```

---

## OnionCat 적용 포인트

### 1. 추천 음악 상태 구조
OnionCat의 게임플레이 흐름에 맞는 4가지 상태:

| 상태 | 트리거 조건 | 음악 느낌 |
|------|-------------|-----------|
| `Safe` | 상점 방, 쉼터 방 진입 | 포근한 피아노, 조용한 농장 느낌 |
| `Exploration` | 적 없는 방, 복도 이동 | 긴장감 낮은 탐험 BGM |
| `Combat` | 일반 적 스폰 | 리듬감 있는 전투 BGM |
| `Boss` | 보스 방 진입 | 웅장한 보스 테마 |

### 2. OnionCat 특성 활용 — 2인 협력과 음악
Cat + Crop이 "위기" 상황(체력 20% 이하)일 때 별도 `Crisis` 스냅샷으로 전환:
- BGM 피치를 +2 semitone 높임 (긴박감 증가)
- `AudioMixer.SetFloat("MasterPitch", 1.12f)`로 구현

### 3. 씬 전환 시 BGM 유지
`DontDestroyOnLoad(gameObject)`를 `AdaptiveMusicManager`에 적용하면 씬 전환 시에도 음악이 끊기지 않는다:
```csharp
private void Awake() {
    if (_instance != null) { Destroy(gameObject); return; }
    _instance = this;
    DontDestroyOnLoad(gameObject);
}
```

### 4. 구현 순서 (초심자 권장)
1. 탐색 BGM AudioSource 하나만 만들어 루프 재생
2. 전투 BGM AudioSource 추가, Mixer 연결
3. AudioMixer Snapshot 2개 (Exploration / Combat) 생성
4. `RoomController`에서 적 스폰/사망 시 `SetState()` 호출
5. 전환 시간을 1~2초로 테스트하며 자연스러운 값 조정
6. 보스 방 추가 후 Boss 스냅샷 추가

---

## 참고 링크

- Unity 공식 — AudioMixer 스냅샷: https://docs.unity3d.com/Manual/AudioMixer.html
- Unity 공식 — TransitionToSnapshots: https://docs.unity3d.com/ScriptReference/Audio.AudioMixer.TransitionToSnapshots.html
- YouTube 튜토리얼 키워드: "Unity adaptive music system AudioMixer snapshots"
- GDC 강연 (개념): "Adaptive Audio in Games — Wwise/FMOD concepts"
- Unity Learn: "Introduction to Audio in Unity 2D"
