# Enemy Encounter Choreography Design

리서치 날짜: 2026-10-13

## 개요

**"어떤 적을 몇 마리, 어느 위치에 배치해서 어떤 순서로 싸우게 만드는가"** — 이 설계를 인카운터 코레오그래피(Encounter Choreography)라고 부른다. 방의 모양과 적의 종류가 있어도, 실제로 재미있는 전투가 되려면 적 구성(Composition)·초기 배치(Placement)·등장 순서(Wave)가 맞아야 한다. OnionCat처럼 방을 클리어하는 구조에서는 방 1개가 짧은 '씬(Scene)'이고, 코레오그래피가 그 씬의 연출 대본에 해당한다.

---

## 핵심 개념

### 1. 역할 구성 (Role Composition)

재미있는 전투는 서로 다른 역할의 적이 상호 강화(Synergy)할 때 생긴다.

| 역할 | 특징 | OnionCat 예시 |
|------|------|--------------|
| **압박(Pressure)** | 플레이어에게 접근·공간 잠식 | 슬라임 (직진 돌진) |
| **원거리 견제(Poke)** | 거리 유지하며 투사체 발사 | 원거리 슬라임 |
| **분열/증식** | 죽어도 수가 늘어남 | 분열 슬라임 |
| **방어 앵커** | 특정 위치에 서서 뚫기 어려움 | 방패 근위병 |

**황금 조합 원칙**: 압박 + 원거리 견제를 함께 넣으면, 플레이어는 원거리를 먼저 죽이러 가면 압박이 따라오고, 압박을 막으면 원거리가 때리는 딜레마에 놓인다. 적이 서로 커버(Cover)해주는 것이 핵심.

### 2. 공간 제어 (Space Control)

- **압박 vs. 원거리 분리 배치**: 원거리 적을 방 반대편에 두면 플레이어가 자연스럽게 가운데서 분리 작업을 해야 함
- **방패병 앵커**: 방패병 1~2명을 출구 쪽에 배치하면 "방패병을 뒤에서 처리하면서 원거리도 막아야"하는 입체적 공간 싸움 발생
- **구덩이 압박**: 구덩이 옆에 돌진형 적을 배치하면 회피 공간이 줄어들어 자연스럽게 긴장감 상승

### 3. 위협 레이어링 (Threat Layering)

동시에 여러 위협이 있되, 처리 순서가 명확해야 한다.

```
위협 우선순위 (플레이어가 직관적으로 느껴야 함):
  즉각적 위협 > 지속 위협 > 잠재 위협
  (돌진 직전 슬라임) > (탄 쏘는 원거리) > (분열 중인 분열 슬라임)
```

위협이 동시에 여러 층이면 "지금 뭘 해야 해?" 가 불명확해져 혼란스럽다. 초반 방은 위협 층을 1~2개로 제한하고, 후반으로 갈수록 층을 늘린다.

### 4. 등장 연출 (Wave Timing)

- **즉시 등장**: 방에 들어서자마자 모든 적이 보이고 활성화 — 간단하고 명확
- **등장 지연(Spawn Wave)**: 첫 적 집단 일부 처치 후 증원 등장 → 공간이 잠깐 숨통이 트였다가 다시 막히는 리듬감
- **OnionCat 권장**: 즉시 등장 기본 + 분열 슬라임 죽으면 새끼 등장처럼 자연스러운 분기만 사용. 별도 웨이브 타이머는 복잡도 대비 혼란 유발.

### 5. 전투 호흡 (Combat Pacing)

방 1개의 전투 시간을 **30초~90초**로 설계한다.
- 30초 미만: 전투가 없는 것처럼 느낌
- 90초 초과: 피로 누적, 특히 co-op에서 집중력 소산

시간 = 총 HP / 평균 DPS로 역산 → 적 수·체력을 조절해 목표 시간 맞춤.

---

## Unity 구현 패턴

### 방별 인카운터 설정 (ScriptableObject 기반)

```csharp
// RoomEncounter.cs
[CreateAssetMenu(fileName = "Encounter_", menuName = "OnionCat/Room Encounter")]
public class RoomEncounter : ScriptableObject
{
    [System.Serializable]
    public struct SpawnEntry
    {
        public EnemyBase prefab;
        public Vector2 spawnOffset;   // 방 중심 기준 오프셋
        public float spawnDelay;      // 등장 지연 (초)
    }
    
    public SpawnEntry[] initialWave;   // 첫 등장
    public SpawnEntry[] reinforcement; // 강화 (초기 전멸 후 등장, 옵션)
    [Range(0, 1)] public float eliteChance; // 엘리트 변환 확률
}
```

### 적 배치 시각화 (Gizmo)

```csharp
// RoomManager.cs - 에디터에서 배치 위치 미리 보기
private void OnDrawGizmos()
{
    if (encounter == null) return;
    foreach (var entry in encounter.initialWave)
    {
        Gizmos.color = entry.spawnDelay > 0 ? Color.yellow : Color.red;
        Gizmos.DrawWireSphere(transform.position + (Vector3)entry.spawnOffset, 0.3f);
    }
}
```

### 공간 기반 위협도 측정 (디버그 헬퍼)

```csharp
// 방 클리어 시간을 로그로 기록해 목표 시간 초과 여부 파악
private float combatStartTime;
void OnRoomActivated() => combatStartTime = Time.time;
void OnRoomCleared()
{
    float elapsed = Time.time - combatStartTime;
    Debug.Log($"[Encounter] {gameObject.scene.name} cleared in {elapsed:F1}s");
}
```

---

## OnionCat 적용 포인트

### 현재 적 조합 분석

현재 5종 적을 역할로 분류하면:
- 슬라임: 압박 ○, 원거리 ×, 수비 ×
- 원거리 슬라임: 압박 ×, 원거리 ○
- 분열 슬라임: 증식 ○ (처치 후 리스크 남음)
- 방패 근위병: 수비 ○, 압박 △
- 보스 영웅 기사: 특수 (1인 대형 위협)

**권장 조합 레시피**:
| 난이도 tier | 조합 예시 | 이유 |
|------------|----------|------|
| 쉬움 | 슬라임 3마리 | 단일 위협, 방향만 신경 쓰면 됨 |
| 보통 | 슬라임 2 + 원거리 1 | 압박/원거리 기본 딜레마 |
| 어려움 | 방패 1 + 원거리 2 + 분열 1 | 뚫기 어려운 수비 + 거리 견제 + 분열 리스크 |
| 엘리트 | 위 조합에 체력 2배·크기 1.2배 | 추가 설계 없이 자동 강화 |

### 걷어차기와 구덩이 시너지 설계

OnionCat은 걷어차기(launch)로 적을 구덩이에 밀어 넣을 수 있다 → 이 기술이 활용되도록 유도하는 배치:
- 구덩이 근처에 **원거리 슬라임** 배치 → "원거리를 구덩이로 걷어차면 빠르게 처리"라는 직관 강화
- 방패 근위병을 구덩이 쪽으로 등 돌려서 배치 → 뒤에서 걷어차기 유도
- 하지만 너무 많으면 "걷어차기만 쓰면 되네"가 되므로 구덩이 없는 방도 절반은 유지

### 협동 콤보 유도 설계

- 대형 적 1마리를 방 중앙에 + 소형 여럿을 주변에 → 대형을 고양이가 공략하는 동안 양파가 소형 정리 → 자연스럽게 교차 타격 발생
- 분열 슬라임을 멀리 배치: 고양이가 돌진 막고 양파가 뒤쪽 새끼 처리 → 역할 분담 → 콤보 확률 상승

### 방 배치에서 직접 적용

현재 방 글자 지도 (1~4·B) 규칙에서:
```
# 좋은 조합 예시 (어려운 방)
## 십자형 방
  [원거리2]
[슬라임1]   [방패4]
  [분열3]
```
원거리를 꼭대기에, 방패를 오른쪽 출구 쪽에 두면 플레이어는 왼쪽에서 시작해 방패를 뚫고 나가야 하는데, 위에서 원거리가 위협하고 분열이 폭발 뒤에 새끼를 만들어낸다.

---

## 참고 링크

- Mark Brown (GMTK) "How to Design an Encounter" – https://www.youtube.com/watch?v=q6-9yq4NfK0
- Hades dev commentary on enemy combination design – https://www.gdcvault.com/play/1026352
- "Encounter Design Fundamentals" by Game Designer's Toolkit – https://gdtoolkit.com/encounter-design
- Diablo III "Rift Composition" analysis (fan wiki) – https://diablo.fandom.com/wiki/Greater_Rift
