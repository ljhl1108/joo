# 부유 데미지 숫자 시스템 (Floating Damage Numbers)

리서치 날짜: 2026-07-11

## 개요

적을 공격했을 때 피격 지점 위로 데미지 수치가 떠오르며 사라지는 UI 이펙트.  
전투 피드백의 핵심 요소로, 플레이어가 "내 공격이 얼마나 강한지"를 즉각 인지하게 만든다.  
OnionCat에서는 **근접(고양이)와 원거리(양파) 데미지를 색상으로 구분**하고, **약점 공격 시 강조 표시**로 협동 유도 신호를 제공하는 역할을 한다.

---

## Unity 구현 방법

### 1. 기본 구조 설계

```
DamageNumberManager (싱글톤)
  └── DamageNumber (TextMeshPro + 애니메이션)
```

### 2. TextMeshPro 프리팹 구성

```
DamageNumber (GameObject)
  ├── Canvas (World Space, Sort Order 10)
  │     └── TextMeshPro - Text (UI)
  └── DamageNumberBehaviour.cs
```

Canvas 설정:
- **Render Mode**: World Space
- **Scale**: 0.01 (픽셀아트와 어울리는 작은 크기)
- **Sort Layer**: "UI" or "Effects" (항상 위에 보임)

### 3. 핵심 스크립트

```csharp
// DamageNumber.cs
using UnityEngine;
using TMPro;

public class DamageNumber : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI text;
    
    private float lifetime = 1.0f;
    private float elapsed = 0f;
    private Vector3 velocity;
    private Color startColor;

    public void Initialize(int damage, Vector3 worldPos, DamageType type)
    {
        transform.position = worldPos;
        elapsed = 0f;

        // 타입별 색상 & 크기
        (string label, Color color, float scale) = type switch
        {
            DamageType.Melee    => (damage.ToString(), Color.white,  1.0f),
            DamageType.Ranged   => (damage.ToString(), Color.cyan,   1.0f),
            DamageType.Critical => (damage.ToString(), Color.yellow, 1.4f),
            DamageType.Weakness => ($"WEAK! {damage}", Color.red,   1.6f),
            _                   => (damage.ToString(), Color.white,  1.0f)
        };

        text.text = label;
        text.color = color;
        startColor = color;
        transform.localScale = Vector3.one * scale;

        // 위로 떠오르면서 약간 좌우 랜덤
        float xRand = Random.Range(-0.5f, 0.5f);
        velocity = new Vector3(xRand, 2.5f, 0f);

        gameObject.SetActive(true);
    }

    void Update()
    {
        elapsed += Time.deltaTime;
        float t = elapsed / lifetime;

        // 위로 이동 (감속)
        transform.position += velocity * Time.deltaTime;
        velocity *= 0.9f;

        // 페이드 아웃 (후반 50% 구간에서)
        if (t > 0.5f)
        {
            float alpha = 1f - (t - 0.5f) / 0.5f;
            text.color = new Color(startColor.r, startColor.g, startColor.b, alpha);
        }

        // 수명 종료 시 풀로 반환
        if (elapsed >= lifetime)
            DamageNumberPool.Instance.Return(this);
    }
}
```

### 4. 오브젝트 풀 (성능 필수)

데미지 숫자는 전투 중 매 프레임 다수 생성될 수 있어 **반드시 풀링** 사용.

```csharp
// DamageNumberPool.cs
using System.Collections.Generic;
using UnityEngine;

public class DamageNumberPool : MonoBehaviour
{
    public static DamageNumberPool Instance;
    [SerializeField] private DamageNumber prefab;
    [SerializeField] private int initialSize = 20;

    private Queue<DamageNumber> pool = new Queue<DamageNumber>();

    void Awake()
    {
        Instance = this;
        for (int i = 0; i < initialSize; i++)
        {
            var num = Instantiate(prefab, transform);
            num.gameObject.SetActive(false);
            pool.Enqueue(num);
        }
    }

    public DamageNumber Get()
    {
        if (pool.Count > 0)
            return pool.Dequeue();
        return Instantiate(prefab, transform);
    }

    public void Return(DamageNumber num)
    {
        num.gameObject.SetActive(false);
        pool.Enqueue(num);
    }

    public void Spawn(int damage, Vector3 pos, DamageType type)
    {
        var num = Get();
        num.Initialize(damage, pos, type);
    }
}
```

### 5. 데미지 타입 정의

```csharp
public enum DamageType
{
    Melee,    // 고양이 근접 — 흰색
    Ranged,   // 양파 원거리 — 청록색
    Critical, // 크리티컬 — 노란색, 크게
    Weakness  // 약점 공격 — 빨간색, 가장 크게, "WEAK!" 텍스트 추가
}
```

### 6. 기존 데미지 코드에 연동

```csharp
// EnemyHealth.cs 내 TakeDamage 호출부
public void TakeDamage(int amount, DamageType type, Vector3 hitPos)
{
    currentHP -= amount;
    DamageNumberPool.Instance.Spawn(amount, hitPos + Vector3.up * 0.5f, type);
    
    if (currentHP <= 0) Die();
}
```

### 7. 카메라 방향 추적 (중요)

World Space Canvas는 카메라를 향하지 않으면 글자가 비뚤어 보임.

```csharp
void LateUpdate()
{
    // 카메라가 회전하지 않는 2D 게임이라면 생략 가능
    // 필요 시 아래 코드로 항상 카메라 정면 유지
    transform.rotation = Camera.main.transform.rotation;
}
```

2D 탑뷰 고정 카메라 게임(OnionCat)에서는 캔버스 회전이 고정되어 있어 **LateUpdate 추적 불필요**.

---

## OnionCat 적용 포인트

### 핵심 활용: 약점 시스템 시각화

OnionCat의 핵심 메카닉 = "근접에만 약한 적, 원거리에만 약한 적" → 이를 숫자로 즉각 표시:

| 상황 | 데미지 표시 |
|------|------------|
| 일반 공격 | 흰색/청록 숫자 |
| 약점 공격 | 빨간색 "WEAK! 24" (크기 1.6배) |
| 비약점 공격 | 회색 작은 숫자 "2" (막혀있음 표시) |

### 비약점 공격 표현 (저항)

```csharp
// 비약점 타입으로 공격 시 데미지 최소화 + 시각적 피드백
DamageType.Resist  // 회색, 작은 크기, "✕" 기호
```

### 두 플레이어 색상 구분

- 고양이 슬래시: **흰색** 숫자
- 양파 투사체: **청록색** 숫자
- 약점 히트: **빨간색 + "WEAK!"**
- 크리티컬: **노란색 + 크기 증가**

### 픽셀아트 폰트 권장

- 일반 폰트 대신 **픽셀 폰트** 사용 (예: "Press Start 2P", "Pixel Operator")
- TextMeshPro 임포트: Window > TextMeshPro > Font Asset Creator에서 픽셀 폰트 임포트

---

## 참고 링크

- TextMeshPro 공식 문서: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
- Unity 오브젝트 풀링 가이드: https://unity.com/resources/object-pooling-free-ebook
- 픽셀 폰트 무료 리소스: https://www.dafont.com/bitmap.php
- 유튜브 튜토리얼: "Unity Floating Damage Numbers Tutorial" (Code Monkey 채널 검색)
