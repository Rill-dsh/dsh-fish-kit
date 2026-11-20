# -*- coding: utf-8 -*-
"""群里发图：python qq-send-group-img.py <群号> "正文" <图片路径>

正文给空字符串就是只发图。
表情包规矩：图单独一条发，别跟字挤在一起 —— 挤在一起会变成
「正文里夹个链接」，QQ 只显示文件名字。
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
    if len(argv) < 2:
        print('用法: qq-send-group-img.py <群号> "正文" <图片绝对路径>')
        return 2

    gid, text, imgs = argv[0], argv[1], argv[2:]
    segs = []
    if text:
        segs.append({"type": "text", "data": {"text": text}})
    for p in imgs:
        if not os.path.isfile(str(p).replace("\\", "/")):
            print(json.dumps({"ok": False, "错": "图片不存在: " + str(p)}, ensure_ascii=False))
            return 2
        segs.append({"type": "image", "data": {"file": to_file_uri(p)}})

    ok, data = fishlib.onebot("send_group_msg",
                              {"group_id": int(gid), "message": segs}, timeout=30)
    if ok and text:
        fishlib.note("我说", gid, "群图", text)
    print(json.dumps({"ok": ok, "返回": data}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(fishlib.main_guard(lambda: main(sys.argv[1:])))
