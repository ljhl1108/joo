# Brotato

리서치 날짜: 2026-08-04

## 기본 정보

- **개발사**: Blobfish (1인 개발자 Arnaud Couturier)
- **출시**: 2023년 9월 (Full Release) / 2022년 8월 (Early Access 시작)
- **플랫폼**: PC, Switch, Xbox, Mobile
- **장르**: 탑다운 서바이벌 로그라이트 (파밍 서바이벌)
- **Steam**: https://store.steampowered.com/app/1942280/Brotato/
- **위키**: https://brotato.wiki.spellsandguns.com/
- **공식 사이트**: https://www.blobfish.dev/

---

## 핵심 시스템

### 웨이브 기반 구조
- **20 웨이브** → 보스 → 런 클리어
- 각 웨이브는 60초 (자동 전투)
- 웨이브 사이 상점에서 무기/아이템 구매
- 적 강도: 웨이브가 진행될수록 적 수·체력·속도 증가

### 캐릭터 시스템 (44종+)
- 각 캐릭터(Brotato)마다 완전히 다른 제한/보너스:
  - **Well Rounded**: 기본 캐릭터, 제한 없음
  - **Crazy**: 무기를 6개가 아닌 10개 장착 가능, 치명타 없음
  - **Chunky**: 체력이 매우 높지만 이동속도 -50%
  - **Engineer**: 터렛 설치, 직접 공격 불가
  - **Ghost**: 투명화, 낮은 체력
  - **Doctor**: 적 처치 시 HP 회복, 다른 아이템은 없음

### 무기 시스템
- **최대 6개 무기 동시 장착** (캐릭터에 따라 다름)
- 무기마다 자동 발사 (플레이어는 이동만 조작)
- 무기 Tier 1~5, 합치기(upgrade) 가능: 동일 무기 3개 → 다음 티어
- 근접/원거리/마법/특수 등 다양한 타입

### 스탯 시스템
15개 이상의 스탯:
- **Speed**, **Armor**, **Dodge**, **Max HP**, **Luck**
- **Melee Damage**, **Ranged Damage**, **Elemental Damage**
- **Attack Speed**, **Projectile Speed**, **Life Steal**
- **Engineering** (터렛 강화), **Harvesting** (상점 아이템 선택지 수)

아이템들은 스탯을 올리거나 특수 효과를 부여 → 시너지 빌드 구성

### 경제 시스템
- 적 처치 시 재화(Materials) 드롭
- 웨이브 사이 **상점** (5~8개 아이템 선택지)
- 무기/아이템 가격: 10~50 재화
- Luck 스탯으로 희귀 아이템 확률 증가

### 난이도 (Danger)
- 0~5 단계 (5 = 가장 어려움)
- 1인 개발이지만 5단계는 하드코어 플레이어도 도전적

---

## 플레이어가 사랑하는 것

1. **짧은 런 길이**: 1런 = 25~40분 → 가볍게 즐기기 가능
2. **빌드 다양성**: 캐릭터 44종 × 아이템 시너지 = 사실상 무한한 빌드
3. **시각적 명확성**: 적은 빨강, 플레이어는 밝음, 무기 타격 이펙트 명확
4. **성장감**: 웨이브가 진행될수록 캐릭터가 강해지는 RPG적 느낌
5. **접근성**: 마우스/키보드 없이 게임패드로도 편하게 플레이

---

## OnionCat 적용 포인트

### 1. 스탯 분리 설계
Brotato는 근접/원거리 스탯이 완전히 분리됨. OnionCat은 이 구조를 그대로 사용 가능:
- Cat 전용 업그레이드: Melee Damage, Dash Cooldown, Slash Arc
- Crop 전용 업그레이드: Ranged Damage, Projectile Speed, Shield Duration
- 공유 업그레이드: Speed, Max HP, Luck

### 2. 상점 / 아이템 선택 UI
Brotato 상점은 단순하고 명확:
- 4~6개 아이템 카드 표시
- 각 카드: 아이콘 + 이름 + 스탯 변화 + 가격
→ OnionCat 업그레이드 선택 화면 레이아웃 참고 가능

### 3. 무기 티어 합치기 시스템
3개 합쳐서 다음 티어로 업그레이드하는 방식은 중복 드롭에 대한 불만을 해소:
- OnionCat: 같은 업그레이드 카드 3번 선택 시 강화 버전 획득으로 응용 가능

### 4. Danger 난이도 구조
런 선택 화면에서 난이도 0~5 선택:
- 각 단계마다 구체적인 수치 변화 (적 체력 +20%, 속도 +10% 등)
- OnionCat의 난이도 시스템 설계에 참고 (Dynamic_Difficulty_System.md와 조합)

### 5. 1인 개발 참고 케이스
Brotato는 1인 개발자가 만든 게임:
- 총 개발 기간: Early Access 포함 14개월
- 무기/아이템 수에서 "더하기 쉬운 구조" 설계가 핵심
- ScriptableObject 기반 데이터 설계 추측 (ScriptableObject_Data_System.md 참고)

### 6. 자동 공격 vs 수동 공격
Brotato: 무기 자동 발사 → 이동에 집중
OnionCat: Cat은 수동 입력, Crop은 마우스 조준 (Brotato보다 인터랙티브)
→ 조준의 재미를 어떻게 Brotato 만큼의 파워 판타지로 연결할지 설계 필요

---

## 개발 인사이트

- **아이템 밸런스 방법**: 모든 아이템을 동일 가격 10 재화로 시작 후 플레이테스트로 조정
- **스탯 투명성**: 모든 수치를 플레이어에게 명시적으로 보여줌 → 빌드 계획 가능
- **비주얼 클리어링**: 배경은 단색에 가깝게 유지, 적과 프로젝타일이 눈에 띄게
- **Early Access 활용**: 커뮤니티 피드백으로 캐릭터 추가, 밸런스 조정

---

## 참고 링크

- https://store.steampowered.com/app/1942280/Brotato/
- https://brotato.wiki.spellsandguns.com/
- Blobfish 개발자 인터뷰: https://www.youtube.com/watch?v=FcJVTHBHVFQ
- 개발 과정 Reddit AMA: https://www.reddit.com/r/gamedev/
