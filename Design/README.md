# Design — 설계 문서

> 무엇을 왜 이렇게 만드나. **지금 들어간 것은 [00_Implemented](00_Implemented.md), 남은 일은 [TODO](../TODO.md)**.

## 문서 지도

| 문서 | 내용 |
|---|---|
| [00_Implemented](00_Implemented.md) | ✅ 지금 게임에 들어간 것 + 진행 기록 + 버린 설계 |
| [01_Characters](01_Characters.md) | 고양이·작물 종류, 기본기, 마법서 스킬, 조작 설계 |
| [02_Enemies](02_Enemies.md) | 예고(텔레그래프) 규칙, 적 설계 원칙, 보스 |
| [02_Enemies_Content](02_Enemies_Content.md) | 적 목록 — 스테이지별 적 · 공통 적 · 조합형 부품 |
| [03_Maps](03_Maps.md) | 방 연결형 진행, 방 종류 |
| [04_Combat](04_Combat.md) | 전투 원칙, 협동 (콤보·합동기·세트·가방), 2인 기믹 |
| [05_Items](05_Items.md) | 런 안의 성장 — 장비 v4 규칙 (칸·등급·세트·분해·중간 저장) |
| [05_Items_Content](05_Items_Content.md) | 장비 효과 · 세트 · 패시브 · 마법서 스킬 목록 |
| [06_FeelParameters](06_FeelParameters.md) | 조절 수치 — 어느 파일에서 고치는지 |
| [07_StoryMeta](07_StoryMeta.md) | 이야기, 런 밖의 성장 (온실·빛 퀘스트) |
| [08_RunFlow](08_RunFlow.md) | 한 판의 흐름 — 갈림길 지도 · 물음표 방 · 방 모양 |
| [Data/](Data/README.md) | 사람과 같이 고치는 표 (적·아이템·세트·스테이지·배경·고양이·작물) |
| [IdeaPool/](IdeaPool/README.md) | 일일 루틴이 쌓는 아이디어 — [날짜별](IdeaPool/README.md) · [주제별](IdeaPool/BY_TOPIC.md) |
| [References/](References/README.md) | 조사한 게임 · 기술 · 아트 |

## 문서 쓰는 법

1. **맨 위 두 줄** — 이 문서가 무엇인지 한 줄 + `기준 날짜 · 관련 문서`
2. **할 일은 `TODO.md`에만.** 설계 문서에는 규칙(왜)과 결정 대기(❓)만
3. **끝난 것은 `00_Implemented.md`로.** 설계 문서에는 ✅ 표시와 한 줄 요약만 남긴다
4. **바뀐 설계는 지운다** (git에 남음). 기록할 가치가 있으면 `00_Implemented.md` 끝 "바뀌거나 버린 설계"에 한 줄, 또는 문서 맨 아래 `<details>`
5. **한 줄에 한 가지.** 괄호는 한 겹까지, 날짜·커밋은 줄 끝에
6. **같은 모양이 넷 이상이면 표로**
7. 표시는 [README](../README.md#표시-규칙-모든-문서-공통)의 ✅ 🔶 📝 ❓ ⏸ 만

## 정리 규칙

- IdeaPool은 **받은 편지함** — 채택할 것은 `01~08`이나 `TODO.md`로 옮겨 적는다
- `python Design/tidy.py` 한 번이면: 지난달 IdeaPool 파일 → `YYYY-MM/` · References 루트의 게임 파일 → `Game/` · 색인 3개 갱신
- 전체 요약은 [GameConcept](../GameConcept.md)
