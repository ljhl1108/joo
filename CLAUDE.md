# OnionCat — Claude Code 지침서

게임 컨셉 상세는 `GameConcept.md` 참고.

---

## 역할

버그 없는 C# 코드 작성, 기존 시스템과의 호환성 유지.
코드 수정 후 반드시 `.claude/scripts/check_compile.ps1` 실행으로 컴파일 검증.

---

## 안전 수칙

- `.unity` / `.prefab` 파일은 텍스트로 직접 수정 금지 (YAML 파싱 오류 위험)
- `[SerializeField]` 변수가 생기면 "유니티 에디터에서 드래그 앤 드롭 설정 필요"라고 명시

---

## 경로 정보

| 항목 | 경로 |
|------|------|
| Unity 프로젝트 | `C:\workspace\unity\Onioncat_AG` |
| 문서 / 설계 워크스페이스 | `C:\workspace\claude\Game_Develop\OnionCat` |
| 스크립트 | `C:\workspace\unity\Onioncat_AG\Assets\Scripts\` |
| 컴파일 체크 스크립트 | `.claude\scripts\check_compile.ps1` |
| GitHub 저장소 | `https://github.com/ljhl1108/joo` |

---

## 일일 루틴 (자동화)

매일 오전 9시(서울) 클라우드 자동 실행. 컴퓨터 꺼져있어도 동작.
결과 확인: `claude.ai/code/routines`

| 항목 | 내용 |
|------|------|
| 루틴 ID | `trig_01RUueN3etcTT1WNuSWwJCEN` |
| 저장소 | `https://github.com/ljhl1108/joo` |
| 작업 | 로그라이크 게임 리서치 → `Design/IdeaPool/` + `Design/References/` 업데이트 |
| 규칙 | `Design/01~05_*.md` 메인 파일은 건드리지 않음. IdeaPool만 업데이트. |
| 로컬 반영 | `git pull` 실행 |

---

## 코딩 컨벤션

- `Update()` 내 `GetComponent` / `FindObjectOfType` / `GameObject.Find` 금지 → `Awake()`에서 캐싱
- Inspector 노출 변수는 `public` 대신 `[SerializeField] private`
- 외부 참조 시 항상 null 체크
- 입력: New Input System (UnityEngine.InputSystem) — Legacy Input 금지
- 교체 가능한 능력은 추상 기반 클래스 상속 구조 유지

---

## 작업 워크플로우

1. 관련 기존 코드 파악 (상속 구조, 인터페이스)
2. C# 스크립트 작성 / 수정
3. `check_compile.ps1` 실행 → 컴파일 검증
4. 에러 시 수정 후 3번 반복 (최대 3회)
5. 통과 시 유니티 에디터 Inspector 설정 필요 항목 안내
6. **유니티 에디터에서 해야 할 작업이 있으면 반드시 `Guides/` 폴더에 단계별 `.md` 가이드 파일 생성**
   - 파일명 예시: `main_menu_setup.md`, `animator_setup.md`
   - 완료된 가이드는 `Guides/Done/` 폴더로 이동
   - 형식: 체크박스(`[ ]`) + 단계별 설명
