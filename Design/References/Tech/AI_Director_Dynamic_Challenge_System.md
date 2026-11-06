# AI Director — 동적 도전 관리 시스템

리서치 날짜: 2026-11-06

## 개요

Valve의 Left 4 Dead(2008)가 도입한 **AI Director** 개념: 고정 스폰 포인트 대신 플레이어의 현재 상태를 읽어 적 출현·아이템 배치·음악을 실시간으로 조절하는 시스템.  
로그라이크에 적용하면 방마다 "플레이어가 얼마나 잘하고 있는가"를 계산해 다음 조우(encounter)의 난이도를 동적으로 맞출 수 있다 — 항상 긴장감 있는 적정 도전 유지.

---

## Left 4 Dead AI Director 핵심 원리

### 스트레스 미터 (Intensity / Stress)
- 현재 위험도를 0~100 사이 단일 값으로 추적
- 올라가는 경우: 적에게 맞음, 체력 감소, 적 수 많음, 근거리 적 존재
- 내려가는 경우: 아이템 획득, 적 처치, 열린 공간으로 이동, 아군 협동

### 페이싱 곡선 (Pacing Curve)
```
[빌드업] → [피크] → [휴식] → [빌드업] → ...
```
- Director는 이 곡선을 반복하되, 플레이어가 잘하면 피크가 더 높고 길게, 고전하면 더 짧고 낮게
- **거리 = 난이도**: 체크포인트에서 멀수록 적이 강해짐

### 동적 스폰·아이템 배치
- 적: 종류·수·공격적 특수 감염자(Tank, Witch) 등장 여부를 Stress에 따라 결정
- 아이템: 플레이어가 체력 낮으면 회복 아이템 더 많이 등장
- 음악: Stress 값이 임계치 넘으면 액션 BGM 전환, 내려가면 긴장 완화 BGM

### Director 2.0 (L4D2 추가)
- 기상 조건·낮밤 사이클도 동적 조절
- "도움 행동" — 아군이 쓰러지면 아이템 출현 확률 올림

---

## Unity 구현 방법 (OnionCat 맞춤)

### Step 1: 플레이어 상태 측정 지표

```csharp
public class DirectorMetrics
{
    // 현재 방 성과
    public float HpPercent;          // GameManager.Run.HP / MaxHP
    public int DamageTakenThisRoom;
    public int EnemiesKilled;
    public float TimeInRoom;         // 초
    public int CoopComboCount;
    public int ParryCount;

    // 직전 N방 평균
    public float RecentAverageDamageTaken;
    public float RecentClearTimeAvg;

    // 계산값
    public float StressLevel;        // 0~1

    public void Recalculate()
    {
        // 체력이 낮을수록, 대미지를 많이 받을수록 스트레스 높음
        float hpStress = 1f - HpPercent;
        float dmgStress = Mathf.Clamp01(DamageTakenThisRoom / 30f);
        float timeStress = Mathf.Clamp01(TimeInRoom / 60f); // 60초 초과시 압박
        StressLevel = hpStress * 0.5f + dmgStress * 0.3f + timeStress * 0.2f;
    }
}
```

### Step 2: 방 조우 예산 (Encounter Budget)

```csharp
public class RoomDirector : MonoBehaviour
{
    [SerializeField] DirectorMetrics metrics;
    
    // 방 종류별 기본 예산 (적 위험도 합산 기준)
    static readonly float[] BaseBudget = { 30f, 50f, 70f, 90f }; // tier 0~3
    
    public float GetAdjustedBudget(int tier)
    {
        float budget = BaseBudget[tier];
        // 스트레스 높으면 예산 감소 (쉬운 방 제공)
        // 스트레스 낮으면 예산 증가 (도전적인 방 제공)
        float modifier = Mathf.Lerp(0.7f, 1.3f, 1f - metrics.StressLevel);
        return budget * modifier;
    }
}
```

### Step 3: 스폰 조정

```csharp
// EnemyRoster.ResolveRoom에 Director 연동
public List<EnemySpawnData> ResolveRoom(RoomNode room, DirectorMetrics metrics)
{
    float budget = director.GetAdjustedBudget(room.tier);
    
    // 스트레스 낮으면(잘 하는 중) 엘리트 추가
    if (metrics.StressLevel < 0.3f && Random.value < 0.3f)
        budget += eliteBonus; // 도전 추가
    
    // 스트레스 높으면 최전방 적 대신 원거리 위주 (숨 돌릴 공간)
    bool preferRanged = metrics.StressLevel > 0.7f;
    
    return FillBudget(budget, preferRanged);
}
```

### Step 4: 아이템·보상 조정

```csharp
// 방 클리어 보상 선택 시 Director 반영
public RewardType GetBonusRewardType(DirectorMetrics metrics)
{
    if (metrics.HpPercent < 0.3f)
        return RewardType.Healing;    // 체력 위기 → 회복 아이템 가중치
    if (metrics.StressLevel < 0.2f)
        return RewardType.Gear;       // 쾌적 → 장비 보상
    return RewardType.Normal;
}
```

### Step 5: 음악 연동

```csharp
// 기존 Dynamic_Adaptive_Music_System과 연결
void Update()
{
    metrics.Recalculate();
    Music.SetIntensity(metrics.StressLevel); // 연속 crossfade
}
```

---

## OnionCat 적용 포인트

### 현재 구조와의 연결
- `DungeonManager.stagePlan`이 방 순서를 결정함 → 그 뒤에 Director가 각 방의 **내용**을 조절하는 구조
- `EnemyRoster.ResolveRoom`이 이미 적 선택을 처리 → 거기에 `DirectorMetrics` 파라미터를 넘기면 됨
- `GameManager.Run`에 RunData가 있어 현재 HP·씨앗·아이템 정보 접근 가능

### 협동 2인 특이점
- 고양이·양파 **각각** Stress를 따로 추적하거나, 공유 HP 기반으로 단일 Stress
- 협동 콤보·패링 성공 = Stress 하락 → "잘 맞추면 쉬워지는" 긍정 피드백
- 한 명이 쓰러지면 Stress 급등 → Director가 즉시 쉬운 적 위주로 전환 (회복 기회)

### 구현 우선순위
1. **즉시 적용 가능**: `ResolveRoom`에서 현재 HP%로 엘리트 등장 여부 조절 (5~10줄)
2. **단기**: `DirectorMetrics` 클래스 만들고 방마다 갱신, 예산 ±30% 조절
3. **장기**: BGM Intensity 연동, 아이템 가중치 조절

---

## 참고 링크
- [Giant Bomb: AI Director 개념](https://www.giantbomb.com/ai-director/3015-2539/)
- [Game Developer: "The Discomfort Zone" - AI Director 심층 분석](https://www.gamedeveloper.com/design/the-discomfort-zone-the-hidden-potential-of-valve-s-ai-director)
- [Inverse: Left 4 Dead 15주년 — Director의 유산](https://inverse.com/gaming/left-4-dead-valve-15-year-anniversary)
- [Starship Troopers: Extermination — Director 클론 사례](https://finalboss.io/starship-troopers-extermination-steals-a-page-from-left)
