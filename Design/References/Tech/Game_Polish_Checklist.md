# 게임 폴리싱 & 출시 준비 체크리스트 (Game Polish & Launch Checklist)

리서치 날짜: 2026-08-15

## 개요
게임이 "기능적으로 동작"하는 것과 "발매할 수 있는" 것 사이에는 **폴리싱 작업**이 있다. 초보 개발자가 가장 놓치기 쉬운 영역: 타격감(juice), 오디오 밸런스, UI 일관성, 퍼포먼스, 빌드 설정. OnionCat을 Itch.io나 Steam에 올리기 전 체크해야 할 항목을 Unity 구현 관점에서 정리한다.

---

## Unity 구현 방법

### 1. 비주얼 주스 (Visual Juice) — 타격감 핵심 3종

**최소 필수 주스 패키지** — 이 3가지만 넣어도 체감이 크게 달라진다:

#### ① 피격 흰색 플래시 (Sprite Hit Flash)
```csharp
public class SpriteHitFlash : MonoBehaviour
{
    [SerializeField] private float flashDuration = 0.1f;
    private SpriteRenderer sr;
    private Color originalColor;

    private void Awake()
    {
        sr = GetComponent<SpriteRenderer>();
        originalColor = sr.color;
    }

    public void Flash()
    {
        StopAllCoroutines();
        StartCoroutine(FlashRoutine());
    }

    private IEnumerator FlashRoutine()
    {
        sr.color = Color.white;
        yield return new WaitForSeconds(flashDuration);
        sr.color = originalColor;
    }
}
```
피격 시 `hitFlash.Flash()` 한 줄로 호출.

#### ② 카메라 흔들림 (CinemachineImpulse)
```csharp
// 컴포넌트: CinemachineImpulseSource (GameObject에 부착)
using Cinemachine;

[RequireComponent(typeof(CinemachineImpulseSource))]
public class ScreenShake : MonoBehaviour
{
    private CinemachineImpulseSource impulse;

    private void Awake() => impulse = GetComponent<CinemachineImpulseSource>();

    public void Shake(float force = 0.3f)
    {
        impulse.GenerateImpulse(force);
    }
}
// 강한 타격: Shake(0.5f), 약한 타격: Shake(0.2f)
```
CinemachineVirtualCamera에 **CinemachineImpulseListener** 컴포넌트 추가 필요 (Inspector).

#### ③ SFX 피치 랜덤 변주
```csharp
public class AudioRandomPitch : MonoBehaviour
{
    [SerializeField] private AudioSource audioSource;
    [SerializeField] private float minPitch = 0.9f;
    [SerializeField] private float maxPitch = 1.1f;

    public void PlayWithRandomPitch(AudioClip clip)
    {
        audioSource.pitch = Random.Range(minPitch, maxPitch);
        audioSource.PlayOneShot(clip);
    }
}
```
같은 SFX가 반복되어도 기계적이지 않게 들림.

---

### 2. 추가 주스 요소

#### 버튼 Hover 애니메이션 (DOTween)
```csharp
using DG.Tweening;
using UnityEngine.EventSystems;

public class ButtonJuice : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler
{
    public void OnPointerEnter(PointerEventData data)
    {
        transform.DOScale(1.08f, 0.1f).SetEase(Ease.OutBack);
    }

    public void OnPointerExit(PointerEventData data)
    {
        transform.DOScale(1f, 0.08f);
    }

    public void OnPointerClick(PointerEventData data)
    {
        transform.DOPunchScale(Vector3.one * 0.1f, 0.15f, 5, 0.5f);
    }
}
```

#### 대미지 숫자 팝업
```csharp
public class DamageNumber : MonoBehaviour
{
    [SerializeField] private TMPro.TextMeshPro text;

    public void Show(int damage, Vector3 position)
    {
        transform.position = position + Vector3.up * 0.5f;
        text.text = damage.ToString();
        // 위로 뜨면서 페이드 아웃
        transform.DOMoveY(transform.position.y + 1f, 0.8f).SetEase(Ease.OutCubic);
        text.DOFade(0f, 0.8f).OnComplete(() => Destroy(gameObject));
    }
}
```

---

### 3. 오디오 밸런스 체크리스트

```
[ ] BGM 볼륨이 SFX보다 낮음 (AudioMixer에서 BGM 그룹: -6dB ~ -12dB)
[ ] 같은 SFX 동시 재생 시 피치 랜덤 변주 적용
[ ] AudioMixer: Master / BGM / SFX / UI 그룹 분리
[ ] 씬 전환 시 BGM 페이드 아웃 (0.5초) → 페이드 인 (0.5초)
[ ] 중요 SFX (사망, 클리어)는 SFX 채널, BGM은 BGM 채널로 분리
[ ] 무음 테스트: SFX 꺼도 게임 진행 가능한지 확인
```

AudioMixer 페이드 적용:
```csharp
// BGM 페이드 아웃
public IEnumerator FadeOutBGM(float duration)
{
    audioMixer.GetFloat("BGMVolume", out float currentVol);
    float timer = 0f;
    while (timer < duration)
    {
        timer += Time.unscaledDeltaTime;
        float newVol = Mathf.Lerp(currentVol, -80f, timer / duration);
        audioMixer.SetFloat("BGMVolume", newVol);
        yield return null;
    }
}
```

---

### 4. UI 일관성 체크리스트

```
[ ] 모든 텍스트가 동일한 폰트 패밀리 사용 (최대 2종)
[ ] 컬러 팔레트 3색 이내 (메인 / 서브 / 포인트)
[ ] 버튼 클릭 영역 최소 44×44px (손가락/마우스 타겟 기준)
[ ] 아이콘과 라벨 텍스트 수직 정렬 일치
[ ] ESC키로 모든 팝업 창 닫기 가능 여부 확인
[ ] 게임패드로도 모든 UI 조작 가능 여부 확인
[ ] 해상도 1920×1080 / 1280×720 양쪽에서 UI 깨지지 않는지 확인
```

---

### 5. 컨트롤 반응성 체크리스트

```
[ ] 입력 버퍼: 대시/공격 버튼 0.15초 내 재입력 기억 (Input Buffer)
[ ] 대시 무적 프레임 시각 피드백 (스프라이트 깜빡임)
[ ] 게임패드 데드존 0.2f ~ 0.3f 설정 (UnityEngine.InputSystem)
[ ] 마우스 조준 화면 밖으로 나가지 않도록 Cursor.lockState 설정
[ ] P1(키보드/게임패드) + P2(마우스) 동시 입력 충돌 없는지 확인
```

---

### 6. 퍼포먼스 체크리스트

```
[ ] Unity Profiler로 Update()당 CPU 1ms 이하 확인
[ ] GC Alloc: 핫패스(Update, FixedUpdate)에서 0B 유지
[ ] 텍스처 압축: 크런치(Crunch) Compression 적용
[ ] 자주 생성/소멸되는 파티클과 투사체에 오브젝트 풀링 적용
[ ] 카메라 컬링 마스크: 렌더링 불필요한 레이어 제외
```

Unity Profiler 확인 방법:
```
Window > Analysis > Profiler > Play 버튼
→ CPU Usage 탭 선택
→ GC.Alloc 항목 확인
→ 빨간 스파이크 구간 클릭 → 원인 메서드 식별
```

---

### 7. 빌드 전 에러 방지 체크리스트

```
[ ] 모든 씬 전환 전 null 체크 완료
[ ] OnDestroy()에서 외부 참조 정리 (이벤트 구독 해제 포함)
[ ] 씬 재시작 시 static 변수 초기화 확인
[ ] Development Build 체크 해제 후 릴리즈 빌드
[ ] Console에 Error/Warning 없는 상태로 빌드
[ ] 모든 씬이 Build Settings에 등록되어 있는지 확인
```

---

### 8. 출시 직전 최종 체크리스트

```
[ ] 타이틀 화면에 게임 버전 표시 (예: v1.0.0)
[ ] 크레딧 씬 존재 (최소 개발자 이름)
[ ] 게임 소개 텍스트 (한국어 + 영어) 작성 완료
[ ] 시작 → 클리어까지 풀 플레이스루 1회 완료 테스트
[ ] 타인(비개발자) 플레이테스트 1회 이상
[ ] 빌드 .zip 압축 후 Itch.io 업로드 테스트
[ ] 게임 스크린샷 3장 이상 (타이틀, 전투, 업그레이드 UI)
[ ] 게임 커버 이미지 460×215px (Steam 스타일) 또는 315×250px (Itch.io)
```

---

## OnionCat 적용 포인트

### 구현 우선순위 (단계별)

**MVP 수준 — 무조건 먼저:**
1. `SpriteHitFlash` — 모든 피격 가능 오브젝트(P1, P2, 적)에 부착
2. `CinemachineImpulse` — 강한 타격(보스 공격, 사망)에만 먼저 적용
3. 피치 랜덤 변주 — 공격 SFX, 피격 SFX에 적용

**Good 수준 — 출시 목표:**
4. `DamageNumber` 팝업
5. 버튼 `ButtonJuice` 애니메이션 (메인 메뉴, 업그레이드 선택)
6. BGM 페이드 아웃/인 (씬 전환, 게임 오버)

**출시 수준 — 최종 점검:**
7. 전체 체크리스트 통과 확인
8. 비개발자 플레이테스트 1회
9. 빌드 테스트 (zip → Itch.io 업로드 동작 확인)

### OnionCat 특수 고려사항
- **2인 컨트롤 명확성**: P1(게임패드/WASD) + P2(마우스) 동시 입력이 충돌 없는지
- **화면 공유**: 두 플레이어가 하나의 화면을 봄 → P1용 UI와 P2용 UI 위치 분리 필요 (좌측 상단 / 우측 상단)
- **대시 무적 피드백**: P1 대시 중 스프라이트 깜빡임으로 P2도 무적 타이밍 인지 가능하게
- **피격 방향 표시**: 공유 바디이므로 피격 방향 표시기(화면 가장자리 붉은 섬광)가 더 중요

---

## 참고 링크
- Game Feel by Steve Swink (필독 서적): https://www.gamedeveloper.com/design/game-feel
- Unity 공식 게임 폴리싱 튜토리얼: https://learn.unity.com/tutorial/make-your-game-shine
- DOTween 공식 문서: https://dotween.demigiant.com/documentation.php
- Unity Profiler 가이드: https://docs.unity3d.com/Manual/Profiler.html
- Cinemachine Impulse: https://docs.unity3d.com/Packages/com.unity.cinemachine@2.6/manual/CinemachineImpulse.html
- Itch.io 업로드 가이드: https://itch.io/docs/creators/getting-started
- Juice it or lose it (GDC 2012 발표): https://www.youtube.com/watch?v=Fy0aCDmgnxg
