# 2D Inverse Kinematics (역운동학)

리서치 날짜: 2026-11-03

## 개요

IK(Inverse Kinematics)는 "끝점(Effector)의 위치를 주면, 뼈대 체인이 자동으로 각도를 계산"하는 기법.
일반 애니메이션(FK, Forward Kinematics)은 각 관절 각도를 직접 지정 → IK는 목적지만 주면 알아서 팔다리를 구부림.

**OnionCat에서 왜 중요한가?**
- 고양이 네 다리의 발이 불규칙한 지형에 자동으로 맞닿는 **절차적 걷기 애니메이션**
- 고양이 등에 탄 화분(양파)이 고양이의 움직임에 따라 자연스럽게 기울기 조정
- 양파의 씨앗 발사 팔이 마우스 방향으로 자연스럽게 회전
- 키프레임 없이 프로그래밍으로 "살아있는 느낌" 구현

---

## Unity 2D IK 패키지

### 설치
Unity의 공식 2D IK 패키지: `com.unity.2d.ik`
- Package Manager → "2D IK" 검색 또는 manifest.json에 추가
- 2D Animation 패키지(com.unity.2d.animation)에 포함되어 있음

### 세 가지 솔버(Solver) 종류

| 솔버 | 특징 | 용도 |
|------|------|------|
| **Limb** | 3개 뼈 고정(상완-하완-손), 빠름 | 팔·다리 (OnionCat 추천) |
| **Chain (CCD)** | 반복적으로 수렴, 관절 수 자유, 느리지만 정확 | 꼬리, 긴 팔 |
| **Chain (FABRIK)** | CCD보다 적은 반복으로 수렴, 회전 제한 시 느림 | 유연한 체인 |

### 기본 설정 순서 (Limb 솔버 기준)

```
1. 캐릭터 뼈대 설정 (Sprite → 2D Rig 사용)
2. IK Manager 2D 컴포넌트를 루트 오브젝트에 추가
3. "Add Solver" → Limb 선택
4. 솔버에 뼈대 루트 지정 (어깨/엉덩이)
5. Effector Transform 생성 → 손/발 위치에 배치
6. Target Transform 생성 → 발이 닿아야 할 위치 설정
7. IK Manager의 Weight로 전체 영향도 조절 (0~1)
```

### Inspector 설정값
```csharp
// IKManager2D 컴포넌트
Weight = 1.0f;  // IK 영향 전체 강도

// LimbSolver2D 컴포넌트  
Target       // 발/손이 향해야 할 Transform
Effector     // 실제 발/손 Transform
Weight       // 이 솔버의 영향도
Flip         // 무릎/팔꿈치 굽히는 방향 반전
SolveFromDefaultPose = true;  // 기본 자세에서 계산
```

---

## 절차적 발 배치 (Procedural Foot Placement)

가장 인상적인 응용: 캐릭터가 걸을 때 발이 지형에 맞게 자동 배치.

```csharp
// 발 Target 위치 결정 로직 개념
public class ProceduralLeg : MonoBehaviour
{
    [SerializeField] Transform stepTarget;      // IK의 Target
    [SerializeField] float stepDistance = 0.3f; // 이 거리 이상 벌어지면 발 이동
    [SerializeField] float stepHeight = 0.2f;   // 발을 드는 높이
    [SerializeField] float stepSpeed = 8f;

    Vector2 currentPos, targetPos;

    void Update()
    {
        // 이상적인 발 위치 = 캐릭터 발 아래 지형
        Vector2 idealPos = GetGroundPoint();

        // 현재 발 위치에서 이상적 위치까지 너무 멀면 발을 이동
        if (Vector2.Distance(currentPos, idealPos) > stepDistance)
            targetPos = idealPos;

        // Lerp로 부드럽게 이동
        currentPos = Vector2.MoveTowards(currentPos, targetPos, stepSpeed * Time.deltaTime);
        stepTarget.position = currentPos + GetArcHeight();
    }
}
```

---

## 코드로 IK 제어 (런타임)

```csharp
// IKManager2D를 코드에서 접근
using UnityEngine.U2D.IK;

public class CatArmController : MonoBehaviour
{
    [SerializeField] LimbSolver2D armSolver;
    [SerializeField] Transform aimTarget;

    void Update()
    {
        // 양파 조준 방향으로 팔 Target 이동
        Vector2 mouseWorldPos = Camera.main.ScreenToWorldPoint(Input.mousePosition);
        aimTarget.position = mouseWorldPos;
    }

    // IK 가중치 부드럽게 켜기/끄기
    IEnumerator BlendIKWeight(float targetWeight, float duration)
    {
        float start = armSolver.weight;
        for (float t = 0; t < duration; t += Time.deltaTime)
        {
            armSolver.weight = Mathf.Lerp(start, targetWeight, t / duration);
            yield return null;
        }
        armSolver.weight = targetWeight;
    }
}
```

---

## 주의사항 & 픽셀아트 주의

**픽셀아트 + IK 조합 시 문제점**
- IK는 소수점 단위로 뼈대를 회전 → 픽셀이 깨질 수 있음
- 픽셀 퍼펙트 렌더러가 적용된 상태에서 중간 각도 뼈대는 흐릿하게 보임

**해결책**
1. Sprite Renderer의 Pixel Snap 활성화
2. IK는 방향 전환 등 큰 각도 변화에만 사용, 세밀한 포즈는 키프레임 애니메이션 유지
3. 8방향 또는 16방향으로 각도를 스냅해 픽셀 정렬 유지:

```csharp
// 8방향 스냅 예시
float SnapAngle(float angle, int directions = 8)
{
    float step = 360f / directions;
    return Mathf.Round(angle / step) * step;
}
```

---

## OnionCat 적용 포인트

### 즉시 적용 가능한 것 (픽셀아트 친화적)
1. **양파 조준팔**: 마우스 방향으로 화분 위쪽 팔이 자연스럽게 회전 (Limb 솔버, 2~3 뼈대)
2. **화분 기울기**: 고양이가 달릴 때 화분이 관성으로 뒤로 살짝 기울기 (Transform Lerp로도 가능하지만 IK로 더 자연스러움)
3. **공격 모션 보완**: 할퀴기 방향으로 팔이 먼저 뻗은 뒤 휘두르는 모션

### 향후 고려 사항
- 고양이 네 다리 절차적 걷기: 현재 sprite 기반 프레임 애니메이션이라면 IK 도입은 리그(rig) 재작업 필요
- 정밀한 발 착지가 필요한 지형 탐색 구간에서 연출 품질 향상

### 구현 우선순위
낮음 — 게임플레이에 영향 없는 비주얼 연출. 기본 기능 완성 후 폴리싱 단계에서 고려.

---

## 참고 링크
- [Unity 2D IK 공식 문서](https://docs.unity3d.com/Packages/com.unity.2d.ik@2.1/manual)
- [2D Animation 패키지의 IK 섹션](https://docs.unity3d.com/Packages/com.unity.2d.animation@9.1/manual/2DIK.html)
- [Unity Procedural Animation GitHub 예시](https://github.com/takaaptech/Unity-Procedural-Animation)
