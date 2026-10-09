# Boss Arena Spatial Design (보스 아레나 공간 설계)

리서치 날짜: 2026-10-09

## 개요

보스 아레나는 단순한 큰 방이 아니라 **보스 패턴과 공간이 함께 만드는 퍼즐**이다.
특히 OnionCat처럼 두 플레이어가 각자 역할이 다른 협력 게임에서는 아레나 공간 설계가
"이 싸움은 협력해야 이길 수 있다"는 것을 **명시적 지시 없이 자연스럽게** 느끼게 만든다.

### OnionCat에서 중요한 이유
- 고양이(근거리)와 양파(원거리)의 역할이 다르므로, 아레나 구조로 두 역할이 **동시에 필요한 순간**을 강제할 수 있음
- 방 크기가 크고 잘못 배치하면 "한 명이 다 한다"는 패턴이 쉽게 발생

---

## 보스 아레나 공간 설계 5원칙

### 1. 분할 목표 (Split Objectives)
**정의**: 보스에게 피해를 주거나 취약점을 여는 조건을 아레나 양쪽에 분산 배치

- 예: 보스 양쪽에 수정 오브젝트가 있고, 두 개를 동시에 파괴해야 무적이 풀림
- 한 명이 하나를 파괴하는 동안 다른 한 명이 보스를 유인해야 함
- **OnionCat 적용**: 보스 쉴드를 여는 스위치를 두 곳에 배치 → 고양이가 전방 교란, 양파가 원거리로 스위치 활성화

### 2. 안전지대 로테이션 (Safe Zone Rotation)
**정의**: 보스의 공격이 아레나 내 안전 구역을 시간에 따라 이동시킴

- 고정 벽 뒤에 숨으면 한 명이 방치되므로 안전지대를 계속 이동시켜야 함
- 두 플레이어가 같은 곳에 모이면 하나의 안전지대가 두 명을 다 커버 못하게 설계
- **OnionCat 적용**: 보스가 지면에 데미지 판정 구역을 생성 → 두 명이 같은 셀에 있으면 둘 다 맞는 범위로 설정

### 3. 역할 강제 레이아웃 (Role-forcing Layout)
**정의**: 지형 자체가 근거리/원거리 역할을 분리하도록 설계

- 전방: 낮은 장애물(엄폐가능, 근거리가 숨을 수 있음)
- 후방: 고지대나 플랫폼(원거리 시야 확보)
- **OnionCat 적용**: 보스 아레나에 전방 낮은 바위(Wall 레이어), 후방 플랫폼 배치
  → 고양이는 바위를 이용해 대쉬 타이밍 잡기 용이, 양파는 플랫폼에서 투사체 조준

### 4. 환경 리소스 배치 (Environmental Resources)
**정의**: 체력 회복, 방어막 아이템을 아레나 가장자리에 배치해 이동을 강제

- 중앙에만 있으면 둘 다 중앙에 몰림 → 보스 공격에 취약
- 가장자리에 배치하면 한 명이 리소스를 수집하는 동안 다른 한 명이 보스를 막아야 함
- **OnionCat 적용**: 보스 방 가장자리에 씨앗 포켓(양파 탄환) 배치 → 양파가 리필하러 이동 시 고양이가 시선 끌기

### 5. 단계적 아레나 변형 (Phase-based Arena Change)
**정의**: 보스 체력 구간마다 아레나 구조가 바뀜

- Phase 1: 기본 아레나 (탐색 단계)
- Phase 2: 기둥/장애물 소환 → 시야 차단 → 근거리 전투 강화
- Phase 3: 장애물 제거 + 바닥 전체 데미지존 → 쉴 곳이 없어짐
- **OnionCat 적용**: 보스 체력 50%에서 방 가장자리에 구덩이(Pit) 생성 → 공간 압박 증가

---

## Unity 구현 방법

### 아레나 단계 전환 스크립트 기본 패턴

```csharp
public class BossArena : MonoBehaviour
{
    [SerializeField] private BossBase boss;
    [SerializeField] private GameObject[] phase2Objects;  // Phase 2에 활성화
    [SerializeField] private GameObject[] pitObjects;     // Phase 3 구덩이
    [SerializeField] private float phase2Threshold = 0.5f;

    private bool phase2Triggered;

    private void OnEnable()
    {
        boss.OnHealthChanged += CheckPhase;
    }

    private void OnDisable()
    {
        boss.OnHealthChanged -= CheckPhase;
    }

    private void CheckPhase(float healthRatio)
    {
        if (!phase2Triggered && healthRatio <= phase2Threshold)
        {
            phase2Triggered = true;
            ActivatePhase2();
        }
    }

    private void ActivatePhase2()
    {
        foreach (var obj in phase2Objects)
            obj.SetActive(true);
        foreach (var obj in pitObjects)
            obj.SetActive(true);
        // 연출: 카메라 흔들기
        CinemachineImpulse();
    }
}
```

### 분할 목표 구현 (두 스위치 동시 활성화)

```csharp
public class DualSwitchGate : MonoBehaviour
{
    [SerializeField] private Switch switchA;
    [SerializeField] private Switch switchB;
    [SerializeField] private BossBase boss;

    private void Update()
    {
        if (switchA.IsActivated && switchB.IsActivated)
            boss.SetVulnerable(true);
        else
            boss.SetVulnerable(false);
    }
}
```

### 안전지대 로테이션 (코루틴 방식)

```csharp
private IEnumerator RotateSafeZone()
{
    int current = 0;
    while (true)
    {
        safeZones[current].SetActive(false);
        current = (current + 1) % safeZones.Length;
        safeZones[current].SetActive(true);
        yield return new WaitForSeconds(safeZoneInterval);
    }
}
```

---

## OnionCat 적용 포인트

### 협력 강제 패턴 체크리스트

- [ ] 보스 취약 조건이 두 캐릭터의 **동시 액션**을 요구하는가?
- [ ] 한 명이 "안전"할 때 다른 한 명은 반드시 위험에 노출되는가?
- [ ] 양파(원거리)가 고양이(근거리) 없이 클리어하기 어려운가? (반대도 마찬가지)
- [ ] 아레나 크기가 너무 크지 않아 두 명이 서로 상황을 볼 수 있는가?
  - 권장 크기: 640×360 (전체 화면) 기준 최대 24×14 타일 이내
  - 카메라가 두 명을 모두 포함하는 줌이 필요하면 `Shared_Body_Camera_Framing_System.md` 참고

### 아레나 구성 요소별 레이어 규칙

| 요소 | 레이어 | 태그 | 정렬 순서 |
|------|--------|------|----------|
| 바닥 타일 | Default | - | -1000 ~ -900 |
| 낮은 장애물 (엄폐용) | Wall | Wall | -100 ~ -1 |
| 구덩이(Pit) | Props | - | -1000 ~ -900 |
| 스위치/오브젝트 | Props | - | -100 ~ 99 |
| 보스 공격 경고존 | Props | - | 100+ |

### Room Layout에 보스 아레나 적용
- `Assets/Data/RoomLayouts/Boss_*.asset`에 글자 지도로 정의
- `B` = 보스 스폰, `D` = 출구 포함 안 함 (보스 격파 후 출구 활성화)
- 장애물은 `X` (벽 덩어리), 구덩이는 별도 스크립트로 Phase 시작 시 활성화

---

## 참고 링크

- [GDD410 Synergy Co-op Design Doc (Quinnipiac)](https://mywebspace.quinnipiac.edu/jbwarren/archive/2018-410/resources/GDD410-Synergy-Design-Doc.pdf)
- It Takes Two — Boss Wasp Queen 분석 (협력 보스 설계 레퍼런스)
- [Boss_Pattern_Design.md](Boss_Pattern_Design.md) — 보스 공격 패턴 설계
- [Boss_Phase_Transition_Implementation.md](Boss_Phase_Transition_Implementation.md) — 페이즈 전환 구현
- [Room_System.md](Room_System.md) — 방 레이아웃 시스템
