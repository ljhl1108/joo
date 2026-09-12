# 방 클리어 셀레브레이션 VFX (Room Clear Celebration VFX)

리서치 날짜: 2026-09-12

## 개요
탑다운 로그라이크에서 방 내 모든 적을 처치했을 때 발생하는 **마이크로 연출 시퀀스**. 
짧지만 명확한 피드백 — "이 방을 클리어했다" — 를 전달하며 플레이어에게 보상감을 준다.

이 시스템이 중요한 이유:
- 연출이 없으면 플레이어가 "마지막 적이 죽었나?" 확신하지 못함
- 문이 열리는 것만으로는 시각 피드백이 약함
- 0.5~1.0초짜리 짧은 연출이 게임 전체 리듬을 결정함

---

## Unity 구현 방법

### 1. 전체 이벤트 체인 코루틴
```csharp
public class RoomClearCelebration : MonoBehaviour
{
    [SerializeField] private ParticleSystem clearBurstParticle;
    [SerializeField] private AudioClip clearSFX;
    [SerializeField] private AudioClip doorOpenSFX;
    [SerializeField] private float hitStopDuration = 0.06f;

    public IEnumerator PlayCelebration(Vector3 roomCenter, DoorController[] doors)
    {
        // 1. 히트스톱 (Time.timeScale 잠깐 멈춤 → 무게감)
        Time.timeScale = 0.05f;
        yield return new WaitForSecondsRealtime(hitStopDuration);
        Time.timeScale = 1f;

        // 2. 방 클리어 파티클 (방 중앙 기준)
        Instantiate(clearBurstParticle, roomCenter, Quaternion.identity);

        // 3. 클리어 SFX
        AudioManager.PlayOneShot(clearSFX);

        // 4. 카메라 약한 흔들림
        CameraShake.Instance.Shake(trauma: 0.2f, duration: 0.3f);

        // 5. 잠깐 기다림 (연출 흡수 시간)
        yield return new WaitForSeconds(0.3f);

        // 6. 문 열기 (순차 또는 동시)
        foreach (var door in doors)
        {
            door.Unlock();
            AudioManager.PlayOneShot(doorOpenSFX);
            yield return new WaitForSeconds(0.05f); // 문마다 약간 시차
        }

        // 7. 루트 스폰 (문 열린 후)
        yield return new WaitForSeconds(0.15f);
        LootSpawner.SpawnAt(roomCenter);
    }
}
```

### 2. 파티클 설계 (픽셀아트 스타일)
```
[Particle System Inspector 설정]
- Duration: 0.5
- Start Lifetime: 0.4 ~ 0.8 (랜덤)
- Start Speed: 3 ~ 8
- Start Size: 0.05 ~ 0.1 (픽셀 낱알 크기)
- Shape: Sphere (360° 방사)
- Color: 밝은 노랑 → 흰색 (Gradient)
- Gravity Modifier: 0.5 (약하게 위로 뜨다 떨어짐)
- Max Particles: 60
- Renderer > Order in Layer: UI 바로 아래 (Sorting Layer "VFX")
```

### 3. 화면 테두리 플래시 (선택 옵션)
방 클리어 시 화면 가장자리가 잠깐 빛나는 효과 — 넓은 방에서도 클리어를 인식시킴:
```csharp
// UI Image (fullscreen, black alpha=0) → 순간 알파 0.4 → 다시 0
public IEnumerator EdgeFlash()
{
    edgeImage.color = new Color(1f, 1f, 0.5f, 0.4f); // 노란빛
    yield return new WaitForSeconds(0.08f);
    // DOTween 없이 수동 페이드
    float t = 0f;
    while (t < 0.3f)
    {
        edgeImage.color = new Color(1f, 1f, 0.5f, Mathf.Lerp(0.4f, 0f, t / 0.3f));
        t += Time.deltaTime;
        yield return null;
    }
    edgeImage.color = Color.clear;
}
```

### 4. 적 사망 연출 vs 클리어 연출 분리
| 이벤트 | 연출 강도 | 요소 |
|--------|-----------|------|
| 일반 적 사망 | 낮음 | 소형 파티클 + 짧은 SFX |
| **마지막 적 사망 (방 클리어)** | 높음 | 히트스톱 + 버스트 파티클 + 카메라 쉐이크 + 문 열림 |
| 보스 사망 | 최고 | 히트스톱 확장 + 슬로모 + 대형 파티클 + 컷씬 |

마지막 적이 죽을 때 `isLastEnemy` 플래그로 구분:
```csharp
public void OnEnemyDied(bool isLastEnemy)
{
    if (isLastEnemy)
        StartCoroutine(celebration.PlayCelebration(center, doors));
    else
        SpawnSmallDeathParticle();
}
```

---

## OnionCat 적용 포인트

### 1. 협력 클리어 보너스 연출
Cat과 Onion이 **동시에 마지막 적을 처치**(Cat 근접 + Onion 원거리 같은 프레임) 할 때:
```
일반 클리어 연출 + "TEAMWORK!" 텍스트 팝업 (0.5초 표시)
→ 추가 골드/씨앗 보너스 지급
```
협력을 "느끼게" 만드는 핵심 보상 루프.

### 2. 약점 공격으로 클리어 보너스
OnionCat의 핵심 필러: 근접/원거리 약점 적을 **올바른 캐릭터로 처치**했을 때만 보너스:
```csharp
public float GetClearBonus(Enemy enemy, DamageType usedType)
{
    return (enemy.WeakTo == usedType) ? 1.5f : 1.0f; // 1.5배 골드
}
```
클리어 파티클 색상도 다르게: 올바른 약점 공격 → 황금 파티클 / 강행 처치 → 흰색 파티클

### 3. 시퀀스 타이밍 (OnionCat 기준 최적값)
```
히트스톱:       0.05초  (짧게 — 협동 게임의 흐름 유지)
파티클 버스트:  즉시
카메라 쉐이크:  trauma=0.2, 0.3초
대기 시간:      0.25초  (루트 스폰 전)
문 열림:        0.25초 시작 후 순차 열림
총 연출 시간:   약 0.7~0.8초
```

### 4. 2인 동시 파티클 위치
Cat이 이동하는 캐릭터이므로 방 클리어 파티클은 **Cat의 현재 위치** 기준:
```csharp
Instantiate(clearBurst, catTransform.position, Quaternion.identity);
```
Onion은 Cat의 등에 있으므로 자동으로 두 캐릭터 위치에 파티클이 발생.

---

## 구현 우선순위 (초보자용 순서)
1. **SFX만 먼저** → `AudioManager.PlayOneShot(clearSFX)` 한 줄
2. **파티클 추가** → `Instantiate(clearBurstParticle, center, Quaternion.identity)`
3. **히트스톱** → `Time.timeScale = 0.05f` + WaitForSecondsRealtime
4. **카메라 쉐이크** → CameraShake.Instance.Shake() 연동
5. **문 열림 딜레이** → Unlock() 호출을 코루틴으로 0.3초 뒤에 실행

각 단계를 추가할 때마다 테스트 → 타격감 차이 체감.

---

## 참고 링크
- Unity ParticleSystem: https://docs.unity3d.com/Manual/ParticleSystemReference.html
- Unity Time.timeScale (히트스톱 원리): https://docs.unity3d.com/ScriptReference/Time-timeScale.html
- Game Feel 영상 참고: YouTube "juice it or lose it" (피드백 시스템 철학)
- Archvale 방 클리어 연출 참고: YouTube "Archvale gameplay" 방 클리어 장면
