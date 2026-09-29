# 세이브 데이터 리셋 / 전체 진행 초기화 화면

리서치 날짜: 2026-09-29

## 개요

완성된 게임에는 반드시 **"처음부터 다시 시작"** 기능이 필요하다.  
로그라이크에서는 특히 중요한데, 메타 진행 데이터(업그레이드 해금, 통계, 런 기록)가 쌓이기 때문에  
가끔 클린 스타트를 원하는 플레이어, QA 테스트, 코옵 파트너와 공유하는 기기 등을 위해 필수다.

**잘못 구현하면 실수로 수십 시간의 진행 데이터가 지워지는 최악의 UX 문제가 된다.** 이 기능은 반드시 이중 확인 구조로 만들어야 한다.

---

## Unity 구현 방법

### 1. 저장 데이터 위치 파악

OnionCat에서 삭제해야 할 데이터:
```
1. PlayerPrefs (Unity 기본 저장소)
   - 위치: HKEY_CURRENT_USER\Software\[CompanyName]\[ProductName] (Windows)
   - 삭제: PlayerPrefs.DeleteAll()

2. JSON 파일 (메타 진행, 런 기록 등)
   - 위치: Application.persistentDataPath
   - 예: C:/Users/feedb/AppData/LocalLow/[Company]/OnionCat/

3. 업적/통계 (로컬)
   - 위치: persistentDataPath 내 별도 파일
```

### 2. 이중 확인 UI 구조

```
[1단계] 설정 메뉴 → "데이터 초기화" 버튼 클릭
    ↓
[2단계] 확인 팝업 출력:
    "정말 모든 진행 데이터를 삭제하시겠습니까?
    런 기록, 업그레이드 해금, 통계가 모두 삭제됩니다.
    이 작업은 되돌릴 수 없습니다."
    [취소] [삭제]
    ↓ (삭제 클릭 시)
[3단계] (선택적) 두 번째 확인:
    "확인: 아래에 'DELETE'를 입력하세요" (중요한 데이터 보호용)
    ↓
[4단계] 데이터 삭제 실행 → 타이틀 화면으로 이동
```

### 3. 데이터 리셋 코드

```csharp
public class SaveDataResetManager : MonoBehaviour
{
    // 설정에서 호출: 리셋 종류 분리
    public enum ResetType
    {
        CurrentRunOnly,   // 현재 런 포기 (중간 저장 삭제)
        AllProgress       // 전체 초기화 (메타 진행 포함)
    }

    public void ExecuteReset(ResetType type)
    {
        switch (type)
        {
            case ResetType.CurrentRunOnly:
                ResetCurrentRun();
                break;
            case ResetType.AllProgress:
                ResetAllProgress();
                break;
        }
    }

    private void ResetCurrentRun()
    {
        // 현재 런 데이터만 삭제 (RunData)
        GameManager.Instance.Run = new RunData();
        DeleteFile("current_run.json");
        // 메인 메뉴로 이동
        SceneManager.LoadScene(SceneNames.MainMenu);
    }

    private void ResetAllProgress()
    {
        // 1. PlayerPrefs 전체 삭제
        PlayerPrefs.DeleteAll();
        PlayerPrefs.Save();

        // 2. persistentDataPath 파일 전체 삭제
        string savePath = Application.persistentDataPath;
        if (Directory.Exists(savePath))
        {
            // 특정 파일만 삭제 (전체 폴더 날리면 위험)
            string[] saveFiles = { "meta_progress.json", "current_run.json", 
                                   "statistics.json", "run_history.json" };
            foreach (string file in saveFiles)
            {
                string fullPath = Path.Combine(savePath, file);
                if (File.Exists(fullPath))
                    File.Delete(fullPath);
            }
        }

        // 3. 메모리 내 데이터도 초기화
        GameManager.Instance.Run = new RunData();

        // 4. 앱 재시작 or 타이틀 이동
        // 완전 초기화는 재시작이 가장 안전
        Application.Quit();
        // 개발 중엔:
        // UnityEditor.EditorApplication.isPlaying = false;
    }

    private void DeleteFile(string fileName)
    {
        string path = Path.Combine(Application.persistentDataPath, fileName);
        if (File.Exists(path))
            File.Delete(path);
    }
}
```

### 4. 확인 팝업 UI (간단 구현)

```csharp
public class ResetConfirmationPanel : MonoBehaviour
{
    [SerializeField] private Button confirmButton;
    [SerializeField] private Button cancelButton;
    [SerializeField] private TMP_Text warningText;
    
    // 이중 확인을 위한 상태
    private bool firstConfirmDone = false;

    private void Start()
    {
        confirmButton.onClick.AddListener(OnConfirmClicked);
        cancelButton.onClick.AddListener(OnCancelClicked);
        UpdateUI();
    }

    private void OnConfirmClicked()
    {
        if (!firstConfirmDone)
        {
            // 1차 확인 후 더 강한 경고 표시
            firstConfirmDone = true;
            warningText.text = "마지막 경고: 모든 데이터가 영구 삭제됩니다!";
            confirmButton.GetComponentInChildren<TMP_Text>().text = "네, 삭제합니다";
        }
        else
        {
            // 2차 확인 → 실행
            FindFirstObjectByType<SaveDataResetManager>()
                .ExecuteReset(SaveDataResetManager.ResetType.AllProgress);
        }
    }

    private void OnCancelClicked()
    {
        firstConfirmDone = false;
        gameObject.SetActive(false);
    }

    private void UpdateUI()
    {
        warningText.text = "모든 진행 데이터(업그레이드, 통계, 기록)가 삭제됩니다.\n이 작업은 되돌릴 수 없습니다.";
    }
}
```

### 5. UX 디자인 원칙

```
DO (해야 할 것):
✓ 무엇이 삭제되는지 구체적으로 명시 (업그레이드, 통계, 기록)
✓ 이중 확인 (실수 방지)
✓ 취소 버튼을 더 크게/눈에 띄게 (파괴적 액션은 취소 유도)
✓ 성공 시 앱 재시작 or 타이틀 이동 (깨끗한 상태에서 재시작)
✓ "런 포기"와 "전체 초기화"를 별도 메뉴로 분리

DON'T (하면 안 되는 것):
✗ 단 한 번의 클릭으로 전체 삭제 되게 하기
✗ 삭제 후 같은 씬에서 계속 진행 (데이터 불일치 가능)
✗ "OK/Cancel" 대신 "Yes/No"만 표시 (무엇을 Yes하는지 불명확)
✗ Directory.Delete(savePath, true) 전체 폴더 삭제 (다른 앱 데이터 혼재 가능)
```

---

## OnionCat 적용 포인트

### 설정 메뉴 내 리셋 구조 제안

```
설정 메뉴 → 데이터 탭
├── [현재 런 포기]       ← 플레이 중에만 활성화
│   → 확인 팝업 1회 → GameManager.ChangeState(GameState.GameOver) 후 메뉴 이동
│
└── [전체 진행 초기화]   ← 항상 보이지만 숨겨진 곳에
    → 이중 확인 팝업 → 모든 JSON 삭제 → Application.Quit() 또는 타이틀 이동
```

### 삭제 대상 파일 목록 (OnionCat 기준)
- `meta_progress.json` — 영구 업그레이드 해금
- `current_run.json` — 진행 중인 런 중간 저장
- `run_history.json` — 런 기록·통계
- PlayerPrefs — 설정 값 (별도로 두거나 함께 삭제 선택 가능)

### 코옵 2인 공용 기기 시나리오
가족/친구와 같은 PC를 쓸 경우  
→ **"Player 1 데이터"** / **"Player 2 데이터"** 분리 저장 + 개별 초기화 고려  
→ 파일명에 플레이어 ID 포함: `meta_progress_p1.json`, `meta_progress_p2.json`

---

## 참고 링크

- [Unity PlayerPrefs API 문서](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [Unity Application.persistentDataPath](https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html)
- [How to Delete Save Data in Unity (Brackeys 스타일)](https://www.youtube.com/results?search_query=unity+delete+save+data+playerprefs)
- [UX 패턴: Destructive Action Confirmation (Nielsen Norman Group)](https://www.nngroup.com/articles/confirmation-dialog/)
- [System.IO.File/Directory API (Microsoft Docs)](https://learn.microsoft.com/en-us/dotnet/api/system.io.file)
