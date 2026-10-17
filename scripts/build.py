#!/usr/bin/env python3
"""Build the static homepage and Markdown blog."""

from datetime import date
from html import escape
from pathlib import Path
import json
import shutil
import sys
import tomllib
import xml.etree.ElementTree as ET

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
SITE_URL = "https://h-g-s.github.io"
PAGES = [
    ("index.html", "About", "home"),
    ("research.html", "Research", "research"),
    ("pub.html", "Publications", "papers"),
    ("software.html", "Software", "code"),
    ("blog/index.html", "Blog", "blog"),
    ("teach.html", "Teaching", "teaching"),
]
ICON_PATHS = {
    "home": '<path d="m4 11 8-7 8 7v9h-6v-6h-4v6H4z"/>',
    "research": '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6M7 10h6m-3-3v6"/>',
    "papers": '<path d="M6 3h9l4 4v14H6zM14 3v5h5M9 12h7m-7 4h7"/>',
    "code": '<path d="m8 7-5 5 5 5m8-10 5 5-5 5m-3-13-2 20"/>',
    "blog": '<path d="M4 4h16v13H9l-5 4zM8 8h8m-8 4h5"/>',
    "teaching": '<path d="m2 8 10-5 10 5-10 5zM6 10v7c4 3 8 3 12 0v-7m4-2v9"/>',
}


def icon(name):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{ICON_PATHS[name]}</svg>'


def render(path, title, content, description=None):
    prefix = "../" * (len(Path(path).parts) - 1)
    section = "blog/index.html" if path.startswith("blog/") else path
    nav = ""
    for target, label, image in PAGES:
        active = ' aria-current="page"' if target == section else ""
        nav += (
            f'<a class="dock-item{" active" if active else ""}" href="{prefix}{target}"{active}>'
            f'<span class="dock-icon">{icon(image)}</span><span>{label}</span></a>'
        )
    description = description or "Haroldo. Software engineer, former CS professor, and open-source optimization enthusiast."
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Haroldo</title>
  <meta name="description" content="{escape(description, quote=True)}">
  <meta name="theme-color" content="#34344e">
  <meta property="og:title" content="{escape(title, quote=True)} · Haroldo">
  <meta property="og:description" content="{escape(description, quote=True)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/{path}">
  <link rel="canonical" href="{SITE_URL}/{path}">
  <link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{prefix}assets/style.css">
  <link rel="alternate" type="application/atom+xml" title="Haroldo's blog" href="{prefix}blog/feed.xml">
  <script src="{prefix}assets/app.js" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="desktop-panel">
    <a class="desktop-brand" href="{prefix}index.html"><span class="brand-mark" aria-hidden="true">H</span> haroldo<span class="muted">@web</span></a>
    <span class="workspace">PERSONAL DESKTOP <span aria-hidden="true">/</span> 01</span>
    <a class="panel-link" href="https://github.com/h-g-s">GitHub <span aria-hidden="true">↗</span></a>
  </header>
  <div class="desktop">
    <nav class="dock" aria-label="Main navigation">{nav}</nav>
    <div class="workspace-area">
      <div class="window">
        <div class="title-bar">
          <span class="window-emblem" aria-hidden="true">H</span>
          <span class="window-title">{escape(title)} <span class="title-context">— Haroldo</span></span>
          <button class="maximize" type="button" aria-label="Maximize window" aria-pressed="false" hidden><span aria-hidden="true">□</span></button>
        </div>
        <main id="main" tabindex="-1">{content}</main>
        <div class="status-bar"><span>~/ {escape(title.lower())}</span><span>Window Maker inspired</span><span class="resize-grip" aria-hidden="true"></span></div>
      </div>
      <footer class="desktop-footer">A little old-school. Still building things. <span>Built with plain HTML, CSS &amp; a little Python.</span></footer>
    </div>
  </div>
</body>
</html>
"""
    destination = OUTPUT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")


def publications():
    records = json.loads((ROOT / "data/publications.json").read_text())
    sections = []
    for category, title in (("journal", "Journal papers"), ("conference", "Conference papers")):
        cards = []
        for paper in records:
            if paper["category"] != category:
                continue
            url = paper["url"]
            label = "PDF" if url.endswith(".pdf") else "Read paper"
            links = f'<a href="{escape(url, quote=True)}">{label} <span aria-hidden="true">↗</span></a>'
            if paper.get("doi"):
                links += f'<a href="{escape(paper["doi"], quote=True)}">Journal article</a>'
            if paper.get("preprint"):
                links += f'<a href="{escape(paper["preprint"], quote=True)}">Preprint (arXiv PDF)</a>'
            if paper["bib"]:
                links += f'<a href="{escape(paper["bib"], quote=True)}">BibTeX</a>'
            cards.append(f"""<article class="publication" id="{escape(paper["id"])}">
  <h3>{escape(paper["title"])}</h3>
  <p class="authors">{escape(paper["authors"])}</p>
  <p class="citation">{escape(paper["citation"])}</p>
  <div class="paper-links">{links}</div>
</article>""")
        sections.append(f'<section class="publication-group" id="{category}-region"><h2>{title}</h2>{"".join(cards)}</section>')
    return f"""<div class="page-heading"><p class="eyebrow">RESEARCH ARCHIVE</p><h1>Publications</h1>
<p>A selection of papers from my academic work (2005–2021), including the archive from my previous homepage. For a broader publication record, see <a href="https://scholar.google.com/citations?user=sHxGMR4AAAAJ">Google Scholar</a> or <a href="https://dblp.org/pers/hd/s/Santos:Haroldo_G=">DBLP</a>.</p></div>
<div class="publication-tools"><nav class="inline-links" aria-label="Publication categories"><a href="#journal-region">Journal papers</a><a href="#conference-region">Conference papers</a></nav>
<div class="search-control" hidden><label for="publication-search">Filter publications</label><input id="publication-search" type="search" placeholder="Title, author, venue, year…" aria-describedby="publication-count"></div>
<p id="publication-count" class="meta" role="status">{len(records)} publications</p></div>
{"".join(sections)}<p id="no-results" hidden>No publications match your search.</p>"""


def read_posts():
    posts = []
    for path in sorted((ROOT / "posts").glob("*.md")):
        source = path.read_text(encoding="utf-8")
        parts = source.split("+++\n", 2)
        if len(parts) != 3 or parts[0]:
            raise ValueError(f"{path.name}: expected TOML front matter enclosed by +++")
        meta = tomllib.loads(parts[1])
        for key in ("title", "summary"):
            if not isinstance(meta.get(key), str) or not meta[key].strip():
                raise ValueError(f"{path.name}: {key} must be a nonempty string")
        if type(meta.get("date")) is not date or type(meta.get("draft")) is not bool:
            raise ValueError(f"{path.name}: date must be a TOML date and draft must be true or false")
        if meta["draft"] or meta["date"] > date.today():
            continue
        body = markdown.markdown(parts[2], extensions=["fenced_code", "tables", "sane_lists"])
        posts.append({**meta, "body": body, "path": f"blog/{path.stem}.html"})
    return sorted(posts, key=lambda post: (post["date"], post["path"]), reverse=True)


def blog(posts):
    heading = """<div class="page-heading"><p class="eyebrow">NOTES FROM THE WORKBENCH</p><h1>Blog</h1>
<p>A place for occasional notes on software, optimization, and things I learn along the way.</p></div>"""
    if posts:
        items = "".join(
            f'<article class="post-preview"><time datetime="{post["date"].isoformat()}">{post["date"]:%d %b %Y}</time>'
            f'<h2><a href="../{post["path"]}">{escape(post["title"])}</a></h2><p>{escape(post["summary"])}</p></article>'
            for post in posts
        )
    else:
        items = f"""<section class="empty-state"><span class="empty-icon">{icon("blog")}</span>
<p class="eyebrow">A FRESH WORKSPACE</p><h2>No posts yet.</h2>
<p>The blog is set up. The first note is still on the drawing board.</p></section>"""
    render("blog/index.html", "Blog", heading + items + '<p class="feed-link"><a href="feed.xml">Subscribe via Atom</a></p>')
    for post in posts:
        content = f"""<nav class="inline-links" aria-label="Blog navigation"><a href="index.html">← All posts</a></nav>
<article class="blog-post"><header class="page-heading"><p class="eyebrow">BLOG / <time datetime="{post["date"].isoformat()}">{post["date"]:%d %b %Y}</time></p>
<h1>{escape(post["title"])}</h1><p>{escape(post["summary"])}</p></header><div class="prose">{post["body"]}</div></article>"""
        render(post["path"], post["title"], content, post["summary"])
    atom(posts)


def atom(posts):
    namespace = "http://www.w3.org/2005/Atom"
    ET.register_namespace("", namespace)

    def element(parent, name, text=None, **attributes):
        node = ET.SubElement(parent, f"{{{namespace}}}{name}", attributes)
        node.text = text
        return node

    feed = ET.Element(f"{{{namespace}}}feed")
    element(feed, "title", "Haroldo — Blog")
    element(feed, "id", f"{SITE_URL}/blog/")
    element(feed, "link", href=f"{SITE_URL}/blog/")
    element(feed, "link", href=f"{SITE_URL}/blog/feed.xml", rel="self")
    updated = f'{posts[0]["date"].isoformat()}T00:00:00Z' if posts else "2026-10-17T00:00:00Z"
    element(feed, "updated", updated)
    author = element(feed, "author")
    element(author, "name", "Haroldo")
    for post in posts:
        entry = element(feed, "entry")
        element(entry, "title", post["title"])
        element(entry, "id", f'{SITE_URL}/{post["path"]}')
        element(entry, "link", href=f'{SITE_URL}/{post["path"]}')
        element(entry, "updated", f'{post["date"].isoformat()}T00:00:00Z')
        element(entry, "summary", post["summary"])
    ET.ElementTree(feed).write(OUTPUT / "blog/feed.xml", encoding="utf-8", xml_declaration=True)


def main():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    shutil.copytree(ROOT / "assets", OUTPUT / "assets")
    (OUTPUT / ".nojekyll").touch()
    for path, title, _ in PAGES:
        if path.startswith("blog/"):
            continue
        content = publications() if path == "pub.html" else (ROOT / "content" / path).read_text(encoding="utf-8")
        render(path, title, content)
    posts = read_posts()
    blog(posts)
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for path, _, _ in PAGES + [(post["path"], "", "") for post in posts]:
        ET.SubElement(ET.SubElement(sitemap, "url"), "loc").text = f"{SITE_URL}/{path}"
    ET.ElementTree(sitemap).write(OUTPUT / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    (OUTPUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    print(f"Built {len(PAGES)} pages and {len(posts)} published blog posts in {OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, tomllib.TOMLDecodeError) as error:
        sys.exit(f"Build failed: {error}")
