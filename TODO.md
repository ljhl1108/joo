# OnionCat TODO

`[ ]` 미완료 · `[x]` 완료

---

## 게임 루프 완성 (최우선)
- [ ] GameOverManager.cs — 게임 오버 화면 + Cat 독백 + 재시작
- [ ] 메인 메뉴 씬 — 타이틀 화면 + 시작/종료 버튼
- [ ] 씬 전환 페이드 — 방 이동 시 0.3초 페이드 인/아웃

## 전투 시스템
- [x] OnionShield.cs — 액티브 실드 + 패링
- [x] HUDController.cs — HP / 실드 HUD
- [ ] WeaknessType 시스템 — 적 약점(근접/원거리) 적용 + 시각 피드백
- [ ] HP / 실드 수치 밸런스 확정

## 적 AI
- [ ] 패트롤 → 경보 → 추격 StateMachine (EnemyBase 리팩토링)
- [ ] EnemyController FindObjectOfType 리팩토링

## 방 시스템
- [x] DungeonManager.cs — 방 연결 + 페이드 전환
- [x] RoomManager.cs — 방 클리어 감지
- [ ] 방 프리팹 구조 — 전투방 3~4종 + 보스방 1종
- [ ] SimpleMapGenerator.cs 제거
- [ ] CameraController FindObjectOfType 리팩토링

## 세이브 / 진행
- [ ] PlayerPrefs — 최고 기록 저장 (처치 수, 클리어 시간)

## 애니메이션
- [x] 고양이 8방향 걷기 (Aseprite → Blend Tree)
- [x] CatController Animator 연동
- [x] 고양이 방향별 CropHolder 위치 오프셋
- [x] Idle 애니메이션
- [ ] 공격 / 대쉬 애니메이션

## 캐릭터 선택 (저순위)
- [ ] CatData ScriptableObject
- [ ] CropData ScriptableObject
- [ ] 런 시작 시 캐릭터 선택 UI

## 작물 시스템 (저순위)
- [ ] CropSubObject.cs — 작물 교체 시 스프라이트 변경
