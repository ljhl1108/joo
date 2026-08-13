# Neon Chrome

리서치 날짜: 2026-08-13

## 기본 정보

- **개발사/퍼블리셔**: 10tons (핀란드)
- **출시**: 2016년 5월 (PC), 이후 콘솔/모바일
- **플랫폼**: PC, PS4, Xbox One, Switch, iOS, Android
- **공식 사이트**: https://10tons.com/neon-chrome/
- **Steam**: https://store.steampowered.com/app/286940/Neon_Chrome/
- **장르**: 탑다운 트윈스틱 슈터 + 로그라이트, 최대 4인 협동

---

## 핵심 메카닉

### 1. 탑다운 + 슈터 + 로그라이트 3요소 통합
- **무작위 레벨 생성**: 타일 기반, 매 런 다른 방 배치
- **클래스 선택**: 런 시작 시 캐릭터 클래스(저격수/해커/엔지니어/돌격대 등) 선택 → 기본 스탯·능력 다름
- **영구 업그레이드**: 런에서 벌어들인 Credits로 메타 업그레이드 잠금 해제

### 2. 협동 시스템 (OnionCat에 가장 직접적인 레퍼런스)
- **최대 4인 로컬/온라인 협동** — 화면 분할 없이 하나의 카메라 공유
- 각 플레이어 **독립 클래스 + 독립 체력** — 한 명이 죽어도 런이 계속됨(파트너 부활 가능)
- **역할 분업**: 저격수 뒤에서 커버, 돌격대 앞에서 적 끌기 → 시너지 발생
- **화면 내 위치 제한**: 모든 플레이어가 하나의 카메라 안에 있어야 함 → 자연스러운 협동 압박

### 3. 파괴 가능한 환경
- **거의 모든 벽/오브젝트 파괴 가능** — 적 뒤의 벽을 폭발물로 부수면 새 경로 생성
- 환경 파괴가 전략적 선택지가 됨 (우회로 개척, 지뢰 유발 등)

### 4. 적 & 방 설계
- **방 진입 시 즉각 전투** — 특별한 "방 잠금" 없이 적이 자연스럽게 등장
- **Enhancer**: 방 내 특수 오브젝트 파괴 시 특수 효과 부여 (속도 증가, 무한 탄약 등)
- 보안 해킹 단말기 — 조작 시 적 비활성화 또는 드론 아군화 → 비전투 해결책

---

## 협동 디자인 특징

### 카메라 공유 협동의 핵심 원칙
Neon Chrome의 가장 큰 교훈: **한 카메라에 모든 플레이어를 수용하는 것 자체가 협동 메카닉**

1. **자연스러운 근접 유지**: 혼자 너무 앞서가면 카메라 중심 이탈 → 파트너 위험
2. **공유 시야각**: 적의 위치 정보가 자동 공유 — 커뮤니케이션 부담 감소
3. **죽은 플레이어 부활**: 파트너가 특정 위치에서 행동으로 부활 가능

### 역할 비대칭 없이도 협동감이 느껴지는 이유
- **클래스별 능력 차이**가 상황에 따라 다른 플레이어가 주역이 됨
- 적의 배치(원거리 집단 방 vs 근접 집단 방)가 자연스럽게 역할을 부여
- 체력이 낮아지면 다른 플레이어가 적을 끌어내야 하는 구조적 의존

---

## 플레이어가 사랑하는 것

1. **진입 장벽 낮은 협동** — 복잡한 시스템 없이 즉시 협동이 체감됨
2. **런당 10~20분의 쾌적한 길이** — 부담 없이 여러 번 시도
3. **고요한 사이버펑크 분위기** — 어둡지만 깔끔한 픽셀 아트 스타일
4. **파괴 가능한 환경** — 예측 불가능한 창의적 해결이 가능

---

## OnionCat 적용 포인트

| Neon Chrome 요소 | OnionCat 적용 |
|---|---|
| 하나의 카메라 공유 | 두 플레이어가 한 몸 → 카메라 단일 추적점은 오히려 더 자연스러움 |
| 클래스별 능력 차이 | P1(근접-대시) vs P2(원거리-방패)의 역할 비대칭이 이미 내재 |
| 방 내 Enhancer 오브젝트 | 방 내 특수 오브젝트 파괴 시 일시적 버프 발생 (속도 UP, 데미지 UP 등) |
| 파트너 부활 지점 | P2가 P1의 근접 공격 지원 시 부활 게이지 복구 (복합 입력 활용) |
| 근접/장거리 방 배치 | 방마다 "근접 전용 약점 적 다수" 방 vs "원거리 전용 약점 적 다수" 방 교대 배치 |

### Enhancer 오브젝트 구현 힌트
```csharp
public class RoomEnhancer : MonoBehaviour
{
    [SerializeField] private BuffType buffType; // Speed, Damage, Invincible
    [SerializeField] private float duration = 5f;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.TryGetComponent<PlayerBuffHandler>(out var handler))
        {
            handler.ApplyBuff(buffType, duration);
            Destroy(gameObject);
        }
    }
}
```

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/286940/Neon_Chrome/
- 공식 사이트: https://10tons.com/neon-chrome/
- 10tons 개발자 인터뷰 (Gamasutra): https://www.gamedeveloper.com/design/the-making-of-neon-chrome
- 협동 로그라이트 디자인 분석: https://www.pcgamer.com/neon-chrome-review/
- Neon Chrome Wiki: https://neon-chrome.fandom.com/wiki/Neon_Chrome_Wiki
