# ScriptableObject Event Channel Architecture

리서치 날짜: 2026-11-07

## 개요

ScriptableObject(SO) 기반 이벤트 채널 아키텍처는 Ryan Hipple이 Unite Austin 2017에서 발표한 패턴으로, **싱글톤 Event Bus 대신 SO 에셋 자체가 이벤트 채널 역할**을 한다.

OnionCat과의 관련성:
- 현재 `GameManager.OnStateChanged` 같은 C# 이벤트를 씬 간에 안전하게 쓸 수 있다
- 에디터에서 Inspector로 이벤트를 직접 연결 → 연결 관계가 눈에 보임
- 도메인 리로드(플레이 모드 진입/종료) 후 이벤트 연결이 끊기지 않음

**기존 Singleton Event Bus와의 차이**:
```
Singleton Bus: GameEvents.Instance.OnPlayerDamaged += handler;
 → 플레이 모드 진입 시 instance가 null → NullReferenceException 위험
 → 모든 이벤트가 한 파일에 집중 → God Object

SO Event Channel: [SerializeField] VoidEventChannelSO onPlayerDamaged;
 → Inspector에서 에셋 드래그 → 연결 관계 명시적
 → 에셋 단위로 분리 → 필요한 채널만 참조
```

---

## Unity 구현 방법

### 1. 기본 이벤트 채널 에셋 (매개변수 없음)

```csharp
// VoidEventChannelSO.cs
[CreateAssetMenu(menuName = "Events/Void Event Channel")]
public class VoidEventChannelSO : ScriptableObject
{
    public event Action OnEventRaised;

    public void RaiseEvent()
    {
        OnEventRaised?.Invoke();
    }
}
```

```csharp
// 발행자 (Publisher)
public class PlayerHealth : MonoBehaviour
{
    [SerializeField] private VoidEventChannelSO onPlayerDied;

    void Die()
    {
        onPlayerDied.RaiseEvent();
    }
}

// 구독자 (Subscriber)
public class GameOverUI : MonoBehaviour
{
    [SerializeField] private VoidEventChannelSO onPlayerDied;

    void OnEnable()  => onPlayerDied.OnEventRaised += ShowGameOver;
    void OnDisable() => onPlayerDied.OnEventRaised -= ShowGameOver;

    void ShowGameOver() { /* ... */ }
}
```

### 2. 타입 있는 이벤트 채널 (제네릭 베이스)

```csharp
// 베이스 클래스
public abstract class EventChannelSO<T> : ScriptableObject
{
    public event Action<T> OnEventRaised;
    public void RaiseEvent(T value) => OnEventRaised?.Invoke(value);
}

// 구체 타입 (CreateAssetMenu용으로 별도 클래스 필요)
[CreateAssetMenu(menuName = "Events/Int Event Channel")]
public class IntEventChannelSO : EventChannelSO<int> { }

[CreateAssetMenu(menuName = "Events/Float Event Channel")]
public class FloatEventChannelSO : EventChannelSO<float> { }

[CreateAssetMenu(menuName = "Events/GameObject Event Channel")]
public class GameObjectEventChannelSO : EventChannelSO<GameObject> { }
```

### 3. OnionCat 맞춤 — GameState 이벤트 채널

```csharp
[CreateAssetMenu(menuName = "Events/GameState Event Channel")]
public class GameStateEventChannelSO : EventChannelSO<GameState> { }
```

```csharp
// GameManager.cs 에서
[SerializeField] private GameStateEventChannelSO onStateChanged;

public void ChangeState(GameState newState)
{
    _state = newState;
    onStateChanged.RaiseEvent(newState);
}
```

```csharp
// 구독자 예시 (UpgradeSelectUI.cs)
[SerializeField] private GameStateEventChannelSO onStateChanged;

void OnEnable()  => onStateChanged.OnEventRaised += HandleStateChange;
void OnDisable() => onStateChanged.OnEventRaised -= HandleStateChange;

void HandleStateChange(GameState state)
{
    gameObject.SetActive(state == GameState.UpgradeSelect);
}
```

### 4. 에셋 폴더 구성 권장

```
Assets/
  Events/
    GameState_Changed.asset       ← GameStateEventChannelSO 인스턴스
    Player_Died.asset             ← VoidEventChannelSO
    Player_Damaged.asset          ← FloatEventChannelSO (피해량 전달)
    Enemy_Killed.asset            ← GameObjectEventChannelSO
    Room_Cleared.asset            ← VoidEventChannelSO
    Run_Started.asset             ← VoidEventChannelSO
```

### 5. 디버그용 에디터 확장 (선택)

```csharp
#if UNITY_EDITOR
[CustomEditor(typeof(VoidEventChannelSO))]
public class VoidEventChannelEditor : UnityEditor.Editor
{
    public override void OnInspectorGUI()
    {
        base.OnInspectorGUI();
        if (GUILayout.Button("Raise Event (Test)"))
            ((VoidEventChannelSO)target).RaiseEvent();
    }
}
#endif
```
→ Inspector에서 버튼 클릭으로 이벤트 테스트 가능

---

## OnionCat 적용 포인트

### 현재 상태와 문제점
OnionCat은 `GameManager.OnStateChanged`를 C# event로 직접 노출한다:
```csharp
public static event Action<GameState> OnStateChanged;
```
이것은 작동하지만:
- 씬 로드 시 static 이벤트 구독자가 null이 되면 silently 실패
- "어떤 오브젝트가 이 이벤트를 듣는지" 에디터에서 볼 방법이 없음
- 테스트 시 GameManager 없이 이벤트 발화가 불가

### 마이그레이션 전략 (점진적)

1단계: 에셋 생성
```
Assets/Events/GameState_Changed.asset 생성
```

2단계: GameManager에 채널 추가 (기존 event도 유지)
```csharp
[SerializeField] private GameStateEventChannelSO stateChangedChannel;

public void ChangeState(GameState newState) {
    _state = newState;
    OnStateChanged?.Invoke(newState);    // 기존 C# event (호환성 유지)
    stateChangedChannel?.RaiseEvent(newState);  // 새 SO 채널
}
```

3단계: 새로 만드는 UI 컴포넌트부터 SO 채널로 연결
4단계: 기존 C# event 구독자를 점진적으로 SO 채널로 이전

### 특히 유용한 케이스 — OnionCat에서

| 채널 | 발행자 | 구독자 |
|------|--------|--------|
| `Room_Cleared` | `RoomManager` | HUD, 카메라 아웃, 적 목록 초기화 |
| `Player_Damaged(float)` | `PlayerHealth` | HUD HP바, 화면 플래시, 사운드 |
| `Run_Started` | `DungeonManager` | UI 초기화, 음악 시작 |
| `Upgrade_Selected` | `UpgradeSelectUI` | RunData 갱신, 애니메이션 시작 |
| `Boss_Defeated` | `EnemyBase` | 연출 시퀀스 시작, 스테이지 전환 |

### 주의사항

- SO 에셋은 **씬 간에 공유**된다 → `OnEnable/OnDisable`에서 반드시 구독/해제 (메모리 누수 방지)
- **플레이 종료 시 구독자가 먼저 파괴**되면 채널에 dangling delegate가 남을 수 있다 → `OnDisable`에서 반드시 `-=`
- 채널 에셋이 너무 많아지면 관리 복잡 → 중요도 높은 이벤트 10~15개만 SO 채널, 나머지는 C# event 유지

---

## 참고 링크

- Ryan Hipple 원본 발표 (Unite Austin 2017): https://www.youtube.com/watch?v=raQ3iHhE_Kk
- Unity Blog - ScriptableObject Architecture: https://blog.unity.com/games/create-modular-game-architecture-in-unity-with-scriptableobjects
- Unity 공식 샘플 프로젝트 (Chop Chop): https://github.com/UnityTechnologies/com.unity.multiplayer.samples.coop (SO 이벤트 패턴 사용)
- 관련 GitHub: https://github.com/roboryantron/Unite2017 (Ryan Hipple 원본 코드)
