# Eldest Souls

리서치 날짜: 2026-08-11

## 기본 정보

- **개발사**: Fallen Flag Studio (소규모 인디팀, 핵심 인원 2명)
- **퍼블리셔**: United Label
- **출시**: 2021년 7월 29일 (PC/Switch/PS4/5/Xbox)
- **장르**: 픽셀아트 보스 러시 액션 RPG / 소울라이크
- **플랫폼**: PC(Steam), Switch, PS4/5, Xbox
- **공식 사이트**: https://www.eldestsouls.com/
- **Steam**: https://store.steampowered.com/app/1285740/Eldest_Souls/
- **Meta 점수**: 73/100 (PC 기준)
- **가격**: ~14,000원

---

## 핵심 메카닉

### 1. 패리 중심 전투 (Parry-Centric Combat)

Eldest Souls의 전투 핵심은 **퍼펙트 패리(Shatter)**다. 소울 시리즈의 패리를 보스 러시 전체 구조로 확장한 형태.

- **기본 공격**: 마우스 방향 자유 공격 (4방향 아님, 360° 자유)
- **회피**: 구르기 (i-frame 포함)
- **차지 공격**: 꾹 누르면 강공격 (적 패리 시에도 강공격으로 반격)
- **Shatter(패리)**: 특정 적 공격에 맞추면 퍼펙트 패리 → **즉각 무력화 + 강타** 기회
  - 소규모 인디팀이 만들었지만 패리 타이밍 윈도우 설계가 정교함
  - 연속 패리 → "Shatter Gauge" 누적 → 특수 기술 발동

### 2. 보스 러시 구조 (Boss Rush Design)

- **오직 보스만 존재**: 잡몹 없음, 맵 탐험 없음 → 전투에만 집중
- 보스 15마리 이상, 각각 독자적인 3~4페이즈 패턴 보유
- 보스 처치 후 능력 선택: 보스에게서 **스킬/패시브를 흡수** (빌드 다양성)
- 보스 순서 일부 자유 선택 가능 → 빌드 구성에 따른 공략 순서 전략

### 3. 능력 흡수 & 빌드 시스템

- 보스 처치 후 "고대 신의 힘" 흡수 → 런 내 능력치 선택
- **3가지 업그레이드 중 1개 선택**: 공격/방어/패리 관련 수동 또는 능동 스킬
- 다회차 플레이 시 다른 빌드로 완전히 다른 플레이 가능
- 인간형 보스 능력 흡수 → 인간형 공격기 사용 가능 (ex. 망치 내리치기)

### 4. 픽셀아트 보스 연출

- 240×135 픽셀 해상도 (극도로 낮은 해상도로 복고풍 표현)
- 보스별 고유 색상 팔레트 + 경고 이펙트 설계
- 공격 예비 동작(Telegraph): 붉은 이펙트 → 0.3~0.5초 경고 → 공격
- 페이즈 전환 시 화면 전체 암전 + 새 패턴 등장 연출

---

## 협력 요소 분석

Eldest Souls는 **싱글플레이어 전용**이다. 그러나 다음 요소들이 OnionCat의 협력 설계에 직접 응용 가능하다:

| 요소 | Eldest Souls | OnionCat 적용 방향 |
|------|-------------|-------------------|
| 패리 타이밍 윈도우 | 보스별 0.2~0.5초 다름 | Crop 패리 윈도우를 보스별로 차별화 |
| 패리 성공 보상 | Shatter Gauge + 반격 기회 | 퍼펙트 패리 시 Crop 에너지 대량 충전 |
| 보스 경고 이펙트 | 빨간 글로우 + 예비 동작 | 패리 가능 공격은 파란 글로우로 구분 |
| 빌드 선택 | 3선택 카드 | 협동 업그레이드 선택 (P1/P2 모두 관여) |
| 페이즈 전환 | 암전 + 새 패턴 | 협력 위기감 조성: 2페이즈 시 Cat만/Crop만 공략 가능한 패턴 분리 |

---

## 플레이어가 사랑하는 요소

1. **쫄깃한 패리 타이밍**: 성공 시 강렬한 피드백 (히트스톱 + 화면 흔들림 + 사운드)
2. **보스별 개성**: 15마리 모두 완전히 다른 무기/속성/페이즈 패턴
3. **소규모 팀 완성도**: 2인 개발팀이 만든 수준으로 완성도가 높아 "인디 소울라이크"의 교과서
4. **짧은 런 타임**: 보스만 존재 → 빠른 재도전 가능 → 반복 플레이 친화적
5. **진행 게이지 명확**: 보스 HP바 + 페이즈 수 표시 → 플레이어가 현재 상황을 항상 파악

---

## OnionCat 적용 포인트

### 1. 패리 윈도우 차별화
Eldest Souls에서 패리 타이밍 윈도우는 보스마다 다르다. OnionCat도:
- 기본 잡몹: 0.3초 윈도우 (쉬운 패리)
- 엘리트 적: 0.2초 윈도우
- 보스 패리 가능 공격: 0.15초 (숙련 필요)
- **시각 차별화**: 기본=노란 글로우, 엘리트=주황, 보스=빨강

### 2. 패리 성공 연출 강화
Eldest Souls의 Shatter 연출(시간 멈춤 0.15초 + 폭발 이펙트 + 효과음)을 참고:
```csharp
IEnumerator PerfectParryEffect() {
    Time.timeScale = 0f;
    yield return new WaitForSecondsRealtime(0.15f); // 히트스톱
    Time.timeScale = 1f;
    CinemachineImpulse.GenerateImpulse(0.3f);       // 화면 흔들림
    ParticleSystem.Play();                            // 폭발 파티클
    AudioSource.PlayOneShot(parrySuccessClip);       // 사운드
}
```

### 3. 보스 2인 역할 분담 패턴
Eldest Souls의 페이즈 개념을 협력 구조로 변환:
- **1페이즈**: 일반 공격 + 패리 가능 공격 혼합 → 두 플레이어 모두 활동
- **2페이즈 전환**: "갑주 강화" 연출 → Cat 슬래시만 데미지, Crop 투사체 0데미지
- **3페이즈 전환**: 원거리 패턴 폭발 → Crop 투사체만 데미지, Cat 근접 불가 구역 생성
- 각 페이즈가 명확한 역할 스위치를 강요 → 소통 필수

### 4. 소규모 팀 교훈
Fallen Flag Studio의 2인 개발 경험:
- **프로토타입 우선**: 보스 패턴은 흰 박스로 먼저 테스트, 픽셀아트는 마지막에
- **패리 가능 vs 불가 공격 구분**: 시각/청각/진동 3가지로 명확히 구분
- **카메라 주의**: 보스 스케일이 커질수록 카메라 줌아웃 로직 필수
  ```csharp
  // 보스 크기에 따른 동적 카메라 줌
  float targetOrthographicSize = Mathf.Lerp(5f, 10f, boss.scale / maxBossScale);
  Camera.main.orthographicSize = Mathf.Lerp(Camera.main.orthographicSize, targetOrthographicSize, Time.deltaTime * 2f);
  ```

---

## 참고 링크

- **공식 사이트**: https://www.eldestsouls.com/
- **Steam 페이지**: https://store.steampowered.com/app/1285740/Eldest_Souls/
- **Steam 커뮤니티 가이드**: https://steamcommunity.com/app/1285740/guides/
- **개발자 인터뷰 (2인팀 개발기)**: https://www.unitedlabel.games/eldest-souls
- **IGN 리뷰**: https://www.ign.com/articles/eldest-souls-review
- **패리 시스템 분석 영상**: YouTube에서 "Eldest Souls parry guide" 검색
- **Steam 긍정 리뷰**: 73% (복합적 평가, 난이도에 대한 의견 갈림)

---

## 총평

Eldest Souls는 "패리만으로 구성된 보스 러시"라는 극도로 집중된 게임이다.
OnionCat 개발에서 직접 쓸 수 있는 설계 요소:
1. **패리 윈도우 밸런싱** 방법론 (적 유형별 차별화)
2. **보스 역할 분담 페이즈** 설계 (협력 강제화)
3. **소규모 팀 개발 방법론** (프로토 우선, 픽셀아트 나중)
4. **피드백 강화 공식**: 히트스톱 + 흔들림 + 사운드 + 파티클 세트
