# Halls of Torment

## 기본 정보

| 항목 | 내용 |
|------|------|
| 장르 | 불릿 헤븐 로그라이트 (Bullet Heaven Roguelite) |
| 개발사 | Chasing Carrots (독일 인디) |
| 출시 | Early Access: 2023.06, 정식: 2024.04 |
| 플랫폼 | PC (Steam) |
| 공식 사이트 | https://www.chasingcarrots.com/halls-of-torment |
| Steam | https://store.steampowered.com/app/2239150 |
| Wiki | https://halls-of-torment.fandom.com/wiki |

---

## 핵심 메카닉

### 클래식 ARPG 미적 + 현대 로그라이트 루프
- **배경**: Diablo 1/2 스타일의 쿼터뷰 어둡고 고딕한 비주얼 — 3D 렌더링이지만 레트로 느낌
- **자동 공격 + 능동 스킬**: Vampire Survivors의 DNA + 능동 스킬 버튼 추가
- 이동만 하면 자동으로 가장 가까운 적 공격 → 초보자 진입 장벽 낮음

### 캐릭터 클래스 시스템
- 8개 이상의 클래스 (전사, 궁수, 마법사, 무당, 발키리 등)
- 각 클래스마다 고유 자동공격 방식과 패시브 특성
- 클래스 선택이 런 전략의 출발점

### 능력 조합 (Ability Synergy)
- 런 중 레벨업 시 3가지 능력/업그레이드 중 선택
- 능력은 특정 조합으로 **극적인 시너지** 발생 (예: 번개 + 전도율 → 연쇄 전격)
- 빌드 발견의 재미가 리플레이를 유도

### 퍼마데스 + 영구 언락 (Meta-progression)
- 런 중 획득한 "골드/경험치"로 영구 스탯 업그레이드 (Vampire Survivors 방식)
- 업적 달성으로 새 클래스/아이템 언락
- **시간 제한 런**: 20분 생존이 기본 목표 → 명확한 단기 목표

### 보스 시스템
- 매 스테이지 종반에 고정 보스 등장
- 보스는 고유 패턴과 취약점 보유
- **취약 시스템**: 특정 보스는 특정 원소 피해에 약함 → OnionCat의 근접/원거리 취약성과 유사!

### 챕터 구조와 스테이지 선택
- 여러 스테이지 중 순서 선택 가능 (Dead Cells 처럼)
- 각 스테이지: 다른 적 조합, 환경 효과 (예: 독 안개 스테이지)

---

## 플레이어들이 사랑하는 점

1. **클래식 ARPG 향수**: Diablo 느낌의 미적을 현대 루프와 결합
2. **빠른 런**: 20분 제한으로 부담 없는 플레이
3. **빌드 다양성**: 클래스 × 능력 조합으로 수십 가지 플레이스타일
4. **시각적 쾌감**: 화면 가득 적이 쌓이고 터지는 "쓸어버리는" 느낌
5. **적당한 난이도 곡선**: 영구 업그레이드로 막힌 구간 돌파 가능

---

## OnionCat 적용 포인트

### 1. "취약 시스템"의 구체적 구현 힌트
Halls of Torment는 적마다 원소 저항치를 가짐:
```csharp
// 적 데이터 예시
public enum DamageType { Melee, Ranged, Fire, Ice }

[System.Serializable]
public class EnemyResistance {
    public DamageType weakTo;      // 이 타입에 150% 피해
    public DamageType resistantTo; // 이 타입에 50% 피해
}
```
OnionCat: 근접 전용 적 / 원거리 전용 적의 저항 시스템에 직접 적용 가능

### 2. 클래스별 자동공격 → 고양이 + 작물 역할 분담
- Halls of Torment 전사: 근접 자동 공격
- Halls of Torment 궁수: 원거리 자동 조준
- **OnionCat**: 고양이(전사)와 작물(궁수)이 각자의 "자동" 타입을 가지되, 협력 시 특수 콤보 발동

### 3. 20분 타임 어택 → 방 클리어 타이머
- 각 방에 소프트 타이머: 빨리 클리어할수록 보너스 점수/아이템
- 강제 클리어는 아니지만 속도플레이 유도 → 게임 템포 조절

### 4. 빌드 시너지 UI 힌트
- 레벨업 선택 화면에서 현재 빌드와 시너지 있는 항목을 강조 표시
- 초보자 친화적: "이 능력은 현재 빌드에 잘 맞아요" 힌트

### 5. 스테이지 선택으로 난이도 자율 조정
- 쉬운 스테이지 → 자원 확보 / 어려운 스테이지 → 고급 아이템
- 플레이어가 스스로 도전 수준 선택 → 개인 맞춤 경험

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/2239150/Halls_of_Torment/
- 공식 개발 블로그: https://www.chasingcarrots.com/blog
- 리뷰 분석 (RPS): https://www.rockpapershotgun.com/halls-of-torment-review
- 빌드 가이드 허브: https://halls-of-torment.fandom.com/wiki/Builds
