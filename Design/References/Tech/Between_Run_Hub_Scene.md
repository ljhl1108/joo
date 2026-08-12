# Between-Run Hub Scene

리서치 날짜: 2026-08-12

## 개요

로그라이크에서 런 사이에 플레이어가 돌아오는 **안전한 거점 씬**.  
단순한 메인 메뉴와 달리, 게임 세계 내 공간으로 존재하며 메타 진행을 담당한다.

### 대표 레퍼런스
| 게임 | 허브 이름 | 특징 |
|------|----------|------|
| Hades | House of Hades | NPC 대화가 매 런마다 변함, 허브 자체가 스토리 |
| Enter the Gungeon | The Breach | 특수 NPC 잠금 해제, 아이템 사전 확인 |
| Dead Cells | 감옥 (Prisoners' Quarters) | 영구 업그레이드 상점이 허브 역할 |
| Risk of Rain 2 | 캐릭터 선택 로비 | 런 시작 전 스테이지 |
| Rogue Legacy 2 | 성 입구 + 족보 | 세대 간 업그레이드가 허브를 성장시킴 |

OnionCat에서는 **고양이와 파가 쉬는 텃밭/집**이 이 역할을 담당할 수 있다.

---

## 왜 허브 씬이 필요한가

1. **메타 진행 표시 공간** — 영구 업그레이드, 잠금 해제 콘텐츠를 세계 안에서 표현
2. **감정 호흡** — 긴장된 런 후 긴장 해소, 다음 런 준비 동기 부여
3. **스토리텔링** — NPC 대화, 환경 변화로 내러티브를 런 플레이 없이 전달
4. **재도전 의지** — "저 NPC가 뭔 말 할지 궁금해서 다시 하게 됨" (Hades 효과)

---

## Unity 구현 방법

### 씬 구조

```
Scenes/
├── Boot.unity          ← 최초 실행, HubScene으로 전환
├── HubScene.unity      ← 허브 (이 파일이 핵심)
├── GameScene.unity     ← 실제 던전 런
└── GameOver.unity      ← 런 결과 → 허브로 복귀
```

### HubScene 핵심 오브젝트 구성

```
HubScene
├── HubManager          ← 허브 전체 상태 관리
├── Player (Cat+Crop)   ← 캐릭터 (이동 가능, 전투 없음)
├── Camera              ← 고정 또는 플레이어 추적
├── UI/
│   ├── MetaProgressPanel   ← 영구 업그레이드 표시
│   └── RunStartButton      ← 던전 입장 버튼
├── NPCs/
│   └── NPC_Vendor, NPC_Story, ...
├── Interactables/
│   ├── StartPortal         ← 런 시작 트리거
│   └── UpgradeAltar        ← 영구 업그레이드 구매
└── Environment/
    └── Garden (시각적 성장 표현)
```

### HubManager

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;

public class HubManager : MonoBehaviour
{
    public static HubManager Instance { get; private set; }

    [SerializeField] private string dungeonSceneName = "GameScene";
    
    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        
        RefreshHubState();
    }

    private void RefreshHubState()
    {
        // MetaProgress에서 데이터 읽어 허브 비주얼 갱신
        int totalRuns = MetaProgressionManager.Instance.TotalRuns;
        UpdateGardenVisual(totalRuns);
        UnlockNPCs();
    }

    public void StartRun()
    {
        // 런 시작 전 인트로 연출 (선택)
        SceneManager.LoadScene(dungeonSceneName);
    }

    private void UpdateGardenVisual(int runCount)
    {
        // 런 횟수에 따라 텃밭 오브젝트 활성화
        // [SerializeField] GameObject[] gardenStages — 유니티 에디터에서 드래그 앤 드롭 설정 필요
    }

    private void UnlockNPCs()
    {
        // 잠금 해제 조건 체크 후 NPC 활성화
        // [SerializeField] NPCUnlockData[] npcUnlocks — 유니티 에디터에서 드래그 앤 드롭 설정 필요
    }
}
```

### NPC 대화 시스템 (간단 버전)

```csharp
using UnityEngine;
using TMPro;

public class HubNPC : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI dialogueText;
    [SerializeField] private GameObject dialoguePanel;
    
    // ScriptableObject로 대화 데이터 관리
    [SerializeField] private HubDialogueSO dialogueData;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (!other.CompareTag("Player")) return;
        ShowDialogue();
    }

    private void OnTriggerExit2D(Collider2D other)
    {
        if (!other.CompareTag("Player")) return;
        dialoguePanel.SetActive(false);
    }

    private void ShowDialogue()
    {
        int runCount = MetaProgressionManager.Instance.TotalRuns;
        string line = dialogueData.GetLineForRunCount(runCount);
        dialogueText.text = line;
        dialoguePanel.SetActive(true);
    }
}
```

```csharp
[CreateAssetMenu(menuName = "OnionCat/Hub Dialogue")]
public class HubDialogueSO : ScriptableObject
{
    [System.Serializable]
    public struct DialogueEntry
    {
        public int minRuns;   // 이 대화가 나오는 최소 런 수
        public string line;
    }
    
    [SerializeField] private DialogueEntry[] entries;

    public string GetLineForRunCount(int runs)
    {
        // 조건 맞는 가장 높은 minRuns의 대화 반환
        string best = entries[0].line;
        foreach (var entry in entries)
        {
            if (runs >= entry.minRuns)
                best = entry.line;
        }
        return best;
    }
}
```

### 허브 → 던전 전환

```csharp
public class StartPortal : MonoBehaviour
{
    private bool playerInRange = false;

    private void Update()
    {
        // [SerializeField] InputActionReference interactAction — 에디터에서 설정 필요
        if (playerInRange && Input.GetKeyDown(KeyCode.E))
            HubManager.Instance.StartRun();
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
        {
            playerInRange = true;
            ShowPrompt(true); // "E: 던전 입장" UI
        }
    }

    private void OnTriggerExit2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
        {
            playerInRange = false;
            ShowPrompt(false);
        }
    }

    private void ShowPrompt(bool show)
    {
        // [SerializeField] GameObject interactPrompt — 에디터에서 드래그 앤 드롭 설정 필요
    }
}
```

### 런 종료 후 허브 복귀

```csharp
// GameOver 씬 또는 런 클리어 씬에서 호출
public class RunEndHandler : MonoBehaviour
{
    [SerializeField] private float delayBeforeReturn = 3f;

    public void ReturnToHub()
    {
        StartCoroutine(ReturnAfterDelay());
    }

    private IEnumerator ReturnAfterDelay()
    {
        // 페이드 아웃
        yield return new WaitForSeconds(delayBeforeReturn);
        SceneManager.LoadScene("HubScene");
    }
}
```

---

## 구현 순서 (초보 개발자 권장)

```
Phase 1 — 기능만 있는 허브
  1. HubScene 생성, 빈 플레이어 캐릭터 이동 가능하게
  2. StartPortal 배치 → E키로 GameScene 이동
  3. GameScene 종료 시 HubScene으로 복귀

Phase 2 — 데이터 연결
  4. MetaProgressionManager에서 런 횟수 읽기
  5. 허브에서 영구 업그레이드 구매 UI 연결

Phase 3 — 분위기 추가
  6. NPC 1~2명 배치, ScriptableObject로 대화 데이터 연결
  7. 런 횟수 따라 허브 비주얼 변화 (식물 성장, 등불 추가 등)
```

---

## OnionCat 적용 포인트

### 컨셉: 고양이의 텃밭 (The Garden)

- 고양이와 파(양파)가 원래 살던 텃밭이 허브
- 런에서 얻은 씨앗/재료로 텃밭이 성장
- 잠금 해제된 NPC: 두더지 상인, 나비 치유사, 지렁이 정보원

### 시각적 성장 아이디어
- 런 0: 황폐한 텃밭, 잡초
- 런 5: 첫 번째 채소 싹
- 런 10: 작은 오두막 생성
- 런 20: 완성된 텃밭, 다양한 채소, NPC 마을 형성

### 첫 번째 허브 구현 체크리스트

```
[ ] HubScene.unity 생성
[ ] 고양이 캐릭터 허브용 이동 스크립트 (전투 없음, 간단 버전)
[ ] StartPortal → 던전 씬 전환
[ ] 런 종료 후 HubScene 복귀 로직
[ ] HubManager 싱글턴 구현
[ ] MetaProgressionManager와 데이터 연결
[ ] NPC 1마리 + 대화 1줄
```

---

## 참고 링크

- Unity SceneManagement: https://docs.unity3d.com/Manual/SceneManagement.html
- Hades 개발 후기 — NPC & World: https://www.gdcvault.com/play/1026352/
- Enter the Gungeon 레벨 디자인 분석: https://www.gamedeveloper.com/design/how-enter-the-gungeon-s-breach-creates-a-sense-of-place
- Unity 공식 2D RPG 튜토리얼 (씬 구조 참고): https://learn.unity.com/project/2d-rpg-kit
