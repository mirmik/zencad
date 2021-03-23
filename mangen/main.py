#!/usr/bin/env python3
# coding: utf-8

import dominate
import markdown2
import writer
import os
import sys

languages_predicates = (":ru", ":en")

list_of_changes = {
    "Сигнатура:": {"ru": "Сигнатура:", "en": "Signature:"},
    "Signature:": {"ru": "Сигнатура:", "en": "Signature:"},
    "Пример:": {"ru": "Пример:", "en": "Example:"},
    "Example:": {"ru": "Пример:", "en": "Example:"},
}


def page_generate(path, title, mdpath, navpath, lang):
    lines = open(mdpath).readlines()
    lines = [l.strip() for l in lines]

    filtered_lines = []
    languages_predicates_prevent = [
        l for l in languages_predicates if l != ":"+lang]

    filter = False
    for l in lines:
        if l.startswith(":"):
            filter = False
            for r in languages_predicates_prevent:
                if l.startswith(r):
                    filter = True
                    break
            else:
                filter = False
            continue

        for k, v in list_of_changes.items():
            if l.startswith(k):
                l = v[lang]
                break

        if filter is False:
            filtered_lines.append(l)

    text = "\n".join(filtered_lines)

    page = dominate.document(title=title)
    with page:
        dominate.tags.meta(charset=u"utf-8")

    header = page.add(dominate.tags.div(id="header", cls="header"))
    content = page.add(dominate.tags.div(id="content"))
    footer = page.add(dominate.tags.div(id="footer"))

    nav = content.add(dominate.tags.nav(cls="nav"))
    article = content.add(dominate.tags.article(cls="article"))

    with page.head:
        dominate.tags.link(rel="stylesheet", href="../main.css")

    with header:
        with dominate.tags.h1():
            dominate.tags.a("ZenCad", href="index.html", cls="header_ref")
        with dominate.tags.a(
            "View on GitHub",
            href="https://github.com/mirmik/zencad",
            cls="btn btn-github",
        ):
            dominate.tags.span(cls="icon")
        with dominate.tags.p():
            dominate.tags.a("Ru", href="../ru/" + path.split("/")[1])
            dominate.tags.a("En", href="../en/" + path.split("/")[1])

    with nav:
        dominate.util.raw(markdown2.markdown(open(navpath).read()))

    with article:
        dominate.util.raw(
            markdown2.markdown(text, extras=[
                               "fenced-code-blocks", "tables", "header-ids"])
        )

    writer.build_file(path, page)


# Подготавка файлов русской версии.
for f in os.listdir("ru"):
    target = os.path.splitext(f)[0] + ".html"
    page_generate(
        path="ru/" + target,
        title="ZenCad",
        mdpath=os.path.join("ru", f),
        navpath="ru/nav.md",
        lang="ru")

# Подготавка файлов английской версии.
for f in os.listdir("ru"):
    target = os.path.splitext(f)[0] + ".html"
    page_generate(
        path="en/" + target,
        title="ZenCad",
        mdpath=os.path.join("ru", f),
        navpath="en/nav.md",
        lang="en"
    )

redirect_page = dominate.document()
with redirect_page:
    dominate.tags.meta(charset=u"utf-8")
redirect_page.add(
    dominate.util.raw(
        """<meta http-equiv="refresh" content="0; url=ru/index.html" />"""
    )
)
with redirect_page:
    dominate.tags.p(
        "Если ваш браузер не поддерживает redirect, перейдите по ссылке:")
    with dominate.tags.p():
        dominate.tags.a("ZenCad/ru", href="ru/index.html")
    with dominate.tags.p():
        dominate.tags.a("ZenCad/en", href="en/index.html")
writer.build_file("index.html", redirect_page)

os.system("cd images && ./imagen.py")
writer.copy_tree(dst=".", src="images")
writer.copy_file("main.css", "main.css")
writer.remove_file("images/imagen.py")

if len(sys.argv) > 1 and sys.argv[1] == "update":
    os.system("cp -rfvT build ../docs")
