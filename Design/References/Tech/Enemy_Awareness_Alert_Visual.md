# 적 경계 & 인지 시각화 시스템 (Enemy Awareness & Alert Visual System)

리서치 날짜: 2026-08-11

## 개요

**적 경계 시각화**란 적이 플레이어를 인지하는 과정(무관심 → 의심 → 발견 → 추격)을 플레이어에게 명확하게 보여주는 시스템이다.

Metal Gear Solid 시리즈의 `!` / `?` 인디케이터가 원형이며, 현대 탑뷰 로그라이크에서도 필수적으로 쓰인다.

**OnionCat에서 왜 필요한가**:
- 적이 두 플레이어 중 누구를 쫓는지 시각적으로 명확히 표시해야 협력 전술이 생김
- "Crop이 어그로를 끌어서 Cat이 뒤를 칠 수 있는" 상황을 UI 없이 전달
- 시야각 탐지 시스템(Raycast_LineOfSight_System.md)과 연동하면 완성도 높아짐
- 초보 플레이어도 "지금 적이 나를 봤는지"를 즉시 알 수 있어야 함

---

## Unity 구현 방법

### 1. 적 인지 상태 정의

```csharp
public enum EnemyAwarenessState {
    Idle,       // 순찰/대기 — 아무 인디케이터 없음
    Suspicious, // 의심 — "?" 표시 + 노란 게이지
    Alerted,    // 발견 — "!" 표시 + 빨간 플래시
    Chasing,    // 추격 — 아무 인디케이터 없음(이미 발견)
    LostTarget  // 놓침 — "?" 표시 + 감소 게이지
}
```

### 2. 인지 게이지 (Awareness Meter)

플레이어가 시야 안에 있는 동안 게이지가 쌓이다가, 꽉 차면 `Alerted` 상태 전환.

```csharp
public class EnemyAwareness : MonoBehaviour {
    [SerializeField] private float alertThreshold = 1f;
    [SerializeField] private float fillSpeed = 1f;      // 시야 안에서 초당 증가량
    [SerializeField] private float decaySpeed = 0.5f;   // 시야 밖에서 초당 감소량

    private float _awarenessLevel = 0f;
    private EnemyAwarenessState _state = EnemyAwarenessState.Idle;

    public void UpdateAwareness(bool canSeePlayer) {
        if (canSeePlayer) {
            _awarenessLevel += fillSpeed * Time.deltaTime;
        } else {
            _awarenessLevel -= decaySpeed * Time.deltaTime;
        }
        _awarenessLevel = Mathf.Clamp01(_awarenessLevel / alertThreshold);

        UpdateState();
    }

    private void UpdateState() {
        if (_state == EnemyAwarenessState.Chasing) return; // 추격 중엔 상태 고정

        if (_awarenessLevel >= 1f && _state != EnemyAwarenessState.Alerted) {
            TransitionTo(EnemyAwarenessState.Alerted);
        } else if (_awarenessLevel > 0.1f && _awarenessLevel < 1f) {
            TransitionTo(EnemyAwarenessState.Suspicious);
        } else if (_awarenessLevel <= 0f) {
            if (_state == EnemyAwarenessState.LostTarget)
                TransitionTo(EnemyAwarenessState.Idle);
        }
    }
}
```

### 3. 인디케이터 UI — WorldSpace Canvas

```csharp
public class AwarenessIndicator : MonoBehaviour {
    [SerializeField] private GameObject questionMarkGO;   // "?" 오브젝트
    [SerializeField] private GameObject exclamationMarkGO; // "!" 오브젝트
    [SerializeField] private Image awarenessFillBar;       // 게이지 이미지
    [SerializeField] private Color suspiciousColor = Color.yellow;
    [SerializeField] private Color alertedColor = Color.red;

    // EnemyAwareness에서 상태 변화 시 호출
    public void OnStateChanged(EnemyAwarenessState state, float level) {
        questionMarkGO.SetActive(false);
        exclamationMarkGO.SetActive(false);
        awarenessFillBar.gameObject.SetActive(false);

        switch (state) {
            case EnemyAwarenessState.Suspicious:
            case EnemyAwarenessState.LostTarget:
                questionMarkGO.SetActive(true);
                awarenessFillBar.gameObject.SetActive(true);
                awarenessFillBar.color = suspiciousColor;
                awarenessFillBar.fillAmount = level;
                break;

            case EnemyAwarenessState.Alerted:
                exclamationMarkGO.SetActive(true);
                StartCoroutine(AlertFlash());
                break;
        }
    }

    private IEnumerator AlertFlash() {
        // "!" 표시 + 빨간 플래시 0.5초
        exclamationMarkGO.transform.localScale = Vector3.one * 1.5f;
        yield return new WaitForSeconds(0.08f);
        exclamationMarkGO.transform.localScale = Vector3.one;
    }
}
```

### 4. 캐릭터 머리 위 고정 (Billboard 방식)

WorldSpace Canvas를 쓰되, 카메라 방향과 무관하게 항상 정면을 보도록 설정:
```csharp
void LateUpdate() {
    // 항상 메인 카메라를 향하게
    transform.rotation = Camera.main.transform.rotation;
    // 픽셀아트: 소수점 위치 반올림
    transform.position = new Vector3(
        Mathf.Round(enemy.position.x * PPU) / PPU,
        Mathf.Round((enemy.position.y + heightOffset) * PPU) / PPU,
        transform.position.z
    );
}
```

### 5. 어그로 대상 표시 (누구를 쫓는가)

OnionCat 특화 기능 — 두 플레이어 중 누구를 타겟으로 하는지 시각화:

```csharp
public class EnemyTargetIndicator : MonoBehaviour {
    [SerializeField] private SpriteRenderer targetArrow; // 화살표 스프라이트
    [SerializeField] private Color catColor = Color.red;
    [SerializeField] private Color cropColor = Color.green;

    public void SetTarget(PlayerType targetType) {
        targetArrow.enabled = true;
        targetArrow.color = (targetType == PlayerType.Cat) ? catColor : cropColor;
        // 화살표를 타겟 방향으로 회전
        Vector2 dir = (targetTransform.position - transform.position).normalized;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
        targetArrow.transform.rotation = Quaternion.Euler(0, 0, angle - 90f);
    }
}
```

### 6. 사운드 연동

```csharp
private void TransitionTo(EnemyAwarenessState newState) {
    _state = newState;
    if (newState == EnemyAwarenessState.Alerted) {
        AudioManager.Instance.Play("enemy_alert"); // "!" 발각 사운드
    } else if (newState == EnemyAwarenessState.LostTarget) {
        AudioManager.Instance.Play("enemy_lost");  // "?" 놓침 사운드
    }
    OnStateChanged?.Invoke(newState, _awarenessLevel);
}
```

---

## OnionCat 적용 포인트

### 구현 우선순위

| 단계 | 내용 | 난이도 |
|------|------|--------|
| MVP | 발견 시 "!" 월드스페이스 텍스트만 표시 | ★☆☆ |
| 2단계 | Suspicious "?" + 인지 게이지 바 추가 | ★★☆ |
| 3단계 | 타겟 화살표 (Cat/Crop 색상 구분) | ★★☆ |
| 4단계 | LostTarget 탐색 상태 + 복귀 로직 | ★★★ |

### OnionCat 전용 규칙

1. **타겟 우선순위**: Cat(근접)이 기본 어그로 대상, Crop이 원거리에서 발사하면 50% 확률로 어그로 전환
2. **색깔 코드**: Cat 어그로 = 주황 화살표, Crop 어그로 = 하늘색 화살표
3. **협력 유도**: 일정 시간 이상 Cat이 어그로를 독점하면 "(Crop: 나도 쏠게!)" 힌트 팝업
4. **근접 전용 적**: 발견 시 화살표 없이 빨간 에너지 오라(Rigidbody2D 돌진 예고)
5. **원거리 전용 적**: 파란 조준선 시각화 → Crop 패리 준비 신호

### 시각 디자인 (픽셀아트)

```
Idle:       [아무것도 없음]
Suspicious: [?] + 노란 게이지바 (적 머리 위 8px 위)
Alerted:    [!] 빨간색 + 0.15초 깜빡임 + 1.2배 스케일 → 1.0배 복귀
Chasing:    [타겟 화살표 색상으로 누구를 쫓는지 표시]
LostTarget: [?] 흰색 + 감소하는 게이지바
```

### 성능 주의사항

- WorldSpace Canvas는 방 안 적 최대 10~15마리 수준이면 성능 이상 없음
- `Canvas.renderMode = RenderMode.WorldSpace` + `Canvas.sortingLayerName = "UI"`
- 오브젝트 풀링 적용: "?" / "!" 오브젝트를 OnEnable/OnDisable로 관리

---

## 참고 링크

- **Unity WorldSpace Canvas 공식 문서**: https://docs.unity3d.com/Manual/UICanvas.html
- **Metal Gear Solid 어웨어니스 시스템 분석**: GDC 발표 "Designing Enemy Awareness in Metal Gear" 검색
- **Game Feel 책 (Steve Swink)**: enemy feedback 챕터 — 적 상태 전달의 중요성
- **유사 구현 튜토리얼**: YouTube "Unity 2D enemy detection indicator tutorial" 검색
- **Spelunky 적 AI 분석**: https://tinysubversions.com/spelunky-book/ — 단순한 적도 명확한 상태 피드백이 얼마나 중요한지
