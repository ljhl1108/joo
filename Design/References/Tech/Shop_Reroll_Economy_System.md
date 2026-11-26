# 상점 리롤 & 가격 에스컬레이션 시스템

리서치 날짜: 2026-11-26

## 개요

로그라이크의 상점(Shop)에서 현재 진열된 아이템이 마음에 들지 않을 때 추가 비용을 내고 목록을 새로 뽑는 **리롤(Reroll / Refresh)** 메카닉. 단순한 편의 기능처럼 보이지만, 리롤 경제를 어떻게 설계하느냐에 따라 런의 긴장감과 의사결정 깊이가 완전히 달라진다.

OnionCat에 필요한 이유:
- 가판대 방(상점)에서 항상 원하는 장비가 나온다면 선택의 의미가 없어짐
- 그렇다고 리롤이 없으면 "운이 나쁘면 10분을 쓸모없이 날린다"는 느낌
- 올바른 리롤 비용 커브 = "한 번쯤 써볼 만한가" 고민이 생기는 긴장감

---

## 주요 게임의 리롤 설계 비교

### Enter the Gungeon — 없음
- 상점 아이템은 고정, 리롤 없음 (방문할 때마다 새 풀)
- 대신 **상인을 죽이면** 아이템을 훔칠 수 있음 (도덕적 선택 + 패널티)
- 교훈: 리롤 없어도 "지금 살지 말지" 결정만으로 충분한 긴장감 가능

### Binding of Isaac — 1회 무료 + 이후 비용
- Devil Deal·Angel Room은 "다음 방에서 더 나은 게 나올까" 선택
- 리롤 아이템 (D6 등)은 아이템 자체를 바꾸는 특수 메카닉
- 교훈: 리롤을 아이템으로 만들면 리롤 자체가 보상·전략 선택지가 됨

### Hades — 없음(가게)·있음(은혜)
- Wretched Broker(가게)는 리롤 없음, 각 방의 Boon은 Fated Authority(패시브)로 리롤 가능
- 리롤 허용 아이템은 **런 내 1회만** 사용 가능한 자원과 연결
- 교훈: 리롤을 "돈으로 사는 것"이 아니라 **전략 자원을 소비하는 행위**로 설계하면 더 의미 있음

### Dead Cells — 무기 판매자 고정, 리롤 없음
- 대신 돈이 충분하면 항상 살 수 있음 → 돈 자체가 리롤 대신

### Rogue Legacy 2 — 없음
- 상점은 고정, 대신 판매 항목이 런마다 다름

### Slay the Spire — 없음(카드 덱), 있음(상점)
- 카드 제거(Scrap) 비용은 고정 (이 자체가 중요한 경제 선택)
- 상점에서 카드 판매·제거 가능. **가격이 고정**이라 "지금 사나 나중에 사나" 선택이 없음

### Vampire Survivors — 리롤 메카닉 있음
- 레벨업 시 아이템 선택화면에서 **리롤 허용 (횟수 제한, 특성으로 증가)**
- 리롤 비용: 무료이나 횟수가 제한됨 (런 내 고정 횟수 or 패시브로 증가)
- 교훈: 리롤 비용이 금화가 아닌 **횟수 제한**이면 "언제 써야 하나" 타이밍 고민이 생김

### Tiny Rogues — 가격 에스컬레이션
- 첫 리롤: 소액, 이후 점점 비쌈 → "언제 포기하나" 타이밍이 의미 있어짐

---

## 리롤 비용 모델 세 가지

### 모델 A: 고정 비용 (Flat Cost)
```
매 리롤: 씨앗 5개
```
- 장점: 단순하고 직관적
- 단점: 돈이 많으면 무한 리롤 가능 → 의미 퇴색
- 적합: 초기 구현, 보조 화폐가 충분한 중후반

### 모델 B: 에스컬레이션 (Escalating Cost)
```
1번째 리롤: 씨앗 5
2번째 리롤: 씨앗 10
3번째 리롤: 씨앗 20
4번째+: 씨앗 40 (상한)
```
- 장점: 무한 리롤 방지, "이 정도면 그냥 사자" 결정 지점이 생김
- 단점: 첫 2회는 거의 항상 쓰게 됨 → 사실상 무의미할 수 있음
- **적합: 대부분의 경우 추천**

### 모델 C: 횟수 제한 (Use Limit)
```
상점 방 1곳당 리롤 2회 무료, 추가 없음
```
- 장점: 돈과 무관하게 "2번 안에 결정해야" 하는 압박
- 단점: 돈이 남아도 쓸 곳 없음 → 경제 불균형
- 적합: 리롤이 핵심 긴장감일 때 (보조 메카닉이면 과함)

### 권장 복합 모델 (OnionCat용)
```
- 첫 리롤: 씨앗 8
- 두 번째: 씨앗 16
- 세 번째: 씨앗 30
- 네 번째+: 씨앗 50 (상한 고정)
- 단, 한 상점에서 최대 4회 리롤 가능 (5번째부터는 버튼 비활성화)
```

---

## Unity 구현 방법

### 1. 데이터 구조

```csharp
// ShopManager.cs에 추가
[SerializeField] private int[] rerollCosts = { 8, 16, 30, 50 }; // 에스컬레이션 테이블
[SerializeField] private int maxRerolls = 4;

private int _rerollCount = 0; // 이 상점에서 리롤한 횟수

public int GetRerollCost()
{
    int idx = Mathf.Min(_rerollCount, rerollCosts.Length - 1);
    return rerollCosts[idx];
}

public bool CanReroll() => _rerollCount < maxRerolls 
                        && RunData.Seeds >= GetRerollCost();
```

### 2. 리롤 실행

```csharp
public void Reroll()
{
    if (!CanReroll()) return;

    RunData.Seeds -= GetRerollCost();
    _rerollCount++;

    _currentInventory = GenerateShopInventory(); // 새 풀 생성
    ShopUI.Show(_currentInventory);
    ShopUI.UpdateRerollButton(GetRerollCost(), CanReroll());

    // 리롤 비용이 오른 것을 플레이어가 알 수 있게 애니메이션
    ShopUI.PlayRerollCostBumpAnim();
}
```

### 3. UI 연동

```csharp
// ShopUI.cs
public void UpdateRerollButton(int cost, bool canReroll)
{
    _rerollButton.interactable = canReroll;
    _rerollCostText.text = $"리롤 {cost}씨앗";

    // 비용이 너무 높으면 빨간 글씨
    _rerollCostText.color = canReroll ? Color.white : Color.red;
}
```

### 4. 상태 초기화 (방 나갈 때)

```csharp
// ShopRoom.cs
void OnRoomExit()
{
    // 다음에 같은 상점에 올 경우를 대비 (대부분 없지만 방어적으로)
    _rerollCount = 0;
}
```

---

## OnionCat 적용 포인트

### 가판대 방(상점) 설계
OnionCat의 가판대 방은 `Room_Special`을 재사용. 여기서:
- **진열 아이템 3개**: 고양이 장비 1 + 양파 장비 1 + 공통 소모품 1 (기본 구성)
- **리롤 버튼**: 한 명이 리롤하면 양쪽 진열 모두 바뀜 → 협동 합의 필요
- **비용은 씨앗(Seeds)**: `RunData.Seeds` 직접 차감

### 2인 협동 리롤의 갈등 설계
리롤 비용이 공동 자원(씨앗)에서 나오므로 **두 플레이어가 합의해야** 함:
- 고양이: "이 장비 별로야, 리롤하자"
- 양파: "나는 이게 마음에 드는데?"
→ 이 대화 자체가 협동 경험의 일부

### 리롤 횟수 표시 방법
```
[리롤 | 🌱×8] → [리롤 | 🌱×16] → [리롤 | 🌱×30] → [리롤 불가 ✗]
```
버튼 아래에 현재 비용을 항상 표시. 비용이 올라갈 때 숫자가 "튀면서" 올라가는 연출 추가.

### 씨앗 경제와의 연동
- 1방 클리어 시 씨앗 10~20개 획득 (평균)
- 리롤 1회 = 씨앗 8~50 → "2방치 보상을 한 번에 소비"하는 느낌
- 너무 쉽게 리롤하면 의미 없음 → **첫 리롤만 "살짝 아깝다" 수준으로**

---

## 참고 링크
- [Roguelike Design: Economy & Rerolls (GDC Vault 개념)](https://gdcvault.com)
- [Slay the Spire Wiki: Shop Mechanics](https://slay-the-spire.fandom.com/wiki/Shop)
- [Vampire Survivors Wiki: Reroll](https://vampire-survivors.fandom.com/wiki/Reroll)
- [Unity Docs: ScriptableObject](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
