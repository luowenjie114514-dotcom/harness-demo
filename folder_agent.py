#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
folder_agent.py —— 把 Pi 拆开之后，剩下的那点东西

Pi 的 agent 循环是 418 行 TypeScript。这个文件用 12 行 Python 复现它的骨架：
工具、循环、把结果回传、事后核对。仅此四样。

    python folder_agent.py

离线版：决策由内置规则给出，行为和真模型一致，断网也能演示。
真模型请用 pi（见 run_pi.cmd）。
"""

import os
import shutil
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "stage", "workspace")

BUCKET = {".jpg": "图片", ".jpeg": "图片", ".png": "图片", ".gif": "图片",
          ".pdf": "文档", ".docx": "文档", ".pptx": "文档", ".xlsx": "文档", ".txt": "文档",
          ".exe": "安装包", ".msi": "安装包", ".zip": "安装包", ".7z": "安装包",
          ".dmg": "安装包", ".bak": "安装包",
          ".mp4": "视频", ".mp3": "视频"}

DIRS = ["图片", "文档", "安装包", "视频", "其它", "待确认"]


def safe(p):
    """所有路径都必须落在 workspace 里面。这是硬边界。"""
    full = os.path.abspath(os.path.join(ROOT, p))
    if not full.startswith(os.path.abspath(ROOT)):
        raise ValueError("越界：" + p)
    return full


# ───────────────────── 工具：模型能碰到的世界（它的"手"） ─────────────────────
def t_ls(_=""):
    items = sorted(os.listdir(ROOT))
    body = [n + ("/" if os.path.isdir(safe(n)) else "") for n in items]
    nf = sum(1 for n in items if os.path.isfile(safe(n)))
    nd = len(items) - nf
    return f"{len(items)} 个条目（文件 {nf}、目录 {nd}）：\n" + "\n".join(body)


def t_head(path, n=4):
    with open(safe(path), "rb") as f:
        b = f.read(n)
    return f"{path} 前 {n} 字节：{' '.join(f'{x:02X}' for x in b)}"


def t_mkdir(name):
    os.makedirs(safe(name), exist_ok=True)
    return f"已创建 {name}/"


def t_mv_many(plan):
    done, renamed, failed = 0, [], []
    for target, names in plan.items():
        os.makedirs(safe(target), exist_ok=True)
        for n in names:
            src = safe(n)
            dst = os.path.join(safe(target), os.path.basename(n))
            try:
                if os.path.exists(dst):
                    stem, ext = os.path.splitext(os.path.basename(n))
                    i = 2
                    while os.path.exists(dst):
                        dst = os.path.join(safe(target), f"{stem}_{i}{ext}")
                        i += 1
                    renamed.append(os.path.basename(dst))
                shutil.move(src, dst)
                done += 1
            except Exception as e:
                failed.append(f"{n}({type(e).__name__})")
    msg = f"移动 {done} 个"
    if renamed:
        msg += f"；{len(renamed)} 个重名改名为 {', '.join(renamed)}"
    if failed:
        msg += f"；失败 {len(failed)} 个：{'、'.join(failed)}"
    return msg


def t_count(_=""):
    return f"{count_num()[0]} 个文件，{count_num()[1]} 个目录"


TOOLS = {"ls": t_ls, "head": t_head, "mkdir": t_mkdir, "mv_many": t_mv_many, "count": t_count}


def count_num():
    files = dirs = 0
    for _, dn, fn in os.walk(ROOT):
        dirs += len(dn)
        files += len(fn)
    return files, dirs


# ══════════════════ 核心：这就是 harness，12 行，Pi 做的也是这件事 ══════════════════
def loop(task, llm, max_steps=20):
    msgs = [{"role": "user", "content": task}]
    for _ in range(max_steps):
        act = llm(msgs)                                   # ① 问模型下一步
        if act["name"] == "finish":                       # ② 它说完了
            return act["args"]["report"], msgs
        try:
            obs = TOOLS[act["name"]](**act["args"])       # ③ 替它动手
        except Exception as e:
            obs = f"ERROR: {type(e).__name__}: {e}"       # ④ 出错也是信息，不是终点
        msgs.append({"role": "tool", "name": act["name"], "content": obs})  # ⑤ 把世界还给它
    return "步数用尽", msgs
# ══════════════════════════════════════════════════════════════════════════════════


_state = {}


def mock_llm(msgs):
    """离线替身。它做的每个决定，都只依赖它真正看到过的东西。"""
    seen = [m for m in msgs if m["role"] == "tool"]
    did = [m["name"] for m in seen]
    last = seen[-1]["content"] if seen else ""

    if "ls" not in did:
        return {"name": "ls", "args": {}}

    if "head" not in did:                                  # 对那个 pdf 起了疑心
        return {"name": "head", "args": {"path": "发票2024.pdf"}}

    if "mv_many" not in did:
        n = did.count("mkdir")
        if n < len(DIRS):
            return {"name": "mkdir", "args": {"name": DIRS[n]}}
        _state["plan"] = build_plan("89 50 4E 47" in t_head("发票2024.pdf"))
        return {"name": "mv_many", "args": {"plan": _state["plan"]}}

    if "count" not in did:
        return {"name": "count", "args": {}}

    return {"name": "finish", "args": {"report": "整理完成"}}


def build_plan(is_png):
    """这里其实是模型该干的活：看清单、定规则、分批搬。"""
    plan, skip = {}, []
    for n in sorted(os.listdir(ROOT)):
        if not os.path.isfile(safe(n)):
            continue
        if os.path.getsize(safe(n)) == 0:                  # 0 字节残留，别碰
            skip.append(n)
            continue
        bucket = BUCKET.get(os.path.splitext(n)[1].lower(), "其它")
        if n == "发票2024.pdf" and is_png:                 # 名字骗人，内容不骗人
            bucket = "图片"
        plan.setdefault(bucket, []).append(n)
    _state["skip"] = skip
    return plan


def run():
    before = count_num()[0]
    print("═" * 64)
    print(f" 整理前：workspace/ 里有 {before} 个文件")
    print("═" * 64)

    report, msgs = loop("把 workspace/ 整理好，按类型分类归档。", mock_llm)

    for m in msgs:
        if m["role"] == "tool":
            head = m["content"].strip().splitlines()[0]
            print(f"  {m['name']:<8} -> {head[:58]}")

    after = count_num()[0]
    print("═" * 64)
    print(f" 前后清点：{before} -> {after}" + ("  ✓" if before == after else "  ✗ 对不上"))
    skip = _state.get("skip", [])
    if skip:
        print(f" 跳过：{'、'.join(skip)}")


if __name__ == "__main__":
    run()
