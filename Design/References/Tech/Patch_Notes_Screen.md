# 패치노트 / 버전 업데이트 화면 (Patch Notes Screen)

리서치 날짜: 2026-09-27

## 개요

플레이어가 게임을 실행할 때 **이전 플레이 이후 변경된 내용을 보여주는 화면**. 인디 게임에서 Early Access 기간이나 정기 업데이트 시 플레이어 신뢰를 쌓는 중요한 UX 요소다. Unity에서는 ScriptableObject + TextMeshPro ScrollView 조합으로 쉽게 구현한다.

### 왜 중요한가
- **Early Access/패치 투명성**: 개발 진행을 플레이어에게 보여줌 → 커뮤니티 신뢰
- **복귀 유저 리텐션**: "이번 업데이트에 뭐가 생겼는지" 바로 확인 가능
- **개발 기록**: 패치노트가 곧 개발 히스토리 → 디버그와 기록 용도로도 유용

---

## Unity 구현 방법

### 1. 패치노트 데이터 구조 (ScriptableObject)

```csharp
// PatchNote.cs
[CreateAssetMenu(menuName = "OnionCat/PatchNote")]
public class PatchNote : ScriptableObject
{
    public string version;          // "0.3.1"
    public string releaseDate;      // "2026-09-27"
    [TextArea(3, 20)]
    public string content;          // 마크다운 유사 텍스트
}
```

```csharp
// PatchNoteDatabase.cs
[CreateAssetMenu(menuName = "OnionCat/PatchNoteDatabase")]
public class PatchNoteDatabase : ScriptableObject
{
    public List<PatchNote> notes;   // 최신순 정렬
}
```

`Assets/Resources/PatchNotes/` 폴더에 버전별 ScriptableObject 생성.

### 2. 화면 레이아웃

```
[PatchNotesPanel]
  ├── Header
  │   ├── TitleText: "PATCH NOTES"
  │   └── CloseButton (X)
  ├── VersionList (좌측 세로 목록)
  │   └── VersionButton × N (클릭 시 우측에 내용 표시)
  └── ContentArea (ScrollRect)
      └── ContentText (TMP)
```

**간단 버전 (단일 스크롤):**
```
[PatchNotesPanel]
  ├── TitleText
  ├── ScrollView
  │   └── Content (VerticalLayoutGroup)
  │       └── PatchEntry × N
  │           ├── VersionHeader (TMP)
  │           └── BodyText (TMP)
  └── CloseButton
```

### 3. PatchNotesUI 스크립트

```csharp
public class PatchNotesUI : MonoBehaviour
{
    [SerializeField] private PatchNoteDatabase database;
    [SerializeField] private Transform contentParent;
    [SerializeField] private GameObject entryPrefab;
    [SerializeField] private ScrollRect scrollRect;

    void OnEnable()
    {
        PopulateEntries();
        MarkCurrentVersionSeen();
    }

    private void PopulateEntries()
    {
        foreach (Transform child in contentParent)
            Destroy(child.gameObject);

        foreach (var note in database.notes)
        {
            var entry = Instantiate(entryPrefab, contentParent);
            entry.GetComponent<PatchNoteEntry>().Setup(note);
        }
    }

    private void MarkCurrentVersionSeen()
    {
        PlayerPrefs.SetString("LastSeenVersion", Application.version);
        PlayerPrefs.Save();
    }
}
```

### 4. PatchNoteEntry 프리팹

```csharp
public class PatchNoteEntry : MonoBehaviour
{
    [SerializeField] private TMP_Text versionText;
    [SerializeField] private TMP_Text bodyText;
    [SerializeField] private Image newBadge; // "NEW" 뱃지 표시용

    public void Setup(PatchNote note)
    {
        versionText.text = $"v{note.version}  <color=#888888>({note.releaseDate})</color>";
        bodyText.text = note.content;
        // 마지막으로 본 버전보다 새로운 항목이면 NEW 뱃지 표시
        string lastSeen = PlayerPrefs.GetString("LastSeenVersion", "0.0.0");
        newBadge.gameObject.SetActive(IsNewerVersion(note.version, lastSeen));
    }

    private bool IsNewerVersion(string a, string b)
    {
        if (!System.Version.TryParse(a, out var va)) return false;
        if (!System.Version.TryParse(b, out var vb)) return false;
        return va > vb;
    }
}
```

### 5. 자동 팝업 — 새 버전 감지

```csharp
// MainMenuUI.cs 등 메인 메뉴 Awake에서 호출
private void CheckAndShowPatchNotes()
{
    string lastSeen = PlayerPrefs.GetString("LastSeenVersion", "");
    if (lastSeen != Application.version)
    {
        patchNotesPanel.SetActive(true);
    }
}
```

`Application.version`은 **Project Settings > Player > Version** 값이다.
빌드할 때마다 버전을 올리면 자동으로 새 버전 감지.

### 6. 패치노트 텍스트 포맷 예시

```
[버그 수정]
- Cat 대쉬 중 적과 충돌 시 강제 종료 버그 수정
- Onion 방패가 대각선 방향 적에게 제대로 작동하지 않던 문제 수정

[밸런스]
- Slime 이동 속도 10% 감소 (난이도 조정)
- 업그레이드 'QuickSlash' 공격 범위 1.2 → 1.5유닛

[추가]
- 보스 방 전환 시 페이드 인/아웃 연출 추가
- 런 결과 화면에 획득 업그레이드 목록 표시
```

### 7. 외부 URL에서 패치노트 불러오기 (선택 — 온라인)

```csharp
// WebGL이나 온라인 게임에서 최신 패치노트를 서버에서 가져오는 패턴
private IEnumerator FetchPatchNotes(string url)
{
    using var req = UnityWebRequest.Get(url);
    yield return req.SendWebRequest();
    if (req.result == UnityWebRequest.Result.Success)
    {
        // JSON 파싱 후 UI 업데이트
        var data = JsonUtility.FromJson<PatchNoteData>(req.downloadHandler.text);
        UpdateUI(data);
    }
}
```

OnionCat은 로컬 ScriptableObject 방식이면 충분. 서버 불필요.

---

## OnionCat 적용 포인트

### 구현 순서

1. `PatchNote` ScriptableObject 클래스 작성
2. `PatchNoteDatabase` SO 생성 (`Assets/Resources/PatchNotes/Database.asset`)
3. 버전별 PatchNote SO 작성 (v0.1.0부터)
4. 메인 메뉴에 ScrollView 패널 추가, `PatchNotesUI` 스크립트 부착
5. `MainMenuUI.Awake`에서 버전 비교 후 자동 팝업 호출
6. "닫기" 버튼 클릭 시 `PlayerPrefs`에 현재 버전 저장

### 주의할 점

- `Application.version`은 빌드 시 고정됨 → 에디터에서는 항상 팝업이 뜰 수 있으므로 `#if UNITY_EDITOR` 분기 필요
- 패치노트 내용은 **영어로** 작성 (TMP 폰트 한글 미지원)
- 스크롤 최상단으로 자동 이동: `scrollRect.verticalNormalizedPosition = 1f;`
- VerticalLayoutGroup의 Content Size Fitter 설정 필수 (스크롤 크기 자동 조절)

### 콘텐츠 가이드라인

- 버그 수정 / 밸런스 / 추가 / 변경 4개 섹션으로 분류
- 최대 10개 항목 (너무 많으면 읽지 않음)
- 게임에 직접 영향 없는 내부 코드 리팩토링은 기재 불필요

---

## 참고 링크

- [Unity Manual — TextMeshPro ScrollView](https://docs.unity3d.com/Packages/com.unity.textmeshpro@latest)
- [Unity Manual — PlayerPrefs](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [Unity Manual — Application.version](https://docs.unity3d.com/ScriptReference/Application-version.html)
- [Game UI Database — Patch Notes Examples](https://www.gameuidatabase.com/)
- [Hades Patch Notes Style Reference](https://store.steampowered.com/news/app/1145360)
