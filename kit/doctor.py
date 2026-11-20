# -*- coding: utf-8 -*-
"""装完先跑这个：一条一条告诉你哪儿还没通。

    python doctor.py

不修东西，只查。哪条打 ✗，就照着前面那句人话去补。
退出码 0 = 全绿；1 = 有红的。
"""

import io
import json
import os
import sys

import fishlib


def line(ok, title, detail=""):
    mark = "✓" if ok else "✗"
    print("%s %s%s" % (mark, title, ("  —  " + detail) if detail else ""))
    return bool(ok)


def main():
    results = []

    # 1. 配置
    try:
        c = fishlib.cfg()
        results.append(line(True, "配置文件", c.get("_path", "")))
    except SystemExit:
        return 1

    # 2. Python
    py = sys.version_info
    results.append(line(py >= (3, 8), "Python 版本", "%d.%d" % (py[0], py[1])))

    # 3. OneBot 通不通
    base = (c.get("onebot") or {}).get("base") or ""
    if not base:
        results.append(line(False, "OneBot 地址", "config.json 里 onebot.base 没填"))
    else:
        ok, data = fishlib.onebot("get_login_info", {})
        if ok:
            d = data.get("data") or {}
            results.append(line(True, "OneBot 连通", "登录中：%s（%s）" % (
                d.get("nickname", "?"), d.get("user_id", "?"))))
            self_qq = (c.get("self") or {}).get("qq")
            if self_qq and str(self_qq) != str(d.get("user_id")):
                results.append(line(False, "self.qq 对不上",
                                    "配置里是 %s，后端登录的是 %s" % (self_qq, d.get("user_id"))))
        else:
            results.append(line(False, "OneBot 连通",
                                "连不上 %s。后端起了吗？端口对吗？token 填了吗？（%s）"
                                % (base, (data or {}).get("错", ""))))

    # 4. 目录能写
    for name in ("daily", "stickers"):
        p = fishlib.path_of(name)
        if not p:
            results.append(line(False, "paths." + name, "没填（不影响跑，但这条鱼会少记东西）"))
            continue
        try:
            probe = os.path.join(p, ".fish-doctor")
            io.open(probe, "w", encoding="utf-8").write("ok")
            os.remove(probe)
            results.append(line(True, "paths." + name, p))
        except Exception as e:
            results.append(line(False, "paths." + name, "写不进去：%s" % e))

    # 5. 语音参考
    ref = fishlib.path_of("voice_ref")
    results.append(line(bool(ref) and os.path.isfile(ref), "声音参考",
                        ref or "没填（要发语音才需要）"))

    # 6. 外部凭证（没配也不算错，配了才查）
    for key, label in (("credential", "B站凭证"), ("cookies", "抖音 cookie")):
        sec = "bili" if key == "credential" else "douyin"
        p = (c.get(sec) or {}).get(key) or ""
        if p:
            results.append(line(os.path.isfile(p), label, p))

    print()
    bad = sum(1 for ok in results if not ok)
    print("全绿，可以开始了。" if not bad else "还有 %d 处没通，照上面的说明补。" % bad)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(fishlib.main_guard(main))
