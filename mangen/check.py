#!/usr/bin/env python3
"""Execute v2 manual examples and check generated local links."""
from __future__ import annotations

from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit

from main import EXAMPLE_PAGES, localized

ROOT = Path(__file__).resolve().parents[1]


def python_blocks(name: str, language: str) -> list[str]:
    source = (ROOT / "mangen" / "ru" / f"{name}.md").read_text(encoding="utf-8")
    return re.findall(r"```python\n(.*?)```", localized(source, language), re.S)


def run(script: Path, directory: Path, environment: dict[str, str]) -> None:
    result = subprocess.run(
        [sys.executable, str(script)], cwd=directory, env=environment,
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode:
        raise AssertionError(f"{script.name}:\n{result.stdout}\n{result.stderr}")


def check_examples() -> None:
    count = 0
    with TemporaryDirectory(prefix="zencad-manual-") as temporary:
        directory = Path(temporary)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT)
        environment["ZENCAD_CACHE_DIR"] = str(directory / "cache")
        (directory / "model.py").write_text(
            python_blocks("helloworld", "en")[0], encoding="utf-8"
        )
        for name in sorted(EXAMPLE_PAGES):
            for language in ("ru", "en"):
                for index, block in enumerate(python_blocks(name, language)):
                    compile(block, f"{name}:{language}:{index}", "exec")
                    script = directory / f"{name}-{language}-{index}.py"
                    if name == "animate":
                        script.write_text(block, encoding="utf-8")
                        continue
                    # Ordinary display examples execute without opening a viewer.
                    script.write_text(
                        "import zencad.showapi\nzencad.showapi.NOSHOW = True\n" + block,
                        encoding="utf-8",
                    )
                    run(script, directory, environment)
                    count += 1
        print(f"PASS {count} Python documentation blocks", flush=True)
        for language in ("ru", "en"):
            driver = directory / f"run-animation-{language}.py"
            driver.write_text('''from pathlib import Path
from tempfile import TemporaryDirectory
from utest.examples import run_managed_example
from zencad.runtime.runner_supervisor import RunnerSupervisor

if __name__ == "__main__":
    with TemporaryDirectory() as cache:
        supervisor = RunnerSupervisor(cache_directory=cache)
        try:
            model = Path(__file__).with_name("animate-'''+language+'''-0.py")
            success, details = run_managed_example(supervisor, model, 15)
            assert success, details
        finally:
            supervisor.shutdown()
''', encoding="utf-8")
            run(driver, directory, environment)
        print("PASS 2 documented managed animations", flush=True)
        for arguments in (
            ("inspect", "--json"),
            ("inspect", "--tree", "--no-cache"),
            ("check", "--valid", "--solid"),
            ("check", "--volume", "700:800", "--bbox-size", "19:21,9:11,3:5", "--json"),
        ):
            result = subprocess.run(
                [sys.executable, "-m", "zencad", arguments[0],
                 str(directory / "model.py"), *arguments[1:]],
                cwd=directory, env=environment, capture_output=True, text=True, timeout=30,
            )
            if result.returncode:
                raise AssertionError((arguments, result.stdout, result.stderr))
        print("PASS documented inspect/check commands", flush=True)


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.anchors = set()
        self.code_blocks = []
        self.in_pre = False

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.in_pre = True
            self.code_blocks.append("")
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.links.append(value)
            if key == "id" and value:
                self.anchors.add(value)

    def handle_data(self, data):
        if self.in_pre:
            self.code_blocks[-1] += data

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_pre = False


def check_links() -> None:
    docs = ROOT / "docs"
    reference_pages = {
        page.stem + ".html" for page in (ROOT / "mangen" / "ru").glob("*.md")
        if page.stem not in {"nav", "bignav"}
    }
    for language in ("ru", "en"):
        navigation = (ROOT / "mangen" / language / "nav.md").read_text(encoding="utf-8")
        targets = set(re.findall(r"\]\(([^)]+)\)", navigation))
        if missing := reference_pages - targets:
            raise AssertionError(f"Manual sections missing from {language} navigation: {missing}")
    pages = [docs / "index.html", *docs.glob("ru/*.html"), *docs.glob("en/*.html")]
    parsed = {}
    for page in pages:
        parser = PageLinks()
        parser.feed(page.read_text(encoding="utf-8"))
        parsed[page.resolve()] = parser
        if page.parent.name in ("ru", "en") and page.stem in EXAMPLE_PAGES:
            source = (ROOT / "mangen" / "ru" / f"{page.stem}.md").read_text(encoding="utf-8")
            blocks = re.findall(r"```[^\n]*\n(.*?)```", localized(source, page.parent.name), re.S)
            if [b.rstrip() for b in blocks] != [b.rstrip() for b in parser.code_blocks]:
                raise AssertionError(f"Generated code differs from source: {page}")
    checked = 0
    for page, parser in parsed.items():
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = (page.parent / unquote(url.path)).resolve() if url.path else page
            if not target.exists():
                raise AssertionError(f"Broken link in {page}: {link}")
            if url.fragment and target in parsed:
                if unquote(url.fragment) not in parsed[target].anchors:
                    raise AssertionError(f"Broken anchor in {page}: {link}")
            checked += 1
    print(f"PASS {checked} local links across {len(pages)} HTML pages", flush=True)


if __name__ == "__main__":
    check_links()
    from check_reference import check_reference
    check_reference()
    from check_contracts import check_contracts
    check_contracts()
    check_examples()
