# Persistent Overworld Visual Progression

리서치 날짜: 2026-11-11

## 개요

허브 세계(메인 메뉴, 마을, 농장 등)가 **이야기 진행에 따라 시각적으로 변화**하는 시스템.
판마다 같은 장소에 돌아왔을 때 "변화가 있다"는 것을 느끼게 해 메타 진행감을 준다.

OnionCat과의 관련성:
- `MetaProgress.Chapter` 1~4에 따라 농장·마을·등대 입구의 모습이 달라짐
- 첫 판 → 완성된 엔딩 사이에 세계가 조금씩 변화 → 반복 플레이의 보람

참고 사례:
- **Hades**: 판마다 NPC 위치·대사·관계 변화, 채석장이 조금씩 개방
- **Cult of the Lamb**: 추종자 수 증가 → 마을 규모가 눈에 보이게 성장
- **Rogue Legacy 2**: 금고 쌓임 → 성 외관 변화
- **Dreamscaper**: 현실 세계 NPC 관계도가 변화하며 아파트 풍경 달라짐

---

## 핵심 개념

### 단계적 외관 변화 방식 3가지

| 방식 | 설명 | 적합한 경우 |
|------|------|-----------|
| 스프라이트 교체 | 단계별 다른 스프라이트 | 큰 변화, 픽셀아트에 적합 |
| 오브젝트 활성화 | 특정 조건에서 오브젝트 On/Off | 새 NPC 등장, 아이템 추가 |
| 셰이더/컬러 변환 | 색상·명도 조정 | 분위기 변화 (어두워지거나 밝아지기) |

OnionCat 같은 2D 픽셀아트에서는 **스프라이트 교체 + 오브젝트 활성화** 조합이 가장 단순하고 효과적.

---

## Unity 구현 방법

### 1. 진행 상태 데이터 (기존 MetaProgress 활용)

```csharp
// MetaProgress.cs (기존)
public class MetaProgressData
{
    public int   Chapter;          // 1~4
    public bool  WitchFreed;
    public int   LanternLight;     // 등불에 모인 빛 양
    // ...
}
```

### 2. 시각 변화 정의 — ScriptableObject

```csharp
[CreateAssetMenu(menuName = "OnionCat/WorldVisualState")]
public class WorldVisualState : ScriptableObject
{
    [System.Serializable]
    public struct VisualCondition
    {
        public int     minChapter;      // 이 Chapter 이상이면 활성화
        public bool    requireWitch;    // WitchFreed 조건
        public Sprite  backgroundSprite;
        public string  activateObjectName;   // 활성화할 자식 오브젝트 이름
        public string  deactivateObjectName; // 비활성화할 자식 오브젝트 이름
        public Color   ambientTint;
    }

    public List<VisualCondition> conditions;
}
```

### 3. 허브 씬 적용 컴포넌트

```csharp
public class WorldVisualApplier : MonoBehaviour
{
    [SerializeField] private WorldVisualState visualState;
    [SerializeField] private SpriteRenderer   backgroundRenderer;

    private void OnEnable()
    {
        Apply(MetaProgress.data);
    }

    public void Apply(MetaProgressData progress)
    {
        foreach (var cond in visualState.conditions)
        {
            bool meets = progress.Chapter >= cond.minChapter
                      && (!cond.requireWitch || progress.WitchFreed);

            if (meets)
            {
                if (cond.backgroundSprite != null)
                    backgroundRenderer.sprite = cond.backgroundSprite;

                if (!string.IsNullOrEmpty(cond.activateObjectName))
                {
                    var obj = transform.Find(cond.activateObjectName);
                    if (obj) obj.gameObject.SetActive(true);
                }

                if (!string.IsNullOrEmpty(cond.deactivateObjectName))
                {
                    var obj = transform.Find(cond.deactivateObjectName);
                    if (obj) obj.gameObject.SetActive(false);
                }

                if (cond.ambientTint != Color.clear)
                    backgroundRenderer.color = cond.ambientTint;
            }
        }
    }
}
```

### 4. 첫 방문 감지 — 변화 연출 추가

```csharp
public class WorldChangePresenter : MonoBehaviour
{
    [SerializeField] private float fadeDuration = 0.5f;

    private int lastChapterSeen;

    private void Start()
    {
        lastChapterSeen = PlayerPrefs.GetInt("LastChapterSeen", 0);
        int current     = MetaProgress.data.Chapter;

        if (current > lastChapterSeen)
        {
            StartCoroutine(RevealChange());
            PlayerPrefs.SetInt("LastChapterSeen", current);
        }
    }

    private IEnumerator RevealChange()
    {
        // 1. 화면 잠깐 어둡게
        yield return FadeOut(fadeDuration);

        // 2. 새 비주얼 적용
        GetComponent<WorldVisualApplier>().Apply(MetaProgress.data);

        // 3. 다시 밝아지며 플레이어가 변화를 발견
        yield return FadeIn(fadeDuration);
    }
}
```

### 5. 간단한 오브젝트 풀 활용 (NPC 등장)

```csharp
// 판 클리어 후 처음 농장에 돌아왔을 때 말하는 책이 새 위치에
public class FarmNPCSpawner : MonoBehaviour
{
    [SerializeField] private GameObject bookNPC;
    [SerializeField] private Transform[] spawnPositions;  // 단계별 위치

    private void OnEnable()
    {
        int chapter = MetaProgress.data.Chapter;
        if (chapter >= 1 && chapter < spawnPositions.Length)
            bookNPC.transform.position = spawnPositions[chapter].position;
        
        bookNPC.SetActive(chapter >= 1);
    }
}
```

### 6. 등불 빛 색 시각화 (OnionCat 고유)

```csharp
public class LanternVisual : MonoBehaviour
{
    [SerializeField] private SpriteRenderer lanternGlow;
    [SerializeField] private Gradient       lightColorByProgress;

    private void OnEnable()
    {
        float t = MetaProgress.data.LanternLight / (float)StoryRoute.MaxLight;
        lanternGlow.color = lightColorByProgress.Evaluate(t);
        lanternGlow.gameObject.SetActive(t > 0f);
    }
}
```

---

## OnionCat 적용 포인트

### 단계별 변화 계획 (MetaProgress.Chapter 기준)

| Chapter | 농장 | 마을 | 등대 입구 |
|---------|------|------|----------|
| 0 (시작) | 말하는 책 혼자, 화분 비어있음 | - | - |
| 1 (1스테이지 클리어) | 화분에 싹 | 등불 첫 빛 (희미) | 문 보임 |
| 2 (2스테이지 클리어) | 화분 작물 자람 | 마을 집 1~2채 추가 | 등대 더 밝아짐 |
| 3 (마녀 해방) | 그리모가 말하는 책 대신 등장 | 마을 주민 추가 | 문 활짝 열림 |
| 4 (엔딩) | 꽃 가득, 밝은 색조 | 마을 완성, 등불 최대 | 등대 빛 최대 |

### 구현 우선순위
1. **즉시**: `WorldVisualApplier` + 농장 배경 2가지(시작/1장 이후) ScriptableObject 제작
2. **다음 스프린트**: 등불 빛 색 시각화 (등불 그림 필요)
3. **추후**: 마을 단계별 변화 (마을 그림이 여러 장 필요)

### 주의사항
- 단계별 스프라이트를 사람(아티스트)이 그려야 함 → 먼저 코드 구조만 짜두고 나중에 채우기
- `MetaProgress.data`가 `meta.json`에 저장되므로 테스트 후 반드시 되돌릴 것 (CLAUDE.md 규칙)
- 처음 변화를 발견하는 연출(페이드, 감탄 대사)이 없으면 플레이어가 눈치 못 챌 수 있음

---

## 참고 링크

- Hades 환경 반응 디자인 분석: https://www.gamedeveloper.com/design/how-supergiant-made-the-world-of-hades-feel-alive
- Cult of the Lamb 메타 진행 UX: https://www.youtube.com/watch?v=cult_lamb_devlog (공식 채널)
- Unity ScriptableObject 기반 게임 상태: https://unity.com/resources/create-modular-game-architecture-with-scriptable-objects-ebook
- 나무위키 Hades 하데스 성장 시스템: https://namu.wiki/w/하데스(게임)
