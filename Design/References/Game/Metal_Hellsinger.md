# Metal: Hellsinger

리서치 날짜: 2026-10-09

## 기본 정보

- **장르**: 리듬 FPS 슈터 (아레나 웨이브)
- **개발**: The Outsiders (Funcom 퍼블리싱)
- **출시**: 2022-09-15
- **Steam**: https://store.steampowered.com/app/1061910/Metal_Hellsinger/
- **위키**: https://metal-hellsinger.fandom.com/wiki/Metal:_Hellsinger_Wiki

## 핵심 시스템

### 리듬 × 전투 융합
- 모든 액션(사격, 재장전, 대쉬, 점프)을 **박자에 맞추면** 스코어 배율(Multiplier) 증가
- 박자 어긋남 → 배율 리셋, 타격음이 허탈하게 들림 (강력한 오디오 피드백)
- 박자 정확도에 따라 3단계: Normal Hit / Beat Hit / Perfect Hit

### Fury 시스템 (배율 = 게임플레이 강화)
- 배율이 오를수록 **실제 피해량 증가** (단순 점수가 아니라 전투력이 강해짐)
- x2 → x4 → x8 → x16 (최고 배율)
- x16 도달 시 **보컬 트랙이 음악에 추가됨** → 음악이 점점 완성되는 느낌
- "음악 = 진행 상태 HUD" 역할: 별도 UI 없이 소리로 배율 인지

### 무기별 리듬 패턴
- 무기마다 **발사 간격과 재장전 템포가 다름** → 각 무기가 다른 리듬 패턴
- 플레이어는 무기를 바꾸면 새로운 리듬에 적응해야 함 → 재플레이 동기

### 적응형 음악 (Adaptive Music)
- 스테이지 음악이 처음에는 인스트루멘탈만 → 배율에 따라 레이어가 쌓임
- 작곡가가 레벨 개념 아트와 레벨 러닝 플레이를 보며 "이 구간의 감정"을 곡에 반영
- 음악과 레벨 디자인을 **동시에 개발**했다는 점이 핵심

### 구조
- 선형 던전 크롤 (로그라이트 아님): 아레나 입장 → 웨이브 격파 → 다음 아레나 이동
- 재플레이 동기는 점수 경쟁(글로벌 리더보드) + 배율 달성 챌린지

## 플레이어가 좋아하는 점

| 요소 | 이유 |
|------|------|
| 음악이 성취 지표 | 배율 올릴수록 음악이 완성되는 정서적 보상 |
| 리듬 게임 접근성 | 다른 리듬 게임보다 쉬워 진입 장벽 낮음 |
| 오디오 피드백 즉시성 | 박자 성공/실패를 소리로 즉각 알 수 있음 |
| 무기 다양성 | 무기별 리듬 패턴 차이가 뚜렷한 플레이스타일 차이로 이어짐 |

## 비판 받는 점

- 리듬 요구 vs 아레나 전투 요구 사이 긴장: "박자에 맞추려면 움직임이 제한된다"
- 스토리 빈약
- 선형 구조라 런마다 차이 없음

## OnionCat 적용 포인트

### 1. 히트감 강화를 위한 "박자 타격 보너스"
- OnionCat에 리듬 시스템을 완전히 추가하기는 과부하지만, **콤보 타이밍 보너스** 정도는 적용 가능
- 예: 적이 쓰러지기 직전 타격에 히트스톱을 더 길게 주거나, 연속 타격 간격이 일정하면 추가 피해
- `HitFeelSettings.asset`의 히트스톱 수치와 연계

### 2. 음악 상태를 전투 강도 HUD로 활용
- OnionCat의 BGM을 콤보/협력 게이지에 따라 인스트루멘탈 → 풀 악기편성으로 레이어업
- `Music.Play(MusicId.X)` 대신 `Music.SetLayer(intensity)` 형태의 API로 확장
- 기술 참고: `Design/References/Tech/Dynamic_Adaptive_Music_System.md`

### 3. "타격음 = 박자 성공 피드백" 디자인 원칙
- 고양이 할퀴기 hit sound와 양파 투사체 hit sound를 **의도적으로 다른 타격감** 설계
- 두 플레이어의 공격이 거의 동시에 맞았을 때 **협력 타격음** 별도 제작 권장
- `Sfx.Play(SfxId.CoopHit)` 트리거 조건: 양쪽 공격이 0.1초 이내 같은 적에게 맞을 때

### 4. 웨이브 압력 관리 (아레나 클리어 구조)
- Metal Hellsinger의 "아레나 입장 → 웨이브 격파 → 이동" 구조가 OnionCat의 방 클리어와 동일
- 방 클리어 후 **팡파르 + 음악 해소** 연출이 플레이어에게 성취감 줌
- Room Clear Celebration VFX 참고: `Design/References/Tech/Room_Clear_Celebration_VFX.md`

### 5. 접근성 있는 리듬 요소
- 리듬 게임처럼 정확하지 않아도 즐길 수 있게: 박자 보너스는 **추가 보상**이지 **필수 조건**이 아니어야 함
- 초보자도 그냥 때리면 재미있고, 숙련자는 타이밍 최적화로 추가 성과 → 두 플레이어의 기술 격차 수용

## 참고 링크

- [Steam 스토어](https://store.steampowered.com/app/1061910/Metal_Hellsinger/)
- [GG Recon 리뷰](https://www.ggrecon.com/reviews/metal-hellsinger-review/)
- [GameSpot — 개발자 디자인 철학](https://www.gamespot.com/articles/in-metal-hellsinger-death-is-your-instrument/1100-6505266/)
- [개발자 인터뷰 (TrueAchievements)](https://www.trueachievements.com/n50185/metal-hellsinger-interview-the-outsiders)
