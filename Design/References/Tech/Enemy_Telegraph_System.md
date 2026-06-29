# Enemy Telegraph System (적 공격 예고 시스템)

리서치 날짜: 2026-06-29

## 개요

**어택 텔레그래프(Attack Telegraph)**란 적이 공격을 실행하기 직전, 플레이어에게 "공격이 온다"는 신호를 시각·청각적으로 미리 알려주는 디자인 패턴이다.

OnionCat처럼 2인 협력 게임에서는 특히 중요하다:
- 고양이(근접)와 양파(원거리) 두 플레이어가 동시에 각기 다른 적을 처리하면서, 상대방의 적도 부분적으로 인지해야 한다
- 명확한 텔레그래프 없이는 화면이 혼란스러워 "내가 왜 맞았지?"라는 불만 발생
- 텔레그래프는 "읽을 수 있는 게임"을 만드는 핵심 — 피하는 쾌감이 생김

---

## Unity 구현 방법

### 1. 상태 기반 텔레그래프 구조

적 상태머신에 `Windup` 상태를 추가하여 공격 전 예비 동작을 구현한다.

```csharp
public enum EnemyState { Idle, Chase, Windup, Attack, Cooldown, Dead }

public class EnemyBase : MonoBehaviour
{
    [SerializeField] private float windupDuration = 0.6f;
    [SerializeField] private float attackDuration = 0.2f;

    private EnemyState _state;
    private Coroutine _attackCoroutine;

    void StartAttack()
    {
        if (_attackCoroutine != null) StopCoroutine(_attackCoroutine);
        _attackCoroutine = StartCoroutine(AttackSequence());
    }

    IEnumerator AttackSequence()
    {
        _state = EnemyState.Windup;
        ShowWindupVFX(true);          // 예고 이펙트 ON
        PlayWindupSound();             // 예고 사운드
        yield return new WaitForSeconds(windupDuration);

        _state = EnemyState.Attack;
        ShowWindupVFX(false);         // 예고 이펙트 OFF
        ExecuteAttack();               // 실제 피해 처리

        yield return new WaitForSeconds(attackDuration);
        _state = EnemyState.Cooldown;
    }
}
```

### 2. 시각적 텔레그래프 종류

#### A. 경고 오버레이 (Warning Overlay)
공격 범위를 붉은 영역으로 미리 표시.

```csharp
[SerializeField] private GameObject warningZonePrefab;  // 붉은 원/扇形 스프라이트

void ShowWarningZone(Vector2 center, float radius, float duration)
{
    var zone = Instantiate(warningZonePrefab, center, Quaternion.identity);
    zone.transform.localScale = Vector2.one * radius * 2f;
    Destroy(zone, duration);  // windup 시간 후 자동 제거
}
```

#### B. 방향 지시 화살표
돌진 적에게 방향 화살표 표시.

```csharp
void ShowDashArrow(Vector2 direction, float duration)
{
    float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
    arrowIndicator.transform.rotation = Quaternion.Euler(0, 0, angle);
    arrowIndicator.SetActive(true);
    StartCoroutine(HideAfter(arrowIndicator, duration));
}
```

#### C. 적 자체 애니메이션 텔레그래프
Animator에서 `Windup` 애니메이션 트리거. 적의 몸이 수축하거나 빛나는 모션.

```csharp
// Animator 파라미터: "Windup" (Trigger)
void TriggerWindupAnim()
{
    _animator.SetTrigger("Windup");
}
```

#### D. 색상 깜빡임 (Flash)
DOTween을 활용한 경고 색상 펄스.

```csharp
// DOTween 필요
void FlashWarningColor()
{
    _spriteRenderer.DOColor(Color.red, 0.1f)
        .SetLoops(4, LoopType.Yoyo)
        .OnComplete(() => _spriteRenderer.color = Color.white);
}
```

### 3. 근접 공격 텔레그래프 (부채꼴)

```csharp
[SerializeField] private MeshRenderer slashWarningMesh;  // 부채꼴 메시

void ShowMeleeWarning(float angle, float range)
{
    slashWarningMesh.enabled = true;
    // 부채꼴 메시를 공격 각도/범위에 맞게 조정
    slashWarningMesh.transform.rotation = Quaternion.Euler(0, 0,
        Mathf.Atan2(aimDir.y, aimDir.x) * Mathf.Rad2Deg - angle / 2f);
    slashWarningMesh.transform.localScale = new Vector3(range, range, 1f);
}
```

### 4. 투사체 예고선 (Projectile Line)

투사체 발사 전 궤적을 선으로 미리 표시.

```csharp
[SerializeField] private LineRenderer trajectoryLine;

void ShowProjectileLine(Vector2 origin, Vector2 direction, float distance)
{
    trajectoryLine.enabled = true;
    trajectoryLine.SetPosition(0, origin);
    trajectoryLine.SetPosition(1, origin + direction.normalized * distance);
    // 투사체 발사 후 비활성화
}
```

### 5. 사운드 텔레그래프

```csharp
[SerializeField] private AudioClip windupSfx;
[SerializeField] private AudioSource audioSource;

void PlayWindupSound()
{
    audioSource.PlayOneShot(windupSfx);
}
```

### 6. 텔레그래프 시간 설계 가이드

| 공격 타입 | 권장 예고 시간 | 이유 |
|---------|------------|------|
| 일반 근접 | 0.4~0.6초 | 반응 가능 + 빠른 리듬 |
| 돌진 | 0.5~0.8초 | 방향 읽고 회피 시간 필요 |
| 광역 | 0.8~1.2초 | 넓은 범위라 이동 시간 필요 |
| 보스 필살기 | 1.5~3.0초 | 연출 + 확실한 경고 |
| 투사체 | 0.2~0.4초 | 너무 길면 답답함 |

---

## OnionCat 적용 포인트

### 두 플레이어 역할에 따른 텔레그래프 차별화

- **근접 공격 예고**: 부채꼴 오버레이 → 고양이가 회피하거나 역공(파리)
- **원거리 공격 예고**: 궤적선 오버레이 → 양파가 방패로 막거나 파리

### 약점 연동 텔레그래프
OnionCat의 핵심 협력 메카닉인 "근접에만 약한 적 / 원거리에만 약한 적"을 텔레그래프로도 표현:
- 근접 약점 적: 공격 예고 색이 **고양이 색(파란/흰색)**으로 표시 → "고양이로 대응하라"는 암시
- 원거리 약점 적: 공격 예고 색이 **양파 색(초록색)**으로 표시 → "양파로 처리하라"는 암시
- 이렇게 하면 텍스트 없이도 직관적으로 역할 분담 가능

### 코루틴 기반 구현 권장

```csharp
// EnemyAttackHandler.cs 구조 예시
public class EnemyAttackHandler : MonoBehaviour
{
    [SerializeField] private float windupTime = 0.5f;
    [SerializeField] private GameObject warningPrefab;
    [SerializeField] private Color meleeWarningColor = Color.red;
    [SerializeField] private Color rangedWarningColor = Color.yellow;

    public IEnumerator ExecuteTelegraphAttack(AttackType type)
    {
        // 1. 예고 표시
        var warning = SpawnWarning(type);
        yield return new WaitForSeconds(windupTime);

        // 2. 예고 제거 + 실제 공격
        Destroy(warning);
        PerformAttack(type);
    }
}
```

### 실수 방지: "예고 없는 즉발 공격" 금지
- 특히 2인 게임에서 한 플레이어가 적에 집중하는 동안 다른 플레이어는 다른 곳을 보고 있음
- 텔레그래프 없는 즉발 공격은 "억울함"을 만들고 협력의 즐거움을 망침
- 예외: 보스 2페이즈 또는 특수 상황의 즉발기는 "예고 없음"을 미리 알려주는 연출로 처리

---

## 참고 링크

- [Unity 공식 Coroutines 문서](https://docs.unity3d.com/Manual/Coroutines.html)
- [Game Design Patterns: Attack Telegraphs (GDC Vault 검색)](https://www.gdcvault.com/)
- [Hades 공격 예고 디자인 분석 - YouTube 검색: "Hades attack telegraph design"](https://www.youtube.com/)
- [Enter the Gungeon 텔레그래프 패턴 분석](https://enterthegungeon.fandom.com/)
- [DOTween 공식 문서](http://dotween.demigiant.com/documentation.php)
- [Unity LineRenderer 공식 문서](https://docs.unity3d.com/ScriptReference/LineRenderer.html)
