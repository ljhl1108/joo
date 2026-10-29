# Enemy Alert State Design

리서치 날짜: 2026-10-29

## 개요

적이 플레이어를 "어떻게, 언제, 어떤 속도로" 인식하느냐는 전투 리듬 전체를 결정한다.
인식이 너무 빠르면 방에 들어서자마자 포위되고, 너무 느리면 각개격파가 너무 쉬워진다.
OnionCat처럼 실시간 액션 로그라이크에서 **경보 상태 설계**는 방 경험의 질을 직접 좌우한다.

이 문서는 구현 방법(→ `Enemy_AI_StateMachine.md`, `Enemy_Awareness_Alert_Visual.md`)이 아닌
**디자인 의사결정**과 **수치 튜닝 기준**에 집중한다.

---

## 경보 상태 4단계 구조

```
Idle → Alert → Aggro → Combat
```

| 상태 | 의미 | 행동 |
|------|------|------|
| **Idle** | 플레이어 모름 | 순찰 또는 제자리 대기 |
| **Alert** | 이상 감지 | 발소리 방향 보기, 천천히 접근 |
| **Aggro** | 플레이어 확인 | 빠르게 접근, 공격 준비 |
| **Combat** | 전투 중 | 패턴 실행 |

---

## 상태 전환 트리거 설계

### Idle → Alert 트리거
- 시야각(FOV) 내 플레이어 감지
- 소음: 플레이어가 공격하거나 피격될 때 반경 내 적 Alert 전환
- 인접 적 Combat 진입 시 "알림" 전파 (소수만 전파, 전체 전파는 혼돈)

**권장 수치 (OnionCat 기준)**:
- FOV 각도: 120°, 거리: 8유닛 (32px PPU 기준 256px)
- 소음 전파 반경: 6유닛
- Alert 유지 시간(플레이어를 놓친 뒤): 3~4초

### Alert → Aggro 트리거
- Alert 상태에서 플레이어를 시야 내에 2초 이상 유지
- 플레이어가 직접 공격하면 즉시 Aggro (피격 = 즉각 반응)

**디자인 원칙**: 플레이어가 "숨을 수 있다"는 느낌을 줄 것인가 결정.
- 스텔스 요소 있음 → Alert→Aggro 전환에 1~2초 여유 줌
- 순수 액션 → Alert 단계를 거의 생략하고 시야 감지 즉시 Aggro

**OnionCat 추천**: 짧은 Alert (0.5초) → 빠른 Aggro. 방에 들어서는 순간 전투 시작을 명확하게.

### Aggro → Combat 트리거
- 공격 사거리 내 진입 시 자동 전환
- 근접 적: 플레이어에서 1.5유닛 내
- 원거리 적: 조준 완료 후 발사

### Combat → Idle (탈각)
- 일반 적은 탈각하지 않는 게 기본 (플레이어가 도망가도 방 안에서 계속 추격)
- 예외: 방 경계 밖으로 나가면 리셋 → `Enemy_Leash_Return_System.md`

---

## 빠른 액션 게임에서의 특별 규칙

### "즉발 인식" 패턴 (OnionCat 권장)
방에 들어서는 순간 모든 적이 Aggro가 되는 패턴:
```csharp
void OnRoomEnter() {
    foreach (var enemy in EnemyBase.Active)
        enemy.ForceAggro(player.transform.position);
}
```
- 장점: 전투 시작이 명확, 순찰 AI 구현 생략
- 단점: "발견의 재미" 없음
- **OnionCat에 적합**: 방 단위 전투 구조이므로 방 입장 = 전투 시작이 자연스러움

### "점진 인식" 패턴 (선택적)
- 방 중앙부 적은 즉발 Aggro
- 방 외곽 적은 소음 전파로 3~5초 후 전투 합류
- **효과**: 전투가 한번에 터지지 않고 웨이브처럼 느껴짐 → 압도감 조절 가능

---

## 플레이어에게 경보 상태를 전달하는 방법

구현은 `Enemy_Awareness_Alert_Visual.md` 참조. 디자인 원칙:

1. **물음표(?)** = Alert 상태 — 아직 확신 없음
2. **느낌표(!)** = Aggro 전환 — 즉시 달려옴
3. **색상 변화** — 눈이 노랑→빨강으로 변하는 패턴도 효과적
4. **사운드 큐** — `Sfx.Play(SfxId.EnemyAlert)`: 인식 소리는 플레이어에게 "방어 준비" 시간 줌

**OnionCat 중요**: 고양이가 이동 중이고 양파는 조준 중일 때 경보 상태를 둘 다 알아차려야 함
→ 화면에 항상 잘 보이는 머리 위 아이콘이 필수

---

## 그룹 인식 vs 개별 인식

### 개별 인식 (각자가 따로 플레이어를 발견)
- 방 청소 중 뒤에서 천천히 다가오는 적이 생김
- "다 잡았다고 생각했는데 뒤에서 등장" → 서프라이즈 요소
- 복잡도 낮음, 구현 쉬움

### 공유 인식 (한 명이 발견하면 전체 알림)
- 한 적이 플레이어를 보면 근처 N마리에게 신호 전파
- "무전" 효과 → 그룹 협동처럼 보임
- 구현: 인식 시 `Physics2D.OverlapCircle`로 반경 내 적에게 `ForceAggro()` 전파

**OnionCat 권장**: 방 입장 시 즉발 전체 Aggro + 이후 소환 적은 개별 인식
(소환 적이 갑자기 포위하면 억울함 → 소환 직후 0.5초 지연 후 Aggro)

---

## 수치 튜닝 체크리스트

플레이 테스트 시 확인할 항목:

- [ ] 방에 들어서면 적이 "이제 싸우는구나"라는 신호를 명확히 줌
- [ ] 적이 등 뒤에서 소리 없이 공격하면 억울하다는 피드백이 없음
- [ ] 방 입장 후 3초 안에 전투가 시작됨 (지루한 대기 없음)
- [ ] 원거리 적은 항상 화면 안에서 조준을 시작함 (화면 밖 발사 없음)
- [ ] 회피 후 적이 새 위치로 재조준하는 모습이 보임

---

## OnionCat 적용 포인트

- **현재 구조**: 방 입장 시 적 즉발 Aggro가 맞는 방향 (로그라이크 템포 유지)
- **개선점**: 소환 적(`EnemySpawner`)은 소환 후 0.5초 Idle → Aggro 전환으로 "등장 확인" 시간 주기
- **보스**: 입장 컷신 후 첫 번째 패턴 시작 전 0.8초 대기 → 플레이어가 준비할 시간
- `EnemyBase`의 `AlertRadius`, `AggroDelay`를 `HitFeelSettings.asset`이 아닌 별도 `CombatSettings.asset`으로 관리하면 튜닝하기 쉬움

---

## 참고 링크

- Game Developer: https://www.gamedeveloper.com/design/enemy-awareness-and-ai-design-patterns
- GDC 2017 Level Design: "How Enemy Behavior Shapes Encounter Design" (검색 권장)
- Unity DOTS-based enemy AI examples: https://docs.unity3d.com/Packages/com.unity.entities@latest
- 관련 OnionCat 파일: `Enemy_AI_StateMachine.md`, `Enemy_Awareness_Alert_Visual.md`, `Enemy_Telegraph_System.md`
