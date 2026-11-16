# Enemy Split Clone System (적 분열/복제 시스템)

리서치 날짜: 2026-11-16

## 개요

적이 일정 체력 임계값에 도달하거나 사망 시 **더 작은 복사본으로 분열**되는 시스템.
Binding of Isaac(Fistula, Big Spider), Nuclear Throne(Rogue Rifle 맞은 적), Noita(분열 주문)에서 활용.
OnionCat에서는 "예상치 못한 분열로 방이 갑자기 혼잡해지는" 긴장감을 추가할 수 있음.

---

## Unity 구현 방법

### 기본 구조 (EnemyBase 확장)

```csharp
// EnemyBase에 분열 데이터 추가
[System.Serializable]
public class SplitData
{
    public string spawnEnemyId;    // EnemyRoster에서 꺼낼 적 ID
    public int    count = 2;       // 분열 수
    public float  scatterRadius = 0.5f;
    public int    maxDepth = 1;    // 재분열 방지 (0 = 더 이상 분열 안 함)
}
```

### EnemyBase에 훅 추가

```csharp
// EnemyBase.Status.cs (OnDamaged 훅 사용)
protected override void OnDied()
{
    if (splitData != null && splitData.maxDepth > 0)
        SplitManager.Spawn(transform.position, splitData);
    base.OnDied();
}
```

### SplitManager

```csharp
public static class SplitManager
{
    public static void Spawn(Vector2 origin, SplitData data)
    {
        var prefab = EnemyRoster.Instance.GetById(data.spawnEnemyId);
        if (prefab == null) return;

        for (int i = 0; i < data.count; i++)
        {
            float angle = (360f / data.count) * i;
            var offset = Quaternion.Euler(0, 0, angle) * Vector2.right * data.scatterRadius;
            var go = PoolManager.Spawn(prefab, origin + (Vector2)offset, Quaternion.identity);

            // 자식은 maxDepth - 1로 설정 (재분열 제한)
            var childEnemy = go.GetComponent<EnemyBase>();
            if (childEnemy != null && childEnemy.splitData != null)
                childEnemy.splitData.maxDepth = data.maxDepth - 1;
        }
    }
}
```

### 체력 비율 임계값 분열 (절반 체력에서 분열)

```csharp
// EnemyBase.InterceptDamage 훅
protected override void InterceptDamage(ref DamageInfo info)
{
    bool wasAboveHalf = CurrentHealth > MaxHealth * 0.5f;
    base.InterceptDamage(ref info);
    bool nowBelow = CurrentHealth <= MaxHealth * 0.5f;

    if (wasAboveHalf && nowBelow && splitData != null && !hasSplitAtHalf)
    {
        hasSplitAtHalf = true;
        SplitManager.Spawn(transform.position, splitData);
    }
}
```

### EnemyBuilder.cs 테이블에 분열 데이터 추가

```csharp
// Editor/EnemyBuilder.cs 테이블 항목 예시
new EnemyEntry {
    id = "slime_large",
    split = new SplitData {
        spawnEnemyId = "slime_small",
        count = 2,
        scatterRadius = 0.4f,
        maxDepth = 1   // 소 슬라임은 더 분열 안 함
    }
}
```

---

## 고려 사항

### 무한 분열 방지
- `maxDepth` 필드로 재귀 한계 설정 (최대 2단계 권장)
- 방당 최대 적 수 체크 (`EnemyBase.Active.Count < maxEnemiesPerRoom`)

### 풀링과 호환성
- `PoolManager.Spawn/Despawn` 필수 — Instantiate 사용 시 방 클리어 중 급증할 수 있음
- 자식 적의 `OnEnable`에서 상태 초기화 (체력 리셋, hasSplitAtHalf = false)

### 분열 연출
- 분열 시 간단한 파티클 (기존 적 death VFX의 작은 버전)
- 분열 직후 짧은 무적 프레임 (0.2초) → 즉시 타격 방지
- 카메라 흔들기 (Cinemachine impulse) 등은 선택적

### 크기 등급 연동
- `EnemyBuilder.SizeOf`로 자식 적의 크기를 부모보다 한 단계 낮게 자동 설정
- 예: 큰(0.75) → 보통(0.6), 보통(0.6) → 작은(0.5)

---

## OnionCat 적용 포인트

### 적 콘텐츠 아이디어
- **대형 슬라임** (ST1 밀밭): 사망 시 소형 슬라임 2마리로 분열
  - 협동 판단 필요: "지금 여기서 처치해도 되나, 위치 조정 먼저?"
  - 고양이가 발로 날려보낸 대형 슬라임이 벽에 부딪혀 분열 → 연쇄 작용

- **씨앗 꼬투리 (ST2 초원)**: 절반 체력에서 2마리 소형 적 소환
  - 양파의 씨앗 한 발에 처치하려면 더 강한 집중 화력 필요 → 협동 유도

- **거품 적 (ST3)**: 처치 시 무적 거품 여러 개 생성 (거품은 1초 후 터지며 피해)
  - 완전한 분열이 아닌 "사망 후 환경 위험 생성" 변형 적용

### 고양이 특수 공격과의 시너지
- 고양이 특수 공격(`CatSpecial`)이 대형 적에 맞으면 즉시 분열 트리거 가능
  - 보통은 임계값 이하에서 자연 분열 → 특수 공격으로 "강제 분열" 하는 고난도 선택

### EnemyBuilder 작업 흐름
1. `EnemyBuilder.cs` 테이블에 `split` 필드 추가
2. 메뉴 **OnionCat > Enemies > Build Enemies** 실행
3. 자식 적 프리팹이 먼저 존재해야 함 (빌드 순서 주의)

---

## 참고 링크

- Binding of Isaac 분열 적 디자인: https://bindingofisaacrebirth.fandom.com/wiki/Fistula
- Unity PoolManager 패턴: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- Unity EnemyBase 조합형 설계: `Design/References/Tech/Enemy_Pattern_Composition_System.md`
- 적 체력 임계값 설계 참고: `Design/References/Tech/Enemy_Elite_Variant_System.md`
