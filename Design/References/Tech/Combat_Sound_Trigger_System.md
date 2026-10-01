# Combat Sound Trigger System (전투 사운드 트리거 시스템)

리서치 날짜: 2026-10-01

## 개요

전투 이벤트(공격, 피격, 사망, 패링)가 발생하는 순간 알맞은 사운드를 재생하는 시스템.
단순한 `AudioSource.Play()`가 아니라 **변주(variation), 위치 기반 볼륨, 이벤트 분리**가 갖춰질 때 
픽셀아트 전투 특유의 찰진 타격감이 만들어진다.

OnionCat 관련성: 고양이 근접 슬래시, 양파 원거리 발사, 공통 피격/사망 사운드 모두 이 시스템으로 처리.

---

## Unity 구현 방법

### 1. SoundClipCollection — 복수 클립 + 피치 랜덤

```csharp
[System.Serializable]
public class SoundClipCollection
{
    public AudioClip[] clips;
    [Range(0f, 1f)] public float volume = 1f;
    [Range(-0.3f, 0.3f)] public float pitchVariance = 0.1f;

    public void Play(AudioSource source)
    {
        if (clips == null || clips.Length == 0) return;
        source.clip = clips[Random.Range(0, clips.Length)];
        source.pitch = 1f + Random.Range(-pitchVariance, pitchVariance);
        source.volume = volume;
        source.PlayOneShot(source.clip);
    }
}
```

**왜 클립 배열인가?**  
같은 소리를 반복하면 뇌가 패턴을 인식해 단조롭게 느껴진다. 2~4개의 미묘하게 다른 클립을 무작위로 선택하면 자연스럽게 들린다.

**왜 피치 랜덤인가?**  
±10~15%의 피치 변동만으로도 타격음이 살아있는 느낌을 준다. 너무 크면 이상하게 들림.

---

### 2. CombatSoundSet ScriptableObject

```csharp
[CreateAssetMenu(menuName = "OnionCat/Audio/CombatSoundSet")]
public class CombatSoundSet : ScriptableObject
{
    [Header("공격")]
    public SoundClipCollection attack;       // 공격 시작 시
    public SoundClipCollection attackHit;    // 공격이 적에게 맞았을 때
    public SoundClipCollection attackMiss;   // 헛스윙

    [Header("피격")]
    public SoundClipCollection hurt;         // 피해를 받음
    public SoundClipCollection block;        // 쉴드로 막음 (Onion 전용)
    public SoundClipCollection parry;        // 패링 성공

    [Header("상태")]
    public SoundClipCollection death;
    public SoundClipCollection dash;         // Cat 전용
    public SoundClipCollection shoot;        // Onion 발사
}
```

ScriptableObject로 만들면 고양이 전투음셋, 적 전투음셋을 Inspector에서 교체 가능.

---

### 3. CombatSoundPlayer — 컴포넌트 (캐릭터/적에 부착)

```csharp
public class CombatSoundPlayer : MonoBehaviour
{
    [SerializeField] private CombatSoundSet soundSet;
    [SerializeField] private AudioSource audioSource;

    private void Awake()
    {
        if (audioSource == null)
            audioSource = GetComponent<AudioSource>();
    }

    public void PlayAttack()     => soundSet?.attack.Play(audioSource);
    public void PlayAttackHit()  => soundSet?.attackHit.Play(audioSource);
    public void PlayHurt()       => soundSet?.hurt.Play(audioSource);
    public void PlayBlock()      => soundSet?.block.Play(audioSource);
    public void PlayParry()      => soundSet?.parry.Play(audioSource);
    public void PlayDeath()      => soundSet?.death.Play(audioSource);
    public void PlayDash()       => soundSet?.dash.Play(audioSource);
    public void PlayShoot()      => soundSet?.shoot.Play(audioSource);
}
```

---

### 4. 기존 전투 코드에서 호출

#### 고양이 근접 공격 (MeleeAttack.cs)
```csharp
private CombatSoundPlayer soundPlayer;

private void Awake()
{
    soundPlayer = GetComponent<CombatSoundPlayer>();
}

private void PerformAttack()
{
    soundPlayer?.PlayAttack();      // 슬래시 시작음

    // 히트 처리
    foreach (var enemy in hitEnemies)
    {
        enemy.TakeDamage(damage);
        soundPlayer?.PlayAttackHit(); // 적에게 맞은 확인음
    }
}
```

#### AnimationEvent 연동 (픽셀아트 프레임 타이밍)
```
Animator State: Cat_Attack
  → AnimationEvent: OnAttackSwingFrame() (슬래시 모션 시작 프레임)
  → AnimationEvent: OnAttackHitFrame()   (히트박스 활성화 프레임)

// MonoBehaviour에서:
public void OnAttackSwingFrame() => soundPlayer?.PlayAttack();
public void OnAttackHitFrame()   // 히트 판정 + PlayAttackHit은 TakeDamage 콜백에서
```

#### 피격 (DamageReceiver.cs)
```csharp
public void TakeDamage(int amount, DamageType type)
{
    // ... 피해 계산 ...

    if (isBlocked)
        soundPlayer?.PlayBlock();
    else if (isParried)
        soundPlayer?.PlayParry();
    else
        soundPlayer?.PlayHurt();
}
```

---

### 5. 위치 기반 볼륨 — AudioSource 설정

Inspector에서 AudioSource 컴포넌트 설정:
```
Spatial Blend: 1 (완전 3D — 카메라 거리에 따라 볼륨 자동 감소)
Min Distance: 2
Max Distance: 15
Rolloff: Logarithmic (자연스러운 감쇠)
```

3D 사운드를 쓰면 화면 밖 전투음이 자연스럽게 작아진다.

---

### 6. AudioMixer 그룹 연결

```
Audio Mixer 계층:
  Master
  ├── SFX
  │   ├── Combat       ← CombatSoundPlayer들이 사용
  │   ├── UI
  │   └── Environment
  └── BGM
```

`audioSource.outputAudioMixerGroup = combatGroup;` (Awake 또는 Inspector에서)

설정 메뉴에서 SFX 볼륨을 바꾸면 모든 전투음에 자동 반영됨.

---

### 7. 오브젝트 풀링된 투사체 사운드

투사체는 Pool에서 Spawn되므로 Awake 대신 OnEnable:
```csharp
public class ProjectileSoundPlayer : MonoBehaviour
{
    [SerializeField] private SoundClipCollection spawnSound;
    [SerializeField] private SoundClipCollection impactSound;
    private AudioSource audioSource;

    private void Awake() => audioSource = GetComponent<AudioSource>();
    private void OnEnable() => spawnSound?.Play(audioSource);  // 발사 시

    public void OnImpact() => impactSound?.Play(audioSource);  // 충돌 시
}
```

---

## OnionCat 적용 포인트

### 사운드셋 파일 구조 (Inspector에서 설정)
```
Assets/Audio/CombatSounds/
├── Cat_CombatSoundSet.asset      ← Cat 슬래시/피격/대쉬
├── Onion_CombatSoundSet.asset    ← Onion 발사/쉴드/패링
├── Slime_CombatSoundSet.asset    ← 슬라임 피격/사망
└── Projectile_CombatSoundSet.asset
```

### OnionCat 특화 사운드 이벤트

| 이벤트 | 타이밍 | 사운드 효과 |
|--------|--------|------------|
| Cat 슬래시 시작 | AnimationEvent (swing frame) | 검풍음 |
| Cat 슬래시 히트 | TakeDamage 콜백 | 타격음 |
| Onion 발사 | Projectile Spawn | 발사음 |
| Onion 쉴드 활성화 | Shield.Activate() | 방패 올리는 소리 |
| Onion 패링 성공 | Parry 판정 순간 | 금속 튕기는 소리 + 히트스톱 |
| 적 사망 (근거리) | Death → Ground | 쓰러지는 소리 |
| 적 사망 (원거리) | Death → Pop | 터지는 소리 |

### 패링 사운드 특별 처리
패링은 게임에서 가장 만족스러운 사운드여야 한다:
```csharp
// ParrySystem.cs
private void OnParrySuccess()
{
    soundPlayer?.PlayParry();
    
    // 추가 연출: 히트스톱 + 음량 강조
    HitstopManager.Instance.DoHitstop(0.15f);
    // parry 사운드는 볼륨 1.2f, 피치 1.1f로 고정 (랜덤 없음 — 항상 선명하게)
}
```

### 같은 소리 겹침 방지 (Anti-Stutter)
여러 적이 동시에 피격될 때 같은 사운드가 n번 겹치면 이상하게 들린다:
```csharp
// PlayOneShot은 겹쳐서 재생됨 — 동일 클립 0.05초 내 중복 방지
private float lastPlayTime;
private AudioClip lastClip;

public void Play(AudioSource source)
{
    var clip = clips[Random.Range(0, clips.Length)];
    if (clip == lastClip && Time.time - lastPlayTime < 0.05f) return;
    
    lastClip = clip;
    lastPlayTime = Time.time;
    source.PlayOneShot(clip, volume);
}
```

---

## 참고 링크

- Unity AudioSource.PlayOneShot 공식 문서: https://docs.unity3d.com/ScriptReference/AudioSource.PlayOneShot.html
- Unity Audio Mixer: https://docs.unity3d.com/Manual/AudioMixer.html
- Game Audio Pro — Combat Sound Design: https://www.gameaudiopro.com
- Brackeys "SOUND in Unity" 튜토리얼: https://youtu.be/6OT43pvUyfY
- 픽셀아트 게임 사운드 디자인 (Dev.to): https://dev.to/kadeemusername/sound-design-for-pixel-art-games
