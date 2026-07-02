# Unity Event Bus / C# 이벤트 패턴

리서치 날짜: 2026-07-02

## 개요

Event Bus(이벤트 버스)는 서로 다른 오브젝트가 직접 참조 없이 신호를 주고받는 패턴이다.
OnionCat에서 Cat과 Onion은 하나의 몸을 공유하지만 코드는 분리되어야 한다 — 이 패턴 없이는 `catScript.GetComponent<OnionScript>()` 같은 강결합이 생겨 유지보수가 어려워진다.

**왜 중요한가:**
- Cat 시스템 ↔ Onion 시스템 분리하면서도 협동 연동 가능
- UI · 사운드 · 파티클이 게임플레이 로직 모르고도 반응 가능
- 테스트·수정 시 영향 범위 최소화

---

## Unity 구현 방법

### 방법 1: Static C# Action (초보자 권장)

```csharp
// PlayerEventBus.cs — 어떤 폴더든 배치, MonoBehaviour 불필요
public static class PlayerEventBus
{
    // Cat 관련 이벤트
    public static event Action OnCatDash;
    public static event Action<int> OnCatHit;       // 남은 HP 전달
    public static event Action OnCatDowned;

    // Onion 관련 이벤트
    public static event Action OnParrySuccess;
    public static event Action<Vector2> OnProjectileFired;

    // 런 전체 이벤트
    public static event Action<int> OnEnemyKilled;  // 처치 수 누적

    // 발행(Publish)
    public static void PublishCatDash()    => OnCatDash?.Invoke();
    public static void PublishParry()      => OnParrySuccess?.Invoke();
    public static void PublishCatHit(int hp) => OnCatHit?.Invoke(hp);
    public static void PublishCatDowned()  => OnCatDowned?.Invoke();
    public static void PublishEnemyKilled(int count) => OnEnemyKilled?.Invoke(count);
}
```

```csharp
// CatController.cs — 이벤트 발행
void PerformDash()
{
    // 대시 로직 ...
    PlayerEventBus.PublishCatDash();   // 발행만. Onion이 어떻게 반응할지 모름 (= 좋은 것)
}

void TakeDamage(int amount)
{
    currentHp -= amount;
    PlayerEventBus.PublishCatHit(currentHp);
    if (currentHp <= 0) PlayerEventBus.PublishCatDowned();
}
```

```csharp
// OnionController.cs — 이벤트 구독
void OnEnable()
{
    PlayerEventBus.OnCatDash     += HandleCatDash;
    PlayerEventBus.OnParrySuccess += HandleOwnParry;
}

void OnDisable()
{
    PlayerEventBus.OnCatDash     -= HandleCatDash;  // 반드시 해제! 메모리 누수 방지
    PlayerEventBus.OnParrySuccess -= HandleOwnParry;
}

void HandleCatDash()
{
    // Cat이 대시할 때 Onion 자동 반응 (예: 잠깐 무적)
    StartCoroutine(BriefInvincibility(0.15f));
}
```

---

### 방법 2: ScriptableObject 기반 Event Channel (규모 확장 시)

```csharp
// GameEvent.cs — ScriptableObject 에셋으로 생성
[CreateAssetMenu(menuName = "Events/GameEvent")]
public class GameEvent : ScriptableObject
{
    private List<GameEventListener> listeners = new();

    public void Raise()
    {
        for (int i = listeners.Count - 1; i >= 0; i--)
            listeners[i].OnEventRaised();
    }

    public void RegisterListener(GameEventListener l)   => listeners.Add(l);
    public void UnregisterListener(GameEventListener l) => listeners.Remove(l);
}

// GameEventListener.cs — 컴포넌트로 오브젝트에 붙임
public class GameEventListener : MonoBehaviour
{
    [SerializeField] private GameEvent gameEvent;
    [SerializeField] private UnityEvent response;

    void OnEnable()  => gameEvent.RegisterListener(this);
    void OnDisable() => gameEvent.UnregisterListener(this);
    public void OnEventRaised() => response.Invoke();
}
```

사용: `catDashEvent.asset` 생성 → CatController에서 `catDashEvent.Raise()` → OnionController의 GameEventListener의 `response`에 메서드 드래그

---

### 주의사항

```csharp
// ❌ 틀린 패턴: OnDisable에서 구독 해제 안 함 → 씬 전환 후 NullReferenceException
void OnEnable() { PlayerEventBus.OnCatDash += HandleCatDash; }
// OnDisable 없음 → 버그

// ✅ 올바른 패턴: 항상 쌍으로
void OnEnable()  { PlayerEventBus.OnCatDash += HandleCatDash; }
void OnDisable() { PlayerEventBus.OnCatDash -= HandleCatDash; }

// ❌ 틀린 패턴: 이벤트 발행 전 null 체크 없음 → 구독자 0명일 때 NullReferenceException
PlayerEventBus.OnCatDash(); // crash!

// ✅ 올바른 패턴: ?. 연산자로 null 안전 호출
PlayerEventBus.OnCatDash?.Invoke();
```

---

## OnionCat 적용 포인트

### 즉시 구현 가능한 이벤트 목록

| 이벤트 | 발행 위치 | 구독 위치 | 효과 |
|---|---|---|---|
| `OnCatDash` | CatController.PerformDash | OnionController | Onion 잠깐 무적 (대시 연동) |
| `OnParrySuccess` | OnionController.Parry | CatController | 다음 슬래시 2배 데미지 |
| `OnCatDowned` | CatController.TakeDamage | OnionController, HUD | 부활 UI 표시, Onion 비상 모드 |
| `OnEnemyKilled` | EnemyBase.Die | RunStatsTracker, HUD | 처치 수 UI 업데이트 |
| `OnCatHit` | CatController.TakeDamage | HPBar, CameraShake | HP UI 갱신, 카메라 진동 |
| `OnProjectileFired` | OnionController.Fire | AudioManager | 발사음 재생 (직접 참조 없이) |

### 아키텍처 권장 구조

```
Assets/Scripts/
├── Events/
│   └── PlayerEventBus.cs      ← static 이벤트 허브
├── Player/
│   ├── CatController.cs       ← 발행 + 자신 이벤트 수신
│   └── OnionController.cs     ← 발행 + Cat 이벤트 수신
├── UI/
│   └── HUDManager.cs          ← PlayerEventBus 구독만 (플레이어 직참 없음)
└── Audio/
    └── AudioManager.cs        ← PlayerEventBus 구독만
```

### 협동 시너지 이벤트 체인 예시
```
1. Cat 대시 → OnCatDash 발행
2. OnionController 수신 → 방어막 잠깐 자동 전개 (연타 회피 보조)
3. 방어막이 적 탄환 막음 → OnParrySuccess 발행
4. CatController 수신 → 슬래시 데미지 ×1.5 버프
```
→ 이 체인이 코드 직접 연결 없이 이벤트 버스만으로 구성됨

---

## 참고 링크

- Unity 공식 - C# Events 설명: https://docs.unity3d.com/Manual/UnityEvents.html
- Ryan Hipple - ScriptableObject Game Architecture (Unite Austin 2017): https://youtu.be/raQ3iHhE_Kk
- Jason Storey - Game Event System (튜토리얼): https://youtu.be/4_DTAnigmaQ
- Unity Blog - Event-driven architecture: https://unity.com/how-to/architect-game-code-scriptable-objects
