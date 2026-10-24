# 모드 지원 시스템 (Mod Support for Indie Roguelikes)

리서치 날짜: 2026-10-24

## 개요
로그라이크에서 플레이어 모드(mod)는 게임 수명을 크게 늘리는 완성도 지표다. Brotato·Vampire Survivors·Risk of Rain 2 모두 활발한 모드 커뮤니티를 보유하며, 이는 재플레이 유도와 장기 판매 유지에 직결된다. Unity에서 소스코드 노출 없이 **아이템·적·밸런스 수치**를 외부에서 추가·수정하는 기본 모드 지원 구조를 구현하는 방법.

OnionCat과의 관련성:
- 이미 `ContentBuilder.cs` + ScriptableObject 기반 아키텍처 → 모드 친화적 구조의 90%가 갖춰짐
- 개발자 본인이 콘텐츠 확장 실험을 빠르게 할 "내부 모드" 도구로도 유용
- Steam Workshop 연동은 출시 후 커뮤니티 반응을 보고 결정하는 것이 현실적

---

## Unity 구현 방법

### 1단계: 수치 외부화 — balance_override.json

가장 단순하고 즉시 적용 가능한 단계. 에디터 없이 빌드 후에도 밸런스 수치를 조정.

```csharp
[Serializable]
public class BalanceOverride
{
    public float enemyHpMultiplier  = 1f;
    public float seedDropRate       = 1f;
    public float shopPriceMultiplier= 1f;
    public int   startingSeedCount  = 0;
}

public static class BalanceConfig
{
    public static BalanceOverride Current { get; private set; } = new();

    public static void Load()
    {
        var path = Path.Combine(Application.persistentDataPath, "balance_override.json");
        if (!File.Exists(path)) return;
        try
        {
            Current = JsonUtility.FromJson<BalanceOverride>(File.ReadAllText(path));
        }
        catch { /* 파싱 오류 시 기본값 유지 */ }
    }
}

// GameBootstrap.Awake() 에서 호출
BalanceConfig.Load();
```

플레이어는 `%AppData%\..\LocalLow\<Company>\<Game>\balance_override.json` 파일을 메모장으로 편집하면 됨.

### 2단계: JSON 아이템 정의 — ModGearData

```csharp
[Serializable]
public class ModGearData
{
    public string id;            // 고유 ID (중복 방지용)
    public string displayName;   // 표시 이름 (한글 가능)
    public string setName;       // 세트 이름 (기존 세트명 or 새 이름)
    public int    rarity;        // 0=common 1=rare 2=epic 3=legendary
    public float  attackBonus;   // 추가 공격력
    public string effectType;    // GearEffect 이름 (허용 목록 검증)
}

public static class ModLoader
{
    static readonly string ModDir =
        Path.Combine(Application.persistentDataPath, "Mods");

    static readonly HashSet<string> AllowedEffects = new()
    {
        "OnHitBurn", "OnHitSlow", "OnDashDamage", /* ... 허용 효과 목록 */
    };

    public static List<ModGearData> LoadAllGear()
    {
        var result = new List<ModGearData>();
        if (!Directory.Exists(ModDir)) return result;

        foreach (var file in Directory.GetFiles(ModDir, "gear_*.json"))
        {
            try
            {
                var mod = JsonUtility.FromJson<ModGearData>(File.ReadAllText(file));
                if (ValidateGear(mod)) result.Add(mod);
                else Debug.LogWarning($"[Mod] 유효하지 않은 장비: {file}");
            }
            catch (Exception e) { Debug.LogWarning($"[Mod] 파싱 오류 {file}: {e.Message}"); }
        }
        return result;
    }

    static bool ValidateGear(ModGearData mod) =>
        !string.IsNullOrEmpty(mod.id) &&
        mod.rarity is >= 0 and <= 3 &&
        mod.attackBonus is >= 0f and <= 99f &&
        (string.IsNullOrEmpty(mod.effectType) || AllowedEffects.Contains(mod.effectType));
}
```

### 3단계: RewardTable에 주입

```csharp
// GameBootstrap.Awake() — ContentBuilder로 생성한 에셋 로드 직후
foreach (var modData in ModLoader.LoadAllGear())
{
    var gear = ScriptableObject.CreateInstance<GearItem>();
    gear.name        = modData.id;
    gear.displayName = modData.displayName;
    gear.rarity      = (Rarity)modData.rarity;
    // ... 필드 설정
    RewardTable.Instance.InjectItem(gear);  // 신규 메서드 추가
}
```

### 4단계: AssetBundle로 커스텀 스프라이트 (선택)

커스텀 아이콘을 포함하는 고급 모드:

```csharp
// 모드 폴더: Mods/my_gear/assets.unity3d
var bundlePath = Path.Combine(modFolder, "assets.unity3d");
if (File.Exists(bundlePath))
{
    var bundle = AssetBundle.LoadFromFile(bundlePath);
    gear.icon = bundle.LoadAsset<Sprite>("icon");
    bundle.Unload(false); // 스프라이트만 유지, 번들 해제
}
```

**주의**: AssetBundle은 Unity 버전이 다르면 로드 실패. 번들 파일명에 Unity 버전을 포함할 것 (`assets_6000.3.unity3d`).

---

## 가벼운 대안: 개발자 전용 외부 밸런스 파일

전체 모드 지원이 부담스럽다면, 개발팀 내부용으로만 활용하는 단순한 방법:

```
Assets/Resources/BalanceDefaults.json   ← 에셋 번들에 포함 (기본값)
%AppData%/.../balance_override.json    ← 플레이어 로컬 덮어쓰기 (없으면 기본값 사용)
```

이 구조만으로도:
- 출시 후 핫픽스를 코드 변경 없이 적용 가능 (단, 서버 배포는 별도)
- QA 단계에서 밸런스 빠른 조정
- 플레이어 모딩 진입장벽 낮춤

---

## OnionCat 적용 포인트

1. **현재 구조 평가**: `ContentBuilder.cs`가 `GearItem` ScriptableObject를 생성하는 방식은 이미 모드 아키텍처의 청사진. `GearItem` 필드가 `[Serializable]`이면 JSON 역직렬화 즉시 가능.

2. **단기 실용 목표 (권장)**: `balance_override.json` 도입만으로 빌드 후 밸런스 조정 편의성 확보. OnionCat 팀 내부 플레이테스트 피드백 반영 속도 향상.

3. **중기 목표**: 장비 JSON 모드 지원 → 커뮤니티 콘텐츠 창작 유도. Steam Workshop 연동은 그 다음 단계.

4. **주의 사항**:
   - AssetBundle은 Unity 버전 종속 → 버전 관리 필수
   - 허용 효과 목록(`AllowedEffects`)을 엄격히 관리하지 않으면 밸런스 파괴 모드 가능
   - 모드로 주입된 아이템은 `GameDatabase` 이름 조회에서 누락됨 → `RunSave` 직렬화 시 예외 처리 필요

5. **OnionCat에 없는 것**: 현재 모드 폴더 탐색 로직, `RewardTable.InjectItem()` 메서드. 각 5~10줄 추가로 구현 가능.

---

## 참고 링크
- Unity AssetBundles 공식 문서: https://docs.unity3d.com/Manual/AssetBundlesIntro.html
- Unity Persistent Data Path: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Unity JsonUtility 직렬화: https://docs.unity3d.com/ScriptReference/JsonUtility.html
- BepInEx (Unity 모드 프레임워크): https://github.com/BepInEx/BepInEx — Mono 빌드에서만 안정적, IL2CPP는 추가 설정 필요
- Thunderstore Mod Manager (Risk of Rain 2, Brotato 생태계): https://www.thunderstore.io
