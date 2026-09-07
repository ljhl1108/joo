# Cinemachine 화면 흔들림 시스템 (CinemachineImpulse Screen Shake)

리서치 날짜: 2026-09-07

## 개요

화면 흔들림(Screen Shake)은 타격감·폭발감을 시각적으로 전달하는 가장 강력한 피드백 수단이다. Unity의 Cinemachine 패키지가 제공하는 **CinemachineImpulse** 시스템은 간단한 코드 한 줄로 물리 기반 카메라 진동을 구현한다. 기존 coroutine 방식보다 성능이 좋고, 카메라가 여러 개여도 각각 반응하도록 설정 가능하다.

OnionCat에서는 P1 근접 슬래시, P2 원거리 발사, 보스 폭발, 환경 위험 등 이벤트별로 세기를 다르게 설정해야 한다. CinemachineImpulse는 **소스(Source)** 컴포넌트와 **리스너(Listener)** 컴포넌트를 분리하므로 이런 다중 이벤트 시나리오에 적합하다.

---

## Unity 구현 방법

### 0단계: 패키지 설치 확인

Unity 2022+ (URP) 에는 Cinemachine이 기본 포함된다.

```
Window → Package Manager → Cinemachine 확인 (Install/Update)
```

### 1단계: Virtual Camera(CinemachineVirtualCamera) 설정

씬에 메인 카메라를 따르는 Virtual Camera가 있어야 한다.

```
Hierarchy → Create → Cinemachine → 2D Camera
  ├── CinemachineVirtualCamera (이름: vcam_main)
  └── CinemachineImpulseListener (컴포넌트 추가)
```

`CinemachineImpulseListener` 설정:
- **Gain**: 1.0 (충격 반응 세기 배율)
- **Use 2D Distance**: ✓ 체크 (2D 게임에서 필수)
- **Channel Mask**: 원하는 채널 선택

### 2단계: ImpulseSource 컴포넌트 추가

충격을 발생시킬 오브젝트(플레이어, 적, 폭발 등)에 추가:

```csharp
// ScreenShaker.cs — 중앙 관리 싱글톤
using UnityEngine;
using Cinemachine;

public class ScreenShaker : MonoBehaviour
{
    public static ScreenShaker Instance { get; private set; }

    [SerializeField] private CinemachineImpulseSource lightSource;   // P2 투사체
    [SerializeField] private CinemachineImpulseSource mediumSource;  // P1 슬래시
    [SerializeField] private CinemachineImpulseSource heavySource;   // 보스/폭발

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    public void ShakeLight()  => lightSource.GenerateImpulse(0.3f);
    public void ShakeMedium() => mediumSource.GenerateImpulse(0.7f);
    public void ShakeHeavy()  => heavySource.GenerateImpulse(1.5f);

    // 방향성 흔들림 (적 날아가는 방향으로 카메라 밀림)
    public void ShakeDirectional(Vector2 direction, float strength)
    {
        mediumSource.GenerateImpulse(direction.normalized * strength);
    }
}
```

### 3단계: CinemachineImpulseSource 인스펙터 설정

| 항목 | 권장값 | 역할 |
|------|--------|------|
| **Impulse Shape** | Rumble | 진동 형태 |
| **Impulse Duration** | 0.15 ~ 0.4초 | 진동 지속 시간 |
| **Dissipation Rate** | 2.0 | 감쇠 속도 |
| **Propagation Speed** | 343 (음속) | 거리별 도달 시간 |
| **Impact Radius** | 5 | 반경 밖에서 점점 약해짐 |

### 4단계: 이벤트 연결

```csharp
// MeleeCombat.cs — 슬래시 히트 시 호출
void OnHitEnemy()
{
    ScreenShaker.Instance.ShakeMedium();
    // 히트스톱, 파티클 등 병행
}

// Projectile.cs — 투사체 충돌 시
void OnCollisionEnter2D(Collision2D col)
{
    ScreenShaker.Instance.ShakeLight();
}

// BossController.cs — 보스 처치 시
void OnBossDeath()
{
    ScreenShaker.Instance.ShakeHeavy();
}
```

### 5단계: 접근성 — 흔들림 강도 설정값 연동

```csharp
// ScreenShaker.cs에 추가
private float shakeMultiplier = 1f;

public void SetShakeIntensity(float value) // 0=없음, 1=기본, 1.5=강함
{
    shakeMultiplier = value;
    PlayerPrefs.SetFloat("ShakeIntensity", value);
}

public void ShakeMedium()
{
    mediumSource.GenerateImpulse(0.7f * shakeMultiplier);
}
```

설정 메뉴 슬라이더와 연결하면 멀미 방지 옵션이 된다.

---

## OnionCat 적용 포인트

### 이벤트별 흔들림 설계

| 이벤트 | 소스 | 세기 | 지속 |
|--------|------|------|------|
| P2 투사체 일반 적중 | light | 0.2 | 0.1s |
| P1 슬래시 일반 적중 | medium | 0.6 | 0.2s |
| P1 슬래시 피니셔 | medium | 1.0 | 0.3s |
| P2 쉴드 패리 성공 | medium | 0.8 + 방향성 | 0.25s |
| 보스 공격 착지 | heavy | 1.2 | 0.5s |
| 보스 처치 | heavy | 2.0 | 0.8s |
| 대쉬(P1 무적) | light | 0.1 | 0.08s |

### 2D 카메라 경계 (Confiner) 와 함께 사용

방 전환 카메라가 `CinemachineConfiner2D`를 쓸 때, 흔들림이 경계 밖으로 나가지 않도록:

```csharp
// CinemachineImpulseListener 컴포넌트 옵션
// "Use 2D Distance" 체크 + Confiner2D 적용 시 자동으로 경계 내에서 흔들림
```

### Shake → 히트스톱 연계 타이밍

```
히트 감지
  → Time.timeScale = 0 (히트스톱 0.05초)
  → WaitForSecondsRealtime(0.05)
  → Time.timeScale = 1
  → ScreenShaker.ShakeMedium()   // 히트스톱 끝난 직후 흔들림
```
히트스톱과 흔들림을 같이 발동하면 흔들림이 timeScale=0에 멈춰버린다. 흔들림은 히트스톱 해제 후에 발동해야 자연스럽다.

---

## 참고 링크

- Unity 공식 CinemachineImpulse 문서: https://docs.unity3d.com/Packages/com.unity.cinemachine@2.9/manual/CinemachineImpulse.html
- Cinemachine Screen Shake (Unity Learn): https://learn.unity.com/tutorial/cinemachine-impulse
- Code Monkey 튜토리얼 (CinemachineImpulse): https://www.youtube.com/watch?v=ACf1I27I6Tk
- Game Feel 설계 논문 참고: https://jbohlen.itch.io/game-feel-guide
