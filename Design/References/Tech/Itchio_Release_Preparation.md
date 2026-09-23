# Itch.io Release Preparation

리서치 날짜: 2026-09-23

## 개요

itch.io는 인디 개발자에게 가장 친화적인 배포 플랫폼으로, 계정 생성부터 게임 페이지 공개까지 24시간 이내에 할 수 있다. 처음 게임을 배포하는 개발자에게 Steam보다 진입 장벽이 낮고, 무료다.

OnionCat의 첫 공개(프로토타입 또는 데모)를 itch.io에 올리는 실전 절차를 다룬다.

---

## Unity 구현 방법 (빌드 준비)

### 1. Unity 빌드 설정

```
File → Build Settings → Platform: Windows (또는 WebGL)
```

**권장 빌드 타겟 우선순위:**
1. **WebGL** — 브라우저에서 바로 플레이 가능. 피드백 가장 빨리 받을 수 있음
2. **Windows (64bit)** — PC 사용자용 다운로드 버전
3. **Mac/Linux** — 나중에 추가

**WebGL 주의사항:**
- Player Settings → WebGL → Compression Format: **Gzip** (itch.io 권장)
- Memory: 256MB 이상 권장 (기본 32MB는 너무 작음)
- 2D 픽셀 게임이므로 WebGL 빌드 크기 50MB 이하 목표

### 2. 필수 Player Settings 체크리스트

```
Edit → Project Settings → Player

[공통]
- Company Name: 본인 이름 또는 팀명 (나중에 변경 불가 아님)
- Product Name: "OnionCat" (게임 이름)
- Version: "0.1.0" (또는 "Demo 1.0")
- Default Icon: 게임 아이콘 이미지 (512×512 PNG)

[Windows]
- Fullscreen Mode: Windowed (첫 배포 시 창모드가 오류 적음)
- Default Screen Width/Height: 1280×720

[WebGL]
- Template: Default 또는 Minimal
- Enable Exceptions: Explicitly Thrown Exceptions Only (성능)
```

### 3. 빌드 후 패키징

**Windows 빌드:**
```bash
# 빌드 폴더 통째로 zip
OnionCat_v0.1.0_Win64.zip
  └── OnionCat.exe
  └── OnionCat_Data/
  └── UnityCrashHandler64.exe
  └── UnityPlayer.dll
```

**WebGL 빌드:**
```bash
# itch.io에 zip 통째로 업로드 (압축 해제 불필요 — itch가 처리)
OnionCat_WebGL.zip
  └── Build/
  └── StreamingAssets/
  └── index.html
  └── TemplateData/
```

---

## itch.io 페이지 설정

### 1. 계정 생성 및 게임 등록

1. itch.io 가입 → **Dashboard → Create new project**
2. 기본 정보:
   - **Title**: OnionCat
   - **Project URL**: `ljhl1108.itch.io/onioncat` (소문자, 하이픈만)
   - **Kind of project**: HTML (WebGL) 또는 Downloadable
   - **Genre**: Action, Roguelike
   - **Tags**: `roguelike`, `local-co-op`, `2d`, `pixel-art`, `top-down`, `co-op`, `unity`

### 2. 업로드 설정

**WebGL 업로드:**
- 파일 업로드 후 **"This file will be played in the browser"** 체크
- `index.html`이 있는 경로를 루트로 인식 (zip 내에 폴더 없이 바로 index.html 권장)

**Windows 업로드:**
- 파일 업로드 후 **"Windows"** 플랫폼 선택
- itch.io App 사용자는 자동 설치/업데이트 지원

### 3. 설명 문구 (영문 추천 — 더 넓은 접근성)

```
OnionCat is a local 2-player co-op roguelite where both players share ONE body.

Player 1 controls a cat that slashes, dodges, and runs.  
Player 2 controls a crop on the cat's back — aiming, shooting, and blocking.

Some enemies can only be defeated by melee. Others only by ranged.
You MUST cooperate to survive.

Controls:
- Cat (P1): WASD to move | Space to dash | F to slash
- Crop (P2): Mouse to aim | LMB to shoot | RMB to shield

[Currently: Prototype / Demo v0.1]
```

### 4. 스크린샷/GIF 준비

itch.io 페이지 품질을 올리는 데 스크린샷이 가장 중요:
- **최소 3장**: 전투 장면, 업그레이드 선택 화면, 보스 장면
- **GIF 1개**: 핵심 협동 순간 (Cat이 달리면서 Crop이 조준하는 장면)
- 권장 해상도: **1280×720** 또는 **640×360** (픽셀아트라면 정수배)
- 캡처 도구: Unity의 `capture_game_view`, 또는 OBS → ScreenToGif

### 5. 가격 설정

처음 데모/프로토타입 공개 시:
- **Free** 선택 + "This project is free but you can leave a donation"
- 도네이션 제안: $0 (기본) → $3 ~ $5 이상 (선택)
- 나중에 정식 버전은 $5~10 설정 후 얼리 억세스 가능

---

## 공개 전 최종 체크리스트

```
[ ] 빌드에서 Debug.Log 출력 없음 (Development Build 체크 해제)
[ ] 타이틀 화면에서 게임이 시작됨
[ ] ESC 또는 Start 버튼으로 게임 종료 가능 (WebGL은 브라우저 탭으로 종료)
[ ] 해상도 1280×720에서 UI가 잘림 없음
[ ] 로컬 코옵: 키보드(Cat) + 마우스(Crop) 동시 입력 확인
[ ] FPS: WebGL에서 30fps 이상
[ ] 크래시 없이 한 런을 완주할 수 있음
[ ] itch.io 페이지: 설명 문구, 스크린샷, 태그 완비
[ ] 가시성 설정: "Restricted" (링크 아는 사람만) → 소규모 테스트 후 "Public"
```

---

## 첫 배포 후 피드백 수집

```
1. 링크를 Discord 인디게임 채널에 공유
   - 예: itch.io Discord, Indie Game Dev Discord, r/gamedev
2. itch.io 커뮤니티 게시판에 "Feedback wanted!" 포스팅
3. 플레이어 리포트 수집 방법:
   - itch.io 내장 댓글
   - Google Form 링크를 게임 화면에 삽입
4. 수집할 피드백 우선순위:
   - "조작이 직관적이었나요?"
   - "Cat과 Crop 중 어느 캐릭터가 더 재미있었나요?"
   - "어디서 막혔나요?"
```

---

## OnionCat 적용 포인트

### 첫 배포 목표 설정

OnionCat의 현재 단계에서 **itch.io 데모 배포 목표**:
1. 방 3개 + 보스 1마리 완성
2. 업그레이드 선택지 3개 이상 작동
3. 게임 오버 화면 + 재시작 버튼 작동
4. 최소 1개 근접 전용 적 + 1개 원거리 전용 적

이 4개만 있어도 "핵심 협동 경험"을 전달할 수 있다.

### 웹빌드 우선 권장 이유

로컬 코옵 게임이지만, WebGL 빌드로 배포하면:
- 설치 없이 브라우저에서 바로 플레이 → 피드백 참여율 3~5배
- 문제: WebGL은 두 번째 플레이어(마우스 조작)가 브라우저 기본 우클릭 메뉴와 충돌할 수 있음
  → 해결: `WebGLInput.captureAllKeyboardInput = true;` + 브라우저 contextmenu 이벤트 차단 (itch.io 제공 WebGL 템플릿에 포함됨)

---

## 참고 링크

- [itch.io 공식 개발자 문서](https://itch.io/docs/creators/html5)
- [Unity WebGL 빌드 가이드](https://docs.unity3d.com/Manual/webgl-building.html)
- [itch.io WebGL 최적화 가이드](https://itch.io/t/139205/how-to-upload-html5-unity-game)
- [Game Dev 피드백 수집 가이드 (reddit)](https://www.reddit.com/r/gamedev/wiki/earlyaccess)
- [Brackeys: Upload Unity Game to itch.io (YouTube)](https://www.youtube.com/watch?v=p1ccXgXfLHE)
