# -*- coding: utf-8 -*-
"""群发：python qq-send-group.py <群号> "正文"

跟私聊一样按空行拆段，一段一条。群里也要分段 ——
一大坨堆着没人读，一条一句才像人在说话。
"""

import json
import sys
import time

import fishlib


def send_one(gid, text):
    return fishlib.onebot("send_group_msg", {"group_id": int(gid), "message": text})


def main(argv):
    if len(argv) < 2:
        print(json.dumps({"ok": False, "错": "用法: qq-send-group.py <群号> <正文>"}, ensure_ascii=False))
        return 2

    gid, text = argv[0], argv[1]
    if not str(text).strip():
        print(json.dumps({"ok": False, "错": "正文为空，不发"}, ensure_ascii=False))
        return 2

    if fishlib.扫句号(text):
        print(json.dumps(
            {"ok": False, "错": "正文里有句号，扫掉再发", "位置": fishlib.扫句号(text)},
            ensure_ascii=False))
        return 2

    segs = fishlib.split_paragraphs(text) or [str(text)]
    last = {"ok": False}
    for i, seg in enumerate(segs):
        if i:
            time.sleep(0.45)
        ok, data = send_one(gid, seg)
        last = {"ok": ok, "返回": data}
        if not ok:
            # HTTP 200 也可能是业务失败（禁言、风控），要报出来，别当发成功了
            last["第几条失败"] = i + 1
            last["条数"] = len(segs)
            print(json.dumps(last, ensure_ascii=False))
            return 1

    last["条数"] = len(segs)
    fishlib.note("我说", gid, "群", text)
    print(json.dumps(last, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(fishlib.main_guard(lambda: main(sys.argv[1:])))
