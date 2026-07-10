# Cosmetic Skin System

리서치 날짜: 2026-07-10

## 개요

**코스메틱 스킨 시스템**은 캐릭터의 외형(색상, 스프라이트 등)을 변경할 수 있는 게임플레이에 영향을 주지 않는 꾸미기 기능이다. 업적 달성·런 완료 등의 조건으로 스킨을 해금하면 플레이어에게 장기적 목표와 수집 욕구를 제공한다. OnionCat에서는 고양이와 양파 각각의 색상 팔레트를 교체하는 형태로 구현할 수 있다.

---

## Unity 구현 방법

### 1. 스킨 데이터 구조 (ScriptableObject)

```csharp
// SkinData.cs
using UnityEngine;

[CreateAssetMenu(fileName = "NewSkin", menuName = "OnionCat/SkinData")]
public class SkinData : ScriptableObject
{
    public string skinId;           // 저장키 식별자 ("skin_golden_cat")
    public string displayName;      // "황금 고양이"
    public Sprite previewSprite;    // UI 미리보기용 스프라이트
    public Color primaryColor;      // 주 색상 (SpriteRenderer.color 적용)
    public Color secondaryColor;    // 보조 색상 (세부 파츠용)
    public bool isDefaultSkin;      // 기본 스킨 여부
}
```

### 2. 스킨 해금 상태 저장 (PlayerPrefs 기반)

```csharp
// SkinManager.cs
using UnityEngine;
using System.Collections.Generic;

public class SkinManager : MonoBehaviour
{
    public static SkinManager Instance { get; private set; }

    [SerializeField] private SkinData[] allSkins;
    [SerializeField] private SkinData defaultCatSkin;
    [SerializeField] private SkinData defaultOnionSkin;

    private const string CAT_SKIN_KEY = "selected_cat_skin";
    private const string ONION_SKIN_KEY = "selected_onion_skin";
    private const string UNLOCKED_PREFIX = "skin_unlocked_";

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public bool IsSkinUnlocked(SkinData skin)
    {
        if (skin.isDefaultSkin) return true;
        return PlayerPrefs.GetInt(UNLOCKED_PREFIX + skin.skinId, 0) == 1;
    }

    public void UnlockSkin(SkinData skin)
    {
        PlayerPrefs.SetInt(UNLOCKED_PREFIX + skin.skinId, 1);
        PlayerPrefs.Save();
    }

    public SkinData GetSelectedCatSkin()
    {
        string id = PlayerPrefs.GetString(CAT_SKIN_KEY, defaultCatSkin.skinId);
        return FindSkinById(id) ?? defaultCatSkin;
    }

    public SkinData GetSelectedOnionSkin()
    {
        string id = PlayerPrefs.GetString(ONION_SKIN_KEY, defaultOnionSkin.skinId);
        return FindSkinById(id) ?? defaultOnionSkin;
    }

    public void SelectCatSkin(SkinData skin)
    {
        if (!IsSkinUnlocked(skin)) return;
        PlayerPrefs.SetString(CAT_SKIN_KEY, skin.skinId);
        PlayerPrefs.Save();
    }

    public void SelectOnionSkin(SkinData skin)
    {
        if (!IsSkinUnlocked(skin)) return;
        PlayerPrefs.SetString(ONION_SKIN_KEY, skin.skinId);
        PlayerPrefs.Save();
    }

    private SkinData FindSkinById(string id)
    {
        foreach (var skin in allSkins)
            if (skin.skinId == id) return skin;
        return null;
    }
}
```

### 3. 캐릭터에 스킨 적용

```csharp
// CharacterSkinApplier.cs
using UnityEngine;

public class CharacterSkinApplier : MonoBehaviour
{
    public enum CharacterType { Cat, Onion }
    [SerializeField] private CharacterType characterType;
    [SerializeField] private SpriteRenderer mainRenderer;
    [SerializeField] private SpriteRenderer detailRenderer; // 보조 파츠 (선택)

    private void Start()
    {
        ApplySkin();
    }

    public void ApplySkin()
    {
        if (SkinManager.Instance == null) return;

        SkinData skin = characterType == CharacterType.Cat
            ? SkinManager.Instance.GetSelectedCatSkin()
            : SkinManager.Instance.GetSelectedOnionSkin();

        if (mainRenderer != null)
            mainRenderer.color = skin.primaryColor;

        if (detailRenderer != null)
            detailRenderer.color = skin.secondaryColor;
    }
}
```

### 4. 팔레트 스왑 쉐이더 방식 (고급, 픽셀아트 권장)

SpriteRenderer.color는 전체 색조(Tint) 변경이라 픽셀아트에서 부자연스러울 수 있다.
완전한 팔레트 교체가 필요하다면 커스텀 쉐이더를 사용:

```
방법 1: Unity Shader Graph에서 PaletteSwap 쉐이더 제작
  - 입력: Original Palette Texture, Target Palette Texture
  - 픽셀별 원본 색상 → 매핑 색상으로 교체
  - 각 스킨마다 "Target Palette Texture" 1장으로 관리

방법 2: Asset Store 무료 에셋 활용
  - "Sprite Color FX" 또는 "2D Sprite Palette Swap" 에셋 검색
```

### 5. 스킨 선택 UI 기본 구조

```
[SkinSelectPanel]
  ├── ScrollView (Horizontal)
  │   └── SkinGrid
  │       ├── SkinSlot (SkinData별 1개)
  │       │   ├── PreviewImage (미리보기)
  │       │   ├── SkinNameText
  │       │   └── LockOverlay (잠금 상태 시 표시)
  └── ConfirmButton
```

```csharp
// SkinSlotUI.cs
public class SkinSlotUI : MonoBehaviour
{
    [SerializeField] private Image previewImage;
    [SerializeField] private TMP_Text nameText;
    [SerializeField] private GameObject lockOverlay;
    [SerializeField] private Button selectButton;

    private SkinData skinData;

    public void Setup(SkinData data)
    {
        skinData = data;
        previewImage.sprite = data.previewSprite;
        nameText.text = data.displayName;

        bool unlocked = SkinManager.Instance.IsSkinUnlocked(data);
        lockOverlay.SetActive(!unlocked);
        selectButton.interactable = unlocked;
    }
}
```

### 6. 스킨 해금 조건 연결

```csharp
// 업적 달성 시 호출 예시
public void OnRunClearFirst()
{
    // 첫 런 클리어 스킨 해금
    SkinData rewardSkin = Resources.Load<SkinData>("Skins/GoldenCat");
    if (rewardSkin != null)
        SkinManager.Instance.UnlockSkin(rewardSkin);
}
```

---

## OnionCat 적용 포인트

### 스킨 기획 아이디어

**고양이 스킨 (Player 1)**
| 스킨 이름 | 색상 | 해금 조건 |
|---|---|---|
| 기본 오렌지 고양이 | 주황 | 기본 제공 |
| 흑묘 | 검정 | 첫 런 클리어 |
| 황금 고양이 | 금색 | 10런 완료 |
| 유령 고양이 | 반투명 흰색 | 사망 50회 |
| 닌자 고양이 | 짙은 파랑 | 보스 노 데미지 |

**양파 스킨 (Player 2)**
| 스킨 이름 | 색상 | 해금 조건 |
|---|---|---|
| 기본 초록 양파 | 초록 | 기본 제공 |
| 자색 양파 | 보라 | 첫 런 클리어 |
| 황금 양파 | 금색 | 10런 완료 |
| 불꽃 양파 | 빨강 | 원거리 1000발 발사 |

### 구현 순서 (초보자 권장)

1. SkinData ScriptableObject 생성 및 기본 스킨 3~4개 제작
2. SkinManager 싱글톤 구현 + PlayerPrefs 저장
3. CharacterSkinApplier 캐릭터 오브젝트에 부착
4. 메인 메뉴에 스킨 선택 버튼 추가 (별도 패널)
5. 업적 시스템(Achievement_Stats_System)과 연결해 해금 조건 추가

### 주의사항

- 스킨은 **게임플레이에 영향 없음**을 반드시 유지 (색맹 플레이어 배려)
- PlayerPrefs Key 충돌 방지: 접두사(`skin_`, `onion_skin_`) 일관 사용
- 스킨 미리보기 스프라이트는 실제 캐릭터 스프라이트와 별도 제작 (UI 해상도 대응)
- 유니티 에디터에서 드래그 앤 드롭 설정 필요:
  - SkinManager → allSkins 배열에 모든 SkinData SO 등록
  - CharacterSkinApplier → mainRenderer에 캐릭터 SpriteRenderer 연결

---

## 참고 링크

- Unity 공식 문서 – PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Unity 공식 문서 – ScriptableObject: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Unity Forum – Palette Swap Shader for 2D Sprites: https://forum.unity.com (검색: "2D sprite palette swap shader")
- Febucci Tools – Palette Swap Shader 튜토리얼: https://www.febucci.com/2019/05/palette-swapper/
- Unity Learn – Create with Code (UI 시스템 부분): https://learn.unity.com/course/create-with-code
