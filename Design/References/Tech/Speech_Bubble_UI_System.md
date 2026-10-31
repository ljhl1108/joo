# 말풍선 UI 시스템 (Speech Bubble UI System)

리서치 날짜: 2026-10-31

## 개요

게임 월드 내 캐릭터·NPC 위에 **말풍선**이 뜨고, 텍스트가 한 글자씩 나타나며, 플레이어 입력으로 다음 줄로 넘어가는 시스템.

OnionCat에서의 역할:
- `Dialogue.Say(Transform speaker, string name, string text, Color nameColor)` API 구현 기반
- 이야기 대사: 책("낡은 책"), 고양이("새벽") 등 NPC별 말풍선
- 게임이 멈추면 숨고, 클릭·Enter·패드 A로 넘기는 인터랙션
- 글자 한 자씩 타이핑 효과 (TMP + Galmuri11 폰트)

---

## Unity 구현 방법

### 1. 말풍선 프리팹 구조

```
SpeechBubble (Canvas → World Space 권장, 또는 Screen Space Overlay)
├── Background (9-slice Image)
│   └── Arrow (Image — 화살촉, 방향 자동 조정)
├── Content
│   ├── NameTag (TMP_Text — "낡은 책", 이름표 색)
│   └── BodyText (TMP_Text — 대사 본문)
└── PromptIcon (Image — "▼" 또는 패드 A버튼 아이콘, 타이핑 완료 후 표시)
```

**Canvas 설정 (World Space)**:
- Sort Order: 150 이상 (HUD보다 아래, 항상 위 100+ 구간 바깥)
- Render Mode: World Space (3D 월드에서 캐릭터 위 배치 시)
- 또는 Overlay Canvas + 월드 좌표 → 스크린 좌표 변환

### 2. 말풍선 컴포넌트

```csharp
// SpeechBubble.cs
public class SpeechBubble : MonoBehaviour {
    [SerializeField] private TMP_Text nameLabel;
    [SerializeField] private TMP_Text bodyText;
    [SerializeField] private Image arrow;
    [SerializeField] private GameObject prompt; // ▼ 아이콘
    [SerializeField] private RectTransform bubbleRect;
    
    [SerializeField] private float charsPerSecond = 24f; // 타이핑 속도
    [SerializeField] private Vector2 offset = new(0f, 1.2f); // 스피커 위
    
    private Transform _speaker;
    private Coroutine _typeRoutine;
    private Camera _cam;
    
    private void Awake() => _cam = Camera.main;
    
    // 외부 호출 진입점
    public void Show(Transform speaker, string name, string text, Color nameColor) {
        _speaker = speaker;
        
        nameLabel.text = name;
        nameLabel.color = nameColor;
        bodyText.text = string.Empty;
        prompt.SetActive(false);
        
        gameObject.SetActive(true);
        UpdatePosition();
        
        if (_typeRoutine != null) StopCoroutine(_typeRoutine);
        _typeRoutine = StartCoroutine(TypeRoutine(text));
    }
    
    public void Hide() {
        if (_typeRoutine != null) StopCoroutine(_typeRoutine);
        gameObject.SetActive(false);
    }
    
    // 스피커 위치 추적 (LateUpdate)
    private void LateUpdate() {
        if (_speaker != null) UpdatePosition();
    }
    
    private void UpdatePosition() {
        // World Space Canvas 기준 위치 보정
        Vector3 worldPos = _speaker.position + (Vector3)offset;
        transform.position = worldPos;
        
        // 화면 끝에 걸릴 경우 방향 반전
        Vector3 screenPos = _cam.WorldToViewportPoint(worldPos);
        bool flipX = screenPos.x > 0.75f;
        bubbleRect.localScale = new Vector3(flipX ? -1f : 1f, 1f, 1f);
        nameLabel.transform.localScale = new Vector3(flipX ? -1f : 1f, 1f, 1f);
        bodyText.transform.localScale = new Vector3(flipX ? -1f : 1f, 1f, 1f);
    }
    
    // 타이핑 효과
    private IEnumerator TypeRoutine(string fullText) {
        float interval = 1f / charsPerSecond;
        
        for (int i = 1; i <= fullText.Length; i++) {
            bodyText.text = fullText.Substring(0, i);
            yield return new WaitForSecondsRealtime(interval); // TimeScale 무관
        }
        
        // 타이핑 완료 → ▼ 표시
        prompt.SetActive(true);
        _typeRoutine = null;
    }
    
    // 입력으로 빨리 감기 or 다음 줄
    public bool TryAdvance() {
        if (_typeRoutine != null) {
            // 아직 타이핑 중 → 즉시 완성
            StopCoroutine(_typeRoutine);
            _typeRoutine = null;
            bodyText.text = bodyText.text; // 전체 텍스트 (Dialogue가 관리)
            prompt.SetActive(true);
            return false; // "줄 넘어감"은 아님
        }
        return true; // 완성 후 → 다음 줄로
    }
}
```

### 3. Dialogue 매니저 (씬 유지 싱글턴)

```csharp
// DialogueManager.cs
public class DialogueManager : MonoBehaviour {
    public static DialogueManager Instance { get; private set; }
    
    [SerializeField] private SpeechBubble bubblePrefab;
    private SpeechBubble _bubble;
    
    private Queue<DialogueLine> _queue;
    private bool _isPlaying;
    private Action _onComplete;
    
    private void Awake() {
        Instance = this;
        _bubble = Instantiate(bubblePrefab);
        _bubble.Hide();
    }
    
    // GameManager.OnStateChanged 구독
    private void OnEnable()  => GameManager.OnStateChanged += OnStateChanged;
    private void OnDisable() => GameManager.OnStateChanged -= OnStateChanged;
    
    private void OnStateChanged(GameState state) {
        // 게임이 일시정지·업그레이드 선택 등이 되면 말풍선 숨김
        bool gameplay = state == GameState.Playing;
        if (_isPlaying) _bubble.gameObject.SetActive(gameplay);
    }
    
    // API: Dialogue.Play(lines) 구현
    public void Play(IEnumerable<DialogueLine> lines, Action onComplete = null) {
        _queue = new Queue<DialogueLine>(lines);
        _onComplete = onComplete;
        _isPlaying = true;
        ShowNext();
    }
    
    private void ShowNext() {
        if (_queue.Count == 0) {
            _bubble.Hide();
            _isPlaying = false;
            _onComplete?.Invoke();
            return;
        }
        
        var line = _queue.Dequeue();
        _bubble.Show(line.speakerTransform, line.speakerName, line.text, line.nameColor);
    }
    
    private void Update() {
        if (!_isPlaying || !GameManager.Instance.IsGameplayActive) return;
        
        bool advance = InputUtils.GetAdvanceInput(); // 클릭·Enter·패드 A
        if (advance && _bubble.TryAdvance()) {
            ShowNext();
        }
    }
}

// DialogueLine: 씬에서 쓸 데이터 구조
[System.Serializable]
public struct DialogueLine {
    public Transform speakerTransform;
    public string speakerName;
    [TextArea] public string text;
    public Color nameColor;
}
```

### 4. 정적 API (CLAUDE.md 명세 그대로)

```csharp
// Dialogue.cs — 정적 래퍼
public static class Dialogue {
    public static void Say(Transform speaker, string name, string text, Color nameColor) {
        DialogueManager.Instance.Play(new[] {
            new DialogueLine { speakerTransform = speaker, speakerName = name,
                               text = text, nameColor = nameColor }
        });
    }
    
    public static void Play(IEnumerable<DialogueLine> lines, Action onComplete = null) {
        DialogueManager.Instance.Play(lines, onComplete);
    }
}
```

### 5. 9-slice 말풍선 배경

```
스프라이트 설정 (Aseprite로 제작):
  - PPU 32, 말풍선 몸통 최소 크기 (예: 64×32px)
  - 화살촉을 별도 스프라이트로 분리 (회전 가능하게)
  - Import: Sprite Mode = Single, 9-slice Border 설정
    → Unity 6에서는 SpriteDataProviderFactories 사용 (TextureImporter.spriteBorder 불가)

RectTransform 자동 크기:
  - Content Size Fitter + Vertical Layout Group
  - 텍스트 양에 따라 말풍선이 자동 확장
```

### 6. 타이핑 사운드

```csharp
// TypeRoutine 안에서 주기적으로 사운드
private IEnumerator TypeRoutine(string fullText) {
    float interval = 1f / charsPerSecond;
    float soundInterval = 0.08f; // 타이핑음 간격 (너무 촘촘하면 소음)
    float soundTimer = 0f;
    
    for (int i = 1; i <= fullText.Length; i++) {
        bodyText.text = fullText.Substring(0, i);
        
        soundTimer += interval;
        if (soundTimer >= soundInterval && fullText[i-1] != ' ') {
            Sfx.Play(SfxId.DialogueType);
            soundTimer = 0f;
        }
        
        yield return new WaitForSecondsRealtime(interval);
    }
    prompt.SetActive(true);
}
```

---

## OnionCat 적용 포인트

### 캐릭터별 말풍선 스타일
```
책 ("낡은 책" / "그리모"):
  - nameColor: Color(0.8f, 0.6f, 0.2f) — 낡은 종이 황색
  - 타이핑 속도: 18 chars/sec (느리게, 깐깐한 느낌)
  - 배경: 양피지 질감 (별도 스프라이트)

고양이 ("새벽"):
  - nameColor: Color(0.5f, 0.9f, 0.7f) — 청록색
  - 타이핑 속도: 26 chars/sec (빠름)

마녀 (반전 전: 이름 없음 / 반전 후: "마녀"):
  - 반전 전 nameColor: Color(0.4f, 0.4f, 0.5f) — 회색
  - 반전 후: Color(0.8f, 0.3f, 0.9f) — 보라색
```

### 게임 상태 연동
```
GameState.Playing    → 말풍선 표시
GameState.Paused     → 말풍선 숨김 (SetActive(false))
GameState.Upgrade    → 말풍선 숨김
GameState.Map        → 말풍선 숨김 (필요시 대화 진행 가능)
GameState.Inventory  → 말풍선 숨김
```

### MetaProgress.WitchFreed 연동
```csharp
// StoryLines.cs 에서 이름 동적 변경
string bookName = MetaProgress.WitchFreed ? "그리모" : "낡은 책";
Color bookColor = MetaProgress.WitchFreed
    ? new Color(0.8f, 0.3f, 0.9f)
    : new Color(0.8f, 0.6f, 0.2f);

Dialogue.Say(bookTransform, bookName, line.text, bookColor);
```

### PromptIcon — 패드/키보드 자동 전환
```csharp
// 입력 장치에 따라 아이콘 교체
prompt.GetComponent<Image>().sprite = InputUtils.IsGamepad
    ? padAButtonSprite    // 패드 A 버튼 아이콘
    : keyboardEnterSprite; // ▼ 또는 Enter 텍스트
```

---

## 참고 링크

- TMP Character-by-Character: https://discussions.unity.com/t/revealing-text-character-by-character/
- World Space Canvas: https://docs.unity3d.com/Manual/UICanvas.html
- Content Size Fitter: https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/HOWTO-UIFitContentSize.html
- Galmuri 폰트: https://github.com/quiple/galmuri (SIL OFL 1.1)
- OnionCat 대사 설계: `Design/07_StoryMeta.md`
