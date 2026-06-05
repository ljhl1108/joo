# 세이브/로드 시스템 (Save & Load System)

## 개요

로그라이크 게임에서 저장 시스템은 두 층위로 나뉜다:
1. **런 내 데이터**: 현재 진행 중인 런의 상태 (원래는 저장 안 함 — 퍼마데스 원칙)
2. **런 간 영구 데이터**: 최고 기록, 잠금 해제 항목, 게임 설정

OnionCat 같은 로그라이크는 주로 "런 간 영구 데이터"만 저장한다. PlayerPrefs는 단순 설정에, JSON 파일 저장은 복잡한 메타 진행도에 사용한다.

---

## Unity 구현 방법

### 방식 비교

| 방식 | 적합한 데이터 | 장점 | 단점 |
|------|-------------|------|------|
| `PlayerPrefs` | 설정, 고득점, 간단한 플래그 | 코드 간단, 즉시 사용 | 보안 취약, 복잡한 구조 불가 |
| JSON + File | 메타 진행도, 업적, 런 통계 | 구조화, 확장성 | 구현 복잡, 파일 관리 필요 |
| Binary (BinaryFormatter) | (사용 비추천) | 빠름 | Unity 2022+에서 deprecated |

**OnionCat 권장**: 설정은 PlayerPrefs, 메타 진행도는 JSON 파일

---

### 구현 1: PlayerPrefs — 설정 저장

```csharp
public static class SettingsData
{
    private const string KEY_MASTER_VOLUME = "MasterVolume";
    private const string KEY_SFX_VOLUME = "SFXVolume";
    private const string KEY_FULLSCREEN = "Fullscreen";

    public static void SaveSettings(float masterVol, float sfxVol, bool fullscreen)
    {
        PlayerPrefs.SetFloat(KEY_MASTER_VOLUME, masterVol);
        PlayerPrefs.SetFloat(KEY_SFX_VOLUME, sfxVol);
        PlayerPrefs.SetInt(KEY_FULLSCREEN, fullscreen ? 1 : 0);
        PlayerPrefs.Save(); // 즉시 디스크에 기록
    }

    public static float LoadMasterVolume() =>
        PlayerPrefs.GetFloat(KEY_MASTER_VOLUME, 1.0f); // 기본값 1.0

    public static bool LoadFullscreen() =>
        PlayerPrefs.GetInt(KEY_FULLSCREEN, 1) == 1;
}
```

---

### 구현 2: JSON 저장 — 메타 진행도

#### 데이터 구조 정의

```csharp
[System.Serializable]
public class MetaProgressData
{
    public int totalRuns;           // 총 런 횟수
    public int totalKills;          // 총 처치 수
    public int bestFloorReached;    // 최고 도달 층
    public float bestRunTime;       // 가장 빠른 클리어 시간
    public List<string> unlockedItems;   // 잠금 해제된 아이템 ID
    public List<string> completedAchievements; // 달성한 업적

    // 기본값 초기화
    public MetaProgressData()
    {
        totalRuns = 0;
        totalKills = 0;
        bestFloorReached = 0;
        bestRunTime = float.MaxValue;
        unlockedItems = new List<string>();
        completedAchievements = new List<string>();
    }
}
```

#### 저장/불러오기 매니저

```csharp
using System.IO;
using UnityEngine;

public class SaveManager : MonoBehaviour
{
    public static SaveManager Instance { get; private set; }

    private string SavePath => Path.Combine(Application.persistentDataPath, "meta_progress.json");

    private MetaProgressData _data;
    public MetaProgressData Data => _data;

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);

        Load(); // 게임 시작 시 즉시 불러오기
    }

    public void Save()
    {
        string json = JsonUtility.ToJson(_data, prettyPrint: true);
        File.WriteAllText(SavePath, json);
        Debug.Log($"저장 완료: {SavePath}");
    }

    private void Load()
    {
        if (!File.Exists(SavePath))
        {
            _data = new MetaProgressData(); // 첫 실행: 기본값 생성
            return;
        }

        string json = File.ReadAllText(SavePath);
        _data = JsonUtility.FromJson<MetaProgressData>(json);

        // null 방어 (파일이 손상됐을 경우)
        if (_data == null)
            _data = new MetaProgressData();
    }

    public void ResetAllData()
    {
        _data = new MetaProgressData();
        Save();
    }
}
```

#### 런 종료 시 데이터 업데이트

```csharp
public class RunResultManager : MonoBehaviour
{
    // 런 종료 시 호출
    public void OnRunEnded(RunResult result)
    {
        var meta = SaveManager.Instance.Data;

        meta.totalRuns++;
        meta.totalKills += result.killCount;

        if (result.floorReached > meta.bestFloorReached)
            meta.bestFloorReached = result.floorReached;

        if (result.isCleared && result.clearTime < meta.bestRunTime)
            meta.bestRunTime = result.clearTime;

        SaveManager.Instance.Save();
    }
}

[System.Serializable]
public class RunResult
{
    public int killCount;
    public int floorReached;
    public bool isCleared;
    public float clearTime;
}
```

---

### 구현 3: Application.persistentDataPath 경로

```csharp
// 플랫폼별 저장 경로 (Unity 자동 결정)
// Windows: C:/Users/[User]/AppData/LocalLow/[Company]/[Product]/
// Mac:     ~/Library/Application Support/[Company]/[Product]/
// Android: /data/data/[package]/files/
// iOS:     /var/mobile/Containers/Data/Application/[UUID]/Documents/

Debug.Log(Application.persistentDataPath); // 경로 확인용
```

---

### 구현 4: 암호화 (간단한 보안)

플레이어가 JSON을 직접 수정하는 것을 막으려면:

```csharp
// 단순 Base64 인코딩 (완벽한 보안은 아님 — 치팅 방지 수준)
public static string Encode(string json) =>
    System.Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes(json));

public static string Decode(string encoded) =>
    System.Text.Encoding.UTF8.GetString(System.Convert.FromBase64String(encoded));

// Save 시: File.WriteAllText(SavePath, Encode(json));
// Load 시: string json = Decode(File.ReadAllText(SavePath));
```

---

## OnionCat 적용 포인트

### 저장할 데이터 목록 (OnionCat 전용)
```
PlayerPrefs (설정):
- MasterVolume, SFXVolume, BGMVolume
- Fullscreen, Resolution
- Player1InputScheme, Player2InputScheme

JSON MetaProgressData:
- totalRuns               // "몇 번 죽었나"
- totalKills              // 업적 용
- bestFloorReached        // 최고 기록
- unlockedItemIds         // 런 성공 시 새 아이템 해금
- completedAchievements   // 업적 시스템 연동
- catSkinUnlocked         // 코스메틱 언락 (나중에)
```

### 저장 타이밍
```
저장 호출 시점:
1. 런 종료 (성공 or 게임 오버) → 런 결과 반영
2. 업적 달성 즉시 → 유실 방지
3. 설정 변경 즉시 → PlayerPrefs.Save()
4. 게임 종료 전 OnApplicationQuit() → 최종 저장

저장 호출 금지 시점:
- 매 프레임 Update() — 성능 저하
- 전투 중 — 버벅임 유발 (파일 I/O는 느림)
```

### DontDestroyOnLoad 활용
```csharp
// SaveManager는 씬 전환에도 유지
// GameManager, AudioManager 같은 글로벌 매니저와 함께
// "Persistent" 씬에 배치하거나 Awake에서 DontDestroyOnLoad 처리
```

---

## 참고 링크

- Unity PlayerPrefs 공식 문서: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Unity Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- JsonUtility 공식 문서: https://docs.unity3d.com/ScriptReference/JsonUtility.html
- Unity 저장 시스템 튜토리얼 (Brackeys): https://www.youtube.com/watch?v=XOjd_qU2Ido
- JSON 저장 시스템 심화: https://gamedevbeginner.com/how-to-save-and-load-a-game-in-unity/
