# Legal Notice / Third-Party License Screen

리서치 날짜: 2026-11-28

## 개요

게임을 Steam·itch.io·콘솔에 출시하려면 법적 고지 화면이 필요하다.
대부분의 인디 개발자가 마지막까지 미루다가 출시 직전에 허둥대는 항목.
OnionCat은 Unity 엔진, 여러 에셋 패키지, 오픈소스 라이브러리(Galmuri 폰트 등)를 쓰고 있으므로
지금부터 목록을 관리해두는 것이 좋다.

## 필수 항목 체크리스트

### 1. 저작권 표시 (Copyright Notice)
게임 어딘가(크레딧 화면 또는 타이틀 하단)에 반드시 표시:
```
© 2026 [개발자 이름/닉네임]. All rights reserved.
```

### 2. Unity 엔진 고지
Unity 개인·Plus·Pro 라이선스 사용 시 "Made with Unity" 로고 스플래시가 자동 포함됨.
Personal 플랜은 의무이므로 별도 로고는 필요 없음.
단, Unity의 TOS 변경 이력을 확인할 것 (2023 이후 런타임 비용 정책 주의).

### 3. 오픈소스 라이브러리 고지

#### OnionCat에서 사용 중인 오픈소스 목록 (관리 필요)

| 항목 | 라이선스 | 고지 위치 |
|------|----------|-----------|
| Galmuri11 폰트 | SIL OFL 1.1 | 크레딧 화면 필수 |
| Unity 기본 패키지들 (Cinemachine, 2D 등) | Unity 라이선스 — 별도 고지 불필요 |
| TextMeshPro | Unity 라이선스 |  |
| CC0 효과음 (`Assets/Audio/`) | CC0 — 고지 의무 없음 (그래도 감사 차원에서 출처 기록) |

**SIL OFL 1.1 필수 요건**:
- 폰트 이름(Galmuri)은 변경 없이 사용 시 — 크레딧 한 줄 충분
- 폰트를 수정·재배포할 경우 OFL 라이선스 전문 포함 필요

### 4. 구매 에셋 / 아트 고지
OnionCat에서 에셋스토어 구매 에셋을 사용 중 (Honeti GUI 그림 29장).
이런 에셋은 구매 라이선스로 보호되므로 별도 고지는 불필요.
단, **절대 에셋을 공개 저장소에 올리지 말 것** (CLAUDE.md에 이미 명시됨).

### 5. 개인정보 처리방침 (Privacy Policy)
게임에서 개인 데이터를 **전혀 수집하지 않는다면** 필요 없음.
로컬 저장만 쓰고 analytics, cloud save, 계정 없으면 → 불필요.
단, Steam 통계 (Steam Stats API) 쓰면 Steam이 데이터를 수집함 → Steam의 PP로 커버됨.

## Unity에서 구현 방법

### 간단한 크레딧/라이선스 화면

```csharp
// LicenseScreen.cs
public class LicenseScreen : MonoBehaviour
{
    [SerializeField] private TMP_Text licenseText;
    [SerializeField] private TextAsset licenseFile;  // Resources/LICENSES.txt

    void Start()
    {
        licenseText.text = licenseFile.text;
    }
}
```

**LICENSES.txt** (Resources/ 폴더에 저장):
```
OnionCat — 오픈소스 고지

■ Galmuri11 폰트
  Copyright (c) 2019-2023, ozh (https://github.com/quiple/galmuri)
  Licensed under SIL Open Font License 1.1
  https://scripts.sil.org/OFL

■ 효과음
  CC0 오디오. 출처 목록: Assets/Audio/LICENSE_AUDIO.txt
```

### 크레딧 화면 UI 구조

```
[크레딧 화면]
  만든 사람
    [개발자 이름]
  
  특별 감사
    [테스트해준 사람들]
  
  오픈소스 / 폰트
    Galmuri11 폰트 — SIL OFL 1.1 (ozh)
  
  효과음
    freesound.org, opengameart.org
  
  Unity 엔진으로 제작
    unity.com
  
  © 2026 [이름]. 모든 권리 보유.
```

### ScrollRect로 긴 라이선스 텍스트 표시

긴 라이선스(예: MIT 전문)를 보여줄 경우:

```csharp
// 크레딧 화면을 스크롤 가능하게
[SerializeField] private ScrollRect scrollRect;

void ShowLongLicense()
{
    scrollRect.gameObject.SetActive(true);
    // 긴 텍스트를 TMP_Text에 넣으면 ScrollRect가 자동으로 스크롤 가능
}
```

## 플랫폼별 추가 요건

### Steam
- Steam 자체 Privacy Policy와 GDPR 처리
- 구매 → 환불 정책: Steam이 처리해 줌
- 연령 등급: PEGI 또는 ESRB 중 하나 필요 (무료 self-rating 가능)
  - 한국 게임물관리위원회(GRAC) 등급: itch.io는 불필요, Steam 한국 출시는 필요할 수 있음

### itch.io
- 별도 법적 의무 없음 (플랫폼이 처리)
- 단, Creative Commons 에셋 사용 시 게임 페이지에 간단 고지 권장

## OnionCat 적용 포인트

### 지금 당장 할 것
1. **LICENSES.txt 파일 만들기** — `Assets/Resources/LICENSES.txt`
   Galmuri11 폰트 고지 한 줄 + 오디오 출처 참조 (이미 `LICENSE_AUDIO.txt` 존재)
2. **크레딧 화면에 폰트 고지 추가** — 크레딧 화면 맨 아래 Galmuri11 한 줄

### 출시 직전 체크
- [ ] Galmuri11 폰트 고지가 크레딧에 있는가?
- [ ] 오디오 출처가 `LICENSE_AUDIO.txt`에 모두 기록되어 있는가?
- [ ] Unity Personal 스플래시가 나오거나 삭제를 위해 라이선스 업그레이드 여부 결정
- [ ] Steam 출시 시 연령 등급 self-rating 완료
- [ ] 게임 내 어딘가에 © 연도 개발자 이름 표시

### 향후 콘솔 출시 시
닌텐도 스위치·PlayStation은 별도 TRC(기술적 요건 체크리스트)가 있으며
법적 고지 화면을 메인 메뉴 접근 가능한 곳에 배치해야 함.
Steam PC 출시 단계에서는 위 간단 체크로 충분.

## 참고 링크

- SIL OFL 1.1 전문: https://scripts.sil.org/OFL
- Galmuri GitHub (라이선스 확인): https://github.com/quiple/galmuri
- Steam 연령 등급 self-rating: https://partner.steamgames.com/doc/store/ratings
- GRAC 한국 게임 등급 분류: https://www.grac.or.kr/
- Unity 개인 라이선스 TOS: https://unity.com/legal/terms-of-service
