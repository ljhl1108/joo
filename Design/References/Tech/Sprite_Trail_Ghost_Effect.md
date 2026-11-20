# Sprite Trail / Ghost Echo Effect

리서치 날짜: 2026-11-20

## 개요

캐릭터가 빠르게 이동할 때 뒤에 잔상(ghost echo)을 남기는 시각 효과.
대쉬, 가속 버프, 특수 공격 돌진, 하이퍼 모드 등에 활용하며 **"빠르다"는 느낌을 시각적으로 증폭**시킨다.

OnionCat 적용 대상: 고양이 대쉬, 야성 특수 공격 돌진, 작물의 에너지 충전 중 연출.

---

## Unity 구현 방법

### 방법 A: SpriteRenderer 복사 + 알파 페이드 (가장 단순)

```csharp
public class SpriteTrail : MonoBehaviour
{
    [SerializeField] SpriteRenderer source;
    [SerializeField] float interval = 0.04f;   // 잔상 생성 간격
    [SerializeField] float lifetime  = 0.25f;  // 잔상 하나가 사라지는 시간
    [SerializeField] Color tintColor = new Color(0.6f, 0.8f, 1f, 1f); // 파란 잔상

    Coroutine _loop;

    public void StartTrail() => _loop = StartCoroutine(SpawnLoop());
    public void StopTrail()  { if (_loop != null) StopCoroutine(_loop); _loop = null; }

    IEnumerator SpawnLoop()
    {
        while (true)
        {
            Spawn();
            yield return new WaitForSeconds(interval);
        }
    }

    void Spawn()
    {
        // 오브젝트 풀에서 꺼내는 게 맞지만 간단 버전
        var go = new GameObject("Trail");
        go.transform.SetPositionAndRotation(source.transform.position, source.transform.rotation);
        go.transform.localScale = source.transform.lossyScale;

        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite        = source.sprite;
        sr.sortingOrder  = source.sortingOrder - 1;
        sr.flipX         = source.flipX;
        sr.color         = tintColor;

        StartCoroutine(FadeOut(sr, go, lifetime));
    }

    IEnumerator FadeOut(SpriteRenderer sr, GameObject go, float duration)
    {
        float elapsed = 0f;
        Color start   = sr.color;
        while (elapsed < duration)
        {
            elapsed    += Time.deltaTime;
            float a     = Mathf.Lerp(start.a, 0f, elapsed / duration);
            sr.color    = new Color(start.r, start.g, start.b, a);
            yield return null;
        }
        Destroy(go);
    }
}
```

사용:
```csharp
// 대쉬 시작할 때
trail.StartTrail();
// 대쉬 끝날 때
trail.StopTrail();
```

### 방법 B: MaterialPropertyBlock으로 색상 주입 (드로우콜 절약)

여러 잔상이 한 번에 화면에 있을 때 각각 다른 `Material` 인스턴스를 만들면 드로우콜 폭발.
`MaterialPropertyBlock`을 쓰면 같은 Material을 공유하면서 색상만 다르게 가능.

```csharp
var mpb = new MaterialPropertyBlock();
sr.GetPropertyBlock(mpb);
mpb.SetColor("_Color", tintColor);
sr.SetPropertyBlock(mpb);
```

### 방법 C: 오브젝트 풀 연동 (권장)

OnionCat에는 `PoolManager.Spawn/Despawn`이 있으므로 잔상 오브젝트도 풀에서 가져오는 게 맞음.

```csharp
// TrailGhost 프리팹에 아래 컴포넌트
public class TrailGhost : MonoBehaviour, IPoolable
{
    SpriteRenderer sr;
    MaterialPropertyBlock mpb;

    void Awake()
    {
        sr  = GetComponent<SpriteRenderer>();
        mpb = new MaterialPropertyBlock();
    }

    public void Init(Sprite sprite, Color tint, int sortOrder, bool flipX, float lifetime)
    {
        sr.sprite       = sprite;
        sr.sortingOrder = sortOrder - 1;
        sr.flipX        = flipX;
        mpb.SetColor("_Color", tint);
        sr.SetPropertyBlock(mpb);
        StartCoroutine(FadeAndReturn(lifetime));
    }

    IEnumerator FadeAndReturn(float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float a  = Mathf.Lerp(1f, 0f, elapsed / duration);
            mpb.SetFloat("_Alpha", a);  // 셰이더가 _Alpha를 쓰거나 _Color.a를 갱신
            sr.SetPropertyBlock(mpb);
            yield return null;
        }
        PoolManager.Despawn(gameObject);
    }

    void OnEnable()  { /* 초기화 */ }
    void OnDisable() { StopAllCoroutines(); }
}
```

### 방법 D: Shader Graph로 색상·디졸브 효과

단순 알파 페이드 대신 디졸브(noisy dissolve) 셰이더를 사용하면 픽셀아트 느낌의 잔상이 가능:
- Noise 텍스처로 마스킹 임계값을 낮춰가며 사라지게
- URP 2D에서 Shader Graph: `Sprite Unlit` → `Step(noise, threshold)` → `Alpha Clip`
- `threshold`를 0→1로 올리면 잔상이 불규칙하게 사라짐

---

## 픽셀아트 주의사항

- 잔상 오브젝트의 PPU가 원본과 같아야 하므로 **원본 SpriteRenderer의 `transform.lossyScale`** 그대로 복사
- 잔상 위치는 **WorldSpace 기준** — localPosition 복사 금지 (부모가 다름)
- 정렬 순서: 원본보다 1~2 낮게 (`sortingOrder - 1`). YSort가 붙어 있으면 잔상 오브젝트에서는 YSort를 비활성화

---

## OnionCat 적용 포인트

### 고양이 대쉬 잔상

```csharp
// CatController.Dash()
trail.StartTrail();
// 대쉬 완료 콜백
trail.StopTrail();
```

- 색상: `new Color(0.5f, 0.7f, 1f, 0.8f)` (옅은 파랑) — 무적 상태임을 시각적으로 암시
- 간격: 0.03초 (60fps 기준 약 2프레임마다)
- 수명: 0.2초 (짧고 선명하게)

### 야성 특수 공격 돌진

- 색상: `new Color(1f, 0.6f, 0.2f, 0.9f)` (주황/불꽃) — 야성 게이지 색에 맞춤
- 간격: 0.02초
- 수명: 0.3초 (공격적이므로 조금 더 길게)
- `HitFeelSettings.asset`에 Trail 간격·수명·색상 넣어두면 플레이 중 조절 가능

### 사용처 체크리스트

| 상황 | 색상 | 간격 | 수명 |
|---|---|---|---|
| 대쉬 무적 중 | 파랑 | 0.03s | 0.2s |
| 야성 돌진 | 주황 | 0.02s | 0.3s |
| 패링 성공 직후 고양이 반동 | 흰색 플래시 1회 | — | 0.1s |
| 가속 버프 장비 효과 중 | 연두색 | 0.05s | 0.15s |

---

## 참고 링크

- Unity 공식(Trail Renderer): https://docs.unity3d.com/Manual/class-TrailRenderer.html
- SpriteRenderer + PropertyBlock 패턴: https://docs.unity3d.com/ScriptReference/MaterialPropertyBlock.html
- 픽셀아트 대쉬 잔상 튜토리얼: https://www.youtube.com/watch?v=MhzwB3Zg5ro (Sasquatch B Studios)
- URP 2D Dissolve Shader Graph: https://docs.unity3d.com/Packages/com.unity.shadergraph@latest
