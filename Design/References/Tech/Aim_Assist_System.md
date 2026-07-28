# 에임 어시스트 시스템 (Aim Assist System)

리서치 날짜: 2026-07-28

## 개요

에임 어시스트는 컨트롤러(게임패드) 사용자가 마우스에 비해 정밀도가 낮은 아날로그 스틱으로 적을 조준할 때 도움을 주는 시스템이다. OnionCat의 Player 2(양파)는 마우스로 정밀한 투사체 방향을 결정하는데, 컨트롤러 플레이어에게 공평한 경험을 제공하려면 에임 어시스트가 필수적이다.

---

## 에임 어시스트의 종류

| 방식 | 설명 | 적합 상황 |
|------|------|---------|
| **불릿 마그네티즘** | 발사된 탄환 궤도가 가까운 적 쪽으로 살짝 휨 | 투사체 게임 |
| **소프트 스냅** | 조준 방향이 적 근처에 오면 살짝 당겨짐 | 일반적 에임 어시스트 |
| **에임 슬로우다운** | 적 근처에서 스틱 감도가 낮아짐 | FPS, TPS |
| **하드 록온** | 버튼 입력 시 특정 적을 완전히 잠금 | 액션 어드벤처 |
| **탄환 중력** | 탄환이 포물선 대신 적 방향으로 중력 적용 | 탑다운 슈터 |

OnionCat에 가장 적합한 방식: **불릿 마그네티즘 + 소프트 스냅 조합**

---

## Unity 구현 방법

### 1. 에임 어시스트 범위 설정

```csharp
[SerializeField] private float assistRadius = 3f;      // 탐지 반경
[SerializeField] private float assistAngle = 30f;      // 조준 방향 기준 각도
[SerializeField] private float assistStrength = 0.3f;  // 당김 강도 (0~1)
[SerializeField] private LayerMask enemyLayer;
```

### 2. 가장 가까운 적 탐지 (콘 형태)

```csharp
private Transform FindBestTarget(Vector2 aimDir)
{
    Collider2D[] candidates = Physics2D.OverlapCircleAll(
        transform.position, assistRadius, enemyLayer);

    Transform bestTarget = null;
    float bestScore = float.MaxValue;

    foreach (var col in candidates)
    {
        Vector2 toEnemy = (col.transform.position - transform.position).normalized;
        float angle = Vector2.Angle(aimDir, toEnemy);

        // 콘 범위 밖이면 무시
        if (angle > assistAngle) continue;

        // 각도와 거리를 가중치로 점수 계산
        float dist = Vector2.Distance(transform.position, col.transform.position);
        float score = angle * 0.6f + dist * 0.4f;

        if (score < bestScore)
        {
            bestScore = score;
            bestTarget = col.transform;
        }
    }
    return bestTarget;
}
```

### 3. 소프트 스냅 적용

```csharp
public Vector2 ApplyAimAssist(Vector2 rawAimDir)
{
    // 마우스 입력이면 에임 어시스트 비활성화
    if (PlayerInput.currentControlScheme == "Keyboard&Mouse")
        return rawAimDir;

    Transform target = FindBestTarget(rawAimDir);
    if (target == null) return rawAimDir;

    Vector2 toTarget = (target.position - transform.position).normalized;
    // rawAimDir과 toTarget 사이를 assistStrength 비율로 보간
    return Vector2.Lerp(rawAimDir, toTarget, assistStrength).normalized;
}
```

### 4. 불릿 마그네티즘 (발사 후 탄환 유도)

```csharp
// ProjectileMover.cs 내부
private Transform magnetTarget;
[SerializeField] private float magnetStrength = 2f;
[SerializeField] private float magnetDuration = 0.15f; // 발사 초기 짧은 시간만 적용

void Update()
{
    if (magnetTarget != null && elapsedTime < magnetDuration)
    {
        Vector2 toTarget = (magnetTarget.position - transform.position).normalized;
        Vector2 newDir = Vector2.Lerp(direction, toTarget, magnetStrength * Time.deltaTime);
        direction = newDir.normalized;
    }
    // 이후엔 직선 이동
    transform.Translate(direction * speed * Time.deltaTime);
    elapsedTime += Time.deltaTime;
}
```

### 5. InputSystem 컨트롤러 감지

```csharp
using UnityEngine.InputSystem;

bool IsUsingController()
{
    var device = InputSystem.GetDevice<Gamepad>();
    return device != null && device.wasUpdatedThisFrame;
}
```

### 6. 에임 어시스트 시각화 (디버그용)

```csharp
void OnDrawGizmosSelected()
{
    Gizmos.color = Color.yellow;
    Gizmos.DrawWireSphere(transform.position, assistRadius);

    // 콘 시각화
    Vector3 fwd = transform.right * assistRadius;
    Quaternion left  = Quaternion.Euler(0, 0,  assistAngle);
    Quaternion right = Quaternion.Euler(0, 0, -assistAngle);
    Gizmos.DrawLine(transform.position, transform.position + left  * fwd);
    Gizmos.DrawLine(transform.position, transform.position + right * fwd);
}
```

---

## OnionCat 적용 포인트

### Player 2 (양파) 투사체 조준 보조
- 마우스 입력: 에임 어시스트 비활성화 (정밀도 그대로)
- 컨트롤러 입력: 소프트 스냅 활성화 → 가까운 적 방향으로 약하게 당김
- `PlayerInput.currentControlScheme`으로 두 플레이어 각각 독립적으로 처리

### 약점 시스템과 연동
- 에임 어시스트 탐지 시 "원거리 공격에 취약한 적"을 우선 타겟으로 가중치 부여
- 이미 죽어가는 적(HP < 20%)보다 건강한 우선 타겟 선호 로직 추가 가능

### 설정 메뉴 연동
- 에임 어시스트 강도를 Settings Menu에서 0 / 약 / 강 3단계로 조절
- 경쟁 플레이어용으로 완전 끄기 옵션 제공

### 멀티플레이어 주의사항
- Player 1과 Player 2가 각각 독립된 AimAssist 컴포넌트를 가짐
- 두 플레이어가 같은 적을 동시에 타겟팅해도 충돌 없음

---

## 참고 링크

- [Unity InputSystem - Control Scheme 감지](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/ActionBindings.html)
- [Game Maker's Toolkit: Aim Assist 분석](https://www.youtube.com/watch?v=yGci-Lb87zs)
- [Physics2D.OverlapCircleAll 문서](https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircleAll.html)
- [Celeste 소스코드 - 에임 어시스트 참고](https://github.com/NoelFB/Celeste)
- [Brackeys: Lock-On Target System in Unity](https://www.youtube.com/watch?v=vBqd3lDMRy4)
