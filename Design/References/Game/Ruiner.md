# Ruiner

리서치 날짜: 2026-08-13

## 기본 정보

- **개발사**: Reikon Games (폴란드)
- **퍼블리셔**: Devolver Digital
- **출시**: 2017년 9월
- **플랫폼**: PC, PS4, Xbox One, Switch
- **공식 사이트**: https://reikongames.com/ruiner/
- **Steam**: https://store.steampowered.com/app/464060/RUINER/
- **장르**: 탑다운 트윈스틱 액션 어드벤처 (로그라이크 아님)

---

## 핵심 메카닉

### 1. 전투 철학 — "공격이 최선의 방어"
- 적을 처치하면 **에너지(HP) 회복** — 방어적 플레이가 오히려 불리
- 대시/구르기는 무적 프레임 없음 → 순수 위치 기동 도구
- **와이어(Wire)**: 적에게 갈고리로 달라붙어 순간 이동 — P1 대시와 유사한 용도
- 킬 momentum이 쌓일수록 콤보 카운터와 에너지 회복량 증가

### 2. 무기 & 능력 시스템
- 총기(근거리~장거리), 근접 무기, 투척 물건 — 맵에 있는 모든 것이 무기
- **스킬 슬롯**: 실드 배리어, 에너지 충전, 군중 제어 등 고정 슬롯에 스킬 장착
- 플레이어가 실시간으로 스킬 조합을 선택 → 빌드 다양성

### 3. 피드백 & 게임 필
- **히트스톱**: 모든 타격에 1~3프레임 정지 → 묵직한 타격감
- **화면 진동 (Screenshake)**: 강조 공격마다 달리 튜닝된 진동 세기
- **파티클 폭발**: 적 사망 시 혈흔 + 사이버 파편 동시 분출
- **슬로우모션 처치 연출**: 마지막 적 처치 시 0.2초 타임스케일 감소 → "쾌감의 선명화"

### 4. 적 설계
- 적마다 명확히 다른 **실루엣과 공격 예고 모션** (전신 플래시, 레이저 라인 등)
- 근접 러셔 / 장거리 저격 / 방패 드론 / 자폭형 — 플레이어에게 다른 반응을 요구
- 다수 적을 동시에 상대할 때 **어그로 우선순위**가 체감됨
  - 플레이어가 근접하면 러셔가 먼저 돌진
  - 저격은 일정 거리 유지하며 플레이어를 공략

---

## 협동 요소

Ruiner는 싱글플레이어 게임이지만 **비대칭 분업의 감각**을 제공:
- "어디를 먼저 처치할 것인가"를 플레이어가 실시간으로 판단 = P1(근접)과 P2(원거리) 역할 분리의 원형
- 방어막 적은 **뒤에서 공격해야 처치 가능** → 회피 + 위치 전환이 핵심 = OnionCat의 "근접 전용/원거리 전용 약점" 철학과 동일

---

## 플레이어가 사랑하는 것

1. **극도로 세련된 타격감** — 히트스톱·파티클·사운드의 3박자 정합
2. **암울한 사이버펑크 세계관** — 단순하지만 강렬한 비주얼 아이덴티티
3. **높은 난이도와 죽음 → 즉각 재시도** 루프 — 짧은 피드백 루프
4. **스킬 조합 실험** — 같은 맵도 다른 빌드로 완전히 달라지는 플레이

---

## OnionCat 적용 포인트

| Ruiner 요소 | OnionCat 적용 |
|---|---|
| 적 처치 시 에너지 회복 | 협동 처치 시 공유 HP 소량 회복 → 공격적 플레이 유도 |
| 히트스톱 3단계 강도 | 일반/강공격/오브젝트 파괴별 히트스톱 프레임 달리 설정 |
| 슬로우모션 마지막 처치 | 방 클리어 시 0.2초 타임스케일 0.3 → 1.0 복구 코루틴 |
| 방패 뒤에서만 약점 | 원거리만 뚫리는 적(방패 앞면) → P2 조준 필수 상황 |
| 와이어(갈고리 이동) | P1 대시가 적에게 적중하면 방향 보정되는 "흡착 대시" 업그레이드 |

### 구현 힌트
```csharp
// 방 클리어 연출: 마지막 적 사망 시 슬로우모션
IEnumerator RoomClearSlomo()
{
    Time.timeScale = 0.25f;
    yield return new WaitForSecondsRealtime(0.2f);
    float t = 0f;
    while (t < 0.3f)
    {
        t += Time.unscaledDeltaTime;
        Time.timeScale = Mathf.Lerp(0.25f, 1f, t / 0.3f);
        yield return null;
    }
    Time.timeScale = 1f;
}
```

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/464060/RUINER/
- 공식 트레일러: https://www.youtube.com/watch?v=ZJNiNl7a5mg
- Reikon Games 개발 블로그: https://reikongames.com/blog/
- Game Design Deep Dive (Game Developer): https://www.gamedeveloper.com/design/how-ruiner-nails-the-perfect-feel-of-a-brutal-action-game
- Videogamedunkey 리뷰 (플레이어 반응 참고): https://www.youtube.com/watch?v=e2fU5_fKHMA
