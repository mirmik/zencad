#!/usr/bin/env python3
# coding: utf-8

import dominate
import markdown2
import os
import shutil


def build_file(path, doc):
    dirpath = os.path.join("build", os.path.dirname(path))
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    f = open(os.path.join("build", path), "w")
    f.write(str(doc))


def copy_file(dst, src):
    shutil.copyfile(src=src, dst=os.path.join("build", dst))


def remove_file(path):
    os.remove(os.path.join("build", path))


def copy_tree(dst, src):
    cmd = "cp -rf {src} {dst}".format(src=src, dst=os.path.join("build", dst))
    os.system(cmd)
