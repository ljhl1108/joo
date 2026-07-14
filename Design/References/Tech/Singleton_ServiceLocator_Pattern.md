# 싱글톤 & 서비스 로케이터 패턴

리서치 날짜: 2026-07-14

## 개요

Unity 프로젝트에서 GameManager, AudioManager, UIManager 같은 전역 시스템에 어디서든 접근해야 할 때 필요한 아키텍처 패턴.
OnionCat처럼 씬 전환이 있는 게임에서는 초반부터 올바른 싱글톤 구조를 잡지 않으면 중반에 전체 리팩토링이 필요해진다.

---

## Unity 구현 방법

### 1. 기본 싱글톤 패턴 (MonoBehaviour)

```csharp
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }
}
```

**사용**: `GameManager.Instance.StartRun();`

**주의점**:
- `Awake()`에서 설정해야 다른 컴포넌트의 `Start()`보다 먼저 초기화됨
- `DontDestroyOnLoad` 없으면 씬 전환 시 파괴됨
- 씬에 2개 이상 있으면 중복 제거 로직 필수

---

### 2. 제네릭 싱글톤 기반 클래스 (재사용 가능)

```csharp
public abstract class Singleton<T> : MonoBehaviour where T : MonoBehaviour
{
    public static T Instance { get; private set; }

    protected virtual void Awake()
    {
        if (Instance != null)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this as T;
        DontDestroyOnLoad(gameObject);
    }
}

// 사용 예
public class AudioManager : Singleton<AudioManager>
{
    public void PlaySFX(AudioClip clip) { /* ... */ }
}
```

**장점**: 한 번 만들어두면 모든 매니저가 상속만 하면 됨

---

### 3. 씬 한정 싱글톤 (DontDestroyOnLoad 없는 버전)

게임 내 HUD나 방(Room) 내부 매니저처럼 씬이 바뀌면 새로 만들어야 할 때:

```csharp
public class RoomManager : MonoBehaviour
{
    public static RoomManager Instance { get; private set; }

    void Awake()
    {
        // DontDestroyOnLoad 없음 → 씬 전환 시 자동 파괴 후 새 인스턴스
        Instance = this;
    }

    void OnDestroy()
    {
        if (Instance == this) Instance = null;
    }
}
```

---

### 4. 서비스 로케이터 패턴 (더 유연한 방법)

싱글톤 대신 서비스를 등록/조회하는 중앙 허브:

```csharp
public static class ServiceLocator
{
    private static Dictionary<System.Type, object> _services = new();

    public static void Register<T>(T service) where T : class
    {
        _services[typeof(T)] = service;
    }

    public static T Get<T>() where T : class
    {
        if (_services.TryGetValue(typeof(T), out var service))
            return service as T;
        Debug.LogError($"Service not found: {typeof(T).Name}");
        return null;
    }

    public static void Clear() => _services.Clear();
}

// 등록 (GameBootstrapper.cs 등에서)
void Awake()
{
    ServiceLocator.Register<IAudioManager>(audioManager);
    ServiceLocator.Register<IGameStateManager>(gameStateManager);
}

// 사용 (어느 스크립트에서든)
ServiceLocator.Get<IAudioManager>().PlaySFX(clip);
```

**장점**:
- 인터페이스 기반이라 테스트 시 Mock으로 교체 가능
- 싱글톤보다 결합도가 낮음
- 씬 전환 시 `ServiceLocator.Clear()` 후 재등록 가능

---

### 5. OnionCat 권장 구조 (초보자용 실용적 접근)

```
[영구 유지 - DontDestroyOnLoad]
  GameManager      : 런 상태, 씬 전환
  AudioManager     : BGM, SFX 재생
  SaveManager      : 데이터 저장/로드

[씬 한정]
  RoomManager      : 현재 방 상태, 적 스폰
  UIManager        : HUD, 메뉴 제어
  SpawnManager     : 적/아이템 스폰 위치
```

**초기화 순서 보장**: GameBootstrapper 오브젝트 하나에 Script Execution Order 설정
- Project Settings → Script Execution Order에서 GameManager를 -100으로 설정

---

### 6. 흔한 실수와 해결책

**실수 1: 씬 로드 후 Instance가 null**
```csharp
// 잘못된 예: Start()에서 Instance 참조 (Awake보다 늦을 수 있음)
void Start() { GameManager.Instance.DoSomething(); }

// 올바른 예: 방어 코드 추가
void Start()
{
    if (GameManager.Instance == null) return;
    GameManager.Instance.DoSomething();
}
```

**실수 2: 씬 전환 후 인스턴스가 2개**
- DontDestroyOnLoad 오브젝트가 있는 씬을 다시 로드하면 중복 생성
- 해결: Awake()에서 중복 체크 + Destroy 로직 필수

**실수 3: 순환 의존성**
- GameManager → AudioManager → GameManager 참조 순환
- 해결: 이벤트/델리게이트로 느슨한 결합 (Event Bus 패턴 참고)

---

## OnionCat 적용 포인트

### 1. 필수 싱글톤 목록
```
GameManager      : 게임 상태(메인메뉴/인게임/게임오버), 씬 전환
AudioManager     : BGM/SFX 재생, 볼륨 조절
RunDataManager   : 현재 런 데이터 (체력, 업그레이드, 층수)
SaveManager      : 영구 데이터 (최고 기록, 설정)
```

### 2. 씬 한정으로 두어야 할 것
```
RoomManager      : 방 클리어 조건, 문 개폐
EnemySpawner     : 현재 방 적 스폰
PlayerController : 플레이어 참조 (씬마다 존재하므로)
```

### 3. 초기화 순서 보장 방법
`GameBootstrapper.cs`를 만들어 Script Execution Order -100으로 설정:
```csharp
void Awake()
{
    // 모든 매니저가 이 시점에 초기화됨을 보장
    DontDestroyOnLoad(gameObject);
}
```

### 4. 왜 초보자에게 싱글톤이 중요한가
- `FindObjectOfType()`를 Update()에서 쓰면 성능 저하 → 싱글톤으로 직접 참조
- 씬 전환 후 매니저 찾기 실패 → DontDestroyOnLoad 싱글톤으로 해결
- 코드 어디서든 접근 → 개발 속도 향상

---

## 참고 링크

- Unity 공식 - DontDestroyOnLoad: https://docs.unity3d.com/ScriptReference/Object.DontDestroyOnLoad.html
- Unity 공식 - Script Execution Order: https://docs.unity3d.com/Manual/class-MonoManager.html
- Game Programming Patterns - Singleton: https://gameprogrammingpatterns.com/singleton.html
- Game Programming Patterns - Service Locator: https://gameprogrammingpatterns.com/service-locator.html
- Unity Patterns YouTube (Jason Weimann): https://www.youtube.com/@Unity3dCollege
- Infallible Code - Singleton Tutorial: https://www.youtube.com/@InfallibleCode
