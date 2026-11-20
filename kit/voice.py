#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""发语音条：克隆音色 TTS -> 音频 -> OneBot 发 QQ。

    python voice.py --text "要说的话" --private 12345678
    python voice.py --text "要说的话" --group 87654321
    python voice.py --text "要说的话" --save out.wav      # 只合成不发送
    python voice.py --file 一段话.txt --private 12345678

为什么要固定一条链路：换一次音色，听的那个人当场就听出来了
（「你声音怎么变成这样了」）。所以参考音频、模型、接口都写死在配置里，
不许临时换通用的 TTS 顶上。

配置（kit/config.json 的 voice / paths 两段）：
  paths.voice_ref   参考音频 wav，越长越稳，10-30 秒够
  voice.api_key     小米 MiMo 的 key
  voice.endpoint    默认 https://api.xiaomimimo.com/v1
  voice.model       默认 mimo-v2.5-tts-voiceclone
  voice.format      wav / mp3
"""

import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

import fishlib


def sample_data_url(path):
    with open(path, "rb") as f:
        raw = f.read()
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {"mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4"}.get(ext, "audio/wav")
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())


def synth(text, vcfg, sample, retries=6, style=None, context=None):
    """合成一段语音。

    style   整体风格标签，写「温柔」就会在开头加 (温柔)
    context 自然语言指令，单独占一条 user 消息（官方示例就在这个位置）
    两个都不传时，请求体和最朴素的版本完全一致。
    """
    if style:
        s = str(style).strip().strip("()（）[]")
        if s:
            text = "(%s)%s" % (s, text)

    messages = []
    if context:
        messages.append({"role": "user", "content": str(context)})
    messages.append({"role": "assistant", "content": text})

    body = {
        "model": vcfg.get("model", "mimo-v2.5-tts-voiceclone"),
        "audio": {
            "format": vcfg.get("format", "wav"),
            "voice": sample_data_url(sample),
        },
        "messages": messages,
    }
    data = json.dumps(body).encode("utf-8")
    url = str(vcfg.get("endpoint") or "https://api.xiaomimimo.com/v1").rstrip("/") + "/chat/completions"

    last = None
    for i in range(retries):
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("api-key", vcfg["api_key"])
        req.add_header("Content-Type", "application/json")
        try:
            raw = urllib.request.urlopen(req, timeout=300).read()
            d = json.loads(raw)
            audio = (d["choices"][0]["message"].get("audio") or {})
            b64 = audio.get("data")
            if not b64:
                raise RuntimeError("响应里没有 audio.data：%s" % raw[:300])
            return base64.b64decode(b64), audio.get("transcript")
        except urllib.error.HTTPError as e:
            last = "HTTP %s %s" % (e.code, e.read().decode("utf-8", "replace")[:300])
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(6 * (i + 1), 40))   # 限流就退避，别硬撞
                continue
            raise RuntimeError(last)
        except urllib.error.URLError as e:
            last = "网络错误 %s" % e
            time.sleep(5 * (i + 1))
    raise RuntimeError(last)


def send_voice(audio_bytes, group=None, private=None):
    b64 = base64.b64encode(audio_bytes).decode()
    msg = [{"type": "record", "data": {"file": "base64://" + b64}}]
    if group:
        return fishlib.onebot("send_group_msg", {"group_id": int(group), "message": msg}, timeout=90)
    if private:
        return fishlib.onebot("send_private_msg", {"user_id": int(private), "message": msg}, timeout=90)
    raise ValueError("要么给 --group，要么给 --private")


def main():
    ap = argparse.ArgumentParser(description="发语音条（克隆音色）")
    ap.add_argument("--text")
    ap.add_argument("--file", help="从文本文件读要念的内容")
    ap.add_argument("--group", type=int)
    ap.add_argument("--private", type=int)
    ap.add_argument("--save", help="只合成，存到这个路径，不发送")
    ap.add_argument("--also-text", action="store_true", help="语音之外，把文字也发一遍")
    ap.add_argument("--style", help="整体风格标签，如 温柔 / 慵懒 / 委屈 / 俏皮")
    ap.add_argument("--context", help="自然语言指令，如 用刚睡醒的语气慢慢说")
    args = ap.parse_args()

    vcfg = fishlib.cfg().get("voice") or {}
    if not vcfg.get("api_key"):
        print(json.dumps({"ok": False, "error": "config.json 里 voice.api_key 还没填"}, ensure_ascii=False))
        return 2

    sample = fishlib.path_of("voice_ref")
    if not sample or not os.path.isfile(sample):
        print(json.dumps({"ok": False, "error": "参考音频没找到（paths.voice_ref）"}, ensure_ascii=False))
        return 2

    text = args.text
    if not text and args.file:
        text = io.open(args.file, encoding="utf-8").read().strip()
    if not text:
        text = sys.stdin.read().strip()
    if not text:
        print(json.dumps({"ok": False, "error": "没有要念的文本"}, ensure_ascii=False))
        return 2

    out = {"ok": True, "text": text}
    try:
        audio, transcript = synth(text, vcfg, sample, style=args.style, context=args.context)
        out["bytes"] = len(audio)
        if transcript:
            out["transcript"] = transcript

        if args.save:
            with open(args.save, "wb") as f:
                f.write(audio)
            out["saved"] = os.path.abspath(args.save)
        else:
            ext = vcfg.get("format", "wav")
            path = os.path.join(os.environ.get("TEMP", "."), "fish-voice-%d.%s" % (int(time.time()), ext))
            with open(path, "wb") as f:
                f.write(audio)
            out["temp"] = path

            ok, resp = send_voice(audio, args.group, args.private)
            out["sent"] = resp
            if not ok:
                out["ok"] = False
                out["error"] = "语音合成好了，但 QQ 那边没发出去（看 sent 里的 retcode）"

            if args.also_text:
                txt = [{"type": "text", "data": {"text": text}}]
                if args.group:
                    out["sent_text"] = fishlib.onebot(
                        "send_group_msg", {"group_id": args.group, "message": txt})[1]
                else:
                    out["sent_text"] = fishlib.onebot(
                        "send_private_msg", {"user_id": args.private, "message": txt})[1]
    except Exception as e:
        out = {"ok": False, "error": str(e), "text": text}

    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    sys.exit(fishlib.main_guard(main))
