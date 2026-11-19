# Coop Split Ownership UI System (협동 UI 분할 소유권 시스템)

리서치 날짜: 2026-11-19

## 개요

2인 로컬 협동 게임에서 하나의 UI 화면을 두 플레이어가 **각자 자기 쪽만 조작**하는 시스템.
OnionCat에서 가장 필요한 곳: 장비 선택 화면(고양이가 왼쪽, 작물이 오른쪽 선택),
가방 화면(고양이가 왼쪽 슬롯, 작물이 오른쪽 슬롯 드래그).

이 패턴은 보기보다 까다롭다:
- 각 플레이어가 자기 커서/포커스를 독립적으로 이동
- 양쪽이 동시에 선택을 완료해야 화면이 닫힘 (또는 한쪽만 완료하면 대기 표시)
- 한쪽이 아직 고르는 중일 때 다른 쪽이 먼저 선택 완료하면 UI/입력이 꼬임

---

## Unity 구현 방법

### 1. 소유권 분리의 기본 구조

```csharp
public enum UIOwner { Cat, Onion, Both }

public interface ISplitUI
{
    void OnInput(UIOwner owner, Vector2 navigate, bool confirm, bool cancel);
    bool IsReady(UIOwner owner);
}
```

### 2. 각 플레이어별 독립 포커스 커서

한 화면에 두 개의 독립적인 Selection Cursor를 운용:
```csharp
public class SplitOwnershipPanel : MonoBehaviour
{
    [SerializeField] SelectionCursor catCursor;
    [SerializeField] SelectionCursor onionCursor;

    void Update()
    {
        // Cat (Gamepad)
        catCursor.Feed(catInput.Navigate.ReadValue<Vector2>(),
                       catInput.Confirm.WasPressedThisFrame());

        // Onion (Keyboard)
        onionCursor.Feed(onionInput.Navigate.ReadValue<Vector2>(),
                         onionInput.Confirm.WasPressedThisFrame());
    }
}
```

### 3. 선택 완료 대기 로직 — 양쪽 모두 완료 시 진행

```csharp
public class UpgradeSelectUI : MonoBehaviour, ISplitUI
{
    private bool _catReady;
    private bool _onionReady;

    public void OnConfirm(UIOwner owner)
    {
        if (owner == UIOwner.Cat) _catReady = true;
        if (owner == UIOwner.Onion) _onionReady = true;

        UpdateReadyVisual(owner);

        if (_catReady && _onionReady)
            GameManager.Instance.ChangeState(GameState.Combat); // 화면 닫기
    }

    private void UpdateReadyVisual(UIOwner owner)
    {
        // 먼저 선택한 쪽에 "대기 중" 애니메이션 표시
        // 아직 안 고른 쪽에 깜빡이는 커서 강조
    }
}
```

### 4. 한쪽이 먼저 완료했을 때 입력 잠금

```csharp
public class SelectionCursor : MonoBehaviour
{
    private bool _locked;

    public void Lock() { _locked = true; /* 선택 완료 표시 */ }

    public void Feed(Vector2 nav, bool confirm)
    {
        if (_locked) return; // 이미 선택함 → 입력 무시
        // 커서 이동, 선택 처리
    }
}
```

### 5. 타임아웃 — 한쪽이 AFK일 때

한 플레이어가 5초 내로 선택 안 하면 자동으로 임의 선택:
```csharp
IEnumerator AutoSelectTimeout(UIOwner owner, float timeout)
{
    yield return new WaitForSecondsRealtime(timeout);
    if (!IsReady(owner))
    {
        SelectRandom(owner); // 무작위 선택
        OnConfirm(owner);
    }
}
```

### 6. 장비 가방 화면 — 드래그&드롭 소유권

```csharp
public class BagSlot : MonoBehaviour
{
    [SerializeField] UIOwner owner; // Cat / Onion / Both

    public bool CanInteract(UIOwner interactor)
    {
        return owner == UIOwner.Both || owner == interactor;
    }
}
```

### 7. UI EventSystem 복수 처리 (중요!)

Unity EventSystem은 기본적으로 1개만 존재. 2인 동시 UI 조작은 커스텀 처리 필요:
```csharp
// 방법 A: EventSystem을 쓰지 않고 직접 레이캐스트
// 방법 B: MultiplayerEventSystem (Unity Input System 패키지 내장)

// Unity Input System의 PlayerInput + MultiplayerEventSystem 사용
// PlayerInputManager가 각 플레이어에게 별도 EventSystem 할당
```

```
[PlayerInputManager]
  ├── Player1 (Cat) ← MultiplayerEventSystem1 연결
  └── Player2 (Onion) ← MultiplayerEventSystem2 연결
```

---

## OnionCat 적용 포인트

### 장비 선택 화면 (UpgradeSelectUI)
현재 고양이와 작물이 동시에 각자 3개 중 1개 선택.
- 화면 왼쪽 = 고양이 카드 (게임패드 방향키+A로 조작)
- 화면 오른쪽 = 작물 카드 (키보드 방향키+Enter 또는 마우스 클릭)
- 한쪽이 먼저 고르면 그 카드에 체크 표시 + "상대방 대기 중" 애니메이션
- 양쪽 완료 시 선택된 장비 적용 → 전투 복귀

### 가방 화면 슬롯 소유권
공유 가방이므로 두 플레이어가 모두 볼 수 있지만:
- 고양이 장비 슬롯(5칸)은 Cat만 조작
- 작물 장비 슬롯(5칸)은 Onion만 조작
- 소모품 가방(공유)은 Both 가능

### 타임아웃 설정 권장
- 싱글 플레이 모드(한 명이 둘 다 조작): 5초 자동 선택 타이머는 OFF
- 실제 2인 플레이: 30초 타임아웃 → 자동 선택 (AFK 방지)

### MultiplayerEventSystem 사용 여부
OnionCat은 현재 UI 조작을 직접 C# 코드로 하는 것으로 보임.
유니티의 `MultiplayerEventSystem`을 붙이면 기존 방식과 충돌할 수 있으므로,
지금처럼 `OnInput(UIOwner)` 방식의 직접 처리가 더 안전.

---

## 참고 링크

- [Unity MultiplayerEventSystem Docs](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.8/manual/UISupport.html#multiple-players)
- [Unity Input System: Co-op UI](https://gamedevbeginner.com/input-in-unity-made-easy-complete-guide-to-the-new-system/)
- [UI Split Screen Co-op Pattern – GameDev StackExchange](https://gamedev.stackexchange.com/questions/tagged/cooperative)
- It Takes Two (EA/Hazelight) — 2인 협동 UI 소유권 분리의 최고 사례
- Lovers in a Dangerous Spacetime — 싱글 화면에서 두 커서 운용 방식 참고
