# 적 소환 예고 시스템 (Enemy Spawn Announcement System)

리서치 날짜: 2026-11-02

## 개요

전투 방에 적이 **나타나기 전에** 소환 위치를 시각적으로 예고하는 시스템.
기존 `Enemy_Telegraph_System`이 **공격 예고**(노란/빨간 경고)를 처리한다면,
이 시스템은 **적의 등장 자체를 예고**한다.

OnionCat의 설계 원칙 "모든 공격은 예고된다 (노란 = 막을 수 있음, 빨간 = 피해야 함)"을
적의 **소환 단계**까지 확장하는 것이 목적.
플레이어가 전략적으로 대응 위치를 잡을 수 있고, 예상치 못한 즉사를 줄여 준다.

---

## Unity 구현 방법

### 핵심 컴포넌트 구조

```
SpawnAnnouncement (MonoBehaviour)
├── SpriteRenderer shadow      ← 적 실루엣 (반투명)
├── float warmupTime           ← 예고 지속 시간
└── Action onSpawn             ← 타이머 만료 시 실제 소환 콜백
```

### SpawnAnnouncement 구현

```csharp
public class SpawnAnnouncement : MonoBehaviour
{
    [SerializeField] SpriteRenderer shadow;
    float warmupTime;
    float elapsed;
    System.Action onSpawn;

    public void Initialize(Sprite silhouette, float delay, System.Action spawnCallback)
    {
        shadow.sprite = silhouette;
        shadow.color = new Color(1f, 0.8f, 0f, 0.5f); // 시작: 노란 반투명
        warmupTime = delay;
        elapsed = 0;
        onSpawn = spawnCallback;
    }

    void Update()
    {
        elapsed += Time.deltaTime;
        float t = elapsed / warmupTime;

        // 노랑 → 빨강으로 선형 보간
        shadow.color = Color.Lerp(
            new Color(1f, 0.8f, 0f, 0.5f),
            new Color(1f, 0.2f, 0f, 0.85f),
            t
        );

        // 소환 직전 맥박 효과 (80% 이후)
        if (t > 0.8f)
        {
            float pulse = 1f + Mathf.Sin(elapsed * 25f) * 0.04f;
            transform.localScale = Vector3.one * pulse;
        }

        if (elapsed >= warmupTime)
        {
            onSpawn?.Invoke();
            PoolManager.Despawn(gameObject);
        }
    }

    void OnDisable() // Pool 반환 시 초기화
    {
        elapsed = 0;
        onSpawn = null;
        transform.localScale = Vector3.one;
    }
}
```

### EnemySpawner 연동

```csharp
// 기존: 즉시 소환
// PoolManager.Spawn(enemyPrefab, spawnPos, Quaternion.identity);

// 변경: 예고 후 소환
public void AnnounceAndSpawn(GameObject enemyPrefab, Vector3 pos, float delay = 1.2f)
{
    var marker = PoolManager.Spawn(spawnMarkerPrefab, pos, Quaternion.identity);
    var announcement = marker.GetComponent<SpawnAnnouncement>();

    // 적의 스프라이트를 실루엣으로 사용
    var enemySr = enemyPrefab.GetComponentInChildren<SpriteRenderer>();
    announcement.Initialize(
        enemySr ? enemySr.sprite : defaultSilhouette,
        delay,
        () => PoolManager.Spawn(enemyPrefab, pos, Quaternion.identity)
    );
}
```

---

## 소환 타이밍 분류

| 상황 | 예고 시간 | 색상 흐름 | 용도 |
|---|---|---|---|
| 즉시 등장 (0초) | 없음 | — | 소환수 (적이 부름), 보스 특수 기술 |
| 단기 예고 (0.5초) | 빠른 노랑→빨강 | 긴박감 전달 | 방 증원, 기습 암부쉬 |
| 표준 예고 (1.2초) | 노랑→빨강 | 기본 패턴 | 일반 전투 방 소환 |
| 장기 예고 (2.0초+) | 천천히 노랑→빨강 | 전략 준비 시간 | 보스 페이즈 전환, 특수 소환 |

---

## OnionCat 적용 포인트

### 기존 공격 예고와 색상 코드 통일
`Enemy_Telegraph_System`의 노란/빨간 공격 예고와 같은 색상 언어 사용.
플레이어가 추가 학습 없이 "노란 실루엣 = 준비 시간 있음, 빨간 실루엣 = 곧 나옴"을 직관적으로 읽음.

### 적용 우선 위치
1. **`DungeonManager.StartAmbush`**: 기습 적 소환 시 0.5~0.7초 예고 마커 선행 스폰
2. **`ShadowWitch` 보스 페이즈 2**: 하수 소환 위치를 1.5~2초 미리 표시
3. **전투 방 증원 패턴**: 방 진입 후 일정 시간 후 나타나는 증원 적에 표준 1.2초 예고

### 소환 예고 → 협동 전술 강화
소환 마커 위치에 양파의 심기 스킬로 식물을 미리 배치 가능.
고양이는 마커 위치를 피하며 현재 적을 처리, 양파는 마커 쪽을 준비.
**2인 역할 분담이 자연스럽게 발생**하는 구조.

### 구현 주의사항
- 마커 자체는 `PoolManager`로 관리 — `Room.ResetForReuse` 시 자동 정리
- 소환된 적의 첫 0.25초는 반투명 + 무적 처리 (마커에 올라탄 식물에 즉사 방지)
- `editor_play` 테스트 시 `OnionCat > Debug > Kill Enemies`로 마커 타이밍 확인

---

## 참고 링크

- Unity Object Pool API: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- GDC "Enemy Telegraphing in Action Games": https://www.gdcvault.com/play/1025437
- Hades 소환 연출 UX 분석: https://store.steampowered.com/app/1145360/Hades/
- Enter the Gungeon 소환 패턴 위키: https://enterthegungeon.fandom.com/wiki/Enemies
