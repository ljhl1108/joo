# OnionCat TODO

`[ ]` 미완료 · `[x]` 완료

---

## 애니메이션
- [x] 고양이 8방향 걷기 (Aseprite → Blend Tree)
- [x] CatController Animator 연동
- [x] 고양이 방향별 CropHolder 위치 오프셋
- [x] Idle 애니메이션 (속도 0 = Blend Tree 중앙)
- [ ] 공격 / 대쉬 애니메이션

## 전투
- [x] OnionShield.cs — 액티브 실드 + 패링
- [ ] HP / 실드 수치 밸런스 확정

## 방 시스템
- [x] DungeonManager.cs — 방 연결 + 페이드 전환
- [x] RoomManager.cs — 방 클리어 감지
- [ ] SimpleMapGenerator.cs 제거
- [ ] EnemyController / CameraController FindObjectOfType 리팩토링

## UI
- [x] HUDController.cs — HP / 실드 HUD
- [ ] GameOverManager.cs — 게임 오버 화면

## 캐릭터 선택 (저순위)
- [ ] CatData ScriptableObject
- [ ] CropData ScriptableObject
- [ ] 런 시작 시 캐릭터 선택 UI

## 작물 시스템
- [ ] CropSubObject.cs — 작물 교체 시 스프라이트 변경
