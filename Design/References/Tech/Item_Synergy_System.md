# 아이템 시너지 시스템 (Item Synergy System)

리서치 날짜: 2026-07-27

## 개요

시너지 시스템이란 **2개 이상의 아이템·업그레이드를 동시에 보유할 때 추가 효과가 발동**하는 메카닉이다. Binding of Isaac, Enter the Gungeon, Hades 등 거의 모든 성공적인 로그라이크가 채용하며, 빌드 조합의 깊이와 발견의 기쁨을 만드는 핵심 시스템이다. OnionCat에서는 P1(근접)과 P2(원거리)의 업그레이드가 서로 상호작용하여 협력의 필요성을 시스템적으로 강화할 수 있다.

---

## 시너지 설계 분류

### 1. 같은 아이템 스택 시너지
- 같은 업그레이드를 n번 선택하면 추가 효과
- Vampire Survivors / Magic Survival 방식
- 구현 난이도: 낮음
- 예시: "원거리 데미지 +20%" 3회 → "탄속 +50%" 보너스

### 2. 태그 기반 시너지 (권장)
- 아이템에 태그(Tag)를 부여하고, 특정 태그 조합을 감지
- Binding of Isaac 방식
- 예시: `[FIRE]` 태그 아이템 + `[AREA]` 태그 아이템 → 화염 범위 공격
- 구현 난이도: 중간
- 장점: 시너지 수가 아이템 수 × 태그 수로 조합 폭발적 증가

### 3. 명시적 페어 시너지
- 정확히 아이템 A + 아이템 B 조합을 하드코딩
- Enter the Gungeon 방식 (일부)
- 구현 난이도: 낮음 (초기 개발에 적합)
- 단점: 아이템이 많아지면 유지보수 어려움

### 4. 크로스플레이어 시너지 (OnionCat 특화)
- P1 업그레이드 + P2 업그레이드 조합 감지
- 협력을 시스템 수준에서 강제
- 예시: P1 "참격 크기 +50%" + P2 "적 둔화" → "둔화된 적 받는 데미지 +30%"

---

## Unity 구현 방법

### Step 1: 아이템 ScriptableObject 설계

```csharp
// ItemData.cs
[CreateAssetMenu(menuName = "OnionCat/Item")]
public class ItemData : ScriptableObject
{
    public string itemId;
    public string displayName;
    public Sprite icon;
    public ItemTag[] tags;           // 태그 배열
    public ItemEffect[] effects;     // 기본 효과
    public PlayerRole owner;         // CAT / CROP / BOTH
}

public enum ItemTag { FIRE, ICE, AREA, PROJECTILE, MELEE, SHIELD, SPEED }
public enum PlayerRole { CAT, CROP, BOTH }
```

### Step 2: 시너지 정의 ScriptableObject

```csharp
// SynergyData.cs
[CreateAssetMenu(menuName = "OnionCat/Synergy")]
public class SynergyData : ScriptableObject
{
    public string synergyId;
    public string displayName;
    
    // 조건: 필요 아이템 ID (명시적 페어)
    public string[] requiredItemIds;
    
    // 조건: 필요 태그 (태그 기반)
    public ItemTag[] requiredTags;
    
    public ItemEffect synergyEffect;
    public bool isCrossPlayerSynergy;  // P1+P2 조합 여부
}
```

### Step 3: 시너지 감지 매니저

```csharp
// SynergyManager.cs
public class SynergyManager : MonoBehaviour
{
    [SerializeField] private SynergyData[] allSynergies;
    
    private List<string> p1ItemIds = new List<string>();
    private List<string> p2ItemIds = new List<string>();
    private List<ItemTag> p1Tags = new List<ItemTag>();
    private List<ItemTag> p2Tags = new List<ItemTag>();
    
    private List<SynergyData> activeSynergies = new List<SynergyData>();
    
    public void OnItemPickedUp(ItemData item, PlayerRole role)
    {
        if (role == PlayerRole.CAT)
        {
            p1ItemIds.Add(item.itemId);
            foreach (var tag in item.tags) p1Tags.Add(tag);
        }
        else
        {
            p2ItemIds.Add(item.itemId);
            foreach (var tag in item.tags) p2Tags.Add(tag);
        }
        
        CheckAllSynergies();
    }
    
    private void CheckAllSynergies()
    {
        foreach (var synergy in allSynergies)
        {
            if (activeSynergies.Contains(synergy)) continue;
            
            if (IsSynergyMet(synergy))
            {
                ActivateSynergy(synergy);
            }
        }
    }
    
    private bool IsSynergyMet(SynergyData synergy)
    {
        // 명시적 ID 체크
        foreach (var id in synergy.requiredItemIds)
        {
            bool inP1 = p1ItemIds.Contains(id);
            bool inP2 = p2ItemIds.Contains(id);
            if (!inP1 && !inP2) return false;
        }
        
        // 태그 체크
        List<ItemTag> allTags = new List<ItemTag>(p1Tags);
        allTags.AddRange(p2Tags);
        foreach (var tag in synergy.requiredTags)
        {
            if (!allTags.Contains(tag)) return false;
        }
        
        // 크로스플레이어 시너지: P1과 P2 양쪽에 태그 있어야 함
        if (synergy.isCrossPlayerSynergy)
        {
            foreach (var tag in synergy.requiredTags)
            {
                if (!p1Tags.Contains(tag) || !p2Tags.Contains(tag)) return false;
            }
        }
        
        return true;
    }
    
    private void ActivateSynergy(SynergyData synergy)
    {
        activeSynergies.Add(synergy);
        synergy.synergyEffect.Apply();
        // 시너지 발동 알림 UI 이벤트
        EventBus.Publish(new SynergyActivatedEvent(synergy));
    }
}
```

### Step 4: 업그레이드 선택 화면에 시너지 힌트 표시

```csharp
// UpgradeCardUI.cs
private void ShowSynergyHint(ItemData item)
{
    // 현재 보유 아이템과 조합 가능한 시너지 미리 표시
    var potentialSynergies = synergyManager.GetPotentialSynergies(item);
    if (potentialSynergies.Count > 0)
    {
        synergyHintIcon.SetActive(true);
        synergyHintText.text = $"시너지 가능: {potentialSynergies[0].displayName}";
    }
}
```

---

## 시너지 발동 연출

시너지는 "발견"이 핵심이므로 연출이 중요하다:

1. **발동 팝업**: "시너지 발동! [시너지명]" 화면 중앙에 잠깐 표시
2. **아이콘 연결 효과**: 기존 아이템 아이콘과 새 아이템 아이콘 사이에 빛나는 선
3. **사운드**: 고유한 시너지 발동음 (일반 픽업음과 다름)
4. **InGame HUD 표시**: 활성 시너지 목록을 HUD 한쪽에 표시

---

## 균형 설계 원칙

| 원칙 | 설명 |
|------|------|
| 기본 아이템은 독립적으로도 유용해야 함 | 시너지 없어도 픽업할 이유 있어야 함 |
| 시너지 효과는 덧셈보다 곱셈 | "데미지 +20"보다 "데미지 ×1.5" |
| 강한 시너지는 조건 까다롭게 | OP 조합은 두 아이템 모두 희귀(Rare/Legendary)로 제한 |
| 크로스플레이어 시너지는 일반보다 강하게 | 협력을 보상해야 함 |
| 시너지 총 개수 | 초기엔 10~20개로 시작, 아이템 추가 시 함께 확장 |

---

## OnionCat 적용 포인트

### 크로스플레이어 시너지 예시
| P1 (Cat) 업그레이드 | P2 (Crop) 업그레이드 | 시너지 효과 |
|---------------------|----------------------|-------------|
| 참격 범위 +50% | 투사체 둔화 | 둔화된 적에게 참격 데미지 2배 |
| 대시 쿨다운 -30% | 방패 방어력 +40% | 대시 직후 2초간 방패 무적 |
| 히트스톱 +0.1초 | 연속 발사 | 히트스톱 중 Crop 탄속 2배 |

### 구현 우선순위
1. 명시적 페어 시너지 5개 먼저 구현 (빠른 검증)
2. 태그 시스템 도입 (확장성)
3. 크로스플레이어 시너지 추가 (OnionCat 정체성)
4. 업그레이드 선택 화면에 시너지 힌트 표시

---

## 참고 링크

- Unity ScriptableObject: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Binding of Isaac 시너지 위키: https://bindingofisaacrebirth.fandom.com/wiki/Synergies
- GDC Talk (Vault of the Void 시너지 설계): https://www.youtube.com/watch?v=GDynomeKGKo
- 유니티 이벤트 시스템: https://docs.unity3d.com/Manual/UnityEvents.html
