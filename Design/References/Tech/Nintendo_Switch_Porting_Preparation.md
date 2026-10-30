# Nintendo Switch 포팅 준비

리서치 날짜: 2026-10-30

## 개요

Unity로 만든 2D 인디 게임을 Nintendo Switch에 출시하는 전 과정.  
OnionCat은 로컬 2인 협동 게임이라 Switch **매우 적합** (분리형 JoyCon = 각자 1개씩).  
주요 단계: Nintendo 개발자 등록 → SDK 취득 → 빌드 최적화 → LotCheck 인증.

---

## Unity 구현 방법

### 사전 요건

1. **Nintendo 개발자 등록**: https://developer.nintendo.com (심사 있음, 수주~수개월 소요)
2. **Switch SDK 취득**: 등록 후 포탈에서 Nintendo Switch SDK 다운로드
3. **Unity 스위치 빌드 모듈**: Unity Hub에서 Nintendo Switch 빌드 지원 설치 (라이선스 필요)
4. **Dev Kit(개발기)**: HW 테스트용 Switch 개발 키트 구매 (공식 경로만, 약 500달러)

### 해상도·프레임 설정

```csharp
// Switch는 두 가지 모드
// - 독 모드(TV): 1080p 60fps 목표
// - 휴대 모드: 720p 60fps 목표 (실제로 더 작은 화면이라 허용)

// Unity Project Settings > Player > Resolution
// Switch는 16:9 고정. OnionCat은 1920x1080 고정 Canvas니까 그대로 OK

// 성능 목표
// CPU: Cortex-A57 1020MHz (모바일 수준) — Update() 최적화 필수
// RAM: 4GB 중 게임 할당 ~3GB
// 저장 공간: 게임 카드 최소 1GB, 권장 파일 크기 2GB 이하 (비용 절감)
```

### 컨트롤러 매핑

```csharp
// Switch에서 JoyCon 분리 시 자동 2플레이어 모드 지원
// New Input System 사용 중 → Switch 전용 레이아웃 추가 필요

// Switch JoyCon 가로 모드 버튼 이름 (SDL2 기준)
// JoyCon L: 조이스틱(위치 제어), SR, SL, -버튼, 십자키, ZL
// JoyCon R: 조이스틱(위치 제어), SR, SL, +버튼, A/B/X/Y, ZR

// OnionCat Cat Player (JoyCon L 가로):
// 이동: 조이스틱
// 할퀴기: SR (오른쪽 어깨)
// 대쉬: ZL
// 던지기: -버튼

// CoopInputLayout이 자동 전환하므로
// InputActionAsset에 "SwitchJoyConL" 컨트롤 스킴 추가하면 됨
```

### 저장 데이터 처리

```csharp
// Switch는 내부 저장소 전용 (외부 SD카드에 세이브 불가)
// 경로: Application.persistentDataPath (Switch에서도 동일하게 동작)

// Nintendo 요구사항: 저장 전 "저장 중..." UI 표시 의무
// 백그라운드 자동 저장 시 반드시 아이콘 표시
void SaveGame()
{
    ShowSavingIcon(true);
    SaveData.Write(savePath, data);
    ShowSavingIcon(false);
}

// 저장 공간 용량 선언 필수 (nmeta 파일에)
// 부족 시 사용자에게 안내 UI 제공 의무
```

### 성능 최적화 포인트

```csharp
// 1. Object.FindObjectsByType 금지 (이미 OnionCat 규칙)
// 2. 가비지 컬렉션 최소화
//    - PoolManager 사용 (이미 적용됨 ✓)
//    - string 연산 StringBuilder로

// 3. 2D Physics: Collision Matrix 최적화 (이미 레이어 정의됨 ✓)
// 4. 오디오: 동시 재생 채널 수 제한 (Switch는 최대 24채널)
// 5. 텍스처 압축: Switch 전용 포맷 ASTC 4x4 사용
//    (Project Settings > Player > Switch > Texture Compression)

// 6. IL2CPP 빌드 필수 (Mono 미지원)
//    Build Settings > Scripting Backend > IL2CPP
```

### LotCheck (닌텐도 인증) 주요 항목

| 항목 | 내용 |
|------|------|
| 기능 테스트 | 시작~클리어 전체 플레이 오류 없음 |
| 저장 안전성 | 저장 중 전원 차단 시 복구 가능 |
| 입력 대응 | JoyCon 분리·연결 핫플러그 |
| 에러 처리 | 저장 공간 부족, 오류 코드 표시 |
| IARC 등급 | 연령 등급 취득 (한국: 게임물관리위원회) |
| 화면 비율 | 모든 16:9 해상도 정상 동작 |
| 슬립 복귀 | 슬립 진입/복귀 시 크래시 없음 |
| 로딩 시간 | 최초 부팅 후 메인메뉴까지 60초 이내 |

---

## OnionCat 적용 포인트

### 왜 Switch가 OnionCat에 최적인가
1. **JoyCon 분리 = 2플레이어 즉시 가능**: 하드웨어가 "1인 1컨트롤러"를 기본으로 지원
2. **로컬 협동 수요**: Switch는 로컬 멀티플레이 플레이어층이 두꺼움
3. **픽셀아트**: Switch 화면 크기에서 픽셀아트 선명함 높음 (PPU 32 → 1080p에서 충분)
4. **이동 플레이**: 통근·여행 중 2인 플레이 수요 존재

### 준비해야 할 작업 목록

```
[ ] Nintendo 개발자 등록 신청 (가장 먼저, 심사 오래 걸림)
[ ] CoopInputLayout에 JoyCon 가로 모드 컨트롤 스킴 추가
[ ] IL2CPP 빌드 확인 (Reflection 사용 부분 점검 — eval 코드 제거)
[ ] 텍스처 압축 ASTC 전환 테스트
[ ] 저장 공간 선언 (nmeta 파일 작성)
[ ] 저장 중 UI 표시 구현 확인
[ ] 슬립/복귀 테스트 자동화
[ ] IARC 등급 신청 (무료, 온라인으로 10분)
[ ] Dev Kit에서 실기 테스트
[ ] LotCheck 제출
```

### Reflection 사용 주의
```csharp
// eval 코드나 런타임 리플렉션은 IL2CPP에서 AOT 문제 발생 가능
// OnionCat의 typeof(PlayerHealth).GetProperty("CurrentHealth")
// → 게임 코드에는 없고 개발자 디버그용만이라면 OK (빌드에서 제외)
// 의심스러우면: Project Settings > Player > AOT Compilation Options에 추가
```

### 예산 고려
| 항목 | 예상 비용 |
|------|-----------|
| Nintendo 개발자 등록 | 무료 |
| Dev Kit | ~$500 |
| Switch 퍼블리싱 | 자체 퍼블리싱 가능 (Nintendo eShop Direct) |
| 게임 카드 인쇄 (옵션) | 최소 발주 수량 있음, 수천 달러 |
| Unity Switch 빌드 지원 | 추가 라이선스 없음 (Personal/Pro 포함) |

---

## 참고 링크

- Nintendo 개발자 포털: https://developer.nintendo.com
- Unity Switch 포팅 가이드: https://docs.unity3d.com/Manual/Nintendo_Switch.html
- "How to port your Unity game to Nintendo Switch" (토마스 브루사 / GDC): https://gdconf.com
- IARC 연령등급 신청: https://www.globalratings.com
- 인디 Switch 포팅 경험담 (Devlog 모음): https://www.gamedeveloper.com 검색 "indie switch port"
- r/NintendoSwitch 개발자 AMA 아카이브
