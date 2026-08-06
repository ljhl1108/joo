# UniTask & Async/Await Pattern in Unity

리서치 날짜: 2026-08-06

## 개요

Unity의 기본 비동기 도구인 **코루틴(Coroutine)**은 `IEnumerator`와 `yield return`을 사용하는데, 이 방식은 코드가 파편화되고 예외 처리가 어렵다는 단점이 있다. C# 5.0부터 도입된 **async/await**는 비동기 코드를 마치 동기 코드처럼 읽을 수 있게 해준다.

Unity 표준 `System.Threading.Tasks.Task`는 GC(가비지 컬렉션) 할당이 많고 Unity의 게임 오브젝트 라이프사이클과 맞지 않는 문제가 있다. 이를 해결한 것이 **UniTask** — Cysharp가 만든 Zero-Allocation async/await 라이브러리.

OnionCat과 같은 로그라이크에서는 방 로딩, 적 스폰 웨이브, 씬 전환 등 **비동기 시퀀스**가 자주 필요하므로 UniTask 패턴 숙지는 핵심 역량이다.

---

## 코루틴 vs async/await 비교

### 코루틴 방식 (기존)
```csharp
IEnumerator SpawnEnemiesCoroutine() {
    for (int i = 0; i < 5; i++) {
        SpawnEnemy();
        yield return new WaitForSeconds(0.5f);
    }
    Debug.Log("스폰 완료");
    // 에러 처리 불가능!
}
StartCoroutine(SpawnEnemiesCoroutine());
```

### async/await 방식 (UniTask)
```csharp
async UniTask SpawnEnemiesAsync(CancellationToken ct) {
    try {
        for (int i = 0; i < 5; i++) {
            SpawnEnemy();
            await UniTask.Delay(500, cancellationToken: ct);  // 500ms
        }
        Debug.Log("스폰 완료");
    } catch (OperationCanceledException) {
        Debug.Log("스폰 취소됨");
    }
}
// 호출 (MonoBehaviour에서)
SpawnEnemiesAsync(this.GetCancellationTokenOnDestroy()).Forget();
```

---

## Unity 구현 방법

### 1. UniTask 설치
Package Manager에서 Git URL 추가:
```
https://github.com/Cysharp/UniTask.git?path=src/UniTask/Assets/Plugins/UniTask
```
또는 `Packages/manifest.json`에 직접 추가:
```json
"com.cysharp.unitask": "https://github.com/Cysharp/UniTask.git?path=src/UniTask/Assets/Plugins/UniTask"
```

### 2. 기본 사용 패턴

#### 단순 대기
```csharp
// 코루틴 대응 비교
// yield return new WaitForSeconds(1f);  // 코루틴
await UniTask.Delay(1000);               // UniTask (밀리초)
await UniTask.DelayFrame(30);            // 30프레임 대기
await UniTask.Yield();                   // 1프레임 대기
await UniTask.WaitForEndOfFrame(this);   // 프레임 끝 대기
```

#### 조건 대기
```csharp
// 적이 죽을 때까지 대기
await UniTask.WaitUntil(() => enemy.IsDead);
await UniTask.WaitWhile(() => enemy.IsAlive);
```

### 3. 병렬 실행 (WhenAll / WhenAny)
```csharp
// 두 작업을 동시에 실행하고 둘 다 끝날 때까지 대기
await UniTask.WhenAll(
    LoadRoomDataAsync(ct),
    PreloadEnemySpritesAsync(ct)
);

// 둘 중 먼저 끝나는 것만 기다림 (레이스)
await UniTask.WhenAny(
    WaitForPlayerInputAsync(ct),
    UniTask.Delay(5000, cancellationToken: ct)  // 5초 타임아웃
);
```

### 4. CancellationToken — 오브젝트 파괴 시 자동 취소
```csharp
public class EnemySpawner : MonoBehaviour {
    private void Start() {
        // this.GetCancellationTokenOnDestroy(): 이 게임오브젝트가 파괴되면 자동 취소
        RunSpawnLoopAsync(this.GetCancellationTokenOnDestroy()).Forget();
    }

    private async UniTask RunSpawnLoopAsync(CancellationToken ct) {
        while (!ct.IsCancellationRequested) {
            SpawnEnemy();
            await UniTask.Delay(2000, cancellationToken: ct);
        }
    }
}
```

### 5. 반환값이 있는 async
```csharp
// 씬 로딩 후 컨트롤러 반환
async UniTask<RoomController> LoadRoomAsync(RoomData data, CancellationToken ct) {
    var operation = SceneManager.LoadSceneAsync(data.sceneName, LoadSceneMode.Additive);
    await operation.ToUniTask(cancellationToken: ct);
    return FindObjectOfType<RoomController>();
}

// 호출
var roomController = await LoadRoomAsync(nextRoom, ct);
roomController.Initialize();
```

### 6. .Forget() vs await 선택
```csharp
// 결과를 기다릴 필요 없을 때 (fire-and-forget)
PlayDeathAnimationAsync(ct).Forget();

// 완료를 확인해야 할 때
await PlayDeathAnimationAsync(ct);
NextPhase();  // 애니메이션 끝난 후 실행 보장
```

---

## OnionCat 적용 포인트

### 1. 방 전환 시퀀스
코루틴 중첩 지옥을 async 체인으로 깔끔하게:
```csharp
async UniTask TransitionToNextRoomAsync(CancellationToken ct) {
    await PlayRoomClearAnimationAsync(ct);       // 방 클리어 연출 (1초)
    await UniTask.Delay(500, cancellationToken: ct);
    await FadeOutAsync(ct);                       // 페이드 아웃 (0.5초)
    LoadNextRoom();
    await FadeInAsync(ct);                        // 페이드 인 (0.5초)
    SpawnPlayers();
}
```

### 2. 적 스폰 웨이브 컨트롤
```csharp
async UniTask SpawnWaveAsync(WaveData wave, CancellationToken ct) {
    foreach (var spawnInfo in wave.enemies) {
        SpawnEnemy(spawnInfo);
        await UniTask.Delay(spawnInfo.delayMs, cancellationToken: ct);
    }
    await UniTask.WaitUntil(() => _aliveEnemies.Count == 0, cancellationToken: ct);
    OnWaveComplete();
}
```

### 3. 업그레이드 선택 UI 대기
```csharp
async UniTask<UpgradeItem> WaitForUpgradeSelectionAsync(CancellationToken ct) {
    _upgradeUI.Show();
    // 플레이어가 선택할 때까지 대기
    var selected = await UniTask.WaitUntil(
        () => _upgradeUI.SelectedItem != null, 
        cancellationToken: ct
    );
    _upgradeUI.Hide();
    return _upgradeUI.SelectedItem;
}
```

### 4. 코루틴과 혼용 (레거시 코드 마이그레이션)
기존 코루틴을 바꾸기 어렵다면 부분적으로 변환 가능:
```csharp
// 코루틴을 UniTask로 감싸기
await coroutine.ToUniTask(this);
```

---

## 주의사항

| 주의점 | 내용 |
|--------|------|
| `.Forget()` 남용 | 예외가 조용히 무시됨 — 중요한 작업엔 `await` 사용 |
| CancellationToken 누락 | 오브젝트 파괴 후도 작업 실행 → NullReference 유발 |
| 메인 스레드 보장 | UniTask는 기본적으로 Unity 메인 스레드에서 실행 (PlayerLoop 기반) |
| `Task` vs `UniTask` | `Task`는 스레드 풀 사용, `UniTask`는 Unity PlayerLoop 사용 — 섞지 말 것 |

---

## 참고 링크

- UniTask GitHub: https://github.com/Cysharp/UniTask
- UniTask 공식 문서: https://github.com/Cysharp/UniTask#readme
- Unity 코루틴 vs async/await 비교 (Unity 블로그): https://blog.unity.com/engine-platform/introduction-to-unitask
- 한국어 설명 (유니티 커뮤니티): "UniTask 사용법" 검색
