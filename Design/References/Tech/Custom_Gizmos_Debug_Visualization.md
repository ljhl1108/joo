# 커스텀 기즈모 & 디버그 시각화 (Custom Gizmos & Debug Visualization)

리서치 날짜: 2026-08-23

## 개요

Unity 에디터에서 **런타임 없이 씬 뷰에 시각적 정보를 표시**하는 기법.
히트박스, 시야각, 공격 범위, 이동 경로 등을 눈으로 확인할 수 있어
**게임 없이 디버그 → 버그 발견 속도를 3~5배 단축**시킨다.

OnionCat처럼 히트박스·시야각·투사체 궤적이 복잡한 게임에서 필수 도구다.
최종 빌드에는 자동으로 포함되지 않으므로 성능 걱정 없이 사용 가능.

---

## Unity 구현 방법

### 1. 기본 기즈모 (OnDrawGizmos / OnDrawGizmosSelected)

```csharp
// MonoBehaviour에 바로 작성
void OnDrawGizmos()
{
    // 항상 표시 (선택 여부 무관)
    Gizmos.color = new Color(1f, 0f, 0f, 0.3f);
    Gizmos.DrawWireSphere(transform.position, attackRange);
}

void OnDrawGizmosSelected()
{
    // 해당 오브젝트 선택 시에만 표시
    Gizmos.color = Color.yellow;
    Gizmos.DrawRay(transform.position, transform.right * detectionRange);
}
```

### 2. 호 형태의 공격 범위 (Handles 사용)

Cat의 180° 슬래시 범위를 에디터에서 시각화:

```csharp
#if UNITY_EDITOR
using UnityEditor;

void OnDrawGizmosSelected()
{
    Handles.color = new Color(1f, 0.5f, 0f, 0.3f);
    // DrawSolidArc(center, normal, fromDir, angle, radius)
    Handles.DrawSolidArc(
        transform.position,
        Vector3.forward,
        -transform.right,   // 시작 방향
        180f,               // Cat의 슬래시 각도
        meleeRange
    );
}
#endif
```

### 3. 적 FOV 시야각 시각화

```csharp
#if UNITY_EDITOR
void OnDrawGizmosSelected()
{
    Gizmos.color = Color.cyan;
    float halfAngle = fovAngle / 2f;
    Vector3 leftDir = Quaternion.Euler(0, 0, halfAngle) * transform.right;
    Vector3 rightDir = Quaternion.Euler(0, 0, -halfAngle) * transform.right;

    Gizmos.DrawRay(transform.position, leftDir * viewDistance);
    Gizmos.DrawRay(transform.position, rightDir * viewDistance);
    Gizmos.DrawWireSphere(transform.position, viewDistance);
}
#endif
```

### 4. 커스텀 인스펙터 (Custom Editor)

Inspector에서 슬라이더나 버튼을 추가해 디버그 편의성 향상:

```csharp
// 에디터 폴더 (Assets/Editor/) 에 별도 파일 작성
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(EnemyAI))]
public class EnemyAIEditor : Editor
{
    public override void OnInspectorGUI()
    {
        DrawDefaultInspector();  // 기존 Inspector 그대로 유지

        EnemyAI enemy = (EnemyAI)target;

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Debug", EditorStyles.boldLabel);

        if (GUILayout.Button("Force Alert State"))
            enemy.SetState(EnemyState.Alert);

        if (GUILayout.Button("Force Idle State"))
            enemy.SetState(EnemyState.Idle);
    }
}
```

### 5. Debug.DrawLine / DrawRay (런타임 확인)

에디터 Play 모드에서 Scene 뷰로 실시간 확인:

```csharp
void Update()
{
    // 투사체 궤적 예측선 (Scene 뷰 + 0.1초 유지)
    Debug.DrawRay(transform.position, transform.right * projectileSpeed, Color.green, 0.1f);
    
    // 히트 감지 라인
    if (Physics2D.Raycast(transform.position, transform.right, attackRange))
        Debug.DrawRay(transform.position, transform.right * attackRange, Color.red);
}
```

### 6. UNITY_EDITOR 조건부 컴파일

빌드에서 기즈모 코드가 포함되지 않도록:

```csharp
public class AttackSystem : MonoBehaviour
{
    public float meleeRange = 1.5f;

#if UNITY_EDITOR
    void OnDrawGizmos()
    {
        Gizmos.color = new Color(1, 0, 0, 0.2f);
        Gizmos.DrawWireSphere(transform.position, meleeRange);
    }
#endif
}
```

---

## OnionCat 적용 포인트

| 시스템 | 기즈모 추가 위치 | 시각화 내용 |
|--------|-----------------|------------|
| Cat 근접 공격 | `MeleeAttack.cs` | 180° 슬래시 호, 유효 반경 |
| Onion 투사체 | `ProjectileLauncher.cs` | 발사 방향 Ray, 최대 사거리 |
| Onion 방패 | `ShieldSystem.cs` | 방어 방향 Arc, parry 판정 범위 |
| 적 FOV | `EnemyAI.cs` | 시야각 부채꼴, 추적 반경 |
| 적 패트롤 | `PatrolController.cs` | 웨이포인트 연결선 |
| 방 연결 | `RoomConnector.cs` | 문 위치, 연결 화살표 |
| 공격 히트박스 | `HitboxCollider.cs` | 히트박스 영역 (너그럽게 설정 확인용) |

**커스텀 인스펙터 우선 추가 추천 스크립트:**
- `EnemyAI` → 상태 강제 전환 버튼
- `RoomManager` → 강제 방 생성 버튼  
- `UpgradeSystem` → 테스트 업그레이드 즉시 부여 버튼

---

## 참고 링크

- Unity 공식 문서 - Gizmos: https://docs.unity3d.com/Manual/GizmosAndHandles.html
- Unity 공식 문서 - Custom Editor: https://docs.unity3d.com/Manual/editor-CustomEditors.html
- Unity 공식 문서 - Handles: https://docs.unity3d.com/ScriptReference/Handles.html
- Catlike Coding - Custom Inspectors: https://catlikecoding.com/unity/tutorials/editor/custom-editors/
- YouTube - "Unity Editor Scripting Basics" by Code Monkey: https://www.youtube.com/watch?v=RInUu1_8aGg
