# Contextual Hint Popup System (상황별 힌트 팝업 시스템)

리서치 날짜: 2026-07-29

## 개요

플레이어가 특정 상황에 처음 처했을 때 일회성 힌트 팝업을 표시하는 시스템. Tutorial_System(첫 런 구조적 온보딩)과는 다르게, 게임 플레이 중 자연스럽게 맥락에 맞는 도움말을 제공한다.

**차이점 정리:**
| 시스템 | 설명 |
|--------|------|
| Tutorial_System | 첫 런에서 강제 진행, 조작 방법 가르치기 |
| **Contextual Hint System** | 언제든지, 조건 충족 시 자동 표시. 한 번 보면 다시 안 나옴 |
| Settings 내 힌트 | How to Play 화면에서 수동 열람 |

**OnionCat에서 필요한 이유:**
- 처음 숍 방 진입 시 → "여기서 아이템을 구매할 수 있습니다"
- 첫 번째 방패 파리 성공 시 → "패리 성공! 반격 기회입니다"
- 근접 약점 적 첫 등장 시 → "이 적은 근접 공격에만 피해를 받습니다 (Cat 담당)"
- Cat이 3번 사망(HP 0) 시 → "대시로 적의 공격을 피할 수 있습니다"

---

## Unity 구현 방법

### 전체 구조

```
ContextualHintManager (싱글톤)
├── HintData (ScriptableObject) × N개
│   ├── hintId (unique string)
│   ├── hintText
│   ├── displayDuration
│   └── iconSprite (선택)
├── HintTrigger (MonoBehaviour) - 각 오브젝트에 부착
└── HintPopupUI (UI Canvas)
```

### 1단계: HintData ScriptableObject

```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "HintData", menuName = "OnionCat/Hint Data")]
public class HintData : ScriptableObject
{
    [Tooltip("PlayerPrefs 저장 키. 이 ID로 표시 여부를 기록함")]
    public string hintId;
    
    [TextArea(2, 5)]
    public string hintText;
    
    public float displayDuration = 3f;
    
    [Tooltip("힌트 아이콘 (없으면 텍스트만 표시)")]
    public Sprite iconSprite;
    
    [Tooltip("이 힌트를 표시하기 위한 최소 게임 진행 상태 (선택)")]
    public int minimumRoomCleared = 0;
}
```

### 2단계: ContextualHintManager (싱글톤)

```csharp
using UnityEngine;
using System.Collections;

public class ContextualHintManager : MonoBehaviour
{
    public static ContextualHintManager Instance { get; private set; }
    
    [SerializeField] private HintPopupUI hintPopupUI;
    
    private bool isShowingHint = false;
    private Coroutine currentHintCoroutine;
    
    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }
    
    public void TryShowHint(HintData hint)
    {
        if (hint == null) return;
        if (HasBeenShown(hint.hintId)) return;   // 이미 본 힌트
        if (isShowingHint) return;                 // 현재 힌트 표시 중
        
        MarkAsShown(hint.hintId);
        currentHintCoroutine = StartCoroutine(ShowHintRoutine(hint));
    }
    
    public bool HasBeenShown(string hintId)
    {
        return PlayerPrefs.GetInt("Hint_" + hintId, 0) == 1;
    }
    
    private void MarkAsShown(string hintId)
    {
        PlayerPrefs.SetInt("Hint_" + hintId, 1);
        PlayerPrefs.Save();
    }
    
    public void ResetAllHints()  // 디버그용: 모든 힌트 초기화
    {
        // HintData는 Resources 폴더에서 로드 또는 별도 관리
        PlayerPrefs.DeleteAll();
    }
    
    private IEnumerator ShowHintRoutine(HintData hint)
    {
        isShowingHint = true;
        hintPopupUI.Show(hint);
        
        yield return new WaitForSecondsRealtime(hint.displayDuration); // Time.timeScale 영향 안 받음
        
        hintPopupUI.Hide();
        isShowingHint = false;
    }
    
    public void DismissCurrentHint()  // 플레이어가 버튼 누르면 즉시 닫기
    {
        if (currentHintCoroutine != null)
        {
            StopCoroutine(currentHintCoroutine);
            currentHintCoroutine = null;
        }
        hintPopupUI.Hide();
        isShowingHint = false;
    }
}
```

### 3단계: HintTrigger (트리거 방식)

트리거 방식 - 물리 영역으로 감지:

```csharp
using UnityEngine;

public class HintTrigger : MonoBehaviour
{
    [SerializeField] private HintData hintData;
    [SerializeField] private bool triggerOnce = true;  // 기본: 한 번만 트리거
    
    private bool hasTriggered = false;
    
    private void OnTriggerEnter2D(Collider2D col)
    {
        if (triggerOnce && hasTriggered) return;
        if (!col.CompareTag("Player")) return;
        
        hasTriggered = true;
        ContextualHintManager.Instance?.TryShowHint(hintData);
    }
}
```

이벤트 방식 - 게임 이벤트에 반응:

```csharp
using UnityEngine;

public class HintOnEvent : MonoBehaviour
{
    [SerializeField] private HintData hintData;
    
    // 적 처치, 패리 성공, 아이템 획득 등 이벤트에서 호출
    public void OnParrySuccess()
    {
        ContextualHintManager.Instance?.TryShowHint(hintData);
    }
    
    public void OnFirstShopEntered()
    {
        ContextualHintManager.Instance?.TryShowHint(hintData);
    }
    
    public void OnPlayerDamagedThreeTimes()
    {
        ContextualHintManager.Instance?.TryShowHint(hintData);
    }
}
```

### 4단계: HintPopupUI (UI 컴포넌트)

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using DG.Tweening;  // DOTween 사용 시

public class HintPopupUI : MonoBehaviour
{
    [SerializeField] private CanvasGroup canvasGroup;
    [SerializeField] private TextMeshProUGUI hintText;
    [SerializeField] private Image iconImage;
    [SerializeField] private GameObject iconObject;
    [SerializeField] private float fadeTime = 0.3f;
    
    private void Awake()
    {
        canvasGroup.alpha = 0f;
        gameObject.SetActive(false);
    }
    
    public void Show(HintData hint)
    {
        gameObject.SetActive(true);
        hintText.text = hint.hintText;
        
        if (hint.iconSprite != null)
        {
            iconObject.SetActive(true);
            iconImage.sprite = hint.iconSprite;
        }
        else
        {
            iconObject.SetActive(false);
        }
        
        // DOTween 페이드인
        canvasGroup.DOFade(1f, fadeTime);
    }
    
    public void Hide()
    {
        canvasGroup.DOFade(0f, fadeTime)
            .OnComplete(() => gameObject.SetActive(false));
    }
}
```

---

## OnionCat 힌트 목록 예시

프로젝트에 추가할 HintData 에셋 목록:

| hintId | 표시 조건 | 텍스트 |
|--------|-----------|--------|
| `shop_first_visit` | 숍 방 첫 진입 | "코인으로 아이템을 구매할 수 있습니다. Cat이 아이템에 접근하세요." |
| `parry_success_first` | Crop 패리 첫 성공 | "완벽한 타이밍의 방패! 패리 성공 시 적이 잠시 기절합니다." |
| `melee_only_enemy` | 근접 약점 적 첫 등장 | "이 적은 Cat의 근접 공격에만 피해를 받습니다." |
| `ranged_only_enemy` | 원거리 약점 적 첫 등장 | "이 적은 Crop의 원거리 공격에만 피해를 받습니다." |
| `dash_hint` | Cat이 연속 3피해 | "Cat은 무적 대시로 공격을 피할 수 있습니다!" |
| `boss_warning` | 보스 방 입구 진입 | "보스 방입니다. 아이템 구매 후 도전을 권장합니다." |
| `coin_drop_first` | 첫 코인 획득 | "코인을 모아 숍에서 사용하세요." |

---

## 주의사항 및 설계 원칙

1. **한 번에 하나만 표시** - 여러 조건이 동시 충족되어도 큐에 넣고 순서대로 표시
2. **플레이 방해 금지** - 힌트는 항상 화면 하단이나 구석에 배치, 전투 중 조준을 가리면 안 됨
3. **패리 타임 기준 적용** - `WaitForSecondsRealtime` 사용, 일시정지 화면에서도 힌트가 닫히도록
4. **데이터 분리** - 힌트 텍스트는 HintData ScriptableObject에만 존재, 코드에 하드코딩 금지
5. **디버그 리셋** - Debug_Cheat_System에 "힌트 전체 초기화" 기능 추가 권장

---

## 참고 링크

- Unity PlayerPrefs 공식 문서: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- ScriptableObject 기반 힌트 시스템 예제: Unite 2017 "ScriptableObject Architecture" (Ryan Hipple)
- DOTween 공식: http://dotween.demigiant.com/
- Unity UI CanvasGroup: https://docs.unity3d.com/ScriptReference/CanvasGroup.html
- 게임 UX 힌트 설계 참고: "Best Practices for In-Game Tooltips" (GDC Vault)
