# 메인 메뉴 씬 설정 가이드

> 진행 상태: `[ ]` 미완료 · `[x]` 완료
> 완료 후 이 파일을 `Guides/Done/` 폴더로 이동

---

## [ ] 1. 메인 메뉴 씬 생성

1. `File → New Scene`
2. **Basic 2D (URP)** 선택
3. `File → Save As` → 이름: `MainMenu`
4. `Assets/Scenes/` 폴더에 저장

---

## [ ] 2. UI 배치

Canvas 없으면 Hierarchy 우클릭 → `UI → Canvas`

Canvas 안에 다음 순서로 생성:

| 이름 | 생성 방법 | 텍스트 내용 |
|------|-----------|-------------|
| `TitleText` | `UI → Text - TextMeshPro` | OnionCat |
| `StartButton` | `UI → Button - TextMeshPro` | Start |
| `QuitButton` | `UI → Button - TextMeshPro` | Quit |

**위치 잡기 (대략):**
- TitleText: 화면 중앙 위쪽 (Pos Y: 80)
- StartButton: 중앙 (Pos Y: 0)
- QuitButton: 중앙 아래 (Pos Y: -80)

---

## [ ] 3. MainMenuUI 스크립트 연결

1. Canvas 선택 → `Add Component → MainMenuUI`
2. Inspector에서:
   - `Start Button` → StartButton 드래그
   - `Quit Button` → QuitButton 드래그
   - `Game Scene Name` → `SampleScene` 확인

---

## [ ] 4. Build Settings에 씬 등록

`File → Build Settings` (단축키: **Ctrl + Shift + B**)

1. **MainMenu 씬을 먼저 드래그** → 인덱스 0
2. **SampleScene 드래그** → 인덱스 1

> 인덱스 0이 게임 실행 시 가장 먼저 열리는 씬

---

## [ ] 5. GameOverPanel에 Main Menu 버튼 추가

SampleScene으로 돌아와서:

1. `GameOverPanel` 안에 `UI → Button - TextMeshPro` 추가
2. 이름: `MainMenuButton`, 텍스트: `Main Menu`
3. `HUD`의 `GameOverManager` Inspector에서:
   - `Main Menu Button` → MainMenuButton 드래그

---

## [ ] 6. 테스트

1. Play 버튼 → MainMenu 씬이 열리는지 확인
2. Start 버튼 → SampleScene으로 이동하는지 확인
3. 게임 중 죽으면 → Game Over 패널에서 Main Menu 버튼 → MainMenu로 복귀하는지 확인
