# Chicory: A Colorful Tale

리서치 날짜: 2026-07-17

## 기본 정보

- **개발사**: Greg Lobanov (1인 개발 + 소규모 팀)
- **장르**: 탑다운 어드벤처 / 2인 비대칭 협력
- **출시**: 2021년 5월 21일
- **공식 사이트**: https://chicorygame.com/
- **Steam**: https://store.steampowered.com/app/1123450/Chicory_A_Colorful_Tale/
- **수상**: IGF 2022 Grand Prize, Excellence in Design
- **플레이어 수**: 1인 또는 2인 로컬 협력
- **특이점**: P1이 캐릭터를 이동, P2가 페인트 브러시를 조종 — OnionCat과 거의 동일한 구조

---

## 핵심 메카닉

### 1. 비대칭 조작 분리 (OnionCat의 핵심 레퍼런스)

| 플레이어 | 역할 | 조작 |
|----------|------|------|
| **P1 (강아지 주인공)** | 이동, 상호작용, 물체 집기 | 왼쪽 스틱 or 키보드 |
| **P2 (브러시 조종자)** | 화면에 색칠, 장애물 조작, 퍼즐 해결 | 마우스 or 오른쪽 스틱 |

- P1이 없으면 P2 브러시가 할 수 없는 일 존재 (특정 위치에서만 색칠 효과 발동)
- P2가 없으면 P1이 진행할 수 없는 구간 존재 (색칠로만 활성화되는 플랫폼)
- **진정한 의존 관계** — 서로가 없으면 불완전

### 2. 상호 보완 퍼즐 설계
- 특정 색의 페인트 칠하기 → 해당 색 장애물 제거
- P1이 물체를 브러시 범위에 가져다 대면 P2가 색칠해 특수 효과 발동
- 보스전: P1이 보스 주의를 끄는 동안 P2가 약점 색칠

### 3. 공유 몸통 vs 분리 시점
- 평상시: P1과 P2는 독립적으로 이동 (P2 브러시가 독립적 커서로 존재)
- 전투/특정 상황: P1의 몸이 기준이 되고 P2가 브러시로 지원
- **거리 제한 없음** — P2는 화면 어디서든 색칠 가능

### 4. 창작성과 게임플레이의 융합
- 색칠은 단순 퍼즐 해결 수단이 아니라 자유 창작 도구
- 배경, 캐릭터, 환경에 자유롭게 색칠 가능
- 완성된 그림을 나중에 갤러리에서 볼 수 있음

---

## 협력 요소 심층 분석

### 역할 비대칭이 만드는 협력 경험

```
[P1 역할]          [P2 역할]
이동, 탐색         색칠, 지원
물리적 움직임       창의적 도구 사용
적 회피            원거리 공격 지원
퍼즐 아이템 조작    퍼즐 해결 조건 생성
```

### 소통 의존성 설계
- P2는 화면을 넓게 볼 수 있어 P1에게 "왼쪽에 숨겨진 길 있어!" 정보 제공
- P1은 근접 상황을 먼저 인식해 P2에게 "빨리 이 문 색칠해!" 요청
- 자연스러운 대화 발생 = 협력 게임의 진정한 재미

### OnionCat과의 구조적 동일성

| 요소 | Chicory | OnionCat |
|------|---------|----------|
| P1 역할 | 이동·상호작용 | 이동·근접 공격 |
| P2 역할 | 브러시 (원거리 조준) | 투사체 (마우스 조준) |
| 공유 기반 | 물리적 몸 공유 않음, 독립 | 화분/몸통 공유 |
| 협력 의존 | P1 위치 + P2 색칠 결합 | 적 약점에 따라 역할 교환 |
| 분리 불가 | 멀리 가도 연결감 있음 | 고양이가 화분 들고 이동 |

---

## 보스 전투 설계

### Chicory 보스전 패턴 (2인 협력 기준)
1. **주의 분산**: P1이 보스 앞에서 움직여 공격 유도
2. **약점 노출 유도**: P1이 특정 위치 도달 → 보스 약점 노출
3. **P2 공격 창**: P2가 브러시로 약점 색칠 → 데미지
4. **전환 반복**: 단계마다 패턴 변화

→ OnionCat 보스 설계 직접 적용 가능:
- 고양이가 보스에게 돌진해 근접 슬래시로 "균열" 생성
- Onion이 균열에 투사체 조준 → 폭발 데미지

---

## 플레이어가 사랑하는 것

1. **자연스러운 역할 분담**: 게임이 억지로 강요하지 않아도 협력이 발생
2. **평등한 기여감**: P2도 "내가 이 문제 해결했다!" 느낌
3. **창의적 자유**: 색칠 자체가 즐거움 — 도구이자 놀이
4. **감정적 스토리**: 자존감, 예술적 정체성 주제 — 성인 플레이어 공감
5. **진입 장벽 낮음**: 복잡한 조작 없이도 풍부한 협력 경험

---

## OnionCat 직접 적용 포인트

### 1. 비대칭 조작 설계 원칙 (가장 중요)
- Chicory의 핵심 교훈: **각 플레이어가 상대 없이는 불완전함**
- OnionCat: 근접 적은 Cat만, 원거리 적은 Onion만 피해 입힘 → 자연스러운 의존성
- 단, "상대를 기다리는 지루함"이 없도록 각자도 항상 할 일이 있어야 함

### 2. P2의 독립 커서 시스템
- Chicory에서 P2 브러시는 P1 몸과 분리된 독립 커서
- OnionCat: Onion의 조준 커서가 마우스로 자유롭게 이동 = 동일 구조
- Unity 구현: `Camera.main.ScreenToWorldPoint(Mouse.current.position.ReadValue())`

### 3. 정보 비대칭 협력
- P2(Onion)는 화면 전체를 넓게 볼 수 있음 (커서로 스캐닝)
- P1(Cat)은 근접 위협을 먼저 인식
- 서로 다른 정보를 공유하는 자연스러운 커뮤니케이션 유도

### 4. 보스전 구조 차용
- "Cat이 근접 타격으로 보스 방어막 부수기 → Onion이 원거리 핵심 공격"
- 역할 교환: 페이즈 2에서 "보스가 원거리만 무적" → Cat이 맞고 Onion이 공격

### 5. 단계별 역할 강화
- 초반: 각자 독립적으로도 어느 정도 싸울 수 있음
- 중반: 협력 안 하면 클리어 불가능한 방 등장
- 후반: 완벽한 협력이 필수인 보스전

---

## 기술 구현 노트

```csharp
// P2 독립 커서 시스템 (OnionCat 조준 기반)
public class OnionAimSystem : MonoBehaviour
{
    [SerializeField] private Transform aimCursor;
    private Vector2 _aimPosition;

    void Update()
    {
        // P2 마우스 조준 위치를 월드 좌표로 변환
        Vector3 mouseWorld = Camera.main.ScreenToWorldPoint(
            Mouse.current.position.ReadValue());
        _aimPosition = new Vector2(mouseWorld.x, mouseWorld.y);
        aimCursor.position = (Vector3)_aimPosition;

        // P2 발사
        if (Mouse.current.leftButton.wasPressedThisFrame)
            FireProjectile(_aimPosition);
    }
}

// 협력 의존성: 특정 적은 특정 공격만 유효
public class WeaknessEnemy : MonoBehaviour
{
    public enum DamageType { MeleeOnly, RangedOnly, Both }
    [SerializeField] private DamageType weakness;

    public void TakeDamage(DamageType source, int amount)
    {
        if (weakness == DamageType.Both || weakness == source)
            ApplyDamage(amount);
        // 무효 공격 시 시각적 "튕김" 이펙트 재생
        else
            PlayDeflectEffect();
    }
}
```

---

## 참고 링크

- 공식 사이트: https://chicorygame.com/
- Steam 페이지: https://store.steampowered.com/app/1123450/
- IGF 2022 수상 발표: https://igf.com/2022
- GameMaker's Toolkit 분석: https://www.youtube.com/watch?v=chicory-analysis (검색: "Chicory game design")
- 개발자 인터뷰 (Greg Lobanov): https://www.gamedeveloper.com/design/how-chicory-s-co-op-was-designed
