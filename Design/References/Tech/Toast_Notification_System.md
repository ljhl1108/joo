# Toast / In-Game Notification Pop-up System

리서치 날짜: 2026-07-21

## 개요

게임 내 특정 이벤트(협공 성공, 콤보 달성, 업적 해금, 아이템 획득 등)를 화면 구석에 작은 팝업으로 알려주는 시스템. "Toast"는 잠깐 떠올랐다 사라지는 알림 UI를 뜻한다.

OnionCat에서는 협공 보너스 알림, 적 약점 발견 알림, 방 클리어 보너스, 런 중 업적 달성 등에 활용 가능. 전투 흐름을 방해하지 않으면서 피드백을 전달하는 핵심 UX 요소다.

## Unity 구현 방법

### ToastData (메시지 정의)
```csharp
[System.Serializable]
public class ToastData
{
    public string message;
    public Color color = Color.white;
    public float duration = 2f;
    public Sprite icon;          // 선택적 아이콘
    public ToastPriority priority = ToastPriority.Normal;
}

public enum ToastPriority { Low, Normal, High }
```

### ToastItem (개별 팝업 프리팹)
```csharp
public class ToastItem : MonoBehaviour
{
    [SerializeField] private TMP_Text _messageText;
    [SerializeField] private Image _iconImage;
    [SerializeField] private CanvasGroup _canvasGroup;

    public void Show(ToastData data)
    {
        _messageText.text = data.message;
        _messageText.color = data.color;
        if (data.icon != null) _iconImage.sprite = data.icon;
        _iconImage.gameObject.SetActive(data.icon != null);

        StartCoroutine(AnimateRoutine(data.duration));
    }

    private IEnumerator AnimateRoutine(float duration)
    {
        // 페이드 인 + 위로 이동
        _canvasGroup.alpha = 0f;
        var startPos = transform.localPosition;
        var targetPos = startPos + Vector3.up * 20f;

        float elapsed = 0f;
        float fadeInTime = 0.2f;
        while (elapsed < fadeInTime)
        {
            elapsed += Time.unscaledDeltaTime;
            _canvasGroup.alpha = elapsed / fadeInTime;
            transform.localPosition = Vector3.Lerp(startPos, targetPos, elapsed / fadeInTime);
            yield return null;
        }

        // 대기
        yield return new WaitForSecondsRealtime(duration - 0.4f);

        // 페이드 아웃
        elapsed = 0f;
        float fadeOutTime = 0.2f;
        while (elapsed < fadeOutTime)
        {
            elapsed += Time.unscaledDeltaTime;
            _canvasGroup.alpha = 1f - elapsed / fadeOutTime;
            yield return null;
        }

        Destroy(gameObject);
    }
}
```

### ToastManager (싱글톤)
```csharp
public class ToastManager : MonoBehaviour
{
    public static ToastManager Instance { get; private set; }

    [SerializeField] private ToastItem _toastPrefab;
    [SerializeField] private Transform _container; // 화면 우하단 등 앵커 위치

    private readonly Queue<ToastData> _queue = new();
    private bool _isShowing;
    private const float GAP_BETWEEN_TOASTS = 0.1f;

    void Awake() => Instance = this;

    public void Show(string message, Color color = default, float duration = 2f, Sprite icon = null)
    {
        var data = new ToastData
        {
            message = message,
            color = color == default ? Color.white : color,
            duration = duration,
            icon = icon
        };
        _queue.Enqueue(data);
        if (!_isShowing) StartCoroutine(ProcessQueue());
    }

    private IEnumerator ProcessQueue()
    {
        _isShowing = true;
        while (_queue.Count > 0)
        {
            var data = _queue.Dequeue();
            var item = Instantiate(_toastPrefab, _container);
            item.Show(data);
            yield return new WaitForSecondsRealtime(data.duration + GAP_BETWEEN_TOASTS);
        }
        _isShowing = false;
    }
}
```

### 사용 예시
```csharp
// 협공 성공
ToastManager.Instance.Show("협공 성공! × 1.5 데미지", Color.yellow, 1.5f);

// 적 약점 발견
ToastManager.Instance.Show("약점 발견: 근접 공격에 취약!", Color.cyan, 2f);

// 방 클리어 보너스
ToastManager.Instance.Show("방 클리어! +10 골드", Color.green, 2f);

// 런 중 업적
ToastManager.Instance.Show("도전: 첫 패링 성공!", Color.white, 2.5f, achievementIcon);
```

### UI 프리팹 구조
```
ToastItem (Prefab)
├── Background (Image, 반투명 검정)
│   ├── Icon (Image, 선택적)
│   └── Message (TextMeshProUGUI)
└── CanvasGroup (알파 애니메이션용)
```

### Canvas 설정
- **Render Mode**: Screen Space - Overlay
- **Sort Order**: 최상위 (다른 UI보다 앞)
- **Container Anchor**: 화면 우하단 (HUD와 겹치지 않도록)
- **Layout**: Vertical Layout Group (위로 쌓이도록 Child Alignment: Lower Right, Reverse Arrangement: true)

## OnionCat 적용 포인트

| 이벤트 | 메시지 예시 | 색상 | 지속시간 |
|--------|-----------|------|---------|
| 협공 Break | "협공! 대미지 ×1.5" | 노랑 | 1.2s |
| 패링 성공 | "퍼펙트 패링!" | 청록 | 1.0s |
| 적 약점 발견 | "[근접 전용] 적 발견" | 흰색 | 2.0s |
| 방 클리어 | "방 클리어 +골드" | 초록 | 1.5s |
| 체력 위험 | "체력 주의!" | 빨강 | 1.5s |
| 업그레이드 획득 | "새 능력: ○○" | 보라 | 2.0s |

**구현 순서**:
1. ToastItem 프리팹 제작 (Canvas, Background, TMP_Text, CanvasGroup)
2. Canvas 최상위에 Container 오브젝트 배치 (Vertical Layout Group)
3. ToastManager 싱글톤 씬에 배치
4. SynergyChecker, EnemyHitReceiver 등 OnHit 이벤트에서 `ToastManager.Instance.Show()` 호출

**주의**: 전투 중 너무 많은 Toast가 겹치면 오히려 노이즈. 중복 방지 로직(같은 메시지 0.5초 이내 재발생 차단)을 추가할 것.

## 참고 링크

- Unity 공식 - TextMeshPro: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
- Unity 공식 - CanvasGroup: https://docs.unity3d.com/ScriptReference/CanvasGroup.html
- Unity 공식 - Vertical Layout Group: https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-VerticalLayoutGroup.html
- UX 참고 - 게임 내 Toast 설계: https://www.gamedeveloper.com/design/feedback-systems-in-games-notifications-and-popups
