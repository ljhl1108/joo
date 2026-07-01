# 난이도 선택 화면

리서치 날짜: 2026-07-01

## 개요

로그라이크에서 난이도 선택은 "게임을 다시 시작하고 싶게 만드는" 중요한 완성도 요소다. 입문자가 쉽게 접근하고, 숙련자는 도전을 유지할 수 있게 해준다. Hades의 Heat System, Dead Cells의 Boss Stem Cells, The Binding of Isaac의 Hard Mode 등 모두 이 철학을 담고 있다. OnionCat처럼 2인 협력 게임에서는 특히 중요한데, 두 플레이어의 실력 차이를 흡수해야 하기 때문이다.

---

## 설계 접근법 비교

### 방식 A: 고정 난이도 선택 (심플, 초심자 개발자에게 권장)

런 시작 전 3단계 중 하나 선택 → 선택한 설정이 그 런 전체에 적용.

```
[쉬움]  [보통]  [어려움]
```

구현 난이도: 낮음. 유지보수 쉬움. 처음 완성 게임 목표로는 최적.

### 방식 B: Hades식 동적 난이도 (히트 시스템)

클리어 후 난이도 수치를 올릴 수 있는 "저주" 시스템. 클리어를 해야만 다음 단계 해금. 구현 난이도 높음 — 나중에 추가 기능으로 적합.

---

## Unity 구현 방법

### 1. 난이도 데이터 ScriptableObject

```csharp
// DifficultyData.cs
[CreateAssetMenu(menuName = "OnionCat/DifficultyData")]
public class DifficultyData : ScriptableObject
{
    public string displayName;          // "쉬움", "보통", "어려움"
    public float enemyHealthMultiplier; // 0.7, 1.0, 1.4
    public float enemyDamageMultiplier; // 0.7, 1.0, 1.4
    public float enemySpeedMultiplier;  // 0.85, 1.0, 1.15
    public int   startingRooms;         // 4, 5, 6 (적을수록 쉬움)
    public bool  allowRevive;           // 쉬움: true, 어려움: false
}
```

에디터에서 Assets/Data/Difficulty/에 3개 SO 생성 후 값 입력.

### 2. GameManager에서 선택 저장

```csharp
// GameManager.cs (DontDestroyOnLoad 싱글턴)
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [SerializeField] private DifficultyData[] difficulties; // [0]=쉬움 [1]=보통 [2]=어려움

    public DifficultyData SelectedDifficulty { get; private set; }

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        SelectedDifficulty = difficulties[1]; // 기본값: 보통
    }

    public void SetDifficulty(int index)
    {
        if (index < 0 || index >= difficulties.Length) return;
        SelectedDifficulty = difficulties[index];
    }
}
```

### 3. 난이도 선택 UI 패널

```csharp
// DifficultySelectPanel.cs
public class DifficultySelectPanel : MonoBehaviour
{
    [SerializeField] private Button[] difficultyButtons; // 쉬움/보통/어려움
    [SerializeField] private Color selectedColor = Color.yellow;
    [SerializeField] private Color defaultColor = Color.white;

    private int _selectedIndex = 1;

    private void Start()
    {
        for (int i = 0; i < difficultyButtons.Length; i++)
        {
            int captured = i; // 클로저 캡처
            difficultyButtons[i].onClick.AddListener(() => OnDifficultySelected(captured));
        }
        RefreshButtons();
    }

    private void OnDifficultySelected(int index)
    {
        _selectedIndex = index;
        GameManager.Instance.SetDifficulty(index);
        RefreshButtons();
    }

    private void RefreshButtons()
    {
        for (int i = 0; i < difficultyButtons.Length; i++)
        {
            var colors = difficultyButtons[i].colors;
            colors.normalColor = (i == _selectedIndex) ? selectedColor : defaultColor;
            difficultyButtons[i].colors = colors;
        }
    }
}
```

### 4. 씬 구조

```
[메인 메뉴] → [모드 선택: 스토리/퀵런] → [난이도 선택] → [런 시작]
                                          ↑
                                    이 패널을 메인 메뉴 씬 안의
                                    별도 캔버스 패널로 구현 권장
                                    (씬 전환 없이 패널 On/Off)
```

### 5. 인게임에서 난이도 설정 읽기

```csharp
// EnemyBase.cs
private void Start()
{
    var diff = GameManager.Instance.SelectedDifficulty;
    maxHealth = Mathf.RoundToInt(baseHealth * diff.enemyHealthMultiplier);
    moveSpeed *= diff.enemySpeedMultiplier;
}

// EnemyAttack.cs
private float ActualDamage => baseDamage * GameManager.Instance.SelectedDifficulty.enemyDamageMultiplier;
```

---

## 2인 협력 게임 특화 설계 고려사항

OnionCat은 2인 코-op이므로 일반 싱글 로그라이크와 다른 점:

1. **부활 허용 여부**: 쉬운 난이도에서는 한 플레이어가 쓰러졌을 때 상대가 부활시킬 수 있게
2. **실력 차 보정**: 한 플레이어가 컨트롤러를 잘 못 다루더라도 쉬운 난이도에서 재미를 느낄 수 있게
3. **적 수 조정**: 어려운 난이도에서는 방당 적 수를 늘려 "2인이서도 힘겹다" 느낌 구현
4. **투명한 안내**: 선택 화면에서 각 난이도가 무엇을 바꾸는지 툴팁으로 명시

```
[쉬움]    ← 적 HP -30%, 피해 -30%, 부활 가능
[보통]    ← 기본 설정
[어려움]  ← 적 HP +40%, 피해 +40%, 부활 불가
```

---

## 난이도 설정 저장 (런 간 유지)

```csharp
// PlayerPrefs로 마지막 선택 난이도 저장
public void SetDifficulty(int index)
{
    SelectedDifficulty = difficulties[index];
    PlayerPrefs.SetInt("LastDifficulty", index);
}

private void Awake()
{
    // ...
    int saved = PlayerPrefs.GetInt("LastDifficulty", 1); // 기본값 1(보통)
    SelectedDifficulty = difficulties[saved];
}
```

---

## OnionCat 적용 포인트

### 권장 구현 순서

1. `DifficultyData` ScriptableObject 3개 생성 (쉬움/보통/어려움)
2. `GameManager`에 `SelectedDifficulty` 필드 추가 (이미 있다면 연결)
3. 메인 메뉴 씬에 `DifficultySelectPanel` 캔버스 패널 추가
4. `EnemyBase`에서 `Start()`에 GameManager 참조로 스탯 조정
5. 각 난이도 버튼에 툴팁 텍스트 표시

### 단계별 확장 계획

- **MVP**: 쉬움/보통/어려움 3단계, 적 HP/피해만 조정
- **v1.1**: 방 수, 부활 가능 여부 추가
- **v1.2**: Hades식 열사 시스템 (클리어 후 커스텀 난이도 추가) - 후순위

---

## 참고 링크

- Unity 공식 — ScriptableObject: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unity 공식 — PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- GDC — Difficulty Design in Roguelikes: https://www.gdcvault.com/play/1025880
- Game Maker's Toolkit — How Difficulty Works: https://www.youtube.com/watch?v=8L7c-QYdfEk
- Hades Heat System 분석: https://supergiantgames.com/blog/hades-design
