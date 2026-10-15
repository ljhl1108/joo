# 협동 비대칭 퍼즐 방 설계

리서치 날짜: 2026-10-15

## 개요
두 플레이어가 **서로 다른 능력**을 가지고 있을 때, 그 차이를 활용해야만 풀 수 있는 퍼즐·기믹을 설계하는 방법. OnionCat처럼 한 플레이어는 물리 이동(고양이), 다른 플레이어는 원거리 조작(양파)인 구조에서 퍼즐을 만드는 것은 일반 1인 퍼즐 설계와 본질적으로 다르다.

"둘이 함께 있어야만 풀 수 있다"는 경험이 협동 게임의 핵심 감정이다.

---

## 비대칭 퍼즐의 핵심 원리

### 1. "나만 할 수 있는 것" 역할 분리
각 플레이어만 수행 가능한 동작이 있어야 퍼즐이 성립한다.

| | 고양이만 | 양파만 | 둘 다 |
|---|---|---|---|
| 능력 | 이동, 발판 밟기, 물체 밀기, 걷어차기 | 원거리 조준 발사, 스킬 Q·W·E, 마우스 클릭 | 가방 사용, 장비 확인 |
| 퍼즐 활용 | 발판 지속 누르기, 적 특정 위치로 날리기 | 멀리 있는 타겟·버튼 쏘기, 식물 심기 | 동시 입력, 협동 기믹 |

### 2. 타이밍 동기화 퍼즐
둘이 동시에 행동해야 작동하는 스위치·문:
- 고양이가 북쪽 발판을 밟고 있는 동안 → 양파가 동쪽 타겟을 쏘기
- 타이밍 창이 짧을수록 어려움, 길수록 쉬움 → 난이도 조절 레버

### 3. 체인 퍼즐 (A → B → C)
한 플레이어의 행동이 다른 플레이어의 기회를 만드는 연쇄:
```
고양이: 적을 걷어차기 → 수정 근처로 날림
양파: 그 수정에 씨앗 탄 맞히기 → 수정 활성화
결과: 방 출구 열림
```
연쇄가 길수록 재미있지만, 첫 행동의 실패 비용이 커짐 → 2~3단계가 적당

### 4. 공간 분리 퍼즐
두 플레이어가 서로 다른 장소에서 동시에 행동:
- 고양이: 남쪽 통로에서 발판 유지
- 양파: 북쪽에서 원거리 타겟 쏘기
- 서로 못 보는 상황이 소통 필요성 강화 → 스플릿 스크린 없어도 HUD 힌트로 보완 가능

---

## Unity 구현 방법

### 기본 구조: 모듈형 PuzzleSwitch

```csharp
// 하나의 퍼즐 요소 — 다른 퍼즐 요소와 연결 가능
public class PuzzleSwitch : MonoBehaviour {
    [SerializeField] PuzzleSwitch[] requiredSwitches; // 모두 켜져야 발동
    public UnityEvent onAllActivated;
    bool _isActive;

    public void Activate() {
        _isActive = true;
        CheckAll();
    }

    public void Deactivate() { _isActive = false; }

    void CheckAll() {
        if (!_isActive) return;
        foreach (var sw in requiredSwitches)
            if (!sw._isActive) return;
        onAllActivated.Invoke();
    }
}
```

### 발판 (고양이 전용)

```csharp
// 고양이가 밟고 있는 동안 활성화
[RequireComponent(typeof(PuzzleSwitch))]
public class HoldPlatform : MonoBehaviour {
    [SerializeField] float holdTime = 0f; // 0 = 즉시, 양수 = 지속 필요

    PuzzleSwitch _switch;
    float _timer;

    void Awake() => _switch = GetComponent<PuzzleSwitch>();

    void OnTriggerStay2D(Collider2D col) {
        if (!col.CompareTag("Player")) return;
        _timer += Time.deltaTime;
        if (_timer >= holdTime) _switch.Activate();
    }

    void OnTriggerExit2D(Collider2D col) {
        if (!col.CompareTag("Player")) return;
        _timer = 0;
        _switch.Deactivate();
    }
}
```

### 원거리 타겟 (양파 전용)

```csharp
// 양파 씨앗 탄이 맞으면 활성화
[RequireComponent(typeof(PuzzleSwitch))]
public class ShootTarget : MonoBehaviour {
    [SerializeField] bool stayActivated = true; // true = 한번 맞으면 유지

    PuzzleSwitch _switch;

    void Awake() => _switch = GetComponent<PuzzleSwitch>();

    void OnTriggerEnter2D(Collider2D col) {
        if (col.gameObject.layer != LayerMask.NameToLayer("PlayerProjectile")) return;
        _switch.Activate();
        if (stayActivated) {
            GetComponent<Collider2D>().enabled = false; // 중복 발동 방지
            // 피격 이펙트: 색 변경, 파티클 등
        }
    }
}
```

### 적을 특정 위치로 날리는 퍼즐 (걷어차기 연동)

```csharp
// 특정 zone에 적이 날아와 착지하면 활성화
public class KickZone : MonoBehaviour {
    [SerializeField] PuzzleSwitch target;

    void OnTriggerEnter2D(Collider2D col) {
        if (!col.CompareTag("Enemy")) return;
        // 날아가는 중인지 확인 (EnemyBase.IsLaunched)
        var enemy = col.GetComponent<EnemyBase>();
        if (enemy != null && enemy.IsLaunched)
            target.Activate();
    }
}
```

### 시각적 힌트 시스템
- **발판**: 발광 테두리 — 빈 상태(어두운 색) → 밟는 중(빛이 차오름) → 완료(밝은 색)
- **타겟**: 회전하는 마름모 아이콘 + 발광 — 양파 플레이어에게 "쏴야 해" 신호
- **연결선**: `LineRenderer`로 연결된 스위치끼리 희미한 선 — 체인 관계 시각화
- **힌트 팝업**: 방 입장 시 HUD에 3초간 조작 힌트 (한국어: "고양이: 발판 밟기 / 양파: 타겟 쏘기")

---

## OnionCat 적용 포인트

### 현재 구현된 쌍둥이 스위치 → 모듈화 확장

현재: 고양이 발판 + 양파 수정 쏘기 (1종 하드코딩)
목표: `HoldPlatform` + `ShootTarget` + `KickZone` 컴포넌트로 모듈화
→ 방 레이아웃 에디터에서 컴포넌트 조합만으로 다양한 퍼즐 생성 가능

### 퍼즐 방 변형 아이디어 (구현 난이도 순)

1. **[쉬움] 타겟 쏘기**: 방 한쪽에 `ShootTarget` 배치 → 출구 연결. 전투 없이 순수 조준 확인
2. **[쉬움] 발판 + 타겟 동시**: `HoldPlatform`과 `ShootTarget`을 `PuzzleSwitch.requiredSwitches`로 연결
3. **[중간] 발판 → 타겟 순서**: 발판을 먼저 밟아야 타겟이 나타남 — 체인 2단계
4. **[중간] 킥 퍼즐**: `KickZone`에 적을 날려넣어야 문 열림. 걷어차기 방향 조준 연습도 됨
5. **[어려움] 타이밍 동기화**: 발판은 2초간만 활성화 → 그 안에 타겟을 쏴야 함

### 설계 주의사항
- 퍼즐 방은 **전투 중에 풀어야** 더 재미있음 — 적과 싸우면서 퍼즐 요소를 의식하는 긴장감
- 너무 어려우면 협동 마찰(서로 탓하기)이 생김 → 첫 시도에 50~60% 성공률이 적당
- 퍼즐 기믹은 보상(씨앗 추가, 에픽 아이템) 방에만 배치 — 필수 경로를 막지 말 것

## 참고 링크
- [It Takes Two - Co-op Design GDC](https://www.gdcvault.com/play/1027844/)
- [Unity Events 공식 문서](https://docs.unity3d.com/Manual/UnityEvents.html)
- [Keep Talking and Nobody Explodes - 정보 비대칭 설계](https://keeptalkinggame.com/)
- [Game Maker's Toolkit - Cooperative Game Design](https://www.youtube.com/watch?v=KE3RYWGbLxY)
