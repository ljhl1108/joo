# WFC (Wave Function Collapse) 절차적 방 내부 생성

리서치 날짜: 2026-10-22

## 개요

WFC(Wave Function Collapse)는 2016년 Maxim Gumin이 공개한 절차적 생성 알고리즘이다.
예시 패턴(타일맵 또는 이미지)에서 "어떤 타일이 어떤 타일 옆에 올 수 있는가"를 자동 학습한 뒤,
그 제약 조건을 만족하는 새 지도를 무한히 생성한다.

OnionCat은 이미 텍스트 지도(`RoomLayout`)와 조립식 덩어리(`RoomChunks`)로 방 내부를 다양화하고 있다.
WFC는 이보다 더 복잡한 내부 배치 — 장애물 섬·통로·함정 밀도를 지역마다 다르게 — 를 자동 생성할 때 유용하다.

---

## 알고리즘 작동 원리

### 핵심 단계

1. **예시 학습 (Constraint Extraction)**
   - 예시 타일맵을 순회하며 모든 인접 쌍을 기록
   - `tileset[A]`의 오른쪽에 올 수 있는 타일 집합 → adjacency rules
   
2. **초기화**
   - 출력 그리드의 모든 셀을 "모든 타일 가능" 상태로 시작 (엔트로피 = 최대)

3. **붕괴 (Collapse)**
   - 엔트로피(가능한 타일 수)가 가장 낮은 셀을 선택
   - 해당 셀의 타일을 가중치 기반으로 하나 무작위 선택 → 확정

4. **전파 (Propagate)**
   - 확정된 셀의 인접 셀에서 불가능한 타일을 제거
   - 그 결과로 엔트로피가 낮아진 셀도 다시 전파

5. **반복 → 완성 or 모순**
   - 모순(어떤 셀에 가능한 타일이 0개)이 생기면 백트래킹 또는 재시작

### 두 가지 변형

| 방식 | 설명 | OnionCat 적합도 |
|------|------|----------------|
| Overlapping | 픽셀 단위로 학습, 이미지 생성 | ❌ 타일맵 게임에 부적합 |
| Simple Tiled | 타일 단위 인접 규칙 명시 | ✅ 적합 |

---

## Unity 구현 방법

### A. 직접 구현 (단순 버전, 300줄 내외)

```csharp
// 타일 인접 규칙 (데이터 에셋으로 분리)
[CreateAssetMenu]
public class WFCTileset : ScriptableObject
{
    public TileBase[] tiles;
    // 각 타일[i]의 상/하/좌/우 방향에 올 수 있는 타일 인덱스 집합
    public List<int>[] compatibleUp;   // 크기 = tiles.Length
    public List<int>[] compatibleDown;
    public List<int>[] compatibleLeft;
    public List<int>[] compatibleRight;
    public float[] weights;            // 각 타일의 등장 빈도 가중치
}
```

```csharp
public class WFCGenerator : MonoBehaviour
{
    [SerializeField] WFCTileset tileset;
    [SerializeField] Tilemap outputTilemap;
    [SerializeField] Vector2Int gridSize;

    // 각 셀의 가능 타일 집합 (비트셋으로 관리하면 빠름)
    private HashSet<int>[,] wave;

    public bool Generate(int seed)
    {
        Random.InitState(seed);
        InitializeWave();
        
        while (true)
        {
            Vector2Int cell = FindLowestEntropyCell();
            if (cell == Vector2Int.one * -1) return true;  // 완성
            
            if (!Collapse(cell)) return false;  // 모순 → 실패
            if (!Propagate(cell)) return false;
        }
    }

    private Vector2Int FindLowestEntropyCell()
    {
        float minEntropy = float.MaxValue;
        Vector2Int result = Vector2Int.one * -1;
        
        for (int x = 0; x < gridSize.x; x++)
        for (int y = 0; y < gridSize.y; y++)
        {
            int count = wave[x, y].Count;
            if (count == 1) continue;  // 이미 확정
            if (count == 0) return Vector2Int.one * -1;  // 모순
            
            float entropy = count + Random.value * 0.01f;  // 동점 방지 노이즈
            if (entropy < minEntropy) { minEntropy = entropy; result = new Vector2Int(x, y); }
        }
        return result;
    }

    private bool Collapse(Vector2Int cell)
    {
        // 가중치 기반 무작위 선택
        float total = wave[cell.x, cell.y].Sum(i => tileset.weights[i]);
        float roll = Random.value * total;
        float cumulative = 0f;
        
        foreach (int tileIdx in wave[cell.x, cell.y])
        {
            cumulative += tileset.weights[tileIdx];
            if (roll <= cumulative)
            {
                wave[cell.x, cell.y] = new HashSet<int> { tileIdx };
                outputTilemap.SetTile(new Vector3Int(cell.x, cell.y), tileset.tiles[tileIdx]);
                return true;
            }
        }
        return false;
    }
}
```

### B. 기성 패키지 활용

- **mxgmn 원본 C# 포트**: [github.com/mxgmn/WaveFunctionCollapse](https://github.com/mxgmn/WaveFunctionCollapse)
  - Unity 직접 통합 가능, Simple Tiled 모드 있음
- **EasyWFC**: Asset Store에서 검색 가능, Unity Tilemap 통합 지원

### C. 인접 규칙 추출 자동화

예시 RoomLayout 텍스트 지도에서 인접 쌍을 자동 추출하는 에디터 도구:

```csharp
// OnionCat > Rooms > Extract WFC Rules from RoomLayouts
public class WFCRuleExtractor : EditorWindow
{
    void ExtractFromLayouts()
    {
        var layouts = Resources.LoadAll<RoomLayoutAsset>("Data/RoomLayouts");
        var rules = new Dictionary<(char, Direction), HashSet<char>>();
        
        foreach (var layout in layouts)
        {
            for (int y = 0; y < layout.Height; y++)
            for (int x = 0; x < layout.Width; x++)
            {
                char c = layout[x, y];
                if (x+1 < layout.Width) AddRule(rules, c, Direction.Right, layout[x+1, y]);
                if (y+1 < layout.Height) AddRule(rules, c, Direction.Up, layout[x, y+1]);
            }
        }
        // → WFCTileset 에셋으로 저장
    }
}
```

---

## OnionCat 적용 포인트

### 1. 현재 구조와의 통합

현재 OnionCat 방 내부 생성 파이프라인:
```
RoomLayout.asset (텍스트 지도)
  → Apply Room Layouts 메뉴 → Tilemap 씬에 적용
  + RoomChunks (? 자리에 3×3 덩어리 16종)
```

WFC를 삽입할 수 있는 위치:
```
RoomLayout.asset (외곽 틀: 벽·출구 위치 확정)
  → WFCGenerator가 내부 영역만 채움 (방 입장 시 런타임 실행)
  + 기존 RoomChunks는 제거 가능
```

**권장 방식**: WFC는 방 내부 빈 공간의 장애물 배치에만 적용. 외곽 벽·출구는 기존 텍스트 지도가 확정.

### 2. 런타임 성능

- 방 크기 최대 40×20 = 800 셀
- WFC 실행 시간: 보통 < 5ms (단순 타일셋 기준)
- 방 입장 시 생성하면 체감 딜레이 없음
- **실패 시**: 미리 만들어 둔 폴백 RoomChunk로 전환

### 3. 타일 정의 예시 (OnionCat용)

| 타일 문자 | 의미 | 인접 허용 |
|-----------|------|----------|
| `.` | 빈 바닥 | 모두 |
| `W` | 벽 | W, X |
| `X` | 벽 덩어리 | W, X |
| `O` | 장애물(단독) | `.`, `O` |
| `~` | 구덩이 | `~`, `.` |
| `?` | 비어있어야 할 공간 (적 스폰) | `.` 만 |

### 4. 구현 우선순위

1. **낮은 위험**: RoomChunks 자리에 WFC만 적용 (현재 16종 → 무한 변형)
2. **중간**: 방 내부 전체를 WFC로 생성 (텍스트 지도는 외곽 틀만)
3. **높음 (나중에)**: 방 형태(shape) 자체도 WFC로 생성

### 5. 주의사항

- **모순 발생률**: 복잡한 제약 조건일수록 높아짐. 간단한 규칙부터 시작
- **시드 재현**: `Random.InitState(roomSeed)` 필수 → 저장/불러오기 때 같은 방 복원
- **편집기 미리보기**: 에디터에서 바로 결과를 볼 수 있도록 EditorWindow 구성 권장

---

## 참고 링크

- [WFC 원본 GitHub (mxgmn)](https://github.com/mxgmn/WaveFunctionCollapse)
- [Maxim Gumin의 알고리즘 설명](https://github.com/mxgmn/WaveFunctionCollapse#algorithm)
- [Unity 타일맵 + WFC 예제 (GDC 2022 발표)](https://www.youtube.com/watch?v=... - "Wave Function Collapse Unity tilemap")
- [Martin Donald의 WFC 영상 해설](https://www.youtube.com/watch?v=2SuvO4Gi7uY) — 알고리즘 시각화 설명
- [Oskar Stålberg의 Bad North 활용 사례](https://www.youtube.com/watch?v=0bcZb-SsnrA)
