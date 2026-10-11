# Steam Remote Play Together 통합

리서치 날짜: 2026-10-11

## 개요

**Steam Remote Play Together**는 Valve가 제공하는 기능으로, 로컬 코옵 게임을 온라인으로 플레이할 수 있게 해준다. 게임은 호스트 PC에서만 실행되고, 게스트는 화면을 스트리밍으로 받고 입력만 전송하는 방식이다. **게스트가 게임을 구매하지 않아도 플레이 가능**하다는 것이 핵심 장점.

OnionCat처럼 1PC·2인 로컬 코옵 게임에게는 사실상 무료 온라인 코옵 인프라로, 구현 비용이 매우 낮다.

---

## 작동 원리

```
[호스트 PC에서 게임 실행]
        ↓
    화면 캡처 + 오디오
        ↓ (Steam 네트워크 스트리밍)
  [게스트 PC에서 화면 수신]
        ↓
  게스트 입력(키보드/마우스/패드)
        ↓ (다시 Steam으로 전송)
  [호스트 PC의 게임이 게스트 입력을 로컬 입력으로 수신]
```

게임 입장에서는 **같은 PC에 여러 입력 장치가 꽂힌 것처럼** 보인다. 네트워크 코드가 전혀 없어도 로컬 코옵이 이미 동작하면 대부분 그대로 작동한다.

---

## 개발자 설정 방법

### Steamworks 포털에서 활성화
1. Steamworks 관리 페이지 → **Store Page > Basic Info**
2. "Remote Play Together" 체크박스 활성화
3. 또는 **Local Multiplayer / Local Co-op / Shared Screen** 중 하나를 이미 체크했다면 자동으로 활성화됨

공식 문서: https://partner.steamgames.com/doc/features/remoteplay

### 초대 API (선택사항)
게임 내에서 Steam 친구를 직접 초대하려면:

```cpp
// Steamworks SDK (C++)
SteamRemotePlay()->BSendRemotePlayTogetherInvite(steamIDFriend);
```

Unity에서는 Steamworks.NET 또는 Facepunch.Steamworks 래퍼로 호출 가능:
```csharp
// Facepunch.Steamworks 예시
SteamRemotePlay.SendRemotePlayTogetherInvite(friendSteamId);
```

Steam 오버레이(Shift+Tab)에서 친구 초대도 별도 코드 없이 가능.

---

## ⚠️ Unity New Input System 호환성 문제

**OnionCat에서 중요**: Unity **New Input System (com.unity.inputsystem)**은 Steam Remote Play Together와 **완전히 호환되지 않는다**.

- Unity 이슈 트래커 공식 확인: https://issuetracker.unity3d.com/issues/onunpaireddeviceused-doesnt-trigger-when-using-steam-remote-play
- 증상: 게스트 입력이 게임에 전달되지 않거나, 컨트롤러로만 작동하고 키보드/마우스는 안 됨
- Valve와 Unity 양쪽 모두에서 추가 작업이 필요하다고 공식 인정

### 해결 방안 옵션

| 방안 | 설명 | OnionCat 적용 가능성 |
|---|---|---|
| **Steam Input API 사용** | Valve의 Steam Input API로 게스트 입력을 직접 폴링 | 복잡, 컨트롤러 전용 |
| **레거시 Input Manager로 일부 전환** | 게스트용 경로만 `Input.GetAxis` 등으로 | 기존 코드 수정 필요 |
| **패드 전용 Remote Play 안내** | 게스트는 컨트롤러만 사용하도록 UI 안내 | 간단, 양파(마우스) 조작 불가 |
| **향후 Unity/Valve 업데이트 대기** | 공식 지원 시 재검토 | 지금 당장은 불가 |

OnionCat의 경우 고양이(패드)는 패드 입력이라 작동할 가능성 높지만, **양파(마우스+키보드)는 호환 문제 가능성**이 크다.

---

## Unity 프로젝트 설정 순서

1. **Steamworks SDK 통합**: Facepunch.Steamworks 또는 Steamworks.NET 패키지 설치
2. Steam App ID 설정 (`steam_appid.txt` 프로젝트 루트에)
3. Steamworks 포털에서 Remote Play Together 활성화
4. **에디터에서는 테스트 불가** — 반드시 Steam 클라이언트로 실행되는 빌드에서만 작동
5. 비밀번호로 잠긴 테스트 브랜치에 업로드 후 테스트 권장

### 에디터에서 로컬 테스트
Remote Play 자체는 에디터에서 테스트 불가이지만, 로컬에서 여러 입력 장치가 동시에 잡히는지는 에디터에서 확인 가능:
```csharp
// 연결된 모든 기기 목록 확인
InputSystem.devices.forEach(d => Debug.Log(d.name));
```

---

## 한계 및 고려사항

- **지연**: 호스트 업로드 + 게스트 다운로드 대역폭에 의존. Wi-Fi 환경에서 끊김 빈번
- **최대 4인**: Steam 설정에 따라 다르나 일반적으로 4인 제한
- **게스트는 게임을 소유할 필요 없음**: 마케팅 포인트 ("친구 한 명만 사도 같이 플레이")
- **화면 공유**: 기본적으로 호스트 화면 전체가 스트리밍됨. Split-screen이 아닌 shared screen 게임은 한 화면이 그대로 감
- **New Input System 미지원**: OnionCat의 가장 큰 장애물

---

## OnionCat 적용 포인트

1. **단기 목표**: Steamworks 포털에서 Remote Play Together 체크박스만 활성화. 추가 코드 없이 컨트롤러 2개 조합은 작동할 수 있음

2. **실용적 접근**: 고양이(패드) + 양파(패드 또는 키보드) 중 **패드 2개 조합**을 Remote Play Together 공식 권장 조작으로 안내. 마우스 조준은 Remote Play에서 지원 보장 불가임을 UI에 표시

3. **향후 개선**: Unity Input System 호환 패치가 나오면 재검토. 또는 Steam Input API 직접 통합으로 완전한 지원

4. **홍보 포인트**: "게스트가 게임을 사지 않아도 플레이 가능"은 인디 게임 홍보에 효과적. Steam 스토어 태그 "Remote Play Together" 추가 권장

---

## 참고 링크

- Steamworks 공식 Remote Play 문서: https://partner.steamgames.com/doc/features/remoteplay
- Steam 지원 FAQ: https://help.steampowered.com/faqs/view/0689-74B8-92AC-10F2
- Unity 이슈 트래커 (New Input System 미지원): https://issuetracker.unity3d.com/issues/onunpaireddeviceused-doesnt-trigger-when-using-steam-remote-play
- Unity 포럼 스레드: https://discussions.unity.com/t/trouble-testing-steam-remote-play-together-in-the-unity-editor/1559993
- Facepunch.Steamworks (Unity용 래퍼): https://github.com/Facepunch/Facepunch.Steamworks
- Heathen Group Remote Play 가이드: https://kb.heathen.group/steam/features/remote-play
