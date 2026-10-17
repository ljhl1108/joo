# Localization Workflow for Solo Dev (1인 개발 로컬라이제이션 워크플로)

리서치 날짜: 2026-10-17

## 개요

기술적 로컬라이제이션 시스템 구축법(CSV 파싱, Unity Localization 패키지 등)은 `Localization_System.md`에 정리되어 있다. 이 문서는 그것과 다른 관점인 **"혼자 개발하는 사람이 실제로 어떤 순서로 작업하고, 어떻게 커뮤니티 번역을 활용하며, 어떤 함정을 피해야 하는가"**에 집중한다.

OnionCat에서 왜 중요한가:
- 현재 UI 문구가 한글로 완성되어 있음 (Galmuri11 폰트)
- 해외 출시를 위한 영어 지원 시 체계 없이 진행하면 나중에 대규모 리팩토링 필요
- 지금부터 "로컬라이제이션 준비된 구조"로 코드를 짜는 것이 핵심

---

## 로컬라이제이션 준비 체크리스트

### Phase 1: 코드 준비 (출시 전 필수)

```
[ ] 모든 UI 문자열이 코드 안에 하드코딩되지 않음
[ ] TextMeshProUGUI.text = "공격!" 같은 코드 → Localization Key로 교체
[ ] 숫자 포맷, 날짜 포맷에 CultureInfo 사용
[ ] 우에서 좌로 읽는 언어(아랍어) 대비 UI 레이아웃 고려 (미래)
[ ] 텍스트 길이 여유: 영어 → 독어는 평균 30% 길어짐, 레이아웃 여유 확보
```

### Phase 2: 문자열 추출 (실제 작업)

```
[ ] 모든 UI 텍스트를 스프레드시트(구글 시트)로 추출
[ ] Key 규칙 정의: ui.menu.start_run, item.gear.basic_claws.name 등
[ ] 한글 원문 입력 (Source Language)
[ ] 영어 번역 1차 (DeepL 또는 ChatGPT 초벌 + 수동 검수)
[ ] 게임 전문 용어 용어집(Glossary) 생성
```

### Phase 3: 통합 및 검증

```
[ ] CSV/JSON으로 내보내 Unity Localization 테이블에 적용
[ ] 영어로 전환 후 전체 화면 스크린샷으로 레이아웃 이상 확인
[ ] 특수 문자, 줄바꿈 처리 확인
[ ] 장비 이름/설명 등 동적 텍스트의 문자열 포맷 확인
```

---

## Unity 구현 방법

### A. 구글 시트 기반 워크플로 (1인 개발 추천)

```
구조:
구글 시트 → CSV 다운로드 → Unity Localization 패키지 테이블 Import

구글 시트 열 구성:
| Key | Comment | ko | en | ja (미래) |
|-----|---------|----|----|-----------|
| ui.menu.start_run | 메인 메뉴 버튼 | 런 시작 | Start Run | |
| item.gear.basic_claws.name | 기본 장비 이름 | 기본 발톱 | Basic Claws | |
| combat.combo_text | 콤보 UI 텍스트 | 콤보! | COMBO! | |

장점: 구글 시트는 공유/협업이 쉬움 → 커뮤니티 번역자 초대 가능
```

### B. Unity Localization 패키지 핵심 코드

```csharp
// 패키지: com.unity.localization
// Package Manager에서 설치

// 런타임에서 문자열 가져오기
using UnityEngine.Localization;
using UnityEngine.Localization.Settings;

// 1. 비동기 방식 (추천)
public async void LoadLocalizedString(string tableKey, string entryKey, 
    System.Action<string> callback)
{
    var op = LocalizationSettings.StringDatabase
        .GetLocalizedStringAsync(tableKey, entryKey);
    await op.Task;
    callback?.Invoke(op.Result);
}

// 2. Component 방식 (간단한 정적 텍스트)
// TextMeshProUGUI에 LocalizeStringEvent 컴포넌트 추가
// → Inspector에서 Table과 Key만 지정하면 자동 업데이트

// 3. 포맷 문자열 (동적 값 포함)
// 시트에: "{0}의 체력이 {1}% 회복됩니다" / "Restores {0} HP by {1}%"
var op = LocalizationSettings.StringDatabase
    .GetLocalizedStringAsync("UI", "heal.effect.desc", new object[] { "사과", 30 });
```

### C. 장비/스킬 설명 텍스트 (ScriptableObject 연동)

```csharp
// GearItem.cs 예시
[CreateAssetMenu(fileName = "GearItem", menuName = "OnionCat/GearItem")]
public class GearItem : ScriptableObject
{
    // 현재: [SerializeField] string itemName, description;
    // 변경 후:
    [SerializeField] LocalizedString localizedName;
    [SerializeField] LocalizedString localizedDescription;
    
    public string GetLocalizedName() => localizedName.GetLocalizedString();
    public string GetLocalizedDesc() => localizedDescription.GetLocalizedString();
}
```

---

## 1인 개발자를 위한 실전 조언

### 1. 처음부터 Key 체계를 잡아라
```
나쁜 예: "text_001", "button_1", "msg_attack"
좋은 예: "ui.hud.health_label", "item.gear.{id}.name", "combat.status.burn.name"

Key 명명 규칙:
{카테고리}.{서브카테고리}.{고유명}

카테고리 예:
- ui.menu.* : 메인 메뉴
- ui.hud.* : 인게임 HUD
- ui.gear.* : 장비 화면
- item.gear.{id}.* : 장비 이름/설명
- item.passive.{id}.* : 패시브 이름/설명
- item.skill.{id}.* : 스킬 이름/설명
- enemy.{id}.* : 적 이름
- combat.* : 전투 관련 텍스트
- meta.* : 메타 정보 (버전, 크레딧 등)
```

### 2. "일단 한글 하드코딩" 함정 피하기
```
// 지금 이렇게 짜고 있다면:
hpLabel.text = "체력: " + hp;

// 나중에 영어 추가할 때 이걸 찾아서 다 바꿔야 함
// 지금 당장은:
hpLabel.text = L("ui.hud.health_label") + ": " + hp;
// 또는 string.Format(L("ui.hud.health_format"), hp);

// L() 헬퍼: 로컬라이제이션이 준비되기 전까지는 그냥 원본 반환
string L(string key) => key; // 임시
// 나중에: string L(string key) => LocalizationManager.Get(key);
```

### 3. 번역 우선순위 (첫 출시 기준)

```
필수 (First Priority):
- 메인 메뉴, 설정, 일시정지
- 장비 이름 + 1줄 설명
- 전투 텍스트 (COMBO, CRASH, BLOCK 등)
- 게임오버/클리어 화면

2순위:
- 장비 상세 설명
- 스킬 설명
- 적 이름

3순위 (나중에):
- 스토리/NPC 대화
- 도움말/튜토리얼 텍스트
- 크레딧
```

### 4. 커뮤니티 번역 활용

```
방법 1: 구글 시트 공유
- 시트에 '편집 권한'을 특정 Discord 커뮤니티 멤버에게 부여
- "일어 번역 담당자 구합니다" 공고 → 시트에서 직접 번역
- 검수 후 CSV 다운로드 → Unity 임포트

방법 2: Crowdin / Weblate (오픈소스)
- 별도 플랫폼 운영 필요하지만 커뮤니티 기여 관리가 체계적
- 작은 인디 게임에는 구글 시트가 더 간단

주의:
- 번역자 이름을 크레딧에 포함할 것
- 게임 전문 용어집(Glossary)을 먼저 제공해야 일관성 유지
- "COMBO!"처럼 의도적으로 영어로 남기는 텍스트를 명확히 표시
```

### 5. 텍스트 길이 대비 UI 설계

```
언어별 평균 텍스트 길이 (한국어 기준):
- 영어: 1.2배 (한국어가 정보 밀도 높음)
- 일어: 0.8배 (한자 압축)
- 독어: 1.6배 (합성어가 매우 길어짐)
- 중국어 (간체): 0.7배

OnionCat UI 대비 방법:
1. 툴팁 텍스트는 자동 크기 조정 (TMP Auto Size)
2. 버튼 텍스트는 최소 영어 기준 2배 너비 여유 확보
3. 장비 설명은 스크롤 가능하게 설계 (이미 툴팁으로 구현됨)
```

---

## OnionCat 적용 포인트

### 지금 당장 할 일 (코드 리팩토링 없이)

1. `ContentBuilder.cs`의 장비 이름/설명을 구글 시트로 복사
2. 시트에 `en` 열 추가 → DeepL로 초벌 번역
3. Key 체계 문서 한 장 작성 (위 규칙 참고)

### 중기 작업 (영어 지원 추가 시)

1. Unity Localization 패키지 설치
2. `ContentBuilder.cs`가 `LocalizedString`을 ScriptableObject에 연결하도록 수정
3. `GearItem.localizedName/localizedDescription`으로 전환
4. 하드코딩된 전투 텍스트("COMBO!", "CRASH", "BLOCK")를 Localization 테이블로 이동

### 확인 방법

```bash
# Unity에서 언어 전환 테스트
# 메뉴 Window > Asset Management > Localization Scene Controls
# 여기서 Active Locale을 바꾸면 에디터에서 즉시 미리보기 가능
```

---

## 참고 링크

- [Unity Localization Package 공식 문서](https://docs.unity3d.com/Packages/com.unity.localization@latest)
- [Unity Localization 시작 튜토리얼 (YouTube)](https://www.youtube.com/results?search_query=unity+localization+package+tutorial)
- [Crowdin - Game Localization Platform](https://crowdin.com/)
- [IndieDev Localization Guide - Thomas Henshell](https://www.gamedeveloper.com/design/indie-game-localization-a-practical-guide)
- [Google Sheets CSV to Unity Localization](https://github.com/Unity-Technologies/com.unity.localization/blob/main/Editor/Import%20Export/)

