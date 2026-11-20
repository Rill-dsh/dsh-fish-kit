# -*- coding: utf-8 -*-
"""看 B站私信有没有新消息。给定时任务用。

    python bili-dm-check.py

有新的就打印「NEW bili-dm 时间 | 内容」，没有就打印 no new。
退出码 0 = 查成功（不管有没有新消息）；1 = 没查成。

为什么要走 curl 兜底：api.vc.bilibili.com 这个域名的 TLS 握手有时会被重置，
urllib 直接连不上，curl 能过（但不稳，要重试）。两个都试，谁通用谁。

前置：B站登录凭证，字段 sessdata / bili_jct / buvid3 / dedeuserid
（bilibili 系插件登录后一般会存在自己的凭证文件里，路径填进 config.json）。
"""

import io
import json
import os
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.request

import fishlib

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def parse_lenient(raw):
    txt = raw.decode("utf-8", "replace").strip()
    if not txt:
        return None
    try:
        return json.loads(txt)
    except Exception:
        pass
    try:  # 尾部被截断时取到最后一个可解析对象
        obj, _ = json.JSONDecoder().raw_decode(txt)
        return obj
    except Exception:
        return None


def fetch_via_curl(cookie, url, attempts=6):
    hdr = os.path.join(tempfile.gettempdir(), "fish_bili_dm_hdr.txt")
    io.open(hdr, "w", encoding="utf-8").write(
        "Cookie: %s\nReferer: https://message.bilibili.com/\nUser-Agent: %s\n" % (cookie, UA))
    try:
        for i in range(attempts):
            try:
                out = subprocess.run(
                    ["curl", "-s", "--max-time", "25", "-H", "@" + hdr, url],
                    capture_output=True, timeout=40)
                obj = parse_lenient(out.stdout)
                if obj and (obj.get("data") or {}).get("messages") is not None:
                    return obj
            except Exception:
                pass
            time.sleep(1 + i)
        raise RuntimeError("bili-dm: 接口多次重试都没拿到数据（网络层不稳）")
    finally:
        try:
            os.remove(hdr)
        except Exception:
            pass


def main():
    c = fishlib.cfg()
    b = c.get("bili") or {}
    cred_path = b.get("credential") or ""
    talker = int(b.get("watch_uid") or 0)
    if not cred_path or not os.path.isfile(cred_path):
        print(json.dumps({"ok": False, "错": "config.json 里 bili.credential 没填或文件不存在"}, ensure_ascii=False))
        return 1
    if not talker:
        print(json.dumps({"ok": False, "错": "config.json 里 bili.watch_uid 没填（要看谁的私信）"}, ensure_ascii=False))
        return 1

    cred = json.load(io.open(cred_path, encoding="utf-8"))
    self_uid = int(cred.get("dedeuserid") or 0)
    cookie = ("SESSDATA=%s; bili_jct=%s; buvid3=%s; DedeUserID=%s" % (
        cred.get("sessdata", ""), cred.get("bili_jct", ""),
        cred.get("buvid3", ""), cred.get("dedeuserid", "")))

    url = ("https://api.vc.bilibili.com/svr_sync/v1/svr_sync/fetch_session_msgs"
           "?talker_id=%d&session_type=1&size=20" % talker)

    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={
            "Cookie": cookie, "User-Agent": UA,
            "Referer": "https://message.bilibili.com/"})
        d = json.loads(urllib.request.urlopen(req, timeout=20, context=ctx)
                       .read().decode("utf-8", "replace"))
    except Exception:
        d = fetch_via_curl(cookie, url)

    msgs = ((d.get("data") or {}).get("messages")) or []

    seen_path = b.get("seen") or os.path.join(fishlib.path_of("daily") or ".", "bili-dm-seen.json")
    state = {}
    if os.path.exists(seen_path):
        try:
            state = json.load(io.open(seen_path, encoding="utf-8"))
        except Exception:
            state = {}
    last = int(state.get(str(talker), 0))

    new = []
    for m in msgs:
        if int(m.get("sender_uid", 0)) == self_uid:
            continue
        ts = int(m.get("timestamp", 0))
        if ts <= last:
            continue
        content = m.get("content", "")
        try:
            content = json.loads(content).get("content", content)
        except Exception:
            pass
        new.append((ts, content))

    if new:
        new.sort()
        state[str(talker)] = new[-1][0]
        io.open(seen_path, "w", encoding="utf-8").write(json.dumps(state, ensure_ascii=False))
        for ts, txt in new:
            print("NEW bili-dm", time.strftime("%H:%M", time.localtime(ts)), "|", str(txt)[:200])
    else:
        print("no new")
    return 0


if __name__ == "__main__":
    sys.exit(fishlib.main_guard(main))
