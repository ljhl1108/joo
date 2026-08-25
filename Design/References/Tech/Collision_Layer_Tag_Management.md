# 충돌 레이어 & 태그 관리 베스트 프랙티스

리서치 날짜: 2026-08-25

## 개요

Unity의 물리 레이어(Layer)와 태그(Tag)는 게임 오브젝트 간의 상호작용을 제어하는 핵심 시스템이다.
초보 개발자들이 흔히 모든 오브젝트를 Default 레이어에 두거나 태그를 남발하다가 나중에 엉키는 경우가 많다.
OnionCat처럼 플레이어, 적, 투사체, 방어막이 복잡하게 상호작용하는 게임에서는 **초기 설계가 매우 중요**하다.

### 왜 중요한가?
- **성능**: 불필요한 충돌 체크 제거 → CPU Physics 부하 감소
- **버그 방지**: 내 투사체가 나를 맞추는 사고 방지
- **명확성**: 어떤 오브젝트가 무엇과 충돌하는지 한눈에 파악

---

## Unity 레이어 시스템 기초

Unity는 최대 **32개의 레이어** 지원 (0~7은 Built-in, 8~31은 User-defined).

### 레이어 vs 태그 차이

| 구분 | Layer | Tag |
|------|-------|-----|
| 용도 | 물리 충돌 필터링, 렌더링, 레이캐스트 | 오브젝트 식별 (코드에서) |
| 성능 영향 | Physics Layer Matrix로 직접 제어 | 비교적 적음 |
| 개수 제한 | 32개 | 제한 없음 |
| 사용 위치 | Physics2D.IgnoreLayerCollision, LayerMask | CompareTag(), GameObject.FindWithTag() |

---

## OnionCat 권장 레이어 설계

### 레이어 목록

```
Layer 0:  Default          (Unity 기본)
Layer 1:  TransparentFX    (Unity 기본)
Layer 2:  Ignore Raycast   (Unity 기본)
Layer 3:  Water            (Unity 기본)
Layer 4:  UI               (Unity 기본)
Layer 5:  (미사용)
Layer 6:  (미사용)
Layer 7:  (미사용)

Layer 8:  Player           ← Cat+Onion 몸체 (플레이어 히트박스)
Layer 9:  Enemy            ← 적 히트박스
Layer 10: PlayerProjectile ← Onion의 투사체
Layer 11: EnemyProjectile  ← 적의 투사체
Layer 12: Shield           ← Onion의 방어막
Layer 13: Wall             ← 방 벽, 장애물 (Tilemap)
Layer 14: Floor            ← 바닥 (이동 가능 영역)
Layer 15: Interactable     ← 문, 아이템, 상호작용 오브젝트
Layer 16: VFX              ← 파티클, 이펙트 (물리 무시)
Layer 17: MeleeHitbox      ← Cat의 슬래시 히트박스 (한 프레임만 활성화)
```

### Physics Layer Collision Matrix 설정

Edit > Project Settings > Physics 2D > Layer Collision Matrix

```
충돌 허용 (O) / 충돌 금지 (X)

              Player  Enemy  PlayerProj  EnemyProj  Shield  Wall  MeleeHitbox
Player          X       X        X           O        X      O        X
Enemy           X       X        X           X        X      O        X
PlayerProj      X       X        X           X        X      O        X
EnemyProj       O       X        X           X        O      O        X
Shield          X       X        X           O        X      X        X
Wall            O       O        O           O        X      X        X
MeleeHitbox     X       O        X           X        X      X        X
```

**핵심 설계 의도:**
- `PlayerProjectile ↔ Enemy`: O (Onion의 투사체가 적 맞춤)
- `PlayerProjectile ↔ Player`: X (내 투사체가 나를 맞추지 않음)
- `EnemyProjectile ↔ Player`: O (적 투사체가 플레이어를 맞춤)
- `EnemyProjectile ↔ Shield`: O (방어막이 적 투사체를 받아냄)
- `MeleeHitbox ↔ Enemy`: O (Cat의 슬래시가 적에게만 작동)
- `Enemy ↔ Enemy`: X (적끼리 서로 밀치지 않음 - 성능 최적화)

---

## Unity 구현 방법

### Step 1: 레이어 설정
1. Edit > Project Settings > Tags and Layers
2. "Layers" 섹션에서 Layer 8~17 이름 입력

### Step 2: Physics Matrix 설정
1. Edit > Project Settings > Physics 2D
2. 하단 "Layer Collision Matrix" 체크박스 설정

### Step 3: 코드에서 레이어 사용

```csharp
// LayerMask 선언 (Inspector에서 설정 가능)
[SerializeField] private LayerMask enemyLayer;
[SerializeField] private LayerMask wallLayer;

// 레이캐스트에서 특정 레이어만 감지
RaycastHit2D hit = Physics2D.Raycast(origin, direction, distance, enemyLayer);

// 오브젝트의 레이어 비교
void OnTriggerEnter2D(Collider2D other)
{
    if (other.gameObject.layer == LayerMask.NameToLayer("Enemy"))
    {
        // 적과 충돌 처리
    }
}

// 런타임에서 레이어 변경 (거의 필요 없음, 피하는 것이 좋음)
gameObject.layer = LayerMask.NameToLayer("PlayerProjectile");
```

### Step 4: 태그 설계

태그는 레이어와 별개로, **코드에서 오브젝트를 식별**할 때 사용.

```
권장 태그 목록:
- "Player"       : Cat+Onion 몸체
- "Enemy"        : 모든 적
- "Boss"         : 보스 (적의 하위 분류)
- "Projectile"   : 모든 투사체 (플레이어/적 공통)
- "Item"         : 획득 가능 아이템
- "Door"         : 방 문
- "SpawnPoint"   : 적 스폰 위치
```

**태그 사용법:**

```csharp
// 추천: CompareTag() 사용 (문자열 할당 없음 → 성능 우수)
if (other.CompareTag("Enemy"))
{
    TakeDamage();
}

// 비추천: == 문자열 비교 (매번 문자열 생성)
if (other.tag == "Enemy") // 이렇게 하지 말 것
```

---

## 자주 하는 실수와 해결법

### 실수 1: 모든 오브젝트를 Default 레이어에 두기
- **문제**: 불필요한 충돌 체크 → 성능 저하, 의도치 않은 충돌 발생
- **해결**: 위의 레이어 설계를 초기에 적용

### 실수 2: 레이어 대신 태그로 충돌 처리
- **문제**: OnTriggerEnter에서 태그로 체크하면 충돌 자체는 항상 발생 → 불필요한 콜백
- **해결**: Physics Layer Matrix로 충돌 여부 결정 → 태그는 "어떻게 처리할지" 결정에만 사용

### 실수 3: MeleeHitbox를 항상 활성화
- **문제**: 슬래시 애니메이션과 무관하게 계속 적과 충돌
- **해결**: 
```csharp
// 슬래시 시작 시
meleeCollider.enabled = true;

// 슬래시 종료 시 (AnimationEvent 또는 코루틴)
meleeCollider.enabled = false;
```

### 실수 4: Enemy끼리 충돌 허용
- **문제**: 적이 많아질수록 서로 밀치는 물리 계산 급증
- **해결**: Enemy ↔ Enemy 충돌 Matrix에서 X로 설정

---

## OnionCat 적용 포인트

### Shield(방어막) 충돌 특이 사항
- Onion의 방어막은 `EnemyProjectile`과만 충돌
- 방어막이 활성화되면 Player Collider와 별도로 동작
- 파리(Perfect Parry) 성공 시 Shield 콜라이더의 `isTrigger` 상태 변경:

```csharp
[SerializeField] private Collider2D shieldCollider;
[SerializeField] private bool isParryWindow = false;

void OnTriggerEnter2D(Collider2D other)
{
    if (other.CompareTag("EnemyProjectile"))
    {
        if (isParryWindow)
            TriggerParry(other); // 파리 성공
        else
            BlockProjectile(other); // 일반 방어
    }
}
```

### MeleeHitbox 애니메이션 연동
Cat의 슬래시 히트박스는 AnimationEvent로 제어:

```csharp
// AnimationEvent에서 호출 (Unity 에디터에서 설정 필요)
public void OnSlashStart()
{
    meleeHitboxCollider.enabled = true;
}

public void OnSlashEnd()
{
    meleeHitboxCollider.enabled = false;
}
```

### LayerMask 캐싱
```csharp
// Awake에서 캐싱 (Update에서 계산하지 말 것)
private int playerLayer;
private int enemyLayer;

void Awake()
{
    playerLayer = LayerMask.NameToLayer("Player");
    enemyLayer = LayerMask.NameToLayer("Enemy");
}
```

---

## 참고 링크

- Unity 공식 - Physics 2D Layer Collision Matrix: https://docs.unity3d.com/Manual/LayerBasedCollision.html
- Unity 공식 - Tags: https://docs.unity3d.com/Manual/Tags.html
- Unity 공식 - LayerMask: https://docs.unity3d.com/ScriptReference/LayerMask.html
- Unity Blog - 2D Physics Performance Tips: https://blog.unity.com/technology/2d-physics-in-unity
- Brackeys - Layers Tutorial: https://www.youtube.com/watch?v=bkVQRqYFMmg
