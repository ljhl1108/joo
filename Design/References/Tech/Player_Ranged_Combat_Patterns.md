# Player 2 원거리 전투 패턴 시스템

리서치 날짜: 2026-08-28

## 개요

OnionCat의 Player 2(작물/양파)는 마우스 조준 기반 원거리 투사체와 방향 방패를 사용한다. 이 문서는 Player 2 전투 패턴의 Unity 구현 방법, 투사체 다양화, 업그레이드 통한 패턴 변형까지를 다룬다. 투사체 시스템(탄막 패턴) 회전 항목의 Player-side 적용 버전.

---

## Unity 구현 방법

### 1. 기본 단발 발사 구조

```csharp
public class CropShooter : MonoBehaviour
{
    [SerializeField] private GameObject projectilePrefab;
    [SerializeField] private Transform firePoint;
    [SerializeField] private float projectileSpeed = 10f;
    [SerializeField] private float fireRate = 0.5f;

    private float _nextFireTime;
    private Camera _mainCamera;

    private void Awake()
    {
        _mainCamera = Camera.main;
    }

    private void Update()
    {
        // Player 2는 마우스 방향으로 조준
        Vector2 mouseWorld = _mainCamera.ScreenToWorldPoint(Input.mousePosition);
        Vector2 direction = (mouseWorld - (Vector2)transform.position).normalized;

        if (Input.GetMouseButton(0) && Time.time >= _nextFireTime)
        {
            Shoot(direction);
            _nextFireTime = Time.time + fireRate;
        }
    }

    private void Shoot(Vector2 direction)
    {
        // 오브젝트 풀에서 가져오는 것이 이상적이나, 프로토타입 단계에서 Instantiate 사용 가능
        GameObject proj = Instantiate(projectilePrefab, firePoint.position, Quaternion.identity);
        proj.GetComponent<Rigidbody2D>().velocity = direction * projectileSpeed;

        // 투사체 회전 (비주얼 정렬)
        float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
        proj.transform.rotation = Quaternion.Euler(0, 0, angle);
    }
}
```

### 2. New Input System 적용 버전

```csharp
// PlayerInput 컴포넌트 + InputActionAsset 사용
public class CropShooter : MonoBehaviour
{
    [SerializeField] private GameObject projectilePrefab;
    [SerializeField] private Transform firePoint;

    private InputAction _fireAction;
    private InputAction _aimAction;
    private Camera _cam;

    private void Awake()
    {
        _cam = Camera.main;
        var input = GetComponent<PlayerInput>();
        _fireAction = input.actions["Fire"];
        _aimAction = input.actions["Aim"]; // Mouse Position 바인딩
    }

    private void OnEnable()  { _fireAction.performed += OnFire; }
    private void OnDisable() { _fireAction.performed -= OnFire; }

    private void OnFire(InputAction.CallbackContext ctx)
    {
        Vector2 aimPos = _cam.ScreenToWorldPoint(_aimAction.ReadValue<Vector2>());
        Vector2 dir = (aimPos - (Vector2)transform.position).normalized;
        SpawnProjectile(dir);
    }
}
```

### 3. 투사체 패턴 변형 (업그레이드 시스템 연동)

```csharp
public enum ShotPattern { Single, Double, Triple, Fan, Burst }

public class CropShooter : MonoBehaviour
{
    [SerializeField] private ShotPattern currentPattern = ShotPattern.Single;
    [SerializeField] private float spreadAngle = 15f;  // Fan 패턴에서 각도 간격

    private void FirePattern(Vector2 baseDir)
    {
        switch (currentPattern)
        {
            case ShotPattern.Single:
                SpawnProjectile(baseDir);
                break;

            case ShotPattern.Double:
                SpawnProjectile(Rotate(baseDir, -spreadAngle * 0.5f));
                SpawnProjectile(Rotate(baseDir,  spreadAngle * 0.5f));
                break;

            case ShotPattern.Triple:
                SpawnProjectile(baseDir);
                SpawnProjectile(Rotate(baseDir, -spreadAngle));
                SpawnProjectile(Rotate(baseDir,  spreadAngle));
                break;

            case ShotPattern.Fan:
                // 5발 부채꼴
                for (int i = -2; i <= 2; i++)
                    SpawnProjectile(Rotate(baseDir, i * spreadAngle));
                break;

            case ShotPattern.Burst:
                StartCoroutine(BurstRoutine(baseDir));
                break;
        }
    }

    private IEnumerator BurstRoutine(Vector2 dir)
    {
        for (int i = 0; i < 3; i++)
        {
            SpawnProjectile(dir);
            yield return new WaitForSeconds(0.08f);
        }
    }

    private Vector2 Rotate(Vector2 v, float degrees)
    {
        float rad = degrees * Mathf.Deg2Rad;
        return new Vector2(
            v.x * Mathf.Cos(rad) - v.y * Mathf.Sin(rad),
            v.x * Mathf.Sin(rad) + v.y * Mathf.Cos(rad)
        );
    }
}
```

### 4. 투사체 ScriptableObject 데이터 분리

```csharp
[CreateAssetMenu(menuName = "OnionCat/ProjectileData")]
public class ProjectileData : ScriptableObject
{
    public float speed = 10f;
    public float damage = 10f;
    public float lifetime = 3f;
    public bool piercing = false;
    public int bounceCount = 0;
    public GameObject vfxOnHit;
}
```

```csharp
public class Projectile : MonoBehaviour
{
    [SerializeField] private ProjectileData data;

    private void Start()
    {
        GetComponent<Rigidbody2D>().velocity = transform.right * data.speed;
        Destroy(gameObject, data.lifetime);
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Enemy"))
        {
            other.GetComponent<EnemyHealth>()?.TakeDamage(data.damage);
            if (!data.piercing)
                Destroy(gameObject);
        }
    }
}
```

### 5. 방패(Shield) + 패리 반사 연동

```csharp
// 방패 방향 체크 → 적 투사체 반사
public class CropShield : MonoBehaviour
{
    [SerializeField] private float parryWindow = 0.15f;  // 패리 가능 시간
    private bool _isParrying;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (!other.CompareTag("EnemyProjectile")) return;

        if (_isParrying)
        {
            // 패리 성공: 반사 처리
            var proj = other.GetComponent<EnemyProjectile>();
            proj.Reflect(transform.up);  // 방패 법선 방향으로 반사
        }
        else
        {
            // 방패로 막기: 데미지 0, 밀림 없음
            Destroy(other.gameObject);
        }
    }
}
```

---

## OnionCat 적용 포인트

### 취약점 체계와 투사체 연동

Player 2의 원거리 공격은 "원거리 공격에만 약한" 적에게만 유효해야 한다:

```csharp
public class EnemyHealth : MonoBehaviour
{
    public enum WeaknessType { MeleeOnly, RangeOnly, Both }
    [SerializeField] private WeaknessType weakness;

    public void TakeDamageFrom(float amount, bool isMelee)
    {
        bool effective = weakness == WeaknessType.Both
            || (weakness == WeaknessType.MeleeOnly && isMelee)
            || (weakness == WeaknessType.RangeOnly && !isMelee);

        if (!effective)
        {
            // 효과 없음 — 실드/저항 VFX 재생
            ShowImmuneEffect();
            return;
        }
        currentHP -= amount;
    }
}
```

### 패턴 업그레이드 연동 시 권장 방식

- 업그레이드 아이템에 `ShotPattern`을 직접 할당하지 말고, **업그레이드 이벤트** 방식으로:

```csharp
// 업그레이드 픽업 시
public void ApplyUpgrade(ShotPattern newPattern)
{
    GetComponent<CropShooter>().currentPattern = newPattern;
}
```

### 연사 속도 vs. 패턴 트레이드오프 설계

| 패턴 | 권장 fireRate | 데미지 배율 | OnionCat 역할 |
|------|-------------|------------|--------------|
| Single | 0.3s | 1.0x | 원거리 약점 적 정밀 타격 |
| Triple | 0.6s | 0.7x per shot | 다수 원거리 약점 적 처리 |
| Fan | 0.8s | 0.5x per shot | 근접 견제, 코너 클리어링 |
| Burst | 0.8s | 0.9x per shot | 단일 강적 집중 타격 |

---

## 참고 링크

- Unity New Input System 마우스 조준 구현: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.8/manual/index.html
- ScriptableObject 무기 데이터 패턴: https://unity.com/how-to/architect-game-code-scriptable-objects
- 투사체 패턴 설계 (GDC): https://www.gdcvault.com/play/1024786
- 2D 투사체 반사 구현: https://docs.unity3d.com/ScriptReference/Physics2D.Reflect.html
