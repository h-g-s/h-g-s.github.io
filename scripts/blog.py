#!/usr/bin/env python3
"""Create a draft or mark a Markdown post as ready to publish."""

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
import tomllib
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def slugify(title):
    plain = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")
    if not slug:
        raise ValueError("The title needs at least one letter or digit for its URL.")
    return slug


def new_post(title, summary, day):
    if not title.strip() or not summary.strip():
        raise ValueError("Title and summary must not be empty.")
    path = ROOT / "posts" / f"{day.isoformat()}-{slugify(title)}.md"
    path.parent.mkdir(exist_ok=True)
    content = (
        f"+++\ntitle = {json.dumps(title, ensure_ascii=False)}\n"
        f"date = {day.isoformat()}\nsummary = {json.dumps(summary, ensure_ascii=False)}\n"
        "draft = true\n+++\n\nWrite your post here.\n"
    )
    with path.open("x", encoding="utf-8") as stream:
        stream.write(content)
    return path


def publish_post(filename):
    path = Path(filename).resolve()
    if path.parent != (ROOT / "posts").resolve() or path.suffix != ".md":
        raise ValueError("Choose a Markdown file directly inside posts/.")
    source = path.read_text(encoding="utf-8")
    parts = source.split("+++\n", 2)
    if len(parts) != 3 or parts[0]:
        raise ValueError("Expected TOML front matter enclosed by +++.")
    meta = tomllib.loads(parts[1])
    if type(meta.get("draft")) is not bool or type(meta.get("date")) is not date:
        raise ValueError("Front matter needs a boolean draft and a TOML date.")
    if not all(isinstance(meta.get(key), str) and meta[key].strip() for key in ("title", "summary")):
        raise ValueError("A nonempty title and summary are required.")
    if meta["date"] > date.today():
        raise ValueError("The post date is in the future; choose today or an earlier date to publish.")
    if not parts[2].strip() or parts[2].strip() == "Write your post here.":
        raise ValueError("Write the post before publishing it.")
    updated, count = re.subn(r"(?m)^draft\s*=\s*(?:true|false)\s*$", "draft = false", parts[1])
    if count != 1:
        raise ValueError("Expected exactly one draft field on its own line.")
    path.write_text(f"+++\n{updated}+++\n{parts[2]}" if updated.endswith("\n") else f"+++\n{updated}\n+++\n{parts[2]}", encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="Create an unpublished Markdown draft")
    new.add_argument("title")
    new.add_argument("--summary", required=True)
    new.add_argument("--date", type=date.fromisoformat, default=date.today())
    publish = commands.add_parser("publish", help="Include a finished post in the next build (does not push)")
    publish.add_argument("file")
    args = parser.parse_args()
    try:
        if args.command == "new":
            path = new_post(args.title, args.summary, args.date)
            print(f"Draft created: {path.relative_to(ROOT)}")
            print("Edit this file, then use scripts/blog.py publish FILE when it is ready.")
        else:
            path = publish_post(args.file)
            print(f"Ready for publication: {path.relative_to(ROOT)}")
            print("Build and preview, then commit and push to deploy. Nothing has been uploaded.")
    except (ValueError, OSError, tomllib.TOMLDecodeError) as error:
        sys.exit(f"Blog command failed: {error}")


if __name__ == "__main__":
    main()
