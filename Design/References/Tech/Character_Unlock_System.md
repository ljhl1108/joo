# Character Unlock System (캐릭터 잠금 해제 시스템)

리서치 날짜: 2026-06-29

## 개요

**캐릭터 잠금 해제 시스템**이란 첫 런에는 기본 캐릭터만 사용 가능하고, 특정 조건(n번 런 완료, 특정 적 처치, 특정 아이템 수집 등)을 달성하면 새로운 캐릭터/스킨/클래스를 해금하는 시스템이다.

게임 완성도 관점에서 왜 중요한가:
- 첫 클리어 이후에도 계속 플레이할 이유를 만듦 (리플레이어빌리티)
- 플레이어에게 단기/중기/장기 목표를 제공
- 내러티브와 연결하면 게임 세계관을 자연스럽게 전달 가능
- Hades, Dead Cells, Rogue Legacy 2 등 성공적인 로그라이크는 모두 이 시스템 보유

OnionCat에서 적용하면:
- 기본 고양이(흰색 고양이 + 양파)에서 시작
- 런 진행에 따라 새로운 고양이 종류, 새로운 작물(양파 대신 당근, 마늘 등) 해금
- 각 조합마다 능력치/스킬셋 차이 → 협력 방식도 달라짐

---

## Unity 구현 방법

### 1. 데이터 구조 설계

#### CharacterData (ScriptableObject)

```csharp
// CharacterData.cs
[CreateAssetMenu(menuName = "OnionCat/CharacterData")]
public class CharacterData : ScriptableObject
{
    [Header("기본 정보")]
    public string characterId;       // "cat_white", "cat_black", "crop_onion" 등
    public string displayName;
    public Sprite portrait;
    public Sprite icon;

    [Header("잠금 해제 조건")]
    public UnlockConditionType conditionType;
    public int conditionValue;       // 조건 수치 (런 횟수, 처치 수 등)
    public string conditionItemId;   // 특정 아이템 조건일 경우
    public string unlockHint;        // "어둠 속에서 10번 살아남기"

    [Header("능력치 차이")]
    public float moveSpeedMultiplier = 1f;
    public float attackRangeMultiplier = 1f;
    public float startingHp = 100f;
}

public enum UnlockConditionType
{
    Default,         // 처음부터 해금
    RunCount,        // n번 런 완료
    TotalKills,      // 누적 처치 수 n 달성
    BossDefeated,    // 특정 보스 처치
    ItemCollected,   // 특정 아이템 n번 획득
    DeathCount,      // n번 사망
    ManualUnlock     // 게임 내 상점/이벤트로 직접 해금
}
```

### 2. 잠금 해제 상태 저장

```csharp
// UnlockManager.cs
public class UnlockManager : MonoBehaviour
{
    public static UnlockManager Instance { get; private set; }

    private const string UNLOCK_KEY_PREFIX = "unlocked_";

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    // 캐릭터가 해금됐는지 확인
    public bool IsUnlocked(string characterId)
    {
        return PlayerPrefs.GetInt(UNLOCK_KEY_PREFIX + characterId, 0) == 1;
    }

    // 캐릭터 해금 처리
    public void Unlock(string characterId)
    {
        if (IsUnlocked(characterId)) return;
        PlayerPrefs.SetInt(UNLOCK_KEY_PREFIX + characterId, 1);
        PlayerPrefs.Save();
        OnCharacterUnlocked?.Invoke(characterId);
    }

    public event Action<string> OnCharacterUnlocked;
}
```

### 3. 조건 체크 시스템

```csharp
// UnlockConditionChecker.cs
public class UnlockConditionChecker : MonoBehaviour
{
    [SerializeField] private CharacterData[] allCharacters;

    // 런 종료 시 호출 (GameOverScreen, RunResultScreen에서)
    public void CheckUnlocksOnRunEnd(RunStats stats)
    {
        foreach (var character in allCharacters)
        {
            if (UnlockManager.Instance.IsUnlocked(character.characterId)) continue;

            bool shouldUnlock = character.conditionType switch
            {
                UnlockConditionType.Default => true,
                UnlockConditionType.RunCount =>
                    stats.totalRunsCompleted >= character.conditionValue,
                UnlockConditionType.TotalKills =>
                    stats.totalKills >= character.conditionValue,
                UnlockConditionType.BossDefeated =>
                    stats.defeatedBossIds.Contains(character.conditionItemId),
                UnlockConditionType.DeathCount =>
                    stats.totalDeaths >= character.conditionValue,
                _ => false
            };

            if (shouldUnlock)
                UnlockManager.Instance.Unlock(character.characterId);
        }
    }
}
```

### 4. 런 통계 데이터 (저장용)

```csharp
// RunStats.cs — SaveLoadSystem과 연동
[System.Serializable]
public class RunStats
{
    public int totalRunsCompleted;
    public int totalKills;
    public int totalDeaths;
    public List<string> defeatedBossIds = new();

    // JSON 직렬화 후 PlayerPrefs 또는 파일에 저장
    public static RunStats Load()
    {
        string json = PlayerPrefs.GetString("RunStats", "{}");
        return JsonUtility.FromJson<RunStats>(json) ?? new RunStats();
    }

    public void Save()
    {
        PlayerPrefs.SetString("RunStats", JsonUtility.ToJson(this));
        PlayerPrefs.Save();
    }
}
```

### 5. 캐릭터 선택 UI (메인 메뉴)

```csharp
// CharacterSelectUI.cs
public class CharacterSelectUI : MonoBehaviour
{
    [SerializeField] private CharacterData[] allCharacters;
    [SerializeField] private CharacterSlotUI slotPrefab;
    [SerializeField] private Transform slotParent;

    void Start()
    {
        foreach (var character in allCharacters)
        {
            var slot = Instantiate(slotPrefab, slotParent);
            bool isUnlocked = UnlockManager.Instance.IsUnlocked(character.characterId);
            slot.Setup(character, isUnlocked);
        }
    }
}

// CharacterSlotUI.cs
public class CharacterSlotUI : MonoBehaviour
{
    [SerializeField] private Image portrait;
    [SerializeField] private Image lockIcon;
    [SerializeField] private TextMeshProUGUI nameText;
    [SerializeField] private TextMeshProUGUI hintText;
    [SerializeField] private Button selectButton;

    public void Setup(CharacterData data, bool isUnlocked)
    {
        portrait.sprite = isUnlocked ? data.portrait : GetLockedSprite();
        lockIcon.gameObject.SetActive(!isUnlocked);
        nameText.text = isUnlocked ? data.displayName : "???";
        hintText.text = isUnlocked ? "" : data.unlockHint;
        selectButton.interactable = isUnlocked;
    }

    private Sprite GetLockedSprite() { /* 실루엣 스프라이트 반환 */ return null; }
}
```

### 6. 잠금 해제 연출 (팝업)

```csharp
// UnlockPopup.cs
public class UnlockPopup : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI titleText;
    [SerializeField] private Image characterImage;
    [SerializeField] private CanvasGroup canvasGroup;

    void Start()
    {
        // UnlockManager 이벤트 구독
        UnlockManager.Instance.OnCharacterUnlocked += ShowUnlockPopup;
    }

    void ShowUnlockPopup(string characterId)
    {
        // characterId로 CharacterData 찾기
        // 팝업 표시 + DOTween 페이드인 애니메이션
        canvasGroup.DOFade(1f, 0.5f);
        titleText.text = $"새 캐릭터 해금!\n{data.displayName}";
    }
}
```

---

## OnionCat 적용 포인트

### 고양이 + 작물 조합 시스템

OnionCat의 "공유 몸통" 컨셉에 맞게 해금은 두 가지 축으로:

```
고양이 축 (Player 1):
  [흰 고양이]    → 기본 (처음부터 해금)
  [검은 고양이]  → 10번 런 완료 시 해금 / 더 빠른 대시, 낮은 HP
  [줄무늬 고양이] → 보스 2마리 처치 시 해금 / 넓은 공격 범위

작물 축 (Player 2):
  [양파]         → 기본 (처음부터 해금)
  [당근]         → 5번 런 완료 시 해금 / 빠른 투사체, 좁은 방패
  [마늘]         → 50번 총 처치 시 해금 / 독 투사체, AoE 방패
```

### 조합 시너지로 재미 배가
- 검은 고양이 + 마늘: 독 + 스텔스 콤보
- 줄무늬 고양이 + 당근: 빠른 투사체 + 넓은 공격 범위 → 공격적 플레이
- 각 조합에 특수 스타팅 스킬 1개 부여하면 선택의 의미 증가

### 구현 순서 추천 (초보자용)

1. `CharacterData` ScriptableObject 만들기 (1~2개만)
2. `PlayerPrefs`로 간단히 잠금 상태 저장
3. `RunStats`를 게임 오버/클리어 시 저장
4. 메인 메뉴에 캐릭터 선택 슬롯 UI 만들기
5. 해금 조건 체크 → 팝업 연출 추가
6. 나중에 조건 수 늘리기

### 주의사항

- **PlayerPrefs는 에디터에서 지워질 수 있음** — 개발 중 테스트는 디버그 키("모두 해금" 버튼)를 만들어두기
- 해금 힌트는 구체적으로: "적을 50마리 처치하세요" (O) vs "더 많이 싸워보세요" (X)
- 처음 게임을 켰을 때 Default 타입 캐릭터들을 자동으로 해금해주는 초기화 로직 필요

---

## 참고 링크

- [Unity PlayerPrefs 공식 문서](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [Unity ScriptableObject 공식 문서](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
- [Hades 캐릭터/무기 해금 시스템 분석 - YouTube 검색: "Hades unlock system design"](https://www.youtube.com/)
- [Rogue Legacy 2 캐릭터 잠금 해제 구조](https://rogue-legacy.fandom.com/wiki/Classes)
- [Game UI Database: Character Select 레퍼런스](https://www.gameuidatabase.com/)
- [Unity UI Button interactable 공식 문서](https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-Button.html)
