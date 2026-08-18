# Wizard with a Gun

리서치 날짜: 2026-08-18

## 기본 정보

- **장르**: 협력 생존 크래프팅 로그라이트 액션
- **개발사**: Galvanic Games
- **출시**: 2023년 10월 17일
- **플랫폼**: PC, PS5, Xbox Series X/S, Switch
- **공식 사이트**: https://galvanicgames.com/wizard-with-a-gun
- **Steam**: https://store.steampowered.com/app/1150530/Wizard_with_a_Gun/
- **위키**: https://wizardwithaguns.fandom.com

---

## 핵심 메카닉

### 1. 협력 중심 설계 (1~2인 온라인/로컬 코옵)
- 두 플레이어가 **동일한 세계를 탐험** — 물리적으로 한 공간에 공존
- **역할 분업 유도 없음** — 둘 다 총을 들고 다르게 플레이 가능
- "혼자도 가능하지만 둘이 더 빠르고 안전" 방식

### 2. 총 커스터마이징 (총알 크래프팅)
- **총알 = 마법 원소 조합**: 화염 + 얼음 = 증기 특수 효과
- 총알 유형을 조합해 독특한 파이어암 제작 (속성, 관통, 유도, 폭발 등)
- 총마다 슬롯 구성 → 빌드 다양성

### 3. 천재 (Shattered Realm) - 로그라이크 런
- **리셋 가능한 세계**: 세계가 카오스로 무너지면 리셋 → 영구 자원만 남음
- 런 단위가 아닌 "세계 단위" 붕괴 → 전통적 로그라이크보다 긴 호흡
- 리셋 사이에 베이스캠프(타워) 업그레이드

### 4. 기지 건설 및 영구 진행
- 탑(베이스캠프)에 워크숍, 농장, 라이브러리 건설
- 런 중 수집한 재료 → 기지 귀환 후 영구 업그레이드
- "로그라이크 수집" + "베이스 빌딩" 혼합

### 5. 시간 압박 메카닉
- 세계는 점점 카오스에 잠식됨 → 무한정 탐험 불가
- 잠식 진행도 UI가 항상 표시 → 탐험 vs. 귀환 판단 긴장감

---

## 협력 요소 심화 분석

### 잘 작동하는 협력 디자인
| 요소 | 설명 |
|---|---|
| 독립적 총알 관리 | 각 플레이어가 자신만의 탄약 관리 → 서로 의존 없음 |
| 재료 공유 경제 | 한 플레이어가 재료 채집, 다른 플레이어가 적 처치 → 자연 분업 |
| 부활 시스템 | 한 플레이어 쓰러지면 다른 플레이어가 구조 → 협력 필요 |
| 포탈 함께 이동 | 두 플레이어 모두 준비됐을 때 귀환 → 타이밍 협력 |

### OnionCat과의 차이점
- Wizard는 두 독립 캐릭터 → OnionCat은 **하나의 몸을 공유**
- Wizard는 생존 위주 → OnionCat은 전투/전략 위주
- Wizard는 장기 런 → OnionCat은 짧은 방 단위 로그라이크

---

## 플레이어가 사랑하는 것

1. **총알 조합 빌드 다양성** — 수백 가지 조합, 발견의 재미
2. **협력 친화적 진입 장벽** — 배우기 쉽고 함께 즐기기 좋음
3. **세계 붕괴 서사** — 카오스와 싸우는 마법사 이야기의 독특한 긴장감
4. **비주얼 아트 스타일** — 픽셀아트 + 마법 서양 판타지 혼합

---

## OnionCat 적용 포인트

| Wizard with a Gun 요소 | OnionCat 적용 아이디어 |
|---|---|
| 총알 원소 조합 | Crop 투사체: 기본 씨앗 + 수집 마법 원소 조합 → 화염/얼음/번개 씨앗 |
| 시간 압박 카오스 잠식 | 방 클리어 시간 초과 시 "마나 오염" 게이지 상승, 가득 차면 방 강화 |
| 재료 공유 경제 | Cat이 근접 처치 시 재료 드롭, Crop이 원거리 처치 시 마나 구슬 드롭 → 서로 다른 자원 |
| 부활 협력 | OnionCat 부활: Cat이 쓰러지면 Crop 단독 도전 가능하지만 이동이 불안정 |
| 기지 귀환 업그레이드 | 런 사이 허브 씬에서 Cat/Crop 각각 업그레이드 트리 선택 |

---

## 기술 참고 사항

- 원소 조합 시스템: `BulletData` ScriptableObject에 `ElementType[]` 배열, 조합 결과는 Dictionary 룩업
- 잠식 게이지: `WorldCorruptionManager` 싱글톤, `Update()`에서 초당 증가량 조절
- 씬 지속 데이터: `DontDestroyOnLoad`로 기지 상태 유지, 런 리셋 시 런 전용 데이터만 초기화

---

## 참고 링크

- [Steam 페이지](https://store.steampowered.com/app/1150530/Wizard_with_a_Gun/)
- [Galvanic Games 공식](https://galvanicgames.com/wizard-with-a-gun)
- [위키](https://wizardwithaguns.fandom.com)
- [IGN 리뷰](https://www.ign.com/articles/wizard-with-a-gun-review)
- [PC Gamer 리뷰](https://www.pcgamer.com/wizard-with-a-gun-review/)
