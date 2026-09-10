#!/usr/bin/env python3
"""Build the bilingual manual without evaluating CAD/image scripts."""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import shutil
import re

import markdown2

ROOT = Path(__file__).resolve().parent
PAGE_ALIASES = {
    "trans1": "trans0", "lincycle": "prim1d", "platonic": "prim3d",
    "navigation": "gui", "markers": "interactive_object",
}

EXAMPLE_PAGES = {
    "index", "installation", "helloworld", "migration", "version2", "caching",
    "prim0d", "modeling", "selectors", "validation", "show", "interactive_object",
    "animate", "kinematic", "agents", "headless", "expimp", "geomprop", "bbox", "trimesh",
}


def check_source_pairs() -> None:
    """Require a matching source page in each language tree."""
    pages = {
        language: {page.name for page in (ROOT / language).glob("*.md")}
        for language in ("ru", "en")
    }
    if pages["ru"] != pages["en"]:
        raise ValueError(
            f"Unpaired manual pages: missing in en: {sorted(pages['ru'] - pages['en'])}; "
            f"missing in ru: {sorted(pages['en'] - pages['ru'])}"
        )


def markdown(source: str) -> str:
    return str(markdown2.markdown(
        source, extras=["fenced-code-blocks", "tables", "header-ids"]
    ))



def render_page(name: str, source: str, nav: str, language: str) -> str:
    html = f'''<!DOCTYPE html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ZenCad — {escape(name)}</title>
  <link rel="stylesheet" href="../main.css">
</head>
<body>
<div id="header" class="header">
  <h1><a class="header_ref" href="index.html">ZenCad</a></h1>
  <a href="https://github.com/mirmik/zencad" class="btn btn-github">View on GitHub<span class="icon"></span></a>
  <p><a href="../ru/{name}.html">Ru</a> · <a href="../en/{name}.html">En</a></p>
</div>
<div id="content">
<nav class="nav">{markdown(nav)}</nav>
<article class="article">{markdown(source)}</article>
</div>
</body>
</html>
'''
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def build(output: Path) -> None:
    check_source_pairs()
    output.mkdir(parents=True, exist_ok=True)
    for language in ("ru", "en"):
        destination = output / language
        destination.mkdir(exist_ok=True)
        nav = (ROOT / language / "nav.md").read_text(encoding="utf-8")
        generated = set()
        for source in sorted((ROOT / language).glob("*.md")):
            if source.stem == "nav":
                continue
            name = source.stem
            content = source.read_text(encoding="utf-8")
            (destination / f"{name}.html").write_text(
                render_page(name, content, nav, language), encoding="utf-8"
            )
            generated.add(f"{name}.html")
        # Preserve pages without a Markdown source and keep their navigation current.
        for old in sorted((ROOT.parent / "docs" / language).glob("*.html")):
            if old.name in generated:
                continue
            if old.stem in PAGE_ALIASES:
                target = PAGE_ALIASES[old.stem]
                content = (ROOT / language / f"{target}.md").read_text(encoding="utf-8")
                (destination / old.name).write_text(
                    render_page(old.stem, content, nav, language), encoding="utf-8"
                )
                continue
            content = old.read_text(encoding="utf-8")
            content = re.sub(r'<aside class="legacy-notice".*?</aside>', "", content, flags=re.S)
            content = re.sub(r'<nav class="nav">.*?</nav>',
                             lambda _: '<nav class="nav">' + markdown(nav) + '</nav>',
                             content, flags=re.S)
            (destination / old.name).write_text(content, encoding="utf-8")
    (output / "index.html").write_text('''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=ru/index.html">
<title>ZenCad documentation</title></head>
<body><h1>ZenCad 2</h1><p><a href="ru/index.html">Руководство на русском</a></p>
<p><a href="en/index.html">English guide</a></p></body></html>
''', encoding="utf-8")
    shutil.copyfile(ROOT / "main.css", output / "main.css")
    for name in ("images", "development", "architecture-council"):
        source = ROOT.parent / "docs" / name
        if source.exists() and source.resolve() != (output / name).resolve():
            shutil.copytree(source, output / name, dirs_exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=["update"])
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    output = arguments.output or (
        ROOT.parent / "docs" if arguments.action == "update" else ROOT / "build"
    )
    build(output.resolve())
    print(f"Manual built: {output.resolve()}")


if __name__ == "__main__":
    main()
