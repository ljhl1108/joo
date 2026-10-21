# Content Warning & Age Rating Screen

리서치 날짜: 2026-10-21

## 개요

게임을 상업적으로 출시하려면 **연령 등급(연령 등급 분류)**을 받고, 첫 실행 시 **콘텐츠 경고 화면**을 표시해야 한다. 한국 개발자는 국내 판매 시 **GRAC(게임물관리위원회) 등급**이 법적으로 의무다. 이 기능은 출시 전에 반드시 갖춰야 하는 완성도 요소이며, 빠뜨리면 스토어 등록 거절 또는 법적 문제가 생길 수 있다.

---

## 연령 등급 기관 및 절차

### 한국 — GRAC (게임물관리위원회)

- **사이트**: https://www.grac.or.kr
- **등급**: 전체이용가 / 12세 이용가 / 15세 이용가 / 청소년이용불가
- **의무 여부**: 국내에서 유료 또는 인앱결제 게임을 서비스하려면 **등급 분류 필수**. itch.io에 무료로 올리는 것은 예외지만 Steam 한국 판매는 해당됨.
- **신청 방법**:
  1. GRAC 포털 회원 가입 (사업자/개인)
  2. 「게임물 자체등급분류 사업자」 신청 가능 (연간 일정 매출 이하 소규모 사업자 혜택)
  3. 심의 신청서 + 게임 시연 파일 또는 영상 제출
  4. 심사비: 소규모 게임 수만원 수준
  5. 처리기간: 2~4주 (비대면 심사 기준)
- **OnionCat 예상 등급**: 12세 이용가 또는 전체이용가 (폭력 표현이 만화풍·경미하고 공포 요소 없음)

### 미주 — ESRB

- **사이트**: https://www.esrb.org
- **등급**: E (Everyone) / E10+ / T (Teen) / M (Mature 17+)
- **인디 자체 심사**: ESRB IARC(국제 연령 등급 연합) 프로그램 — **무료 온라인 설문**으로 자동 등급 부여. Steam/itch.io/Google Play 모두 지원.
- **소요 시간**: 15분 내외 (설문 작성)

### 유럽 — PEGI

- **사이트**: https://pegi.info
- **등급**: PEGI 3 / 7 / 12 / 16 / 18
- **IARC 연동**: ESRB IARC와 동일한 설문으로 PEGI 등급도 동시 부여됨

### IARC — 한 번에 여러 등급 취득

- **사이트**: https://www.globalratings.com
- Steam, Epic, itch.io, Google Play에서 게임 출시 시 IARC 설문 진행 → ESRB+PEGI+USK+CERO+ClassInd 등 동시 부여
- **GRAC는 별도 신청 필요** (IARC에 포함되지 않음)

---

## 콘텐츠 경고 화면 구현 (Unity)

### 필수 표시 항목

1. **연령 등급 아이콘** (GRAC·PEGI·ESRB 로고 이미지)
2. **광과민성 발작 경고** (간질 경고): 거의 모든 플랫폼이 요구
3. **저작권 / 회사명**
4. **첫 실행 시 1회만 표시** 권장 (매번 띄우면 불쾌)

### Unity 구현

```csharp
public class FirstBootWarningScreen : MonoBehaviour
{
    const string PREF_KEY = "WarningShown_v1";
    
    void Start()
    {
        // 이미 본 적 있으면 스킵
        if (PlayerPrefs.GetInt(PREF_KEY, 0) == 1)
        {
            LoadMainMenu();
            return;
        }
        
        // 경고 화면 표시 (이미 활성화된 UI)
        // 버튼 클릭 시 OnConfirm() 호출
    }
    
    public void OnConfirm()
    {
        PlayerPrefs.SetInt(PREF_KEY, 1);
        PlayerPrefs.Save();
        LoadMainMenu();
    }
    
    void LoadMainMenu()
    {
        SceneManager.LoadScene("MainMenu");
    }
}
```

### 광과민성 경고 권고 문구 (한국어)

```
경고: 이 게임에는 일부 사람에게 광과민성 발작을 일으킬 수 있는
빠르게 깜빡이는 이미지 또는 섬광이 포함되어 있습니다.

간질 또는 광과민성이 있는 경우 의사와 상담 후 플레이하세요.
```

영어 버전:
```
WARNING: This game contains flashing lights and rapidly changing
images that may affect a small percentage of people.
If you or anyone in your household has epilepsy or is photosensitive,
consult your doctor before playing.
```

### 화면 구성 예시

```
[게임 타이틀 로고] - 작게
[GRAC 등급 아이콘 이미지]   [PEGI 등급 아이콘]
─────────────────────────────────────────
⚠ 광과민성 발작 경고
이 게임은 빠르게 깜빡이는 이미지가 포함될 수 있습니다.
─────────────────────────────────────────
© 2026 [개발사명]. All rights reserved.
         [확인] 버튼
```

### 스킵 방지

`Input.anyKeyDown`으로 즉시 스킵되는 것을 막으려면:
```csharp
// 최소 2초 후 버튼 활성화
IEnumerator EnableButtonAfterDelay()
{
    confirmButton.interactable = false;
    yield return new WaitForSeconds(2f);
    confirmButton.interactable = true;
}
```

---

## Steam 출시 시 추가 요건

- **콘텐츠 디스크립터**: Steam 대시보드 → App Admin → 콘텐츠 서베이 (폭력·성인 내용 여부 체크)
- **연령 제한 게이팅**: 성인용 게임만 해당 (OnionCat 불필요)
- **게임 설명 내 내용 고지**: Steam 상점 페이지에 "이 게임에는 폭력적인 내용이 포함될 수 있습니다" 형식의 자체 고지 권장

---

## OnionCat 적용 포인트

### 구현 우선순위

1. **IARC 설문 먼저** (itch.io 또는 Steam 출시 신청 시 자동 안내됨): 15분, 무료
2. **Unity 첫 실행 경고 화면** 추가: `Boot` 씬 → `MainMenu` 씬 사이에 삽입, `Bootstrap_Scene_Architecture.md` 참고
3. **GRAC 신청** (Steam 한국 판매 직전): GRAC 포털에서 신청, 2~4주 여유를 두고 진행

### 주의사항

- `PlayerPrefs`에 저장하는 "경고 봤음" 키는 **게임 버전에 따라 다른 키**를 쓸 것 (`WarningShown_v1`, `v2`...). 업데이트로 경고 내용이 바뀌면 다시 보여줘야 할 경우 대비
- GRAC 등급 아이콘 이미지는 GRAC 사이트에서 공식 제공 이미지를 사용 (비공식 재제작 금지)
- 등급 아이콘을 메인 메뉴 하단 또는 타이틀 화면에 **항상 표시** 권장 (로딩 화면에만 한 번이 아니라)

---

## 참고 링크

- GRAC 공식 사이트: https://www.grac.or.kr
- ESRB 자체 등급 (인디): https://www.esrb.org/ratings-process/getting-a-rating/
- IARC 글로벌 등급: https://www.globalratings.com
- PEGI 공식: https://pegi.info
- Steam 콘텐츠 서베이 안내: https://partner.steamgames.com/doc/store/contentratings
- 인디 출시 법률 체크리스트 (GameDev.net 검색)
