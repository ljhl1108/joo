# Crawl

리서치 날짜: 2026-06-28

## 기본 정보

- **개발사**: Powerhoof
- **장르**: 비대칭 멀티플레이어 로그라이크 던전 크롤러
- **플랫폼**: PC (Steam), 닌텐도 스위치
- **공식 사이트**: https://www.powerhoof.com/crawl/
- **Steam**: https://store.steampowered.com/app/293780/Crawl/
- **위키**: https://crawl.fandom.com/wiki/Crawl_Wiki

---

## 핵심 메커니즘

### 비대칭 Co-op 구조 (1 Hero vs N Haunts)
- **Hero**: 한 플레이어가 영웅을 담당. 던전을 탐험하며 레벨업, 아이템 수집
- **Haunts**: 나머지 플레이어(최대 3명)가 '유령'이 되어 몬스터와 트랩을 조종
- **역할 교체**: Haunt가 조종하는 몬스터가 Hero를 처치하면 그 Haunt가 새 Hero가 됨
- **최종 보스**: 가장 오래 Hero를 못 해본 Haunt가 최종 보스를 조종

### Hero 성장 시스템
- 몬스터 처치 → 경험치 → 레벨업 (최대 레벨 10)
- 상점에서 무기/아이템 구매 (골드 수집)
- 레벨이 높을수록 Haunt의 보스 단계도 강해짐 → 자연스러운 밸런싱

### Haunt 메커니즘
- 방 안의 포털/오브에 빙의 → 몬스터 스폰·조종
- 트랩(스파이크, 화염 바닥) 활성화
- 몬스터 종류: 일반 근접, 원거리, 특수 스킬형
- 빙의 유지 비용(Wrath) 시스템 → 무한 스폰 방지

### 던전 구조
- 총 5개 층, 층마다 테마(숲·묘지·용암 등)
- 각 방: 전투 방 / 상점 방 / 보스 방
- Hero가 탈출구 찾아 다음 층으로 이동
- Haunt는 Hero가 탈출 전까지 최대한 많이 처치 시도

### 승리 조건
- Hero가 레벨 10 달성 후 최종 보스 처치 → Hero 플레이어 승리
- Haunt가 Hero를 처치하고 자신이 Hero가 되어 최종 승리 → Haunt→Hero 전환 플레이어 승리

---

## 플레이어들이 좋아하는 요소

1. **긴장 역전의 쾌감**: 영웅이었다가 유령이 됐다가 다시 영웅 — 모두가 이길 기회
2. **비대칭 전략**: Hero는 생존·성장 전략, Haunts는 협동해 Hero 잡기 전략
3. **사회적 게임플레이**: "나 몬스터 뒤에서 스폰할게 막아!" 자연스러운 소통
4. **픽셀아트 + 도트 애니메이션**: 작은 팀이 만든 감성적 그래픽
5. **짧은 런**: 1시간 내외 완결, 파티 게임으로 반복 플레이 적합

---

## 비대칭 Co-op 설계 철학 (OnionCat 적용 핵심)

### 정보 비대칭
- Hero는 자신 주변만 보임(시야 제한)
- Haunts는 전체 맵 조감 가능
- → OnionCat에서 Cat(이동)과 Onion(원거리·조준)의 정보 역할 분리로 참고 가능

### 능력 비대칭
- Hero는 강하지만 혼자 / Haunts는 약하지만 협동
- → OnionCat: 캣(근접 무적 대쉬)과 어니언(원거리+방어)이 서로 보완하는 구조와 유사

### 자연스러운 밸런싱
- Hero가 강해질수록 Haunt의 몬스터도 자동으로 강해짐
- → OnionCat 적 설계: 플레이어 파워 지표에 따라 적 HP·공격 조정 참고

---

## OnionCat 적용 포인트

| Crawl 요소 | OnionCat 적용 |
|---|---|
| 비대칭 역할 명확화 | 캣과 어니언 각자의 '할 수 있는 것 / 못 하는 것' 명확히 정의 |
| 역할 고유 시야/정보 | 어니언 마우스 조준(화면 끝까지 겨냥) vs 캣 근접 시야 → UI로 시각화 |
| 적 취약점 분류 | 근접에만 약한 적 / 원거리에만 약한 적 → 플레이어 협력 강제 |
| 짧고 긴장감 있는 런 | OnionCat 런 목표: 30~45분 내 완결 구조 설계 |
| 스폰 포인트 방어전 | 방 내 캣이 근접 적 막는 동안 어니언이 원거리 적 처리 — 역할 분담 방 설계 |
| 비대칭 업그레이드 | 캣 전용 업그레이드(슬래시 범위, 대쉬 쿨) vs 어니언 전용(투사체 수, 실드 크기) |

---

## 참고 링크

- [Crawl Steam 페이지](https://store.steampowered.com/app/293780/Crawl/)
- [Powerhoof 공식 사이트](https://www.powerhoof.com/crawl/)
- [Crawl Wiki](https://crawl.fandom.com/wiki/Crawl_Wiki)
- [비대칭 멀티플레이어 설계 분석 — Game Maker's Toolkit](https://www.youtube.com/c/GameMakersToolkit)
- [Crawl 리뷰 — RPS](https://www.rockpapershotgun.com/crawl-review)
