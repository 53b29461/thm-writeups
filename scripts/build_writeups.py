#!/usr/bin/env python3
"""Build HTML writeups from Obsidian markdown notes."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import markdown

VAULT = Path("/home/rkametani/Documents/Obsidian Vault/000 TryHackMe")
IMAGE_DIR = Path("/home/rkametani/Documents/Obsidian Vault/301 📷Images")
REPO = Path(__file__).resolve().parent.parent

MANUAL_HTML = {"lianyu", "overpass"}

ROOMS = [
    {
        "slug": "publisher",
        "md": "001 Publisher/001 Publisher.md",
        "title": "Publisher",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/publisher",
        "desc": "SPIP CMS RCE、SSH 鍵再利用、Docker/AppArmor 回避、SUID bash による権限昇格。",
        "difficulty": "Medium",
        "target": "Linux",
        "status": "complete",
    },
    {
        "slug": "vulnversity",
        "md": "002 Vulnvresity/002 Vulnvresity.md",
        "title": "Vulnversity",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/vulnversity",
        "desc": "多サービス列挙（FTP/Samba/Squid）、Web シェル、systemd 権限昇格。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
    },
    {
        "slug": "blue",
        "md": "003 Blue/003 Blue.md",
        "title": "Blue",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/blue",
        "desc": "Windows SMBv1 列挙、EternalBlue (MS17-010)、Meterpreter によるフラグ取得。",
        "difficulty": "Easy",
        "target": "Windows",
        "status": "complete",
    },
    {
        "slug": "simple-ctf",
        "md": "004 Simple CTF/004 Simple CTF.md",
        "title": "Simple CTF",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/simplectf",
        "desc": "Web/FTP 列挙、隠し CMS 認証情報、SSH、sudo vim GTFOBins。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
    },
    {
        "slug": "bounty-hacker",
        "md": "005 Bounty Hacker/005 Bounty Hacker.md",
        "title": "Bounty Hacker",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/bountyhacker",
        "desc": "匿名 FTP、Web 列挙、SSH、sudo tar GTFOBins。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
    },
    {
        "slug": "brute-it",
        "md": "006 Brute it/006 Brute it.md",
        "title": "Brute It",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/bruteit",
        "desc": "管理画面ブルートフォース、SSH、shadow クラック、su による root 化。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
    },
    {
        "slug": "agent-sudo",
        "md": "007 Agent Sudo/007 Agent Sudo.md",
        "title": "Agent Sudo",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/agentsudo",
        "desc": "User-Agent 列挙、FTP/ステガノ、SSH、CVE-2019-14287 sudo バイパス。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
    },
    {
        "slug": "lazy-admin",
        "md": "008 LazyAdmin/008 LazyAdmin.md",
        "title": "Lazy Admin",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/lazyadmin",
        "desc": "SweetRice CMS バックアップ漏洩、Web シェル、cron/sudo perl 権限昇格。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
    },
    {
        "slug": "juice-shop",
        "md": "009 OWASP Juice Shop/009 OWASP Juice Shop.md",
        "title": "OWASP Juice Shop",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/owaspjuiceshop",
        "desc": "OWASP Top 10 入門ルーム（Web アクセス未完了のメモ）。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "stub",
    },
    {
        "slug": "bolt",
        "md": "010 Bolt/010 Bolt.md",
        "title": "Bolt",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/bolt",
        "desc": "Bolt CMS (:8000)、認証情報漏洩、認証済み RCE、root シェル。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
    },
    {
        "slug": "corridor",
        "md": "011 Corridor/011 Corridor.md",
        "title": "Corridor",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/corridor",
        "desc": "MD5 ハッシュ化されたルーム URL、IDOR（room 0）の調査（途中）。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "partial",
    },
    {
        "slug": "takeover",
        "md": "012 TakeOver/012 TakeOver.md",
        "title": "TakeOver",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/takeover",
        "desc": "サブドメイン列挙とテイクオーバー調査（途中）。",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "partial",
    },
    {
        "slug": "mr-robot",
        "md": "014 MrRobot/014 MrRobot.md",
        "title": "Mr. Robot",
        "lang": "ja",
        "lang_label": "日本語",
        "room_url": "https://tryhackme.com/room/mrrobot",
        "desc": "WordPress（Mr. Robot テーマ）、robots.txt、ハッシュクラック、権限昇格。",
        "difficulty": "Medium",
        "target": "Linux",
        "status": "complete",
    },
]

MANUAL_ROOMS = [
    {
        "slug": "lianyu",
        "title": "Lian_Yu",
        "lang_label": "English",
        "desc": "Enumeration, FTP, steganography, SSH access, and privilege escalation via pkexec.",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
        "href": "lianyu.html",
    },
    {
        "slug": "overpass",
        "title": "Overpass",
        "lang_label": "日本語",
        "desc": "Cookie-based auth bypass, SSH key cracking, cron job abuse via /etc/hosts poisoning.",
        "difficulty": "Easy",
        "target": "Linux",
        "status": "complete",
        "href": "overpass.html",
    },
]

IMG_PATTERN = re.compile(r"!\[\[([^\]]+\.(?:png|jpg|jpeg|gif|webp))\]\]", re.IGNORECASE)
WIKI_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def preprocess_obsidian(text: str, slug: str, image_map: dict[str, str]) -> str:
    def replace_image(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in image_map:
            return f"*[Missing image: {name}]*"
        alt = Path(name).stem
        return f"![{alt}]({image_map[name]})"

    text = IMG_PATTERN.sub(replace_image, text)
    text = WIKI_PATTERN.sub(lambda m: m.group(2) or m.group(1), text)
    return text


def collect_images(text: str, slug: str) -> tuple[str, dict[str, str]]:
    names = IMG_PATTERN.findall(text)
    if not names:
        return text, {}

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
    return text, image_map


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
        output_format="html5",
    )


def render_page(room: dict, body_html: str) -> str:
    stub = ""
    if room.get("status") in {"stub", "partial"}:
        label = "未完成メモ" if room["status"] == "stub" else "途中経過メモ"
        stub = f'<div class="stub-banner"><strong>{label}:</strong> Obsidian のノートをそのまま公開しています。内容は未完成の可能性があります。</div>'

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
    <p>{html.escape(room["desc"])}</p>
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
        href = room.get("href", f"{room['slug']}.html")
        status_tag = ""
        if room.get("status") == "partial":
            status_tag = '<span class="tag">途中</span>'
        elif room.get("status") == "stub":
            status_tag = '<span class="tag">未完成</span>'
        cards.append(
            f"""      <a class="writeup-card" href="{html.escape(href)}">
        <h2>{html.escape(room["title"])}</h2>
        <p>{html.escape(room["desc"])}</p>
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
    <p>TryHackMe room walkthroughs created with AI assistance. For authorized lab practice and learning only.</p>
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
        "TryHackMe room writeups created with AI assistance.",
        "",
        "**GitHub Pages:** https://53b29461.github.io/thm-ai-writeups/",
        "",
        "Rebuild HTML from Obsidian notes:",
        "",
        "```bash",
        "python3 scripts/build_writeups.py",
        "```",
        "",
        "## Writeups",
        "",
        "| # | Room | Language | Status | Pages |",
        "|---|------|----------|--------|-------|",
    ]
    for i, room in enumerate(all_rooms, start=1):
        href = room.get("href", f"{room['slug']}.html")
        url = f"https://53b29461.github.io/thm-ai-writeups/{href}"
        status = room.get("status", "complete")
        lines.append(
            f"| {i:02d} | {room['title']} | {room['lang_label']} | {status} | [View]({url}) |"
        )
    lines.append("")
    return "\n".join(lines)


def build_room(room: dict) -> None:
    md_path = VAULT / room["md"]
    if not md_path.exists():
        print(f"SKIP {room['slug']}: missing {md_path}")
        return

    text = md_path.read_text(encoding="utf-8").strip()
    if not text:
        print(f"SKIP {room['slug']}: empty markdown")
        return

    print(f"BUILD {room['slug']} ({len(text)} chars)")
    text, image_map = collect_images(text, room["slug"])
    text = preprocess_obsidian(text, room["slug"], image_map)
    body_html = md_to_html(text)
    page_html = render_page(room, body_html)
    out = REPO / f"{room['slug']}.html"
    out.write_text(page_html, encoding="utf-8")


def main() -> None:
    for room in ROOMS:
        build_room(room)

    all_rooms = MANUAL_ROOMS + ROOMS
    (REPO / "index.html").write_text(render_index(all_rooms), encoding="utf-8")
    (REPO / "README.md").write_text(render_readme(all_rooms), encoding="utf-8")
    print(f"Done. {len(ROOMS)} generated + {len(MANUAL_ROOMS)} manual pages indexed.")


if __name__ == "__main__":
    main()
