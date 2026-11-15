# Tutorial Seen-State Persistence System

리서치 날짜: 2026-11-15

## 개요

튜토리얼 힌트나 도움말이 "처음 봤을 때 한 번만" 나타나고, 다음 판부터는 나오지 않게 하는 시스템.
독립된 Tutorial 시스템(`Tutorial_System.md`)과 연동되는 **상태 저장 레이어**다.

왜 별도 주제로 다루는가:
- 튜토리얼 표시 로직과 "언제 보여줄지" 판단 로직이 뒤섞이면 복잡해짐
- Save/Load 시스템(`Save_Load_System.md`)과 연동해야 하는데, 연결 방법이 명확해야 함
- 초보 개발자가 가장 흔히 실수하는 부분: "런 중에만 체크" vs "판 간에도 유지"

---

## 핵심 개념

### 튜토리얼 힌트의 세 가지 범위

| 범위 | 설명 | 예시 |
|---|---|---|
| **런 내 1회** | 이번 판에서만 한 번 | "대쉬로 무적 프레임!" (1판마다 첫 대쉬 시) |
| **영구 1회** | 모든 판 통틀어 단 한 번 | "패링에 성공했습니다!" (처음 패링 성공 시) |
| **조건 충족 시마다** | 반복 허용 | 체력 20% 미만 경고 (매번 나와도 됨) |

OnionCat에서:
- 런 내 1회: 새 작물 처음 쓸 때 / 특수 공격 처음 발동할 때
- 영구 1회: 협동 콤보 처음 발생 시 / 패링 처음 성공 시 / 세트 보너스 처음 활성화 시
- 반복 허용: 거의 없음 (힌트보다는 HUD 경고로)

---

## Unity 구현 방법

### 단계 1: 튜토리얼 힌트 ID 정의

```csharp
public enum TutorialHintId
{
    // 영구 1회 (once-ever)
    ComboDemoFirst,
    ParrySuccessFirst,
    SetBonusActivatedFirst,
    JointUltimateFirst,
    
    // 런 내 1회 (once-per-run)
    SunflowerCropIntro,
    BlueMushCropIntro,
    CatSpecialAttackIntro,
    HairballThrowIntro,
}
```

### 단계 2: 상태 저장소

```csharp
// MetaProgress에 편입하거나 별도 클래스로
[System.Serializable]
public class TutorialSeenData
{
    // 영구 1회 힌트 — 한 번 보면 절대 안 나옴
    public HashSet<string> permanentlySeen = new HashSet<string>();
}

[System.Serializable]  
public class RunTutorialSeenData
{
    // 런 내 1회 힌트 — 판 시작 시 초기화
    public HashSet<string> seenThisRun = new HashSet<string>();
}
```

### 단계 3: TutorialManager

```csharp
public class TutorialManager : MonoBehaviour
{
    public static TutorialManager Instance { get; private set; }
    
    private TutorialSeenData permanent;
    private RunTutorialSeenData currentRun;

    // 런 시작 시 호출
    public void OnRunStart()
    {
        currentRun = new RunTutorialSeenData();
    }

    // 힌트를 보여줄지 체크 (true = 보여줘야 함)
    public bool ShouldShow(TutorialHintId id)
    {
        string key = id.ToString();
        bool isPermanent = IsPermanentHint(id);
        
        if (isPermanent)
            return !permanent.permanentlySeen.Contains(key);
        else
            return !currentRun.seenThisRun.Contains(key);
    }

    // 힌트를 봤다고 기록
    public void MarkSeen(TutorialHintId id)
    {
        string key = id.ToString();
        if (IsPermanentHint(id))
        {
            permanent.permanentlySeen.Add(key);
            SavePermanent();  // 즉시 저장
        }
        else
        {
            currentRun.seenThisRun.Add(key);
            // 런 중 세이브엔 포함 (MidRun save)
        }
    }

    // 힌트 표시 + 기록을 한 번에
    public bool TryShow(TutorialHintId id, string message, Transform speaker = null)
    {
        if (!ShouldShow(id)) return false;
        
        // Dialogue 시스템 호출 (OnionCat의 Dialogue.Play)
        if (speaker != null)
            Dialogue.Say(speaker, "도움말", message, Color.yellow);
        else
            Dialogue.Play(new[] { message });
        
        MarkSeen(id);
        return true;
    }

    bool IsPermanentHint(TutorialHintId id)
    {
        return id == TutorialHintId.ComboDemoFirst 
            || id == TutorialHintId.ParrySuccessFirst
            || id == TutorialHintId.SetBonusActivatedFirst
            || id == TutorialHintId.JointUltimateFirst;
    }
    
    void SavePermanent() { /* MetaProgress.Save() 호출 */ }
}
```

### 단계 4: 사용처에서 호출

```csharp
// 협동 콤보 처음 발생 시
void OnComboBonusTriggered()
{
    TutorialManager.Instance.TryShow(
        TutorialHintId.ComboDemoFirst,
        "번갈아 가며 공격하면 콤보 보너스!"
    );
    // ... 실제 콤보 로직
}

// 작물 교체 시
void OnCropChanged(CropData newCrop)
{
    if (newCrop.cropId == "sunflower")
        TutorialManager.Instance.TryShow(TutorialHintId.SunflowerCropIntro, 
            "해바라기: R로 햇빛 기둥을 불러 고양이를 회복!");
}
```

---

## 저장/로드 연동

### MetaProgress에 편입

```csharp
// MetaProgress.data에 추가
[System.Serializable]
public class MetaData
{
    // ... 기존 필드들
    public List<string> tutorialSeen = new List<string>(); // HashSet은 직렬화 안 됨
}

// 저장 시
MetaProgress.data.tutorialSeen = permanent.permanentlySeen.ToList();
MetaProgress.Save();

// 로드 시
permanent.permanentlySeen = new HashSet<string>(MetaProgress.data.tutorialSeen);
```

### 런 중 세이브에 포함

```csharp
// RunData 또는 MidRun save에 추가
[System.Serializable]
public class RunSaveData
{
    // ... 기존 필드들
    public List<string> tutorialSeenThisRun;
}
```

---

## 개발자 테스트 모드

```csharp
// OnionCat > Debug 메뉴에 추가
[MenuItem("OnionCat/Debug/Reset All Tutorial Hints")]
static void ResetAllTutorials()
{
    // MetaProgress.data.tutorialSeen 비우기
    MetaProgress.data.tutorialSeen.Clear();
    MetaProgress.Save();
    Debug.Log("모든 튜토리얼 힌트 초기화됨");
}

// 특정 힌트만 초기화
[MenuItem("OnionCat/Debug/Reset Run Tutorials")]
static void ResetRunTutorials()
{
    TutorialManager.Instance?.OnRunStart(); // currentRun 초기화
}
```

---

## OnionCat 적용 포인트

### 필요한 힌트 목록 (우선순위순)

| 우선순위 | 힌트 | 범위 | 트리거 |
|---|---|---|---|
| 1 | 협동 콤보 첫 발생 | 영구 | 콤보 발생 직후 |
| 2 | 패링 첫 성공 | 영구 | 패링 성공 직후 |
| 3 | 세트 보너스 첫 활성화 | 영구 | 세트 2단계 첫 충족 시 |
| 4 | 합동기 게이지 첫 충전 | 영구 | 게이지 100% 첫 도달 |
| 5 | 새 작물 첫 사용 | 런 내 | 작물 교체 직후 첫 발사 |
| 6 | 고양이 특수 공격 첫 발동 | 런 내 | 특수 공격 첫 발동 |
| 7 | 덤불 구덩이 첫 발견 | 런 내 | Pit 근처 접근 시 |

### 말풍선 연동

```csharp
// OnionCat의 Dialogue 시스템과 자연스럽게 연동
// 책 캐릭터가 힌트를 알려주는 연출로 쓸 수 있음
TutorialManager.Instance.TryShow(
    TutorialHintId.ParrySuccessFirst,
    "패링을 성공했군! 오른쪽 클릭으로 적의 공격을 반사할 수 있지.",
    bookTransform  // 말하는 책 위치
);
```

### 주의: `meta.json` 보호

테스트 중 메타 힌트 초기화를 하면 `meta.json`이 변경됨.
테스트 전 백업 필수 (기존 CLAUDE.md 주의사항과 동일한 맥락).

---

## 참고 링크

- Unity PlayerPrefs 대안 (ScriptableObject 세이브): https://unity.com/how-to/architect-game-code-scriptable-objects
- HashSet 직렬화: https://docs.unity3d.com/Manual/script-Serialization.html
- 첫 플레이 경험 설계: https://www.gamedeveloper.com/design/the-first-hour-of-your-game-s-tutorial
