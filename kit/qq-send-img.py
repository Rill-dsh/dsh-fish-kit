# -*- coding: utf-8 -*-
"""私聊发图 / 图文：python qq-send-img.py <QQ号> "正文" <图片路径> [第二张...]

正文可以是空字符串（只发图）。表情包就靠这个单独发一条，
别把 markdown 图片链接塞进正文 —— QQ 不渲染，只会变成一行字。

图片路径用绝对路径，Windows 的 C:\\... 或 D:/... 都行。
"""

import json
import os
import sys

import fishlib


def to_file_uri(p):
    p = os.path.abspath(str(p).replace("\\", "/"))
    if p.startswith("file:///"):
        return p
    return "file:///" + p.replace("\\", "/")


def main(argv):
    if len(argv) < 3:
        print('用法: qq-send-img.py <QQ号> "正文" <图片绝对路径> [第二张...]')
        return 2

    uid, text, imgs = argv[0], argv[1], argv[2:]
    segs = []
    if text:
        segs.append({"type": "text", "data": {"text": text}})
    for p in imgs:
        if not os.path.isfile(str(p).replace("\\", "/")):
            print(json.dumps({"ok": False, "错": "图片不存在: " + str(p)}, ensure_ascii=False))
            return 2
        segs.append({"type": "image", "data": {"file": to_file_uri(p)}})

    ok, data = fishlib.onebot("send_private_msg",
                              {"user_id": int(uid), "message": segs}, timeout=30)
    if ok and text:
        fishlib.note("我说", uid, "私聊图", text)
    print(json.dumps({"ok": ok, "返回": data}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(fishlib.main_guard(lambda: main(sys.argv[1:])))
