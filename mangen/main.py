#!/usr/bin/env python3
# coding: utf-8

import dominate
import markdown2
import writer
import os


def page_generate(path, title, mdpath, navpath, comming=False):
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
        if comming:
            article.add("English version in preparation. COMMING SOON.")
        dominate.util.raw(
            markdown2.markdown(open(mdpath).read(), extras=["fenced-code-blocks"])
        )

    writer.build_file(path, page)


for f in os.listdir("ru"):
    target = os.path.splitext(f)[0] + ".html"
    page_generate("ru/" + target, "ZenCad", os.path.join("ru", f), "ru/nav.md")

for f in os.listdir("en"):
    target = os.path.splitext(f)[0] + ".html"
    page_generate(
        "en/" + target, "ZenCad", os.path.join("en", f), "en/nav.md", comming=True
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
    dominate.tags.p("Если ваш браузер не поддерживает redirect, перейдите по ссылке:")
    with dominate.tags.p():
        dominate.tags.a("ZenCad/ru", href="ru/index.html")
    with dominate.tags.p():
        dominate.tags.a("ZenCad/en", href="en/index.html")
writer.build_file("index.html", redirect_page)

writer.copy_tree(dst=".", src="images")
writer.copy_file("main.css", "main.css")
writer.remove_file("images/imagen.py")

os.system("cp -rfvT build ../docs")
