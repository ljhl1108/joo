# 플레이어 프로필 / 이름 입력 화면 (Player Profile & Name Entry Screen)

리서치 날짜: 2026-09-28

## 개요

게임 첫 실행 시 플레이어에게 이름을 입력받고, 이후 런 기록·리더보드·감사 화면에 표시하는 기능.
아주 작은 기능이지만 "내 런"이라는 소속감을 높이고, 코옵에서 P1/P2 식별에도 유용하다.

OnionCat은 로컬 2인 코옵이므로 **P1(Cat 조종자)과 P2(Onion 조종자)** 각각 이름을 입력한다.

---

## Unity 구현 방법

### 1. 데이터 구조 (PlayerPrefs 방식)

```csharp
public static class PlayerProfile
{
    private const string KEY_P1 = "profile_name_p1";
    private const string KEY_P2 = "profile_name_p2";

    public static string P1Name
    {
        get => PlayerPrefs.GetString(KEY_P1, "Cat");
        set { PlayerPrefs.SetString(KEY_P1, value); PlayerPrefs.Save(); }
    }

    public static string P2Name
    {
        get => PlayerPrefs.GetString(KEY_P2, "Onion");
        set { PlayerPrefs.SetString(KEY_P2, value); PlayerPrefs.Save(); }
    }

    public static bool HasSetNames =>
        PlayerPrefs.HasKey(KEY_P1) && PlayerPrefs.HasKey(KEY_P2);
}
```

- 기본값 "Cat" / "Onion" → 설정 없이 바로 플레이해도 안전

### 2. 이름 입력 UI (TMP_InputField)

```csharp
public class NameEntryScreen : MonoBehaviour
{
    [SerializeField] private TMP_InputField p1Input;
    [SerializeField] private TMP_InputField p2Input;
    [SerializeField] private Button confirmButton;
    [SerializeField] private int maxLength = 12;

    private void Start()
    {
        p1Input.text = PlayerProfile.P1Name;
        p2Input.text = PlayerProfile.P2Name;
        p1Input.characterLimit = maxLength;
        p2Input.characterLimit = maxLength;
    }

    public void OnConfirm()
    {
        string n1 = p1Input.text.Trim();
        string n2 = p2Input.text.Trim();

        PlayerProfile.P1Name = string.IsNullOrEmpty(n1) ? "Cat"   : n1;
        PlayerProfile.P2Name = string.IsNullOrEmpty(n2) ? "Onion" : n2;

        // 다음 씬으로 또는 화면 닫기
        GameManager.Instance.ChangeState(GameState.MainMenu);
    }
}
```

### 3. 첫 실행 감지 → 이름 입력 화면 유도

```csharp
// App_Boot_Sequence 또는 MainMenu에서 확인
private void CheckFirstRun()
{
    if (!PlayerProfile.HasSetNames)
    {
        // 이름 입력 화면 패널 열기
        nameEntryPanel.SetActive(true);
    }
}
```

### 4. 런 결과 화면에 이름 표시

```csharp
// RunResultScreen.cs
runnerNameText.text  = PlayerProfile.P1Name;  // "Cat 조종자"
onionPlayerText.text = PlayerProfile.P2Name;  // "Onion 조종자"
```

### 5. 컨트롤러 대응 (가상 키보드 대안)

- 컨트롤러만 있는 경우 TMP_InputField 포커스 시 **On-Screen Keyboard 패널** 또는
  미리 만든 **버튼 키보드 UI** 띄우기
- 간단하게는 미리 설정된 이름 목록 스크롤(닌자·고양이·농부 등) 제공 → 선택만 하는 방식
- PC 우선 게임이면 키보드 입력으로 충분 (OnionCat은 PC 우선)

### 6. 설정 메뉴에서 이름 변경

```csharp
// SettingsMenu에서 이름 변경 버튼
public void OnEditNamesButtonClicked()
{
    nameEntryPanel.SetActive(true);
}
```

---

## OnionCat 적용 포인트

### P1 / P2 명확한 구분

- P1 = "Cat 이름" (기본: "Cat"), P2 = "Onion 이름" (기본: "Onion")
- 런 결과 화면, 사망 화면에 이름 표시 → "OOO의 Cat이 쓰러졌습니다"

### 최초 실행 온보딩 흐름

```
앱 시작 → App_Boot → HasSetNames? 
  → No  → 이름 입력 화면 → 컨트롤 안내 → 메인 메뉴
  → Yes → 메인 메뉴
```

### 런 히스토리와 연동

- `RunData.P1Name = PlayerProfile.P1Name` → 런 시작 시 스냅샷
- 나중에 이름을 바꿔도 이전 런 기록은 그대로 유지

### 짧은 구현 시간

- 이름 입력 화면은 UI 패널 1개 + 스크립트 1개로 30분 내 구현 가능
- MVP 단계에서도 넣을 가치 있음: 플레이테스트 참가자의 런 기록 구분에 유용

---

## 참고 링크

- [Unity TMP_InputField 공식 문서](https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/api/TMPro.TMP_InputField.html)
- [PlayerPrefs 공식 문서](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [Unity UI - Input Field Tutorial (Unity Learn)](https://learn.unity.com/tutorial/working-with-the-input-field)
