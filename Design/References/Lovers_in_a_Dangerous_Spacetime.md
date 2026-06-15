# Lovers in a Dangerous Spacetime

리서치 날짜: 2026-06-15

## 기본 정보

- **개발사**: Asteroid Base
- **출시**: 2015 (PC/Mac), 2016 (Xbox One, PS4), 2017 (Switch)
- **공식 사이트**: https://www.asteroidbase.com/games/lovers
- **Steam**: https://store.steampowered.com/app/252110/Lovers_in_a_Dangerous_Spacetime/
- **장르**: 2D 협동 액션 / 아케이드 (로그라이트 요소 포함)
- **플레이어 수**: 1~4인 협동 (솔로 시 AI 펫 동반)

---

## 핵심 메카닉

### 공유 함선 시스템 (Shared Vessel)

게임의 핵심은 **하나의 우주선을 여러 플레이어가 나눠 조종**하는 것. 우주선에는 여러 스테이션이 있으며, 플레이어는 한 번에 하나의 스테이션만 점유하고 나머지 스테이션을 비울 수 있음.

| 스테이션 | 역할 |
|---------|------|
| 무기 (4방향) | 각 방향에 장착된 무기 발사 |
| 방어막 | 이동식 보호막 배치 및 강화 |
| 엔진 | 이동 속도·방향 제어 |
| 슈퍼 | 강력한 필살기 발동 |

2인 플레이 시: 한 명이 이동(엔진)을 맡고 다른 명이 공격(무기)을 맡는 분업이 자연스럽게 발생. 필요에 따라 즉석 역할 전환 가능.

### 역할 전환의 압박 (Role-Switching Pressure)

- 보스전에서 방어막이 급히 필요한 순간 → 공격 담당이 방어막 스테이션으로 달려가야 함
- 이동 담당이 새 무기 스테이션 시도 → 잠깐 이동 불능
- **역할 전환이 선택이자 위험 요소** — OnionCat의 "협업 강제 설계"와 동일한 철학

### 절차적 생성 은하 (Procedural Galaxy)

- 각 런마다 다른 은하 지도 생성
- 구역별 적 구성, 아이템, 보스 배치 무작위화
- 런 중 획득한 젬(Gem)으로 스테이션 업그레이드 → 런 종료 시 초기화 (퍼마데스 요소)

### 보스 패턴

- 여러 페이즈로 나뉜 보스 디자인
- 특정 공격은 방어막 없이 막기 불가능 → 양쪽 역할 필요
- 페이즈 전환 시 BGM, 비주얼 변화

---

## 플레이어들이 사랑하는 요소

1. **협동의 즐거움**: "소파 협동(couch co-op)"의 정석으로 꼽힘. 각자의 역할이 명확하고 소통이 필수
2. **네온 픽셀 비주얼**: 밝고 화려한 색감, 귀여운 우주 생명체 디자인
3. **즉각적인 피드백**: 폭발, 파티클, 화면 진동 등 타격감 탁월
4. **솔로 가능**: AI 펫이 방어막을 담당해 혼자서도 플레이 가능 (밸런스 잘 맞음)
5. **짧고 강렬한 런**: 1~2시간 안에 런 완주 가능

---

## 비판받는 부분

- 반복성: 런이 길어질수록 패턴이 단조로워짐
- 업그레이드 다양성 부족: 스테이션 커스터마이징이 제한적
- 컨트롤러 필수: 키보드+마우스로는 협동 플레이가 어색

---

## OnionCat 적용 포인트

### 1. 공유 몸체 설계 철학 직접 참조

Lovers의 "하나의 우주선 + 여러 스테이션" = OnionCat의 "하나의 몸 + 고양이(이동/근접) + 작물(조준/원거리)".

두 게임 모두 **"하나의 유닛, 두 역할"** 구조. Lovers가 보여준 핵심 교훈:
- 역할이 명확할수록 협동이 자연스럽다
- 한 역할이 비워지는 상황(무기 스테이션에 아무도 없음)이 위기감을 만든다
- OnionCat에서 Cat이 대시 중 무적이면 Crop의 방어막이 비는 순간 → 동일한 위기감 설계 가능

### 2. 역할별 강점/약점 매핑

Lovers의 스테이션 설계를 OnionCat에 번역:

| Lovers 스테이션 | OnionCat 대응 |
|---------------|-------------|
| 엔진 (이동) | Cat의 이동 + 대시 |
| 무기 (공격) | Cat의 근접 슬래시 / Crop의 원거리 투사체 |
| 방어막 | Crop의 방향성 방어막 + 패리 |
| 슈퍼 (필살기) | 미구현 — 협동 게이지 기반 합동 필살기 가능성 |

### 3. 보스전에서 역할 전환 강제 설계

Lovers 보스는 방어막 없이 막을 수 없는 공격 패턴 보유. OnionCat에서:
- 근접만 효과있는 적 + 원거리만 효과있는 적을 동시 등장 → 두 플레이어 모두 집중 필요
- 보스 특정 페이즈: 방어막 없으면 무조건 피해 → Crop 플레이어 방어막 집중 필요

### 4. 솔로 플레이 AI 펫 개념

Lovers는 솔로 플레이 시 AI 펫이 방어막을 담당. OnionCat에서 싱글 플레이 지원 시:
- AI가 Crop(또는 Cat) 역할 담당
- 단순한 AI: Crop은 가장 가까운 적 자동 조준 / 방어막은 피해 방향 자동 전개
- 솔로 모드는 난이도 쉬움 고정 추천

### 5. 시각 피드백 참고

- 방어막 히트 시 특유의 버블 이펙트 → OnionCat Crop 방어막 파티클 참고
- 폭발 파티클의 색상 언어: 적 종류별 색상 코딩 가능

---

## 기술 스택 참고 (Unity 적용)

```csharp
// 스테이션/역할 전환 구조 예시 — OnionCat 적용 가능
public enum PlayerRole { Move, Attack, Shield, Special }

public class SharedBodyController : MonoBehaviour
{
    // Cat과 Crop이 각자 다른 "역할" 담당
    // 역할 충돌 시 우선순위 결정 로직 필요
    public PlayerRole catRole = PlayerRole.Move;
    public PlayerRole cropRole = PlayerRole.Attack;
}
```

---

## 참고 링크

- 공식 사이트: https://www.asteroidbase.com/games/lovers
- Steam 페이지: https://store.steampowered.com/app/252110/
- 개발 포스트모템 (GDC): https://www.gdcvault.com/play/1022395
- Giant Bomb 리뷰: https://www.giantbomb.com/lovers-in-a-dangerous-spacetime/3030-48744/
- 인디게임 협동 설계 분석: https://www.gamedeveloper.com/design/designing-co-op-for-one-machine
