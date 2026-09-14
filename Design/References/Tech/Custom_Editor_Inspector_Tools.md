# Unity 커스텀 에디터 & Inspector 도구

리서치 날짜: 2026-09-14

## 개요

Unity 에디터를 확장하여 Inspector·씬 뷰에 전용 UI와 도구를 추가하는 기법. 레벨 디자인, 적 배치, 방 설정 등 반복 작업을 가속하며 팀원(또는 미래의 자신)이 실수 없이 작업하도록 돕는다. 초보 개발자도 빌드 전에 에디터에서 바로 검증할 수 있어 OnionCat 같은 소규모 로그라이크에서 생산성을 크게 높인다.

---

## Unity 구현 방법

### 1. `[CustomEditor]` — Inspector 커스터마이징

```csharp
using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(RoomConfig))]
public class RoomConfigEditor : Editor
{
    public override void OnInspectorGUI()
    {
        DrawDefaultInspector(); // 기본 필드 그대로 유지

        RoomConfig room = (RoomConfig)target;

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("── 빠른 도구 ──", EditorStyles.boldLabel);

        if (GUILayout.Button("스폰 포인트 자동 배치"))
        {
            room.AutoPlaceSpawnPoints();
            EditorUtility.SetDirty(room); // 변경사항 저장 표시
        }

        if (GUILayout.Button("방 유효성 검사"))
        {
            bool valid = room.Validate();
            EditorUtility.DisplayDialog("검사 결과",
                valid ? "방 설정 정상" : "오류: 스폰 포인트 누락", "확인");
        }
    }
}
```

**핵심 규칙**:
- 에디터 스크립트는 반드시 `Editor/` 폴더 안에 두거나 `#if UNITY_EDITOR` 조건부 컴파일로 감쌀 것
- `EditorUtility.SetDirty(target)` 후 `AssetDatabase.SaveAssets()` 호출 → 변경사항 즉시 저장

---

### 2. `[ContextMenu]` — 우클릭 메뉴 (가장 빠른 방법)

```csharp
public class EnemySpawner : MonoBehaviour
{
    [SerializeField] private Transform[] spawnPoints;

    [ContextMenu("스폰 포인트 시각화")]
    private void VisualizeSpawnPoints()
    {
        foreach (var pt in spawnPoints)
            Debug.DrawRay(pt.position, Vector3.up * 2f, Color.red, 5f);
    }

    [ContextMenu("거리 기반 재배치")]
    private void RearrangeByDistance()
    {
        // 중심에서 거리 순으로 spawnPoints 정렬
        System.Array.Sort(spawnPoints,
            (a, b) => Vector3.Distance(transform.position, a.position)
                .CompareTo(Vector3.Distance(transform.position, b.position)));
        EditorUtility.SetDirty(this);
    }
}
```

> `[ContextMenu]`는 에디터 스크립트 없이 `MonoBehaviour` 안에 바로 쓸 수 있어 초보자에게 최적.

---

### 3. `OnDrawGizmos` / `OnDrawGizmosSelected` — 씬 뷰 시각화

```csharp
public class RoomDoor : MonoBehaviour
{
    [SerializeField] private float doorWidth = 2f;
    [SerializeField] private Color gizmoColor = Color.cyan;

    private void OnDrawGizmos()
    {
        Gizmos.color = gizmoColor;
        Gizmos.DrawWireCube(transform.position, new Vector3(doorWidth, 1f, 0f));
    }

    private void OnDrawGizmosSelected()
    {
        // 선택했을 때만 연결 방향 표시
        Gizmos.color = Color.yellow;
        Gizmos.DrawRay(transform.position, transform.right * 3f);
    }
}
```

---

### 4. `PropertyDrawer` — 특정 타입 필드 커스텀 렌더링

```csharp
// 데이터 타입
[System.Serializable]
public class WeightedEnemy
{
    public EnemyData enemy;
    [Range(0f, 1f)] public float spawnWeight;
}

// 드로어 (Editor/ 폴더)
[CustomPropertyDrawer(typeof(WeightedEnemy))]
public class WeightedEnemyDrawer : PropertyDrawer
{
    public override void OnGUI(Rect pos, SerializedProperty prop, GUIContent label)
    {
        EditorGUI.BeginProperty(pos, label, prop);
        float half = pos.width * 0.6f;

        Rect enemyRect = new Rect(pos.x, pos.y, half - 4, pos.height);
        Rect weightRect = new Rect(pos.x + half, pos.y, pos.width - half, pos.height);

        EditorGUI.PropertyField(enemyRect, prop.FindPropertyRelative("enemy"), GUIContent.none);
        EditorGUI.Slider(weightRect, prop.FindPropertyRelative("spawnWeight"), 0f, 1f, GUIContent.none);

        EditorGUI.EndProperty();
    }
}
```

---

### 5. `Handles` API — 씬 뷰에서 드래그로 값 조정

```csharp
[CustomEditor(typeof(PatrolPath))]
public class PatrolPathEditor : Editor
{
    private void OnSceneGUI()
    {
        PatrolPath path = (PatrolPath)target;

        for (int i = 0; i < path.waypoints.Length; i++)
        {
            EditorGUI.BeginChangeCheck();
            Vector3 newPos = Handles.PositionHandle(path.waypoints[i], Quaternion.identity);
            if (EditorGUI.EndChangeCheck())
            {
                Undo.RecordObject(path, "Move Waypoint");
                path.waypoints[i] = newPos;
            }
        }

        // 경로 선 그리기
        Handles.color = Color.green;
        for (int i = 0; i < path.waypoints.Length - 1; i++)
            Handles.DrawLine(path.waypoints[i], path.waypoints[i + 1]);
    }
}
```

---

### 6. `EditorWindow` — 독립 도구 창

```csharp
public class RoomBatchTool : EditorWindow
{
    [MenuItem("OnionCat/방 일괄 설정")]
    public static void ShowWindow()
    {
        GetWindow<RoomBatchTool>("방 일괄 설정");
    }

    private void OnGUI()
    {
        GUILayout.Label("선택한 방 오브젝트에 일괄 적용", EditorStyles.boldLabel);

        if (GUILayout.Button("모든 방 유효성 검사"))
        {
            RoomConfig[] rooms = FindObjectsOfType<RoomConfig>();
            int failCount = 0;
            foreach (var r in rooms)
                if (!r.Validate()) failCount++;
            Debug.Log($"총 {rooms.Length}개 방, 오류 {failCount}개");
        }
    }
}
```

---

## OnionCat 적용 포인트

### A. 방(Room) 스폰 포인트 시각화
- `RoomConfig` 컴포넌트에 `OnDrawGizmos`로 적 스폰 위치, 아이템 스폰 위치 색상 구분 표시
- 방 입구/출구(Door) 방향 화살표를 씬 뷰에서 실시간 확인
- **바로 구현**: `EnemySpawner`에 `[ContextMenu]` 추가해 스폰 포인트 미리보기

### B. 적 등장 가중치 편집 UI
- `WeightedEnemy` 배열을 `PropertyDrawer`로 "적 이름 + 가중치 슬라이더" 나란히 표시
- 기획 의도(근접 약점 적 vs 원거리 약점 적 비율)를 숫자로 바로 조정

### C. 순찰 경로 (PatrolPath) 핸들
- 씬 뷰에서 드래그로 패트롤 웨이포인트 배치 → 좌표 직접 입력 불필요
- Handles.DrawLine으로 경로 미리보기

### D. 런 밸런스 일괄 검증 도구
- `EditorWindow`로 씬 내 모든 방 설정을 한 번에 검사 (문 연결 누락, 스폰 포인트 0개 등)
- 빌드 전 실수 방지

---

## 구현 순서 (초보자용)

1. `RoomConfig` MonoBehaviour에 `[ContextMenu("스폰 유효성 검사")]` 추가 (5분)
2. 적 배치 오브젝트에 `OnDrawGizmos`로 시각화 추가 (10분)
3. 필요하면 `[CustomEditor]`로 버튼 추가 (30분)
4. `PropertyDrawer`로 WeightedEnemy 표시 개선 (1시간)
5. `EditorWindow` 일괄 도구는 방 수가 10개 이상 됐을 때 만들기

> **초보자 팁**: `[ContextMenu]`와 `OnDrawGizmos`만으로도 작업 속도가 크게 향상됨. 복잡한 에디터 창은 나중에.

---

## 참고 링크

- [Unity 공식 - Custom Editors](https://docs.unity3d.com/Manual/editor-CustomEditors.html)
- [Unity 공식 - PropertyDrawers](https://docs.unity3d.com/ScriptReference/PropertyDrawer.html)
- [Unity 공식 - Handles](https://docs.unity3d.com/ScriptReference/Handles.html)
- [Unity 공식 - EditorWindow](https://docs.unity3d.com/Manual/editor-EditorWindows.html)
- [Tutorial: Custom Inspector in Unity - Brackeys](https://www.youtube.com/watch?v=RInUu1_8aGg)
- [Custom Property Drawers - Code Monkey](https://www.youtube.com/watch?v=9gZ2MTjgMIc)
