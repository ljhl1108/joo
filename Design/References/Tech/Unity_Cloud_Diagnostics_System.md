# Unity Cloud Diagnostics — 충돌/오류 분석 시스템

리서치 날짜: 2026-11-21

## 개요

**Unity Cloud Diagnostics**는 Unity Gaming Services(UGS)에 포함된 충돌·예외 보고 서비스다. 플레이어의 게임이 크래시하거나 처리되지 않은 예외가 발생할 때 자동으로 스택 트레이스와 기기 정보를 클라우드에 보내준다.

OnionCat처럼 첫 게임을 출시하는 개발자에게는 "내가 테스트를 못 한 환경에서 뭐가 터지나"를 파악하는 가장 현실적인 방법이다. 플레이어는 버그를 보고하지 않고 그냥 게임을 꺼버리기 때문이다.

---

## Unity 구현 방법

### 1. 패키지 설치 및 연결

```
Package Manager → Unity Registry → "Cloud Diagnostics" 검색 → Install
Edit → Project Settings → Services → Cloud Diagnostics → Enable
```

또는 `Packages/manifest.json`에 직접:
```json
"com.unity.services.clouddiagnostics": "1.0.6"
```

### 2. 자동 수집 (코드 없이)

활성화만 하면 다음을 자동 수집:
- C# 처리되지 않은 예외 (Exception)
- Unity 엔진 크래시 (native crash)
- 로그 레벨 Error·Fatal 메시지
- 기기 정보 (OS, GPU, RAM, Unity 버전)

### 3. 커스텀 메타데이터 추가 (선택)

```csharp
using Unity.Services.CloudDiagnostics;

// 초기화 시 세션 정보 첨부
CrashReportHandler.SetUserIdentifier("anonymous_id");

// 충돌 맥락을 위한 커스텀 키-값
CrashReportHandler.SetCustomKey("chapter", MetaProgress.Chapter.ToString());
CrashReportHandler.SetCustomKey("current_room", DungeonManager.currentRoomId);
CrashReportHandler.SetCustomKey("run_time_sec", runTimer.ToString());
```

### 4. 대시보드 확인

https://cloud.unity.com → 프로젝트 선택 → Cloud Diagnostics

- **Crash Groups**: 같은 스택 트레이스끼리 묶어 빈도 순으로 정렬
- **Exception Groups**: NullReferenceException 등 예외 종류별
- **Occurrences**: 발생 시각, 기기별 분포
- **Symbol 업로드**: IL2CPP 빌드는 `.sym` 파일 업로드해야 스택 트레이스가 읽힘

### 5. 티어 및 비용

| 플랜 | 한도 |
|---|---|
| Unity Personal (무료) | 하루 25건 (테스트·소규모 출시에 충분) |
| Unity Pro | 무제한 기본 (월정액 플랜에 포함) |
| Cloud Diagnostics Advanced (Backtrace) | 월 100만 건 + 커스텀 필터링 |

첫 출시엔 Personal 무료 티어로 충분. 오픈 베타에서 버그가 쏟아지면 Pro 고려.

### 6. User Reporting — 플레이어 직접 버그 제보

```csharp
using Unity.Services.UserReporting;

// 플레이어가 버그 신고 버튼을 누르면
UserReportingService.Instance.CreateUserReport(
    summary: "적이 사라지지 않아요",
    description: inputField.text,
    screenshotPixels: screenshotTexture
);
```

- 대시보드에서 스크린샷 + 설명 + 로그가 한꺼번에 보임
- Early Access 기간에 디스코드보다 체계적인 버그 수집 가능

---

## OnionCat 적용 포인트

### 1. 출시 전 베타 테스트 단계

- Steam Next Fest / 클로즈 베타 → 플레이어가 100명 이상이면 충돌 패턴이 무작위로 나옴
- **커스텀 키로 장비 조합 로깅**: `CrashReportHandler.SetCustomKey("cat_gear", string.Join(",", RunData.catGear))` → 특정 장비 조합에서만 터지는 버그 추적

### 2. OnionCat에서 가장 취약한 지점

다음 코드 경로에 `try/catch` + 로그를 추가해두면 대시보드에서 바로 보임:

```csharp
// PaintedRoomImporter.Apply — 방 가져오기 실패
// RewardTable.RollFor — 보상 풀이 비어있을 때 NullRef
// GameManager.ChangeState — 잘못된 상태 전환
// PoolManager.Spawn — 존재하지 않는 프리팹 ID
```

### 3. 맥락 없는 스택 트레이스 대응

IL2CPP 빌드(`Release` 설정)에서는 함수명이 숫자로 압축됨.
→ 빌드 후 `Build/[플랫폼]_BackUpThisFolder_ButDontShipItWithYourGame` 안의 `.sym` 파일을
  대시보드 → Symbol 업로드에 올려야 사람이 읽을 수 있는 스택 트레이스가 됨

### 4. 경량 대안 — `Application.logMessageReceived`

서비스 없이 직접 하려면:

```csharp
void OnEnable()
{
    Application.logMessageReceived += HandleLog;
}

void HandleLog(string msg, string stack, LogType type)
{
    if (type == LogType.Exception || type == LogType.Error)
    {
        // 로컬 파일에 쓰거나 간단한 HTTP POST
        File.AppendAllText(logPath, $"[{DateTime.Now}] {msg}\n{stack}\n");
    }
}
```

오프라인 환경용 백업. 클라우드 서비스와 병행 사용 권장.

### 5. 적용 순서 (권장)

1. `com.unity.services.clouddiagnostics` 패키지 추가
2. Services 창에서 Cloud Diagnostics 활성화
3. 주요 맥락 커스텀 키 5~6개 세팅 (챕터, 방 ID, 런 시간, 장비 슬롯)
4. Release 빌드 후 `.sym` 업로드
5. 테스트 기기에서 의도적으로 `throw new Exception("test")` 호출 → 대시보드 확인
6. Personal 티어(25건/일) → 베타 출시 후 Pro 전환

---

## 참고 링크

- [Unity Cloud Diagnostics 공식](https://unity.com/products/cloud-diagnostics)
- [Unity Docs: Crash and Exception Reporting](https://docs.unity.com/cloud-diagnostics/en/manual/CrashandExceptionReporting/AboutCrashandExceptionReporting)
- [Unity Cloud Diagnostics 설정 가이드](https://docs.unity.com/cloud-diagnostics/crash-and-exception-reporting/setting-up-crash-and-exception-reporting)
- [Unity Backtrace (고급 플랜)](https://unity.com/products/backtrace)
