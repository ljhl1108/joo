# Revita

리서치 날짜: 2026-08-03

## 기본 정보

- **개발사**: BenStar (솔로 인디 개발자)
- **출시**: 2022년 4월 (Steam Early Access 2021)
- **플랫폼**: PC (Steam), Nintendo Switch
- **장르**: 트윈스틱 슈터 로그라이크
- **Steam**: https://store.steampowered.com/app/1175460/Revita/
- **공식 사이트**: https://revita.bensart.games/
- **엔진**: Unity (솔로 개발 레퍼런스로 가치 높음)

---

## 핵심 메카닉

### 1. HP = 탄약 (생명력 소모 사격)
Revita 최고의 핵심 루프. 투사체를 발사할 때마다 **HP를 1 소모**. 근접 공격(대시+검)으로 HP 회복. 모든 전투가 "공격적으로 싸워야 살아남는다"는 원칙으로 수렴.

- HP 1이어도 사격 가능 (죽지 않음, 단 1발)
- 근접 공격은 무조건 HP 회복 → 근접과 원거리를 끊임없이 교차
- "원거리만 쓰면 죽는다" → 밀리/원거리 전환을 강제하는 시스템

### 2. 트윈스틱 이동 + 대시
- 왼쪽 스틱: 이동
- 오른쪽 스틱: 조준 및 사격 방향
- 대시: 무적 프레임 포함, 짧은 쿨타임
- 대시 도중 근접 공격 = HP 회복 + 무적 = 핵심 스킬

### 3. 업그레이드 시스템
- 방 클리어 후 3가지 수동 아이템 중 선택
- 아이템 간 시너지 → 빌드 다양성
- 일부 아이템: "HP 최대치 감소 대신 강력한 효과" (리스크 리워드)

### 4. 보스 전투
- 층마다 고유 보스, 각각 독창적인 공격 패턴
- 보스 처치 시 핵심 업그레이드 보장
- 패턴 암기 + HP 관리 = 고강도 전투

### 5. 절차적 방 생성
- 각 층마다 랜덤 방 배치
- 방 유형: 전투, 상점, 보물, 휴식, 보스
- 전형적인 로그라이크 구조이나 픽셀아트 비주얼 퀄리티 높음

---

## 플레이어가 사랑하는 요소

1. **HP=탄약 시스템의 긴장감** — "내 총알이 곧 내 생명" → 모든 사격이 결단
2. **절제된 미학** — 다크한 세계관 + 아름다운 픽셀아트 + 멜랑꼴리 사운드트랙
3. **빠른 피드백 루프** — 죽으면 빠르게 재시작, 런 하나가 짧고 임팩트 있음
4. **솔로 개발의 완성도** — 1인 개발자가 만들었다는 사실에 커뮤니티 애착
5. **보스전 퀄리티** — 각 보스가 독창적이고 기억에 남는 패턴 보유

---

## OnionCat 적용 포인트

### A. HP-탄약 연계를 협동 구조로 변환
Revita의 개인 HP=탄약을 **공유 HP 풀**에 적용:
- Onion이 투사체를 발사하면 **공유 HP에서 소량 소모**
- Cat의 근접 공격이 공유 HP 회복
- "Onion이 많이 쏠수록 Cat이 더 많이 근접해야 한다" → 협동 필수성 강화

```csharp
// SharedHPPool.cs 개념
public class SharedHPPool : MonoBehaviour {
    public int currentHP;
    
    // Onion이 발사할 때 호출
    public bool TrySpendHP(int cost) {
        if (currentHP <= cost) return false;
        currentHP -= cost;
        return true;
    }
    
    // Cat이 근접 공격 명중 시 호출
    public void RestoreHP(int amount) {
        currentHP = Mathf.Min(currentHP + amount, maxHP);
    }
}
```

### B. 원거리/근거리 교차 강제 메카닉
Revita처럼 "원거리만 쓰면 손해" 구조를 OnionCat에:
- Onion 연속 발사 → 과열(Overheat) → 쿨타임 발생
- 쿨타임 중 Cat 근접 공격 시 쿨타임 즉시 리셋
- 플레이어들이 자연스럽게 "Cat 먼저 → Onion 사격 → Cat 회복" 리듬 형성

### C. 픽셀아트 보스 연출
Revita 보스의 **대형 스프라이트 + 명확한 패턴 예고** 방식 참고:
- 보스 공격 직전 어두운 선(telegraph line) 표시
- 보스 체력바 하단 고정(화면 가득 차도 UI 가림 없음)
- 3페이즈 체력 기반 패턴 전환

### D. 솔로/2인 개발 참고
BenStar 1인 개발 방식:
- 핵심 루프 1개만 완벽히 만들고 확장
- 아트/사운드 모두 Itch.io 에셋 활용 초기 → 이후 전부 교체
- 얼리 액세스로 피드백 반영 → OnionCat 개발 전략으로 활용 가능

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/1175460/Revita/
- 개발자 트위터: https://twitter.com/BenSartDev
- 유튜브 게임플레이: Revita gameplay Steam trailer
- 인디 개발 인터뷰: https://www.thegamer.com/revita-interview-bensart/
