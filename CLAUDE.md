# OnionCat — Claude Code 지침서

게임 컨셉 상세는 `GameConcept.md`, 로드맵/할일은 `TODO.md`, 아트 할일은 `TODO_Art.md` 참고.

---

## 역할

버그 없는 C# 코드 작성, 기존 시스템과의 호환성 유지.
**유니티 에디터 조작도 직접 수행** (아래 Unity CLI 섹션 참고) — 가이드 문서만 쓰고 넘기지 말 것.

---

## 경로 정보

| 항목 | 경로 |
|------|------|
| Unity 프로젝트 | `C:\workspace\unity\Onioncat_AG` (**git, → GitHub 비공개 저장소, 브랜치 `master`**) |
| 문서 / 설계 워크스페이스 | `C:\workspace\claude\Game_Develop\OnionCat` (**git, → GitHub**) |
| 스크립트 | `C:\workspace\unity\Onioncat_AG\Assets\Scripts\` |
| **Unity CLI** | `C:\Users\feedb\AppData\Local\Unity\bin\unity.exe` (**PATH에 없음 — 전체 경로로 호출**) |
| GitHub 저장소 (문서) | `https://github.com/ljhl1108/joo` (브랜치 `main`) |
| GitHub 저장소 (유니티) | `https://github.com/ljhl1108/OnionCat-Unity` (**Private**, 브랜치 `master`) |

- 두 저장소 모두 git으로 관리됨. **에디터를 조작하기 전에 작업트리가 깨끗한지 확인**하면 실패 시 `git checkout`으로 되돌릴 수 있다.
- 유니티 버전 `6000.3.9f1`, URP 2D, New Input System.

---

## Unity CLI — 에디터 직접 조작

Pipeline 패키지(`com.unity.pipeline`)를 통해 **실행 중인 에디터**에 151개 도구로 접근한다.
씬/프리팹/레이어/임포트 설정을 직접 읽고 쓰고, 플레이 모드를 돌려 검증할 수 있다.

### 기본 호출 형태

```bash
export MSYS_NO_PATHCONV=1                      # 필수 (아래 함정 참고)
U="/c/Users/feedb/AppData/Local/Unity/bin/unity.exe"
P="C:/workspace/unity/Onioncat_AG"

"$U" pipeline list --no-banner                 # 연결 상태 (Server Reachable 확인)
"$U" list --no-banner                          # 사용 가능한 도구 151종
"$U" command --query <검색어> --detail full --project-path "$P"   # 특정 도구 파라미터 조회
"$U" cmd <도구> --<파라미터> <값> --project-path "$P" --no-banner --result-only
```

### 시작 절차

1. `unity pipeline list` → `Server Reachable=true` 확인
2. 에디터가 안 떠 있으면 **직접 켠다**: `"$U" open "$P"` (사용자에게 요청하지 말 것)
3. 기동/도메인 리로드 후 **Pipeline 서버가 올라오기까지 약 8초** — 재시도 루프로 대기
4. 작업 시작 시 한 번 켜두고 유지. 매번 껐다 켜면 대기 시간만 쌓인다

### ⚠️ 함정 (전부 실제로 겪은 것)

- **`MSYS_NO_PATHCONV=1` 없으면** Git Bash가 `/Room_01/ExitDoor`를 `C:/Program Files/Git/Room_01/ExitDoor`로 바꿔버린다
- **`--project-path`를 항상 붙일 것.** 없으면 "현재 디렉터리가 속한 프로젝트"를 찾는데, 작업 폴더(문서)와 유니티 프로젝트 경로가 다르다
- **모르는 파라미터 키는 조용히 무시된다.** 에러 대신 `"No changes specified"`가 뜨므로 성공으로 착각하기 쉽다.
  → **`dry_run` 결과에 `"dryRun": true`가 떠야 제대로 인식된 것**
- **`eval`에서 `Object`는 이름 충돌** → `UnityEngine.Object.DestroyImmediate(...)`처럼 명시
- **씬 변경 후 `save_scene` 호출 필수.** 안 하면 에디터 메모리에만 남는다
- **백그라운드 에디터에서는 플레이 모드 게임 시간이 멈춘다** (Player Settings `Run In Background` 꺼짐).
  플레이 테스트 시작 직후 `eval`로 `UnityEngine.Application.runInBackground = true;` (런타임 값만, 설정 파일 불변)
- **캡처 전 일시정지 요령**: `isPaused = true` 직후엔 TMP 메시가 아직 없어 글자가 안 찍힘 →
  `UnityEditor.EditorApplication.Step()`으로 한 프레임 진행 후 `capture_game_view`
- **시간 대기는 `sleep` 대신 `wait_for`** — 예: `{"member":"GameManager.Instance.State","op":"equals","value":"Victory"}`.
  단 `findType` 대상 멤버는 **public 읽기 가능 멤버만** (private 필드 불가)
- **플레이 테스트 중 고양이 생존**: `typeof(PlayerHealth).GetProperty("CurrentHealth").SetValue(ph, 999)` — 적을 죽여야 하는 테스트용
- 파괴적 명령은 `--confirm` 필요. 먼저 `--dry_run`으로 확인할 것
- **MCP `eval`에서는 `using` 문 불가** → `UnityEngine.InputSystem.Keyboard`처럼 전체 이름으로 쓸 것. 기본 타임아웃 5초라 재임포트 등은 `timeout`을 늘릴 것
- **입력 시뮬레이션 불가**: 에디터가 백그라운드면 가상 키 입력이 액션까지 전달되지 않는다. 조작 확인은 사용자에게 요청
- **캡처 `save_path`는 `Assets/` 기준이고 `..` 불가** → 저장 후 반드시 `AssetDatabase.DeleteAsset`으로 지울 것
- **사용자가 플레이 중일 때 recompile 금지**: 플레이 모드 중 도메인 리로드가 일어나면 `GameManager.Instance` 등 static이 null이 되어 게임이 반쯤 죽는다.
  `editor_status`로 playing 여부를 먼저 확인하고, 플레이 중이면 컴파일·플레이 모드 조작을 하지 말 것 (사용자 테스트를 방해함)
- **플레이 테스트 시 적을 먼저 제거**: 입력 없이 서 있는 고양이는 약 5초 만에 슬라임에게 죽는다
- **`eval`은 게임 스크립트 타입을 직접 참조 가능** (`GameManager.Instance`, `UnityEngine.Object.FindFirstObjectByType<PlayerHealth>()`).
  단, 방금 만든 스크립트는 recompile 후에 쓸 것. private 메서드는 리플렉션으로 호출해 입력 없이 로직 검증
- **코드의 기본값을 바꿔도 이미 저장된 프리팹·씬 값이 우선한다** (`[SerializeField] float x = 9f`를 14로 고쳐도 프리팹은 9 유지).
  수치를 바꿨으면 **프리팹/씬 값도 SerializedObject로 함께 갱신**하고, 플레이에서 실제 값을 확인할 것
- **`EditorApplication.Step()`은 일시정지 상태를 남긴다** → 이후 Start/Update가 전혀 안 돌아 "적이 안 나온다"처럼 보인다.
  캡처 후에는 반드시 `isPaused = false`로 되돌릴 것
- **씬 diff가 수천 줄이어도 당황하지 말 것**: 오브젝트를 추가하면 Unity가 파일 내 순서를 재정렬한다.
  `grep -c '^--- !u!1 &'`로 GameObject 수가 (이전 + 추가분)과 맞는지, 삭제된 이름이 다시 추가됐는지 확인
- **에셋스토어 패키지가 ProjectSettings를 덮어쓸 수 있다** (실제로 Cainos 팩이 레이어·태그·물리·품질 설정을 날림).
  증상: 월드가 전혀 렌더링되지 않음. 확인: 임포트 직후 `git status ProjectSettings`.
  복구: 에디터 종료 → `git checkout -- ProjectSettings` → 에디터 재기동 (ProjectSettings는 기동 시 읽으므로 재시작 필수)
- **대용량 패키지 임포트 중에는 MCP 명령이 모두 타임아웃된다** (메인 스레드 점유).
  `du -s Library`가 안정될 때까지 기다린 뒤 진행할 것
- **유니티 저장소에는 git 사용자 설정이 없다** → 직전 커밋 작성자를 재사용:
  `git -c user.name="$(git log -1 --format=%an)" -c user.email="$(git log -1 --format=%ae)" commit ...`

### 알아낸 파라미터 형식

```bash
# 레이어/태그
--settings '{"setLayers":[{"index":8,"name":"Wall"}],"addTags":["Foo"],"removeTags":["Bar"]}'

# 자주 쓰는 도구
get_scene_hierarchy / find_gameobjects / get_component_properties   # 씬 조사
set_layer / set_tag / set_transform / set_serialized_field          # 오브젝트 수정
create_gameobject / add_component / create_prefab                   # 생성
recompile → recompile_status → console --level Error                # 컴파일 검증
editor_play / editor_stop / screenshot / capture_game_view          # 플레이 검증
batch                                                               # 트랜잭션 (실패 시 전체 롤백)
```

### 컴파일 검증

```bash
"$U" cmd recompile --project-path "$P" --no-banner --result-only
"$U" cmd recompile_status --project-path "$P" --no-banner --result-only     # completed 까지 폴링
"$U" cmd console --level Error --tail 20 --project-path "$P" --no-banner --result-only
```

`.claude/scripts/check_compile.ps1`도 여전히 동작하지만, 에디터가 떠 있으면 위쪽이 빠르고 정확하다.

---

## 픽셀아트 파이프라인

| 항목 | 값 |
|------|-----|
| Aseprite | `D:\SteamLibrary\steamapps\common\Aseprite\Aseprite.exe` (1.3.18.5, Steam판) |
| 유니티 임포터 | `com.unity.2d.aseprite` 3.0.1 — **`.aseprite` 파일을 `Assets/`에 넣으면 스프라이트·애니메이션 클립 자동 생성** |
| 작업 분담 | 그림은 사람이 Aseprite에서, 반복 작업(슬라이스·팔레트 검사·유니티 연결·프리팹 교체)은 CLI로 자동화 |

```bash
A="/d/SteamLibrary/steamapps/common/Aseprite/Aseprite.exe"
"$A" --batch --list-layers <파일>             # 레이어 확인
"$A" --batch <파일> --list-tags --list-slices  # 애니메이션 태그·슬라이스 확인
"$A" --batch <파일.aseprite> --sheet out.png --data out.json --sheet-type packed  # 시트 추출
"$A" --batch --script <스크립트.lua> <파일>    # Lua 스크립트 실행 (일괄 편집)
```

- **Aseprite 태그 이름이 유니티 애니메이션 클립 이름이 된다** → `idle` / `walk` / `attack` 규칙으로 달 것
- PixelLab 확장은 구독 해지 후 제거됨 (2026-09-24). 백업: `%APPDATA%\Aseprite\pixellab_disabled_backup`
  → 남겨두면 CLI 배치 실행마다 `handle-pose.lua` 에러가 출력된다
- 구매한 에셋스토어 패키지는 계정에 묶여 있어 로컬에서 확인 불가. 확인하려면 Package Manager → My Assets에서 다운로드 필요

---

## 설치된 Unity 스킬

`~/.claude/skills/`에 15종. **세션(프로세스) 시작 시 로드**되므로 설치 직후에는 안 잡힌다.

`unity-cli`(CLI 내장본) + `2d-pixel-perfect`, `manage-sprite-atlas`, `sprite-editor`,
`sprite-segment-3x3grid`, `tilemap-palette-create`, `tilemap-ruletile-createempty`,
`audio-setup-mixers`, `optimize-audio`, `ui-ugui`, `optimize-text-mesh-pro`,
`localization`, `urp-postprocessing`, `unity-package-management`, `generate-editor-search-query`

```bash
# 추가 설치 — -s 는 쉼표 목록 불가, 플래그를 반복해야 한다
npx skills add Unity-Technologies/skills -g -a claude-code -y --copy -s <이름> -s <이름2>
```

`--copy` 권장 (Windows에서 심볼릭 링크는 관리자 권한이 필요할 수 있음).
유니티 쪽 YAML 오류로 `physics-3d-collision`, `tilemap-ruletile-createfromsegment`, `ui`, `ui-imgui`는 설치 불가.

### 업데이트는 전부 수동

```bash
"$U" pipeline list          # Update Available 열 확인 → "$U" pipeline upgrade
"$U" skill refresh          # CLI 업데이트 후 내장 스킬 재생성 (잊기 쉬움)
npx skills update           # npx로 받은 스킬 갱신
```

---

## 안전 수칙

- `.unity` / `.prefab` / `.asset` 파일을 **텍스트로 직접 수정 금지** → 반드시 Unity CLI 도구 사용
- 에디터를 조작하는 변경 후에는 **`git diff`로 실제 파일 변경을 확인**할 것 (의도치 않은 대량 변경 탐지)
- `[SerializeField]` 변수가 생기면 CLI로 직접 연결하고, 못 하면 그때 안내
- 유니티 프로젝트는 **비공개** 원격 `OnionCat-Unity`에 커밋 후 push (2026-09-27부터)
- ⚠️ **유니티 저장소를 절대 공개(Public)로 바꾸지 말 것** — 구매 에셋(Honeti GUI, SPUM)과 재배포 금지 에셋(Cainos)이 들어 있어 공개 시 라이선스 위반

---

## 코딩 컨벤션

- `Update()` 내 `GetComponent` / `FindObjectOfType` / `GameObject.Find` 금지 → `Awake()`에서 캐싱
- Inspector 노출 변수는 `public` 대신 `[SerializeField] private`
- 외부 참조 시 항상 null 체크
- 입력: New Input System (UnityEngine.InputSystem) — Legacy Input 금지
- 교체 가능한 능력은 추상 기반 클래스 상속 구조 유지

### 프로젝트 고유 규칙

- **레이어**: 8 Wall / 9 Player / 10 PlayerAttack / 11 PlayerProjectile / 12 Enemy / 13 EnemyProjectile / 14 Props
- **태그**: Player, Enemy, Wall (코드가 `CompareTag`로 참조하므로 레이어와 별개로 유지)
- 투사체는 `targetTag`로 피아 구분: `Projectile_Seed`=플레이어용, `Projectile_Seed 1`=적용
- **게임 상태 전환은 `GameManager.Instance.ChangeState()`로만.** `Time.timeScale`을 직접 바꾸지 말 것
- 상태에 반응하는 시스템은 `GameManager.OnStateChanged`를 `OnEnable/OnDisable`에서 구독/해제
- 런 누적 데이터는 `GameManager.Instance.Run`(RunData). 씬 이름은 `SceneNames` 상수 사용
- **런타임 생성·제거가 잦은 오브젝트는 `PoolManager.Spawn/Despawn`** (Instantiate/Destroy 금지). 풀링 대상은 상태 초기화를 `OnEnable`에서
- **플레이어 행동 입력**(공격·대쉬·발사·실드)은 `GameManager.IsGameplayActive`로 막을 것 (업그레이드 선택·일시정지 중 새지 않게)
- **업그레이드 스탯**: 기본값은 Inspector, 보정은 `PlayerStats.Current`에서 읽어 합산/곱셈. 컴포넌트 필드를 직접 바꾸지 말 것.
  새 스탯 = `StatType` 추가 + `PlayerStats.Modify` 분기 + 사용하는 곳에서 읽기
- **입력**: 컨트롤 스킴 `Cat`(키보드·게임패드 둘 다 선택) / `Onion`(마우스). 배치는 `CoopInputLayout`이 자동 전환
  - 패드 모드(패드 연결): 고양이 = 패드만 / 양파 = 마우스 + Q W E R 스킬 · 1~5 가방 · Space 합동기
  - 고양이 특수 공격(야성 게이지, `CatSpecial`) = 키보드 **왼쪽 Ctrl** / 패드 **Y** (Player1/Special). 장비 효과 발동 `EffectTrigger.SpecialHit`
  - 키보드 모드(패드 없음): 고양이 = WASD · Space 대쉬 · **왼쪽 Shift 할퀴기 · 왼쪽 Ctrl 특수 공격** · Q 던지기 · E 합동기 · Z/X 가방
  - **걷어차기는 꺼 둠** (2026-10-21, `GameFeatures.Kick = false` — 키 F·패드 LB는 남아 있지만 무시). 걷어차기에 기대는 장비가 생기면 `GameFeatures.IsAvailable`이 보상에서 제외
  - 적 크기는 4등급만 (작음 0.5 · 보통 0.6 · 큼 0.75 · 보스 1.1) — `EnemyBuilder.SizeOf`
    / 양파 = 마우스 + 1~4 스킬 · 6~0 가방 · 휠 클릭 합동기 (W가 이동과 겹쳐서 숫자로)
  - 양파 키보드 키는 페어링과 무관한 독립 InputAction(`OnionInputKeys`)으로 읽는다
- **코어 시스템** (설계 `Design/04_Combat.md`·`05_Items.md`, 구현 목록 `Design/00_Implemented.md`, 테스트 결과 `Guides/Done/v4_playtest.md`)
  - 성장 3축: 체급(`StatUpgrade`) / 패시브(`Passive`, 세트 햇살·바람 — 고양이·양파 조각 합산) / 특수(양파 `OnionSkill`, 고양이 `ClawStyle`)
  - 보상: 방마다 고양이·양파가 **동시에** 각자 3장 중 1장 (`UpgradeSelectUI`), 출구 표식 = 다음 방 중점 축(`RewardAxis`)
  - 세트 보너스는 `PassiveHost.Recalculate` → `CombatModifiers`(정적, 읽기 전용)로 반영
  - 적에게 피해를 줄 때 `TakeDamage(..., Attacker.Cat/Onion)`을 넘길 것 — 협동 콤보가 "누가 때렸나" 기준
  - 적 목록은 `EnemyBase.Active` (FindObjectsByType 금지). 상태이상은 `ApplyBurn / ApplySlow / ApplyStun / Launch`
    (`Launch(..., interruptTelegraph: true)`는 걷어차기 전용 — 예고를 끊음. 보스는 `kickInterruptsTelegraph` 끔)
  - 새 카드 = `OnionSkill` / `Passive` / `ClawStyle` / `StatUpgrade` 에셋 → `Assets/Data/RewardTable.asset`의 축별 목록에 추가
    새 아이템 = `ItemData` 상속 → `itemDrops`. **ScriptableObject는 클래스마다 같은 이름 파일 필수**
  - 런 상태(스킬·패시브·할퀴기 변형·공유 가방·게이지)는 `RunData`에, 쿨다운처럼 씬에 묶인 값은 컴포넌트에
  - **성장은 장비 v4** (`Design/05_Items.md`): `GearItem` 에셋(`Assets/Data/Gear`) → `RewardTable.catGear/cropGear`. 능력치·효과·할퀴기·스킬은 `RunData.RecomputeGear`가 장비에서 다시 계산 (Passive·ClawStyle을 직접 넣지 말 것)
  - **장비·효과·스킬 콘텐츠는 `Assets/Editor/ContentBuilder.cs` 표에서 고치고 메뉴 `OnionCat > Content > Build v4 Content`** (에셋·보상표·GameDatabase까지 갱신). 효과는 조합형 `GearEffect`(발동 → 행동 → 대상), 상태이상은 `EnemyBase.Status.cs`, 세트 단계는 `CombatModifiers.Has(세트, 단계)`
  - **새 장비·효과·소모품을 손으로 만들면 메뉴 `OnionCat > Rebuild Game Database`** (중간 저장이 이름으로 찾음)
  - 런 순서는 `DungeonManager.stagePlan` 문자열, 특수 방(보물·상점·휴식)은 `Room_Special` 하나를 돌려 씀. 게임 상태 `Inventory` = 장비 화면
  - 코어 HUD(`CoreHUD`)는 코드로 생성. HUD 캔버스는 **1920×1080 고정 픽셀**이라 `uiScale` 2배 기준으로 배치
  - 대쉬는 충전식(`Dash_Default.Charges`), 고양이 발밑 탄창은 `CatPips` (고양이 스프라이트 바닥에 자동 정렬)
  - 플레이 테스트 메뉴 `OnionCat > Debug` (Kick Test, 세트·할퀴기 변형 지급, 게이지, 적 제거, 무적)
- **사운드** (2026-10-04, 확인 가이드 `Guides/sound_check.md`)
  - 효과음 `Sfx.Play(SfxId.X)`, 음악 `Music.Play(MusicId.X)` — `AudioManager`가 자동 생성·씬 유지 (씬에 배치 불필요)
  - 새 효과음 = `SfxId` 추가 → `Assets/Audio/SFX/<이름>_0.ogg …` → 메뉴 **OnionCat > Audio > Rebuild Sound Bank**
  - 음량·음높이·연타 간격은 `Assets/Resources/Audio/SoundBank.asset`. 음원은 전부 CC0 (`Assets/Audio/LICENSE_AUDIO.txt`에 출처 기록 유지)
  - Claude는 소리를 들을 수 없음 → 소리 품질 판단은 사람에게
- **방 배치** (2026-10-04, 가이드 `Guides/room_layout.md`)
  - 방 모양은 `Assets/Data/RoomLayouts/*.asset`(글자 지도, W 벽·X 벽 덩어리·D 출구 포함 시 크기·모양 자유 — 최대 40×20) → 메뉴 **OnionCat > Rooms > Apply Room Layouts**로 씬에 찍는다. 씬의 Layout 자식을 손으로 고치지 말 것 (다시 적용하면 지워짐)
  - 적은 지도 글자로 (1 슬라임·2 원거리·3 분열·4 방패병·B 보스). 런의 방 순서는 `DungeonManager`가 시작방 + 전투방 풀(난이도 tier) + 보스방으로 무작위 생성
  - **정렬 순서 구간**: 바닥 -1000~-900 (바닥 타일·구덩이·장판·벽 타일) / 서 있는 물체 -100~99 (`YSort`가 발 높이로 보정) / 항상 위 100+ (투사체·이펙트·숫자·라벨). 새 그림을 추가할 때 이 구간을 지킬 것
  - 장애물 = Wall 레이어·태그(탄 막음·CRASH), 구덩이 = `Pit`(Props 레이어, 걷어찬 적만 낙사, 보스 `immuneToPits`)
  - Unity 6에서 스프라이트 9-slice 테두리는 `TextureImporter.spriteBorder`가 안 먹힘 → `SpriteDataProviderFactories`로 설정
- **UI 문구는 한글로** (2026-10-13~) — 글꼴은 **Galmuri11** (`Assets/Fonts/Galmuri`, SIL OFL)로 통일, TMP 기본·대체 폰트로 지정. 언어 선택(영어 등)은 나중에 로컬라이제이션으로
  - Galmuri SDF는 동적 아틀라스라 플레이하면 에셋이 커진다 → 커밋 전에 `ClearFontAssetData(true)`로 비우기 (6KB)
- **적 콘텐츠** (2026-10-15, 목록 `Design/02_Enemies_Content.md`)
  - 새 적 = `Assets/Editor/EnemyBuilder.cs` 표에 한 줄 (조합형 `ModularEnemy`: 움직임 + 공격 + 특성) → 메뉴 **OnionCat > Enemies > Build Enemies** (프리팹 `Prefabs/Enemies` + 명단 `Resources/EnemyRoster` 갱신)
  - 고양이를 아프게 하는 장판·충격은 `EnemyHazard` (적을 아프게 하는 건 `EffectZone`). 방의 적 자리는 `EnemyRoster.Resolve`가 스테이지 테마에 맞게 일부 교체
  - 조합형 적은 `EnemyBase`의 private 메시지 메서드(Update·OnCollisionEnter2D)를 다시 정의하지 말 것 → `FixedUpdate` override와 `InterceptDamage`·`OnDamaged` 훅을 쓴다
  - **체력 기준선** (2026-10-22): 표의 hp는 예전 눈금, 빌드 시 ×5 (소환물·보스 ×3, `EnemyBuilder.HpOf`). `enemies.csv` 체력 칸은 최종값 → CSV를 표에 옮길 때 5(또는 3)로 나눌 것. 기존 적 5종은 메뉴 `Apply Size Classes To Old Enemies`가 크기·체력을 같이 넣음
  - **적 조합**: 전투방 70%는 `EnemyRoster.squads` (표 `EnemyBuilder.BuildSquads`, 스테이지 -1 공통·0~4 테마) → `EnemyRoster.ResolveRoom`
  - **물음표 방 손해 규칙**: 능력치 손해(최대 체력·받는 피해·대쉬 봉인 등)는 영구 금지 → `TimedEffects`로 "방 N개 동안"만. 바로 끝나는 손해(체력·씨앗·매복)는 OK. 매복 = `DungeonManager.StartAmbush(마릿수, 이기면)`
- **공용 데이터 표** (2026-10-18, `Design/Data/README.md`) — 사람과 같이 고치는 표. 적 `enemies.csv` · 아이템 `items.csv` · 세트 `sets.csv` · 스테이지 `stages.csv` · 고양이 `cats.csv`+`cat_weapons.csv` · 작물 `crops.csv`+`crop_seeds.csv` (고양이·작물은 아직 아이디어 — 구현 전)
  - 작업 시작 시 `git diff Design/Data`로 사람이 고친 칸 확인 (엑셀이 `2.0`→`2`처럼 숫자 모양만 바꾼 건 무시) → 적은 `EnemyBuilder.cs`, 아이템·세트는 `ContentBuilder.cs`·`PassiveSetBonus.cs`에 반영 후 빌드 메뉴, **'요청' 열은 처리하고 비운다**
  - 반대로 코드에서 적·아이템을 바꾸거나 추가하면 CSV에도 같은 내용 반영 (둘이 어긋나지 않게). ID·프리팹·에셋 열은 유지
  - CSV 저장은 `utf-8-sig`(BOM) + 쉼표 — 엑셀 호환. 보기 화면은 `python Design/Data/build_viewer.py` (HTML은 gitignore)
  - 사람이 엑셀로 열어 두면 파일이 잠긴다 (PermissionError) — 덮어쓰지 말고 닫아 달라고 할 것
- **한 판의 흐름** (2026-10-27 이야기 구조, `Design/07_StoryMeta.md` 1장): `StoryRoute`가 길을 만든다 — 스테이지와 마을이 번갈아 (농장(시작, 노트·온실·화분) → 1 → 2 → 마을 → 3·4 → 등대 입구 → 5 → 등대탑 → 6 최종), 테마는 무작위(고르기 없음). 이야기 단계 `MetaProgress.Chapter` 1~4가 판이 끝나는 마을을 정한다. 스테이지마다 갈림길 지도(`RunMap.cs`, 8층), 마을은 방 하나짜리 지도(`StepKind.Village`, `Room_Special` 재사용 — 등불·샘물·가판대). 방은 씬의 것을 재사용(`Room.ResetForReuse`). 지도 UI `MapScreen`(GameState.Map)
  - **빛 색깔 퀘스트**: 마을 등불에 작물의 빛(`LightColor`, 판마다 쌓여 섞임)을 비추면 다음 단계. 필요한 빛 `StoryRoute.NeedOf`, 작물 목록·빛 `StoryRoute.Crops` (지금 양파뿐 → 낼 수 있는 빛만 요구). 등대탑 = 작물 종류 모으기. 최종 보스 처치 = 엔딩
  - meta.json — **사람의 실제 진행이 들어 있음** (이야기 단계·등불 빛·파편·해금). 테스트 전에 백업하고 끝나면 되돌릴 것 + 에디터 메모리의 `MetaProgress.data`도 null로 (안 그러면 다음 저장 때 테스트 값이 다시 써짐). 디버그 메뉴 `OnionCat > Debug > Story` (사람용 안내 `Guides/story_debug.md`)
  - 보스는 자리별 `EnemyRoster.BossFor(RouteSlot)` (bossFirst/Middle/Last + 비어 있는 bossFinal)
  - **온실** (2026-10-23): 메인 메뉴 → `GreenhouseScreen`. 장비 `GearItem.UnlockCost` > 0이면 `MetaProgress`에서 해금하기 전까지 `RewardTable.Pool`에서 빠짐. 가격 표 `Editor/GreenhouseBuilder.cs` ↔ `items.csv` 해금 열. 퀘스트용 파편 수는 `fragmentsEarned`(써도 안 줄어듦). 테스트로 해금했으면 meta.json 되돌릴 것
  - 고르기 화면(지도·스테이지·물음표)은 `MapScreen` 하나 — 둘이 같으면 바로, 한 명이면 5초. 물음표 이벤트 `RunEvents.cs`, 새 방 모양 `RoomShapeBuilder.cs`, 덩어리 `RoomChunks`(템플릿 `?`)
- **타격감·연출 수치는 `Assets/Resources/HitFeelSettings.asset`** (플레이 중 조절 가능). 전체 조절 항목은 `Design/06_FeelParameters.md`
  - **조절 수치를 새로 만들거나 기본값을 바꾸면 `06_FeelParameters.md`에도 한 줄** (⚡ 에셋 / 🧩 씬·프리팹 / 🛠 코드 / 📊 CSV 표시 + 실제 저장된 값). 사람이 "그 수치 어디서 고쳐?"를 이 문서 하나로 찾게
- **PPU 32** 고정 (타일 1칸 = 32px = 1유닛). Pixel Perfect Camera 640×360

---

## 작업 워크플로우

1. 관련 기존 코드 파악 (상속 구조, 인터페이스)
2. 에디터 상태가 필요하면 **CLI로 직접 조사** (`get_scene_hierarchy` 등) — 추측하지 말 것
3. C# 스크립트 작성 / 수정
4. `recompile` → `console --level Error`로 검증, 에러 시 수정 반복 (최대 3회)
5. Inspector 연결·레이어·임포트 설정은 **CLI로 직접 수행**
6. 가능하면 `editor_play`로 실제 동작까지 검증 후 `editor_stop`
7. `save_scene` → `git diff` 확인 → 커밋 → push (유니티는 `master`, 문서는 `main`)
8. **사람이 판단해야 하는 것만** `Guides/`에 문서화
   - 예: 타일을 어디에 그릴지, 스프라이트를 어떤 걸 쓸지 같은 디자인 결정
   - 완료된 가이드는 `Guides/Done/`으로 이동
   - 형식: 체크박스(`[ ]`) + 단계별 설명

---

## 일일 루틴 (자동화)

매일 오전 9시(서울) 클라우드 자동 실행. 컴퓨터 꺼져있어도 동작.
결과 확인: `claude.ai/code/routines`

| 항목 | 내용 |
|------|------|
| 루틴 ID | `trig_01RUueN3etcTT1WNuSWwJCEN` |
| 작업 | 로그라이크 게임 리서치 → `Design/IdeaPool/` + `Design/References/` 업데이트 |
| 규칙 | `Design/00~07_*.md` 메인 파일은 건드리지 않음. IdeaPool만 업데이트 |
| 로컬 반영 | `git pull` |

### 파일 정리 규칙

- `Design/IdeaPool/` 루트 = 이번 달 파일. 월이 끝나면 `YYYY-MM/` 폴더로 아카이브
- 루틴이 `Design/References/` 루트에 게임 파일을 만들면 `Game/`으로 이동
- 같은 게임을 재리서치한 중복이 생길 수 있음 — 최신본을 메인으로 두고 구본은 `<details>`로 보존
