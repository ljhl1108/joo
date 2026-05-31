# Unity 2인 협동 로그라이크 — 고양이와 화분 (Claude Code 지침서)

## 🎯 에이전트의 역할
당신은 이 유니티 게임(고양이와 작물의 2인 1캐릭터 협동 로그라이크)의 핵심 개발 파트너입니다.
버그 없는 C# 코드를 작성하고, 코드가 기존 시스템과 완벽하게 호환되도록 하는 것이 목표입니다.

---

## ⚠️ 절대 지켜야 할 안전 수칙
1. **Scene 파일(`.unity`) 및 Prefab 파일(`.prefab`)은 절대 텍스트 에디터로 직접 수정하지 마세요.** (YAML 파싱 오류로 파일 전체가 손상될 수 있습니다.)
2. 유니티 Inspector나 프리팹에 할당해야 할 컴포넌트나 변수(`[SerializeField]` 등)가 생기면, 사용자에게 "유니티 에디터에서 다음 항목을 드래그 앤 드롭으로 설정해주세요"라고 명확히 안내하세요.

---

## 🎮 게임 컨셉 상세

### 핵심 아이덴티티
- **장르**: 2인 협동 로그라이크 (로컬 협동 우선, 온라인 추후)
- **비주얼**: 픽셀 아트 로그라이크 스타일 (Binding of Isaac, Enter the Gungeon 참고)
- **플랫폼**: PC — Player 1은 게임패드 메인 (키보드/마우스 호환 목표), Player 2는 키보드+마우스

### 2인 1캐릭터 구조
두 플레이어가 **하나의 캐릭터 바디를 공유**하되 역할을 분리합니다.

| | Player 1 (고양이) | Player 2 (작물/양파) |
|---|---|---|
| **담당** | 이동, 대쉬, 밀리 공격 | 원거리 공격, 방향 실드, 패링 |
| **입력** | 게임패드 (WASD/방향키 호환) | 키보드 + 마우스 |
| **이동** | ✅ 캐릭터를 직접 이동 | ❌ 이동하지 않음 |

### 화분과 작물 설정
- 고양이는 **등에 화분을 메고** 다닌다.
- 화분에는 **작물(양파, 당근 등)**이 자라고 있으며, 이것이 Player 2의 캐릭터.
- Player 2는 런 시작 시 **작물을 선택**할 수 있으며, 작물마다 능력이 다르다. → **로그라이크의 핵심 선택 요소**
- 현재 구현 대상: **양파** (방향 실드 + 패링 + 원거리 투사체)
- 시각적으로 양파는 고양이에 부착된 **분리된 서브 오브젝트(CropHolder)**로 구현

---

## ⚔️ 전투 시스템 설계

### 2레이어 실드 시스템
#### 레이어 1: 패시브 실드 (PlayerHealth.cs — 구현 완료)
- **역할**: 수치형 HP 버퍼 (체력 방어막)
- **동작**: 피격 시 실드가 먼저 소모되고, 실드가 0이 되면 고양이 체력에 영향
- **회복**: 피격 후 4초 대기 → 2초마다 1칸씩 자동 회복

#### 레이어 2: 액티브 실드 (OnionShield.cs — 미구현)
- **역할**: 투사체 차단용 방향 실드
- **동작**:
  1. 양파 플레이어가 버튼 입력 → **마우스 방향**으로 실드 생성
  2. 실드 활성화 직후 짧은 시간 (약 0.2~0.3초) 내: **패링** → 투사체가 적에게 반사
- 두 실드는 **공존**: 패시브 = HP 버퍼, 액티브 = 투사체 차단/패링

### 모듈형 공격 시스템 (구현 완료)
고양이의 공격과 대쉬는 **교체 가능한 컴포넌트** 구조입니다.

```
BaseMeleeAttack (추상 클래스)
├── MeleeAttack_Slash.cs  ← 현재 (180° 부채꼴, MeleePivot에 부착)
├── MeleeAttack_Stab.cs   ← 향후 (직선 찌르기)
└── MeleeAttack_Spin.cs   ← 향후 (360° 회전)

BaseDash (추상 클래스)
├── Dash_Default.cs  ← 현재 (직선 돌진 + 무적, Player_Cat에 부착)
└── Dash_Blink.cs    ← 향후 (순간이동)
```

### 고양이 선택 시스템 (미구현 — 설계 방향)
- 작물 선택과 동일하게, **런 시작 시 고양이 종류(여우, 호랑이 등)**를 선택
- `CatData.cs` (ScriptableObject) 로 각 고양이의 스탯과 기본 공격/대쉬를 정의
- `CatController`가 선택된 `CatData`를 읽어 속도, 공격 컴포넌트를 초기화

### 적 분류 개념 (설계 방향)
- **고양이 전용 적**: 원거리 공격에 내성, 밀리로만 처치 가능
- **양파 전용 적**: 밀리 공격에 내성, 원거리/패링으로만 유효
- 두 플레이어의 협력을 **자연스럽게 강제**하는 구조

---

## 📊 현재 코드베이스 현황

### 스크립트 위치
`Assets/Scripts/` (하위 폴더 구조)

### 폴더 구조
```
Assets/Scripts/
  Player/
    CatController.cs       ← 이동 입력, 피벗 회전, 공격/대쉬 위임
    OnionController.cs     ← 마우스 조준, 투사체 발사
    PlayerHealth.cs        ← HP + 패시브 실드
    BaseMeleeAttack.cs     ← 밀리 공격 추상 기반
    MeleeAttack_Slash.cs   ← 밀리 공격 1 (180° 부채꼴)
    BaseDash.cs            ← 대쉬 추상 기반
    Dash_Default.cs        ← 대쉬 1 (직선 돌진)
    OnionShield.cs         ← [미구현] 액티브 실드 + 패링
    CropSubObject.cs       ← [미구현] 화분+작물 비주얼
  Enemy/
    EnemyController.cs     ← 기본 슬라임 AI
  Map/
    SimpleMapGenerator.cs  ← 테스트용 직사각형 방
    RoomManager.cs         ← [미구현] 방 클리어/문 시스템
    DungeonManager.cs      ← [미구현] 런 단위 방 연결
  UI/
    HUDController.cs       ← [미구현] HP/실드 HUD
    GameOverManager.cs     ← [미구현] 게임오버 화면
  Projectile/
    Projectile.cs          ← 양파 기본 투사체
  Camera/
    CameraController.cs    ← SmoothDamp 카메라 추적
```

### ⚠️ 알려진 기술 부채
- 패시브 실드 UI 없음 (수치만 존재)
- 게임 오버 처리 미완성 (`Die()` 임시 처리 중)
- CatData ScriptableObject 미구현 (고양이 선택 시스템 전제조건)
- `EnemyController.Start()`의 `FindObjectOfType` → 방 시스템 도입 시 리팩토링 필요

---

## 🗺️ Unity Hierarchy 구조

### 표기 규칙
- **굵게 → GameObject** (Hierarchy 창에 나타남)
- *이탤릭 → Component* (Inspector에서 Add Component로 부착)

```
[씬]
├── GameManager                        GameObject
│     └── (GameManager.cs — Phase 3)
│
├── Player_Cat                         GameObject  (Tag: Player)
│     ├── CatController.cs             Component
│     ├── Dash_Default.cs              Component   (BaseDash 구현체, 교체 가능)
│     ├── PlayerHealth.cs              Component
│     ├── PlayerInput                  Component   (Unity 내장)
│     ├── Rigidbody2D                  Component
│     └── CircleCollider2D             Component
│
│     ├── CatBody                      GameObject  (고양이 외형)
│     │     └── SpriteRenderer         Component
│     │
│     ├── MeleePivot                   GameObject  (이동방향으로 회전)
│     │     ├── MeleeAttack_Slash.cs   Component   (BaseMeleeAttack 구현체, 교체 가능)
│     │     └── AttackPoint            GameObject  (공격 판정 위치)
│     │
│     └── CropHolder                   GameObject  (화분 전체 서브오브젝트)
│           ├── CropSubObject.cs       Component   [미구현]
│           ├── OnionController.cs     Component
│           ├── OnionShield.cs         Component   [미구현]
│           ├── PotSprite              GameObject  (화분 스프라이트)
│           │     └── SpriteRenderer   Component
│           ├── CropSprite             GameObject  (작물 스프라이트)
│           │     └── SpriteRenderer   Component
│           └── AimPivot               GameObject  (조준 피벗)
│                 └── ShootPoint       GameObject  (발사 위치)
│
├── Main Camera                        GameObject
│     ├── Camera                       Component
│     ├── CameraController.cs          Component
│     └── AudioListener                Component
│
├── HUD                                GameObject  (Canvas — Screen Space Overlay)
│     └── HUDPanel                    GameObject  (Horizontal Layout Group)
│           ├── HeartContainer         GameObject  (하트 아이콘 자동 생성)
│           └── ShieldContainer        GameObject  (실드 아이콘 자동 생성)
│                 └── HUDController.cs Component
│
└── Map                                GameObject
      ├── SimpleMapGenerator.cs        Component
      └── Grid                         GameObject
            ├── FloorTilemap           GameObject
            └── WallTilemap            GameObject
```

---

## 🌱 작물 시스템

### 개념
- 런 시작 시 Player 2가 **작물(Crop)**을 선택
- 작물마다 **원거리 공격 방식, 실드 특성, 특수 능력**이 다름

### 현재 구현 대상: 양파
- 원거리 투사체: 마우스 클릭 → 마우스 방향 발사
- 액티브 실드: 마우스 방향 차단막 + 패링 타이밍 윈도우

### 향후 확장 (미정)
- 당근, 부추, 마늘 등 → 능력 설계는 추후 논의

---

## 🎯 현재 개발 우선순위

1. **[1순위] 전투 시스템 체계화**
   - OnionShield.cs (액티브 실드 + 패링)
   - CropSubObject.cs (화분 서브오브젝트 비주얼)
   - HP 수치 밸런스 확정
2. **[2순위] Hades 스타일 방 시스템** — 방 클리어 → 문 열림 → 다음 방 이동
3. **[3순위] UI** — HP/실드 HUD, 게임 오버 화면
4. **[4순위] 캐릭터 선택 시스템** — CatData + CropData ScriptableObject

---

## 🛠️ 작업 워크플로우
1. **분석**: 요구사항을 받으면 관련된 기존 코드의 상속 구조나 인터페이스를 먼저 파악합니다.
2. **코드 작성**: 목표에 맞게 C# 스크립트를 작성하거나 수정합니다.
3. **컴파일 검증**: 코드를 수정한 후에는 **반드시 터미널에서 `.claude\scripts\check_compile.ps1`을 실행**하여 문법 에러가 없는지 스스로 확인하세요.
4. **오류 자동 수정**: 만약 스크립트 실행 결과에 `error CS...` 가 포함되어 있다면, 에러 로그를 분석하여 스스로 코드를 수정하고 다시 3번으로 돌아가 검증합니다. (최대 3회 반복)
5. **완료 및 가이드**: 컴파일 에러 없이 완벽히 통과되면 사용자에게 작업 완료를 알리고, 유니티 에디터 창에서 마무리해야 할 작업(Inspector 설정 등)을 리스트업하여 전달합니다.

---

## 💻 유니티 코딩 컨벤션
- **성능 최적화**: `Update()` 내에서 `GetComponent<T>()`, `FindObjectOfType<T>()`, `GameObject.Find()` 호출 금지. `Awake()`나 `Start()`에서 캐싱하여 사용.
- **직렬화**: 에디터에서 접근/수정해야 하는 변수는 `public` 대신 `[SerializeField] private` 형태로 선언.
- **안전한 참조**: 외부 오브젝트/컴포넌트 참조 시 항상 `null` 체크 수행.
- **입력 시스템**: New Input System (UnityEngine.InputSystem) 사용 중. Legacy Input 사용 금지.
- **모듈형 설계**: 공격/대쉬 등 교체 가능한 능력은 추상 기반 클래스(BaseMeleeAttack, BaseDash)를 상속하여 구현.

---

## 📁 주요 경로 정보
- 스크립트 위치: `Assets/Scripts/` (하위 폴더로 분류)
- 자동화 스크립트 위치: `/.claude/scripts/`
