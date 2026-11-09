# OnionCat — 설계 문서

**고양이가 몸, 작물이 방패.** 두 명이 한 캐릭터를 조종하는 2인 협동 탑다운 로그라이크 (Unity 6, 픽셀 아트).

이 저장소는 **기획·설계 문서**만 담는다. 게임 프로젝트(유니티)는 비공개 저장소에 따로 있다.

---

## 어디서 무엇을 보나

| 알고 싶은 것 | 문서 |
|---|---|
| 어떤 게임인가 (한 장 요약) | [GameConcept.md](GameConcept.md) |
| 지금 무엇을 하고 있나 · 다음 할 일 | [TODO.md](TODO.md) |
| 그림 할 일 | [TODO_Art.md](TODO_Art.md) |
| 지금 게임에 실제로 들어간 것 · 최근 진행 | [Design/00_Implemented.md](Design/00_Implemented.md) |
| 설계 (왜 이렇게 만드나 · 앞으로 만들 것) | [Design/](Design/README.md) — 캐릭터 · 적 · 맵 · 전투 · 아이템 · 수치 · 이야기 · 한 판 흐름 |
| 같이 고치는 데이터 표 (적·아이템·배경…) | [Design/Data/](Design/Data/README.md) — 엑셀로 열고 `뷰어_갱신.bat`로 도감 보기 |
| 사람이 직접 해 볼 일의 안내서 | [Guides/](Guides/) (끝난 것은 `Guides/Done/`) |
| 매일 쌓이는 아이디어 | [Design/IdeaPool/](Design/IdeaPool/README.md) · [주제별](Design/IdeaPool/BY_TOPIC.md) |
| 조사한 게임·기술 | [Design/References/](Design/References/README.md) |
| Claude 작업 지침 (유니티 조작·코딩 규칙) | [CLAUDE.md](CLAUDE.md) |

## 표시 규칙 (모든 문서 공통)

| 표시 | 뜻 |
|---|---|
| ✅ | 구현됨 · 결정됨 |
| 🔶 | 잠정 — 해 보고 조정 |
| 📝 | 계획 · 아이디어 |
| ❓ | 결정 대기 |
| ⏸ | 만들었지만 꺼 둠 |
| 👤 / 🤖 / 🎨 | 사람이 할 일 / Claude가 할 일 / 그림이 필요 |

## 정리 도구

- **`문서_보기.bat`** — 이 저장소의 .md 문서를 도감처럼 보는 화면 (브라우저가 열림). 왼쪽 문서 목록 · 장마다 카드 · 오른쪽 목차 · 모든 문서 검색. **파일을 저장하면 1~2초 안에 화면이 저절로 바뀐다.** 창을 닫으면 꺼짐 (인터넷 필요 — 표시 도구를 cdnjs에서 받음)
- `python Design/tidy.py` — 지난달 IdeaPool 파일을 월 폴더로 옮기고, IdeaPool·References 색인을 다시 만든다
- `Design/Data/뷰어_갱신.bat` — 데이터 표 → 도감 화면 (`도감.html`, git에 안 올림)
