# Steam Next Fest 데모 빌드 시스템

리서치 날짜: 2026-10-22

## 개요

Steam Next Fest는 Valve가 연 3회(2·6·10월 예정) 개최하는 1주짜리 행사로,
미출시 게임이 무료 데모를 올리고 플레이어와 스트리머에게 노출되는 기회다.

OnionCat은 M5 마일스톤(itch.io 비공개 테스트) 이후 Steam Next Fest 참가가 현실적 목표다.
데모는 풀게임 빌드에서 콘텐츠 일부를 막는 방식이 가장 효율적이다.

---

## Steam 데모 기본 사항

### 앱 구조
- Steam에서 데모는 **별도 App ID**를 부여받음 (Steamworks 개발자 대시보드에서 무료 생성)
- 데모 전용 App ID → 플레이 시간·리뷰·데이터가 본 게임과 분리됨
- 데모를 플레이한 사람이 본 게임 위시리스트에 추가하기 쉽도록 스토어 링크 필수

### 데모 제약 (Steam 정책)
- 무료 플레이, 시간 제한 없음 (단 Next Fest 기간 외에는 내리거나 유지 선택)
- 세이브 데이터를 본 게임으로 이전하는 것은 가능하지만 OnionCat 규모에서는 불필요

---

## Unity 구현 방법

### 1. 빌드 플래그로 콘텐츠 게이팅

**Scripting Define Symbols에 `DEMO_MODE` 추가** (Build Settings → Player Settings):

```csharp
// DemoGate.cs
public static class DemoGate
{
#if DEMO_MODE
    public static bool IsDemo => true;
#else
    public static bool IsDemo => false;
#endif
    
    // 데모 종료 조건: Stage 1 보스 클리어 후
    public static bool ShouldBlockProgress(int stageIndex)
    {
        return IsDemo && stageIndex >= 1; // Stage 0 = 무너진 정원 (스테이지 1)
    }
}
```

### 2. 데모 게이트 씬 (DemoEndScreen)

```csharp
// DungeonManager.cs 수정
void OnStageClear(int stageIndex)
{
    if (DemoGate.ShouldBlockProgress(stageIndex))
    {
        GameManager.Instance.ChangeState(GameState.DemoEnd);
        return;
    }
    // 일반 다음 스테이지 진행...
}
```

```csharp
// DemoEndScreen.cs
public class DemoEndScreen : MonoBehaviour
{
    [SerializeField] Button wishlistButton;
    [SerializeField] Button mainMenuButton;
    
    void Start()
    {
        // 런 결과 화면과 같은 통계 표시 (처치 수, 시간 등)
        // + "전체 게임을 플레이하면 3스테이지 + 163종 장비를 즐길 수 있습니다!" 문구
        
        wishlistButton.onClick.AddListener(() => {
            Application.OpenURL("https://store.steampowered.com/app/[APPID]");
        });
    }
}
```

### 3. 데모 전용 콘텐츠 줄이기

**장비 개수**: 163종 전부 드랍하면 데모에서 "다 봤다"는 느낌. 데모에서는 30~40종만.

`RewardTable.asset` 방식 대신 데모 전용 RewardTable 에셋 별도 생성:
```
Assets/Data/RewardTable.asset          ← 본 게임
Assets/Data/RewardTable_Demo.asset     ← 데모 (장비 수 제한)
```

```csharp
// GameManager.cs
RewardTable GetRewardTable() =>
    DemoGate.IsDemo
        ? Resources.Load<RewardTable>("RewardTable_Demo")
        : Resources.Load<RewardTable>("RewardTable");
```

### 4. 빌드 자동화 스크립트

```csharp
// BuildScript.cs (에디터 전용)
public static class BuildScript
{
    [MenuItem("OnionCat/Build/Demo Build")]
    static void BuildDemo()
    {
        var options = new BuildPlayerOptions
        {
            scenes = GetScenePaths(),
            locationPathName = "Builds/Demo/OnionCat_Demo.exe",
            target = BuildTarget.StandaloneWindows64,
            extraScriptingDefines = new[] { "DEMO_MODE" }
        };
        BuildPipeline.BuildPlayer(options);
        Debug.Log("Demo build complete.");
    }

    [MenuItem("OnionCat/Build/Full Build")]
    static void BuildFull()
    {
        var options = new BuildPlayerOptions
        {
            scenes = GetScenePaths(),
            locationPathName = "Builds/Full/OnionCat.exe",
            target = BuildTarget.StandaloneWindows64
        };
        BuildPipeline.BuildPlayer(options);
    }

    static string[] GetScenePaths() =>
        EditorBuildSettings.scenes
            .Where(s => s.enabled)
            .Select(s => s.path)
            .ToArray();
}
```

---

## OnionCat 적용 포인트

### 데모 범위 결정

| 항목 | 데모 | 풀 게임 |
|------|------|---------|
| 스테이지 | 1개 (무너진 정원) | 3개 |
| 보스 | 성녀 궁수 | 3명 |
| 장비 | ~40종 | 163종 |
| 물음표 이벤트 | 4개 | 8개 |
| 플레이 시간 예상 | 15~30분 | ~1시간 |

### 데모 특유의 설계 고려사항

1. **첫 5분이 전부**: 데모 플레이어는 풀 게임 구매자와 다르게 "바로 재미를 느껴야" 계속 함
   - 첫 방부터 협동 콤보 유도 (튜토리얼 메시지)
   - 첫 2~3방 내에 장비 드랍 1~2개 보장 (데모 전용 드랍률 상향)

2. **장비 종류 선별**: 세트 보너스가 빠르게 드러나야 "더 하고 싶다"는 욕구 생성
   - 데모에서 태양(Sun) 세트 장비 집중 → 2단계 보너스까지 경험 가능
   - Wind 세트는 풀 게임 유인 요소로 제외

3. **데모 끝 화면**: 런 결과와 이어서 노출 (기존 화면 재사용 + 추가 UI만)
   - "오늘 플레이 통계" + "위시리스트 추가" 버튼 크게
   - 클리어 실패 시도: "다시 도전" + "위시리스트"

4. **Steam Next Fest 타이밍**: 행사 신청은 보통 2~3개월 전에 열림
   - M5 완료 후 → 다음 Next Fest 신청 → 1주일 전 데모 업로드 권장

### 빌드 구성 체크리스트

- [ ] `DEMO_MODE` 정의 심볼 Player Settings에 추가
- [ ] `RewardTable_Demo.asset` 생성 (장비 ~40종)
- [ ] `DemoEndScreen` 씬/프리팹 제작
- [ ] 스팀 상점 링크 URL 상수화 (`GameConstants.SteamStoreURL`)
- [ ] Build 메뉴에 데모/풀게임 버튼 분리
- [ ] 데모 빌드 시 `meta.json` 초기화 (플레이테스터 진행 데이터 유출 방지)
- [ ] 데모 고유 AppId로 스팀 빌드 업로드

---

## 참고 링크

- [Steamworks 데모 설정 가이드](https://partner.steamgames.com/doc/store/application/demos)
- [Steam Next Fest 신청 안내](https://partner.steamgames.com/doc/marketing/upcoming_events/nextfest)
- [Unity 스크립팅 Define Symbols 문서](https://docs.unity3d.com/Manual/CustomScriptingSymbols.html)
- [GMTK: 게임 데모 만드는 법](https://www.youtube.com/watch?v=... - "how to make a good game demo")
