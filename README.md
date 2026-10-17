# Haroldo's desktop

A small personal homepage with a Window Maker-inspired desktop: a dock,
beveled title bars, and a muted purple workspace. Responsive, keyboard-friendly,
and usable without JavaScript. No analytics, external fonts, or tracking scripts.

## Build and preview

Requires Python 3.11 or newer.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/build.py
.venv/bin/python -m http.server 8000 --bind 127.0.0.1 --directory _site
```

Open <http://localhost:8000>. Rebuild after editing; the preview serves the
generated files, not the source files.

## Edit the homepage

- `content/`: About, Research, Software, and Teaching page content.
- `data/publications.json`: the publication archive, including local PDF/BibTeX links.
- `assets/`: styles, small progressive enhancements, original SVG icons, and downloads.
- `scripts/build.py`: the shared desktop layout, publication rendering, blog, and feeds.
- `posts/`: Markdown blog posts with TOML front matter.

The biography intentionally says only **software engineer and former CS professor**.
Teaching materials stay on the old university site. Publication PDFs, BibTeX,
research diagrams, and software downloads that were available there were copied
locally so they no longer depend on that server.

## Write a blog post

```sh
.venv/bin/python scripts/blog.py new "My first note" --summary "A short description."
```

This creates `posts/YYYY-MM-DD-my-first-note.md` as an **unpublished draft**:

```markdown
+++
title = "My first note"
date = 2026-10-17
summary = "A short description."
draft = true
+++

Write in Markdown here. Code fences and tables are supported.
```

Edit the Markdown, then mark it ready:

```sh
.venv/bin/python scripts/blog.py publish posts/YYYY-MM-DD-my-first-note.md
.venv/bin/python scripts/build.py
.venv/bin/python scripts/check_links.py
```

The `publish` command only changes `draft` to `false`; it does **not** push or
upload anything. Preview locally, then commit and push when ready. Draft and
future-dated posts never appear in the generated site, blog index, sitemap, or
Atom feed. Future-dated posts require a build on or after their date; there is
no scheduled publishing job. Relative post images can be placed in `assets/`
and linked as `../assets/example.png`.

**Privacy:** draft files committed to a public repository are still public in
its source, even though they are omitted from the website. Keep sensitive
drafts outside the repository.

The initially empty blog lives at `/blog/`; its Atom feed is `/blog/feed.xml`.

## Check links

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_links.py
.venv/bin/python scripts/check_links.py --external
```

The local check validates files, downloads, and HTML fragment targets.
The external check distinguishes confirmed failures from bot protection,
rate limits, and network failures, which require manual verification.

During migration, obsolete institutional/personal links, the old Cbc benchmark
host, a malformed MathProg link, and dead documentation downloads were removed
or replaced. A duplicate XHSTT entry was removed, and the GOAL solver citation
now points to its correct paper. The archive contains 30 distinct publications,
including the 2021 papers on cover by disjoint cliques cuts and preprocessing
and cutting planes with conflict graphs;
it is not presented as a complete or current publication list. DOI links
replace ResearchGate paper links. Scholar, DBLP, and some publishers may
challenge automated link checks.

The decision-tree algorithm-selection paper includes both its ITOR journal
link and the downloadable arXiv preprint, alongside the existing local PDF.
Its citation records the 2021 journal issue and the 2019 online publication.

## GitHub Pages

The public repository is `h-g-s/h-g-s.github.io`, publishing to
<https://h-g-s.github.io/>.

GitHub Pages uses **Settings → Pages → Source → GitHub Actions**.
The included workflow builds and checks pull requests, and deploys pushes to
`main`. No custom domain is required. If the hostname changes, update `SITE_URL`
in `scripts/build.py` and `SITE_HOST` in `scripts/check_links.py`.

## Credits

The visual concept is inspired by [Window Maker](https://www.windowmaker.org/)
and the previous homepage. The new SVG dock icons are original; no third-party
icon set or web font is needed. Research figures and archived downloads were
migrated from the original homepage. Papers retain their respective authors'
and publishers' rights; no blanket license is applied to those files.
