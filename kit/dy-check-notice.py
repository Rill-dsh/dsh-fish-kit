# -*- coding: utf-8 -*-
"""看抖音有没有新的 @ / 评论 / 私信。给定时任务用。

    python dy-check-notice.py

有新的就一行一条打出来，没有就打印 no new。
结果同时落到 daily 目录下的 dy-notices.json，方便别的东西接着用。

前置：抖音 web 端的 cookies，存在浏览器导出的 json 里
（形状是 {"cookies": [{"name":..., "value":..., "domain":...}, ...]}）。
路径填进 config.json 的 douyin.cookies。

为什么自己写而不是调插件：插件那条路要先起浏览器，太重；
这个只是一次 GET，用现成 cookie 就够了。风控要紧的时候它会返回
空列表而不是报错 —— 那就当没新消息，别硬重试去撞。
"""

import io
import json
import os
import ssl
import sys
import time
import urllib.request

import fishlib

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36")

URL = ("https://www.douyin.com/aweme/v1/web/notice/?device_platform=webapp&aid=6383"
       "&channel=channel_pc_web&is_new_notice=1&is_mark_read=0&notice_group=960&count=20"
       "&min_time=0&max_time=0&update_version_code=170400&pc_client_type=1"
       "&pc_libra_divert=Windows&support_h265=1&support_dash=0&cpu_core_num=12"
       "&version_code=170400&version_name=17.4.0&cookie_enabled=true"
       "&screen_width=1440&screen_height=950&browser_language=zh-CN"
       "&browser_platform=Win32&browser_name=Edge&browser_version=156.0.0.0")


def main():
    c = fishlib.cfg()
    dcfg = c.get("douyin") or {}
    state_path = dcfg.get("cookies") or ""
    if not state_path or not os.path.isfile(state_path):
        print(json.dumps({"ok": False, "错": "config.json 里 douyin.cookies 没填或文件不存在"}, ensure_ascii=False))
        return 1

    daily = fishlib.path_of("daily") or "."
    seen_path = dcfg.get("seen") or os.path.join(daily, "dy-seen.json")

    state = json.load(io.open(state_path, encoding="utf-8"))
    cookies = {ck["name"]: ck["value"] for ck in state.get("cookies", [])
               if "douyin.com" in (ck.get("domain") or "")}
    if not cookies:
        print(json.dumps({"ok": False, "错": "cookie 文件里没有 douyin.com 的 cookie"}, ensure_ascii=False))
        return 1
    cookie_hdr = "; ".join("%s=%s" % (k, v) for k, v in cookies.items())

    ctx = ssl.create_default_context()
    req = urllib.request.Request(URL, headers={
        "Cookie": cookie_hdr, "User-Agent": UA,
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json, text/plain, */*",
    })
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))

    items = data.get("notice_list_v2") or []
    print("items:", len(items))

    seen = {}
    if os.path.exists(seen_path):
        try:
            seen = json.load(io.open(seen_path, encoding="utf-8"))
        except Exception:
            seen = {}

    out = []
    for it in items:
        nid = str(it.get("nid"))
        t = it.get("type")
        cm = (it.get("comment") or {}).get("comment") or {}
        at = it.get("at") or {}
        if t == 45 and at:      # @ 我
            text = at.get("content") or ""
            user = (at.get("user_info") or {}).get("nickname") or ""
            su = at.get("schema_url") or ""
            aweme = ""
            if "/detail/" in su:
                aweme = su.split("/detail/")[1].split("?")[0]
        else:                    # 评论 / 回复
            text = cm.get("text") or ""
            user = (cm.get("user") or {}).get("nickname") or ""
            aweme = cm.get("aweme_id") or ""
        ts = it.get("create_time") or 0
        rec = {"nid": nid, "type": t, "text": text, "user": user,
               "aweme_id": aweme, "time": ts,
               "when": time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else ""}
        rec["is_new"] = nid not in seen
        seen[nid] = 1
        out.append(rec)

    io.open(seen_path, "w", encoding="utf-8").write(json.dumps(seen, ensure_ascii=False))
    io.open(os.path.join(daily, "dy-notices.json"), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))

    new = [r for r in out if r["is_new"]]
    if not new:
        print("no new")
        return 0

    for r in new[:15]:
        print("%s | %s | %s | %s" % (r["when"], r["user"], (r["text"] or "")[:60], r["aweme_id"]))
    return 0


if __name__ == "__main__":
    sys.exit(fishlib.main_guard(main))
