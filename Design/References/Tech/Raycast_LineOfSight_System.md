# 2D 레이캐스팅 시야선 차단 감지 시스템 (Raycast Line-of-Sight)

리서치 날짜: 2026-08-09

## 개요

**시야선(Line of Sight, LOS)**이란 적이 플레이어를 "볼 수 있는지"를 벽/장애물 기준으로 판단하는 시스템이다.
FOV 감지(각도·거리 체크)와는 별개로, 두 점 사이에 벽이 있으면 시야 차단 처리를 한다.

OnionCat에서 왜 필요한가:
- 방 안에 기둥/장벽이 있을 때 적이 벽 뒤 플레이어를 무시해야 함
- 잠복 적(매복 몬스터): 시야에 들어와야 활성화
- 원거리 적: 플레이어가 벽 뒤에 있으면 투사체 발사 중단
- 플레이어가 "숨기" 전술을 사용할 수 있게 함 → 협력 전술 다양화

---

## Unity 구현 방법

### 1. 기본 원리

```csharp
// Physics2D.Linecast: 두 점 사이에 특정 레이어 콜라이더가 있으면 hit
bool HasLineOfSight(Vector2 origin, Vector2 target, LayerMask obstacleMask)
{
    // origin → target 사이에 장애물이 없으면 true
    RaycastHit2D hit = Physics2D.Linecast(origin, target, obstacleMask);
    return hit.collider == null;
}
```

### 2. 올바른 LayerMask 설정

```csharp
// Inspector에서 설정 (권장)
[SerializeField] private LayerMask wallLayerMask;  // "Wall" 레이어만 포함

// 또는 코드에서 이름으로 설정
private LayerMask wallLayerMask;
void Awake()
{
    // "Wall"과 "Obstacle" 레이어 포함
    wallLayerMask = LayerMask.GetMask("Wall", "Obstacle");
}
```

**중요**: 플레이어/적 레이어는 제외해야 함. 그렇지 않으면 적 자신의 콜라이더에 레이가 걸림.

### 3. 발사 위치 오프셋

```csharp
// 눈 높이에서 레이 발사 (발 기준 X)
Vector2 GetEyePosition(Transform t, float eyeHeight = 0.5f)
{
    return (Vector2)t.position + Vector2.up * eyeHeight;
}

bool CanSeePlayer()
{
    Vector2 eyePos = GetEyePosition(transform);
    Vector2 playerPos = GetEyePosition(player.transform);
    return HasLineOfSight(eyePos, playerPos, wallLayerMask);
}
```

### 4. 성능 최적화 — 체크 빈도 제한

```csharp
public class EnemyVisionChecker : MonoBehaviour
{
    [SerializeField] private float checkInterval = 0.1f;  // 0.1초마다 체크 (10Hz)
    [SerializeField] private LayerMask wallLayerMask;
    [SerializeField] private float visionRange = 8f;
    
    private Transform _player;
    private bool _hasLOS;
    private float _nextCheckTime;

    void Awake()
    {
        _player = GameObject.FindGameObjectWithTag("Player").transform;
    }

    void Update()
    {
        if (Time.time >= _nextCheckTime)
        {
            _nextCheckTime = Time.time + checkInterval;
            _hasLOS = CheckLOS();
        }
        
        if (_hasLOS)
            ChasePlayer();
    }

    bool CheckLOS()
    {
        Vector2 toPlayer = (Vector2)(_player.position - transform.position);
        
        // 1. 거리 체크 (비싼 Raycast 전에 싼 거리 체크 먼저)
        if (toPlayer.magnitude > visionRange) return false;
        
        // 2. 레이캐스트로 벽 차단 체크
        RaycastHit2D hit = Physics2D.Raycast(
            transform.position,
            toPlayer.normalized,
            toPlayer.magnitude,
            wallLayerMask
        );
        return hit.collider == null;
    }
}
```

### 5. 다중 레이 (정확도 향상)

단일 레이는 아주 얇은 틈에서 오작동 가능. 3개의 레이를 써서 정확도 향상:

```csharp
bool CheckLOSMultiRay()
{
    Vector2 enemyCenter = transform.position;
    Vector2 playerCenter = _player.position;
    
    // 3개 레이: 중앙, 약간 위, 약간 아래
    Vector2[] offsets = {
        Vector2.zero,
        Vector2.up * 0.3f,
        Vector2.down * 0.3f
    };
    
    // 하나라도 통하면 시야 있음
    foreach (var offset in offsets)
    {
        Vector2 from = enemyCenter + offset;
        Vector2 to = playerCenter + offset;
        RaycastHit2D hit = Physics2D.Linecast(from, to, wallLayerMask);
        if (hit.collider == null) return true;
    }
    return false;
}
```

### 6. FOV + LOS 조합 (완전한 시야 시스템)

```csharp
bool IsPlayerVisible()
{
    Vector2 toPlayer = (Vector2)(_player.position - transform.position);
    
    // 1. 거리 체크
    if (toPlayer.magnitude > visionRange) return false;
    
    // 2. 각도 체크 (FOV 180도 예시)
    float angle = Vector2.Angle(transform.right, toPlayer);
    if (angle > visionAngle * 0.5f) return false;
    
    // 3. 벽 차단 체크 (LOS)
    RaycastHit2D hit = Physics2D.Raycast(
        transform.position, toPlayer.normalized, toPlayer.magnitude, wallLayerMask
    );
    return hit.collider == null;
}
```

### 7. 디버그 시각화 (에디터에서 확인용)

```csharp
void OnDrawGizmosSelected()
{
    if (_player == null) return;
    
    Gizmos.color = _hasLOS ? Color.red : Color.green;
    Gizmos.DrawLine(transform.position, _player.position);
    
    // 시야 범위 원
    Gizmos.color = Color.yellow;
    Gizmos.DrawWireSphere(transform.position, visionRange);
}
```

---

## OnionCat 적용 포인트

### 1. 적 AI 행동 트리에 통합
```
Idle → [거리 체크] → [LOS 체크] → [FOV 각도 체크] → Chase 상태로 전환
```
- 체크 순서: 거리(값싼 연산) → LOS(중간) → 각도(비쌈)
- 각 체크를 통과해야 다음 체크로 넘어감 → 불필요한 계산 최소화

### 2. 적 유형별 LOS 다르게 적용
| 적 유형 | LOS 방식 |
|---------|---------|
| 근접 슬라임 | 단일 레이, 짧은 범위 (4~5유닛) |
| 원거리 궁수 | 단일 레이, 긴 범위 (10~12유닛), 벽 뒤면 이동하여 각도 확보 |
| 매복 몬스터 | LOS가 0.5초 이상 지속될 때만 활성화 (순간 시야 무시) |
| 보스 | 멀티레이 + 세밀한 범위 |

### 3. "벽 뒤 숨기" 협력 전술 유도
Cat이 적의 시선을 끌고 있는 동안 Crop이 벽 뒤에서 안전하게 재장전하는 전술 가능:
```
Cat → 적의 LOS에 노출 (어그로 유지)
Crop → 벽 뒤, LOS 차단 (안전 포지셔닝)
```
→ 이 시스템이 없으면 적이 벽 뒤 Crop을 항상 감지해서 전술이 무의미해짐

### 4. 구현 순서
1. Unity Project Settings → Physics 2D → Layer Collision Matrix에서 "Wall" 레이어 설정
2. `EnemyVisionChecker` 컴포넌트 작성
3. 기존 `EnemyAIStateMachine`의 `CanChase()` 조건에 LOS 체크 추가
4. `OnDrawGizmosSelected()`로 에디터에서 시야선 실시간 확인

---

## 참고 링크

- Unity Docs — Physics2D.Raycast: https://docs.unity3d.com/ScriptReference/Physics2D.Raycast.html
- Unity Docs — Physics2D.Linecast: https://docs.unity3d.com/ScriptReference/Physics2D.Linecast.html
- Unity Docs — LayerMask.GetMask: https://docs.unity3d.com/ScriptReference/LayerMask.GetMask.html
- 튜토리얼 (유튜브 검색): "Unity 2D line of sight raycast tutorial"
- 레이어 매트릭스 설정: https://docs.unity3d.com/Manual/LayerBasedCollision.html
