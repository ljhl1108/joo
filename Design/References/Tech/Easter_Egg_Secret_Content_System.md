# 이스터에그 & 숨겨진 콘텐츠 시스템 (Easter Egg & Secret Content System)

리서치 날짜: 2026-11-08

## 개요

이스터에그와 숨겨진 콘텐츠는 게임에 "발견의 경험"을 추가한다. 로그라이크에서 특히 중요한 이유는 반복 플레이 중 새로운 발견이 계속 나와야 플레이어가 계속 돌아오기 때문.

**OnionCat 맥락**: 이미 `MetaProgress` (장기 진행 데이터)와 `meta.json`이 있어 비밀 해금 조건을 저장하기 좋은 구조가 갖춰져 있음. 온실(`GreenhouseScreen`)이 이미 해금 시스템을 갖고 있으므로 연장선에서 구현 가능.

---

## 로그라이크의 비밀 콘텐츠 유형

| 유형 | 예시 게임 | 설명 |
|------|----------|------|
| 숨겨진 방 | Binding of Isaac, Hades | 조건 충족 시 특수 방 출현 |
| 비밀 아이템 | Enter the Gungeon | 특정 행동 조합으로 출현 |
| 개발자 메모/로어 | Hades, Inscryption | 텍스트 속 숨겨진 이야기 |
| 도전 방 | Dead Cells | 특수 방에서 고난이도 조건 클리어 |
| 숨겨진 엔딩 조건 | Hades 엔딩 플래그 | 판마다 대화 누적 → 진짜 엔딩 해금 |

---

## Unity 구현 방법

### 1. 비밀 해금 조건 시스템

`ScriptableObject`로 비밀 조건을 데이터화:

```csharp
[CreateAssetMenu]
public class SecretCondition : ScriptableObject {
    public string secretId;          // "secret_dev_room"
    public SecretType type;          // HiddenRoom, SecretItem, Lore 등
    [TextArea] public string description; // 개발자용 설명
}

// 판단 로직: MetaProgress에 추가
public static bool IsUnlocked(string secretId)
    => MetaProgress.data.unlockedSecrets.Contains(secretId);

public static void Unlock(string secretId) {
    if (!IsUnlocked(secretId)) {
        MetaProgress.data.unlockedSecrets.Add(secretId);
        MetaProgress.Save();
        // 선택: 해금 연출
        Toast.Show($"비밀을 발견했습니다!");
    }
}
```

### 2. 숨겨진 방 트리거

`DungeonManager`의 방 생성 시 조건 확인:

```csharp
// 조건: 엘리트 방을 연속 3개 클리어
// DungeonManager에서 추적
int _consecutiveElites = 0;

void OnRoomCleared(Room room) {
    if (room.type == RoomType.Elite) {
        _consecutiveElites++;
        if (_consecutiveElites >= 3 && !SecretCondition.IsUnlocked("secret_garden"))
            SpawnSecretRoom(); // 다음 갈림길에 숨겨진 방 추가
    } else {
        _consecutiveElites = 0;
    }
}
```

### 3. 아이템 설명 속 로어

장비 `GearItem`의 설명(`description`)에 개발자가 짧은 이야기를 숨김. 별도 구현 없이 텍스트만 추가. 플레이어가 아이템을 조합하다 발견하는 방식.

```
[기본 발톱]
설명: "예전에 고양이가 직접 갈았던 흔적이 있다.
       손잡이 안쪽에 작은 글씨: '새벽에게, 돌아와.'"
```

### 4. 조건부 대화 트리거

`StoryLines.cs`에 비밀 조건 체크:

```csharp
// 말하는 책이 특정 아이템 조합을 감지해 특별 대사 출력
if (RunData.HasItem("ancient_claw") && RunData.HasItem("moon_spellbook"))
    Dialogue.Play(StoryLines.SecretCombinationDialogue);
```

---

## OnionCat 적용 포인트

### 아이디어 1: 숨겨진 개발자 방
**조건**: 한 판에서 걷어차기 없이(GameFeatures.Kick=false인 현재 상태) 보스를 클리어 → 다음 보스 클리어 시 개발자 메모가 있는 특수 방 출현.
**내용**: 개발자가 "걷어차기를 뺀 이유"를 고양이 시점의 대사로 설명하는 유머러스한 방.

### 아이디어 2: 비밀 작물 힌트 발견
**조건**: 햇살 세트 8단계를 처음 달성 → "오래된 씨앗 봉투" 아이템이 보물방에서 가끔 출현. 해독하면 미구현 작물(예: 블루 머슈름 뒤의 4번째 작물)의 존재를 암시하는 짧은 텍스트.
**구현**: `RewardTable`의 특수 조건 풀에 조건부로 추가.

### 아이디어 3: 그리모(낡은 책)의 숨겨진 메모
**조건**: `MetaProgress.WitchFreed`(마녀 해방) 이후, 특정 아이템 조합을 맞추면 그리모가 과거 이야기를 추가로 말해줌.
**구현**: `Dialogue.Play` 호출 조건에 아이템 보유 여부 + MetaProgress 플래그 추가.

### 4: meta.json 보호
비밀 해금 데이터도 `meta.json`에 저장. CLAUDE.md 지침대로 테스트 전 백업 필수 — 비밀 발견 여부가 사람의 실제 플레이 기록이므로 덮어쓰면 경험이 망가짐.

---

## 참고 링크

- Binding of Isaac 비밀 방 메커니즘: https://bindingofisaacrebirth.fandom.com/wiki/Secret_Room
- Hades 이스터에그 목록: https://hades.fandom.com/wiki/Easter_Eggs
- GDC 토크 "Secrets in Roguelikes" (일반 비밀 설계): https://www.gdcvault.com/
- Unity ScriptableObject 패턴: https://docs.unity3d.com/Manual/class-ScriptableObject.html
