# Castle Crashers

리서치 날짜: 2026-09-24

## 기본 정보

- **개발/출시**: The Behemoth, 2008 (XBLA) / 2010 (PC)
- **Steam**: https://store.steampowered.com/app/204360/Castle_Crashers/
- **장르**: Co-op Beat-em-up + RPG + Action Roguelite 요소
- **플레이어 수**: 1-4명 로컬/온라인 협동

## 핵심 시스템

### 캐릭터 & 전투
- 4개 기본 캐릭터 + 다수 잠금 해제 캐릭터, 각각 **고유 마법(Magic)**이 다름
- 기본 공격: 약/강 근접, 공중 콤보, 마법 (방향키 조합으로 발동)
- 모든 캐릭터가 **동일한 기본 무기 + 장착 무기** 시스템 공유 → 캐릭터 개성은 마법으로 차별화
- **Arrow 시스템**: 원거리 공격은 버튼 홀드+방향으로 조준, 공동 협력에 중요

### 스탯 & 성장
- 레벨업마다 4가지 스탯 포인트 배분: Strength / Magic / Defense / Agility
- **빌드 다양성**: 마법 특화(힐러), 물리 특화(탱크), 속도 특화 등 플레이어별 역할 분화
- 무기별 숨겨진 스탯 보너스 → 아이템 수집 동기 부여

### 협동 설계
- **4명 동시 화면**: 플레이어가 흩어지면 화면이 줌아웃, 모이면 줌인 (다이나믹 카메라)
- **부활 시스템**: 죽은 플레이어를 살아있는 플레이어가 집어 들면 부활 가능 (리소스 소비 없음)
- **Friendly Fire OFF**: 협력 플레이에서 팀킬 없음 → 입문 장벽 낮춤
- **아이템 공동 사용**: 고기(회복), 보물 → 경쟁보다 협력 구조

### 진행 구조
- **선형 스테이지 + 비선형 월드맵**: 다음 스테이지 선택 가능한 구간 있음
- **Arena 시스템**: 별도 투기장에서 PvP 가능 (협동과 경쟁 공존)
- **New Game+**: 클리어 후 같은 캐릭터로 더 강한 난이도 재도전, 메타 성장 감

## 플레이어가 좋아하는 것

1. **광기의 적 다양성** — 수십 종의 적, 각자 고유 패턴과 약점
2. **아트 스타일** — Newgrounds 시절 The Behemoth 특유의 카툰 폭력성 + 유머
3. **길지 않은 플레이타임** — 1회차 4~6시간, 가볍게 친구와 즐길 수 있는 볼륨
4. **캐릭터 수집** — 동물 오브들, 숨겨진 캐릭터 잠금 해제 → 리플레이 유도
5. **쉬운 합류**: 아무 때나 플레이어 참가/이탈 가능 (Drop-in/Drop-out)

## OnionCat 적용 포인트

### 1. 역할 분화 모델
- Castle Crashers에서 캐릭터마다 마법이 다르듯, OnionCat도 Cat(근접)·Onion(원거리)의 역할 분화가 선명해야 함
- **약점 연동**: 어떤 적은 Cat으로만, 어떤 적은 Onion으로만 처치 가능 → CC의 마법 저항 적 개념과 유사
- 핵심 인사이트: **"기계적 강제"** 보다 **"상황적 유인"** 이 더 좋은 협동을 만들어냄 (CC는 강제하지 않지만 협력하면 훨씬 쉬움)

### 2. 다이나믹 카메라
- CC의 동적 줌아웃 카메라는 공유 바디 개념의 OnionCat에서는 불필요하지만, **방 카메라 이동 시 양 플레이어의 시야 균형**은 동일하게 중요
- Shared_Body_Camera_Framing_System.md 참고

### 3. Drop-in 협동 (미래 확장)
- 현재 OnionCat은 2인 고정이지만, CC의 드롭인 방식은 싱글 플레이어 지원 설계 시 참고 가능
- "혼자 플레이 시 Onion을 AI가 조종" 시나리오에 적용

### 4. 부활 시스템
- Coop_Revival_System.md 이미 존재하지만, CC의 **"들어 올려 부활"** 방식은 OnionCat의 물리적 공유 바디 콘셉트에 더 자연스럽게 맞음
- → 아이디어: Cat이 죽으면 Onion이 자율 조종으로 대피 → 심장 근처에서 부활 모션

### 5. 스탯 배분 UI
- CC의 단순한 4-스탯 배분은 초보 개발자가 구현하기 쉬운 업그레이드 UI 레퍼런스
- OnionCat의 업그레이드 선택 화면 디자인에 참고

## 기술 구현 참고

```
// CC 스타일 레벨업 스탯 배분 (OnionCat 적용 예시)
public enum StatType { Strength, Magic, Defense, Agility }

[System.Serializable]
public class CharacterStats {
    public int strength, magic, defense, agility;
    public int availablePoints;

    public void Allocate(StatType stat) {
        if (availablePoints <= 0) return;
        availablePoints--;
        switch(stat) {
            case StatType.Strength: strength++; break;
            // ...
        }
    }
}
```

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/204360/Castle_Crashers/
- Castle Crashers Wiki: https://castlecrashers.fandom.com/wiki/Castle_Crashers_Wiki
- GDC 2009 (The Behemoth 디자인 철학): Dan Paladin 인터뷰 다수
- Giant Bomb 리뷰 (협동 설계 분석): https://www.giantbomb.com/castle-crashers/3030-25735/
