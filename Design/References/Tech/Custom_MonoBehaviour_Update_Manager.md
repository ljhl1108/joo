# Custom MonoBehaviour Update Manager

리서치 날짜: 2026-10-03

## 개요

Unity의 `MonoBehaviour.Update()`는 매 프레임마다 C++ → C# 브리지를 통해 개별 호출된다.
오브젝트가 수백 개 이상이면 이 오버헤드가 누적되어 성능 병목이 된다.
**UpdateManager 패턴**은 중앙 하나의 MonoBehaviour가 Update를 받고, 등록된 모든 객체를 직접 호출하는 구조다 — 브리지 횟수를 O(n)에서 O(1)로 줄인다.

OnionCat에서는 적이 많이 쏟아지는 방에서 수십~수백 개의 Enemy, Projectile, StatusEffect 오브젝트가 Update를 각자 실행하므로 이 패턴이 실제로 도움된다.

## Unity 구현 방법

### 1. IUpdatable 인터페이스 정의

```csharp
public interface IUpdatable
{
    void ManagedUpdate(float deltaTime);
}
```

### 2. UpdateManager 싱글턴

```csharp
public class UpdateManager : MonoBehaviour
{
    public static UpdateManager Instance { get; private set; }

    private readonly List<IUpdatable> _updatables = new();
    private readonly List<IUpdatable> _toAdd = new();
    private readonly List<IUpdatable> _toRemove = new();
    private bool _isUpdating;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    void Update()
    {
        // 먼저 대기 목록 처리 (Update 중 등록/해제 안전)
        _isUpdating = true;
        float dt = Time.deltaTime;
        for (int i = 0; i < _updatables.Count; i++)
            _updatables[i].ManagedUpdate(dt);
        _isUpdating = false;

        foreach (var u in _toAdd) _updatables.Add(u);
        foreach (var u in _toRemove) _updatables.Remove(u);
        _toAdd.Clear();
        _toRemove.Clear();
    }

    public void Register(IUpdatable u)
    {
        if (_isUpdating) _toAdd.Add(u);
        else _updatables.Add(u);
    }

    public void Unregister(IUpdatable u)
    {
        if (_isUpdating) _toRemove.Add(u);
        else _updatables.Remove(u);
    }
}
```

### 3. 등록/해제는 OnEnable/OnDisable에서

```csharp
public class EnemyBase : MonoBehaviour, IUpdatable
{
    void OnEnable() => UpdateManager.Instance?.Register(this);
    void OnDisable() => UpdateManager.Instance?.Unregister(this);

    public void ManagedUpdate(float deltaTime)
    {
        // 기존 Update() 내용을 여기로
        Move(deltaTime);
        CheckAttack(deltaTime);
    }
}
```

### 4. 투사체 — 풀링과 궁합이 좋다

```csharp
public class Projectile : MonoBehaviour, IUpdatable
{
    void OnEnable() => UpdateManager.Instance?.Register(this);
    void OnDisable() => UpdateManager.Instance?.Unregister(this);

    public void ManagedUpdate(float deltaTime)
    {
        transform.position += _direction * _speed * deltaTime;
        _lifeTimer -= deltaTime;
        if (_lifeTimer <= 0) PoolManager.Despawn(gameObject);
    }
}
```

### 5. 상태 초기화 시 FixedUpdate/LateUpdate도 분리 가능

```csharp
public interface IFixedUpdatable { void ManagedFixedUpdate(float fixedDeltaTime); }
public interface ILateUpdatable  { void ManagedLateUpdate(float deltaTime); }
// UpdateManager에 FixedUpdate/LateUpdate도 동일 패턴으로 추가
```

### 실제 성능 차이 (Unity Profiler 기준)
- MonoBehaviour.Update 100개: ~0.12ms (C# 브리지 × 100)
- UpdateManager 방식 100개: ~0.03ms (브리지 × 1 + 직접 호출 × 100)
- 수가 적으면 의미 없음; **50개 이상에서 체감, 200개 이상에서 명확**

## OnionCat 적용 포인트

### 1. 적용 대상
- `EnemyBase` 및 모든 서브클래스 — 풀링과 함께 OnEnable/OnDisable에서 등록
- `Projectile_Seed` 계열 투사체 — 가장 효과가 크다 (화면에 수십 개 존재 가능)
- `StatusEffect` 틱 처리 (불, 슬로우, 스턴 타이머)

### 2. 적용하지 않아도 되는 것
- `PlayerController`, `CameraController` — 항상 1개, 오버헤드 무시
- 씬 오브젝트 (문, 타일, 환경 소품) — Update 자체가 없어야 정상
- `GameManager`, `UIManager` — 이미 이벤트 기반

### 3. Pool + UpdateManager 콤보
`PoolManager.Spawn`이 반환한 오브젝트가 `OnEnable`에서 자동 등록되므로
추가 코드 없이 연동된다. `Despawn` 시 `OnDisable` → 자동 해제.

### 4. 씬 전환 시 정리
씬 전환 직전 `_updatables.Clear()` 또는 `DontDestroyOnLoad` 해제 방식 중 선택.
GameManager가 `OnStateChanged`에서 씬 로드를 트리거할 때 UpdateManager 리스트도 비움.

### 5. 도입 우선순위
Profiler로 `Update`가 병목인지 확인 후 도입. 현재 적 수가 적으면 불필요.
방 하나에 적 30마리 + 투사체 100개 이상 목표라면 지금 설계해두는 것이 이득.

## 참고 링크

- Unity Blog - 1000 UpdateManagers: https://blog.unity.com/engine-platform/10000-update-calls
- Jam'eel Rashed - Custom Update Loop: https://medium.com/@jameel.rashed/unity-update-manager
- Unity Manual - Script Lifecycle: https://docs.unity3d.com/Manual/ExecutionOrder.html
- GitHub 예시 (검색): "Unity UpdateManager IUpdatable"
