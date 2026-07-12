# Floor Clear Transition (플로어 클리어 연출)

리서치 날짜: 2026-07-12

## 개요

로그라이크에서 하나의 플로어(층/구역)를 클리어한 후 다음 플로어로 넘어가는 **전환 연출**은 리듬감과 성취감을 담당한다. 단순히 씬을 바꾸는 것이 아니라, 플레이어가 "한 단계 넘어섰다"는 느낌을 주는 시각·청각 시퀀스다. 잘 만들면 플레이어가 계속 진행하고 싶게 만드는 동기 부여 루프가 된다.

---

## 레퍼런스 분석

| 게임 | 연출 방식 |
|------|----------|
| **Hades** | 보스 사망 → 대화 → 어두운 방으로 이동 → 보상 선택 → 문 통과 |
| **Enter the Gungeon** | 엘리베이터 탑승 컷신 → 층 번호 표시 → 하강 → 새 층 도착 |
| **Dead Cells** | 문 통과 → 블랙아웃 → 다음 바이옴 도착 (빠름) |
| **Ember Knights** | 보스 사망 → 파티클 이펙트 → 방 클리어 배너 → 출구로 걸어가기 |
| **Risk of Rain 2** | 텔레포터 충전 → 충전 완료 폭발 → 포털 등장 → 인터루드 씬 |

**공통 패턴**: 보스/방 클리어 → 짧은 연출 → 보상 → 이동 → 다음 구역 시작

---

## Unity 구현 방법

### 1. 전체 시퀀스 구조

```
[FloorClearSequence]
1. 보스 사망 이벤트 발생
2. 0.5초 히트스톱 + 화면 잠금 (플레이어 입력 차단)
3. "FLOOR CLEAR" 텍스트 + 이펙트 (1초)
4. 런 통계 짧게 표시 (처치 수, 클리어 시간 등) (1.5초)
5. 페이드 아웃 (0.5초)
6. 다음 씬/방 로드
7. 페이드 인 (0.5초)
8. 업그레이드 선택 UI 등장
```

---

### 2. 코루틴 기반 구현

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class FloorClearTransition : MonoBehaviour
{
    [SerializeField] private CanvasGroup fadeOverlay;
    [SerializeField] private GameObject floorClearBanner;
    [SerializeField] private float fadeDuration = 0.5f;

    public IEnumerator PlayFloorClearSequence(int floorNumber)
    {
        // 1. 입력 차단
        GameManager.Instance.SetInputEnabled(false);

        // 2. 배너 표시
        floorClearBanner.SetActive(true);
        yield return new WaitForSecondsRealtime(1.5f);
        floorClearBanner.SetActive(false);

        // 3. 페이드 아웃
        yield return StartCoroutine(Fade(0f, 1f, fadeDuration));

        // 4. 씬/방 전환
        RoomManager.Instance.LoadNextFloor(floorNumber + 1);

        // 5. 페이드 인
        yield return StartCoroutine(Fade(1f, 0f, fadeDuration));

        // 6. 업그레이드 선택 UI
        UpgradeSelectionUI.Instance.Show();
    }

    private IEnumerator Fade(float from, float to, float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.unscaledDeltaTime; // 타임스케일 0일 때도 작동
            fadeOverlay.alpha = Mathf.Lerp(from, to, elapsed / duration);
            yield return null;
        }
        fadeOverlay.alpha = to;
    }
}
```

**핵심**: `Time.unscaledDeltaTime` 사용 → 히트스톱(Time.timeScale = 0) 중에도 UI 애니메이션 작동.

---

### 3. 플로어 클리어 배너 UI

```
[Canvas - ScreenSpace Overlay]
  └─ [FloorClearBanner - CanvasGroup]
       ├─ Background (반투명 검정)
       ├─ "FLOOR 1 CLEAR" Text (큰 픽셀 폰트)
       ├─ SubText ("처치: 12 | 클리어 시간: 2:34") 
       └─ FloorNumber Sprite (숫자 픽셀아트)
```

DOTween으로 배너 진입 애니메이션:
```csharp
// 위에서 슬라이드 인 → 잠시 대기 → 위로 슬라이드 아웃
bannerRect.DOAnchorPosY(0f, 0.3f).SetEase(Ease.OutBack)
    .OnComplete(() => bannerRect.DOAnchorPosY(300f, 0.3f).SetDelay(1.2f));
```

---

### 4. 영구 데이터 보존 (씬 전환 시)

```csharp
// DontDestroyOnLoad로 런 데이터 유지
public class RunData : MonoBehaviour
{
    public static RunData Instance;
    public int CurrentFloor;
    public int TotalKills;
    public List<UpgradeItem> Upgrades = new();

    private void Awake()
    {
        if (Instance == null) { Instance = this; DontDestroyOnLoad(gameObject); }
        else Destroy(gameObject);
    }

    public void AdvanceFloor() => CurrentFloor++;
}
```

---

### 5. 보상 선택 (업그레이드 선택)

```csharp
// 플로어 클리어 후 업그레이드 3개 제시
public void ShowUpgradeSelection()
{
    var options = UpgradePool.GetRandom(3, RunData.Instance.CurrentFloor);
    upgradeSelectionUI.Display(options, OnUpgradeChosen);
    Time.timeScale = 0f; // 선택 중 게임 정지
}

private void OnUpgradeChosen(UpgradeItem chosen)
{
    RunData.Instance.Upgrades.Add(chosen);
    chosen.Apply(player);
    Time.timeScale = 1f;
    // 다음 플로어 탐색 시작
}
```

---

## OnionCat 적용 포인트

### 플로어 구조 제안
- **플로어 1-2**: 일반 던전 방들 + 미니보스 (2번 방 클리어 후 클리어 연출)
- **플로어 3**: 대형 보스 방 → 메인 보스 클리어 → 플로어 클리어 연출 + 특별 보상

### 고양이-양파 전환 연출
플로어 클리어 배너에 두 캐릭터 반응 표시:
- 고양이: 승리 포즈 스프라이트
- 양파: 화분에서 잎이 흔들리는 소소한 애니메이션
- (선택) 짧은 텍스트 바터: "야옹~" / "냄새나는 승리다!"

### 업그레이드 선택의 협동 결정
플로어 클리어 후 업그레이드 3개 중 1개 선택 시:
- 고양이용 (이동/근접 관련) - 고양이 아이콘
- 양파용 (발사체/방패 관련) - 양파 아이콘
- 공용 (체력, 속도 등) - 공용 아이콘
→ 2인 플레이 시 합의 시스템 (단순하게: 선택 버튼 둘 다 눌러야 확정)

### 씬 전환 없이 구현 (권장)
OnionCat 규모에서는 씬 전환 없이 방 단위로 진행하는 것이 구현 부담이 낮음:
- `RoomManager`가 다음 방 프리팹 생성 + 카메라 이동
- 플로어 클리어는 "특정 방 수 클리어 후" 이벤트로 처리
- 완전한 씬 로드는 메인 메뉴 ↔ 게임 사이에만 사용

---

## 참고 링크

- Unity Docs - SceneManager: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- Unity Coroutine 가이드: https://docs.unity3d.com/Manual/Coroutines.html
- DOTween 공식: http://dotween.demigiant.com/documentation.php
- Game Feel — 레벨 클리어 연출 패턴 (Jonas Tyroller): https://www.youtube.com/watch?v=AJdEqssNZ-U
- Hades 씬 전환 분석 (GDC 2020): https://www.youtube.com/watch?v=X9-ygX6cBDs
