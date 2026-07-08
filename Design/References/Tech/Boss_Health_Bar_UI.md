# Boss Health Bar UI System (보스 체력바 UI)

리서치 날짜: 2026-07-08

## 개요

보스 체력바는 로그라이크에서 빠질 수 없는 완성도 지표 UI다. 일반 잡몹과 달리 보스는 화면 하단(또는 상단)에 큼직한 전용 체력바가 표시되고, 입장 시 극적인 연출(이름 표시, 체력바 슬라이드인)을 포함한다. Hades, Dead Cells, Enter the Gungeon 모두 보스 전용 체력바로 "이 전투가 다르다"는 신호를 플레이어에게 전달한다.

OnionCat에서는 Cat(근접)과 Onion(원거리)이 보스의 각기 다른 약점 페이즈를 공략해야 하므로, **현재 페이즈에 따른 체력바 색상 변화**가 핵심 디자인 포인트다.

---

## Unity 구현 방법

### 1. UI 구조 설계

```
Canvas (Screen Space - Overlay)
└── BossHUD (GameObject, 비활성화 상태로 시작)
    ├── BossNameText (TextMeshProUGUI)
    ├── BossHealthBarContainer (RectTransform, 배경 포함)
    │   ├── HealthBarBG (Image, 어두운 배경)
    │   ├── HealthBarFill (Image, fillAmount 방식)
    │   └── HealthBarDelayFill (Image, 지연 반응 효과)
    └── PhaseIndicators (선택사항 — 페이즈 체크포인트 표시)
        ├── Phase2Marker (작은 세로선)
        └── Phase3Marker
```

### 2. 보스 체력바 스크립트

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;

public class BossHealthBarUI : MonoBehaviour
{
    [SerializeField] private GameObject bossHUD;
    [SerializeField] private Image healthBarFill;
    [SerializeField] private Image healthBarDelayFill;   // 지연 반응 (흰색/노란색)
    [SerializeField] private TextMeshProUGUI bossNameText;
    [SerializeField] private CanvasGroup hudCanvasGroup;  // 페이드 인/아웃용

    [SerializeField] private float delayFillSpeed = 2f;   // 지연 체력바 감소 속도
    [SerializeField] private float fadeInDuration = 0.5f;

    // 페이즈별 색상
    [SerializeField] private Color phase1Color = new Color(0.8f, 0.2f, 0.2f);  // 빨강
    [SerializeField] private Color phase2Color = new Color(0.2f, 0.4f, 0.9f);  // 파랑 (원거리 약점)
    [SerializeField] private Color phase3Color = new Color(0.9f, 0.5f, 0.1f);  // 주황 (위험)

    private float targetFill;
    private Coroutine showRoutine;

    private void Awake()
    {
        bossHUD.SetActive(false);
    }

    public void ShowBossHUD(string bossName)
    {
        bossNameText.text = bossName;
        healthBarFill.fillAmount = 1f;
        healthBarDelayFill.fillAmount = 1f;
        bossHUD.SetActive(true);

        if (showRoutine != null) StopCoroutine(showRoutine);
        showRoutine = StartCoroutine(FadeIn());
    }

    public void HideBossHUD()
    {
        StartCoroutine(FadeOutAndHide());
    }

    public void UpdateHealth(float currentHp, float maxHp)
    {
        targetFill = currentHp / maxHp;
        healthBarFill.fillAmount = targetFill;
        // healthBarDelayFill는 Update에서 부드럽게 추적
    }

    public void SetPhaseColor(int phase)
    {
        Color target = phase switch
        {
            1 => phase1Color,
            2 => phase2Color,
            3 => phase3Color,
            _ => phase1Color
        };
        healthBarFill.color = target;
    }

    private void Update()
    {
        // 지연 체력바: 실제 체력바보다 천천히 감소
        if (healthBarDelayFill.fillAmount > healthBarFill.fillAmount)
        {
            healthBarDelayFill.fillAmount = Mathf.MoveTowards(
                healthBarDelayFill.fillAmount,
                healthBarFill.fillAmount,
                delayFillSpeed * Time.deltaTime
            );
        }
    }

    private IEnumerator FadeIn()
    {
        hudCanvasGroup.alpha = 0f;
        float elapsed = 0f;
        while (elapsed < fadeInDuration)
        {
            elapsed += Time.deltaTime;
            hudCanvasGroup.alpha = elapsed / fadeInDuration;
            yield return null;
        }
        hudCanvasGroup.alpha = 1f;
    }

    private IEnumerator FadeOutAndHide()
    {
        float elapsed = 0f;
        while (elapsed < fadeInDuration)
        {
            elapsed += Time.deltaTime;
            hudCanvasGroup.alpha = 1f - (elapsed / fadeInDuration);
            yield return null;
        }
        bossHUD.SetActive(false);
    }
}
```

### 3. 보스에서 UI 연동

보스 오브젝트는 `BossHealthBarUI`를 직접 참조하지 않고 **이벤트(Event Bus)** 또는 **싱글톤 매니저**를 통해 연동하는 것이 권장된다:

```csharp
// 보스 스크립트에서
public class BossEnemy : MonoBehaviour
{
    [SerializeField] private string bossDisplayName = "양파 수호자";
    [SerializeField] private int maxHp = 300;
    private int currentHp;

    private void Start()
    {
        currentHp = maxHp;
        // BossHealthBarUI는 씬에 하나만 존재 — FindObjectOfType은 Start()에서만 허용
        var bossUI = FindObjectOfType<BossHealthBarUI>();
        bossUI?.ShowBossHUD(bossDisplayName);
    }

    public void TakeDamage(int amount)
    {
        currentHp -= amount;
        var bossUI = FindObjectOfType<BossHealthBarUI>();  // Awake에서 캐싱 권장
        bossUI?.UpdateHealth(currentHp, maxHp);
        
        CheckPhaseTransition();
        if (currentHp <= 0) Die();
    }

    private void CheckPhaseTransition()
    {
        var bossUI = FindObjectOfType<BossHealthBarUI>();
        if (currentHp <= maxHp * 0.33f) bossUI?.SetPhaseColor(3);
        else if (currentHp <= maxHp * 0.66f) bossUI?.SetPhaseColor(2);
    }

    private void Die()
    {
        var bossUI = FindObjectOfType<BossHealthBarUI>();
        bossUI?.HideBossHUD();
        // ... 보스 사망 처리
    }
}
```

**최적화 주의**: `FindObjectOfType`은 `Awake()`에서 캐싱해야 한다 (코딩 컨벤션 준수). 위 예시는 구조 설명용이며 실제 구현 시 `Awake()`에서 참조를 저장할 것.

### 4. 보스 입장 연출 시퀀스 (드라마틱 연출)

```csharp
// BossRoomController: 보스 방 입장 시 실행
private IEnumerator BossIntroSequence(BossEnemy boss)
{
    // 1. 문 잠금 (다른 룸 연결 차단)
    LockRoomDoors();
    
    // 2. 카메라 보스 포커스 (Cinemachine Priority 올리기)
    bossCinemachineCamera.Priority = 15;
    yield return new WaitForSeconds(1.5f);
    
    // 3. 보스 이름 표시 + 체력바 페이드 인
    bossHealthBarUI.ShowBossHUD(boss.bossDisplayName);
    yield return new WaitForSeconds(0.5f);
    
    // 4. 카메라 플레이어로 복귀
    bossCinemachineCamera.Priority = 5;
    yield return new WaitForSeconds(0.5f);
    
    // 5. 보스 AI 활성화
    boss.ActivateAI();
}
```

---

## OnionCat 적용 포인트

### 페이즈 색상으로 약점 표시

OnionCat 보스는 Cat(근접)과 Onion(원거리)이 교대로 약점을 공략하는 구조다. 체력바 색상으로 "현재 어느 플레이어가 딜을 넣어야 하는지" 직관적으로 표시:

| 페이즈 | 체력바 색상 | 의미 |
|---|---|---|
| 1페이즈 (HP 100~66%) | 빨강 (따뜻한 색) | Cat 근접 공격 약점 |
| 2페이즈 (HP 66~33%) | 파랑 (차가운 색) | Onion 원거리 공격 약점 |
| 3페이즈 (HP 33~0%) | 보라/주황 (섞임) | 둘 다 필요 (협력 페이즈) |

### 구현 순서 (초보자용)

1. Canvas 생성 → BossHUD UI 오브젝트 수동 배치
2. `BossHealthBarUI.cs` 작성 후 BossHUD에 컴포넌트 추가
3. Inspector에서 Image/TMP 참조 드래그 앤 드롭 연결
4. 테스트용 보스에 `BossEnemy.cs` 추가
5. 씬 실행 후 보스 방 진입 → 체력바 표시 확인
6. 페이즈 색상 전환 테스트 (HP 임계값 도달 시)

**[SerializeField] 설정 필요**:
- `bossHUD` — BossHUD 게임오브젝트
- `healthBarFill` — 채워지는 Image 컴포넌트
- `healthBarDelayFill` — 지연 반응 Image 컴포넌트
- `bossNameText` — TextMeshProUGUI 컴포넌트
- `hudCanvasGroup` — CanvasGroup 컴포넌트
→ 유니티 에디터에서 드래그 앤 드롭 설정 필요

---

## 참고 링크

- Unity UI - Image fillAmount: https://docs.unity3d.com/Manual/script-Image.html
- TextMeshPro 공식 문서: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
- Brackeys "Health Bar in Unity": https://youtu.be/BLfNP4Sc_iA
- Game Dev Guide "Boss Health Bar with Phases": https://youtu.be/b5B4F8KAjL8
- CanvasGroup 페이드 인/아웃: https://docs.unity3d.com/ScriptReference/CanvasGroup.html
