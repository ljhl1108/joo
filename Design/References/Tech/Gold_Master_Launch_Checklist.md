# Gold Master & Launch Checklist

리서치 날짜: 2026-09-18

## 개요

**Gold Master**는 게임이 "출시 가능 상태"에 도달했음을 선언하는 단계다.
처음 게임을 완성하는 개발자(beginner)가 가장 자주 빠뜨리는 것들 위주로 정리.

OnionCat에서 중요한 이유:
- 기능 구현을 끝낸 뒤 "진짜로 게임이 돌아가는지" 전체 경로를 검증해야 함
- Steam 등록/제출에 필요한 최소 요건을 사전에 알아야 일정 관리가 된다
- 처음 게임을 만드는 개발자는 "완성"이 어디인지 모르는 경우가 많음 — 이 체크리스트가 기준점

---

## Unity 구현 방법

### 단계 1: 빌드 설정 정리

```
File > Build Settings > Player Settings
```

```
ProductName      = "OnionCat"
BundleVersion    = "1.0.0"
Company          = 개발자 이름
defaultIsFullScreen = false  (창 모드 기본 권장)
Target Platform  = Windows (64-bit 우선, 32-bit 선택)
```

**IL2CPP vs Mono**: Steam 출시는 IL2CPP 권장 (보안 + 성능).
단, 초기 프로토타입/테스트용은 Mono가 빌드 속도 빠름.

### 단계 2: Debug 코드 제거 검증

```csharp
// 빌드에서 제외할 디버그 코드 패턴
#if UNITY_EDITOR || DEVELOPMENT_BUILD
    DebugCheatSystem.Enable();
#endif
```

- `Debug.Log` 남발하면 성능 저하 → Release 빌드에서 `Debug.unityLogger.logEnabled = false`
- Debug 치트 메뉴 (`Debug_Cheat_System.md` 참고)는 `DEVELOPMENT_BUILD` 매크로로 격리

### 단계 3: 전체 게임 플로우 테스트

OnionCat의 검증 경로:
```
콜드 스타트(최초 실행)
→ 스플래시 화면
→ 메인 메뉴
→ 캐릭터 선택 or 바로 시작
→ 인트로 / 튜토리얼 방
→ 전투 룸 3개 이상
→ 업그레이드 선택
→ 보스 방
→ 게임오버 OR 클리어
→ 결과 화면
→ 재시작 → 메뉴 복귀 두 가지 모두 확인
```

코드로 정리하면:
```csharp
// QA 자동화 불가능한 부분 — 직접 눈으로 확인 체크리스트
// [ ] 게임 오버 시 결과 정상 표시
// [ ] 재시작 시 이전 런 데이터 완전 초기화
// [ ] ESC 언제든 일시정지, 재개 시 게임 상태 복원
// [ ] 설정 저장 후 재실행해도 유지
```

### 단계 4: 입력 장치 검증

```
키보드/마우스 전용 → 패드 전용 → 키보드+패드 혼합 → 패드 2개 동시 (로컬 코업)
```

- 패드 진동 OS 권한 확인 (Windows GameInput API)
- 패드 프롬프트 아이콘이 현재 입력 장치에 맞게 전환되는지

### 단계 5: 해상도 & 화면비 검증

```csharp
// 지원 해상도 리스트 (Settings 메뉴에서 선택 가능하게)
// 1920×1080 (16:9) — 기준
// 2560×1440 (16:9)
// 1280×720  (16:9)
// 2560×1080 (21:9) — Ultra-wide
// 3840×2160 (4K) — 선택사항
```

픽셀아트 게임은 **정수 배율**이 중요:
- 기준 해상도(예: 320×180)의 정수 배로만 렌더 → `Pixel Perfect Camera` 컴포넌트 활용

### 단계 6: 세이브/로드 엣지 케이스

```csharp
// 반드시 테스트할 시나리오
// [ ] 최초 실행 (세이브 파일 없음) → 기본값으로 정상 시작
// [ ] 런 중 강제 종료 후 재시작 → 메인 메뉴로 복귀 (런 중 데이터는 영구 저장 안 됨)
// [ ] 설정 파일 손상 시뮬레이션 → 예외처리 후 기본값 복구
// [ ] 업적/통계 데이터 누적 수십 회 → 오버플로우/버그 없음
```

---

## 출시 전 최종 체크리스트

### ✅ 빌드

- [ ] Release 빌드 완성 (IL2CPP + 최적화 설정)
- [ ] 실행 파일(.exe) 독립 실행 확인 (Unity Editor 없이)
- [ ] Steam Deck(Proton) 실행 확인 (`Steam_Deck_Compatibility.md` 참고)
- [ ] 크래시 리포터 연결 (Sentry, Backtrace, 또는 Unity 내장)
- [ ] 빌드 번호/버전 표시 (메인 메뉴 구석 또는 크레딧)

### ✅ Steam 등록

- [ ] App ID 발급 (Steamworks)
- [ ] SteamCMD or Steamworks SDK로 빌드 업로드
- [ ] 스토어 페이지: 제목, 설명(short/long), 장르/태그 입력
- [ ] 스크린샷 최소 5장 (1280×720 이상)
- [ ] 트레일러 영상 (선택사항이지만 강력 권장)
- [ ] 시스템 요건 작성 (최소/권장)
- [ ] 가격 설정
- [ ] Steam 업적 등록 (`Achievement_Stats_System.md` 참고)
- [ ] Steam 클라우드 세이브 설정 (선택)
- [ ] 컨트롤러 지원 구성 (Steam Input API)
- [ ] 출시 날짜 + 시간 설정 (UTC 기준 확인)

### ✅ 콘텐츠

- [ ] 플레이스홀더 아트 없음
- [ ] 크레딧 화면 완성 (개발자, 사용한 에셋/음악 출처 포함)
- [ ] 튜토리얼 방 신규 플레이어 관점으로 테스트
- [ ] 게임 내 모든 한국어/영어 텍스트 오탈자 검토
- [ ] 배경음악 + 효과음 볼륨 밸런스 최종 확인

### ✅ 법적 요건

- [ ] 사용 에셋 라이선스 확인 (무료 에셋의 상업 이용 허가 여부)
- [ ] 프리웨어 폰트 상업 라이선스 확인 (`Pixel_Font_TextMeshPro_System.md` 참고)
- [ ] 저작권 표기 (스플래시 or 크레딧)

### ✅ QA 최종 통과 기준

| 항목 | 기준 |
|---|---|
| P0 버그 (진행 불가, 크래시) | 0개 |
| P1 버그 (중요 기능 이상) | 0개 |
| P2 버그 (불편하지만 진행 가능) | 허용 (hotfix 예약) |
| 메모리 누수 | 1시간 플레이 후 메모리 증가 없음 |
| 프레임 드롭 | 목표 FPS(60) 유지율 95% 이상 |

---

## OnionCat 적용 포인트

### 초기부터 Gold Master 역순으로 설계

- **버전 표시 먼저 넣기**: 개발 초기에 메인 메뉴 구석에 `v0.1-dev` 등 표시 → 나중에 수정만 하면 됨
- **Debug 분리 먼저**: `UNITY_EDITOR` 매크로 습관화 → 출시 전 `ifdef` 빠뜨리는 사고 방지
- **씬 전환 전체 흐름 1회/스프린트**: 스프린트마다 첫 씬부터 마지막까지 한 번씩 직접 플레이

### 로컬 코업 특화 출시 체크

- 패드 2개 동시 연결 → 입력 페어링 화면 정상 작동 (`Controller_Pairing_System.md`)
- 패드 1개 + 키보드/마우스 혼합 모드도 지원되는지
- 한 명이 먼저 조인하고 나중에 다른 플레이어 합류 시 시나리오

### Steam Next Fest / 데모 버전 활용

처음 게임 제작자는 **Full 출시 전 Steam Next Fest(데모 행사) 참여**를 강력 권장:
- 데모 버전: 1~2층, 보스 1명 클리어까지
- 플레이어 피드백으로 조기 방향 수정 가능
- Wishlist 확보 → 출시 판매량에 직결

---

## 참고 링크

- [Unity 빌드 설정 공식 문서](https://docs.unity3d.com/Manual/PublishingBuilds.html)
- [Steamworks 출시 가이드](https://partner.steamgames.com/doc/store/releasing)
- [How to Ship a Game on Steam — GDC 2019](https://www.gdcvault.com/)
- [Steam Deck 인증 가이드](https://partner.steamgames.com/doc/steamdeck/compat)
- [Indie Dev 체크리스트 — Rami Ismail의 Release Checklist](https://raw.githubusercontent.com/tha_rami/gamedev-resources/master/index.md)
- [Game Launch Checklist — howtomarketagame.com](https://howtomarketagame.com)
