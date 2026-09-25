# Save Data Migration and Version Compatibility System

리서치 날짜: 2026-09-25

## 개요

게임 업데이트 시 저장 데이터 구조가 바뀌면 기존 플레이어의 세이브가 깨질 수 있다.
버전 번호를 포함한 저장 포맷과 마이그레이션 함수로 이를 방지하는 시스템.

**OnionCat 관련성**: 출시 후 패치에서 새 스탯·런 데이터 필드를 추가할 때 기존 세이브를 안전하게 유지해야 한다.
초기에 버전 관리를 갖추면 나중에 데이터 손실 버그를 피할 수 있다.

## 문제 상황

```
v1.0: { "runs": 5, "bestTime": 120.5 }
v1.1: runs 필드 → rogue_runs 이름 변경, highestFloor 필드 추가
```
→ v1.1에서 v1.0 세이브 로드 시: `rogue_runs = 0`으로 초기화되거나 파싱 오류 발생.

## Unity 구현 방법

### 1. 저장 데이터에 버전 번호 포함

```csharp
[Serializable]
public class PersistentSaveData {
    public int saveVersion = CURRENT_VERSION;
    public const int CURRENT_VERSION = 1;

    // 영구 데이터
    public int totalRuns;
    public float bestClearTime;
    public List<string> unlockedItems = new();
}
```

### 2. 저장 / 로드 베이스 (JSON)

```csharp
using System.IO;
using UnityEngine;

public static class SaveSystem {
    static string SavePath => Path.Combine(Application.persistentDataPath, "save.json");

    public static void Save(PersistentSaveData data) {
        data.saveVersion = PersistentSaveData.CURRENT_VERSION;
        File.WriteAllText(SavePath, JsonUtility.ToJson(data, prettyPrint: true));
    }

    public static PersistentSaveData Load() {
        if (!File.Exists(SavePath))
            return new PersistentSaveData(); // 첫 실행

        try {
            string json = File.ReadAllText(SavePath);
            var data = JsonUtility.FromJson<PersistentSaveData>(json);
            return Migrate(data); // ← 버전 마이그레이션 적용
        } catch (Exception e) {
            Debug.LogWarning($"[SaveSystem] Load failed: {e.Message} — starting fresh");
            BackupCorruptedSave();
            return new PersistentSaveData();
        }
    }

    static void BackupCorruptedSave() {
        string backup = SavePath + ".corrupted_" + System.DateTime.Now.Ticks;
        if (File.Exists(SavePath)) File.Move(SavePath, backup);
    }
}
```

### 3. 마이그레이션 체인

```csharp
static PersistentSaveData Migrate(PersistentSaveData data) {
    // 버전 0 → 1
    if (data.saveVersion < 1) {
        // 예: v0에서 totalRuns 필드가 없었다면 기본값 유지 (이미 0)
        // v0에서 필드 이름이 달랐다면 여기서 변환
        data.saveVersion = 1;
    }

    // 버전 1 → 2 (미래)
    // if (data.saveVersion < 2) { ... data.saveVersion = 2; }

    return data;
}
```

순서대로 올라가는 체인 구조 → 어느 버전에서도 현재 버전까지 자동으로 마이그레이션됨.

### 4. PlayerPrefs 기반 설정 버전 관리

런 영구 데이터(JSON)와 별개로, 설정(볼륨/해상도)은 PlayerPrefs를 쓸 경우:

```csharp
public static class SettingsMigrator {
    const string VERSION_KEY = "settings_version";
    const int CURRENT = 1;

    public static void MigrateIfNeeded() {
        int ver = PlayerPrefs.GetInt(VERSION_KEY, 0);
        if (ver < 1) {
            // v0: 볼륨이 0~1 float이었음 → v1: 0~100 int로 변경
            float oldVol = PlayerPrefs.GetFloat("MasterVolume", 0.7f);
            PlayerPrefs.SetInt("MasterVolumeInt", Mathf.RoundToInt(oldVol * 100));
            PlayerPrefs.DeleteKey("MasterVolume");
            PlayerPrefs.SetInt(VERSION_KEY, 1);
        }
        PlayerPrefs.Save();
    }
}
```

### 5. 안전 규칙 (데이터 호환성)

| 안전 | 위험 |
|------|------|
| 새 필드 추가 (기본값 설정) | 필드 삭제 |
| enum에 값 추가 (끝에) | 필드 이름 변경 |
| 리스트 원소 타입 유지 | enum 순서 변경 |
| 버전 체크 후 마이그레이션 | 버전 없이 구조 변경 |

**필드 이름 변경이 불가피할 때**: 새 이름의 필드를 추가하고, 마이그레이션에서 `newField = oldField`로 복사, 이후 oldField는 무시(삭제 안 함 — JsonUtility는 없는 필드 무시).

### 6. 개발 중 마이그레이션 테스트

```csharp
// Editor 전용 테스트 헬퍼
#if UNITY_EDITOR
[MenuItem("Debug/Save/Reset Save Data")]
static void ResetSave() {
    if (File.Exists(SaveSystem.SavePath)) File.Delete(SaveSystem.SavePath);
    Debug.Log("[Dev] Save data deleted");
}

[MenuItem("Debug/Save/Simulate v0 Save")]
static void SimulateOldSave() {
    // 마이그레이션 경로 테스트용 구버전 JSON 작성
    var oldJson = "{\"saveVersion\":0,\"totalRuns\":3}";
    File.WriteAllText(SaveSystem.SavePath, oldJson);
    Debug.Log("[Dev] Wrote simulated v0 save — press Play to test migration");
}
#endif
```

## OnionCat 적용 포인트

### 현재 저장 대상 (GameManager.RunData 기반)

OnionCat에서 영구 저장이 필요한 데이터:
- 총 런 횟수, 최고 클리어 시간
- 잠금 해제된 아이템/캐릭터 스킨 목록
- 총 처치 수, 업적 진행도

### 권장 저장 구조 (초기 설계)

```csharp
[Serializable]
public class PersistentSaveData {
    public int saveVersion = CURRENT_VERSION;
    public const int CURRENT_VERSION = 1;

    // 런 통계
    public int totalRuns;
    public int totalKills;
    public float bestClearTime = float.MaxValue;
    public int highestFloorReached;

    // 업적 / 잠금 해제
    public List<string> unlockedItems = new();
    public List<string> completedAchievements = new();
}
```

### 주의: RunData vs PersistentSaveData 구분

`GameManager.Instance.Run`(RunData)은 **현재 런의 임시 데이터** — 저장 불필요(런 종료 시 폐기).
PersistentSaveData는 **런 간 유지 데이터** — 런 종료 시 통계 합산 후 저장.

```csharp
// 런 종료 시 영구 저장 업데이트
void OnRunEnd(RunData run) {
    var save = SaveSystem.Load();
    save.totalRuns++;
    save.totalKills += run.TotalKills;
    if (run.ClearTime < save.bestClearTime) save.bestClearTime = run.ClearTime;
    SaveSystem.Save(save);
}
```

## 참고 링크

- Unity 공식 Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- JsonUtility 문서: https://docs.unity3d.com/ScriptReference/JsonUtility.html
- 세이브 시스템 심화 (Brackeys): https://www.youtube.com/watch?v=XOjd_qU2Ido
- 마이그레이션 패턴: https://www.gamedeveloper.com/design/the-art-of-game-save-systems
