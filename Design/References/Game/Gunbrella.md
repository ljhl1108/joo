# Gunbrella

리서치 날짜: 2026-08-29

## 기본 정보

- **개발사**: Doinksoft
- **퍼블리셔**: Devolver Digital
- **출시**: 2023년 9월
- **플랫폼**: PC (Steam), Nintendo Switch
- **장르**: 2D 횡스크롤 액션 로그라이트 / 누아르 액션
- **공식 사이트**: https://www.devolverdigital.com/games/gunbrella
- **Steam**: https://store.steampowered.com/app/1580690/Gunbrella/
- **픽셀아트 스타일**: 어두운 누아르 톤, 흑백/회색 위주의 픽셀아트

---

## 핵심 메카닉

### 1. 건우산(Gunbrella) — 무기와 이동의 완전한 융합
- 주인공은 총+우산 하이브리드 무기 하나만 사용
- **총격 모드**: 산탄 계열 근~중거리 공격
- **우산 전개(Open Umbrella)**: 공중에서 낙하 속도 감속 / 글라이딩
- **우산으로 투사체 반사**: 앞으로 우산을 펼치면 날아오는 총알을 막고 방향 전환 반사 가능 (패리 메카닉)
- **대시 샷**: 우산을 뒤로 쏘아 추진력으로 앞으로 돌진
- 한 가지 아이템으로 "이동 + 방어 + 공격" 전부 처리 → 조작 깊이가 매우 높음

### 2. 절차적 레벨 + 바이옴
- 완전 랜덤보다 반(半)고정 레이아웃 + 무작위 방 배치 혼합
- 다양한 바이옴(습지, 도시 유적, 공장 등) 각각의 시각적 정체성 강함
- 각 지역마다 고유 적, 함정, 환경 요소 존재

### 3. 업그레이드 시스템
- 런 중 획득한 변형 탄약 / 부품으로 건우산 성능 수정
- 예: "더블 배럴", "폭발 탄착", "리코쳇 탄"
- 조합 시너지보다 단일 빌드 집중형

### 4. 패리/반사 메카닉 (OnionCat 관련도 ★★★)
- 적 투사체를 우산으로 막으면 공짜 반사탄 생성
- 반사 타이밍이 완벽하면 강화 반사탄 발사 (퍼펙트 패리)
- **OnionCat Player 2의 방패 패리 메카닉과 직결**

### 5. 보스 설계
- 각 구역 마지막에 유니크 보스 등장
- 보스의 공격 패턴을 분석해 패리 / 닷지 / 카운터 타이밍 학습
- 체력 게이지가 낮아질수록 페이즈 전환 (공격 패턴 변화)

---

## 플레이어가 사랑하는 요소

1. **무기 하나로 모든 것을 해결하는 깔끔한 철학** — 인벤토리/장비 복잡성 없이 조작 깊이 극대화
2. **누아르 픽셀아트 미학** — 흑백 톤에 포인트 컬러 사용, 강한 시각적 정체성
3. **패리의 쾌감** — 투사체를 튕겨내는 물리적 피드백과 사운드 디자인이 매우 만족스러움
4. **레벨 디자인의 선택지** — 상점 방, 비밀 방, 지름길 등 탐험 보상
5. **단기 플레이 적합** — 1~2시간 짧은 런 길이로 반복 플레이 부담 없음

---

## OnionCat 적용 포인트

| 영역 | Gunbrella 참고 아이디어 | 적용 방법 |
|------|------------------------|-----------|
| **Player 2 패리** | 퍼펙트 패리 → 강화 반사탄 | 패리 성공 시 EnemyProjectile을 velocity 반전 + 데미지 2배로 돌려보냄 |
| **무기-이동 융합** | 우산 후진 샷 추진 | Player 1 대시 방향에 따라 공격 판정이 달라지는 "차지 슬래시 + 대시" 연계 아이디어 |
| **단일 무기 철학** | 아이템 없이 조작 깊이 | 업그레이드를 "도구 추가"가 아닌 "기존 조작의 변형"으로 설계 → 학습 부담 감소 |
| **패리 반사 투사체** | 막힌 탄이 적을 향해 날아감 | Player 2 방패 활성 중 적 탄이 닿으면 ShieldReflectProjectile 스크립트로 velocity = reflect(incoming, normal) |
| **픽셀아트 분위기** | 어두운 배경 + 포인트 컬러 | OnionCat의 픽셀아트도 배경을 어둡게 유지하고 캐릭터/적에 채도 높은 포인트 컬러 사용 |
| **반(半)고정 레벨** | 바이옴별 고정 구조 + 무작위 배치 | 방 프리팹을 "타입별(일반/보물/상점)"로 나누어 가중치 선택, 전체 순서는 사전 정의 |

---

## 구현 힌트 (Unity)

```csharp
// 투사체 반사 기초 로직
void OnTriggerEnter2D(Collider2D other)
{
    if (other.CompareTag("EnemyProjectile") && shieldActive)
    {
        Rigidbody2D rb = other.GetComponent<Rigidbody2D>();
        Vector2 normal = (other.transform.position - transform.position).normalized;
        rb.linearVelocity = Vector2.Reflect(rb.linearVelocity, normal) * reflectMultiplier;
        other.tag = "PlayerProjectile"; // 팀 변경
    }
}
```

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/1580690/Gunbrella/
- Devolver Digital 공식: https://www.devolverdigital.com/games/gunbrella
- Doinksoft (개발사): https://doinksoft.com/
- 패리 메카닉 분석: Steam 리뷰 및 커뮤니티 가이드 참고
