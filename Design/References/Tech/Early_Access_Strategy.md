# Early Access Strategy (얼리 액세스 전략)

리서치 날짜: 2026-10-14

## 개요

Steam Early Access(이하 EA)는 미완성 게임을 유료로 공개하면서 플레이어 피드백과 수익을 동시에 얻는 방법이다.
OnionCat 같은 1인(소규모) 인디 로그라이크에게 EA는 단순 출시 채널이 아니라 **개발·피드백·마케팅 주기**를 돌리는 운영 전략 자체다.

잘못 사용하면 "버그 많은 미완성작" 이미지로 리뷰가 박히고 정식 출시 때 이미 지쳐버린다.
올바르게 사용하면 개발 방향을 검증하고, 코어 팬 커뮤니티를 만들고, 정식 출시 때 리뷰·위시리스트가 준비된 상태로 나올 수 있다.

---

## EA에 적합한 게임 조건 (OnionCat 체크리스트)

| 항목 | OnionCat 현황 | 권장 기준 |
|---|---|---|
| 핵심 루프 완성 | ✅ 런 클리어 가능 | 한 번의 런을 끝까지 플레이 가능해야 |
| 클리어 루트 존재 | ✅ 보스 1명 | 보스 최소 1명, 엔딩 화면 |
| 크래시 없는 안정성 | 점검 필요 | 세션 중 크래시율 5% 미만 |
| 핵심 재미 검증 | ✅ 킥·협동 콤보 | "이거 재미있다"가 10분 내에 생겨야 |
| 저장/불러오기 | ✅ 중간 저장 | 중단하고 이어할 수 있어야 |

**EA 입장 시점 권장**: 런 1~2 스테이지 완성, 장비 최소 50종, 방 15~20개

---

## Unity 구현 방법 (기술적 EA 지원 시스템)

### 1. EA 전용 버전 표시 (빌드 정보 UI)

```csharp
// 메인 메뉴 또는 하단 코너에 버전 정보 표시
[SerializeField] private TMP_Text _buildInfoText;

void Start()
{
    string version = Application.version;   // ProjectSettings에서 설정
    string buildDate = BuildInfo.Date;      // 빌드 시 자동 생성 (아래 참고)
    _buildInfoText.text = $"Early Access v{version}  ({buildDate})";
}
```

**자동 BuildInfo.cs 생성** (Editor 스크립트):
```csharp
// Assets/Editor/BuildDateInjector.cs
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;

public class BuildDateInjector : IPreprocessBuildWithReport
{
    public int callbackOrder => 0;

    public void OnPreprocessBuild(BuildReport report)
    {
        string code = $@"public static class BuildInfo
{{
    public static string Date = ""{System.DateTime.Now:yyyy-MM-dd}"";
}}";
        System.IO.File.WriteAllText("Assets/Scripts/BuildInfo.cs", code);
        AssetDatabase.ImportAsset("Assets/Scripts/BuildInfo.cs");
    }
}
```

### 2. 인게임 피드백 수집 링크 (F12 키)

```csharp
// 플레이어가 F12 누르면 구글 폼 / Discord 링크 열기
void Update()
{
    if (Input.GetKeyDown(KeyCode.F12))
        Application.OpenURL("https://forms.gle/yourformlink");
}
```

또는 메인 메뉴에 "버그 신고 / 피드백" 버튼 추가.

### 3. 세션 데이터 간단 로컬 로그

```csharp
// 런 종료 시 간단한 통계를 로컬 파일로 기록
// 개발자가 직접 플레이하고 체크 — 외부 서버 불필요
[System.Serializable]
public class RunLog
{
    public string date;
    public int runNumber;
    public float clearTimeSeconds;
    public int enemiesKilled;
    public int roomsCleared;
    public bool bossDefeated;
    public List<string> equippedGear;
}

public static void SaveRunLog(RunLog log)
{
    string path = Application.persistentDataPath + "/run_logs.json";
    // ... JSON 직렬화하여 append
}
```

### 4. EA 전용 "로드맵 팝업" (첫 실행 시)

```csharp
// PlayerPrefs로 첫 실행 감지, EA 로드맵 이미지/URL 표시
void Start()
{
    if (!PlayerPrefs.HasKey("ea_welcome_shown"))
    {
        ShowEAWelcomePopup();
        PlayerPrefs.SetInt("ea_welcome_shown", 1);
    }
}
```

---

## EA 운영 전략 (업데이트 주기 & 커뮤니케이션)

### 권장 업데이트 주기

| 기간 | 업데이트 내용 | 목표 |
|---|---|---|
| EA 1주차 | 긴급 버그픽스 | 부정 리뷰 방지 |
| EA 2~4주차 | 소규모 밸런스 패치 + QoL | "개발자가 살아있다" 신호 |
| 매 월말 | 콘텐츠 업데이트 (방 2~3개, 장비 10개) | 위시리스트 재활성화 |
| 분기별 | 큰 기능 (스테이지 2, 새 보스) | 미디어 픽업 기회 |

### Steam 커뮤니티 운영

1. **EA 시작 글**: "무엇이 완성됐고 무엇이 미완인지" 솔직하게 공개
2. **버그 리포트 스레드**: 고정 게시물로 유지, 빠른 응답 (24시간 내)
3. **업데이트 노트**: 패치마다 한국어·영어 동시 작성
4. **로드맵 공개**: 향후 3개월 계획을 투명하게 (달성 못해도 OK, 소통이 중요)

### 가격 전략

- **EA 가격**: 정식 가격 × 0.7~0.8 (20~30% 할인)
  - 예: 정식 출시 ₩12,000 → EA ₩8,400 ~ ₩9,600
- **정식 출시 시 가격 인상** 공지 → 조기 구매 인센티브
- 런칭 위크 추가 할인 (10~15%) → 위시리스트 전환율 극대화

---

## EA 중 수집해야 할 피드백 항목

### 1회차 플레이어 (가장 중요)
- "처음 10분 안에 뭘 해야 할지 알았나?"
- "어느 부분에서 막혔나?"
- "다시 하고 싶었나?"

### 피드백 수집 방법 (OnionCat 규모에 맞게)
1. Steam 리뷰 모니터링 (Daily)
2. Discord 서버 운영 (#버그신고, #아이디어)
3. 정기 플레이테스트 세션 (월 1회, 5~10명)

---

## 실패 패턴 (피해야 할 것)

| 실패 패턴 | 설명 | 방지책 |
|---|---|---|
| 너무 이른 EA | 핵심 루프도 없는 상태에서 유료 공개 | 위 체크리스트 충족 후 출시 |
| 침묵 개발 | EA 3개월 이상 업데이트 없음 | 소규모 패치라도 공지 |
| 피드백 무시 | 리뷰·포럼 응답 없음 | 첫 1주는 매일 확인 |
| 기능 크리프 | EA 피드백에 과잉 반응해 범위 무한 확장 | 코어 루프 기준으로 필터링 |
| 정식 출시 시점 애매 | "EA 2년째, 언제 나오나요?" | EA 기간 목표 (12~18개월) 공개 |

---

## OnionCat 구체적 EA 로드맵 초안 (예시)

```
EA 입장 조건:
  - 스테이지 1 (방 15+, 보스 1) 완성
  - 장비 60종 이상
  - 세이브/불러오기, 설정 메뉴 완성
  - 1~2인 로컬 협동 작동

EA Month 1: 긴급 수정 + 방 5개 추가
EA Month 2~3: 스테이지 2 (방 10개, 새 적 1종, 엘리트 보스)
EA Month 4~5: 장비 30종 추가 (전설 3개 포함), 세트 2개 추가
EA Month 6: 스테이지 3 + 최종 보스 + 정식 출시

정식 출시:
  - 스테이지 3, 방 30+, 장비 120종, 보스 3명
  - 한국어·영어 로컬라이제이션 완성
  - OST 완성
```

---

## 참고 링크

- Steam Early Access FAQ (Valve 공식): https://store.steampowered.com/earlyaccessfaq/
- 인디 EA 성공 사례 분석: https://howtomarketagame.com/
- Hades EA 사례 (Supergiant 개발자 GDC): https://www.youtube.com/watch?v=oLxfxnMCkCc
- Vampire Survivors EA 사례: https://store.steampowered.com/news/app/1794680/
- Dungeon Drafters EA 운영 사례: https://store.steampowered.com/news/app/1529640/
