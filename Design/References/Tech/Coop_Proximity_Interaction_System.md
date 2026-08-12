# Coop Proximity Interaction System

리서치 날짜: 2026-08-12

## 개요

두 플레이어가 **동시에 또는 순차적으로 특정 행동을 해야** 발동되는 상호작용 시스템.  
OnionCat처럼 공유 신체 구조에서는 두 캐릭터가 사실상 한 위치에 있지만,  
특정 오브젝트를 "두 플레이어가 함께 활성화"하는 패턴이 게임 전반에 반복된다.

로그라이크에서의 응용 예시:
- 특수 제단/버튼: P1이 버튼 위에 서 있는 동안 P2가 특정 오브젝트를 조준/쏘아야 활성화
- 협동 자물쇠: 두 플레이어가 동시에 상호작용 버튼을 누르는 문
- 소환 의식: P1이 적을 막는 동안 P2가 특정 횟수 투사체를 적중시키면 완료
- 회복 역할 분담: P1이 적을 막고 P2가 힐 포탈을 조작

---

## Unity 구현 방법

### 기본 구조: 두 플레이어 동시 감지

```csharp
using UnityEngine;
using UnityEngine.Events;

public class CoopInteractable : MonoBehaviour
{
    [SerializeField] private float interactRadius = 1.5f;
    [SerializeField] private bool requireSimultaneous = true; // 동시 vs 순차
    [SerializeField] private float simultaneousWindow = 0.5f; // 동시 허용 시간차
    [SerializeField] private UnityEvent onBothPlayersInteract;

    private bool p1Ready = false;
    private bool p2Ready = false;
    private float p1ReadyTime = -999f;
    private float p2ReadyTime = -999f;

    // 각 플레이어 Input에서 호출
    public void SetPlayerReady(int playerIndex, bool ready)
    {
        if (playerIndex == 0)
        {
            p1Ready = ready;
            if (ready) p1ReadyTime = Time.time;
        }
        else
        {
            p2Ready = ready;
            if (ready) p2ReadyTime = Time.time;
        }
        CheckTrigger();
    }

    private void CheckTrigger()
    {
        if (!p1Ready || !p2Ready) return;

        if (requireSimultaneous)
        {
            if (Mathf.Abs(p1ReadyTime - p2ReadyTime) <= simultaneousWindow)
                Activate();
        }
        else
        {
            Activate();
        }
    }

    private void Activate()
    {
        p1Ready = p2Ready = false;
        onBothPlayersInteract.Invoke();
    }
}
```

### Collider 기반 근접 감지

```csharp
// OnionCat는 고양이 한 몸이므로 근접 감지는 단순화 가능
// 단, 파(P2)의 조준 방향이 오브젝트를 향하는지 별도 체크

public class CoopProximityZone : MonoBehaviour
{
    [SerializeField] private CoopInteractable target;

    // P1(고양이)이 범위 안에 들어왔는지
    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
            target.SetPlayerReady(0, true);
    }

    private void OnTriggerExit2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
            target.SetPlayerReady(0, false);
    }
}
```

### P2 조준 기반 인터랙션 (OnionCat 특화)

```csharp
// P2(파)가 특정 오브젝트를 조준하면 인터랙션 가능 상태
public class AimInteractable : MonoBehaviour
{
    [SerializeField] private CoopInteractable coopTarget;
    [SerializeField] private float aimAngleThreshold = 20f; // 조준 허용 각도

    private void Update()
    {
        Vector2 aimDir = CropController.Instance.AimDirection; // P2 조준 방향
        Vector2 toObject = (transform.position - CropController.Instance.transform.position).normalized;
        
        float angle = Vector2.Angle(aimDir, toObject);
        bool isAiming = angle <= aimAngleThreshold;
        coopTarget.SetPlayerReady(1, isAiming);
    }
}
```

---

### 순차 인터랙션 (A 후 B 순서)

```csharp
public class SequentialCoopInteractable : MonoBehaviour
{
    private enum State { WaitingForFirst, WaitingForSecond, Complete }
    
    [SerializeField] private int firstPlayerIndex = 0; // P1 먼저
    [SerializeField] private float timeoutSeconds = 5f;
    [SerializeField] private UnityEvent onComplete;
    
    private State state = State.WaitingForFirst;
    private float stepTime;

    public void PlayerInteract(int playerIndex)
    {
        switch (state)
        {
            case State.WaitingForFirst:
                if (playerIndex == firstPlayerIndex)
                {
                    state = State.WaitingForSecond;
                    stepTime = Time.time;
                }
                break;
            case State.WaitingForSecond:
                if (playerIndex != firstPlayerIndex)
                {
                    if (Time.time - stepTime < timeoutSeconds)
                    {
                        state = State.Complete;
                        onComplete.Invoke();
                    }
                }
                break;
        }
    }

    private void Update()
    {
        // 타임아웃 시 리셋
        if (state == State.WaitingForSecond && Time.time - stepTime > timeoutSeconds)
            state = State.WaitingForFirst;
    }
}
```

---

### 진행 표시 UI (Fill Bar)

```csharp
// 두 플레이어가 채널링하는 동안 진행 바를 채우는 방식
public class CoopChannelInteractable : MonoBehaviour
{
    [SerializeField] private float channelDuration = 2f;
    [SerializeField] private UnityEvent onChannelComplete;
    
    private float progress = 0f;
    private bool p1Channeling;
    private bool p2Channeling;

    // 두 명 모두 채널링 중일 때 2배 속도
    private void Update()
    {
        int activeCount = (p1Channeling ? 1 : 0) + (p2Channeling ? 1 : 0);
        float rate = activeCount == 2 ? 2f : activeCount;
        
        progress += (rate / channelDuration) * Time.deltaTime;
        progress = Mathf.Clamp01(progress);
        
        UpdateUI(progress);
        
        if (progress >= 1f)
        {
            onChannelComplete.Invoke();
            progress = 0f;
        }
    }
    
    private void UpdateUI(float value)
    {
        // [SerializeField] Slider channelBar — 유니티 에디터에서 드래그 앤 드롭 설정 필요
    }
}
```

---

## OnionCat 적용 포인트

### OnionCat 구조 특수성
- P1(고양이)과 P2(파)는 **같은 위치**에 있음 → 개별 근접 감지 불필요
- 대신 "P1이 공격 버튼 누름" + "P2가 특정 방향 조준" 조합으로 구성
- 근접 인터랙션은 고양이 위치 기준 단일 Trigger로 충분

### 구체적 활용 시나리오

1. **협동 자물쇠 방문**  
   - P1: 상호작용 버튼 홀드 (고양이가 버튼 위에 섬)
   - P2: 문 위의 특정 인장을 조준·발사
   - 두 조건 동시 충족 시 문 열림

2. **강화 제단**  
   - P1: 제단 범위 안에 위치
   - P2: 4방향 심볼을 순서대로 조준 (화살 잠금 퍼즐 느낌)
   - 완료 시 해당 런에서 강력한 버프 획득

3. **긴급 부활 의식**  
   - 파(P2)가 HP 0으로 쓰러진 상태
   - P1: 파 근처에 서서 상호작용 버튼 홀드
   - 채널링 완료 시 파 부활 (체력 일부 회복)

4. **비밀 방 진입**  
   - 벽의 특정 문양을 P2가 조준
   - P1은 대시로 해당 벽에 충돌
   - 두 조건이 0.3초 내 발생 시 비밀 방 열림

### 인풋 처리 주의사항
- New Input System에서 `playerInput.actions["Interact"].ReadValue<float>()` 으로 홀드 감지
- 두 플레이어 인풋은 별도 `InputActionAsset`로 분리 관리 (LocalCoop_Input_System 참고)

---

## 참고 링크

- Unity 공식 — Trigger 이벤트: https://docs.unity3d.com/Manual/CollidersOverview.html
- Unity UnityEvents: https://docs.unity3d.com/Manual/UnityEvents.html
- New Input System 멀티플레이어: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.6/manual/PlayerInput.html
- GDC — Cooperative Game Design: https://www.gdcvault.com/play/1023329/Designing-and-Building-Next-Gen
