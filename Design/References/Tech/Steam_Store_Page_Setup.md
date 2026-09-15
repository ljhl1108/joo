# Steam 스토어 페이지 설정

리서치 날짜: 2026-09-15

## 개요

게임이 완성되어도 **Steam 스토어 페이지가 없으면 판매 불가**. Steamworks SDK 연동(Achievements, Cloud Save 등)과는 별개로, Steam에서 실제로 게임을 노출하고 판매하기 위한 페이지 설정 전체 흐름을 다룬다.

**OnionCat 적용 이유**: 게임 개발 초기부터 Steam 페이지를 "Coming Soon"으로 등록하면 Wishlist 수집이 가능하고, 이것이 출시 초기 판매에 결정적 영향을 미친다. 제작이 시작된 시점에 페이지도 함께 준비해야 한다.

---

## Unity 구현 방법 (Steam 등록 절차)

### 1. Steamworks 파트너 등록

1. [partner.steamgames.com](https://partner.steamgames.com/) 접속
2. 회사/개인 계정 등록 (Steamworks 계정 = Steam 계정과 별개)
3. **Steam Direct 비용**: $100 USD (출시 후 매출 $1,000 초과 시 환급)
4. 세금 정보 입력 (한국 개인: 주민등록번호 기반 W-8BEN 양식)
5. 앱 생성 → App ID 발급 (고유 숫자)

### 2. 필수 에셋 규격

| 에셋 | 크기 | 형식 | 용도 |
|------|------|------|------|
| **Header Capsule** | 460×215 px | PNG/JPG | 검색/추천 목록 |
| **Small Capsule** | 231×87 px | PNG/JPG | 큐레이션 섹션 |
| **Main Capsule** | 616×353 px | PNG/JPG | 스토어 상단 메인 이미지 |
| **Library Capsule** | 600×900 px | PNG/JPG | Steam 라이브러리 세로 이미지 |
| **Library Hero** | 3840×1240 px | PNG/JPG | 라이브러리 배경 이미지 |
| **Screenshots** | 1280×720 이상 | PNG/JPG | 최소 5장 권장 (실제 플레이 화면) |
| **Trailer** | MP4 720p+ | H.264 | 선택이지만 사실상 필수 |

> 픽셀아트 게임: 캡슐 이미지를 픽셀아트 타이포와 로고로 구성, **작게 봐도 읽히는 제목**이 핵심.

### 3. 스토어 페이지 텍스트 구성

```
Short Description (한 줄 설명): 최대 300자
- 예: "고양이 등에 탄 양파와 함께하는 2인 협동 로그라이크. 
  메인 소식: 근접이면 고양이, 원거리면 양파!"

Long Description (상세 설명): HTML 지원
- 게임 컨셉 소개
- 주요 특징 (Bullet Point)
- 조작 방법 소개
- 협동 플레이 설명
```

### 4. 태그 & 장르 설정 (SEO 역할)

Steam 내부 검색 알고리즘에 중요. OnionCat에 적합한 태그:
- **Roguelite**, **Top-Down Shooter**, **2D**, **Pixel Art**
- **Co-op**, **Local Co-Op**, **Action Roguelike**
- **Shoot 'Em Up**, **Twin Stick Shooter**, **Cute**

*태그는 정확성이 중요. 무관한 태그 추가 시 유저 민원 발생.*

### 5. 시스템 요구사양

```
최소사양:
- OS: Windows 10 64-bit
- CPU: Intel Core i5-4460 / AMD FX-8350
- RAM: 4 GB
- GPU: NVIDIA GTX 760 / AMD Radeon R9 280
- DirectX: Version 11
- Storage: 500 MB

권장사양:
(최소 + 약간 여유)
```

### 6. 출시 전략 선택

| 전략 | 특징 | OnionCat 추천 시점 |
|------|------|--------------------|
| **Coming Soon** | 출시 날짜 미정, Wishlist 수집 가능 | 지금 당장 (프로토타입 완성 후) |
| **Early Access** | 미완성 게임 판매, 피드백 수집 | 핵심 루프 완성 후 |
| **Full Release** | 완성본 출시 | 콘텐츠 완성 후 |

**Coming Soon 페이지 등록 시 주의**: 스크린샷이 실제 플레이 화면이어야 함. 컨셉 아트만으로는 거부될 수 있음.

### 7. 출시 일정과 Wishlist의 관계

- 출시 **2주 전**: Steam이 Wishlist 보유자에게 이메일 발송
- 출시 당일 Wishlist의 **10~30%**가 구매로 전환 (장르/가격에 따라 다름)
- Wishlist 1,000개 = 출시 당일 약 100~300 판매 기대

---

## OnionCat 적용 포인트

### 즉시 시작: Coming Soon 페이지

현재 시점에서 할 수 있는 것:
1. Steam Direct $100 결제 → App ID 획득
2. 게임 제목 "OnionCat" 입력
3. 임시 스크린샷 5장 업로드 (현재 플레이 화면 캡처)
4. 태그 설정: Roguelite, Local Co-Op, 2D, Pixel Art
5. 짧은 설명 작성 후 Coming Soon 공개

Wishlist 1,000개 달성 → Early Access 진입 목표.

### 캡슐 이미지 방향
- 고양이(Cat) + 화분(Crop) 두 캐릭터가 함께 있는 일러스트
- 배경에 던전 분위기
- 픽셀아트 폰트로 "OnionCat" 제목
- 460×215 px에서 작게 봐도 두 캐릭터가 보여야 함

### 트레일러 최소 요건
- 길이: 60~90초
- 첫 5초: 게임 장르 + 분위기 전달 (로그라이크 + 협동)
- 중간 30초: 실제 플레이 장면 (Cat 슬래시 + Crop 투사체 + 보스)
- 마지막 10초: 제목 + Coming Soon/Early Access

### 가격 전략
- 인디 협동 로그라이크 기준: $9.99 ~ $14.99 USD
- Enter the Gungeon: $14.99, Brotato: $4.99, Dead Cells: $24.99
- OnionCat 예상: **$9.99** (첫 출시 가격, 출시 세일 20% 할인으로 $7.99 진입)

---

## 참고 링크

- [Steamworks 공식 문서 - 스토어 페이지 설정](https://partner.steamgames.com/doc/store/listing)
- [Steam 캡슐 이미지 가이드라인](https://partner.steamgames.com/doc/store/assets/capsule)
- [Steam Direct 안내](https://partner.steamgames.com/doc/gettingstarted/appfee)
- [Game Developer - How to Build Your Steam Page](https://www.gamedeveloper.com/business/how-to-build-an-effective-steam-page)
- [Wishlist 통계 분석 - Simon Carless (GameDiscoverCo)](https://newsletter.gamediscover.co/)
- [한국 개발자 Steam 세금 처리 가이드](https://www.notion.so/Steam-d35b51d5ab3c4cd28e1a19f9a745d94e)
