# Rogue Stormers

리서치 날짜: 2026-08-14

## 기본 정보

- **개발사**: Black Forest Games (독일)
- **출시**: 2016년 4월
- **플랫폼**: PC (Steam), PS4
- **공식 사이트**: https://roguestormers.com
- **Steam**: https://store.steampowered.com/app/329130/Rogue_Stormers/
- **장르**: Co-op 탑다운 런앤건 로그라이트 (최대 4인 로컬/온라인)

---

## 핵심 메카닉

### 클래스 기반 Co-op 시스템
8개 캐릭터 클래스, 각자 고유한 무기 + 스킬 조합:
- 근거리 전사 / 원거리 사수 / 샷건 / 화염방사기 / 저격수 등
- 팀 구성에 따라 시너지 조합이 달라지는 빌드 다양성

### 절차적 레벨 생성
- 랜덤 방 배치 + 랜덤 적 조합 + 랜덤 업그레이드 선택
- 각 층 클리어 후 업그레이드 카드 3장 중 선택 (전형적 로그라이트 루프)

### 물리 기반 전투
- 적이 피격 시 실제 물리 날아감 (Rigidbody2D impulse)
- 폭발물 · 화염 등 환경 파괴 요소
- 탄환이 벽에 충돌하는 반응 처리 (단, 반사탄 없음)

### 업그레이드 시너지 시스템
- 특정 업그레이드 조합 시 "특수 시너지" 발동 (예: 화염+폭발 = 대형 폭발)
- 플레이어가 빌드를 스스로 발견하는 탐험 재미
- 협동 플레이 시 상대 캐릭터의 업그레이드와 시너지 발생 가능

---

## 플레이어가 사랑하는 요소

1. **빠른 속도감**: 총알이 빠르고 적이 많으며 화면이 끊임없이 역동적
2. **시너지 발견**: 우연히 발견하는 강력한 빌드 조합 → "이게 되네?" 순간의 쾌감
3. **픽셀 아트 + 폭발 이펙트**: 클래식 런앤건 감성 + 현대적 파티클 효과
4. **로컬 Co-op**: 소파 협동이 자연스럽게 작동하는 적 배치 설계

---

## OnionCat 적용 포인트

### 1. 업그레이드 시너지 명시화
Rogue Stormers처럼 "이 업그레이드 + 저 업그레이드 → 특수 효과" 조합을 명시.
- OnionCat: P1 업그레이드 "날카로운 발톱"(근접 대미지+) + P2 업그레이드 "독 씨앗"(독 투사체) 조합 시 "독 발톱 슬래시" 특수 효과 발동
- 구현 힌트: `UpgradeManager.RegisteredUpgrades` 리스트를 순회해 `SynergyDatabase`에서 매칭 시너지 검색

### 2. 물리 기반 히트 반응
피격 시 `Rigidbody2D.AddForce(hitDirection * knockbackForce, ForceMode2D.Impulse)`.
- 적이 날아가 벽에 부딪히면 추가 피해 (BumpDamage) → 타격감 극대화
- OnionCat 근접 공격이 특히 이 느낌이 중요

### 3. 클래스별 탄환 다양성
탄환 유형: 단발/산탄/유도/관통/범위 폭발을 업그레이드로 변환.
- P2(파)의 기본 투사체가 업그레이드에 따라 형태 변환 → 매 런 다른 원거리 경험
- 구현 힌트: `ProjectileConfig` ScriptableObject로 발사 패턴 정의, `ProjectileLauncher`가 런타임에 Config 교체

### 4. 탑다운 적 배치 설계
"총알 피하기 공간"과 "근접 전투 공간"을 동시에 고려한 방 레이아웃.
- Rogue Stormers의 좁은 복도 + 열린 아레나 혼합 → OnionCat 방 디자인에 참고
- 기둥·차폐물 배치: P2가 뒤에서 조준하고 P1이 앞에서 근접 전담하는 구도 자연스럽게 형성

---

## 참고 링크

- Steam 상점: https://store.steampowered.com/app/329130/Rogue_Stormers/
- 공식 사이트: https://roguestormers.com
- YouTube 플레이스루: 검색 "Rogue Stormers gameplay 2016"
- Black Forest Games 트위터: @BlackForestGames
- 로그라이트 Co-op 설계 참고: https://www.gamedeveloper.com/design/making-co-op-roguelites-feel-fair
