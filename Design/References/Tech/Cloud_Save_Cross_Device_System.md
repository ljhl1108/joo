# 클라우드 저장 / 크로스 디바이스 시스템

리서치 날짜: 2026-10-15

## 개요
로컬 파일 저장과 달리, 게임 진행 데이터를 클라우드 서버에 동기화해 다른 기기에서도 이어할 수 있게 하는 시스템. OnionCat은 현재 로컬 JSON 저장(`RunSave`)이 있지만, Steam 출시 시 다른 PC나 Steam Deck에서 이어하기를 지원하려면 클라우드 저장이 필요하다.

---

## Unity 구현 방법

### 옵션 1: Steam Cloud (Steam 출시 예정이라면 가장 간단)

Steamworks 대시보드에서 활성화만 하면 코드 변경 없이 동작:

**Steamworks 대시보드 설정**:
1. 앱 설정 → **Cloud** → "Enable Steam Cloud" 체크
2. 동기화할 파일 경로 패턴 등록:
   ```
   Windows: %USERPROFILE%\AppData\LocalLow\[CompanyName]\OnionCat\*.json
   Mac:      ~/Library/Application Support/[CompanyName]/OnionCat/*.json
   Linux:    ~/.config/unity3d/[CompanyName]/OnionCat/*.json
   ```
3. 용량 한도 설정 (대부분 100MB면 충분)

**필수 전제 조건**:
```csharp
// 저장 경로를 Application.persistentDataPath 기준으로 통일해야 함
// ← Steam Cloud는 이 경로를 자동으로 감시하고 동기화

string savePath = Path.Combine(Application.persistentDataPath, "run_save.json");
File.WriteAllText(savePath, JsonUtility.ToJson(saveData));
// 게임 종료 시 Steam이 자동으로 클라우드에 업로드
// 게임 시작 시 Steam이 자동으로 로컬에 다운로드
```

**장점**: 코드 변경 거의 없음, 완전 자동  
**단점**: Steam 전용 (itchio, 단독 exe에서는 동작 안 함)

---

### 옵션 2: Unity Gaming Services (UGS) Cloud Save

플랫폼 독립적, 계정 기반. 인터넷 연결 + 계정 필요:

```csharp
using Unity.Services.CloudSave;
using Unity.Services.Authentication;
using Unity.Services.Core;

// 1. 초기화 (게임 시작 시 한 번)
async Task InitializeUGS() {
    await UnityServices.InitializeAsync();
    if (!AuthenticationService.Instance.IsSignedIn)
        await AuthenticationService.Instance.SignInAnonymouslyAsync();
}

// 2. 클라우드에 저장
async Task SaveToCloud(RunSaveData runData, MetaData meta) {
    var data = new Dictionary<string, object> {
        ["run_save"]  = JsonUtility.ToJson(runData),
        ["meta"]      = JsonUtility.ToJson(meta),
        ["timestamp"] = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
    };
    await CloudSaveService.Instance.Data.Player.SaveAsync(data);
}

// 3. 클라우드에서 불러오기
async Task<RunSaveData> LoadFromCloud() {
    var keys = new HashSet<string> { "run_save", "timestamp" };
    var result = await CloudSaveService.Instance.Data.Player.LoadAsync(keys);
    if (!result.TryGetValue("run_save", out var val)) return null;
    return JsonUtility.FromJson<RunSaveData>(val.Value.GetAsString());
}
```

**장점**: 멀티플랫폼, itchio·단독 빌드에도 사용 가능  
**단점**: 인터넷 필수, 익명 계정이라 기기 분실 시 데이터 손실 위험

---

### 충돌(Conflict) 해결 — 양쪽이 모두 최신인 경우

```csharp
async Task SyncSave() {
    var localSave = LoadLocal();
    var cloudTimestamp = await GetCloudTimestamp();
    
    if (localSave == null) {
        // 로컬 없음 → 클라우드에서 다운로드
        ApplySave(await LoadFromCloud());
        return;
    }
    
    if (cloudTimestamp > localSave.savedAt) {
        // 클라우드가 더 최신 → UI로 선택 물어보기
        ShowConflictUI(localSave, await LoadFromCloud());
    } else {
        // 로컬이 더 최신 → 클라우드에 업로드
        await SaveToCloud(localSave);
    }
}
```

---

### 저장 데이터에 버전 필드 추가 (필수)

패치 후 구버전 저장 데이터 호환성 문제 방지:

```csharp
[Serializable]
public class RunSaveData {
    public int saveVersion = 1;   // ← 클라우드 동기화 시 필수
    public long savedAt;          // Unix timestamp
    // ... 나머지 런 데이터
}

// 불러올 때 버전 체크
public static RunSaveData Load(string json) {
    var data = JsonUtility.FromJson<RunSaveData>(json);
    if (data.saveVersion < CURRENT_VERSION)
        data = MigrateData(data);
    return data;
}
```

---

## OnionCat 적용 포인트

### 권장 접근: Steam Cloud 자동 동기화

OnionCat은 Steam 출시 예정이므로 추가 코드 없이 가능:

1. `Application.persistentDataPath` 경로 확인:
   ```csharp
   Debug.Log(Application.persistentDataPath);
   // Windows: C:/Users/feedb/AppData/LocalLow/[Company]/OnionCat
   ```
2. Steamworks 대시보드에서 해당 경로 패턴 등록
3. 테스트: Steam 클라이언트 열고 게임 저장 → 다른 PC에서 확인

### OnionCat 저장 파일 분류

| 파일 | 클라우드 동기화 | 이유 |
|---|---|---|
| `run_save.json` (런 중간 저장) | **필수** | Steam Deck에서 이어하기 |
| `meta.json` (향후 메타 성장) | **필수** | 영구 언락 유지 |
| `settings.json` (음량·해상도) | **선택** | 기기마다 다를 수 있음 |
| `records.json` (최고 기록) | **선택** | |

### 2인 플레이에서 저장 주인

- 고양이 플레이어(P1, 게임패드)가 게임을 실행한 사람 → 해당 Steam 계정 기준으로 저장
- 양파 플레이어(P2, 마우스·키보드)의 진행은 P1 계정에 저장됨
- 역할 바꿔서 플레이하면 데이터가 P1 계정에만 쌓임 → UI에 "게임 저장은 P1 계정 기준" 안내 권장

### 주의 사항

- **런 저장은 버전에 민감**: 패치 후 구버전 저장 데이터를 읽으면 버그 가능 → `saveVersion` 필드 + 마이그레이션 함수 준비
- **오프라인 대응**: Steam 오프라인 모드에서는 로컬 저장만 사용, 재연결 시 동기화
- **저장 용량**: `run_save.json`은 런 상태(장비·패시브·씨앗 등) 기준 수십 KB — Steam의 기본 1GB 한도에 여유 있음

## 참고 링크
- [Steam Cloud 공식 문서](https://partner.steamgames.com/doc/features/cloud)
- [Application.persistentDataPath Unity Docs](https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html)
- [Unity Gaming Services Cloud Save 공식](https://docs.unity.com/ugs/en-us/manual/cloud-save/manual)
- [Save_Load_System.md (로컬 저장 구현)](./Save_Load_System.md)
- [Save_Data_Migration_System.md (버전 마이그레이션)](./Save_Data_Migration_System.md)
