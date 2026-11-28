# Crop / Resource Growth System

리서치 날짜: 2026-11-28

## 개요

작물·식물 성장 메카닉은 "시간 또는 행동 → 가시적 변화 → 보상"의 사이클을 게임에 더한다.
Stardew Valley, Atomicrops, Turnip Boy 등 다양한 게임에서 쓰이며, 특히 로그라이크와 결합하면
"런 내 성장"과 "런 간 성장(메타)"의 두 레이어를 동시에 느끼게 할 수 있다.

OnionCat은 이미 작물(CropData)이 등의 화분에 담긴 형태로 존재하며,
런 내에서 무기·스킬로 작동하는 작물이 시각적으로 "성장하는 느낌"을 줄 수 있는 구조.

## 주요 패턴

### 1. 단계별 성장 (Stage Growth)
가장 단순한 형태. 카운터가 채워질 때마다 외형·성능 변화.

```
씨앗(0) → 새싹(1) → 성체(2) → 꽃(3) → 열매(4)
```

- 카운터 조건: 적 처치 수, 방 클리어 수, 경과 시간, 획득 아이템 수
- 각 단계에서 스프라이트 교체 (또는 파티클/크기 변경)
- 선택지: 단순 비주얼 vs. 단계마다 성능 변화

```csharp
// Unity 예시 — CropGrowth 컴포넌트
public class CropGrowth : MonoBehaviour
{
    [SerializeField] private Sprite[] growthStages;  // 0=씨앗 ~ 4=열매
    [SerializeField] private SpriteRenderer cropRenderer;

    private int _stage;
    private int _killCount;

    public void OnEnemyKilled()
    {
        _killCount++;
        int newStage = Mathf.Min(_killCount / 5, growthStages.Length - 1);  // 5마리마다 성장
        if (newStage != _stage)
        {
            _stage = newStage;
            cropRenderer.sprite = growthStages[_stage];
            // 성장 이펙트 재생
        }
    }
}
```

### 2. 연속 성장 (Continuous Growth)
실시간으로 조금씩 커지는 시각 효과. Scale이나 Atlas UV 애니메이션으로 구현.

```csharp
// 런 내 보스 처치마다 작물이 조금씩 커지는 예시
void GrowOnBossKill()
{
    var target = cropTransform.localScale + Vector3.one * 0.1f;
    DOTween.Kill(cropTransform);
    cropTransform.DOScale(target, 0.5f).SetEase(Ease.OutElastic);
}
```

### 3. 조건부 개화 (Conditional Bloom)
특정 조건(세트 보너스 활성화, 합동기 발동 등)에 반응해 꽃이 피거나 빛나는 연출.

```csharp
// 세트 보너스 2단계 활성화 시 작물 꽃 연출
void OnSetBonusActivated(SetId set, int tier)
{
    if (tier >= 2)
        PlayBloomAnimation();  // 꽃잎 파티클 + 스프라이트 교체
}
```

### 4. 작물별 고유 자원 (Resource Generation)
각 작물이 고유한 자원을 생성하는 시스템. Stardew의 작물→가공품 개념.

```csharp
// CropData에 자원 생성 정의
[CreateAssetMenu]
public class CropData : ScriptableObject
{
    public Color lightColor;         // 메타 빛 색깔 (스토리 퀘스트용)
    public float resourcePerKill;    // 적 처치마다 생성되는 자원량
    public GameObject uniqueAbility; // R키 고유기 프리팹
    public Sprite[] growthSprites;   // 성장 단계 스프라이트
}
```

### 5. 반복 수확 (Recurring Harvest)
일정 주기마다 보너스를 주는 시스템. Stardew의 "고대 과일" 아이디어.

```csharp
// N번째 적 처치마다 씨앗 한 개 자동 획득
private int _killSinceLastHarvest;
void OnKill()
{
    _killSinceLastHarvest++;
    if (_killSinceLastHarvest >= harvestInterval)
    {
        _killSinceLastHarvest = 0;
        GameManager.Instance.Run.AddSeed(cropData.defaultSeed, 1);
        PlayHarvestFX();
    }
}
```

## OnionCat 적용 포인트

### 작물 시각적 성장 (즉시 적용 가능)
현재 `CatArtRenderer`에 `attachment_config.json` 소켓이 있어 작물 외형 변경이 가능.
런 내에서 작물이 성장하는 느낌을 주는 단계적 스프라이트 교체:
- **보스 처치마다 성장**: 보스 1마리 → 꽃봉오리, 보스 2마리 → 꽃 핌, 보스 3마리 → 열매 맺음
- 성장 단계를 `RunData`에 저장 → 런 중 씬 전환 후에도 유지
- 성장 단계가 올라갈 때 짧은 파티클 + 소리 → 성취감 강화

```csharp
// RunData에 추가
public int CropGrowthStage { get; private set; }

public void OnBossDefeated()
{
    CropGrowthStage = Mathf.Min(CropGrowthStage + 1, 3);
    CropGrowthStageChanged?.Invoke(CropGrowthStage);
}
```

### 작물별 메타 빛 생성
현재 `LightColor`가 판마다 쌓이는 구조.
더 나아가 "런 내에 더 많은 적을 잡을수록 더 많은 빛"을 모을 수 있는 시스템으로:
- `RunData.lightAmount += cropData.lightPerKill * damageDealt`
- 마을 등불에 비출 때 양이 더 많으면 "더 밝게 타는" 연출

### 스테이지 테마 × 작물 조합
Stardew의 계절×작물 조합처럼, OnionCat의 스테이지 테마×작물 조합으로 시너지:
- 밀밭 테마 + 해바라기: 햇빛 광선이 더 넓게 (초목 많은 환경)
- 등대 테마 + 푸른 버섯: 독 연기가 어두운 공간에서 더 잘 보임
- 이를 패시브 `CombatModifiers`에 반영 (스테이지 테마 조건 추가)

### 온실 비주얼
온실 화면(`GreenhouseScreen`)에서 해금된 작물을 화분에 실제로 심어 보여주는 연출:
- 해금 전: 빈 화분 또는 흙
- 해금 후: 작물이 자라고 있는 모습
- 클릭하면 그 작물로 다음 판을 시작하는 선택

## 참고 링크

- Stardew Valley 위키 - Crops: https://stardewvalleywiki.com/Crops
- Atomicrops (전투 × 농사 로그라이크): https://store.steampowered.com/app/1062140/Atomicrops/
- Turnip Boy Commits Tax Evasion (채소 성장 판타지): https://store.steampowered.com/app/1205450/
- Unity DOTween (성장 애니메이션용): https://dotween.demigiant.com/
- Unity ScriptableObject 패턴: https://docs.unity3d.com/Manual/class-ScriptableObject.html
