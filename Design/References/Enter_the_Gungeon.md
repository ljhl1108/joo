# Enter the Gungeon

리서치 날짜: 2026-08-01

## 기본 정보

- **개발사**: Dodge Roll
- **출시**: 2016년 4월
- **장르**: 탑다운 트윈스틱 슈터 로그라이크
- **공식 사이트**: https://dodgeroll.com/gungeon/
- **Steam**: https://store.steampowered.com/app/311690/Enter_the_Gungeon/
- **위키**: https://enterthegungeon.fandom.com/wiki/Enter_the_Gungeon_Wiki

---

## 핵심 메카닉

### 전투 시스템
- **트윈스틱 구조**: 왼쪽 스틱(이동) + 오른쪽 스틱(조준). OnionCat의 P2(Onion) 마우스 조준과 구조적으로 동일.
- **Dodge Roll(닷지 롤)**: 방향키 + 구르기 버튼 → 일정 프레임 완전 무적. 총알 패턴을 꿰뚫고 통과하는 핵심 기술.
- **테이블 뒤집기**: 장애물(테이블)을 뒤집어 탄막 차폐물로 활용. 일정 데미지 후 파괴됨.
- **탄막 디자인**: 적마다 고유한 총알 패턴. 보스는 여러 페이즈에 걸쳐 복잡한 패턴 전환.

### 총기 시스템 (400종 이상)
- **다양성**: 권총부터 레이저, 산탄총, 미사일까지. 각 총마다 고유 탄약량과 특성.
- **시너지**: 특정 총기 2개를 함께 들고 있으면 시너지 발동 → 능력 강화. 총기 간 상호작용.
- **맥마스터**: 화폐(Casings)로 총기 잠금 해제, 상점 구매.
- **Blanks**: 방 안의 모든 총알 제거. 위기 탈출 아이템. 긴장감 해소 아이템.

### 방 시스템
- **방 클리어 선행 입장**: 적이 모두 살아있으면 방 출구 잠김. 클리어 후 출구 열림 → 명확한 전투 완료 조건.
- **보물방**: 키(Key)로 열 수 있는 잠긴 방에 총기 1개 보장. 키 관리가 중요한 전략 요소.
- **상점(Bello's Shop)**: 각 층 1개. Casings로 총기·아이템·총알 구매.
- **비밀 방**: 특정 조건 충족(폭발물으로 벽 파괴 등) 시 숨겨진 방 등장.
- **미니보스 방**: 층마다 일반 적보다 강한 중간 보스 등장. 선택적 도전.

### 2인 협동 (Local Co-op)
- **Cultist**: 2P가 "Cultist"라는 별도 캐릭터로 참여. 전용 무기와 능력 보유.
- **살아있는 한 계속**: 1P가 죽어도 2P가 살아있으면 방 클리어 가능.
- **공동 자원**: 화폐(Casings)와 열쇠(Keys)는 공유. 협의가 필요한 구매 결정.
- **역할 분담 가능**: 1P가 탄막 유인, 2P가 공격에 집중하는 자연스러운 역할 분화.

### 캐릭터 & 메타 진행
- **5개 기본 캐릭터**: 각자 고유 무기와 특수 능력(Gunslinger, Hunter, Marine, Convict, Pilot).
- **과거(Past) 클리어**: 각 캐릭터가 숨긴 과거 이야기를 완성하는 숨겨진 챕터 해금.
- **Winchester**: 사격 미니게임으로 총기 보상.
- **상점 NPC 해금**: 특정 행동 시 추가 NPC 등장(예: Ox & Cadence — 무기 합성).

---

## 플레이어가 사랑하는 이유

1. **탄막 회피의 쾌감**: 복잡한 총알 패턴을 Dodge Roll로 꿰뚫는 느낌이 중독적.
2. **총기 유머와 유머러스한 게임성**: "폴리건(Polybius Remastered)", "레인보우(Unicorn Horn)" 같은 개그 총기들.
3. **방마다 긴장감**: 총알이 난무하는 방에서 완전 집중하게 만드는 설계.
4. **시너지 발견의 즐거움**: 총기 조합 시너지를 직접 발견하는 탐색 쾌감.
5. **코옵 시너지**: 2인 플레이 시 자연스러운 역할 분담 + "둘 다 살아야" 하는 긴장감.

---

## OnionCat 적용 포인트

### 1. 트윈스틱 → Cat(이동) + Onion(마우스 조준) 직접 대응
- **Gungeon**: 1인이 이동+조준 모두 담당.
- **OnionCat 적용**: Cat이 이동, Onion이 마우스로 조준/발사하는 구조가 Gungeon 2인 분리판. 기존 2P 코옵보다 더 강한 역할 비대칭으로 협동 필수성 극대화.
  - 구현 참고: `Local_Coop_Input_System.md` — P1 GamepadStick(이동), P2 Mouse(조준 Vector2) 분리 처리.

### 2. Dodge Roll 무적 → Cat 대시 IFrame 직접 레퍼런스
- **Gungeon**: Dodge Roll = 무적 구간 탈출기. 타이밍 기술.
- **OnionCat 적용**: Cat의 무적 대시가 Gungeon의 Dodge Roll과 동일 개념. **무적 판정 프레임을 Gungeon 수준(0.3~0.5초)으로 설계**, 총알을 꿰뚫고 통과하는 쾌감 제공.
  - 참고: `Dash_IFrame_System.md`

### 3. 방 클리어 잠금 → OnionCat 방 구조 채택
- **Gungeon**: 적 전멸 시 출구 오픈.
- **OnionCat 적용**: 방 입장 시 출구 잠금 → Cat+Onion 모두 협력해 클리어해야 출구 오픈. 구현: `RoomManager.LockExits()` / `UnlockExits()` 메서드.

### 4. 탄막 패턴 디자인 철학
- **Gungeon**: 각 적마다 구별되는 총알 색상/속도/형태. 읽을 수 있는 패턴으로 회피 동선 설계 가능.
- **OnionCat 적용**: 근거리 약점 적(Cat)과 원거리 약점 적(Onion) 외에, 탄막 패턴이 복잡한 적은 Onion이 파리 방패로 튕겨내거나 Cat이 대시로 뚫는 명확한 솔루션 제공. 색상 코딩으로 탄막 읽기 쉽게.

### 5. 총기 시너지 → 코옵 업그레이드 시너지
- **Gungeon**: 총기 조합으로 시너지 발동.
- **OnionCat 적용**: Cat 업그레이드 + Onion 업그레이드 특정 조합 시 "코옵 시너지" 발동. 예: Cat의 "광역 참" + Onion의 "관통 투사체" = "베기+관통 합성 연격" 발동.
  - 구현: `SynergyManager` — 양 캐릭터 현재 능력 태그 비교, 매칭 시 `CoopSynergyAbility` 활성화.

### 6. Blank → 2인 긴급 탈출 기술
- **Gungeon**: Blank로 방 안 모든 총알 제거. 소모성.
- **OnionCat 적용**: Onion의 방패 파리(패링 성공 시 반사) 외에, 양쪽 스킬 동시 발동으로 "긴급 Blank" 발동. 공유 쿨다운(긴 쿨다운) 부여.

---

## 참고 링크

- 공식 사이트: https://dodgeroll.com/gungeon/
- Steam: https://store.steampowered.com/app/311690/Enter_the_Gungeon/
- Gungeon Wiki: https://enterthegungeon.fandom.com/wiki/Enter_the_Gungeon_Wiki
- Game Maker's Toolkit — Enter the Gungeon 분석: https://www.youtube.com/watch?v=UFtFe8dR6tI
- Dodge Roll 개발 인터뷰 (GDC 2016): https://www.gdcvault.com/play/1023573
