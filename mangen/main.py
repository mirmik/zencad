#!/usr/bin/env python3
#coding: utf-8

import dominate
import markdown2
import writer
import os

def page_generate(path, title, mdpath):
	page = dominate.document(title = title)
	with page: dominate.tags.meta(charset=u'utf-8')
	
	header  = page.add(dominate.tags.div(id='header', cls="header"))
	content = page.add(dominate.tags.div(id='content'))
	footer  = page.add(dominate.tags.div(id='footer'))
	
	nav = content.add(dominate.tags.nav(cls="nav"))
	article = content.add(dominate.tags.article(cls="article"))
	
	with page.head:
		dominate.tags.link(rel='stylesheet', href='main.css')
	
	with header:
		with dominate.tags.h1():
			dominate.tags.a("ZenCad", href="index.html", cls="header_ref")
		with dominate.tags.a("View on GitHub", href="https://github.com/mirmik/zencad", cls="btn btn-github"):
			dominate.tags.span(cls='icon')
		
	with nav:
		dominate.util.raw(markdown2.markdown(open("texts/nav.md").read()))
	
	with article:
		dominate.util.raw(markdown2.markdown(open(mdpath).read(), extras=["fenced-code-blocks"]))

	writer.build_file(path, page)

for f in os.listdir("texts"):
	target = os.path.splitext(f)[0]+".html"
	page_generate(target, "ZenCad", os.path.join("texts", f))

writer.copy_tree(dst=".", src="images")
writer.copy_file("main.css", "main.css")
writer.remove_file("images/imagen.py")