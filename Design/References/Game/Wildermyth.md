# Wildermyth

리서치 날짜: 2026-11-16

## 기본 정보

- **개발사**: Worldwalker Games
- **출시**: 2021-06-15 (Early Access 2019)
- **플랫폼**: PC (Steam), Nintendo Switch
- **장르**: 전술 RPG, 절차적 스토리 로그라이트, 협동
- **공식 사이트**: https://worldwalkergames.com/wildermyth
- **Steam**: https://store.steampowered.com/app/763890/Wildermyth/
- **Wiki**: https://wildermyth.fandom.com/wiki/Wildermyth_Wiki

---

## 핵심 시스템

### 1. 캐릭터 변신 (Mythic Transformation)
- 전투·이벤트 중 캐릭터 일부가 마법 생물에 융합됨
- 팔이 불꽃이 되거나 눈이 돌이 되는 등 **신체 일부 단위 변신**
- 변신 부위마다 새 능력 해금, 외형도 그에 맞게 바뀜
- 변신은 캐릭터의 정체성이 되어 스토리에도 반영됨
- 특정 부위 조합 → 세트 보너스처럼 추가 시너지 발동

### 2. 절차적 서사 (Procedural Story Events)
- 이벤트 카드 형태 (Hades의 경우처럼 조우마다 텍스트 선택지)
- 각 캐릭터의 특성·변신 상태에 따라 다른 이벤트 분기
- 캐릭터 간 관계(친구·연인·라이벌)가 전투 시너지에 영향
- 죽은 캐릭터는 "레거시"로 다음 세대에 등장 — 메타 진행의 감성적 뼈대

### 3. 전술 전투 (Tactical Grid Combat)
- 턴제 전략이지만 적의 의도가 미리 표시됨 (텔레그래프)
- 엄폐물·지형 활용이 핵심, 위치가 중요
- 근접/원거리/마법 각기 다른 효과 범위
- 협동 콤보: 옆에 있는 아군과 함께 공격하면 보너스 적용

### 4. 세대 시스템 (Legacy / Generational System)
- 캠페인은 여러 "챕터"로 구성, 각 챕터마다 새 영웅 세대 등장
- 이전 챕터 영웅의 무기·유물이 다음 세대에 전수됨
- 메타 성장이 "능력 해금"이 아닌 "감정적 유산"으로 설계됨

### 5. 협동 멀티플레이
- 최대 4인 로컬/온라인 협동
- 각자 1~2명의 캐릭터를 담당
- 비대칭 역할(근접/원거리/마법)로 자연스러운 역할 분담

---

## 플레이어들이 사랑하는 점

- 변신 조합의 창의성 — 같은 캐릭터가 없을 정도로 다양
- 절차적 텍스트임에도 감정적으로 몰입되는 서사
- "죽어도 다음 세대가 이어받는다"는 로그라이트 특유의 위로감
- 전투는 단순하지만 위치와 시너지가 깊이를 만듦
- 아트 스타일: 2D 종이 인형 같은 독창적 외형

---

## OnionCat 적용 포인트

### A. 신체 부위 단위 성장 (장비 시스템)
OnionCat은 이미 슬롯별 장비 시스템이 있음.
Wildermyth처럼 **각 슬롯에 장착된 장비의 그림이 고양이 외형에 반영**되는 방향 고려 가능
- 예: "화염 발톱" 장비 → 발에 불꽃 스프라이트 오버레이
- CatArtRenderer의 `attachment_config.json` 소켓에 슬롯별 비주얼 추가 가능
- 완전 구현 전 단계로 "장비 아이콘을 HUD 슬롯에 표시"만 해도 비슷한 감성

### B. 조합 시너지 비주얼화
Wildermyth의 변신 조합처럼, OnionCat의 세트 효과가 발동할 때 고양이+양파 비주얼에 변화 추가
- 세트 2단계 발동 시 특정 파티클이나 색상 오버레이
- `PassiveHost.Recalculate` 이후 `CombatModifiers`를 읽어 비주얼 갱신 가능

### C. 협동 역할 분담 설계
Wildermyth의 근접/원거리/마법 자연 분담처럼, OnionCat의 고양이/양파도 명확한 역할이 중요:
- 고양이 = 전선 돌파 + 적 발사체 차단 (할퀴기, 대쉬)
- 양파 = 광역 씨앗 + 필드 설치 (스킬, 화분)
- 협동 콤보 게이지를 더 가시적으로 만들어 역할 분담을 강화할 수 있음

### D. 텔레그래프 전투 디자인
Wildermyth의 "적 의도 미리 표시"와 OnionCat의 "노랑=막기/빨강=피하기" 시스템이 같은 철학.
Wildermyth에서 배울 점: 적 의도 아이콘을 단순화해도 충분히 읽힌다 (복잡한 UI 불필요)

### E. 감성적 메타 성장
Wildermyth의 레거시 시스템처럼, OnionCat의 메타 진행도 단순 해금이 아닌 "서사적 연결"을 추가 가능
- 예: 이전 런에서 모은 빛의 색이 등불에 쌓이는 현재 시스템 → 시각적 역사 기록
- 온실 화면에서 "지난번에 이 장비로 클리어한 기록" 표시

---

## 참고 링크

- Steam 상점: https://store.steampowered.com/app/763890/Wildermyth/
- 공식 사이트: https://worldwalkergames.com/wildermyth
- Polygon 리뷰: https://www.polygon.com/reviews/22533060/wildermyth-review-pc
- 개발 블로그: https://www.reddit.com/r/wildermyth/ (커뮤니티)
- GDC 발표 자료 (절차적 서사): https://www.gdcvault.com/
