# Rotwood

리서치 날짜: 2026-06-28

## 기본 정보

- **개발사**: Klei Entertainment
- **장르**: Co-op 로그라이크 액션 RPG
- **플랫폼**: PC (Steam Early Access)
- **공식 사이트**: https://www.klei.com/games/rotwood
- **Steam**: https://store.steampowered.com/app/2015270/Rotwood/
- **위키**: https://rotwood.fandom.com/wiki/Rotwood_Wiki

---

## 핵심 메커니즘

### 협동 구조
- 최대 4인 로컬/온라인 Co-op
- 각 플레이어가 독립적인 클래스를 선택해 팀 구성
- 공유 체력(던전 입장 횟수 기반 라이프) 시스템
- 한 명이 죽어도 다른 플레이어가 부활 아이템으로 살릴 수 있음

### 클래스 시스템
- **Swordfighter**: 근접 공격 특화, 대쉬/파리 기반
- **Witch**: 원거리 마법 공격, AoE 스킬
- **Brawler**: 강타·잡기(Grab) 중심 근접
- **Seedling**: 서포트+원거리 하이브리드 (식물 기반)
- 각 클래스는 고유 기본기 3종 + 필살기 → OnionCat의 캣/어니언 역할분담과 유사 구조

### 전투 시스템
- **타이밍 기반 반격(Dodge & Counter)**: 공격 직전 회피 → 카운터 보너스 대미지
- **히트스톱 + 넉백**: 적에 맞을 때 뚜렷한 타격감 연출
- **무기 강화**: 방 클리어 후 무기를 임시 강화(Skill 슬롯 추가)
- **연계 콤보**: 기본기 → 스킬 순서로 연계하면 추가 효과 발동

### 방·던전 구조
- 선형 방 진행(분기는 제한적) → 깊이감보다 전투 집중도 우선
- 방 클리어 후 보상 선택(무기 업그레이드, 소비 아이템)
- 보스룸 직전 상점(Canteen) 존재
- 각 바이옴마다 다른 타일셋·적 세트

### 로그라이크 요소
- 런 내 업그레이드는 런 종료 시 초기화
- 영구 해금(Unlocks): 새 무기, 새 스킬 슬롯, NPC 대화를 통한 설정 확장
- 시작 조건 영구 개선(메타 프로그레션) — 초보자 친화적 난이도 곡선

---

## 플레이어들이 좋아하는 요소

1. **묵직한 타격감**: 히트스톱·카메라 흔들림·파티클이 통합된 피드백 루프
2. **클래스 다양성**: 플레이 스타일이 크게 달라 Co-op 시너지 높음
3. **Klei 특유의 아트**: 손그림 느낌의 애니메이션, 어두운 동화 분위기
4. **낮은 진입장벽**: 조작법 단순, Co-op으로 캐주얼 플레이 가능
5. **빠른 런**: 한 런 30~50분 내 완결 → 단기 세션 플레이에 적합

---

## OnionCat 적용 포인트

| Rotwood 요소 | OnionCat 적용 |
|---|---|
| 클래스별 역할 분담(근접/원거리) | 캣(근접 슬래시·대쉬) vs 어니언(원거리·실드) 고유성 강화 |
| 타이밍 카운터 | 어니언 방패 패리 타이밍 윈도우 설계 참고 |
| 방 클리어 후 즉시 보상 선택 | 업그레이드 선택 화면 흐름 (런 내 3택1) |
| 부활 아이템 | 2인 Co-op에서 한 명 쓰러졌을 때 구출 메커니즘 고려 |
| 단순 조작 + 깊은 타이밍 | 초보 개발자가 구현하기 좋은 '단순 입력 → 복잡한 결과' 패턴 |
| 방 내 물약/소비 아이템 | 런 중 소비 자원으로 긴장감 유지 |

### 특히 참고할 전투 피드백 레이어
```
적 피격 → 히트스톱(0.05~0.1초) → 파티클 스폰 → 카메라 미세 진동 → 넉백 적용
```
이 4단계 피드백 파이프라인을 OnionCat 전투에 그대로 적용 가능.

---

## 참고 링크

- [Rotwood Steam 페이지](https://store.steampowered.com/app/2015270/Rotwood/)
- [Rotwood 공식 사이트](https://www.klei.com/games/rotwood)
- [Rotwood Wiki](https://rotwood.fandom.com/wiki/Rotwood_Wiki)
- [Klei 개발 블로그](https://forums.kleientertainment.com/game-updates/rotwood/)
- [Combat feel 분석 GDC 류 자료 참고](https://www.gamedeveloper.com/design/the-art-of-the-hit-stop)
