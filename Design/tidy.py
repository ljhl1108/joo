"""Design 폴더 정리 + 색인 만들기.  실행: python Design/tidy.py

1. IdeaPool 루트에 쌓인 지난달 파일 → IdeaPool/YYYY-MM/ 로 옮김 (이번 달은 루트에 둠)
2. References 루트에 생긴 게임 파일 → References/Game/ 으로 옮김
3. IdeaPool/README.md       — 날짜별 색인 (그날 조사한 게임·기술·기능)
4. IdeaPool/BY_TOPIC.md     — 아이디어 제목을 주제별로 (캐릭터·적·맵·전투·아이템·스토리)
5. References/README.md     — 게임·기술·아트 레퍼런스 목록

일일 루틴이 파일을 더할 때마다 다시 실행하면 된다 (같은 결과면 파일이 안 바뀜).
"""
import datetime
import sys
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IDEA = ROOT / "IdeaPool"
REF = ROOT / "References"

TOPICS = [  # (제목, IdeaPool 파일의 '## ' 머리글에 들어 있는 낱말)
    ("캐릭터", ["캐릭터"]),
    ("적", ["적 ("]),
    ("맵·한 판 흐름", ["맵"]),
    ("전투·협동", ["전투"]),
    ("아이템·세트", ["아이템"]),
    ("스토리·메타", ["스토리"]),
]
RECENT_MONTHS = 2  # BY_TOPIC에서 펼쳐 두는 최근 달 수 (그 전은 접어 둠)


def write(path: Path, text: str):
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")
    print("갱신", path.relative_to(ROOT.parent))


def archive_ideas():
    this_month = datetime.date.today().strftime("%Y-%m")
    for f in sorted(IDEA.glob("20??-??-??.md")):
        month = f.stem[:7]
        if month < this_month:
            (IDEA / month).mkdir(exist_ok=True)
            shutil.move(str(f), IDEA / month / f.name)
            print("이동", f.name, "→", month)


def move_stray_refs():
    for f in REF.glob("*.md"):
        if f.name == "README.md":
            continue
        shutil.move(str(f), REF / "Game" / f.name)
        print("이동", f.name, "→ References/Game")


def idea_files():
    files = list(IDEA.glob("20??-??-??.md")) + list(IDEA.glob("20??-??/20??-??-??.md"))
    return sorted(files, key=lambda p: p.stem, reverse=True)


def link(f: Path, base: Path) -> str:
    return f.relative_to(base).as_posix()


def header(text: str, key: str) -> str:
    m = re.search(rf"{key}:\s*(.+?)(?:\||$)", text, re.M)
    return m.group(1).replace("**", "").strip() if m else ""


def topic_of(heading: str):
    for name, keys in TOPICS:
        if any(k in heading for k in keys):
            return name
    return None


def build_idea_index(files):
    by_month = defaultdict(list)
    for f in files:
        by_month[f.stem[:7]].append(f)
    out = [
        "# 아이디어 풀 — 날짜별 색인",
        "",
        "> 일일 루틴이 매일 한 장씩 쌓는 **받은 편지함**. 쓸 만한 것은 `Design/01~08` 설계 문서나 `TODO.md`로 옮긴다.",
        "> 주제별로 보려면 [BY_TOPIC.md](BY_TOPIC.md). 이 파일은 `python Design/tidy.py`가 만든다 (손으로 고치지 말 것).",
        "",
        f"총 {len(files)}일치 · 마지막 {files[0].stem if files else '-'}",
        "",
    ]
    for i, month in enumerate(sorted(by_month, reverse=True)):
        rows = ["| 날짜 | 조사한 게임 | 기술 주제 | 완성 기능 |", "|---|---|---|---|"]
        for f in by_month[month]:
            t = f.read_text(encoding="utf-8")
            rows.append(f"| [{f.stem[5:]}]({link(f, IDEA)}) | {header(t, '리서치 대상')} | {header(t, '기술 주제')} | {header(t, '완성 기능')} |")
        if i == 0:
            out += [f"## {month}", ""] + rows + [""]
        else:
            out += [f"<details><summary><b>{month}</b> ({len(by_month[month])}일)</summary>", ""] + rows + ["", "</details>", ""]
    write(IDEA / "README.md", "\n".join(out))


def build_topic_index(files):
    ideas = defaultdict(lambda: defaultdict(list))  # topic -> month -> [(date, title, file)]
    for f in files:
        topic = None
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                topic = topic_of(line)
            elif topic and line.startswith("- **"):
                m = re.match(r"- \*\*(.+?)\*\*", line)
                if m:
                    ideas[topic][f.stem[:7]].append((f.stem, m.group(1), f))
    months = sorted({f.stem[:7] for f in files}, reverse=True)
    out = [
        "# 아이디어 풀 — 주제별 제목 모음",
        "",
        "> 날짜를 누르면 그날 파일 (설명·참고 게임은 거기에). 최근 두 달은 펼쳐 두고 그 전은 접어 둠.",
        "> 이 파일은 `python Design/tidy.py`가 만든다 (손으로 고치지 말 것). 날짜별 색인은 [README.md](README.md).",
        "",
        " · ".join(f"[{name}](#{name.replace('·', '').replace(' ', '-')})" for name, _ in TOPICS),
        "",
    ]
    for name, _ in TOPICS:
        total = sum(len(v) for v in ideas[name].values())
        out += ["---", "", f"## {name}", "", f"{total}개", ""]
        for i, month in enumerate(months):
            items = ideas[name].get(month)
            if not items:
                continue
            lines = [f"- {title} · [{date[5:]}]({link(f, IDEA)})" for date, title, f in items]
            if i < RECENT_MONTHS:
                out += [f"### {month}", ""] + lines + [""]
            else:
                out += [f"<details><summary>{month} ({len(items)}개)</summary>", ""] + lines + ["", "</details>", ""]
    write(IDEA / "BY_TOPIC.md", "\n".join(out))


def first_heading(f: Path) -> str:
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return f.stem


def research_date(f: Path) -> str:
    m = re.search(r"리서치 날짜:\s*(\S+)", f.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def build_ref_index():
    games = sorted((REF / "Game").glob("*.md"), key=lambda p: p.stem.lower())
    techs = sorted((REF / "Tech").glob("*.md"), key=lambda p: p.stem.lower())
    arts = sorted((REF / "Art").glob("*.md"), key=lambda p: p.stem.lower())
    out = [
        "# 레퍼런스 목록",
        "",
        "> 일일 루틴이 조사한 게임·기술 정리. 이 파일은 `python Design/tidy.py`가 만든다 (손으로 고치지 말 것).",
        "",
        f"[게임 {len(games)}](#게임) · [기술 {len(techs)}](#기술) · [아트 {len(arts)}](#아트)",
        "",
        "## 게임",
        "",
        "| 게임 | 조사한 날 |",
        "|---|---|",
    ]
    out += [f"| [{first_heading(f)}]({link(f, REF)}) | {research_date(f)} |" for f in games]
    out += ["", "## 기술", ""]
    groups = defaultdict(list)
    for f in techs:
        groups[f.stem[0].upper()].append(f)
    for letter in sorted(groups):
        out.append(f"- **{letter}** — " + " · ".join(f"[{first_heading(f)}]({link(f, REF)})" for f in groups[letter]))
    out += ["", "## 아트", ""]
    out += [f"- [{first_heading(f)}]({link(f, REF)})" for f in arts]
    out.append("")
    write(REF / "README.md", "\n".join(out))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    archive_ideas()
    move_stray_refs()
    files = idea_files()
    build_idea_index(files)
    build_topic_index(files)
    build_ref_index()
