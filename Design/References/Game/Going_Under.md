# Going Under

리서치 날짜: 2026-08-18

## 기본 정보

- **장르**: 로그라이트 액션 RPG
- **개발사**: Aggro Crab
- **출시**: 2020년 9월 24일
- **플랫폼**: PC, PS4, Xbox One, Switch
- **공식 사이트**: https://aggrocrab.com/going-under
- **Steam**: https://store.steampowered.com/app/1267820/Going_Under/
- **위키**: https://going-under.fandom.com/wiki/Going_Under_Wiki

---

## 핵심 메카닉

### 1. 물리 기반 즉흥 무기 시스템
- **모든 주변 오브젝트를 무기로 사용** — 노트북, 화분, 자전거, 검도 검, 경광봉 등 수백 종류
- 무기마다 고유한 물리 특성: 노트북은 범위 타격, 식물 화분은 투척 후 폭발, 자전거는 휘두를 때 원심력
- 무기 내구도 존재 → 소진 시 파괴됨, 항상 다음 무기를 탐색해야 하는 긴장감
- **온도**: 뜨거운 커피·냉각팩 등 특수 속성 무기, 환경 오브젝트와 결합

### 2. 스킬 캡슐 시스템 (Perks)
- 층마다 스킬 캡슐 획득: 런 기간에만 유효한 소극적 보너스
- 스킬끼리 시너지 형성 — 예: "음료 투척 +50% 데미지" + "음료 소비 시 이동속도 증가"
- 스킬 선택이 플레이 스타일을 규정함 (무기 특화 vs. 근접 vs. 투척)

### 3. 앱/파워업 시스템
- **Apps** = 적이 드롭하는 액티브 아이템 (일시적 버프, 피해 반사 등)
- 인벤토리 슬롯 제한 → 선택과 집중 필요

### 4. 고용주 시스템 (Mentors / Sponsors)
- 층별로 과거 스타트업의 유령 캐릭터가 멘토 역할
- 멘토의 요청(도전)을 수행하면 런 내 보너스 스킬 제공
- 메타 서사: 실패한 스타트업들의 '던전' 안에서 이유를 찾는 스토리

### 5. 영구 진행 (메타 프로그레션)
- 런 실패 시 '경험' 형태로 복귀 → 잠금 해제 아이템, 시작 스킬 풀 확장
- 특정 보스 처치 후 새로운 게임 모드 오픈

---

## 협력 요소

Going Under는 싱글플레이 기반이지만, 설계 철학에서 OnionCat이 참고할 점이 많다:
- **즉흥 무기**: 협력에서 "누가 어떤 무기를 쓸지" 분업하는 재미
- **멘토 도전 이원화**: P1(Cat)은 근접 도전, P2(Crop)은 원거리 도전 각각 수행
- **역할 분리**: 무기 유형 단순화 (Cat=근접/투척, Crop=원거리/방어)로 Going Under의 물리 무기 다양성을 협력 맥락으로 변환 가능

---

## 플레이어가 사랑하는 것

1. **물리 장난감 상자 같은 느낌** — 어떤 물건이든 집어 던질 수 있는 자유도
2. **스타트업 풍자 유머** — 현실 IT 업계 밈 충만 (NFT 보스, 긱 이코노미 보스 등)
3. **스킬 조합 발견** — 뜻밖의 시너지를 발견할 때의 쾌감
4. **접근성** — 짧은 런 타임(15~25분), 낮은 진입 장벽

---

## OnionCat 적용 포인트

| Going Under 요소 | OnionCat 적용 아이디어 |
|---|---|
| 임시 무기 → 내구도 소진 | Crop의 투사체를 "씨앗" 자원 기반으로 제한, 방마다 자원 보충 |
| 물리 투척 무기 | Cat이 적을 집어 Crop의 투사체 방향으로 던지는 합체 콤보 |
| 멘토 챌린지 시스템 | 방마다 선택적 보너스 목표: "근접만으로 클리어" → Cat 특화 보상 |
| 스킬 캡슐 런 빌드 | OnionCat 업그레이드 선택지: Cat 전용 / Crop 전용 / 공용 3분류 |
| 스타트업 던전 서사 | OnionCat 세계관: "마법 왕국의 각 층은 다른 마법사의 실패 실험실" |

---

## 기술 참고 사항

- 오브젝트 물리: Unity의 `Rigidbody2D` + `AddForce`로 투척 궤적 구현
- 내구도 시스템: `WeaponData` ScriptableObject에 `durability` 필드, 히트마다 감소
- 씬 내 스폰된 프롭을 무기로 변환: `IInteractable` 인터페이스 + 레이어 태그

---

## 참고 링크

- [Steam 페이지](https://store.steampowered.com/app/1267820/Going_Under/)
- [Aggro Crab 공식](https://aggrocrab.com/going-under)
- [Going Under 위키](https://going-under.fandom.com/wiki/Going_Under_Wiki)
- [GDC 발표: 물리 무기 설계](https://www.gdcvault.com/)
- [리뷰: Rock Paper Shotgun](https://www.rockpapershotgun.com/going-under-review)
