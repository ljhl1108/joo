# The Rogue Prince of Persia

리서치 날짜: 2026-06-30

## 기본 정보

- **개발사**: Evil Empire (Dead Cells 개발팀)
- **퍼블리셔**: Ubisoft
- **출시**: 2024년 5월 (Early Access) → 2025년 정식 출시
- **플랫폼**: PC (Steam), Epic Games Store
- **Steam 링크**: https://store.steampowered.com/app/1903340/The_Rogue_Prince_of_Persia/
- **장르**: 2D 액션 플랫포머 로그라이트

---

## 핵심 메카닉

### 1. 유동적인 이동 시스템 (Fluid Movement)
The Rogue Prince of Persia의 핵심 차별점:
- **벽달리기(Wall Running)**: 벽에 붙어 수평 이동, 높은 위치로 올라가는 핵심 동작
- **폴 킥(Pole Kick)**: 폴 위에서 점프 → 적에게 킥 → 다음 폴로 이동 연결
- **슬라이드 & 롤**: 빠른 지면 이동, 적의 공격 피하기
- **공중 대시**: 공중에서 방향 전환
- **이동 연결성**: 벽달리기 → 폴 킥 → 대시 → 공격 등 끊김없는 콤보

**철학**: 죽기 전까지 모든 이동이 연결되어 있어야 함. 멈추는 순간 죽는다.

### 2. 근접 & 원거리 무기 이중 시스템
- **주무기(Melee)**: 검, 도끼, 체인, 모닝스타 등 근접 무기
- **보조 무기(Ranged/Tool)**: 투창, 폭탄, 후크 등 보조 도구
- 두 슬롯 자유 조합 → 자신만의 스타일 구축
- Dead Cells와 달리 무기 **수집 후 선택** 방식 (런 내 고정 2슬롯)

### 3. 업그레이드 & 빌드 시스템
- **보물(Boon)**: 각 지역 클리어 후 3개 중 선택
- **부적(Amulet)**: 패시브 강화 장신구
- **빌드 방향**: 이동 강화형 / 공격적 근접형 / 원거리 집중형
- 업그레이드 간 시너지가 명확하게 설계됨

### 4. 시간 역행 메카닉 (Time Rewind)
- 사망 순간 짧은 시간 역행 → 재도전 가능
- 단, 역행 사용 시 현재 런에서 골드 패널티
- "죽음을 한 번 되돌릴 수 있다"는 서사적 정당성도 갖춤

### 5. 영구 해금 시스템
- 골드로 타운 건물 업그레이드 → 새 아이템 추가, 상인 서비스 확대
- Dead Cells의 세포(Cell) 시스템과 유사

---

## 진행 구조

```
Hub(Town) → 지역1(Hammam) → 보스 → 지역2(Oasis) → 보스 → 지역3(Citadel) → 최종 보스
```
- 각 지역: 선형 이동 + 숨겨진 방
- 방 구조: 전투 방 / 상인 방 / 보물 방 / 도전 방

---

## 플레이어가 사랑하는 것

1. **이동의 유려함**: "움직이는 것만으로 재미있다" → 최고의 칭찬
2. **Dead Cells DNA**: 같은 팀이 만든 탄탄한 게임 느낌, 피드백
3. **페르시아 왕자 리부트**: 원작 팬에게 서비스 + 신규 플레이어도 진입 용이
4. **빠른 런**: 한 런이 30~60분 → 부담 없는 플레이

---

## OnionCat 적용 포인트

### A. 이중 무기 슬롯 → OnionCat의 역할 분리
고양이(근접) + 양파(원거리)가 이미 이중 무기 시스템:
- 이 게임의 **근접↔원거리 전환 타이밍 설계**를 참고할 것
- "이 상황엔 근접이 답, 저 상황엔 원거리가 답" 명확히 구분하는 적 디자인

### B. 이동 연결성 → 고양이 대시 시스템
대시가 단순 회피가 아니라 이동 흐름의 일부가 되도록:
- 대시 후 자동 공격 연결 (Dead Cells도 동일 방식)
- 대시 = 이동 + 무적 + 공격 시작 → 3기능 압축

### C. 보물(Boon) 선택 UI
업그레이드 선택 UI의 레이아웃:
- 3개 선택지를 가로로 배치
- 각 카드에: 아이콘 + 이름 + 설명 2줄 + 레어리티 색상 테두리
- OnionCat의 Upgrade_Selection_Screen 구현 시 참고

### D. 시간 역행 → OnionCat의 "부활" 메카닉 아이디어
- 죽었을 때 1회 부활 기회 (업그레이드로 해금)
- 단, 부활 시 현재 런 골드 절반 차감
- 쉬운 난이도로 접근하는 입문자를 배려하는 시스템

### E. 빠른 런 타임
OnionCat 목표 런 타임: **20~30분**
- Rogue Prince of Persia의 30분 런 구조 참고
- 방 수 설계: 초반부(5~7개) → 중반부(5~7개) → 보스 → 종료

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/1903340/The_Rogue_Prince_of_Persia/
- 공식 사이트: https://www.ubisoft.com/en-us/game/prince-of-persia/the-rogue-prince-of-persia
- IGN 리뷰: https://www.ign.com/articles/the-rogue-prince-of-persia-review
- GDC 세션 (Evil Empire 이동 설계 철학): https://www.gdcvault.com/
- Dead Cells와의 비교 분석: https://www.thegamer.com/the-rogue-prince-of-persia-vs-dead-cells/
