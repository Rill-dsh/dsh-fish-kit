# -*- coding: utf-8 -*-
"""私聊直发：只发给指定 QQ 号，不走桥接的绑定名单。

    python qq-send.py 12345678 "正文"
    python qq-send.py --file 12345678 一段话.txt

为什么要绕过桥接名单：桥接的 [QQ]…[/QQ] 块会把同一条消息发给
所有开着的私聊，几个人同时收到。串线的根就埋在那儿。
直发只认一个号，没有第二种解释。

分段规矩：正文里的空行 = 一条消息。一个换行不算，一句一行会炸成一串碎片。
"""

import json
import sys
import time
import io

import fishlib


def send_one(uid, text):
    return fishlib.onebot("send_private_msg", {"user_id": int(uid), "message": text})


def send_split(uid, text, gap=0.45):
    segs = fishlib.split_paragraphs(text) or [str(text)]
    last = {"ok": False}
    for i, seg in enumerate(segs):
        if i:
            time.sleep(gap)
        ok, data = send_one(uid, seg)
        last = {"ok": ok, "返回": data}
        if not ok:
            last["第几条失败"] = i + 1
            last["条数"] = len(segs)
            return last
    last["条数"] = len(segs)
    return last


def main(argv):
    if len(argv) < 2:
        print(json.dumps(
            {"ok": False, "错": "用法: qq-send.py <QQ号> <正文> | --file <QQ号> <文件>"},
            ensure_ascii=False))
        return 2

    if argv[0] == "--file":
        uid, text = argv[1], io.open(argv[2], encoding="utf-8").read()
    else:
        uid, text = argv[0], argv[1]

    if not str(text).strip():
        print(json.dumps({"ok": False, "错": "正文为空，不发"}, ensure_ascii=False))
        return 2

    # 她说过五次：QQ 里不许有句号。发之前扫一遍，不是记着，是扫。
    if fishlib.扫句号(text):
        print(json.dumps(
            {"ok": False, "错": "正文里有句号，扫掉再发", "位置": fishlib.扫句号(text)},
            ensure_ascii=False))
        return 2

    r = send_split(uid, text)
    if r.get("ok"):
        fishlib.note("我说", uid, "私聊", text)
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(fishlib.main_guard(lambda: main(sys.argv[1:])))
