# Input 버퍼링 & 콤보 입력 시스템

리서치 날짜: 2026-06-24

## 개요

**입력 버퍼링(Input Buffering)**이란, 플레이어의 입력을 일정 프레임 동안 저장해두고 조건이 충족되면 뒤늦게 실행하는 기술이다. 격투 게임, 액션 게임에서 필수적이며, OnionCat에서는 다음 상황에 핵심적이다:

- 대시 중 슬래시 입력 예약 → 대시 끝나자마자 자동 실행
- 패리 직전 쉴드 입력 → 패리 타이밍 관용도 향상
- 연속기(콤보) 입력 → 슬래시 → 슬래시 → 스킬 연계

버퍼링이 없으면 프레임 단위로 입력해야 해서 게임이 불필요하게 어렵게 느껴진다.

---

## Unity 구현 방법

### 1. 기본 입력 버퍼 (Queue 방식)

```csharp
public class InputBuffer : MonoBehaviour
{
    private struct BufferedInput
    {
        public string ActionName;
        public float Timestamp;
    }

    [SerializeField] private float bufferWindow = 0.15f; // 150ms 버퍼 윈도우
    private Queue<BufferedInput> _buffer = new Queue<BufferedInput>();

    // 입력 발생 시 버퍼에 등록
    public void RegisterInput(string actionName)
    {
        _buffer.Enqueue(new BufferedInput
        {
            ActionName = actionName,
            Timestamp = Time.time
        });
    }

    // 조건이 충족됐을 때 버퍼에서 꺼내기
    public bool ConsumeInput(string actionName)
    {
        while (_buffer.Count > 0)
        {
            var input = _buffer.Peek();

            // 만료된 입력 제거
            if (Time.time - input.Timestamp > bufferWindow)
            {
                _buffer.Dequeue();
                continue;
            }

            if (input.ActionName == actionName)
            {
                _buffer.Dequeue();
                return true;
            }
            break;
        }
        return false;
    }
}
```

### 2. New Input System과 연동

```csharp
// PlayerInput 컴포넌트의 액션 콜백에서 버퍼 등록
private void OnSlash(InputAction.CallbackContext ctx)
{
    if (ctx.performed)
        _inputBuffer.RegisterInput("Slash");
}

private void OnDash(InputAction.CallbackContext ctx)
{
    if (ctx.performed)
        _inputBuffer.RegisterInput("Dash");
}

// 상태머신에서 버퍼 소비
private void Update()
{
    if (currentState == PlayerState.Dashing)
    {
        // 대시 중에도 슬래시 입력을 버퍼에서 확인
        if (_inputBuffer.ConsumeInput("Slash"))
            _pendingSlash = true; // 대시 끝나면 실행
    }
}
```

### 3. 콤보 시스템 (시퀀스 입력)

```csharp
public class ComboSystem : MonoBehaviour
{
    [System.Serializable]
    public struct ComboEntry
    {
        public string[] Sequence;   // ["Slash", "Slash", "Dash"]
        public string ResultAction; // "SlashDashCombo"
        public float TimeLimit;     // 0.5초 내에 입력해야
    }

    [SerializeField] private ComboEntry[] combos;
    [SerializeField] private float comboTimeout = 0.5f;

    private List<string> _inputHistory = new List<string>();
    private float _lastInputTime;

    public string RegisterAndCheck(string input)
    {
        // 타임아웃 경과 시 초기화
        if (Time.time - _lastInputTime > comboTimeout)
            _inputHistory.Clear();

        _inputHistory.Add(input);
        _lastInputTime = Time.time;

        // 최대 길이 제한
        if (_inputHistory.Count > 5)
            _inputHistory.RemoveAt(0);

        // 콤보 매칭 확인
        foreach (var combo in combos)
        {
            if (MatchesSequence(combo.Sequence))
            {
                _inputHistory.Clear();
                return combo.ResultAction;
            }
        }
        return input; // 콤보 없으면 단일 입력 반환
    }

    private bool MatchesSequence(string[] sequence)
    {
        if (_inputHistory.Count < sequence.Length) return false;
        int offset = _inputHistory.Count - sequence.Length;
        for (int i = 0; i < sequence.Length; i++)
        {
            if (_inputHistory[offset + i] != sequence[i]) return false;
        }
        return true;
    }
}
```

### 4. 패리 타이밍 버퍼 (관용 윈도우)

```csharp
public class ParrySystem : MonoBehaviour
{
    [SerializeField] private float parryBufferBefore = 0.1f; // 피격 0.1초 전
    [SerializeField] private float parryBufferAfter = 0.05f;  // 피격 후 0.05초까지

    private float _shieldInputTime = -99f;

    public void OnShieldInput()
    {
        _shieldInputTime = Time.time;
    }

    // 적 공격 피격 판정 시 호출
    public bool TryParry(float hitTime)
    {
        float timeDiff = hitTime - _shieldInputTime;
        // 입력이 피격보다 최대 bufferBefore 전, 또는 bufferAfter 후까지
        return timeDiff >= -parryBufferAfter && timeDiff <= parryBufferBefore;
    }
}
```

---

## OnionCat 적용 포인트

### Player 1 (고양이) — 대시 & 슬래시 버퍼
```
상황: 대시 중 슬래시 버튼 누름
버퍼 없을 때: 대시 중에는 입력 무시 → 타이밍 놓침
버퍼 있을 때: 대시 종료 직후 자동으로 슬래시 실행
```
- `bufferWindow = 0.15f` (150ms) 권장
- 대시 상태(PlayerState.Dashing)에서 Slash 입력은 버퍼에만 저장
- 대시 완료 시 버퍼 확인 → 슬래시 즉시 실행

### Player 2 (작물) — 패리 버퍼
```
상황: 적 공격이 날아올 때 정확한 타이밍에 쉴드 입력
버퍼 없을 때: 프레임 퍼펙트 타이밍 필요 → 초보자 극히 어려움
버퍼 있을 때: 피격 0.1초 전 ~ 0.05초 후 입력 모두 패리 성공
```
- 패리 윈도우를 UI로 표시하면 학습 용이 (튜토리얼 단계)
- 버퍼 창 크기로 난이도 조절 가능 (버퍼 클수록 쉬움)

### 콤보 예시 (Optional 확장)
| 입력 시퀀스 | 결과 |
|------------|------|
| Slash → Slash | 2타 슬래시 (연타) |
| Slash → Dash | 이동 슬래시 (전진하며 공격) |
| Shield → Shield | 즉시 패리 자세 |

### 아키텍처 권장 구조
```
PlayerController
  ├── InputBuffer       (버퍼링 로직)
  ├── ComboSystem       (시퀀스 판단)
  └── StateController   (상태별 버퍼 소비)
```

---

## 참고 링크

- [Unity New Input System 공식 문서](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/index.html)
- [GDC: 격투 게임의 입력 버퍼 설계](https://www.gdcvault.com/play/1023474/)
- [Game Feel — Steve Swink (입력 관용도 이론)](https://www.gamefeelbook.com/)
- [YouTube: How Input Buffering Works (Codeer)](https://www.youtube.com/results?search_query=unity+input+buffering+system)
- [Unity 포럼: Input Buffer Implementation](https://forum.unity.com/threads/input-buffer-implementation.html)
