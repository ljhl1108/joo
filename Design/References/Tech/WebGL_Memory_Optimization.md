# WebGL Memory Optimization (WebGL 메모리 최적화)

리서치 날짜: 2026-08-19

## 개요

Unity 게임을 WebGL로 itch.io에 올리면 브라우저에서 바로 플레이 가능하다 — 가장 빠르게 다른 사람에게 보여줄 수 있는 방법. 그러나 WebGL은 메모리, 로딩 시간, 기능 제한이 크다. 빌드는 Build_and_Deploy.md에서 다뤘고, 여기서는 **WebGL 브라우저 런타임에서 발생하는 메모리 문제와 최적화**에 집중한다. OnionCat 데모를 itch.io에 올릴 때 필수 지식이다.

---

## Unity 구현 방법

### Step 1: WebGL 메모리 설정 (Player Settings)

```
Edit → Project Settings → Player → WebGL → Publishing Settings
```

| 설정 | 권장값 | 설명 |
|------|--------|------|
| Initial Memory Size | 32MB | 시작 메모리 (너무 크면 로드 실패) |
| Maximum Memory Size | 512MB | 최대 한도 (256~512 권장) |
| Memory Growth Mode | Geometric | 필요 시 자동으로 늘어남 |
| Exception Support | Explicitly Thrown Exceptions Only | None 다음으로 가볍고 디버그 가능 |
| Compression Format | Brotli | 가장 압축률 높음 (itch.io는 지원) |

### Step 2: 텍스처 메모리 줄이기

WebGL에서 VRAM이 아닌 **시스템 RAM**에 텍스처가 올라감 → 픽셀아트 게임이라도 큰 아틀라스는 문제:

```csharp
// 텍스처 임포트 설정 (스크립트로 일괄 처리 가능)
// Edit → Project Settings → Texture Import에서 직접 설정 가능

// 픽셀아트용 최적 임포트 세팅
// Inspector에서 수동 설정:
// - Compression: Crunch Compression (WebGL에서 효율적)
// - Max Size: 1024 이하 (픽셀아트는 512 이하도 충분)
// - Generate Mipmaps: 체크 해제 (2D 게임은 불필요)
```

Sprite Atlas 사용으로 드로우콜 + 메모리 효율 동시 개선:
- `Sprite_Atlas_Pixel_Art_Import.md` 참고

### Step 3: 오디오 압축

WebGL에서 오디오는 메모리를 많이 잡아먹음:

```
Audio Clip Inspector 권장 설정 (WebGL):
- Load Type: Compressed In Memory
- Compression Format: Vorbis
- Quality: 50~70%
- BGM은 Streaming 사용 (메모리 즉시 해제)
```

코드에서 AudioClip 미리 해제:

```csharp
// 씬 전환 시 미사용 오디오 클립 해제
Resources.UnloadUnusedAssets();
```

### Step 4: 오브젝트 풀링으로 GC 압박 줄이기

WebGL은 Garbage Collector가 느리다. 적이 계속 생성/삭제되면 GC 스파이크 → 프레임 드랍:

```csharp
// 오브젝트 풀 사용 예시 (Unity 2021.1+ 내장 풀 API)
using UnityEngine.Pool;

public class EnemySpawner : MonoBehaviour
{
    [SerializeField] private Enemy enemyPrefab;
    private ObjectPool<Enemy> _pool;

    private void Awake()
    {
        _pool = new ObjectPool<Enemy>(
            createFunc: () => Instantiate(enemyPrefab),
            actionOnGet: e => e.gameObject.SetActive(true),
            actionOnRelease: e => e.gameObject.SetActive(false),
            collectionCheck: false,
            defaultCapacity: 20,
            maxSize: 50
        );
    }

    public Enemy SpawnEnemy() => _pool.Get();
    public void ReturnEnemy(Enemy e) => _pool.Release(e);
}
```

`Object_Pooling_System.md` 및 `Unity_Object_Pool_API.md` 참고.

### Step 5: 씬 로딩 전략

WebGL은 씬을 메모리에서 분리하기 어려움. 작은 씬 단위로 분리:

```csharp
// 이전 씬 메모리 명시적 해제
IEnumerator LoadSceneAndCleanup(string sceneName)
{
    yield return SceneManager.UnloadSceneAsync(SceneManager.GetActiveScene());
    Resources.UnloadUnusedAssets();
    GC.Collect();
    yield return SceneManager.LoadSceneAsync(sceneName);
}
```

### Step 6: WebGL 빌드 후 실제 메모리 측정

브라우저 개발자 도구 (F12) → Performance 탭 → Memory 탭에서 JS Heap 확인:
- 정상: 게임 플레이 중 100~200MB 수준
- 경고: 400MB 이상 → 텍스처/오디오 재검토
- 크래시: "Out of Memory" 오류 → Initial Memory Size 늘리거나 에셋 줄이기

### 흔한 WebGL 오류 및 해결책

| 오류 | 원인 | 해결 |
|------|------|------|
| "Out of memory" | 메모리 부족 | Maximum Memory Size 증가 or 에셋 압축 |
| 로딩에 5분 이상 | 빌드 파일 크기 과다 | Brotli 압축, 텍스처 축소 |
| 오디오 안 들림 | 브라우저 자동 재생 차단 | 첫 클릭 후 AudioListener.pause = false |
| 마우스 포인터 게임 밖 이탈 | Cursor.lockState 미설정 | 입력 시 CursorLockMode.Confined 설정 |
| 멀티플레이어 입력 충돌 | 단일 키보드 2인 입력 | New Input System으로 분리 (Local_Coop_Input_System.md) |

---

## OnionCat 적용 포인트

### 데모 빌드 목표 기준
- **최대 빌드 크기**: 50MB 이하 (itch.io 기본 허용 범위)
- **로딩 시간**: 30초 이내 (보통 인터넷 기준)
- **실행 중 메모리**: 200MB 이하 유지

### OnionCat 특화 설정
- 마우스 커서 게임 화면 내 고정 필수 → `CursorLockMode.Confined` 설정
- Onion(P2) 마우스 조준이 WebGL에서 작동하는지 반드시 테스트
- 로컬 2인 협력은 WebGL에서도 작동 (같은 키보드/마우스)

### 빠른 WebGL 테스트 워크플로우
1. 소규모 테스트 씬만 포함한 WebGL 빌드
2. 로컬 서버로 테스트: `python -m http.server 8080` 후 localhost:8080 접속
3. itch.io 업로드 전 로컬에서 메모리/오류 검증

---

## 참고 링크

- Unity WebGL Memory 공식 문서: https://docs.unity3d.com/Manual/webgl-memory.html
- Unity WebGL Performance 최적화: https://docs.unity3d.com/Manual/webgl-performance.html
- Unity WebGL 배포 가이드: https://docs.unity3d.com/Manual/webgl-deploying.html
- itch.io WebGL 업로드 방법: https://itch.io/docs/creators/html5
- WebGL 커스텀 템플릿: https://docs.unity3d.com/Manual/webgl-templates.html
