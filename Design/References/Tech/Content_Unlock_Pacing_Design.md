# Content Unlock Pacing Design (콘텐츠 해금 페이싱 설계)

리서치 날짜: 2026-11-09

## 개요

로그라이크 게임에서 여러 번의 런에 걸쳐 새 캐릭터·아이템·스테이지·이야기를 **언제** 해금할지
결정하는 설계 이론. 너무 빨리 다 보여주면 흥미가 금방 꺼지고,
너무 느리면 "재미없다 — 삭제"가 된다.

OnionCat은 온실(장비 해금), 작물 해금(2·3단계 작물), 이야기 단계(MetaProgress.Chapter),
파편 시스템이 있어 이 페이싱 설계가 직접 적용된다.

---

## 핵심 원칙

### 1. 첫 런에서 핵심 판타지를 완전히 경험시켜라

첫 런은 **전체 게임의 축소판**이어야 한다:
- 모든 핵심 시스템을 최소 한 번씩 써보게 (장비 획득, 협동 콤보, 보스 처치)
- 클리어 여부와 무관하게 "이게 이런 게임이구나" 느끼게
- Hades, Vampire Survivors 모두 10분 안에 핵심 루프를 보여줌

**OnionCat**: 첫 런 ≤ 20분에 고양이 할퀴기·양파 씨앗·협동 콤보·장비 1개 획득·보스 1마리 경험 목표

### 2. 조기 해금 — 처음 3런이 가장 중요하다

```
런 1: 핵심 루프 체험 (클리어 불필요)
런 2: 첫 번째 의미 있는 해금 (신규 아이템 2~3개 or 신규 작물)
런 3: 그 해금이 플레이에 영향을 미침을 느낌
```

3런 안에 "이게 더 나아지고 있다"는 느낌이 없으면 이탈률 급증.
(Hades는 2번째 런부터 무기 1개 추가 선택, Slay the Spire는 2런 차에 첫 번째 잠금 카드 해금)

### 3. 긴장 → 보상 리듬

```
탐색 2~3런 (알려지지 않은 것 발견) →
보상 1런 (해금 달성) →
정착 1~2런 (새 콘텐츠 소화) →
탐색 반복
```

한 번에 너무 많이 주면 선택 마비(choice paralysis) 발생.
한 번에 1~2가지 주는 것이 적정.

### 4. 해금 조건의 명확성

| 좋은 조건 | 나쁜 조건 |
|----------|----------|
| "런에서 50마리 처치" | "운 좋으면 얻을 수도 있음" |
| "1스테이지를 10회 완료" | "조건 불명확 — 그냥 했더니 해금됨" |
| "해바라기로 보스 처치" | "파편 100개 — 언제 모으나?" |

**핵심**: 플레이어가 조건을 미리 알고 목표를 가질 수 있어야 함.
Hades의 무기 잠금 해제는 거울 메뉴에서 항상 보임.

### 5. 반복 플레이 유인 — "다음 런에 하고 싶은 것"

런 종료 시점에서 플레이어 머릿속에 최소 1개의 "다음에 해볼 것"이 있어야 함:
- 방금 해금된 아이템 써보기
- 조금 더 가면 클리어할 것 같은 느낌
- "저 조합을 한 번 더 시도해보고 싶다"

---

## 로그라이크별 해금 페이싱 비교

### Hades
- 런 1~5: 무기 1개 → 2개, 거울 1~3 업그레이드 (매 런 의미 있는 성장)
- 런 10~20: 첫 번째 엔딩 도달 가능 → 진짜 엔딩 위한 10번 더 클리어 요구
- 런 20~50: 대화·이야기 해금 계속, 각 무기 종류별 도전

**교훈**: 짧은 사이클(매 런)과 긴 사이클(10~20런 목표)을 동시에 운영

### Vampire Survivors
- 분 단위: 무기 조합 발견 → 즉시 강력해짐 느낌
- 런 단위: 새 캐릭터·무기 해금 (5~10런 단위)
- 충격적인 해금: "대포 무기 추가됨" 같은 질적 도약

**교훈**: 양적 성장(레벨업)과 질적 도약(해금) 구분

### Dead Cells
- 세포(통화)로 패시브 업그레이드: 매 런 조금씩 강해짐
- 무기 블루프린트: 처음 보는 적에게서 드롭 → 탐험 동기
- Boss Stem Cell: 1~5BC 난이도 단계가 콘텐츠 잠금 열쇠

**교훈**: 탐험 자체가 해금 조건 → "새 구역 가면 뭔가 나옴" 기대

---

## OnionCat 적용 포인트

### 1. 현재 온실 해금 구조 분석

```
파편(fragmentsEarned) → MetaProgress → GearItem.UnlockCost → RewardTable.Pool 추가
```

현재 구조는 올바르나, 플레이어가 "파편 얼마 모으면 뭐가 열리나"를 미리 볼 수 있어야 함.
→ **온실 화면에서 잠긴 장비를 흐리게 표시 + 필요 파편 수 보여주기** 권장

### 2. 작물 해금 페이싱 조정 제안

현재:
- 1단계: 양파 (시작부터)
- 2단계: 해바라기 (MetaProgress.Chapter ≥ 2)
- 3단계: 푸른 버섯 (MetaProgress.Chapter ≥ 3)

이야기 단계가 런 10~20개 분량이라면 각 작물 사이가 너무 길 수 있음.
**제안**: 2단계 작물은 "첫 번째 보스 처치" 시 해금 (런 수 기준이 아닌 이정표 기준)

### 3. 런 종료 화면에서 "다음 목표" 명시

현재 런 결과 화면에서 추가:
- "파편 N개 더 모으면 [장비명] 해금 가능!" 한 줄
- "다음 이야기 단계까지 판 N개 남음" 등

`Coop_Run_Result_Screen.md` 구현 시 이 요소 포함 권장

### 4. 짧은 사이클 + 긴 사이클 구분

| 사이클 | 현재 OnionCat | 보강 방향 |
|--------|-------------|---------|
| 런 내 (즉시) | 장비 획득·레벨업 | 이미 있음 |
| 런 단위 (1~3런) | 파편 소량 획득 | **해금 카운트다운 UI 추가** |
| 중기 (5~10런) | 이야기 단계 진행 | **이야기 단계별 작물 해금** |
| 장기 (20런+) | 모든 장비 해금 | 온실 목표 명확화 |

### 5. 첫 런 경험 체크리스트

OnionCat 테스트 시 아래를 확인:
- [ ] 10분 이내 첫 번째 장비 획득
- [ ] 20분 이내 보스 1마리 경험 (처치 불필요)
- [ ] 30분 이내 협동 콤보 1회 발동
- [ ] 런 종료 시 "다음에 해볼 것"이 머릿속에 있음

---

## Unity 구현 체크리스트

```csharp
// 런 종료 시 "다음 해금 힌트" 계산
string GetNextUnlockHint()
{
    var next = RewardTable.GetCheapestLocked();      // 가장 저렴한 미해금 장비
    if (next == null) return "모든 장비 해금 완료!";
    int need = next.unlockCost - MetaProgress.Data.fragmentsEarned;
    return $"파편 {need}개 더 모으면 [{next.displayName}] 해금!";
}
```

```csharp
// 온실 화면: 잠긴 장비 흐리게 표시 + 비용 표시
void UpdateGreenhouse()
{
    foreach (var gear in allGear)
    {
        bool unlocked = MetaProgress.Data.unlockedGear.Contains(gear.id);
        gearCard.SetAlpha(unlocked ? 1f : 0.4f);
        lockIcon.SetActive(!unlocked);
        costLabel.text = unlocked ? "" : $"파편 {gear.unlockCost}개";
    }
}
```

---

## 참고 링크

- GDC 2016 "The Road to the Hades Release" (Supergiant Games): https://www.gdcvault.com/
- Game Maker's Toolkit — "What Makes Celeste's Assist Mode Work": https://www.youtube.com/watch?v=NInNVEHe1WY
- Rami Ismail "Releasing Your First Game" — 해금 페이싱 조언 포함
- Hades 개발자 commentary — Steam 커뮤니티
- "Loss Aversion in Game Design" — Gamasutra/Game Developer: https://www.gamedeveloper.com/
