#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clear.py —— 清空待整理区

只动 stage/workspace 这一个目录，外面的东西一概不碰。
"""

import os
import shutil
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "stage", "workspace")


def count():
    return sum(len(f) for _, _, f in os.walk(ROOT))


def main():
    if not os.path.isdir(ROOT):
        print("待整理区不存在，什么都不用做。")
        return 0

    assert os.path.abspath(ROOT).startswith(HERE), "拒绝操作待整理区之外的路径"

    n = count()
    if n == 0:
        print("待整理区已经是空的。")
        return 0

    print(f"待整理区里有 {n} 个文件。")
    try:
        ans = input("全部删掉？输入 y 确认：").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n没动。")
        return 0

    if ans != "y":
        print("没动。")
        return 0

    shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    print(f"已清空，删掉 {n} 个文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
