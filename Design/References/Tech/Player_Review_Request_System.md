# Player Review Request System

리서치 날짜: 2026-11-20

## 개요

게임이 완성 단계에 가까워졌을 때 플레이어에게 Steam 리뷰·평점을 요청하는 시스템.
타이밍과 방식이 나쁘면 거부감이 생기고, 잘 하면 긍정 리뷰 비율이 올라간다.

OnionCat처럼 첫 게임을 출시하는 개발자에게 Steam 리뷰 개수와 평점은 **노출(알고리즘)과 구매 전환**에 직결되는 핵심 지표.

---

## 언제 요청해야 하는가 (타이밍 디자인)

### 좋은 타이밍: "플레이어가 만족감을 느낀 직후"

| 이벤트 | 예시 |
|---|---|
| **보스 클리어 직후** | 첫 번째 보스 처치 — 성취감 최고조 |
| **첫 런 클리어** | 처음으로 엔딩 도달 — 완주 감동 |
| **세트 보너스 첫 발동** | "오, 이 조합이 강하다" 느낌 |
| **플레이타임 임계값** | 약 2~3시간 경과 (Steam 환불 기간 2시간 이후) |
| **런 개수 임계값** | 5~7번째 런 (어느 정도 익숙해졌을 때) |

### 나쁜 타이밍: 피해야 할 순간

- 게임 오버 직후 (좌절감)
- 전투 중 (방해됨)
- 게임 첫 시작 직후
- 튜토리얼 중

---

## Unity + Steam API 구현

### Steam API 리뷰 요청 (Steamworks.NET 기준)

```csharp
using Steamworks;

public static class ReviewRequestSystem
{
    static bool _hasRequested = false;

    public static void TryRequestReview(ReviewMoment moment)
    {
        if (_hasRequested) return;
        if (!SteamManager.Initialized) return;
        if (!ShouldRequest(moment)) return;

        // Steam이 적절한 타이밍에 리뷰 UI를 표시 (Steam이 판단 — 너무 자주 나오지 않게 Steam이 조절)
        SteamFriends.ActivateGameOverlayToWebPage(
            "steam://store/" + SteamUtils.GetAppID().m_AppId
        );
        // 또는 더 최신 API (Steam SDK 1.52+):
        // SteamUtils.RequestGameSurvey(); // 실험적
        
        _hasRequested = true;
        SaveRequested();
    }

    static bool ShouldRequest(ReviewMoment moment)
    {
        // 이미 요청했으면 안 함
        if (PlayerPrefs.GetInt("ReviewRequested", 0) == 1) return false;

        return moment switch
        {
            ReviewMoment.FirstBossKill    => MetaProgress.data.bossKills >= 1,
            ReviewMoment.FirstClear       => MetaProgress.data.clearCount >= 1,
            ReviewMoment.RunCountThreshold=> MetaProgress.data.runCount   >= 6,
            _                             => false
        };
    }

    static void SaveRequested()
        => PlayerPrefs.SetInt("ReviewRequested", 1);
}

public enum ReviewMoment
{
    FirstBossKill,
    FirstClear,
    RunCountThreshold
}
```

### 호출 위치

```csharp
// 보스 처치 직후 (GameManager 또는 BossHealth)
ReviewRequestSystem.TryRequestReview(ReviewMoment.FirstBossKill);

// 엔딩 화면 로드 직후
ReviewRequestSystem.TryRequestReview(ReviewMoment.FirstClear);

// 런 결과 화면 초기화 시
ReviewRequestSystem.TryRequestReview(ReviewMoment.RunCountThreshold);
```

### 인게임 UI 방식 (Steam API 대신)

Steam 오버레이 대신 게임 내 토스트 메시지로 먼저 물어보는 방법:

```csharp
// 토스트 UI: "즐거우셨나요? Steam 리뷰를 남겨주시면 큰 도움이 됩니다 ♥"
// [지금 쓰기] [나중에] 버튼

// "지금 쓰기" → SteamFriends.ActivateGameOverlayToWebPage(steamReviewUrl)
// "나중에"   → PlayerPrefs에 "askLater" + 다음 런 결과 화면에서 한 번만 더
// 두 번 거절 → 다시는 묻지 않음
```

---

## 비Steam 플랫폼 대응

| 플랫폼 | API |
|---|---|
| itch.io | 직접 URL 열기 (itch.io 리뷰 없음 — 개발자 직접 받는 방법만) |
| Nintendo Switch | `nn::friend::ShowOverlayNintendoNetworkSystemApplicationPage` (인증된 개발자만) |
| Xbox | `Windows.Services.Store.StoreRequestHelper` |
| iOS/Android | `SKStoreReviewController.RequestReview()` / `ReviewManager.requestReview()` |

---

## 설계 원칙

### 1. 한 번만 묻는다

어떤 버튼을 눌렀든 (남김 / 나중에 / 무시), **같은 세션이나 같은 런에서 다시 묻지 않는다.**
"나중에"를 눌렀으면 다음 런 클리어 때 한 번만 더. 그 이후에는 조용히.

### 2. 강요하지 않는다

[지금 쓰기] 버튼이 절대 "게임 계속하기" 버튼보다 크지 않아야 함.
닫기 버튼을 항상 명확하게 보이도록.

### 3. 상황을 존중한다

보스전 직전이나 직후의 흥분 상태, 또는 게임오버 화면에서는 절대 묻지 않는다.
OnionCat에서 적합한 순간: **런 결과 화면** (전투가 끝나고 숨 돌리는 순간).

### 4. 감사 표현을 앞에

"리뷰 써줘"보다 "지금까지 플레이해주셔서 감사합니다. Steam 리뷰를 남겨주시면 작은 팀에 큰 힘이 됩니다."
→ 상업적 요청이 아닌 진심으로 느껴지게.

---

## OnionCat 적용 포인트

```
트리거:
① 첫 보스 클리어 → 런 결과 화면에서 토스트 표시
② 런 5회 → 런 결과 화면 (①가 발동되지 않은 경우 대비)
③ 엔딩 도달 → 엔딩 크레딧 후 (최우선)

저장: MetaProgress.reviewRequested (bool) → meta.json에 포함
주의: 테스트 플레이 후 meta.json 되돌릴 때 reviewRequested도 초기화
```

| 상황 | 표시 방법 |
|---|---|
| 첫 보스 클리어 | 런 결과 화면 하단 토스트 (3초 뒤 자동 닫힘, 클릭하면 Steam 열림) |
| 엔딩 도달 | 크레딧 후 별도 "감사합니다" 화면에 리뷰 버튼 |

---

## 참고 링크

- Steamworks 오버레이 활성화: https://partner.steamgames.com/doc/api/ISteamFriends#ActivateGameOverlay
- Steamworks.NET: https://steamworks.github.io
- 모바일 리뷰 요청 모범 사례 (Google): https://developer.android.com/guide/playcore/in-app-review
- 인디 개발자 Steam 리뷰 가이드: https://howtomarketagame.com/2021/01/11/how-to-get-more-steam-reviews/
