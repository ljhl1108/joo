# 자원 수집 UI 피드백 시스템 (코인·픽업 애니메이션)

리서치 날짜: 2026-08-24

## 개요

플레이어가 코인·골드·경험치 구슬 등 자원을 획득할 때, 해당 아이템이 **HUD의 수치 카운터 쪽으로 날아가는 애니메이션**을 재생하는 시스템.
"코인이 UI에 빨려 들어가는" 피드백은 수집 행위를 보람 있게 만들어 게임 만족도를 크게 높인다.

OnionCat에서는 체력 회복 아이템, 골드, 잠금해제 파편 등에 적용 가능.

---

## Unity 구현 방법

### 아키텍처 개요

```
World: ResourcePickup 오브젝트 (픽업 시 비활성화)
  ↓ 이벤트 발생
ResourceCollectFeedback (싱글톤 또는 서비스)
  → WorldToScreenPoint로 시작 위치 변환
  → Canvas에 임시 아이콘 생성
  → Coroutine: Arc/직선으로 HUD 카운터 위치까지 이동
  → 도착 시: 아이콘 파괴 + 카운터 Pulse 애니메이션 + SFX
```

---

### 1. ResourceCollectFeedback.cs

```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

public class ResourceCollectFeedback : MonoBehaviour
{
    [SerializeField] private Canvas uiCanvas;
    [SerializeField] private RectTransform goldCounterRect;  // HUD의 골드 수치 UI 위치
    [SerializeField] private GameObject coinIconPrefab;      // 날아갈 아이콘 프리팹 (Image)
    [SerializeField] private float flyDuration = 0.6f;
    [SerializeField] private float arcHeight = 80f;          // 포물선 높이 (픽셀)
    [SerializeField] private int maxConcurrent = 8;          // 동시 최대 코인 수

    private Camera mainCam;
    private int activeCount = 0;

    private void Awake()
    {
        mainCam = Camera.main;
    }

    public void PlayCoinFly(Vector3 worldPosition, System.Action onArrive = null)
    {
        if (activeCount >= maxConcurrent) return;
        StartCoroutine(FlyRoutine(worldPosition, onArrive));
    }

    private IEnumerator FlyRoutine(Vector3 worldPos, System.Action onArrive)
    {
        activeCount++;

        // 월드→스크린→캔버스 좌표 변환
        Vector2 startScreenPos = mainCam.WorldToScreenPoint(worldPos);
        RectTransformUtility.ScreenPointToLocalPointInRectangle(
            uiCanvas.transform as RectTransform,
            startScreenPos,
            uiCanvas.renderMode == RenderMode.ScreenSpaceOverlay ? null : mainCam,
            out Vector2 startCanvasPos);

        RectTransformUtility.ScreenPointToLocalPointInRectangle(
            uiCanvas.transform as RectTransform,
            RectTransformUtility.WorldToScreenPoint(mainCam, goldCounterRect.position),
            uiCanvas.renderMode == RenderMode.ScreenSpaceOverlay ? null : mainCam,
            out Vector2 endCanvasPos);

        // 아이콘 생성
        GameObject icon = Instantiate(coinIconPrefab, uiCanvas.transform);
        RectTransform iconRect = icon.GetComponent<RectTransform>();
        iconRect.anchoredPosition = startCanvasPos;

        float elapsed = 0f;
        while (elapsed < flyDuration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / flyDuration;
            float smooth = Mathf.SmoothStep(0f, 1f, t);

            // 포물선 보간
            Vector2 pos = Vector2.Lerp(startCanvasPos, endCanvasPos, smooth);
            pos.y += arcHeight * Mathf.Sin(t * Mathf.PI);  // 포물선 호
            iconRect.anchoredPosition = pos;

            // 도착 직전 축소
            float scale = t > 0.8f ? Mathf.Lerp(1f, 0.3f, (t - 0.8f) / 0.2f) : 1f;
            iconRect.localScale = Vector3.one * scale;

            yield return null;
        }

        Destroy(icon);
        onArrive?.Invoke();
        activeCount--;
    }
}
```

**유니티 에디터에서 드래그 앤 드롭 설정 필요:**
- `uiCanvas`: 메인 HUD Canvas
- `goldCounterRect`: 골드 숫자 Text/Image가 있는 RectTransform
- `coinIconPrefab`: 날아갈 동전 아이콘 (Image 컴포넌트 포함)

---

### 2. 카운터 Pulse 애니메이션 (CounterPulse.cs)

```csharp
using System.Collections;
using UnityEngine;

public class CounterPulse : MonoBehaviour
{
    [SerializeField] private float pulseScale = 1.25f;
    [SerializeField] private float pulseDuration = 0.15f;

    private Vector3 originalScale;

    private void Awake() => originalScale = transform.localScale;

    public void Pulse()
    {
        StopAllCoroutines();
        StartCoroutine(PulseRoutine());
    }

    private IEnumerator PulseRoutine()
    {
        float half = pulseDuration * 0.5f;
        for (float t = 0; t < half; t += Time.deltaTime)
        {
            transform.localScale = Vector3.Lerp(originalScale, originalScale * pulseScale, t / half);
            yield return null;
        }
        for (float t = 0; t < half; t += Time.deltaTime)
        {
            transform.localScale = Vector3.Lerp(originalScale * pulseScale, originalScale, t / half);
            yield return null;
        }
        transform.localScale = originalScale;
    }
}
```

---

### 3. ResourcePickup.cs에서 호출

```csharp
private void OnTriggerEnter2D(Collider2D other)
{
    if (!other.CompareTag("Player")) return;

    // 실제 수치 증가
    GameManager.Instance.AddGold(goldAmount);

    // 피드백 실행
    ResourceCollectFeedback.Instance.PlayCoinFly(transform.position, () =>
    {
        goldCounterText.GetComponent<CounterPulse>().Pulse();
        AudioManager.Instance.PlaySFX("coin_arrive");
    });

    AudioManager.Instance.PlaySFX("coin_pickup");
    Destroy(gameObject);
}
```

---

### 4. 여러 코인 분산 수집 (웨이브 효과)

```csharp
// 코인 여러 개를 약간씩 지연해서 날리기 (더 생동감 있음)
IEnumerator SpawnMultipleCoinFeedback(Vector3 origin, int count)
{
    for (int i = 0; i < count; i++)
    {
        Vector3 offset = new Vector3(
            Random.Range(-0.3f, 0.3f),
            Random.Range(-0.3f, 0.3f), 0);
        ResourceCollectFeedback.Instance.PlayCoinFly(origin + offset,
            i == count - 1 ? () => counterPulse.Pulse() : null);
        yield return new WaitForSeconds(0.05f);
    }
}
```

---

## OnionCat 적용 포인트

### 1. 획득 자원 종류별 다른 아이콘
| 자원 | 아이콘 | 날아가는 대상 HUD |
|------|--------|----------------|
| 골드 | 동전 스프라이트 | 골드 카운터 |
| 체력 회복 | 하트 스프라이트 | HP 바 |
| 파 성장치 | 파 잎 스프라이트 | 파 성장 게이지 |
| 경험치 | 별/구슬 | 경험치 바 |

### 2. "파(P2)"가 아이템을 먹을 때 피드백
- P1(고양이)이 픽업하더라도 P2 HUD 방향으로 날아가는 연출 가능
- "공유 몸" 컨셉을 시각적으로 강화 — 두 UI가 연결된 느낌

### 3. 보스 클리어 대량 드롭
- 보스 처치 후 코인 10~20개가 순차적으로 날아오는 연출 → 만족감 극대화
- `SpawnMultipleCoinFeedback` 코루틴 활용

### 4. Object Pool과 연계
- 날아가는 아이콘을 Instantiate 대신 `Object Pool`에서 꺼내 쓰면 GC 부하 감소
- `Unity_Object_Pool_API.md` 참고

---

## 구현 순서 요약

```
1. HUD Canvas에 골드 Text와 CounterPulse 컴포넌트 추가
2. 동전 아이콘 프리팹 제작 (Image + CanvasGroup)
3. ResourceCollectFeedback 싱글톤을 HUD씬에 배치
4. goldCounterRect, coinIconPrefab 할당
5. ResourcePickup.OnTriggerEnter2D에서 PlayCoinFly 호출
6. 테스트: 픽업 → 코인 날아감 → 카운터 pulse + SFX 확인
```

---

## 참고 링크

- Unity UI RectTransformUtility: https://docs.unity3d.com/ScriptReference/RectTransformUtility.html
- Unity Coroutine 공식: https://docs.unity3d.com/Manual/Coroutines.html
- DOTween 사용 시 더 간결: http://dotween.demigiant.com/documentation.php
- YouTube "Unity coin fly to UI" 검색 권장
