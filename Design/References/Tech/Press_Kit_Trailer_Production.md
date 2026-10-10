# Press Kit & Trailer Production

리서치 날짜: 2026-10-10

## 개요

인디 게임 출시 전 **프레스 킷(Press Kit)**과 **트레일러**는 미디어 커버리지와 Steam 전환율에 직접 영향을 준다. 개발자가 직접 만들 수 있는 수준의 실용 가이드. OnionCat처럼 2인 협동 픽셀아트 로그라이크는 "두 플레이어가 함께하는 순간"을 시각적으로 잘 담는 것이 핵심.

## Press Kit 필수 구성

### 1. 기본 정보 시트 (fact sheet)
```
게임명: OnionCat (가제)
장르: 2인 협동 탑다운 픽셀아트 로그라이크
플랫폼: PC (Steam)
출시일: TBD
가격: TBD
개발사: [이름]
연락처: [이메일]
웹사이트/Steam 페이지: [URL]
플레이어 수: 2명 필수 (컨트롤러 + 키보드/마우스)
런 시간: 약 1시간
```

### 2. 게임 설명 (3종류 준비)
- **한 줄 설명 (50자 이하)**: "One body, two players — a cat carrying a flowerpot onion in a co-op dungeon brawl."
- **짧은 설명 (100~150 단어)**: 핵심 메커니즘 + 무엇이 독특한지 + 협동 감성
- **긴 설명 (400~600 단어)**: 전체 메커니즘, 성장 시스템, 분위기

### 3. 스크린샷 (최소 8~12장)
| 유형 | 내용 | 해상도 |
|------|------|--------|
| 전투 액션 | 고양이 할퀴기 + 양파 씨앗탄 동시 장면 | 1920×1080 |
| 킥 & CRASH | 걷어차기로 적이 벽에 충돌하는 순간 | 1920×1080 |
| 보스 전투 | 보스 HP바 보이는 상태로 전투 중 | 1920×1080 |
| 장비 선택 UI | 업그레이드 선택 화면 (둘이 동시 선택) | 1920×1080 |
| 장비 화면 | GearScreen에서 세트 구성 보이는 장면 | 1920×1080 |
| 협동 콤보 | "COMBO!" 텍스트 뜨는 순간 | 1920×1080 |
| 합동기 | ONION STORM 발동 장면 | 1920×1080 |
| 방 탐험 | 특징적인 방 레이아웃 + 두 플레이어 | 1920×1080 |

**Unity에서 고품질 스크린샷 캡처**:
```bash
# Unity pipeline CLI로 게임뷰 캡처
"$U" cmd capture_game_view --width 1920 --height 1080 \
  --save_path "Assets/Temp/screenshot.png" \
  --project-path "$P" --no-banner --result-only
```

### 4. 로고 & 아트
- 게임 로고 (PNG, 투명 배경) — 가로형 + 정사각형 2종
- 캡슐 이미지 (Steam용: 460×215, 616×353, 231×87)
- 헤더 이미지 (Steam 라이브러리용: 460×215)
- GIF 또는 짧은 클립 (트위터/SNS용, 15~30초)

### 5. presskit() 페이지
무료 온라인 프레스킷 생성 도구: https://dopresskit.com
- 구조화된 HTML 페이지 자동 생성
- 미디어가 원클릭으로 다운로드 가능하게 압축 제공
- Steam, itch.io, 공식 사이트에 링크 걸기

## 트레일러 제작 가이드

### 트레일러 종류
| 종류 | 길이 | 시점 | 목적 |
|------|------|------|------|
| Announcement Trailer | 30~60초 | 개발 초기 | 관심 유발, 미리 보기 |
| Gameplay Trailer | 60~90초 | 알파~베타 | 메커니즘 설명 |
| Launch Trailer | 60~90초 | 출시 직전 | 판매 전환 |

### 60초 Gameplay Trailer 구조
```
0:00 - 0:05 │ Hook — 가장 임팩트 있는 장면 (킥 → CRASH, 합동기 등)
0:05 - 0:15 │ "두 명이 한 몸을 공유" 콘셉트 설명 (자막 + 조작 장면)
0:15 - 0:35 │ 핵심 메커니즘 몽타주 (할퀴기, 씨앗탄, 킥, 식물, 실드)
0:35 - 0:50 │ 성장 시스템 (장비 선택 → 세트 발동 → 강해지는 캐릭터)
0:50 - 0:60 │ 보스 클라이맥스 + 타이틀 카드 + 출시 정보
```

### 트레일러 제작 팁 (도구 없이)
1. **OBS Studio로 녹화**: 무료, Unity 게임뷰 직접 캡처, 60fps
2. **DaVinci Resolve로 편집**: 무료, 색보정·자막 포함
3. **사운드 믹싱**: 게임 내 BGM + 효과음 그대로 사용 (저작권 이미 확보됨)
4. **자막**: TMP 폰트와 통일된 폰트로 텍스트 오버레이

### Unity에서 좋은 영상 장면 만들기
```csharp
// Debug 메뉴로 세팅 후 촬영
// 1. 적 제거 → 원하는 적만 배치
// 2. 무적 ON → 자연스럽게 시연
// 3. 씨앗 100 → 원하는 장비 즉시 구매
// 4. 세트 지급 → 시너지 장면 연출
```

## OnionCat 적용 포인트

### "두 플레이어가 동시에 움직이는" 장면이 핵심
OnionCat의 가장 독특한 포인트는 **한 화면에서 Cat과 Onion이 동시에 플레이되는** 장면. 트레일러 첫 5초 안에 이 장면이 와야 함.
- Cat가 이동하며 적 할퀴기 + 동시에 Onion 마우스 조준 씨앗탄 — 같은 몸에서 두 플레이어가 나오는 장면

### CRASH 장면은 반드시 포함
"적을 걷어차서 벽에 CRASH" 장면은 게임의 독창적 순간 중 하나. 이 장면이 없으면 다른 로그라이크와 차별화 불가.

### 스크린샷 미리 찍어두기 스케줄
출시 6개월 전부터 플레이 테스트 때마다 좋은 장면 스크린샷 저장 → 나중에 골라 쓰기.
`Guides/` 폴더에 촬영 체크리스트 만들어두면 편함.

### presskit() 주소 후보
- `[개발자사이트]/presskit` 또는 dopresskit.com 호스팅

## 참고 링크

- presskit() 무료 도구: https://dopresskit.com
- OBS Studio (무료 녹화): https://obsproject.com
- DaVinci Resolve (무료 편집): https://www.blackmagicdesign.com/products/davinciresolve
- Rami Ismail의 인디 마케팅 가이드: https://ltpf.ramiismail.com
- Steam 그래픽 에셋 가이드: https://partner.steamgames.com/doc/store/assets/standard
