#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成一个"像真的"的下载文件夹，用来演示整理。

45 个文件，够乱、够看清、跑得快。
只写 stage/workspace 内部，删之前也只删它。绝不碰真实的 Downloads。
"""

import os
import random
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "stage", "workspace")

TOTAL = 45
random.seed(20261113)

DOCS = ["高数作业第3章.pdf", "线性代数复习提纲.pdf", "实验报告.pdf", "课程论文终稿.pdf",
        "选课手册.pdf", "第4讲 机器学习入门.pptx", "组会汇报0912.pptx",
        "成绩汇总.xlsx", "班费明细.xlsx", "个人简历v3.docx", "读书笔记.docx",
        "~$课件.docx",]

PICS = ["IMG_20240913_142233.jpg", "IMG_20240915_083012.jpg", "IMG_20240920_191544.jpg",
        "相机导出_001.jpg", "表情包 (1).jpg",
        "微信图片_20240915083012.png", "微信图片_20240918142205.png",
        "Screenshot_2024-09-21.png", "屏幕截图 2024-09-23 140522.png", "头像.png",
        "扫码结果.png", "表情包 (2).jpg", "相机导出_002.jpg",
        "发票2024.pdf",]

PKGS = ["Setup_Chrome_v127.exe", "WeChatSetup.exe", "python-3.12.4-amd64.exe",
        "ffmpeg-release.zip", "数据集_sample.zip", "字体包.zip",]

MEDIA = ["录屏_高数第3讲.mp4", "答辩彩排.mp4", "英语听力材料.mp3", "背景音乐.mp3",]

MISC = ["readme.txt", "爬虫草稿.py", "config.json", "备份_旧版.bak", "下载失败.tmp",]

SUBDIRS = {
    "课程资料": ["实验报告.pdf", "讲义合集.pdf"],
    "2024备份": ["旧照片1.jpg", "论文v1.docx"],
}


def wipe():
    """只清空 workspace，函数名就叫 wipe，提醒自己边界在哪。"""
    if os.path.isdir(ROOT):
        assert os.path.abspath(ROOT).startswith(HERE), "拒绝操作 workspace 之外的路径"
        shutil.rmtree(ROOT)
    os.makedirs(ROOT)


MAGIC = {
    ".pdf": b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\n",
    ".docx": b"PK\x03\x04\x14\x00\x06\x00", ".xlsx": b"PK\x03\x04\x14\x00\x06\x00",
    ".pptx": b"PK\x03\x04\x14\x00\x06\x00", ".zip": b"PK\x03\x04\x14\x00\x00\x00",
    ".7z": b"7z\xbc\xaf\x27\x1c\x00\x04",
    ".jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00",
    ".jpeg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00",
    ".png": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x04\x00",
    ".exe": b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff",
    ".msi": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1\x00\x00\x00\x00",
    ".mp4": b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom",
    ".mp3": b"ID3\x03\x00\x00\x00\x00\x00\x00",
    ".bak": b"\x1f\x8b\x08\x00\x00\x00\x00\x00", ".tmp": b"\x00\x01\x02\x03",
}

TEXT = {".txt": "readme\n这是随手记的一些东西。\n".encode() * 80,
        ".py": "import os\n\n\ndef main():\n    print('hello')\n".encode() * 60,
        ".json": '{\n  "version": 1,\n  "items": [],\n  "note": "draft"\n}\n'.encode() * 60}

# 一张货真价实的 1×1 PNG（89 字节）。用来当"被改错后缀的图片"。
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c63000100000500010d0a2db4"
    "0000000049454e44ae426082")


def real_png(w=1024, h=768, rgb=(118, 120, 124)):
    """造一张真正能打开的 PNG：IHDR 合法、IDAT 有数据、结尾有 IEND。"""
    import struct
    import zlib

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    raw = (b"\x00" + bytes(rgb) * w) * h
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


_PNG_CACHE = {}


def png_bytes():
    if "v" not in _PNG_CACHE:
        _PNG_CACHE["v"] = real_png()
    return _PNG_CACHE["v"]


def touch(path, size=None, head=None):
    """造一个占位文件：真的文件头 + 随机内容，看得出是什么格式。

    head 参数用来故意伪造格式——演示里那个"假 PDF"就是靠它。
    """
    ext = os.path.splitext(path)[1].lower()
    if size == 0:
        open(path, "wb").close()          # 真的 0 字节，Word 锁文件就长这样
        return
    if head is not None:
        lead = head
        body = None
    elif ext in TEXT:
        blob = TEXT[ext]
        n = size or random.choice([12_000, 48_000, 89_000])
        data = (blob * (n // len(blob) + 1))[:n]
        with open(path, "wb") as f:
            f.write(data)
        return
    else:
        lead = MAGIC.get(ext, b"\x00\x00\x00\x00")
        body = None

    if size is None:
        size = random.choice([12_000, 48_000, 89_000, 156_000, 340_000])
    with open(path, "wb") as f:
        f.write(lead)
        rest = size - len(lead)
        if rest > 0:
            f.write(os.urandom(rest))


def build():
    wipe()
    plan = [(n, "doc") for n in DOCS] + [(n, "pic") for n in PICS] \
         + [(n, "pkg") for n in PKGS] + [(n, "media") for n in MEDIA] \
         + [(n, "misc") for n in MISC]

    for name, _ in plan:
        p = os.path.join(ROOT, name)
        low = name.lower()
        if name == "发票2024.pdf":
            # 坑 1：一张正常能打开的 PNG，只是名字被改成了 .pdf
            with open(p, "wb") as f:
                f.write(png_bytes())
        elif low.endswith(".png"):
            with open(p, "wb") as f:
                f.write(png_bytes())
        elif name == "~$课件.docx":
            touch(p, size=0)                          # 坑 2：0 字节的 Word 残留
        else:
            touch(p)

    for d, names in SUBDIRS.items():
        dp = os.path.join(ROOT, d)
        os.makedirs(dp, exist_ok=True)
        for n in names:
            touch(os.path.join(dp, n))                # 坑 3：与根目录同名的 实验报告.pdf

    files, dirs = count()
    assert files == TOTAL, f"应生成 {TOTAL} 个文件，实际 {files}"
    print(f"{files} files / {dirs} folders -> stage/workspace")


def count():
    files = dirs = 0
    for _, dirnames, filenames in os.walk(ROOT):
        dirs += len(dirnames)
        files += len(filenames)
    return files, dirs


if __name__ == "__main__":
    build()
