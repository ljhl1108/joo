# Unity Test Runner / 자동화 테스트 시스템

리서치 날짜: 2026-09-29

## 개요

Unity Test Runner는 Unity 에디터에 내장된 테스트 프레임워크다. NUnit 기반이며  
**Edit Mode 테스트**(게임 로직 단위 테스트)와 **Play Mode 테스트**(실제 런타임 동작 검증) 두 종류를 지원한다.

초보 개발자에게 테스트는 "귀찮은 것"처럼 느껴지지만, OnionCat처럼 여러 시스템(PoolManager, GameManager, PlayerStats, UpgradeSystem)이 얽혀 있는 게임에서는 **코드 수정 후 게임 전체를 켜지 않고도 핵심 로직이 깨지지 않았는지** 검증할 수 있어 개발 속도가 오히려 빨라진다.

---

## Unity 구현 방법

### 1. Test Runner 창 열기
```
Window → General → Test Runner
```
두 탭이 있다: **EditMode**, **PlayMode**

### 2. 테스트 Assembly Definition 생성

테스트 파일은 일반 Scripts 폴더와 **분리된 Assembly**에 있어야 한다.

```
Assets/Tests/EditMode/        ← Edit Mode 테스트 폴더
Assets/Tests/PlayMode/        ← Play Mode 테스트 폴더
```

각 폴더에 `.asmdef` 파일 생성:
- **EditMode .asmdef**: `Test Platforms` → `Editor` 체크, `References`에 `UnityEngine.TestRunner`, `UnityEditor.TestRunner` 추가
- **PlayMode .asmdef**: `Test Platforms` → `Player` + `Editor` 체크

### 3. Edit Mode 테스트 작성 (순수 로직 검증)

게임 오브젝트 없이 C# 로직만 테스트. ScriptableObject, 데이터 클래스, 계산 함수에 적합.

```csharp
using NUnit.Framework;
using UnityEngine;

public class PlayerStatsTests
{
    [Test]
    public void Modify_AttackMultiplier_AppliesCorrectly()
    {
        // Arrange
        var stats = ScriptableObject.CreateInstance<PlayerStats>();
        stats.BaseAttack = 10f;
        
        // Act
        stats.Modify(StatType.AttackMultiplier, 1.5f);
        
        // Assert
        Assert.AreEqual(15f, stats.Current.Attack);
    }

    [Test]
    public void HealthClamps_AboveMax_StaysAtMax()
    {
        var hp = new HealthComponent(100f);
        hp.Heal(200f);  // 최대치 초과 힐
        Assert.AreEqual(100f, hp.Current);
    }
}
```

### 4. Play Mode 테스트 작성 (런타임 동작 검증)

실제 Unity 씬을 로드하거나 MonoBehaviour가 필요한 테스트. `IEnumerator` + `yield` 사용.

```csharp
using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

public class ProjectilePoolTests
{
    [UnityTest]
    public IEnumerator Spawn_ThenDespawn_ReturnsToPool()
    {
        // Setup PoolManager
        var poolManagerGO = new GameObject("PoolManager");
        var pool = poolManagerGO.AddComponent<PoolManager>();
        
        // Spawn
        var prefab = Resources.Load<GameObject>("Projectile_Seed");
        var obj = PoolManager.Spawn(prefab, Vector2.zero, Quaternion.identity);
        Assert.IsTrue(obj.activeSelf);
        
        // Wait a frame
        yield return null;
        
        // Despawn
        PoolManager.Despawn(obj);
        Assert.IsFalse(obj.activeSelf);
        
        Object.Destroy(poolManagerGO);
    }
    
    [UnityTest]
    public IEnumerator GameManager_ChangeState_ToPause_FreezesTime()
    {
        // Time.timeScale을 직접 건드리지 않고 GameManager 상태를 검증
        GameManager.Instance.ChangeState(GameState.Paused);
        yield return null;
        Assert.AreEqual(GameState.Paused, GameManager.Instance.State);
        // OnionCat 규칙: Time.timeScale 직접 변경 금지 → GameManager 상태로만 확인
        GameManager.Instance.ChangeState(GameState.Gameplay);
    }
}
```

### 5. 자주 쓰는 Assert 패턴

```csharp
Assert.AreEqual(expected, actual);          // 값 동일
Assert.IsTrue(condition);                   // 조건 참
Assert.IsNull(obj);                         // null 확인
Assert.Throws<ArgumentException>(() => {    // 예외 발생 검증
    new Damage(-5f);                        // 음수 대미지 금지
});
Assert.That(value, Is.InRange(0f, 100f));   // 범위 검증
```

### 6. CLI로 테스트 실행 (CI/CD 연동)

```bash
# Unity 커맨드라인에서 테스트 실행
"C:/Users/feedb/AppData/Local/Unity/bin/unity.exe" \
  -runTests \
  -testPlatform editmode \
  -projectPath "C:/workspace/unity/Onioncat_AG" \
  -testResults "C:/workspace/test_results.xml" \
  -batchmode -quit

# 결과 파일 확인
cat "C:/workspace/test_results.xml"
```

### 7. 테스트 대상 우선순위

**테스트할 것** (순수 로직, 빠르게 검증 가능):
- `PlayerStats.Modify()` — 스탯 보정 계산 정확성
- `PoolManager.Spawn/Despawn` — 풀 상태 유지
- `UpgradeSystem` — 업그레이드 스택 적용 결과
- `RandomGeneration` — 씨드값 재현성 (같은 씨드 → 같은 결과)
- `DamageCalculation` — 저항/약점 배율 적용

**테스트 안 할 것** (UI·비주얼·Input):
- 스프라이트 렌더링, 애니메이션 전환
- Input System 실제 입력 시뮬레이션
- 씬 전체 통합 테스트 (→ 직접 플레이 테스트로)

---

## OnionCat 적용 포인트

### 즉시 도입 가능한 테스트 3가지

1. **StatType별 Modify 계산 검증**
   ```csharp
   // PlayerStats.Modify(StatType.DashCooldown, 0.5f)가
   // 실제로 대쉬 쿨타임을 절반으로 줄이는지
   ```

2. **공유 체력 heal/damage 경계값 테스트**
   ```csharp
   // HP 0 이하로 내려가지 않는지, 최대치 초과하지 않는지
   ```

3. **PoolManager 스트레스 테스트**
   ```csharp
   // 1000개 Spawn → 1000개 Despawn 후 활성 오브젝트 0개 확인
   ```

### 개발 워크플로우 통합 방법
1. 새 시스템 스크립트 작성
2. **Edit Mode 테스트 1~3개 추가** (5분 이내)
3. Test Runner에서 Run All → 초록불 확인
4. 이후 리팩터링/업그레이드 추가 시 자동 회귀 검증

---

## 참고 링크

- [Unity Test Framework 공식 문서](https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/index.html)
- [NUnit 공식 사이트 (Assert API)](https://nunit.org)
- [Unity Testing with Test Runner (Unity Learn)](https://learn.unity.com/tutorial/testing-with-test-runner)
- [Game Dev Beginner: Unity Testing Guide](https://gamedevbeginner.com/unity-testing-guide/)
- [Writing Unit Tests in Unity (Infallible Code)](https://www.youtube.com/watch?v=KzBMSVBr8sE)
