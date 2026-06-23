# Dialogue & Event System (대화 & 이벤트 시스템)

리서치 날짜: 2026-06-23

## 개요
로그라이크의 랜덤 이벤트 방, 상점 NPC 대화, 스토리 연출에 필요한 텍스트 기반 인터랙션 시스템.
OnionCat에서는 간단한 대화 표시 + 선택지 분기가 필요하며, 런 진행 중 게임을 일시정지하고 이벤트를 처리하는 구조가 핵심.

**왜 중요한가**: 완성도 있는 로그라이크는 전투 외에 "이야기가 있다"는 느낌을 줘야 함. 짧은 대화 하나가 세계관을 살리고 플레이어의 몰입도를 2배로 높인다.

---

## Unity 구현 방법

### 1. 데이터 구조 (ScriptableObject 기반)

```csharp
// DialogueLine.cs
[System.Serializable]
public class DialogueLine {
    public string speakerName;
    [TextArea(2, 5)] public string text;
    public Sprite portrait;
}

// DialogueChoice.cs
[System.Serializable]
public class DialogueChoice {
    public string choiceText;
    public UnityEvent onChoose;
}

// DialogueData.cs
[CreateAssetMenu(menuName = "OnionCat/Dialogue")]
public class DialogueData : ScriptableObject {
    public DialogueLine[] lines;
    public DialogueChoice[] choices; // 비어있으면 단순 대화, 있으면 선택지 팝업
}
```

---

### 2. DialogueManager (싱글턴)

```csharp
// DialogueManager.cs
public class DialogueManager : MonoBehaviour {
    public static DialogueManager Instance { get; private set; }
    
    [SerializeField] private GameObject dialoguePanel;
    [SerializeField] private TextMeshProUGUI nameText;
    [SerializeField] private TextMeshProUGUI bodyText;
    [SerializeField] private Image portraitImage;
    [SerializeField] private Transform choiceContainer;
    [SerializeField] private Button choiceButtonPrefab;
    
    private DialogueLine[] lines;
    private DialogueChoice[] choices;
    private int currentIndex;
    private Coroutine typingCoroutine;
    private System.Action onDialogueEnd;
    
    private void Awake() {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }
    
    public void StartDialogue(DialogueData data, System.Action onEnd = null) {
        lines = data.lines;
        choices = data.choices;
        currentIndex = 0;
        onDialogueEnd = onEnd;
        dialoguePanel.SetActive(true);
        Time.timeScale = 0f;  // 게임 일시정지
        ShowLine(0);
    }
    
    // 플레이어가 클릭/버튼으로 다음 줄로
    public void Advance() {
        // 타이핑 중이면 즉시 완성
        if (typingCoroutine != null) {
            StopCoroutine(typingCoroutine);
            typingCoroutine = null;
            bodyText.text = lines[currentIndex].text;
            return;
        }
        
        currentIndex++;
        if (currentIndex >= lines.Length) {
            if (choices != null && choices.Length > 0)
                ShowChoices();
            else
                EndDialogue();
            return;
        }
        ShowLine(currentIndex);
    }
    
    private void ShowLine(int index) {
        nameText.text = lines[index].speakerName;
        if (lines[index].portrait != null)
            portraitImage.sprite = lines[index].portrait;
        
        if (typingCoroutine != null) StopCoroutine(typingCoroutine);
        typingCoroutine = StartCoroutine(TypeText(lines[index].text));
    }
    
    private IEnumerator TypeText(string text) {
        bodyText.text = "";
        foreach (char c in text) {
            bodyText.text += c;
            yield return new WaitForSecondsRealtime(0.03f);  // unscaled: 정지 중에도 동작
        }
        typingCoroutine = null;
    }
    
    private void ShowChoices() {
        // 기존 선택지 버튼 제거
        foreach (Transform child in choiceContainer) Destroy(child.gameObject);
        
        foreach (var choice in choices) {
            var btn = Instantiate(choiceButtonPrefab, choiceContainer);
            btn.GetComponentInChildren<TextMeshProUGUI>().text = choice.choiceText;
            var captured = choice;
            btn.onClick.AddListener(() => {
                captured.onChoose?.Invoke();
                EndDialogue();
            });
        }
    }
    
    private void EndDialogue() {
        dialoguePanel.SetActive(false);
        Time.timeScale = 1f;
        onDialogueEnd?.Invoke();
    }
}
```

---

### 3. 랜덤 이벤트 시스템

```csharp
// RandomEventData.cs
[CreateAssetMenu(menuName = "OnionCat/RandomEvent")]
public class RandomEventData : ScriptableObject {
    public string eventTitle;
    public Sprite eventImage;
    public DialogueData dialogue;
    [Range(0f, 100f)] public float weight;  // 출현 가중치
}

// RandomEventRoom.cs
public class RandomEventRoom : MonoBehaviour {
    [SerializeField] private RandomEventData[] possibleEvents;
    private bool triggered = false;
    
    private void OnTriggerEnter2D(Collider2D other) {
        if (triggered || !other.CompareTag("Player")) return;
        triggered = true;
        var selected = PickWeightedRandom(possibleEvents);
        DialogueManager.Instance.StartDialogue(selected.dialogue);
    }
    
    private RandomEventData PickWeightedRandom(RandomEventData[] events) {
        float total = 0f;
        foreach (var e in events) total += e.weight;
        float roll = UnityEngine.Random.Range(0f, total);
        float cumulative = 0f;
        foreach (var e in events) {
            cumulative += e.weight;
            if (roll <= cumulative) return e;
        }
        return events[events.Length - 1];
    }
}
```

---

### 4. Input 연동 (New Input System)

대화 진행은 New Input System의 별도 Action Map으로:
```csharp
// PlayerInput에서 "Dialogue" Action Map 추가
// - Advance (Keyboard: Space, Gamepad: A/South 버튼)
// Action Map 전환:
playerInput.SwitchCurrentActionMap("Dialogue");  // 대화 시작 시
playerInput.SwitchCurrentActionMap("Gameplay");  // 대화 종료 시
```

---

### 5. Ink 연동 (복잡한 분기 필요 시)
분기가 3단계 이상 복잡해지면 Ink 스크립트 언어 + Unity Ink Integration 사용:
```ink
VAR hasKey = false

Cat: 이 문은... 잠겨있어.
Crop: 어떻게 하지?

* [문을 부수자] -> smash
* [열쇠를 찾자] -> find_key

=== smash ===
Cat: 좋아, 간다!
-> END
```
- Package Manager에서 `Ink Unity Integration` 설치
- InkStory 컴포넌트로 분기 처리

---

## OnionCat 적용 포인트

1. **Cat & Crop의 티격태격 대화**
   - 같은 몸 안에 있지만 성격 다름 → 짧은 대화가 세계관 전달
   - 예: 보스 방 진입 전 자동 대화 트리거 "Cat: 저기 큰 녀석이다... Crop: 뛰지 마! 흔들린다고!"

2. **상점 NPC 대화**
   - 농부 또는 이상한 NPC가 아이템 판매 전 한두 마디
   - 선택지로 "구매 / 거절" 연동 → `onChoose`에 아이템 지급 UnityEvent 연결

3. **Time.timeScale = 0 주의사항**
   - 타이핑 코루틴 반드시 `WaitForSecondsRealtime` 사용 (unscaled)
   - 파티클, 애니메이터가 멈추는 것은 의도된 동작 → 대화 UI만 살아있음

4. **New Input System Action Map 전환 필수**
   - 대화 중 캐릭터가 움직이는 버그 방지
   - `SwitchCurrentActionMap("Dialogue")` → `SwitchCurrentActionMap("Gameplay")`

5. **ScriptableObject 데이터 분리**
   - 대화 내용 변경 시 코드 수정 없이 에셋만 교체 가능
   - 나중에 한국어/영어 로컬라이제이션도 같은 구조로 확장 가능

---

## 참고 링크
- TextMeshPro 공식 문서: https://docs.unity3d.com/Packages/com.unity.textmeshpro@latest
- Unity New Input System - Action Maps: https://docs.unity3d.com/Packages/com.unity.inputsystem@latest/manual/ActionBindings.html
- Ink Unity Integration (GitHub): https://github.com/inkle/ink-unity-integration
- Brackeys 대화 시스템 튜토리얼: https://www.youtube.com/watch?v=_nRzoTzeyxU
- Dialogue System ScriptableObject 패턴: https://unity.com/how-to/architect-game-code-scriptable-objects
