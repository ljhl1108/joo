# 보스 입장 연출 시스템 (Boss Entrance Presentation System)

리서치 날짜: 2026-08-14

## 개요

보스 방 진입 시 자동으로 실행되는 "보스 등장 연출" 시퀀스.
게임을 완성된 느낌으로 만드는 핵심 폴리시 요소 중 하나.

구성요소:
1. 방 문 봉인 (플레이어 탈출 차단)
2. 카메라 연출 (보스 쪽으로 패닝 → 복귀)
3. 보스 스폰 애니메이션
4. 보스 타이틀 카드 UI
5. BGM 전환

Hades의 Tartarus boss room, Enter the Gungeon의 보스 스크린이 대표 예시.

---

## Unity 구현 방법

### 전체 시퀀스 흐름

```
[PlayerEnterBossRoom]
   → 문 봉인 (DoorSeal)
   → 0.5초 딜레이
   → 카메라 보스 위치로 팬 (1.2초)
   → 보스 스폰 애니메이션 재생 (1.5초)
   → 보스 타이틀 카드 페이드인 → 2초 대기 → 페이드아웃
   → 카메라 플레이어 복귀 (0.8초)
   → BGM "보스 테마" 전환
   → [BossPhase 시작]
```

---

### 1. 방 문 봉인

```csharp
// BossRoomDoor.cs
public class BossRoomDoor : MonoBehaviour
{
    [SerializeField] private Collider2D doorCollider;
    [SerializeField] private SpriteRenderer doorSprite;

    public void Seal()
    {
        doorCollider.enabled = true;
        doorSprite.enabled = true;
        // 선택: 봉인 이펙트 파티클
    }
}
```

`BossRoomTrigger`(Trigger Collider2D)가 플레이어 감지 시 모든 `BossRoomDoor` 봉인.

---

### 2. 카메라 팬 (Cinemachine 없이 간단 구현)

```csharp
// BossEntranceCamera.cs — CameraFollower 일시 비활성화 후 직접 이동
IEnumerator PanToBoss(Vector3 bossPos, Vector3 playerPos, float panTime, float returnTime)
{
    cameraFollower.enabled = false;

    // 보스 위치로 이동
    yield return MoveCameraTo(bossPos, panTime);
    yield return new WaitForSeconds(1.5f); // 보스 등장 감상 시간

    // 플레이어 위치로 복귀
    yield return MoveCameraTo(playerPos, returnTime);

    cameraFollower.enabled = true;
}

IEnumerator MoveCameraTo(Vector3 target, float duration)
{
    Vector3 start = Camera.main.transform.position;
    float t = 0f;
    while (t < 1f)
    {
        t += Time.deltaTime / duration;
        Camera.main.transform.position = Vector3.Lerp(start, target, Mathf.SmoothStep(0, 1, t));
        yield return null;
    }
}
```

---

### 3. 보스 스폰 애니메이션

보스 Animator에 `Entrance` 트리거 설정:
```
[Idle(비활성)] → (Entrance 트리거) → [EntranceAnim] → (완료) → [BossIdle]
```

스폰 시퀀스:
```csharp
boss.gameObject.SetActive(true);
boss.GetComponent<Animator>().SetTrigger("Entrance");
// 무적 상태로 전환 (연출 중 피해 방지)
boss.GetComponent<BossHealth>().SetInvincible(true);

yield return new WaitForSeconds(entranceAnimLength);

boss.GetComponent<BossHealth>().SetInvincible(false);
```

---

### 4. 보스 타이틀 카드 UI

```
Canvas (Screen Space - Overlay)
 └── BossTitlePanel (CanvasGroup)
      ├── BossNameText (TMP_Text) — "양파밭의 수호자"
      └── BossSubtitleText (TMP_Text) — "The Guardian of the Onion Field"
```

```csharp
// BossTitleCard.cs
public class BossTitleCard : MonoBehaviour
{
    [SerializeField] private CanvasGroup panel;
    [SerializeField] private TMP_Text nameText;

    public IEnumerator Show(string bossName, float displayDuration = 2f)
    {
        nameText.text = bossName;
        panel.alpha = 0f;
        panel.gameObject.SetActive(true);

        // 페이드인
        yield return FadePanel(0f, 1f, 0.4f);
        yield return new WaitForSeconds(displayDuration);
        // 페이드아웃
        yield return FadePanel(1f, 0f, 0.4f);

        panel.gameObject.SetActive(false);
    }

    IEnumerator FadePanel(float from, float to, float duration)
    {
        float t = 0f;
        while (t < 1f)
        {
            t += Time.deltaTime / duration;
            panel.alpha = Mathf.Lerp(from, to, t);
            yield return null;
        }
    }
}
```

---

### 5. BGM 전환

```csharp
// AudioManager.TransitionToBossBGM()
public void TransitionToBossBGM(AudioClip bossBGM, float fadeDuration = 1f)
{
    StartCoroutine(CrossFade(currentBGMSource, bossBGMSource, bossBGM, fadeDuration));
}

IEnumerator CrossFade(AudioSource from, AudioSource to, AudioClip newClip, float duration)
{
    to.clip = newClip;
    to.Play();
    float t = 0f;
    while (t < 1f)
    {
        t += Time.deltaTime / duration;
        from.volume = Mathf.Lerp(1f, 0f, t);
        to.volume = Mathf.Lerp(0f, 1f, t);
        yield return null;
    }
    from.Stop();
}
```

---

### 6. 전체 오케스트레이션

```csharp
// BossEntranceDirector.cs
public class BossEntranceDirector : MonoBehaviour
{
    [SerializeField] private BossRoomDoor[] doors;
    [SerializeField] private BossEntranceCamera camCtrl;
    [SerializeField] private BossTitleCard titleCard;
    [SerializeField] private AudioManager audioManager;
    [SerializeField] private AudioClip bossBGM;

    public IEnumerator PlayEntrance(BossController boss, string bossName)
    {
        // 플레이어 조작 비활성화
        PlayerInput.Instance.SetActive(false);

        // 문 봉인
        foreach (var door in doors) door.Seal();

        yield return new WaitForSeconds(0.5f);

        // 카메라 + 보스 등장 + 타이틀 병렬 실행
        StartCoroutine(camCtrl.PanToBoss(boss.transform.position,
            PlayerManager.Instance.transform.position, 1.2f, 0.8f));

        boss.gameObject.SetActive(true);
        boss.GetComponent<Animator>().SetTrigger("Entrance");

        yield return new WaitForSeconds(0.8f); // 카메라 도착 대기
        yield return titleCard.Show(bossName, 2f);

        yield return new WaitForSeconds(0.3f);

        // BGM 전환
        audioManager.TransitionToBossBGM(bossBGM);

        // 플레이어 조작 복원
        PlayerInput.Instance.SetActive(true);

        // 보스 전투 시작
        boss.StartBattle();
    }
}
```

---

## OnionCat 적용 포인트

### 보스 이름 & 서브타이틀 한/영 병기
```
"대지의 두더지 왕"
The Mole King of the Earth
```
`BossData` ScriptableObject에 `bossKorName`, `bossEngSubtitle` 필드 추가.

### 연출 중 타임스케일 활용
입장 연출 첫 0.3초: `Time.timeScale = 0.3f` → 느린 화면으로 "무게감"
보스 이름 카드 등장 직전: `Time.timeScale = 1.0f` 복귀

### 유니티 에디터에서 드래그 앤 드롭 설정 필요
- `BossEntranceDirector` 컴포넌트에 `doors[]`, `camCtrl`, `titleCard`, `audioManager` 참조 연결
- 보스 Animator의 `Entrance` → `Idle` 전환 트리거 설정
- `BossRoomTrigger` Collider2D의 Layer: Player 감지 전용

### 단계별 구현 순서 (초보자 권장)
1. 문 봉인만 먼저 구현 (1시간)
2. 타이틀 카드 페이드인/아웃 추가 (1시간)
3. 보스 스폰 애니메이션 연결 (30분)
4. 카메라 팬 추가 (1시간)
5. BGM 전환 마무리 (30분)

---

## 참고 링크

- Unity Coroutine 공식 가이드: https://docs.unity3d.com/Manual/Coroutines.html
- CanvasGroup 공식 문서: https://docs.unity3d.com/ScriptReference/CanvasGroup.html
- Unity Audio CrossFade 튜토리얼: https://www.youtube.com/results?search_query=unity+audio+crossfade+bgm
- Enter the Gungeon Boss Intro 분석: https://www.reddit.com/r/EnterTheGungeon/comments/boss_intro
- TMP_Text API: https://docs.unity3d.com/Packages/com.unity.textmeshpro@latest
