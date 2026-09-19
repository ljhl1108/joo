# OnionCat — Claude Code 지침서

게임 컨셉 상세는 `GameConcept.md`, 로드맵/할일은 `TODO.md` 참고.

---

## 역할

버그 없는 C# 코드 작성, 기존 시스템과의 호환성 유지.
**유니티 에디터 조작도 직접 수행** (아래 Unity CLI 섹션 참고) — 가이드 문서만 쓰고 넘기지 말 것.

---

## 경로 정보

| 항목 | 경로 |
|------|------|
| Unity 프로젝트 | `C:\workspace\unity\Onioncat_AG` (**git 저장소, 원격 없음**) |
| 문서 / 설계 워크스페이스 | `C:\workspace\claude\Game_Develop\OnionCat` (**git, → GitHub**) |
| 스크립트 | `C:\workspace\unity\Onioncat_AG\Assets\Scripts\` |
| **Unity CLI** | `C:\Users\feedb\AppData\Local\Unity\bin\unity.exe` (**PATH에 없음 — 전체 경로로 호출**) |
| GitHub 저장소 (문서) | `https://github.com/ljhl1108/joo` |

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
- **시간 대기는 `sleep` 대신 `wait_for`** — 예: `{"member":"GameManager.Instance.State","op":"equals","value":"Victory"}`.
  단 `findType` 대상 멤버는 **public 읽기 가능 멤버만** (private 필드 불가)
- **플레이 테스트 중 고양이 생존**: `typeof(PlayerHealth).GetProperty("CurrentHealth").SetValue(ph, 999)` — 적을 죽여야 하는 테스트용
- 파괴적 명령은 `--confirm` 필요. 먼저 `--dry_run`으로 확인할 것
- **MCP `eval`에서는 `using` 문 불가** → `UnityEngine.InputSystem.Keyboard`처럼 전체 이름으로 쓸 것. 기본 타임아웃 5초라 재임포트 등은 `timeout`을 늘릴 것
- **입력 시뮬레이션 불가**: 에디터가 백그라운드면 가상 키 입력이 액션까지 전달되지 않는다. 조작 확인은 사용자에게 요청
- **캡처 `save_path`는 `Assets/` 기준이고 `..` 불가** → 저장 후 반드시 `AssetDatabase.DeleteAsset`으로 지울 것
- **플레이 테스트 시 적을 먼저 제거**: 입력 없이 서 있는 고양이는 약 5초 만에 슬라임에게 죽는다
- **`eval`은 게임 스크립트 타입을 직접 참조 가능** (`GameManager.Instance`, `UnityEngine.Object.FindFirstObjectByType<PlayerHealth>()`).
  단, 방금 만든 스크립트는 recompile 후에 쓸 것. private 메서드는 리플렉션으로 호출해 입력 없이 로직 검증
- **씬 diff가 수천 줄이어도 당황하지 말 것**: 오브젝트를 추가하면 Unity가 파일 내 순서를 재정렬한다.
  `grep -c '^--- !u!1 &'`로 GameObject 수가 (이전 + 추가분)과 맞는지, 삭제된 이름이 다시 추가됐는지 확인
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
- 유니티 프로젝트는 원격이 없으므로 **push 하지 말 것** (로컬 커밋만)

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
- **입력**: 컨트롤 스킴 `Cat`(키보드+게임패드) / `Onion`(마우스). 고양이 키보드 = WASD / Space 대쉬 / F 할퀴기
- **UI 문구는 영어로** — TMP 폰트에 한글 글리프가 없음 (로컬라이제이션 작업 전까지)
- **PPU 32** 고정 (타일 1칸 = 32px = 1유닛). Pixel Perfect Camera 640×360

---

## 작업 워크플로우

1. 관련 기존 코드 파악 (상속 구조, 인터페이스)
2. 에디터 상태가 필요하면 **CLI로 직접 조사** (`get_scene_hierarchy` 등) — 추측하지 말 것
3. C# 스크립트 작성 / 수정
4. `recompile` → `console --level Error`로 검증, 에러 시 수정 반복 (최대 3회)
5. Inspector 연결·레이어·임포트 설정은 **CLI로 직접 수행**
6. 가능하면 `editor_play`로 실제 동작까지 검증 후 `editor_stop`
7. `save_scene` → `git diff` 확인 → 커밋
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
| 규칙 | `Design/01~05_*.md` 메인 파일은 건드리지 않음. IdeaPool만 업데이트 |
| 로컬 반영 | `git pull` |

### 파일 정리 규칙

- `Design/IdeaPool/` 루트 = 이번 달 파일. 월이 끝나면 `YYYY-MM/` 폴더로 아카이브
- 루틴이 `Design/References/` 루트에 게임 파일을 만들면 `Game/`으로 이동
- 같은 게임을 재리서치한 중복이 생길 수 있음 — 최신본을 메인으로 두고 구본은 `<details>`로 보존
