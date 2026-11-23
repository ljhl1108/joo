# Steel Assault

리서치 날짜: 2026-11-23

## 기본 정보

- **개발사**: Zenovia Interactive (서울, 한국)
- **퍼블리셔**: Tribute Games
- **출시**: 2021년 9월
- **플랫폼**: PC, Nintendo Switch
- **장르**: 횡스크롤 액션 (로그라이크 아님)
- **공식 Steam**: https://store.steampowered.com/app/1491040/Steel_Assault/
- **플레이타임**: 약 1.5시간 (짧은 아케이드 스타일)

## 핵심 메커니즘

### 집라인/그래플 훅
- 수직·수평·대각선 축 어디서나 연결 가능한 집라인이 핵심 이동 수단
- 적에게도 갈고리를 걸어 당기거나 위치 전환 가능
- Kotaku: "독특하고 창의적이지만 타이밍이 까다로울 때도 있다"

### 조작 체계
- 점프, 더블 점프, 슬라이드, 집라인 — 단순하지만 조합 깊이가 있음
- 개발자 인터뷰: "메트로배니아도 로그라이크도 아니다. 현대 트렌드를 따르지 않는 순수 아케이드"

### 난이도 설계 철학
- 적 수를 늘리거나 HP를 올리는 "스탯 벽" 방식을 쓰지 않음
- 대신 이동 도구(집라인)를 얼마나 잘 쓰는지, 적 패턴을 얼마나 잘 읽는지로 난이도 결정
- Gaming Trend: "점프와 도구 사용 숙련도를 통해 도전을 유지한다"

### 적 텔레그래프
- 모든 적 공격은 애니메이션 프레임으로 명확히 예고
- "읽고 반응" 설계 철학: 갑작스러운 공격은 없음
- Nintendo World Report: "어렵지만 짧고, 무자비하지만 공정하다"

## 평가

| 항목 | 내용 |
|---|---|
| Metacritic PC | 77/100 |
| Metacritic Switch | 75/100 |
| Nintendo Life | 8/10 |
| 호평 | 레트로 비주얼, 타이트한 조작감, 타격 피드백, 적 디자인 |
| 비판 | 짧은 플레이타임, 반복적인 전투, 제한적인 다양성 |

## OnionCat 적용 포인트

### 1. 적 텔레그래프 애니메이션 설계
Steel Assault는 적 공격 직전에 명확한 모션(웅크리기, 차지 포즈)을 보여준다. OnionCat의 설계 원칙(황색=막기 가능, 적색=회피)과 정확히 일치한다. 텔레그래프 → 판정 활성화 사이의 프레임 수가 "공정하다는 느낌"을 결정한다.

**실용 힌트**: 황색 선이 뜨기 직전 1~2프레임 "웅크리기/차지 피크" 애니메이션을 추가하면 반사 신호가 더 자연스럽다. `DirectionalSprite`에 `Idle → WindUp → WindUpPeak → Attack` 태그 구조 고려.

### 2. 마스터리 기반 난이도
적의 HP를 높이거나 수를 늘리지 않고, "패턴 읽기 + 이동 도구 활용" 숙련도로 난이도를 만든다. OnionCat도 같은 방향이어야 한다 — 고양이 대쉬 충전이 적 텔레그래프를 읽고 맞춰 쓸 때 가장 재미있도록, 대쉬 타이밍 창이 충분히 열려 있는지 플레이테스트 필수.

### 3. 타격 피드백 품질 기준
한국 픽셀 아트 인디 중에서 타격 느낌 완성도가 높은 편. 히트 스톱, 화면 흔들림, 타격 이펙트의 조합이 짧은 게임에서도 얼마나 중요한지 보여준다.

### 4. 짧은 런 밀도 설계
1.5시간에 완결감을 주는 구성 — OnionCat이 목표로 하는 ~1시간 런과 플레이 밀도가 비슷하다. 각 방의 도전 밀도와 리듬이 "길지 않은 시간 안에 충분히 경험했다"는 느낌을 주어야 한다.

## 참고 링크

- [Steam 페이지](https://store.steampowered.com/app/1491040/Steel_Assault/)
- [Gaming Trend 리뷰](https://gamingtrend.com/feature/reviews/steel-assault-review-tough-as-steel/)
- [Nintendo Life 리뷰](https://www.nintendolife.com/reviews/switch-eshop/steel_assault)
- [Kotaku 프리뷰](https://kotaku.com/switchs-steel-assault-looks-like-a-gorgeous-lost-gba-g-1847797065)
