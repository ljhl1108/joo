# 로딩 화면 & 힌트 팁 시스템 (Loading Screen & Hint Tips System)

리서치 날짜: 2026-07-06

## 개요

로딩 화면은 씬 전환 중 플레이어에게 진행 상황을 알리고, 힌트/팁을 통해 대기 시간을 유익하게 채우는 시스템이다.

OnionCat에서 필요한 이유:
- **씬 전환 시 빈 화면 방지**: 첫 씬 로드, 플로어 간 이동, 게임 오버 후 재시작 시 블랙 화면이 아닌 정보 제공
- **게임플레이 힌트 전달**: 튜토리얼 없이도 핵심 기믹(협력 필수, 근접/원거리 약점) 자연스럽게 학습
- **게임 세계관 구축**: 짧은 문구나 캐릭터 대사로 Cat & Onion의 관계 표현

로그라이크에서 로딩 화면 활용 예시: Hades(신화 힌트), Dead Cells(팁), Binding of Isaac(이상한 유머)

---

## Unity 구현 방법

### 1. 비동기 씬 로딩 기반 구조

```csharp
// LoadingScreenManager.cs
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using System.Collections;
using TMPro;

public class LoadingScreenManager : MonoBehaviour
{
    public static LoadingScreenManager Instance { get; private set; }

    [SerializeField] private GameObject loadingScreenCanvas;
    [SerializeField] private Slider progressBar;
    [SerializeField] private TextMeshProUGUI tipText;
    [SerializeField] private TextMeshProUGUI percentText;
    [SerializeField] private float minimumLoadTime = 1.5f; // 너무 빠르면 화면이 번쩍임

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        loadingScreenCanvas.SetActive(false);
    }

    public void LoadScene(string sceneName)
    {
        StartCoroutine(LoadSceneRoutine(sceneName));
    }

    IEnumerator LoadSceneRoutine(string sceneName)
    {
        // 힌트 설정
        tipText.text = TipDatabase.GetRandomTip();

        // 로딩 화면 표시 (페이드 인)
        loadingScreenCanvas.SetActive(true);

        float elapsed = 0f;
        AsyncOperation op = SceneManager.LoadSceneAsync(sceneName);
        op.allowSceneActivation = false; // 로딩 완료 후 바로 전환하지 않음

        while (!op.isDone)
        {
            elapsed += Time.unscaledDeltaTime;
            float progress = Mathf.Clamp01(op.progress / 0.9f); // 0.9가 실제 100%

            progressBar.value = progress;
            percentText.text = $"{Mathf.RoundToInt(progress * 100)}%";

            // 최소 로딩 시간 보장 + 실제 로딩 완료 대기
            if (op.progress >= 0.9f && elapsed >= minimumLoadTime)
            {
                op.allowSceneActivation = true;
            }

            yield return null;
        }

        loadingScreenCanvas.SetActive(false);
    }
}
```

### 2. 힌트 데이터베이스 — ScriptableObject 방식

```csharp
// TipDatabase.cs — ScriptableObject로 팁 관리
using UnityEngine;

[CreateAssetMenu(fileName = "TipDatabase", menuName = "OnionCat/TipDatabase")]
public class TipDatabase : ScriptableObject
{
    [System.Serializable]
    public class TipEntry
    {
        [TextArea(2, 4)]
        public string text;
        [Range(1, 10)]
        public int weight = 5; // 가중치: 높을수록 자주 등장
    }

    [SerializeField] private TipEntry[] tips;

    private static TipDatabase instance;

    public static string GetRandomTip()
    {
        if (instance == null)
            instance = Resources.Load<TipDatabase>("TipDatabase");

        return instance.GetWeightedRandomTip();
    }

    private string GetWeightedRandomTip()
    {
        int totalWeight = 0;
        foreach (var tip in tips) totalWeight += tip.weight;

        int roll = Random.Range(0, totalWeight);
        int cumulative = 0;
        foreach (var tip in tips)
        {
            cumulative += tip.weight;
            if (roll < cumulative) return tip.text;
        }
        return tips[0].text;
    }
}
```

### 3. 씬별 로딩 타입 분기

```csharp
public enum LoadingType
{
    Instant,    // 방 이동 (내부 씬 전환, 페이드만)
    Quick,      // 같은 플로어 재시작 (0.5초)
    Full        // 플로어 이동, 게임 오버 후 재시작 (힌트 표시)
}

public void LoadScene(string sceneName, LoadingType type = LoadingType.Full)
{
    switch (type)
    {
        case LoadingType.Instant:
            SceneManager.LoadScene(sceneName);
            break;
        case LoadingType.Quick:
            StartCoroutine(LoadSceneRoutine(sceneName, minimumTime: 0.5f, showTip: false));
            break;
        case LoadingType.Full:
            StartCoroutine(LoadSceneRoutine(sceneName, minimumTime: 1.5f, showTip: true));
            break;
    }
}
```

### 4. 로딩 화면 UI 구성 (Canvas 구조)

```
LoadingCanvas (DontDestroyOnLoad)
├── BackgroundPanel (검은 패널 또는 게임 아트)
├── CenterGroup
│   ├── LogoImage (게임 로고 / 캐릭터 아트)
│   ├── TipText (TextMeshPro)
│   └── TipLabel ("TIP" 레이블)
└── BottomGroup
    ├── ProgressBar (Slider)
    └── PercentText ("73%")
```

### 5. OnionCat 힌트 텍스트 예시

```
// TipDatabase ScriptableObject에 입력할 내용들
"고양이는 근접 공격, 양파는 원거리 공격. 둘의 협력이 핵심이야!"
"일부 적은 근접 공격에만 반응해. 고양이가 돌격할 때야!"
"방어막(Shield)으로 적의 투사체를 튕겨낼 수 있어. 타이밍을 잡아봐."
"대시는 무적이야! 위험한 순간엔 주저 말고 대시."
"Cat: '조심해!' Onion: '알아, 알아...'"
"적을 처치하면 가끔 씨앗이 떨어져. 절대 놓치지 마."
"업그레이드는 런마다 달라져. 이번 런엔 어떤 조합을?"
"보스 방은 항상 문이 잠겨. 모든 적을 처치해야 열려!"
```

---

## OnionCat 적용 포인트

### 로딩 화면이 필요한 씬 전환 시점
1. **게임 시작 → 첫 번째 플로어**: 풀 로딩 화면 + 기본 힌트
2. **플로어 클리어 → 다음 플로어**: 풀 로딩 화면 + "다음 플로어 예고" 텍스트
3. **게임 오버 → 재시작**: 퀵 로딩 (0.8초) + 짧은 격려 메시지
4. **메인 메뉴 → 게임 시작**: 풀 로딩 화면 + 게임 조작법 힌트

### 힌트 카테고리 분류 권장
- **조작법 힌트** (weight 8): 초보 플레이어 대상, 게임 초반 반복 등장
- **전략 힌트** (weight 5): "Cat이 적을 밀면 Onion으로 마무리!"
- **세계관 플레이버** (weight 3): Cat과 Onion의 짧은 대화체
- **이스터에그** (weight 1): 유머러스한 메시지, 희귀하게 등장

### 로딩 최소 시간 권장값
- Unity 에디터에서는 씬 로딩이 매우 빠름 → `minimumLoadTime = 1.5f` 설정으로 UX 보장
- 실제 빌드에서 로딩이 오래 걸리면 자동으로 대기
- 모바일 빌드는 `minimumLoadTime = 0.5f`로 단축 권장

### 구현 우선순위
1. 먼저 블랙 화면 페이드 인/아웃 (`Scene_Transition.md` 참고)으로 시작
2. 진행 바 추가 (진짜 로딩 진행 반영)
3. TipDatabase ScriptableObject 작성 + 무작위 힌트 표시
4. 가중치 시스템 적용 (선택)

---

## 참고 링크

- Unity SceneManager.LoadSceneAsync: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadSceneAsync.html
- Unity AsyncOperation.allowSceneActivation: https://docs.unity3d.com/ScriptReference/AsyncOperation-allowSceneActivation.html
- Unity ScriptableObject: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- "Loading Screens Done Right" (Unity Blog): https://blog.unity.com/games/loading-scenes
- Game UI 로딩 화면 UX 참고: https://www.gamedeveloper.com/design/the-best-loading-screens-in-games
