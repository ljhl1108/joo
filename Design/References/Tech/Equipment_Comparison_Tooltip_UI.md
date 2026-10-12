# Equipment Comparison Tooltip UI (장비 비교 툴팁 UI)

리서치 날짜: 2026-10-12

## 개요

장비 선택·상점 화면에서 새 아이템을 확인할 때, 현재 장착된 아이템과 **수치 차이(delta)와 효과 차이**를 나란히 보여주는 UI 패턴. 플레이어가 빠른 판단을 내릴 수 있게 해 인지 부하를 줄인다.

OnionCat에서는 보상 카드 선택(`UpgradeSelectUI`), 상점 구매, 전투방 드롭 알림에서 이 패턴이 필요하다.

---

## Unity 구현 방법

### 1. 데이터 모델: 비교 가능한 스탯 집계

```csharp
// GearItem은 ScriptableObject. 비교 계산은 순수 데이터 함수.
public static class GearComparer
{
    public struct Delta
    {
        public float hpDelta;
        public float atkDelta;
        public float spdDelta;
        // 효과 추가·제거 목록
        public List<EffectData> added;
        public List<EffectData> removed;
    }

    public static Delta Compare(GearItem current, GearItem next, RunData run)
    {
        var curStats = run.GetStatsWithGear(current);
        var nxtStats = run.GetStatsWithGear(next);
        return new Delta {
            hpDelta  = nxtStats.maxHp  - curStats.maxHp,
            atkDelta = nxtStats.attack - curStats.attack,
            spdDelta = nxtStats.speed  - curStats.speed,
            added    = next.effects.Except(current?.effects ?? Enumerable.Empty<EffectData>()).ToList(),
            removed  = (current?.effects ?? Enumerable.Empty<EffectData>()).Except(next.effects).ToList(),
        };
    }
}
```

### 2. 툴팁 프리팹 구조

```
TooltipRoot (RectTransform, ContentSizeFitter vertical)
├── Header ("현재" / "신규" 레이블)
├── StatRow (HP)      — 현재값 | 화살표 + delta | 신규값
├── StatRow (ATK)
├── StatRow (SPD)
├── Divider
├── EffectAdded (초록 텍스트, 반복)
└── EffectRemoved (빨간 취소선 텍스트, 반복)
```

### 3. 수치 색상 규칙

```csharp
TMP_Text deltaLabel;
void SetDelta(float delta, TMP_Text label)
{
    label.text = delta >= 0 ? $"+{delta:0.#}" : $"{delta:0.#}";
    label.color = delta > 0 ? Color.green
                : delta < 0 ? Color.red
                : Color.gray;
}
```

### 4. 위치 잡기 (카드 UI 기준)

```csharp
// 카드 오른쪽 여백에 툴팁 배치, 화면 밖으로 나가면 왼쪽으로 반전
RectTransform tooltip;
RectTransform card;

void PositionTooltip()
{
    Vector3[] corners = new Vector3[4];
    card.GetWorldCorners(corners);
    float rightEdge = corners[3].x;

    if (rightEdge + tooltip.rect.width > Screen.width)
        tooltip.pivot = new Vector2(1, 0.5f);   // 왼쪽으로
    else
        tooltip.pivot = new Vector2(0, 0.5f);   // 오른쪽으로

    tooltip.position = new Vector3(rightEdge, (corners[0].y + corners[1].y) * 0.5f, 0);
}
```

### 5. 비교 없이 빈 슬롯 처리

```csharp
// current == null 이면 "신규 장착" 모드 — delta 컬럼 숨기고 효과만 표시
bool isEmptySlot = run.GetEquipped(newGear.slot) == null;
deltaColumn.SetActive(!isEmptySlot);
```

---

## OnionCat 적용 포인트

### 보상 카드 선택 (`UpgradeSelectUI`)
- 3장 카드 중 하나에 마우스 오버(또는 게임패드 선택) → 현재 해당 슬롯 장비와 비교 툴팁 표시
- 고양이·양파 카드가 동시에 표시되므로 툴팁은 **각자 카드 바깥쪽**에 배치 (화면 중앙 침범 금지)

### 상점 구매 확인 팝업
- "구매?" 팝업에 간략 비교(HP·ATK delta + 새 효과 하나) 인라인 표시
- 상세 툴팁은 R키 또는 패드 Y로 토글 — 빠른 구매도 지원

### 전투방 드롭 HUD 알림
- 화면 위 알림에 `+HP 5 | 새 효과: 화상` 한 줄 요약 → 전투 중에도 즉시 판단 가능
- 빈 슬롯이면 "신규 장착" 표시, 같은 장비면 "Lv 업" 표시

### 세트 효과 변화 표시
- 새 장비로 세트 수가 늘거나 줄면 `☀ 햇살 4 → 달성!` 또는 `💨 바람 2 → 1` 한 줄 추가
- `PassiveHost.Recalculate` 시뮬레이션을 실제 장착 전에 호출해 미리 계산

### GearScreen 효과 갈아끼우기
- 현재 슬롯 효과와 교체 후보 효과의 능력치 영향 비교
- 세트 수 변화를 강조(노란 하이라이트) — 세트 달성 여부가 핵심 판단 기준이므로

---

## 참고 링크

- Unity UI Layout: https://docs.unity3d.com/Manual/UIE-Layout-Engine.html
- ContentSizeFitter: https://docs.unity3d.com/Packages/com.unity.ugui@2.0/manual/script-ContentSizeFitter.html
- TextMeshPro Rich Text: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/RichText.html
- Hades 장비 비교 UI 분석: https://www.gamedeveloper.com/design/how-hades-minimizes-menu-interruptions
