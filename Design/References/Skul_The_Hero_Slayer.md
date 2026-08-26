# Skul: The Hero Slayer

리서치 날짜: 2026-08-26

## 기본 정보

- **개발사**: SouthPAW Games (한국 인디)
- **플랫폼**: PC, Console
- **장르**: 횡스크롤 액션 로그라이크
- **공식 사이트**: https://southpaw.co.kr/
- **Steam**: https://store.steampowered.com/app/1147560/Skul_The_Hero_Slayer/
- **Wiki**: https://skul-the-hero-slayer.fandom.com/

---

## 핵심 메카닉

### 1. 해골(Skull) 교체 시스템 — OnionCat과 가장 유사한 메카닉
- 주인공 스컬은 **최대 2개의 해골을 장착**, 언제든 교체 가능 (Q키)
- 각 해골 = 완전히 다른 캐릭터 (스켈레톤 기사, 마법사, 닌자, 드래곤 등)
- **두 해골의 조합으로 전투 스타일이 결정됨** — 단순 스탯 합이 아닌 시너지
- 교체 직후 잠깐 무적 프레임 발생 → 교체 자체가 전술적 도구
- 각 해골은 고유 노멀 공격 + 스킬 2개 (쿨타임 기반)

### 2. 해골 등급 시스템
- Common / Rare / Unique / Legendary 등급
- 높은 등급 해골 = 더 강력한 스킬 + 시각적으로 화려한 이펙트
- 런마다 랜덤 해골 조합 → 매 런이 다른 경험

### 3. 전투 철학: 빠르고 화려하게
- 에어리얼 콤보, 대시, 해골 교체가 자연스럽게 연결되는 리듬감
- **히트스톱 + 파티클 이펙트** 적극 활용 → 타격감이 핵심 셀링포인트
- 적의 공격 패턴이 명확하게 시각화 (전조 이펙트)

### 4. 보스 디자인
- 각 보스는 다단계 페이즈 전환
- 보스마다 고유한 전투 문법 (근접 전문 보스 vs 원거리 탄막 보스)
- 일부 보스는 특정 해골 타입에 약함 (해골 다양성 강요)

### 5. 메타 진행
- 마을 재건 시스템: 클리어 후 자원 획득 → 마을 NPC 해금 → 게임 편의 향상
- 골드/뼈 재화 이원 구조: 골드(런 내 사용), 뼈(런 간 영구 재화)

---

## 플레이어가 사랑하는 이유
- **한국 인디의 자존심** — 국내외에서 호평 받은 완성도
- 해골 교체 시스템의 참신함 — "이 두 해골 조합이 최강!" 빌드 탐구
- 빠른 전투 속도와 화려한 이펙트 → 유튜브 하이라이트 클립 생산
- 접근성 있는 조작 (버튼 수 적음)이지만 깊은 전술적 심도
- BGM과 한국 설화 모티프 세계관의 독창성

---

## OnionCat 적용 포인트

### A. 해골 교체 → Cat+Onion "모드 전환" 영감
스컬의 해골 교체처럼 OnionCat도 특정 업그레이드 선택 시 **스탠스/모드 전환** 개념 도입 고려:
- "공격 모드": Cat 이동속도↑, Onion 투사체 데미지↑
- "방어 모드": Cat 대시 쿨타임↓, Onion 방어막 지속시간↑
- 전환 시 짧은 무적 프레임 부여 → Skul의 교체 무적과 동일 원리

### B. 해골 등급 → 업그레이드 희귀도 시스템
스컬의 Common/Rare/Unique/Legendary를 OnionCat 업그레이드 희귀도에 적용:
```csharp
public enum ItemRarity { Common, Rare, Unique, Legendary }
// Legendary는 런당 최대 1개만 등장
```
시각적 구분: Common(회색 테두리) → Legendary(금색 빛나는 테두리)

### C. 보스 페이즈 설계 참고
OnionCat 보스도 Skul처럼 HP 임계값 기반 페이즈 전환 + 페이즈마다 공격 패턴 추가:
- Phase 1 (100~60% HP): 기본 패턴
- Phase 2 (60~30% HP): 새 패턴 추가, 이동속도 증가
- Phase 3 (30~0% HP): 분노 상태, 화면 전체 연출

### D. 타격감 이펙트 벤치마크
Skul의 히트스톱 + 파티클 조합을 OnionCat의 기준 삼기:
- Cat 슬래시: 0.08초 히트스톱 + 혈흔 파티클 + 칼날 이펙트
- Onion 투사체 명중: 작은 폭발 파티클 + 사운드 피치 변화
- **Skul보다 "과하다"는 느낌이 들면 0.5배로 줄이기** (픽셀아트라 자칫 과해질 수 있음)

### E. 마을 재건 → OnionCat 허브 화원
스컬의 마을 재건처럼 OnionCat도 허브 화원에서 런 간 영구 업그레이드 구현:
- 재료(씨앗/흙) → 화원에 새 식물 심기 → 런 시작 시 초기 버프
- 시각적으로 화원이 점점 풍성해지는 성장감

---

## 참고 링크
- [공식 사이트](https://southpaw.co.kr/)
- [Steam 페이지](https://store.steampowered.com/app/1147560/Skul_The_Hero_Slayer/)
- [위키 (해골 목록/스킬)](https://skul-the-hero-slayer.fandom.com/)
- [한국 인디게임 개발기 인터뷰](https://www.youtube.com/results?search_query=Skul+The+Hero+Slayer+개발+인터뷰)
- [IGN 리뷰](https://www.ign.com/articles/skul-the-hero-slayer-review)
