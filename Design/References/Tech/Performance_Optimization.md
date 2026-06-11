# 성능 최적화 (Performance Optimization)

리서치 날짜: 2026-06-11

## 개요
게임이 커질수록 FPS가 떨어지는 주요 원인: 잦은 Instantiate/Destroy, 과도한 드로우콜, 불필요한 물리 연산.
OnionCat처럼 투사체·적·파티클이 많이 생성/삭제되는 2D 로그라이크에서 필수 최적화 영역.

---

## Unity 구현 방법

### 1. 오브젝트 풀링 (Object Pooling)

Unity 2021+부터 `UnityEngine.Pool` 네임스페이스에서 `ObjectPool<T>` 기본 제공.
`Instantiate`/`Destroy` 대신 풀에서 꺼내고 돌려주는 방식으로 GC 스파이크 제거.

```csharp
using UnityEngine;
using UnityEngine.Pool;

public class BulletSpawner : MonoBehaviour
{
    [SerializeField] private Bullet bulletPrefab;
    private IObjectPool<Bullet> _pool;

    void Awake()
    {
        _pool = new ObjectPool<Bullet>(
            createFunc:      () => Instantiate(bulletPrefab),
            actionOnGet:     b  => b.gameObject.SetActive(true),
            actionOnRelease: b  => b.gameObject.SetActive(false),
            actionOnDestroy: b  => Destroy(b.gameObject),
            defaultCapacity: 20,
            maxSize:         100
        );
    }

    public Bullet GetBullet()         => _pool.Get();
    public void   ReturnBullet(Bullet b) => _pool.Release(b);
}
```

Bullet 클래스에서 수명 종료 시:
```csharp
// Bullet.cs
void OnBulletExpired()
{
    _spawner.ReturnBullet(this);   // Destroy() 대신 풀에 반환
}
```

적용 대상: 투사체, 히트 파티클, 적, 아이템 드롭 오브젝트 모두 풀링 권장.

---

### 2. 스프라이트 아틀라스 (Sprite Atlas)

같은 아틀라스에 묶인 스프라이트들은 GPU가 텍스처를 1번만 바인딩 → 드로우콜 대폭 감소.

**설정 방법:**
1. `Window > 2D > Sprite Atlas` → `.spriteatlas` 에셋 생성
2. Objects to Pack 목록에 스프라이트 또는 폴더 드래그
3. Pack Preview 클릭으로 결과 확인
4. `Edit > Project Settings > Editor > Sprite Packer` → `Always Enabled` 설정

**카테고리별 아틀라스 분리 권장 구성:**
| 아틀라스 이름 | 포함 스프라이트 |
|---------------|----------------|
| `Atlas_Player` | 고양이, 작물 전체 애니메이션 프레임 |
| `Atlas_Enemy` | 모든 적 스프라이트 |
| `Atlas_UI` | HUD 아이콘, 업그레이드 카드, 버튼 |
| `Atlas_Environment` | 타일, 방 장식물 |

**실측 사례:** 80개 개별 스프라이트 → 4개 아틀라스 묶기 후 드로우콜 74 → 8 (89% 감소), 프레임 타임 19ms → 11ms

---

### 3. 물리 레이어 콜리전 매트릭스 최적화

`Edit > Project Settings > Physics 2D > Layer Collision Matrix`
불필요한 레이어 간 충돌 체크 비활성화 → 브로드 페이즈 연산 감소.
대규모 시뮬레이션에서 충돌 체크 40%+ 감소 사례 보고.

**OnionCat 권장 레이어 충돌 설정:**
```
레이어          Player  Enemy  PlayerBullet  EnemyBullet  Wall
Player            -      O         -              O         O
Enemy             O      X         O              -         O
PlayerBullet      -      O         -              -         O
EnemyBullet       O      X         -              -         O
Wall              O      O         O              O         -

O = 충돌 ON  /  X = 충돌 OFF  /  - = 무관
```

핵심: `Enemy ↔ Enemy` OFF, `EnemyBullet ↔ Enemy` OFF, `PlayerBullet ↔ Player` OFF

---

### 4. Unity Profiler 활용

`Window > Analysis > Profiler`로 병목 지점을 데이터로 찾아야 올바른 최적화 가능.
"느린 것 같다"는 느낌으로 최적화하면 효과 없는 곳에 시간 낭비하게 됨.

| 탭 | 확인 항목 |
|----|-----------|
| CPU Usage | 어떤 함수가 ms를 많이 쓰는지 |
| Memory | GC Alloc 발생 위치 (new 키워드, LINQ, string 연산) |
| Rendering | 드로우콜 수, SetPass Call 수 |

**최적화 순서**: 프로파일러로 병목 찾기 → 병목 수정 → 재측정 → 반복

---

### 5. 기타 2D 최적화 팁

```csharp
// 나쁜 예: Update()마다 GetComponent 호출
void Update()
{
    GetComponent<Rigidbody2D>().velocity = ...;
    Camera.main.transform.position = ...;  // Camera.main도 Find와 동일한 비용
}

// 좋은 예: Awake()에서 캐싱
private Rigidbody2D _rb;
private Camera _cam;

void Awake()
{
    _rb = GetComponent<Rigidbody2D>();
    _cam = Camera.main;
}
```

- `Rigidbody2D.CollisionDetectionMode`:
  - `Discrete` (기본값): 빠름, 빠른 투사체 관통 가능
  - `Continuous`: 관통 방지, CPU 비용 더 높음 → 빠른 투사체에만 적용
- 파티클 시스템도 자주 재생되는 것(히트 이펙트, 사망 이펙트)은 풀링 대상
- `string.Format` / LINQ 사용 최소화 → GC Alloc 주범

---

## OnionCat 적용 포인트

1. **작물 투사체 즉시 풀링** — 작물(Player 2)의 투사체는 매 공격마다 생성 → `ObjectPool<Bullet>` 적용이 가장 체감 효과 큰 최적화

2. **적 풀링** — 방 입장 시 적을 한꺼번에 스폰하는 구조에서 `ObjectPool<Enemy>` 활용 → 방 전환 시 GC 스파이크 제거

3. **파티클 풀링** — 히트 이펙트, 파리 이펙트, 사망 이펙트처럼 반복 재생되는 파티클도 풀링 대상

4. **아틀라스 4개** — `Atlas_Player`, `Atlas_Enemy`, `Atlas_UI`, `Atlas_Environment`로 분리 → 씬 드로우콜 목표: 30 이하

5. **레이어 매트릭스** — `EnemyBullet ↔ Enemy` OFF만으로도 적 밀집 상황에서 체감 성능 개선 기대

6. **프로파일러 테스트 시나리오** — "방에 적 50마리 + 작물 연사 30발" 상황을 만들어 정기적으로 프로파일링

---

## 참고 링크
- [Unity 공식: Introduction to Object Pooling](https://learn.unity.com/tutorial/introduction-to-object-pooling)
- [Unity 공식: Pooling and Reusing Objects](https://docs.unity3d.com/6000.3/Documentation/Manual/performance-reusable-code.html)
- [IObjectPool 구현 예제 (Yarsa Labs)](https://blog.yarsalabs.com/object-pooling-in-unity-with-iobjectpool/)
- [Object Pooling in Unity 2021+ (TheGamedev.Guru)](https://thegamedev.guru/unity-cpu-performance/object-pooling/)
- [Draw Call Optimization 가이드 (TheGamedev.Guru)](https://thegamedev.guru/unity-performance/draw-call-optimization/)
- [Sprite Atlas 최적화 (Yarsa Labs)](https://blog.yarsalabs.com/game-optimization-using-unity-sprite-atlas/)
- [Layer Collision Matrix 공식 문서](https://docs.unity3d.com/6000.3/Documentation/Manual/physics-optimization-cpu-collision-layers.html)
- [Medium: Unity Draw Call & Sprite Atlas](https://medium.com/@shanlogauthier/unity-optimization-draw-calls-and-sprite-atlases-ae8af5c35e00)
