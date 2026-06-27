# DOTween & 트위닝 애니메이션 시스템

리서치 날짜: 2026-06-27

## 개요
DOTween은 Unity에서 가장 널리 쓰이는 무료 트위닝 라이브러리다. 트위닝(Tweening)이란 시작값 → 끝값을 지정된 시간 동안 부드럽게 보간하는 기법으로, Animator 없이도 게임오브젝트의 위치/스케일/색상/알파를 코드 한 줄로 애니메이션할 수 있다.

OnionCat에서 DOTween이 필요한 이유:
- **업그레이드 카드 팝업**: 패배 후 카드가 위에서 슬라이드 인
- **피격 flash**: 스프라이트 알파/색상 깜빡임
- **보스 등장 줌인**: 카메라 FOV 트윈
- **UI 버튼 hover 효과**: 마우스 오버 시 스케일 1.0 → 1.1
- **체력바 감소**: 즉시 깎이지 않고 빨간색 게이지가 천천히 따라옴

---

## Unity 구현 방법

### 1. 설치
Asset Store에서 **DOTween (HOTween v2)** 무료 버전 설치.
설치 후 `Tools > Demigiant > DOTween Utility Panel > Setup DOTween` 실행 필수.

### 2. 기본 문법
```csharp
using DG.Tweening;

// 오브젝트를 2초 동안 (3,0,0)으로 이동
transform.DOMove(new Vector3(3, 0, 0), 2f);

// 스케일 1.0 → 1.3으로 0.2초
transform.DOScale(1.3f, 0.2f);

// 알파 0 → 1로 0.5초 (SpriteRenderer)
GetComponent<SpriteRenderer>().DOFade(1f, 0.5f);

// UI Image 알파 0 → 1로 0.5초
GetComponent<CanvasGroup>().DOFade(1f, 0.5f);

// 색상 변경
GetComponent<SpriteRenderer>().DOColor(Color.red, 0.1f);
```

### 3. Ease (가속/감속 곡선)
```csharp
transform.DOMove(target, 0.5f).SetEase(Ease.OutBack);    // 튀어 나왔다가 안착
transform.DOMove(target, 0.3f).SetEase(Ease.InOutQuad);  // 부드럽게
transform.DOScale(0f, 0.2f).SetEase(Ease.InBack);        // 작아지며 사라짐
```
주요 Ease 값:
- `Ease.OutBack` — UI 카드가 나타날 때 (살짝 overshooting)
- `Ease.OutBounce` — 점프 착지
- `Ease.InOutSine` — 체력바 감소
- `Ease.Flash` — 피격 깜빡임

### 4. 콜백 연결
```csharp
transform.DOMove(target, 0.5f)
    .OnComplete(() => {
        // 이동 완료 후 실행
        gameObject.SetActive(false);
    })
    .OnStart(() => Debug.Log("트윈 시작"));
```

### 5. Sequence (순서 있는 연출)
```csharp
Sequence seq = DOTween.Sequence();
seq.Append(transform.DOScale(1.2f, 0.15f));      // 0.15초 동안 크게
seq.Append(transform.DOScale(1.0f, 0.1f));       // 0.1초 동안 원래 크기
seq.AppendInterval(0.3f);                         // 0.3초 대기
seq.Append(canvasGroup.DOFade(0f, 0.3f));        // 페이드아웃
seq.OnComplete(() => Destroy(gameObject));
```

### 6. Punch & Shake (피격/충격 연출)
```csharp
// 피격 시 오브젝트 흔들림
transform.DOShakePosition(0.3f, strength: 0.15f, vibrato: 10);

// UI 버튼을 눌렀을 때 눌린 느낌
transform.DOPunchScale(new Vector3(0.1f, 0.1f, 0), 0.2f, 5, 1f);

// 카메라 히트스톱 + 흔들림 (Cinemachine 없을 때 대체)
Camera.main.transform.DOShakePosition(0.2f, 0.1f);
```

### 7. 루프
```csharp
// 무한 반복 깜빡임 (UI 힌트 등)
transform.DOScale(1.05f, 0.5f).SetLoops(-1, LoopType.Yoyo);

// 5회 반복 후 종료
spriteRenderer.DOFade(0f, 0.2f).SetLoops(5, LoopType.Yoyo);
```

### 8. 트윈 정리 (메모리 누수 방지)
```csharp
void OnDestroy() {
    // 이 오브젝트에 연결된 모든 트윈 종료
    DOTween.Kill(transform);
    // 또는 gameObject 기준
    DOTween.Kill(gameObject);
}
```

### 9. 피격 flash 패턴 (가장 자주 쓰는 예시)
```csharp
public class HitFlash : MonoBehaviour
{
    [SerializeField] private SpriteRenderer spriteRenderer;
    private static readonly Color HitColor = new Color(1f, 0.3f, 0.3f, 1f);

    public void PlayHitFlash()
    {
        DOTween.Kill(spriteRenderer);
        spriteRenderer.DOColor(HitColor, 0.05f)
            .OnComplete(() => spriteRenderer.DOColor(Color.white, 0.1f));
    }
}
```

---

## OnionCat 적용 포인트

### A. 업그레이드 선택 카드 등장 연출
```csharp
// 카드 3장이 위에서 순차적으로 내려오는 연출
for (int i = 0; i < cards.Length; i++) {
    int idx = i;
    cards[idx].transform.localPosition = new Vector3(0, 600, 0); // 화면 위에서 시작
    cards[idx].transform.DOLocalMoveY(0, 0.4f)
        .SetEase(Ease.OutBack)
        .SetDelay(idx * 0.1f); // 0.1초 간격으로 순차 등장
}
```

### B. Cat / Crop 피격 flash
- `SpriteRenderer.DOColor()`로 빨간 flash 구현 — Animator 없이 코드로 처리
- `DOTween.Kill(transform)` 호출 후 새 트윈 시작 → 중복 방지

### C. 체력바 지연 감소 (붉은 게이지)
```csharp
// 즉시 감소하는 게이지 + 천천히 따라오는 빨간 게이지
float targetHP = currentHP / maxHP;
hpBarFill.fillAmount = targetHP;                                 // 즉시
hpBarDelayed.DOFillAmount(targetHP, 0.5f).SetEase(Ease.InOutSine); // 0.5초 후
```

### D. 보스 등장 줌인
```csharp
Camera.main.DOOrthoSize(3f, 0.8f).SetEase(Ease.InOutQuad)
    .OnComplete(() => bossIntroUI.SetActive(true));
```

### E. UI 버튼 hover 스케일
```csharp
button.OnPointerEnterAsObservable()  // DOTween + UniRx 조합 or 단순 OnPointerEnter
    .Subscribe(_ => button.transform.DOScale(1.1f, 0.1f));
button.OnPointerExitAsObservable()
    .Subscribe(_ => button.transform.DOScale(1.0f, 0.1f));
// UniRx 없으면: EventTrigger 컴포넌트 + DOTween 콜백으로 동일 구현
```

---

## 참고 링크
- 공식 문서: http://dotween.demigiant.com/documentation.php
- Asset Store (무료): https://assetstore.unity.com/packages/tools/animation/dotween-hotween-v2-27676
- DOTween 시작 가이드 (한국어): https://www.youtube.com/watch?v=Y-dZPHpCf-s (검색어: "Unity DOTween 한국어 튜토리얼")
- Ease 시각화 도구: https://easings.net
- Brackeys - DOTween Tutorial: https://www.youtube.com/watch?v=BY9wRoZ1LnM
