# Design 폴더 구조

```
Design/
├── 01_Characters.md   ← 메인 설계 파일 (직접 관리, 루틴이 건드리지 않음)
├── 02_Enemies.md
├── 03_Maps.md
├── 04_Combat.md
├── 05_Story.md
│
├── IdeaPool/          ← 일일 루틴이 매일 1개씩 생성
│   ├── (YYYY-MM-DD.md — 이번 달 신규 파일은 루트에 쌓임)
│   ├── 2026-05/       ← 월별 아카이브
│   ├── 2026-06/
│   └── 2026-07/
│
└── References/
    ├── Game/          ← 게임 레퍼런스 (Hades.md, Dead_Cells.md …)
    └── Tech/          ← 기술 레퍼런스 (Parry_Shield_System.md …)
```

## 운영 규칙

1. **IdeaPool은 받은 편지함** — 루틴이 매일 아이디어를 쌓는다. 검토 후 채택할 것은
   `01~05` 메인 파일에 옮겨 적고, 월이 끝나면 해당 월 파일들을 `YYYY-MM/` 폴더로 이동.
2. **루틴이 References 루트에 새 게임 파일을 만들면** 월별 정리 때 `Game/`으로 이동.
3. **메인 파일(01~05)이 유일한 진실** — IdeaPool에만 있는 아이디어는 아직 채택 전.
4. 전체 컨셉 요약은 저장소 루트의 `GameConcept.md` 참고.
