# 픽셀아트 VFX 파티클 시스템

리서치 날짜: 2026-08-17

## 개요

픽셀아트 게임에서 파티클 이펙트는 일반 파티클과 달리 **픽셀 격자감(pixel grid feel)** 을 유지해야 한다. 부드럽게 보간되는 파티클은 도트아트 스타일을 깨뜨리기 때문에, 색상·크기·이동 방식을 픽셀 단위로 제어하는 것이 핵심이다.

OnionCat의 경우 히트 이펙트, 대시 잔상, 적 사망 효과, 투사체 착탄 등에 파티클이 필요하며, 픽셀아트 스타일을 유지하면서 시각적 피드백을 풍부하게 만드는 것이 목표다.

---

## Unity 구현 방법

### 1. 파티클 임포트 설정

픽셀아트 파티클 스프라이트는 반드시 아래 설정을 지켜야 한다:

```
Import Settings (Texture Importer):
  Filter Mode: Point (no filter)   ← 핵심! Bilinear 금지
  Compression: None 또는 Lossless
  Sprite Mode: Single 또는 Multiple
  Pixels Per Unit: 게임 PPU와 동일하게 (예: 16 또는 32)
```

### 2. Particle System 기본 구성 (Inspector)

```
Particle System Component:
  Duration: 0.3~0.6 (짧은 이펙트)
  Looping: false
  Start Lifetime: 0.2~0.5
  Start Speed: 1~4 (픽셀 단위 속도)
  Start Size: 1~3 (픽셀 수)
  Simulation Space: World (위치 고정 이펙트)

Emission:
  Rate over Time: 0
  Bursts: Count 5~15 at time 0

Shape:
  Shape: Circle
  Radius: 0.1~0.3 (작게 유지)

Renderer:
  Render Mode: Billboard 또는 Horizontal Billboard
  Material: (스프라이트 픽셀아트 머티리얼, 아래 참조)
  Sorting Layer: 게임 오브젝트보다 위
```

### 3. 픽셀아트 머티리얼 설정

URP 2D에서 파티클 스프라이트가 흐려지지 않으려면:

```
Material: Sprites/Default 또는 Universal Render Pipeline/Particles/Unlit
Shader: "Particles/Unlit" 또는 커스텀 URP Shader

커스텀 설정:
  Blending: Alpha Blending (Transparent)
  Texture Filtering: Point (Filter Mode를 Material에서도 강제)
```

**중요**: URP에서 Particle System의 머티리얼이 `Sprites/Default`를 쓰면 Point filtering이 무시될 수 있다. 별도 머티리얼을 만들고 텍스처 필터링을 명시적으로 Point로 설정해야 한다.

### 4. 색상 제한 (픽셀아트 팔레트 고수)

픽셀아트 스타일의 핵심은 제한된 팔레트:

```
Color over Lifetime:
  시작: 밝은 흰색/노란색 (히트 플래시)
  중간: 캐릭터/적 관련 색상
  끝: 투명 (Alpha 0)

권장 방식:
  - Color over Lifetime 그래디언트에서 키포인트를 2~3개로 제한
  - 부드러운 그래디언트 대신 갑작스러운 색상 전환 (픽셀아트다움)
```

### 5. 크기와 이동 — 픽셀 스냅

파티클이 픽셀 격자에 맞게 이동하도록:

```cs
// ParticleSystemScript.cs — 파티클 픽셀 스냅 강제
using UnityEngine;

[RequireComponent(typeof(ParticleSystem))]
public class PixelSnapParticleSystem : MonoBehaviour
{
    [SerializeField] private float pixelsPerUnit = 16f;

    private ParticleSystem _ps;
    private ParticleSystem.Particle[] _particles;

    void Awake()
    {
        _ps = GetComponent<ParticleSystem>();
        _particles = new ParticleSystem.Particle[_ps.main.maxParticles];
    }

    void LateUpdate()
    {
        int count = _ps.GetParticles(_particles);
        for (int i = 0; i < count; i++)
        {
            Vector3 pos = _particles[i].position;
            pos.x = Mathf.Round(pos.x * pixelsPerUnit) / pixelsPerUnit;
            pos.y = Mathf.Round(pos.y * pixelsPerUnit) / pixelsPerUnit;
            _particles[i].position = pos;
        }
        _ps.SetParticles(_particles, count);
    }
}
```

### 6. 오브젝트 풀 연동 (풀에서 파티클 재사용)

```cs
// PixelVFXPool.cs
using UnityEngine;
using UnityEngine.Pool;

public class PixelVFXPool : MonoBehaviour
{
    public static PixelVFXPool Instance { get; private set; }

    [SerializeField] private ParticleSystem hitVFXPrefab;
    [SerializeField] private ParticleSystem deathVFXPrefab;

    private IObjectPool<ParticleSystem> _hitPool;
    private IObjectPool<ParticleSystem> _deathPool;

    void Awake()
    {
        Instance = this;
        _hitPool = new ObjectPool<ParticleSystem>(
            createFunc: () => Instantiate(hitVFXPrefab),
            actionOnGet: ps => ps.gameObject.SetActive(true),
            actionOnRelease: ps => ps.gameObject.SetActive(false),
            actionOnDestroy: ps => Destroy(ps.gameObject),
            defaultCapacity: 20
        );
        _deathPool = new ObjectPool<ParticleSystem>(
            createFunc: () => Instantiate(deathVFXPrefab),
            actionOnGet: ps => ps.gameObject.SetActive(true),
            actionOnRelease: ps => ps.gameObject.SetActive(false),
            actionOnDestroy: ps => Destroy(ps.gameObject),
            defaultCapacity: 10
        );
    }

    public void PlayHitVFX(Vector3 position)
    {
        var ps = _hitPool.Get();
        ps.transform.position = position;
        ps.Play();
        StartCoroutine(ReleaseAfterDelay(ps, _hitPool, ps.main.duration));
    }

    public void PlayDeathVFX(Vector3 position)
    {
        var ps = _deathPool.Get();
        ps.transform.position = position;
        ps.Play();
        StartCoroutine(ReleaseAfterDelay(ps, _deathPool, ps.main.duration));
    }

    private System.Collections.IEnumerator ReleaseAfterDelay(
        ParticleSystem ps, IObjectPool<ParticleSystem> pool, float delay)
    {
        yield return new WaitForSeconds(delay + 0.1f);
        pool.Release(ps);
    }
}
```

### 7. 자주 쓰는 픽셀아트 이펙트 종류

| 이펙트 | Burst Count | Lifetime | 특징 |
|--------|-------------|----------|------|
| 히트 스파크 | 4~6 | 0.2~0.3s | 작은 흰색 점, 빠른 속도 |
| 적 사망 | 8~12 | 0.4~0.6s | 적 색상 조각, 흩어짐 |
| 투사체 착탄 | 3~5 | 0.15~0.25s | 착탄 방향으로 퍼짐 |
| 대시 잔상 | 1~2/tick | 0.1s | 플레이어 색상, 페이드 |
| 패링 성공 | 6~10 | 0.3~0.5s | 밝은 노란색/흰색, 원형 |
| 레벨업 | 10~15 | 0.8~1.0s | 골드색, 위로 상승 |

---

## OnionCat 적용 포인트

### Cat (P1) 관련 VFX
- **슬래시 스윙**: 흰색 → 주황색 3~4개 파티클, 슬래시 방향으로 퍼짐
  - 180° 범위이므로 Shape를 Arc(180°)로 설정
- **대시 잔상**: 고양이 실루엣 색상(회색) 파티클 3~5개 / 0.05초마다 Burst
- **히트**: 피격 시 붉은 파티클 + 히트 플래시 동시 재생

### Crop (P2) 관련 VFX
- **투사체 발사**: 발사구에서 2~3개 연기 파티클 (작은 흰색/회색)
- **투사체 착탄**: 착탄 위치에서 녹색 파티클 5~8개 폭발
- **방패 패링**: 방패 방향으로 흰색 빛 파티클 6~10개 (짧고 강하게)

### 구조 제안
```
Prefabs/
  VFX/
    VFX_CatSlash.prefab         ← Cat 슬래시 이펙트
    VFX_CatDash.prefab          ← Cat 대시 잔상
    VFX_CropShot.prefab         ← Crop 투사체 착탄
    VFX_CropParry.prefab        ← Crop 패링 성공
    VFX_EnemyHit.prefab         ← 적 피격
    VFX_EnemyDeath.prefab       ← 적 사망
    VFX_LevelUp.prefab          ← 레벨업 / 업그레이드 획득
```

### [SerializeField] 설정 필요
- `PixelVFXPool` 컴포넌트의 `hitVFXPrefab`, `deathVFXPrefab` 필드에 유니티 에디터에서 드래그 앤 드롭 설정 필요
- `PixelSnapParticleSystem`의 `pixelsPerUnit` 값을 프로젝트 PPU와 맞게 설정

### 성능 주의
- 파티클 시스템은 화면에 많아지면 드로우콜이 급증
- `maxParticles`를 각 프리팹마다 30~50개로 제한
- 동시에 재생되는 VFX는 최대 10~15개로 제한 (VFXPool에서 큐 관리)

---

## 참고 링크

- [Unity Docs: Particle System](https://docs.unity3d.com/Manual/PartSysReference.html)
- [Unity Docs: Object Pool](https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html)
- [픽셀아트 파티클 튜토리얼 (GDQuest)](https://www.gdquest.com/tutorial/godot/vfx/particles/)
- [Unity 2D Pixel Art Best Practices](https://docs.unity3d.com/Manual/2DPixelPerfect.html)
- [URP Particle Shader 설정](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/particles-unlit-shader.html)
- [Low-res Pixel Particle Tips (itch.io devlogs)](https://itch.io/jam/pixel-art-jam)
