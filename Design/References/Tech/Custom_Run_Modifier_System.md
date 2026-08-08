# Custom Run Modifier System (커스텀 런 모디파이어 시스템)

리서치 날짜: 2026-08-08

## 개요

런을 시작하기 전에 플레이어가 직접 **핸디캡이나 챌린지 조건을 선택**할 수 있는 시스템.
Hades의 "처벌 계약(Pact of Punishment)", Dead Cells의 "보스 줄기세포(Boss Stem Cells)",
Noita의 "숨겨진 모드" 등이 대표 사례.

OnionCat에서 적용하면:
- 메타 진행의 일환으로 잠금 해제되는 챌린지 모드
- "기본 게임 + 도전 요소"로 플레이 수명 연장
- 이미 클리어한 유저도 새 도전 목표를 갖게 됨

---

## 레퍼런스 사례 분석

| 게임 | 구현 방식 | 특징 |
|------|-----------|------|
| Hades | 처벌 계약 20종 (각 단계별 ON/OFF) | 클리어 후 해금, 히트 포인트 리워드와 연동 |
| Dead Cells | 보스 줄기세포 (0~5 Stars) | 누적형, 단계가 올라갈수록 조건 가중 |
| Noita | 시드 기반 챌린지 + 저주 설정 | 커뮤니티 공유 가능 |
| The Binding of Isaac | 챌린지 모드 (특정 조건 런) | 시작 아이템·적 조건 사전 고정 |
| Risk of Rain 2 | Eclipse 난이도 (적 AI+능력 버프 누적) | 멀티플레이 가능 |

---

## Unity 구현 방법

### 1. 모디파이어 데이터 정의 (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "OnionCat/RunModifier")]
public class RunModifierData : ScriptableObject
{
    [Header("기본 정보")]
    public string modifierID;         // 고유 식별자 "NO_DASH"
    public string displayName;        // "대시 봉인"
    public string description;        // 설명 텍스트
    public Sprite icon;
    
    [Header("잠금 해제")]
    public bool isUnlockedByDefault;
    public string unlockCondition;    // "런 5회 클리어"

    [Header("효과")]
    public ModifierEffect[] effects;  // 실제로 적용되는 효과 목록
    
    [Header("점수 가중치")]
    public int scoreMultiplierBonus;  // 이 모디파이어 활성화 시 최종 점수에 추가 %
}

[System.Serializable]
public class ModifierEffect
{
    public ModifierEffectType type;
    public float value;
}

public enum ModifierEffectType
{
    DisableDash,            // Cat 대시 비활성화
    DisableShield,          // Crop 실드 비활성화
    EnemyHPMultiplier,      // 적 체력 배율
    EnemySpeedMultiplier,   // 적 이동속도 배율
    PlayerHPMaxReduction,   // 플레이어 최대 체력 감소
    NoHealthDrops,          // 체력 드롭 제거
    EliteEnemyOnly,         // 모든 적을 엘리트로
    TimeLimitPerRoom        // 방당 제한 시간
}
```

### 2. 런 시작 전 선택 UI

```csharp
public class RunModifierSelectionScreen : MonoBehaviour
{
    [SerializeField] private RunModifierData[] allModifiers;
    [SerializeField] private Transform modifierListParent;
    [SerializeField] private GameObject modifierTogglePrefab;
    [SerializeField] private TextMeshProUGUI scoreMultiplierText;

    private HashSet<RunModifierData> selectedModifiers = new();

    private void Start()
    {
        PopulateModifierList();
        UpdateScoreDisplay();
    }

    private void PopulateModifierList()
    {
        foreach (var modifier in allModifiers)
        {
            bool unlocked = IsUnlocked(modifier);
            var toggle = Instantiate(modifierTogglePrefab, modifierListParent);
            toggle.GetComponent<ModifierToggleUI>().Initialize(modifier, unlocked, OnToggleChanged);
        }
    }

    private void OnToggleChanged(RunModifierData modifier, bool isOn)
    {
        if (isOn) selectedModifiers.Add(modifier);
        else selectedModifiers.Remove(modifier);
        UpdateScoreDisplay();
    }

    private void UpdateScoreDisplay()
    {
        int totalBonus = selectedModifiers.Sum(m => m.scoreMultiplierBonus);
        scoreMultiplierText.text = $"점수 보너스: +{totalBonus}%";
    }

    public void OnStartRunButton()
    {
        RunSessionManager.Instance.StartRun(selectedModifiers.ToList());
    }

    private bool IsUnlocked(RunModifierData modifier)
    {
        if (modifier.isUnlockedByDefault) return true;
        return SaveManager.Instance.IsModifierUnlocked(modifier.modifierID);
    }
}
```

### 3. 런 세션에서 모디파이어 적용

```csharp
public class RunSessionManager : MonoBehaviour
{
    public static RunSessionManager Instance { get; private set; }
    public List<RunModifierData> ActiveModifiers { get; private set; } = new();

    public void StartRun(List<RunModifierData> modifiers)
    {
        ActiveModifiers = modifiers;
        ApplyModifiers();
        SceneManager.LoadScene("GameScene");
    }

    private void ApplyModifiers()
    {
        foreach (var mod in ActiveModifiers)
        {
            foreach (var effect in mod.effects)
            {
                ApplyEffect(effect);
            }
        }
    }

    private void ApplyEffect(ModifierEffect effect)
    {
        switch (effect.type)
        {
            case ModifierEffectType.DisableDash:
                PlayerController.Instance.dashEnabled = false;
                break;
            case ModifierEffectType.EnemyHPMultiplier:
                EnemySpawner.Instance.hpMultiplier *= effect.value;
                break;
            case ModifierEffectType.NoHealthDrops:
                LootTable.Instance.healthDropRate = 0f;
                break;
            case ModifierEffectType.TimeLimitPerRoom:
                RoomTimer.Instance.SetTimeLimit((int)effect.value);
                break;
            // ... 기타 케이스
        }
    }

    // 외부에서 모디파이어 활성 여부 확인
    public bool HasModifier(ModifierEffectType type) =>
        ActiveModifiers.Any(m => m.effects.Any(e => e.type == type));
}
```

### 4. 잠금 해제 저장

```csharp
// SaveManager에 추가
public void UnlockModifier(string modifierID)
{
    var unlocked = LoadUnlockedModifiers();
    if (!unlocked.Contains(modifierID))
    {
        unlocked.Add(modifierID);
        SaveUnlockedModifiers(unlocked);
        
        // 잠금 해제 알림 표시
        ToastNotification.Show($"새 챌린지 해금: {modifierID}");
    }
}

public bool IsModifierUnlocked(string modifierID)
{
    return LoadUnlockedModifiers().Contains(modifierID);
}
```

### 5. 씬 전환 간 데이터 유지

`RunSessionManager`를 `DontDestroyOnLoad`로 관리하거나,
데이터를 JSON 형태로 임시 파일에 저장 후 게임씬 진입 시 로드:

```csharp
private void Awake()
{
    if (Instance != null && Instance != this) { Destroy(gameObject); return; }
    Instance = this;
    DontDestroyOnLoad(gameObject);
}
```

---

## OnionCat 적용 포인트

### A. OnionCat 전용 모디파이어 아이디어

| 모디파이어 명 | 효과 | 해금 조건 |
|-------------|------|----------|
| **"대시 봉인"** | Cat 대시 비활성화 | 기본 해금 |
| **"실드 봉인"** | Crop 실드 비활성화 | 기본 해금 |
| **"반전 제어"** | P1·P2 조작 캐릭터 맞교환 | 기본 클리어 1회 |
| **"엘리트만 등장"** | 일반 적 제거, 엘리트·보스만 | 3회 클리어 |
| **"체력 공유 없음"** | Cat·Crop 체력 완전 분리 (각자 사망 가능) | 5회 클리어 |
| **"노드롭 챌린지"** | 체력·골드 드롭 없음 | 10회 클리어 |
| **"방당 1분 제한"** | 방 입장 후 60초 내 클리어 못하면 패널티 | 7회 클리어 |

### B. 구현 순서 (초보자용 권장 순서)

1. `RunModifierData` ScriptableObject 클래스 작성
2. 2~3개 샘플 모디파이어 에셋 생성 ("대시 봉인", "적 체력 2배")
3. 간단한 모디파이어 선택 UI (토글 버튼 리스트) 제작
4. `RunSessionManager` 싱글턴 작성 + `DontDestroyOnLoad`
5. 게임 씬에서 모디파이어 효과 적용하는 코드 연결
6. 테스트 → 각 모디파이어가 실제 게임에 적용되는지 확인
7. 잠금 해제 조건 시스템 + SaveManager 연동

### C. 메타 진행과 연동
- 클리어 횟수·업적에 따라 새 모디파이어 해금
- 어려운 모디파이어 + 클리어 시 특별 엔딩 또는 스킨 해금
- 점수 보너스 배율 → 리더보드와 연동하면 시너지

---

## 참고 링크

- [Hades - Pact of Punishment 공식 위키](https://hades.fandom.com/wiki/Pact_of_Punishment)
- [Dead Cells - Boss Cells 설명](https://deadcells.fandom.com/wiki/Boss_Stem_Cells)
- [GMTK - How Hades Makes Hard Mode Fun](https://www.youtube.com/watch?v=OVJDOHMYgIE)
- [Unity ScriptableObject 공식 튜토리얼](https://learn.unity.com/tutorial/introduction-to-scriptable-objects)
- [Unity DontDestroyOnLoad 공식 문서](https://docs.unity3d.com/ScriptReference/Object.DontDestroyOnLoad.html)
