# Platform Submission & Certification Process (플랫폼 제출·심사 절차)

리서치 날짜: 2026-11-16

## 개요

게임 완성 후 Steam, Nintendo eShop 등 플랫폼에 출시하려면 각 플랫폼의 심사를 통과해야 함.
특히 첫 출시 개발자는 "언제 뭘 준비해야 하는지"를 모르는 경우가 많아 출시가 지연됨.
OnionCat 출시를 위한 최소 체크리스트와 절차를 정리.

---

## Unity 구현 방법 (빌드 세팅 중심)

### 1. PC (Steam) 빌드 준비

#### Unity Build Settings

```csharp
// PlayerSettings 주요 항목 (Inspector 또는 코드로 설정)
PlayerSettings.companyName = "YourStudio";
PlayerSettings.productName = "OnionCat";
PlayerSettings.bundleVersion = "1.0.0";

// 아이콘 설정
PlayerSettings.SetIconsForTargetGroup(BuildTargetGroup.Standalone, icons);

// 화면 설정
PlayerSettings.defaultScreenWidth = 1920;
PlayerSettings.defaultScreenHeight = 1080;
PlayerSettings.fullScreenMode = FullScreenMode.FullScreenWindow;
PlayerSettings.runInBackground = false; // 기본값 유지

// IL2CPP 추천 (Steam: 리버스 엔지니어링 방어)
PlayerSettings.SetScriptingBackend(BuildTargetGroup.Standalone, ScriptingImplementation.IL2CPP);
```

#### Build Script (자동화)

```csharp
// Editor/BuildScript.cs
public static class BuildScript
{
    [MenuItem("OnionCat/Build/Windows x64")]
    public static void BuildWindows()
    {
        var options = new BuildPlayerOptions
        {
            scenes = GetScenes(),
            locationPathName = "Builds/Windows/OnionCat.exe",
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.None
        };
        BuildPipeline.BuildPlayer(options);
    }

    static string[] GetScenes() =>
        EditorBuildSettings.scenes
            .Where(s => s.enabled)
            .Select(s => s.path)
            .ToArray();
}
```

#### 빌드 후 확인 체크리스트
```
[ ] 폴더명에 한글/특수문자 없음
[ ] .pdb 파일 포함 여부 결정 (디버깅 필요 시 포함, 배포는 제외)
[ ] 외부 DLL 라이선스 확인 (Steamworks.NET 등)
[ ] 첫 실행 시 화이트스크린 없는지 테스트
[ ] 한글 출력 테스트 (한국어 Windows 외 환경에서도 동작 확인)
```

---

## Steam 출시 절차

### 단계 1: Steamworks 계정 설정 ($100 USD)
- https://partner.steamgames.com/ 에서 개인/법인 등록
- 한국 개발자: 사업자등록증 OR 개인 (주민등록번호 기반)
- 세금 처리: W-8BEN (미국 세금 조약국 — 한국 포함 → 30% → 10% 세율)
- AppID 발급까지 24~48시간

### 단계 2: 상점 페이지 준비 (출시 90일 전 목표)
필수 에셋:
```
- 캡슐 이미지: 460×215px, 231×87px, 616×353px (각각 필요)
- 헤더 이미지: 460×215px
- 스크린샷: 최소 5장 (1920×1080 권장)
- 트레일러: 선택 사항이나 위시리스트에 큰 영향
- 설명: HTML 가능 (Steam 마크업)
- 짧은 설명: 최대 300자
- 태그: 최대 20개 (Roguelite, Co-op, Pixel Art, Action 등)
```

### 단계 3: 연령 심사
- IARC 심사 (무료, 온라인 설문): Steam에서 자동 연동
- 한국 GRAC 별도 심사 필요: https://www.grac.or.kr/ (약 2~3주 소요)
  - 한국 스토어에 출시하려면 필수
  - 비용: 소규모 개발사 할인 적용 가능

### 단계 4: 빌드 업로드

```bash
# SteamCMD 설치 후
steamcmd +login <계정> +run_app_build <앱빌드.vdf> +quit

# .vdf 예시
"AppBuild"
{
    "AppID" "XXXXXXX"
    "Desc" "v1.0.0 Release Build"
    "BuildOutput" "output/"
    "Depots"
    {
        "XXXXXXX1"
        {
            "FileMapping"
            {
                "LocalPath" "Builds/Windows/*"
                "DepotPath" "."
                "recursive" "1"
            }
        }
    }
}
```

### 단계 5: 심사 및 출시

- 빌드 제출 후 Steam 검토 팀 심사: **3~5 영업일** 소요
- 심사 통과 → "Release" 버튼 활성화
- 출시일 예약 가능 (Steam 출시 날짜 설정)
- **주의**: Steam Next Fest, 다른 대형 출시일 피하기 → 가시성 확보

---

## Nintendo Switch 준비 사항 (참고용)

> OnionCat은 PC 우선이지만 추후를 위해 정리

- Nintendo Developer Portal 신청 (승인제, 한국 법인 or 개인사업자 필요)
- Unity용 Nintendo Switch 플랫폼 모듈 별도 설치 (승인 후 다운로드)
- 하드웨어 테스트 (실기기 필수)
- 심사: **약 2~3주**
- 가격 차이: USD 기준 → Nindies Direct 출시 타이밍 중요

---

## 출시 전 최종 체크리스트

### 기능
```
[ ] 첫 실행 튜토리얼 또는 가이드 존재
[ ] 설정 메뉴 (볼륨, 전체화면, 해상도)
[ ] 종료 확인 다이얼로그
[ ] 크래시 후 세이브 데이터 보호 (Save_Load_System.md 참고)
[ ] Steam 업적 최소 1개 이상 (Steam에서 권장)
[ ] 로컬 멀티플레이어 명확히 설명 (상점 페이지에 "Local Co-op" 태그)
```

### 법적
```
[ ] 서드파티 라이선스 화면 (Fonts: Galmuri SIL OFL, 음악: CC0 출처)
[ ] 개인정보처리방침 (로컬 세이브만 하면 불필요, 온라인 기능 있으면 필수)
[ ] 에셋스토어 구매 에셋 라이선스 확인 (배포 가능 여부)
```

### 한국 출시 특이사항
```
[ ] GRAC 등급 취득 (12세 or 15세 예상 — 폭력성 경미, 공포 없음)
[ ] 게임 내 결제 없으면 심사 간단 (OnionCat은 단일 판매 예정)
[ ] 한글 지원 — 이미 Galmuri 폰트로 구현됨
```

---

## 출시 타이밍 전략

| 시기 | 행동 |
|------|------|
| 출시 90일 전 | Steam 상점 페이지 공개 → 위시리스트 모으기 시작 |
| 출시 60일 전 | GRAC 심사 신청 |
| 출시 30일 전 | Steam에 빌드 제출 (여유분 확보) |
| 출시 2주 전 | 미디어 배포용 Steam key 발급 (인디 게임 미디어, 유튜버) |
| 출시일 | 한국 오전 10시 (Steam 기본: 태평양 시간 10시 = 한국 익일 02시) |

---

## OnionCat 적용 포인트

- 현재 Steamworks.NET 통합 여부 확인 필요 → 초기 단계에서 연결해두면 나중에 편함
- **Galmuri 폰트 SIL OFL 라이선스** → 배포 가능, 크레딧 화면에 표기 필요
- **CC0 오디오** → LICENSE_AUDIO.txt 그대로 크레딧에 넣으면 됨
- AppID는 무료 발급 후 개발 중 테스트 가능 → 조기 등록 권장

---

## 참고 링크

- Steamworks 공식: https://partner.steamgames.com/
- Steam 상점 에셋 가이드: https://partner.steamgames.com/doc/store/assets
- GRAC 등급 신청: https://www.grac.or.kr/Business/ApplyDefGuide.aspx
- SteamCMD 빌드 업로드: https://partner.steamgames.com/doc/sdk/uploading
- 인디 개발자 출시 가이드: https://www.gamedeveloper.com/business/how-to-launch-your-indie-game-on-steam
- Unity IL2CPP 빌드: https://docs.unity3d.com/Manual/IL2CPP.html
