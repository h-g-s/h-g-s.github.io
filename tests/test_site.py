from datetime import date, timedelta
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    imported = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imported)
    return imported


build = module("build")
blog = module("blog")
links = module("check_links")


class BlogTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "posts").mkdir()
        (self.root / "_site").mkdir()
        for mod in (blog, build):
            patcher = patch.object(mod, "ROOT", self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(build, "OUTPUT", self.root / "_site")
        patcher.start()
        self.addCleanup(patcher.stop)

    def draft(self, title="A note", summary="A concise summary.", day=None):
        return blog.new_post(title, summary, day or date.today())

    def finish(self, path):
        path.write_text(path.read_text().replace("Write your post here.", "## Hello\n\nA **useful** note.\n"))

    def test_new_draft_is_excluded(self):
        path = self.draft()
        self.assertTrue(path.exists())
        self.assertEqual(build.read_posts(), [])
        build.blog(build.read_posts())
        self.assertIn("No posts yet.", (build.OUTPUT / "blog/index.html").read_text())
        self.assertFalse((build.OUTPUT / f"blog/{path.stem}.html").exists())
        self.assertNotIn("A concise summary", (build.OUTPUT / "blog/feed.xml").read_text())

    def test_publish_generates_post_index_and_feed(self):
        path = self.draft('A "note" & more')
        self.finish(path)
        blog.publish_post(path)
        posts = build.read_posts()
        self.assertEqual(len(posts), 1)
        build.blog(posts)
        page = (build.OUTPUT / posts[0]["path"]).read_text()
        self.assertIn("<strong>useful</strong>", page)
        self.assertIn("A &quot;note&quot; &amp; more", page)
        self.assertIn('href="../index.html"', page)
        self.assertIn(f'href="../{posts[0]["path"]}"', (build.OUTPUT / "blog/index.html").read_text())
        feed = ET.parse(build.OUTPUT / "blog/feed.xml")
        self.assertEqual(len(feed.findall("{http://www.w3.org/2005/Atom}entry")), 1)

    def test_publish_rejects_placeholder(self):
        with self.assertRaisesRegex(ValueError, "Write the post"):
            blog.publish_post(self.draft())

    def test_publish_rejects_files_outside_posts(self):
        outside = self.root / "other.md"
        outside.write_text("not a post")
        with self.assertRaisesRegex(ValueError, "directly inside posts"):
            blog.publish_post(outside)

    def test_future_posts_stay_hidden(self):
        path = self.draft(day=date.today() + timedelta(days=1))
        self.finish(path)
        with self.assertRaisesRegex(ValueError, "future"):
            blog.publish_post(path)
        path.write_text(path.read_text().replace("draft = true", "draft = false"))
        self.assertEqual(build.read_posts(), [])

    def test_invalid_metadata_fails_explicitly(self):
        path = self.draft()
        path.write_text(path.read_text().replace("draft = true", 'draft = "false"'))
        with self.assertRaisesRegex(ValueError, "draft must be true or false"):
            build.read_posts()

    def test_duplicate_draft_is_not_overwritten(self):
        path = self.draft("Café & code")
        original = path.read_text()
        with self.assertRaises(FileExistsError):
            self.draft("Café & code")
        self.assertEqual(path.read_text(), original)
        self.assertTrue(path.name.endswith("-cafe-code.md"))

    def test_empty_titles_and_summaries_are_rejected(self):
        for title, summary in (("", "text"), ("A title", " "), ("💬", "text")):
            with self.subTest(title=title), self.assertRaises(ValueError):
                self.draft(title, summary)


class LinkTests(unittest.TestCase):
    def test_local_targets_anchors_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text('<a href="other.html#exists">OK</a><a href="https://example.org">Web</a>')
            (root / "other.html").write_text('<h1 id="exists">Found</h1>')
            errors, external = links.check_local(root)
            self.assertEqual(errors, [])
            self.assertEqual(external, {"https://example.org"})
            (root / "other.html").write_text(
                '<h1 id="exists">Found</h1><p id="exists">Duplicate</p>'
                '<a href="index.html#absent">Broken</a><img src="missing.png">'
            )
            errors, _ = links.check_local(root)
            self.assertEqual(len(errors), 3)

    def test_nested_and_same_site_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "blog").mkdir()
            (root / "index.html").write_text('<h1 id="top">Home</h1>')
            (root / "blog/index.html").write_text(
                '<a href="../index.html#top">Home</a>'
                '<a href="https://h-g-s.github.io/index.html#top">Canonical</a>'
            )
            self.assertEqual(links.check_local(root), ([], set()))

    def test_empty_output_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            errors, _ = links.check_local(Path(directory))
            self.assertEqual(len(errors), 1)


class ArchiveTests(unittest.TestCase):
    def test_decision_tree_paper_includes_journal_and_preprint(self):
        papers = json.loads((ROOT / "data/publications.json").read_text())
        matches = [paper for paper in papers if paper["id"] == "VillasBoas2019"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["preprint"], "https://arxiv.org/pdf/1907.02211")
        self.assertEqual(matches[0]["doi"], "https://doi.org/10.1111/itor.12724")
        rendered = build.publications()
        self.assertIn('href="https://arxiv.org/pdf/1907.02211"', rendered)
        self.assertIn('href="https://doi.org/10.1111/itor.12724"', rendered)

    def test_publication_count_categories_and_downloads(self):
        papers = json.loads((ROOT / "data/publications.json").read_text())
        self.assertEqual(len(papers), 30)
        self.assertEqual(len({paper["title"] for paper in papers}), 30)
        by_id = {paper["id"]: paper for paper in papers}
        self.assertEqual(by_id["Luiz2021"]["url"], "https://doi.org/10.1016/j.orl.2021.10.001")
        self.assertEqual(by_id["Brito2021"]["url"], "https://doi.org/10.1016/j.cor.2020.105176")
        self.assertEqual(by_id["Brito2021"]["preprint"], "https://arxiv.org/pdf/1909.07780")
        self.assertEqual(sum(paper["category"] == "conference" for paper in papers), 5)
        for paper in papers:
            for key in ("url", "bib"):
                target = paper[key]
                if target and target.startswith("assets/"):
                    self.assertTrue((ROOT / target).is_file(), target)
                    if target.endswith(".pdf"):
                        self.assertTrue((ROOT / target).read_bytes().startswith(b"%PDF-"), target)

    def test_biography_does_not_retain_old_contact_details(self):
        home = (ROOT / "content/index.html").read_text()
        self.assertIn("software engineer and former CS professor", home)
        self.assertNotIn("mailto:", home)
        self.assertNotIn("ufop", home.lower())
        self.assertNotIn("ZIP code", home)


if __name__ == "__main__":
    unittest.main()
