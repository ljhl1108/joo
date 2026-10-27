# 게임 데모 설계 모범 사례

리서치 날짜: 2026-10-27

## 개요

게임 데모는 단순히 "게임의 일부를 자르는 것"이 아니다. **최고의 데모는 본 게임과 별개로 기획된 독립 경험**이다. Steam Next Fest, itch.io 무료 데모, 미디어 프리뷰 등 다양한 시나리오에서 OnionCat이 데모를 공개할 때 어떻게 설계하면 최대 전환율(데모 → 구매)을 얻을 수 있는지 정리한다.

---

## 왜 데모 설계가 게임 설계와 다른가

| 본 게임 목표 | 데모 목표 |
|------------|---------|
| 장기 재미 (10~30시간) | 즉각 인상 (20~40분) |
| 점진적 복잡도 | 핵심 재미를 빠르게 전달 |
| 세이브/이어하기 | 완결된 경험 |
| 콘텐츠 깊이 | 폭발적 첫인상 |

---

## 1. 데모 범위 설계 원칙

### 황금률: 데모는 끝나야 한다

- 데모는 "본 게임의 특정 챕터까지" 또는 "첫 보스 격파"처럼 **명확한 엔딩이 있어야 함**
- "런 2회까지" 같은 카운터 제한은 UI를 추가해야 하지만 효과적
- 끝이 없는 데모 → 플레이어가 지쳐서 끊음 → 기억이 흐릿해짐

### 데모 길이 권장

| 장르 | 권장 데모 길이 | 이유 |
|------|-------------|------|
| 단타 액션 | 15~25분 | 빠른 만족 + 짧은 콘텐츠 |
| 로그라이크 | 30~45분 (런 1~2회) | 한 런을 완주하는 만족감 필요 |
| 스토리 중심 | 60~90분 (1챕터) | 세계관 몰입에 시간 필요 |

**OnionCat 권장**: 스테이지 1 완주 (전투방 6~8개 + 보스). 약 30분. 1회 런 완주 경험.

### 뭘 잘라야 하나

✅ **데모에 넣어야 하는 것**:
- 핵심 기믹의 가장 재미있는 순간 (2인 협동 기믹 필수)
- 장비 드래프트 최소 3~4회 (성장의 쾌감)
- 중간 난이도 전투 (쉽지도 어렵지도 않게)
- 보스 1명 (게임의 강도를 보여주는 정점)
- 협동 콤보가 폭발하는 순간

❌ **데모에서 빼야 하는 것**:
- 메타 진행(온실, 해금 시스템) — 본 게임 구매 동기가 됨
- 전설급 장비 — 본 게임만의 특별함
- 스테이지 2~3 적 — 미리 보여주면 신선함 소진
- 복잡한 세트 보너스 풀 세팅 — 데모에서 이해하기 전에 끝남

---

## 2. 첫 5분이 전부다

플레이어가 데모를 삭제하는 가장 큰 이유: **"처음 5분이 재미없었다"**.

### 첫 5분 체크리스트

```
□ 로딩 화면이 10초 이내
□ 제목 화면 → 게임 시작 클릭이 3단계 이내
□ 1분 내에 첫 전투 발생
□ 3분 내에 첫 "와!"를 유발하는 순간 (협동 콤보 폭발, 적 날리기 등)
□ 5분 내에 첫 장비 선택 (성장 시스템 소개)
```

OnionCat의 경우:
- 시작 → 첫 방 진입이 60초 이내여야 함
- 첫 방을 클리어하면 즉시 드래프트 화면
- 두 번째 방에서 협동 콤보가 자연스럽게 발생하도록 방 설계 (적 배치가 고양이-양파 교번 공격 유도)

---

## 3. 난이도 튜닝 — 데모는 본 게임보다 약간 쉬워야 한다

이유: 데모 플레이어는 스킬이 없다. 죽어서 포기하면 전환율 0.

### 데모 전용 난이도 조정 목록

```
□ 적 HP: 본 게임 × 0.8
□ 적 데미지: 본 게임 × 0.8
□ 보스 HP: 본 게임 × 0.7
□ 첫 드래프트: 희귀 아이템 1개 보장 (평소 60/28/10/2 비율 대신)
□ 실드 회복 속도: 약간 빠르게
□ 합동 게이지: 10~15% 빠르게 참 (협동기 경험시키기)
```

"데모가 쉽다"는 리뷰는 드물다. 대부분은 "어려워서 못하겠다"는 리뷰가 전환율을 낮춤.

---

## 4. 데모 전용 UX 추가 요소

### 4-1. 미완성 알림 배너

화면 상단에 작게:
```
데모 버전 — 스테이지 1까지 플레이 가능
```
→ 갑자기 "To Be Continued" 화면이 나와도 배신감이 덜함.

### 4-2. 엔딩 후 구매 유도 화면

보스 클리어 → "런 완주!" 화면 → 5초 후 자동으로 (또는 버튼으로):

```
[ 스테이지 2와 3이 기다리고 있어요! ]
[ 장비 163종 중 이번 런에서 만난 장비는 XX종이었습니다 ]
[ Steam에서 지금 구매 → ]  [ 다시 플레이 ]
```

Steam Next Fest 기간이라면 카운트다운 타이머도 효과적.

### 4-3. 데모 전용 저장 분리

```csharp
// 데모 세이브와 본 게임 세이브 경로 분리
string savePath = Application.isDemo
    ? Path.Combine(Application.persistentDataPath, "demo_save.json")
    : Path.Combine(Application.persistentDataPath, "save.json");
```

본 게임 구매 후 실행할 때 데모 데이터가 섞이지 않아야 함.

---

## 5. Unity 구현 — 데모 전용 빌드 설정

### 방법 1: Define Symbol 활용

```csharp
// Player Settings → Scripting Define Symbols에 DEMO_BUILD 추가
#if DEMO_BUILD
    const int MAX_RUN = 1;           // 런 1회만
    const int MAX_STAGE = 1;         // 스테이지 1까지
    const bool SHOW_DEMO_BANNER = true;
#else
    const int MAX_RUN = int.MaxValue;
    const int MAX_STAGE = int.MaxValue;
    const bool SHOW_DEMO_BANNER = false;
#endif
```

### 방법 2: ScriptableObject Demo Config

```csharp
[CreateAssetMenu(menuName = "Config/DemoConfig")]
public class DemoConfig : ScriptableObject
{
    public bool IsDemoMode;
    public int MaxStage = 1;
    public float EnemyHpMultiplier = 0.8f;
    public float DraftRareGuaranteeChance = 0.5f;
    public string SteamStoreUrl;
    public string PurchaseCTA;        // "지금 구매하고 스테이지 2 공략!"
}
```

에디터에서 쉽게 켜고 끌 수 있어 별도 브랜치 없이 관리 가능.

### 방법 3: Steam Playtest 기능 활용

Steam에는 별도 데모 앱 ID가 있음. 본 게임 앱 ID와 분리되어 있어:
- 데모 리뷰가 본 게임 리뷰에 포함되지 않음
- 데모 플레이어 수 통계를 따로 볼 수 있음
- 전환율 (데모 플레이 → 본 게임 구매) 통계 제공

---

## 6. 데모 출시 시기와 전략

### Steam Next Fest가 가장 효과적

- 1년에 여러 번 (2월, 6월, 10월)
- 참여한 데모는 Steam 홈화면에 노출
- 위시리스트 수가 Next Fest 기간에 폭발적으로 증가
- 권장: 본 게임 출시 3~6개월 전

### 데모 출시 전 체크리스트

```
□ 크래시 없이 시작~보스 클리어까지 5회 이상 테스트 완료
□ 처음 보는 사람 (가족/친구) 에게 플레이시켜 막히는 곳 파악
□ 데모 종료 화면에 스팀 링크 또는 위시리스트 버튼
□ itch.io에도 동시 업로드 (Steam 없는 플레이어 대비)
□ 개발자 Discord/SNS에 출시 공지 준비
```

---

## OnionCat 적용 포인트

1. **데모 범위**: 스테이지 1 (정원) 완주. 보스 성녀 궁수 격파 후 "데모 완료" 화면. 약 30분 분량.
2. **2인 기믹 필수 포함**: 쌍둥이 스위치 기믹이 데모에 반드시 포함되어야 "2인 협동 게임"의 정체성 전달.
3. **첫 5분**: 1번 방부터 씨앗 탄 + 할퀴기 교번 공격이 자연스럽게 일어나도록 적 배치 (한 명이 오른쪽, 한 명이 왼쪽).
4. **데모 전용 드래프트 조정**: 첫 드래프트에 희귀 50% 보장 → "다음 런에서 더 강해질 수 있다" 기대감.
5. **`Application.isDemo`** 활용 또는 ScriptableObject 기반 DemoConfig로 브랜치 없이 관리.
6. **온실 잠금**: 데모에서 메타 해금은 보이지 않음 → 본 게임 구매 후 온실 오픈이 "보상"이 됨.

## 참고 링크

- [How to Design a Game Demo (GDC 2019)](https://www.gdcvault.com/play/1026024)
- [Steam 데모 등록 가이드](https://partner.steamgames.com/doc/store/demo)
- [Steam Next Fest 가이드](https://partner.steamgames.com/doc/marketing/next_fest)
- [itch.io Demo Best Practices](https://itch.io/blog/257442/how-to-make-a-good-game-demo)
- [Mark Brown - What Makes a Good Demo? (GMTK)](https://www.youtube.com/watch?v=DOFAN28z56o)
