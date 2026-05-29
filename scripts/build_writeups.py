#!/usr/bin/env python3
"""Build HTML writeups from Obsidian markdown notes (verbatim, no summarization)."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import markdown

VAULT = Path("/home/rkametani/Documents/Obsidian Vault/000 TryHackMe")
IMAGE_DIR = Path("/home/rkametani/Documents/Obsidian Vault/301 📷Images")
REPO = Path(__file__).resolve().parent.parent

# Metadata only — body text comes straight from Obsidian, untouched.
ROOMS = [
    {"slug": "publisher", "md": "001 Publisher/001 Publisher.md", "title": "Publisher", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/publisher", "difficulty": "Medium", "target": "Linux", "status": "complete", "publish": False},
    {"slug": "vulnversity", "md": "002 Vulnvresity/002 Vulnvresity.md", "title": "Vulnversity", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/vulnversity", "difficulty": "Easy", "target": "Linux", "status": "complete"},
    {"slug": "blue", "md": "003 Blue/003 Blue.md", "title": "Blue", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/blue", "difficulty": "Easy", "target": "Windows", "status": "complete"},
    {"slug": "simple-ctf", "md": "004 Simple CTF/004 Simple CTF.md", "title": "Simple CTF", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/simplectf", "difficulty": "Easy", "target": "Linux", "status": "complete"},
    {"slug": "bounty-hacker", "md": "005 Bounty Hacker/005 Bounty Hacker.md", "title": "Bounty Hacker", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/bountyhacker", "difficulty": "Easy", "target": "Linux", "status": "complete"},
    {"slug": "brute-it", "md": "006 Brute it/006 Brute it.md", "title": "Brute It", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/bruteit", "difficulty": "Easy", "target": "Linux", "status": "complete"},
    {"slug": "agent-sudo", "md": "007 Agent Sudo/007 Agent Sudo.md", "title": "Agent Sudo", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/agentsudo", "difficulty": "Easy", "target": "Linux", "status": "complete"},
    {"slug": "lazy-admin", "md": "008 LazyAdmin/008 LazyAdmin.md", "title": "Lazy Admin", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/lazyadmin", "difficulty": "Easy", "target": "Linux", "status": "complete"},
    {"slug": "juice-shop", "md": "009 OWASP Juice Shop/009 OWASP Juice Shop.md", "title": "OWASP Juice Shop", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/owaspjuiceshop", "difficulty": "Easy", "target": "Linux", "status": "stub"},
    {"slug": "bolt", "md": "010 Bolt/010 Bolt.md", "title": "Bolt", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/bolt", "difficulty": "Easy", "target": "Linux", "status": "complete"},
    {"slug": "corridor", "md": "011 Corridor/011 Corridor.md", "title": "Corridor", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/corridor", "difficulty": "Easy", "target": "Linux", "status": "partial"},
    {"slug": "takeover", "md": "012 TakeOver/012 TakeOver.md", "title": "TakeOver", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/takeover", "difficulty": "Easy", "target": "Linux", "status": "partial"},
    {"slug": "lianyu", "md": "013 Lianyu/013 Lianyu.md", "title": "Lian_Yu", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/lianyu", "difficulty": "Easy", "target": "Linux", "status": "complete"},
    {"slug": "mr-robot", "md": "014 MrRobot/014 MrRobot.md", "title": "Mr. Robot", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/mrrobot", "difficulty": "Medium", "target": "Linux", "status": "complete"},
    {"slug": "overpass", "md": "016 Overpass/016 Overpass.md", "title": "Overpass", "lang": "ja", "lang_label": "日本語", "room_url": "https://tryhackme.com/room/overpass", "difficulty": "Easy", "target": "Linux", "status": "complete"},
]

IMG_PATTERN = re.compile(r"!\[\[([^\]]+\.(?:png|jpg|jpeg|gif|webp))\]\]", re.IGNORECASE)
WIKI_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
FENCE_PATTERN = re.compile(r"(```.*?```)", re.DOTALL)


# Attacker-side addresses (tun0 / LHOST) — not target lab IPs.
TUN0_IP_PLACEHOLDER = "10.10.14.5"


def anonymize(text: str) -> str:
    text = text.replace("rkametani", "kali")
    text = text.replace("192.168.205.211", TUN0_IP_PLACEHOLDER)
    return text


def extract_card_desc(text: str, max_len: int = 100) -> str:
    """First meaningful line from the note — not a summary."""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("```") or s.startswith("![") or s.startswith("#"):
            continue
        if s.startswith("┌──") or s.startswith("└─$"):
            continue
        return s[:max_len]
    return "Obsidian ノート原文"


def preserve_line_breaks(text: str) -> str:
    """Keep single newlines as markdown hard breaks (原文の改行を維持)."""
    parts = FENCE_PATTERN.split(text)
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
            continue
        lines = part.split("\n")
        kept: list[str] = []
        for j, line in enumerate(lines):
            kept.append(line)
            if (
                line.strip()
                and j + 1 < len(lines)
                and lines[j + 1].strip()
                and not line.endswith("  ")
            ):
                kept[-1] = line + "  "
        out.append("\n".join(kept))
    return "".join(out)


def preprocess_obsidian(text: str, image_map: dict[str, str]) -> str:
    def replace_image(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in image_map:
            return f"*[Missing image: {name}]*"
        alt = Path(name).stem
        return f"![{alt}]({image_map[name]})"

    text = IMG_PATTERN.sub(replace_image, text)
    text = WIKI_PATTERN.sub(lambda m: m.group(2) or m.group(1), text)
    return preserve_line_breaks(text)


def collect_images(text: str, slug: str) -> dict[str, str]:
    names = IMG_PATTERN.findall(text)
    if not names:
        return {}

    img_dir = REPO / slug / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    image_map: dict[str, str] = {}
    for idx, name in enumerate(dict.fromkeys(names), start=1):
        src = IMAGE_DIR / name
        ext = Path(name).suffix.lower()
        dest_name = f"{idx:02d}-{Path(name).stem.replace(' ', '-')}{ext}"
        dest = img_dir / dest_name
        rel = f"{slug}/images/{dest_name}"
        if src.exists():
            shutil.copy2(src, dest)
            image_map[name] = rel
        else:
            print(f"  WARN missing image: {name}")
    return image_map


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists"],
        output_format="html5",
    )


def render_page(room: dict, body_html: str) -> str:
    stub = ""
    if room.get("status") in {"stub", "partial"}:
        label = "未完成メモ" if room["status"] == "stub" else "途中経過メモ"
        stub = (
            f'<div class="stub-banner"><strong>{label}:</strong> '
            "Obsidian のノートをそのまま公開しています。内容は未完成の可能性があります。</div>"
        )

    lang = room.get("lang", "ja")
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TryHackMe {html.escape(room["title"])} Writeup</title>
  <link rel="stylesheet" href="assets/writeup.css">
</head>
<body>
  <div class="nav-top"><a href="index.html">&larr; All writeups</a></div>

  <header class="hero">
    <h1>{html.escape(room["title"])}</h1>
    <p>Obsidian ノート原文 — 要約・編集なし</p>
    <div class="badges">
      <span class="badge">Platform: TryHackMe</span>
      <span class="badge">Difficulty: {html.escape(room["difficulty"])}</span>
      <span class="badge">Language: {html.escape(room["lang_label"])}</span>
      <span class="badge">Target: {html.escape(room["target"])}</span>
    </div>
  </header>

  <main>
    <div class="notice">
      <strong>ネタバレ注意:</strong> この writeup にはコマンド、認証情報、フラグが含まれる場合があります。
      許可されたラボ環境での学習目的でのみご利用ください。
    </div>
    {stub}
    <article class="writeup-body">
      {body_html}
    </article>
  </main>

  <footer>
    <p>Educational CTF writeup for <a href="{html.escape(room["room_url"])}">{html.escape(room["room_url"])}</a></p>
  </footer>
</body>
</html>
"""


def render_index(all_rooms: list[dict]) -> str:
    cards = []
    for room in all_rooms:
        href = f"{room['slug']}.html"
        status_tag = ""
        if room.get("status") == "partial":
            status_tag = '<span class="tag">途中</span>'
        elif room.get("status") == "stub":
            status_tag = '<span class="tag">未完成</span>'
        cards.append(
            f"""      <a class="writeup-card" href="{html.escape(href)}">
        <h2>{html.escape(room["title"])}</h2>
        <p>{html.escape(room.get("desc", ""))}</p>
        <div class="tags">
          <span class="tag">{html.escape(room["lang_label"])}</span>
          <span class="tag">{html.escape(room["difficulty"])}</span>
          <span class="tag">{html.escape(room["target"])}</span>
          {status_tag}
        </div>
      </a>"""
        )

    cards_html = "\n\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>THM AI Writeups</title>
  <link rel="stylesheet" href="assets/writeup.css">
  <style>
    main {{ width: min(900px, calc(100% - 2rem)); }}
    .writeup-list {{ display: grid; gap: 1rem; }}
    .writeup-card {{
      display: block;
      padding: 1.5rem;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgba(18, 26, 47, 0.82);
      box-shadow: 0 18px 50px var(--shadow);
      text-decoration: none;
      transition: border-color 0.2s, transform 0.2s;
    }}
    .writeup-card:hover {{
      border-color: rgba(97, 218, 251, 0.45);
      transform: translateY(-2px);
    }}
    .writeup-card h2 {{ margin: 0 0 0.5rem; color: var(--accent); font-size: 1.5rem; }}
    .writeup-card p {{ margin: 0; color: var(--muted); }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }}
    .tag {{
      padding: 0.25rem 0.65rem;
      border: 1px solid var(--border);
      border-radius: 999px;
      font-size: 0.85rem;
      color: var(--text);
      background: rgba(255, 255, 255, 0.06);
    }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>THM AI Writeups</h1>
    <p>Obsidian の原文ノートをそのまま公開。要約・編集なし。</p>
  </header>

  <main>
    <div class="writeup-list">
{cards_html}
    </div>
  </main>

  <footer>
    <p><a href="https://github.com/53b29461/thm-ai-writeups">GitHub Repository</a></p>
  </footer>
</body>
</html>
"""


def render_readme(all_rooms: list[dict]) -> str:
    lines = [
        "# thm-ai-writeups",
        "",
        "TryHackMe room writeups — Obsidian ノート原文を HTML 化（要約・編集なし）。",
        "",
        "**GitHub Pages:** https://53b29461.github.io/thm-ai-writeups/",
        "",
        "Rebuild:",
        "",
        "```bash",
        "python3 scripts/build_writeups.py",
        "```",
        "",
        "## Writeups",
        "",
        "| # | Room | Status | Pages |",
        "|---|------|--------|-------|",
    ]
    for i, room in enumerate(all_rooms, start=1):
        href = f"{room['slug']}.html"
        url = f"https://53b29461.github.io/thm-ai-writeups/{href}"
        status = room.get("status", "complete")
        lines.append(f"| {i:02d} | {room['title']} | {status} | [View]({url}) |")
    lines.append("")
    return "\n".join(lines)


def is_published(room: dict) -> bool:
    return room.get("publish", True)


def remove_unpublished_artifacts(slug: str) -> None:
    page = REPO / f"{slug}.html"
    if page.exists():
        page.unlink()
        print(f"  removed unpublished: {page.name}")
    assets = REPO / slug
    if assets.is_dir():
        shutil.rmtree(assets)
        print(f"  removed unpublished: {assets.name}/")


def build_room(room: dict) -> dict | None:
    md_path = VAULT / room["md"]
    if not md_path.exists():
        print(f"SKIP {room['slug']}: missing {md_path}")
        return None

    raw = anonymize(md_path.read_text(encoding="utf-8").strip())
    if not raw:
        print(f"SKIP {room['slug']}: empty markdown")
        return None

    if not is_published(room):
        print(f"SKIP publish {room['slug']} (local only)")
        remove_unpublished_artifacts(room["slug"])
        return None

    built = {**room, "desc": extract_card_desc(raw)}
    print(f"BUILD {room['slug']} ({len(raw)} chars)")

    image_map = collect_images(raw, room["slug"])
    text = preprocess_obsidian(raw, image_map)
    body_html = md_to_html(text)
    page_html = render_page(built, body_html)
    (REPO / f"{room['slug']}.html").write_text(page_html, encoding="utf-8")
    return built


def main() -> None:
    built_rooms: list[dict] = []
    for room in ROOMS:
        built = build_room(room)
        if built is not None:
            built_rooms.append(built)
    (REPO / "index.html").write_text(render_index(built_rooms), encoding="utf-8")
    (REPO / "README.md").write_text(render_readme(built_rooms), encoding="utf-8")
    print(f"Done. {len(built_rooms)} published pages — verbatim from Obsidian.")


if __name__ == "__main__":
    main()
