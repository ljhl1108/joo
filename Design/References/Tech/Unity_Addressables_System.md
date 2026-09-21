# Unity Addressables System

리서치 날짜: 2026-09-18

## 개요

Unity Addressables(어드레서블)는 **런타임에 에셋을 주소(address)로 요청해 비동기 로드/언로드**하는 에셋 관리 시스템이다.
`Resources.Load`나 `AssetBundle`의 단점을 개선한 공식 패키지(`com.unity.addressables`).

OnionCat에서 중요한 이유:
- 방(Room) 프리팹을 게임 내내 메모리에 올려두지 않고 **필요한 순간에만 로드**
- 적 프리팹을 층(Floor) 테마별로 묶어서 한 번에 로드/언로드
- 업그레이드 아이템 ScriptableObject를 씬 시작 시 비동기 로드 → 씬 전환이 빨라짐
- 빌드 용량 최적화 — 사용 안 하는 에셋은 번들에 포함되지 않음

---

## Unity 구현 방법

### 1. 패키지 설치

```
Window > Package Manager > Unity Registry > Addressables > Install
```
설치 후 `Window > Asset Management > Addressables > Groups`로 Addressables Groups 창 열기.

### 2. 에셋에 주소 할당

Inspector에서 에셋 선택 → **Addressable 체크박스 활성화** → 자동으로 기본 주소(파일 경로)가 할당됨.
주소를 짧고 명확하게 수정 권장: `Enemies/Goblin`, `Rooms/CombatRoom_01`

### 3. 라벨(Label) 활용

Addressables Groups 창에서 에셋마다 **Label** 부여 가능:
- `Floor1Enemies`, `Floor2Enemies`
- `CommonRooms`, `BossRooms`
- `UpgradeItems`

라벨로 한 번에 여러 에셋을 일괄 로드할 수 있음.

### 4. 코드로 로드 — 단일 에셋

```csharp
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

// AssetReference 필드 (Inspector에서 드래그 연결)
[SerializeField] private AssetReference enemyPrefabRef;

private AsyncOperationHandle<GameObject> _handle;

private async void SpawnEnemy()
{
    _handle = Addressables.LoadAssetAsync<GameObject>(enemyPrefabRef);
    await _handle.Task;

    if (_handle.Status == AsyncOperationStatus.Succeeded)
    {
        Instantiate(_handle.Result, spawnPos, Quaternion.identity);
    }
}

private void OnDestroy()
{
    if (_handle.IsValid())
        Addressables.Release(_handle); // 참조 카운트 감소 → 0 되면 메모리 해제
}
```

### 5. 코드로 로드 — 라벨 일괄 로드

```csharp
private List<AsyncOperationHandle<GameObject>> _handles = new();

private async void LoadFloorEnemies(int floorIndex)
{
    string label = $"Floor{floorIndex}Enemies";
    var locations = await Addressables.LoadResourceLocationsAsync(label).Task;

    foreach (var loc in locations)
    {
        var handle = Addressables.LoadAssetAsync<GameObject>(loc);
        await handle.Task;
        _handles.Add(handle);
    }
}

private void UnloadFloorEnemies()
{
    foreach (var handle in _handles)
        Addressables.Release(handle);
    _handles.Clear();
}
```

### 6. InstantiateAsync (로드 + 생성 한 번에)

```csharp
// 로드 + 인스턴스화를 한 번에. 해당 오브젝트 Destroy 시 자동으로 Release됨
var handle = Addressables.InstantiateAsync(enemyPrefabRef, position, Quaternion.identity);
await handle.Task;
```

`InstantiateAsync`를 사용하면 **Destroy()가 Release() 역할도 함** — 간단한 경우 권장.

### 7. ScriptableObject 로드

```csharp
[SerializeField] private AssetReferenceT<UpgradeItemData> upgradeDataRef;

private async void LoadUpgradeItem()
{
    var data = await Addressables.LoadAssetAsync<UpgradeItemData>(upgradeDataRef).Task;
    ApplyUpgrade(data);
    // 사용 완료 후 Release 필요 (ScriptableObject는 Destroy로 안 됨)
}
```

### 8. 원격 배포 (선택사항, 나중에)

Addressables Groups의 각 그룹 설정에서 **Build Path / Load Path**를 변경하면 CDN에서 다운로드 가능.
OnionCat 수준에서는 Local만 써도 충분.

---

## OnionCat 적용 포인트

### 방(Room) 프리팹 관리

```csharp
// RoomLoader.cs
[SerializeField] private AssetReference[] combatRoomRefs;
[SerializeField] private AssetReference[] bossRoomRefs;

public async Task<GameObject> LoadRoom(RoomType type)
{
    var pool = type == RoomType.Boss ? bossRoomRefs : combatRoomRefs;
    var randomRef = pool[Random.Range(0, pool.Length)];
    var handle = Addressables.InstantiateAsync(randomRef, Vector3.zero, Quaternion.identity);
    await handle.Task;
    return handle.Result;
}
```

방이 언로드될 때 `Addressables.ReleaseInstance(roomGO)` 호출 → 이전 방 메모리 즉시 정리.

### 층 테마 적 일괄 관리

- 1층 진입 시 `Floor1Enemies` 라벨 에셋 모두 PreWarm 로드
- 2층 전환 직전 `Floor1Enemies` 언로드 + `Floor2Enemies` 로드 시작 (비동기로 전환 중 미리 준비)
- 보스 룸 진입 시 `BossEnemies` 별도 로드

### 업그레이드 아이템 ScriptableObject

- 모든 업그레이드 아이템 데이터를 `UpgradeItems` 라벨로 묶기
- 업그레이드 선택 화면이 열릴 때 해당 라벨 에셋 5~6개 랜덤 로드
- 선택 완료 후 선택 안 한 나머지 Release

### 빌드 최적화

- Addressables Analyze 창(`Window > Asset Management > Addressables > Analyze`)에서 중복 에셋 확인
- "Check Duplicate Bundle Dependencies" 규칙 실행 → 중복 포함 에셋 발견 시 별도 공유 그룹으로 분리

---

## 참고 링크

- [Unity Addressables 공식 문서](https://docs.unity3d.com/Packages/com.unity.addressables@latest)
- [Unity Learn: Addressables 시작하기](https://learn.unity.com/tutorial/introduction-to-addressable-assets)
- [Unity Blog: Addressables 모범 사례](https://blog.unity.com/games/addressables-best-practices)
- [Infallible Code: Addressables 실전 영상 (YouTube)](https://www.youtube.com/c/InfallibleCode)
- [Jason Weimann: Memory 관리 + Addressables](https://www.youtube.com/c/JasonWeimann)
