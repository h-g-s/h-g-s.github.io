#!/usr/bin/env python3
"""Check built HTML targets and anchors; optionally check external URLs."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urldefrag, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SITE_HOST = "h-g-s.github.io"


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = set()
        self.duplicates = set()
        self.links = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            identifier = attrs["id"]
            if identifier in self.ids:
                self.duplicates.add(identifier)
            self.ids.add(identifier)
        for attribute in ("href", "src"):
            if attrs.get(attribute):
                self.links.append(attrs[attribute])


def check_local(root):
    root = root.resolve()
    pages = {path: Document(path.read_text(encoding="utf-8")) for path in root.rglob("*.html")}
    errors = []
    external = set()
    if not pages:
        errors.append("No built HTML pages found. Run scripts/build.py first.")
    for path, document in pages.items():
        for identifier in document.duplicates:
            errors.append(f"{path.relative_to(root)}: duplicate id {identifier}")
        for link in document.links:
            url = urlsplit(link)
            if url.scheme in ("mailto", "tel", "data"):
                continue
            if url.scheme in ("http", "https") or url.netloc:
                if url.hostname != SITE_HOST:
                    external.add(urldefrag(link)[0])
                    continue
            elif url.scheme:
                errors.append(f"{path.relative_to(root)}: unsupported link {link}")
                continue
            target = root / unquote(url.path).lstrip("/") if url.path.startswith("/") else path.parent / unquote(url.path)
            if not url.path:
                target = path
            if target.is_dir():
                target /= "index.html"
            target = target.resolve()
            if not target.is_relative_to(root) or not target.is_file():
                errors.append(f"{path.relative_to(root)}: missing target {link}")
            elif url.fragment and target.suffix == ".html":
                destination = pages.get(target)
                if destination is None or unquote(url.fragment) not in destination.ids:
                    errors.append(f"{path.relative_to(root)}: missing anchor {link}")
    return errors, external


def check_external(url):
    request = Request(url, headers={"User-Agent": "HomepageLinkChecker/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            sample = response.read(4096).lower()
            if response.status == 202 or b"making sure you" in sample or b"captcha" in sample:
                return "UNVERIFIED", url, "bot challenge"
            return "OK", url, str(response.status)
    except HTTPError as error:
        result = "UNVERIFIED" if error.code in (401, 403, 429) else "BROKEN"
        return result, url, str(error.code)
    except (URLError, TimeoutError, OSError) as error:
        return "UNVERIFIED", url, str(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external", action="store_true")
    parser.add_argument("--directory", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    errors, external = check_local(args.directory)
    for error in errors:
        print(f"BROKEN {error}")
    print(f"Local check: {len(errors)} errors; {len(external)} unique external URLs.")
    broken = len(errors)
    if args.external:
        with ThreadPoolExecutor(max_workers=5) as executor:
            for status, url, detail in executor.map(check_external, sorted(external)):
                print(f"{status} {url} ({detail})")
                broken += status == "BROKEN"
        print("UNVERIFIED links need a manual browser check; they are not counted as confirmed broken links.")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
