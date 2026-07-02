# 랜덤 이벤트 선택지 팝업 시스템

리서치 날짜: 2026-07-02

## 개요

로그라이크에서 "전투 없는 이벤트 방"에 등장하는 텍스트 선택지 팝업이다.
플레이어에게 보상 vs 위험의 결정을 요구해 런마다 다른 경험을 만들어 준다.

예시: "낯선 상인이 이상한 약을 팔고 있다. [마신다: 랜덤 버프/디버프] [무시한다: 통과]"

**왜 중요한가 (OnionCat):**
- 전투만 이어지면 피로감 → 이벤트 방이 완급 조절
- 스토리 느낌 추가 (비용 0 — 코드만으로 서사 제공)
- 선택 결과가 런마다 달라 재플레이 동기 강화
- 비교적 쉽게 구현 가능 (UI + ScriptableObject)

---

## Unity 구현 방법

### 1. 이벤트 데이터 정의 (ScriptableObject)

```csharp
// EventData.cs
[CreateAssetMenu(menuName = "OnionCat/EventData")]
public class EventData : ScriptableObject
{
    [TextArea] public string description;          // 이벤트 설명 텍스트
    public List<EventChoice> choices;
}

[System.Serializable]
public class EventChoice
{
    public string choiceText;                      // 버튼에 표시될 텍스트
    public List<EventEffect> effects;              // 선택 시 발생 효과 목록
}

[System.Serializable]
public class EventEffect
{
    public EventEffectType type;                   // enum: HealHP, DamageHP, GiveGold, SpawnItem, etc.
    public int value;
    public bool isRandom;                          // true면 +value ~ -value 랜덤
}

public enum EventEffectType
{
    HealHP, DamageHP, GiveGold, RemoveGold,
    SpawnItem, SpawnEnemy, GiveBuff, GiveDebuff
}
```

### 2. 팝업 UI 구조

```
Canvas (Screen Space - Overlay)
└── EventPopup (Panel, 기본 비활성화)
    ├── Background (Image, 반투명 어둡게)
    ├── DescriptionText (TextMeshPro)
    └── ChoicesContainer (Vertical Layout Group)
        ├── ChoiceButton_0
        ├── ChoiceButton_1
        └── ChoiceButton_2 (선택지 수만큼 동적 생성)
```

### 3. 팝업 매니저 코드

```csharp
// EventPopupManager.cs
public class EventPopupManager : MonoBehaviour
{
    public static EventPopupManager Instance;

    [SerializeField] private GameObject popupRoot;
    [SerializeField] private TextMeshProUGUI descriptionText;
    [SerializeField] private Transform choicesContainer;
    [SerializeField] private GameObject choiceButtonPrefab;  // 버튼 프리팹

    private EventData currentEvent;

    void Awake() => Instance = this;

    public void ShowEvent(EventData eventData)
    {
        currentEvent = eventData;
        popupRoot.SetActive(true);
        descriptionText.text = eventData.description;
        Time.timeScale = 0f;   // 게임 일시정지

        // 기존 버튼 제거 후 재생성
        foreach (Transform child in choicesContainer) Destroy(child.gameObject);

        foreach (var choice in eventData.choices)
        {
            var btn = Instantiate(choiceButtonPrefab, choicesContainer);
            btn.GetComponentInChildren<TextMeshProUGUI>().text = choice.choiceText;

            // 클로저 캡처 주의: 로컬 변수로 복사
            var capturedChoice = choice;
            btn.GetComponent<Button>().onClick.AddListener(() => OnChoiceSelected(capturedChoice));
        }
    }

    void OnChoiceSelected(EventChoice choice)
    {
        foreach (var effect in choice.effects) ApplyEffect(effect);
        ClosePopup();
    }

    void ApplyEffect(EventEffect effect)
    {
        int val = effect.isRandom ? Random.Range(-effect.value, effect.value + 1) : effect.value;

        switch (effect.type)
        {
            case EventEffectType.HealHP:
                PlayerHealth.Instance.Heal(val);
                break;
            case EventEffectType.DamageHP:
                PlayerHealth.Instance.TakeDamage(val);
                break;
            case EventEffectType.GiveGold:
                RunManager.Instance.AddGold(val);
                break;
            case EventEffectType.SpawnItem:
                ItemSpawner.Instance.SpawnRandomItem(transform.position);
                break;
            // ... 추가 케이스
        }
    }

    void ClosePopup()
    {
        Time.timeScale = 1f;
        popupRoot.SetActive(false);
        PlayerEventBus.PublishEventCompleted();  // 방 클리어 처리용 이벤트
    }
}
```

### 4. 이벤트 방 트리거

```csharp
// EventRoom.cs — 이벤트 방 입장 시 자동 팝업
public class EventRoom : MonoBehaviour
{
    [SerializeField] private List<EventData> possibleEvents;  // Inspector에서 에셋 드래그

    private bool triggered = false;

    void OnTriggerEnter2D(Collider2D other)
    {
        if (triggered || !other.CompareTag("Player")) return;
        triggered = true;

        var selected = possibleEvents[Random.Range(0, possibleEvents.Count)];
        EventPopupManager.Instance.ShowEvent(selected);
    }
}
```

### 5. 이벤트 에셋 예시 (Inspector 설정)

```
EventData: "수상한_약장수.asset"
  description: "낡은 외투를 두른 상인이 빛나는 약을 내밀었다."
  choices:
    [0] choiceText: "마신다 (랜덤 효과)"
        effects: [{ type: HealHP, value: 10, isRandom: true }]
    [1] choiceText: "거절한다"
        effects: []

EventData: "오래된_제단.asset"
  description: "피 묻은 제단 위에 빛나는 코인이 놓여 있다."
  choices:
    [0] choiceText: "코인을 집는다 (+50골드, -10HP)"
        effects: [{ type: GiveGold, value: 50 }, { type: DamageHP, value: 10 }]
    [1] choiceText: "무시하고 지나간다"
        effects: []
```

---

## OnionCat 적용 포인트

### OnionCat 전용 이벤트 아이디어

| 이벤트명 | 설명 | Cat 선택지 | Onion 선택지 |
|---|---|---|---|
| 물의 여신 | 고여있는 연못 앞 | 뛰어든다 (이동속도+) | 씨앗 던진다 (투사체 강화) |
| 배고픈 새 | 작물 노리는 새 | 쫓아낸다 (골드 획득) | 씨앗으로 유인 (아이템 교환) |
| 녹슨 무기함 | 낡은 상자 발견 | 발로 찬다 (무기 드롭) | 뿌리로 여닫는다 (골드 드롭) |

### Cat/Onion 분리 선택 시스템 (심화)
```csharp
// 두 플레이어가 각자 다른 선택지를 고르는 UI
// Cat Player는 좌측 버튼, Onion Player는 우측 버튼
// 두 선택지가 조합되어 결과 결정
public class CoopEventManager : MonoBehaviour
{
    public void OnCatChoice(EventChoice catChoice) { ... }
    public void OnOnionChoice(EventChoice onionChoice) { ... }

    void TryResolve()
    {
        if (catChoice != null && onionChoice != null)
            ApplyCombinedEffect(catChoice, onionChoice);
    }
}
```

### 구현 우선순위
1. **MVP**: 단일 선택지 팝업 (한 명이 선택) → EventPopupManager 기본 버전
2. **확장 1**: ScriptableObject 에셋 5~10개 작성
3. **확장 2**: Cat/Onion 각자 선택 후 조합 결과

### 주의사항
- `Time.timeScale = 0f` 사용 시 Coroutine이 멈춤 → `Time.unscaledDeltaTime` 사용 또는 팝업 애니메이션 회피
- 팝업 열릴 때 입력 Lock 처리 필요 (PlayerInput 비활성화 or EventSystem 이동)
- 이벤트 중복 방지: `triggered = false` 플래그 반드시 관리

---

## 참고 링크

- Unity UI 공식 문서: https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/index.html
- TextMeshPro 설치 및 사용: https://docs.unity3d.com/Manual/com.unity.textmeshpro.html
- ScriptableObject 기반 게임 이벤트 (Ryan Hipple): https://youtu.be/raQ3iHhE_Kk
- Unity Button onClick 동적 추가: https://docs.unity3d.com/ScriptReference/UI.Button-onClick.html
