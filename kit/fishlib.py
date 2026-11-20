# -*- coding: utf-8 -*-
"""fishlib —— 这条鱼和外界之间那层的公共件。

所有脚本共用同一份配置：config.json（放在 kit 目录里，或者用环境变量
FISH_CONFIG 指到别处）。配置文件不要提交进 git。

配置长这样（config.example.json 有完整版）：

{
  "onebot": {
    "base": "http://127.0.0.1:3000",
    "token": ""
  },
  "paths": {
    "daily": "D:/fish/daily",
    "stickers": "D:/fish/stickers",
    "voice_ref": "D:/fish/voice-reference.wav"
  },
  "voice": {
    "model": "mimo-v2.5-tts-voiceclone",
    "api_key": "",
    "endpoint": ""
  }
}

别在脚本里写死路径和 QQ 号 —— 换一台机器就废了。
"""

import io
import json
import os
import re
import sys
import datetime
import time
import urllib.request
import urllib.error


# ---------------------------------------------------------------- 配置

def _candidates():
    here = os.path.dirname(os.path.abspath(__file__))
    yield os.environ.get("FISH_CONFIG") or ""
    yield os.path.join(here, "config.json")
    yield os.path.join(os.path.expanduser("~"), ".dsh", "fish-kit.json")


def load_config():
    """按优先级找配置；一个都找不到就报一句人话，不要抛栈。"""
    for p in _candidates():
        if p and os.path.isfile(p):
            with io.open(p, encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["_path"] = p
            return cfg
    sys.stderr.write(
        "找不到配置文件。复制 config.example.json 成 config.json，填好再跑。\n"
        "（也可以用环境变量 FISH_CONFIG 指到别处）\n"
    )
    raise SystemExit(2)


_CFG = None


def cfg():
    global _CFG
    if _CFG is None:
        _CFG = load_config()
    return _CFG


def path_of(name, default=""):
    """取一个路径配置，顺带把目录建出来。"""
    p = (cfg().get("paths") or {}).get(name) or default
    if not p:
        return ""
    p = os.path.expanduser(str(p))
    if name != "voice_ref":
        os.makedirs(p, exist_ok=True)
    return p


# ---------------------------------------------------------------- OneBot

def onebot(action, payload, timeout=20):
    """打一发 OneBot v11 接口，返回 (ok, data)。

    注意 HTTP 200 不等于发成功：禁言、风控、被拉黑都还是 200。
    所以要看 retcode，不能只看状态码。
    """
    c = cfg().get("onebot") or {}
    base = str(c.get("base") or "http://127.0.0.1:3000").rstrip("/")
    token = str(c.get("token") or "").strip()
    # token 只能是 ASCII。填成「这里填token」这种中文说明时，
    # urllib 的 add_header 会拿 latin-1 编码直接炸，报出来的错跟真正原因
    # 八竿子打不着。与其让人对着 UnicodeEncodeError 找半天，不如说清楚。
    if token and not token.isascii():
        return False, {"错": "onebot.token 里有中文，像是没改成真的 token（没设 token 就留空）"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(base + "/" + action, data=body, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return False, {"错": "HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:300])}
    except Exception as e:
        return False, {"错": "%s: %s" % (type(e).__name__, e)}
    try:
        data = json.loads(raw)
    except Exception:
        return False, {"错": "返回不是 JSON: " + raw[:300]}
    ok = data.get("status") == "ok" or data.get("retcode") == 0
    return bool(ok), data


# ---------------------------------------------------------------- 拆段

def split_paragraphs(text):
    """按空行拆段。桥接的规矩也是这个：一个空行 = 一条消息。

    单换行不拆，否则一句一行会炸成一串碎片。
    """
    parts = [s.strip() for s in re.split(r"\n\s*\n", str(text or ""))]
    return [s for s in parts if s]


# ---------------------------------------------------------------- 流水

def note(direction, target, kind, text):
    """把说过的话追加到 每日流水/<日期>_我说.md，句子级，不写结论。

    记的是原话和出处，不是「她今天心情不错」这种被压过的判断。
    """
    daily = path_of("daily")
    if not daily:
        return
    try:
        day = datetime.date.today().isoformat()
        fp = os.path.join(daily, day + "_%s.md" % direction)
        stamp = datetime.datetime.now().strftime("%H:%M")
        with io.open(fp, "a", encoding="utf-8") as f:
            for seg in split_paragraphs(text):
                f.write("%s %s%s：%s\n" % (stamp, kind, target, seg))
    except Exception:
        pass  # 记流水失败不该拦住说话


# ---------------------------------------------------------------- 口令

def 扫句号(text):
    """发之前机械扫一遍：QQ 里不许有句号。

    她说过五次的事。靠记着必漏，中文默认就是句号收尾，
    所以做成一次检查，别靠记性。
    """
    bad = [m.start() for m in re.finditer(r"[。．.]", str(text or ""))]
    return bad


def guard_no_period(text):
    """发现有句号就返回 None（调用方决定发不发），干净就返回原文。"""
    if 扫句号(text):
        return None
    return text


def main_guard(fn):
    """脚本入口包一层：异常打成一句人话 + 非零退出码。"""
    try:
        return fn()
    except SystemExit:
        raise
    except Exception as e:
        print(json.dumps({"ok": False, "错": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 1
