# The Last Spell

리서치 날짜: 2026-09-01

## 기본 정보

- **개발사**: Ishtar Games (프랑스 인디)
- **장르**: 전술 로그라이크 / 타운 디펜스 / 픽셀아트 RPG
- **출시**: Early Access 2021 → 정식 출시 2023년 5월
- **공식 사이트**: https://ishtargames.fr/the-last-spell/
- **Steam**: https://store.steampowered.com/app/1105670/The_Last_Spell/
- **위키**: https://the-last-spell.fandom.com/wiki/The_Last_Spell_Wiki
- **플레이어 수**: 1~4인 로컬/온라인 협동
- **플랫폼**: PC, Nintendo Switch

---

## 핵심 시스템

### 낮/밤 루프 (Day/Night Loop)

- **낮(Day)**: 타운 건물 수리·강화, 영웅 장비 구매, 스킬 업그레이드
- **밤(Night)**: AP(Action Point) 기반 턴제 전투로 몰려오는 적 웨이브 격퇴
- 15~20일 밤을 버티면 클리어, 매 밤마다 적 수·강도 상승
- 타운 건물 파괴 시 방어력 영구 감소 → 영웅과 거점 동시 관리

### AP 기반 턴제 전투

- 각 영웅은 AP 풀을 보유, 이동/공격/스킬 각각 AP 소모
- 적도 AP 시스템 적용 → 적 이동 궤적 예측 가능
- 한 턴 안에 모든 영웅+적이 입력 후 동시 실행 → 실시간에 가까운 박진감
- AP 배분 전략이 승패를 결정

### 적 취약점 시스템 ★

- 적마다 **물리 저항 / 마법 저항** 수치가 다름
- 물리 면역 적: 마법 공격만 유효
- 마법 면역 적: 물리 공격만 유효
- 혼합 저항 적: 두 타입을 조합해야 효율적 처치
- UI에 저항 수치를 명확하게 표시 → 플레이어가 즉시 전략 수정

### 협동 메카닉

- 공유 타운 HP (하나의 거점을 함께 방어)
- 영웅 독립 이동 → 화면 구역 분담 자연 발생
- 영웅 간 시너지 스킬: 한 영웅의 디버프를 다른 영웅이 폭발 활성화
- 공유 자원(Gold)으로 업그레이드 → 협의/합의 필요

### 메타 진행

- 타운 건물 업그레이드는 런 간 영구 보존
- 특정 조건 달성 시 새 영웅 클래스·무기 타입 잠금 해제
- 각 지역(맵)마다 전용 적·보스·아이템 풀 보유

---

## 플레이어가 좋아하는 요소

1. **웨이브 긴장감** — 밤이 길어질수록 화면이 적으로 가득 차는 극적 압박
2. **취약점 기반 역할 분담** — 각 영웅이 자신이 효과적인 적에 집중하는 자연스러운 협동
3. **픽셀아트 퀄리티** — 상세한 적 스프라이트, 화려한 마법 이펙트
4. **빌드 다양성** — 런마다 다른 무기·스킬 조합으로 플레이스타일 변화
5. **공유 목표의 긴장감** — 타운이 무너지면 함께 지는 구조 → 협동 집중도 상승

---

## OnionCat 적용 포인트

### 1. 적 취약점 이분법 → OnionCat 핵심 기둥 직접 구현 참고

- The Last Spell의 물리/마법 이분법 = OnionCat의 근접/원거리 이분법
- 취약점이 있으면 "억지 협동 메카닉" 없이도 역할 분담이 자연 발생
- **구현 힌트**:
  ```csharp
  public enum DamageType { Melee, Ranged }

  public class EnemyStats : MonoBehaviour
  {
      [SerializeField] private float meleeResistance;   // 0=취약, 1=면역
      [SerializeField] private float rangedResistance;
      
      public float GetDamageMultiplier(DamageType type) =>
          type == DamageType.Melee ? (1f - meleeResistance) : (1f - rangedResistance);
  }
  ```
- 적 스프라이트에 색상 또는 소형 아이콘 오버레이로 취약 타입 직관 표시

### 2. 낮/밤 리듬 → "안전 방 + 전투 방" 교대 배치

- The Last Spell의 낮=회복·준비, 밤=전투를 OnionCat에서는 방 단위로 구현
- 전투 방 클리어 → 상점/업그레이드 방(안전 방) → 전투 방의 반복
- 안전 방에서 업그레이드 선택 + 체력 회복 → 다음 전투 방에서 긴장감 회복

### 3. 웨이브 에스컬레이션 → 방 내 적 수 조절

- 층이 깊어질수록 방 입장 시 스폰되는 적 수 증가
- 마지막 웨이브에서 대규모 적 등장 연출 (적 스폰 완료 후 문 오픈) → 클리어 카타르시스

### 4. 시너지 스킬 아이디어 → 두 플레이어 연계기

- P1 슬래시가 적을 "기절" 상태로 만들면 P2 투사체가 크리티컬 데미지 적용
- 두 플레이어의 입력이 일정 시간 내에 같은 적에게 들어오면 "공명 폭발" 발동
- 협동이 전략적 이득으로 이어지는 구조

---

## 참고 링크

- 공식 사이트: https://ishtargames.fr/the-last-spell/
- Steam: https://store.steampowered.com/app/1105670/The_Last_Spell/
- 위키: https://the-last-spell.fandom.com/wiki/The_Last_Spell_Wiki
- 리뷰 (Rock Paper Shotgun): https://www.rockpapershotgun.com/the-last-spell-review
- 게임 분석 영상: YouTube "The Last Spell Review" 검색
