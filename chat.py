#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat.py —— 和 agent 对话

你输入一句话，它去做。它做的每一步都显示出来，最后把它说的话原样给你。
没有旁白，没有总结，没有"下面让我们看看"。

    python chat.py

整个文件夹可以原样拷到别的 Windows 机器上跑：node / Git Bash / Python
都放在 runtime\\ 里，provider 配置由本文件按 key.txt 生成在 .pi-agent\\。

────────────────────────────────────────────────────────────
来源：本项目修改自 Pi（https://github.com/earendil-works/pi，MIT 协议）。
      本文件不改 Pi 源码，只调用它的 CLI（--mode json 事件流）。
      开发过程中有 DeepSeek 参与辅助，详见 NOTICE.md。
────────────────────────────────────────────────────────────
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(HERE, "stage")
CLI = os.path.join(HERE, "node_modules", "@earendil-works", "pi-coding-agent",
                   "dist", "bundle", "cli.js")

# 随包携带的运行时。有这个文件夹就不用管目标机装没装 node / Git / Python。
RUNTIME = os.path.join(HERE, "runtime")

# Pi 的配置目录（models.json / settings.json / 会话记录）。
# 放在包内，整套东西自给自足，不碰目标机的 ~/.pi。
AGENT_DIR = os.path.join(HERE, ".pi-agent")

TOOL = {"bash": "执行", "read": "读", "write": "写", "edit": "改"}


def find_node():
    """node 不一定在系统 PATH 里，自己找一遍。

    顺序：包内 runtime\\node 优先，其次系统 PATH，最后各种常见安装位置。
    包内自带的那份能保证换台机器照样跑。
    """
    for cand in (os.path.join(RUNTIME, "node", "node.exe"),
                 os.path.join(RUNTIME, "node.exe")):
        if os.path.isfile(cand):
            return cand
    p = shutil.which("node")
    if p:
        return p
    pats = [
        os.path.expanduser(r"~\.workbuddy\binaries\node\versions\*\node.exe"),
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.expanduser(r"~\AppData\Roaming\nvm\v*\node.exe"),
        os.path.expanduser(r"~\scoop\apps\nodejs\current\node.exe"),
    ]
    for pat in pats:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


NODE = find_node()


def is_wsl_bash(path):
    """Windows 自带的 System32\\bash.exe 只是 WSL 的启动器，不是 Git Bash。

    WSL 没装好的机器上它会直接甩一句
    "execvpe(/bin/bash) failed: No such file or directory"，
    Pi 又把它当成"找不到 shell"，于是每条命令都失败。
    """
    if not path:
        return True
    p = os.path.normpath(path).lower()
    root = os.environ.get("SystemRoot", r"C:\Windows").lower()
    if p in (os.path.join(root, "system32", "bash.exe"),
             os.path.join(root, "sysnative", "bash.exe")):
        return True
    return p.endswith(os.path.join("microsoft", "windowsapps", "bash.exe"))


def bash_works(path):
    """光看文件存在不算数，真跑一句才知道能不能用。"""
    try:
        r = subprocess.run([path, "-c", "echo __BASH_OK__"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=20, text=True, encoding="utf-8", errors="replace")
        return r.returncode == 0 and "__BASH_OK__" in (r.stdout or "")
    except Exception:
        return False


def find_bash():
    """找一台真能用的 bash。

    包内 runtime\\git 优先。PATH 里第一个 bash.exe 很可能是 WSL 启动器
    （这台机器的 WSL 走不通），所以不能见到就返回，得挑出 Git Bash 并实跑一句验证。
    """
    cands = [
        os.path.join(RUNTIME, "git", "bin", "bash.exe"),
        os.path.join(RUNTIME, "git", "usr", "bin", "bash.exe"),
        os.path.join(RUNTIME, "bash.exe"),
    ]
    p = shutil.which("bash")
    if p:
        cands.append(p)
    for pat in [
        os.path.expanduser(r"~\.workbuddy\binaries\PortableGit\versions\*\bin\bash.exe"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        os.path.expanduser(r"~\scoop\apps\git\current\bin\bash.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Git\bin\bash.exe"),
    ]:
        cands.extend(sorted(glob.glob(pat), reverse=True))
    seen = set()
    for c in cands:
        if not os.path.isfile(c):
            continue
        k = os.path.normcase(os.path.abspath(c))
        if k in seen or is_wsl_bash(c):
            continue
        seen.add(k)
        if bash_works(c):
            return os.path.abspath(c)
    return None


BASH = find_bash()


def load_cfg():
    """读 key.txt：

        provider=apigoto
        model=deepseek-flash
        key=sk-...
        thinking=minimal
        base_url=https://api.apigoto.com/v1

    只有 key= 是必需的，其余留空就用默认值。
    """
    cfg = {"provider": "", "model": "", "key": "", "thinking": "", "base_url": ""}
    p = os.path.join(HERE, "key.txt")
    if not os.path.exists(p):
        return cfg
    # 记事本可能存成 UTF-8（带不带 BOM 都有），也可能存成 GBK。
    # 直接 utf-8 读 GBK 文件会抛 UnicodeDecodeError，整个程序闪退，
    # 所以先按 utf-8-sig 试，失败再退到 GBK。
    text = None
    for enc in ("utf-8-sig", "gbk"):
        try:
            with open(p, encoding=enc) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return cfg
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip().lower()
        if k in cfg:
            cfg[k] = v.strip()
    return cfg


def ensure_agent_dir(cfg, bash):
    """在包内建一个 Pi 的配置目录，顺便写好 models.json 和 settings.json。

    这一步是"换台机器也能跑"的关键：Pi 认 provider 全靠 models.json，
    而 apigoto 这类自定义 provider 不在它的内置列表里。没有这个文件，
    换台机器一启动就是 Unknown provider。
    """
    os.makedirs(AGENT_DIR, exist_ok=True)

    provider = (cfg["provider"] or "apigoto").strip()
    model = (cfg["model"] or "deepseek-flash").strip()
    envname = re.sub(r"[^A-Z0-9]", "_", provider.upper()) + "_API_KEY"

    models = {
        "providers": {
            provider: {
                "baseUrl": (cfg.get("base_url") or "https://api.apigoto.com/v1").strip(),
                "api": "openai-completions",
                "apiKey": "$" + envname,
                "models": [{"id": model, "name": model}],
            }
        }
    }
    mp = os.path.join(AGENT_DIR, "models.json")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)

    # Pi 只会去 PATH 里找第一个 bash.exe，而 Windows 自带的那个是 WSL 启动器。
    # shellPath 优先级最高，直接写死成本机真正能跑的那一个。
    sp = os.path.join(AGENT_DIR, "settings.json")
    data = {}
    if os.path.exists(sp):
        try:
            with open(sp, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    if bash:
        data["shellPath"] = bash
    with open(sp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def bash_dirs(bash):
    """bash 旁边那些 coreutils 也得进 PATH，否则 find/wc 全找不到。"""
    if not bash:
        return []
    d = os.path.dirname(os.path.abspath(bash))
    out = [d]
    gitroot = os.path.dirname(os.path.dirname(d))       # ...\git\bin -> ...\git
    usrbin = os.path.join(gitroot, "usr", "bin")
    if os.path.isdir(usrbin) and os.path.normcase(usrbin) != os.path.normcase(d):
        out.append(usrbin)
    return out


def brief(name, args):
    if name == "bash":
        cmd = (args.get("command") or "").replace("\n", " ")
        cmd = re.sub(r"^\s*cd\s+\S+\s*&&\s*", "", cmd)      # 去掉冗长的 cd 前缀
        cmd = re.sub(r"^cd\s+\S+\s+", "", cmd)
        return cmd
    return args.get("path") or ""


def text_of(res):
    try:
        sc = res.get("structuredContent")
        if isinstance(sc, dict) and isinstance(sc.get("output"), str):
            return sc["output"]
        if isinstance(sc, str):
            return sc
        parts = res.get("content") or []
        if isinstance(parts, list):
            return "".join(c.get("text", "") for c in parts if isinstance(c, dict))
    except Exception:
        pass
    return ""


def ask_debug(prompt, cfg, sid):
    """调试模式：把思考过程、工具调用、工具返回原样摊开。

    和 ask_quiet() 走同一条命令，只是把中间事件全都打出来。
    最终回答仍然返回，由 main() 统一打印。
    """
    provider = (cfg["provider"] or "apigoto").strip()
    model = (cfg["model"] or "deepseek-flash").strip()
    cmd = [NODE, CLI, "-p", "--mode", "json", "--session-id", sid,
           "--provider", provider, "--model", model]
    # 调试模式下强制打开思考：平时可以是 off，但要演示"它在想什么"就必须有思考块
    thinking = (cfg.get("thinking") or "").strip()
    if not thinking or thinking.lower() == "off":
        thinking = "medium"
    cmd += ["--thinking", thinking]
    cmd.append(prompt)

    env = dict(os.environ, NO_COLOR="1", FORCE_COLOR="0")
    env["PI_CODING_AGENT_DIR"] = AGENT_DIR
    env["PI_SKIP_VERSION_CHECK"] = "1"
    env[re.sub(r"[^A-Z0-9]", "_", provider.upper()) + "_API_KEY"] = cfg["key"]
    if BASH:
        dirs = bash_dirs(BASH)
        env["PATH"] = os.pathsep.join(dirs + [env.get("PATH", "")])
        env["SHELL"] = BASH
    try:
        p = subprocess.Popen(cmd, cwd=STAGE, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", bufsize=1)
    except (FileNotFoundError, OSError) as e:
        print(f"  [!] 起不来：{e}")
        return ""

    answer = ""
    thinking = False          # 当前是否在思考块里
    texts = False             # 当前是否在正文块里
    n_tool = 0

    # 逐行读 stdout。子进程异常退出时迭代器会自然结束，不会抛错。
    for raw in p.stdout:
        raw = raw.strip()
        if not raw.startswith("{"):
            continue
        try:
            ev = json.loads(raw)
        except Exception:
            continue
        kind = ev.get("type")

        # ── 流式内容：思考 / 正文 ──────────────────────────
        if kind == "message_update":
            ame = ev.get("assistantMessageEvent") or {}
            t = ame.get("type")
            if t == "thinking_start":
                print("\n  ┌─ 思考 " + "─" * 52)
                print("  │ ", end="", flush=True)
                thinking = True
            elif t == "thinking_delta" and thinking:
                # delta 是碎片，直接续着打，不要每片都加前缀
                print(str(ame.get("delta", "")).replace("\n", "\n  │ "),
                      end="", flush=True)
            elif t == "thinking_end":
                if thinking:
                    print()
                    print("  └" + "─" * 58)
                    thinking = False
            elif t == "text_delta":
                if not texts:
                    print("\n  ┌─ 回复 " + "─" * 52)
                    print("  │ ", end="", flush=True)
                    texts = True
                print(str(ame.get("delta", "")).replace("\n", "\n  │ "),
                      end="", flush=True)

        # ── 工具调用 ──────────────────────────────────────
        elif kind == "tool_execution_start":
            if texts:
                print()
                print("  └" + "─" * 58)
                texts = False
            n_tool += 1
            name = ev.get("toolName", "")
            args = ev.get("args", {}) or {}
            print(f"\n  ▸ [{n_tool}] 调用 {TOOL.get(name, name)} ({name})")
            if name == "bash":
                print("  │ $ " + str(args.get("command", "")).replace("\n", "\n  │   "))
            else:
                for k, v in args.items():
                    v = str(v).replace("\n", "\n  │     ")
                    print(f"  │ {k}: {v[:800]}")

        elif kind == "tool_execution_end":
            out = text_of(ev.get("result", {}))
            dur = ev.get("durationMs")
            bad = ev.get("isError")
            flag = "失败" if bad else "完成"
            if dur is not None:
                flag += f" · {dur} ms"
            print(f"  ◂ [{n_tool}] {flag}")
            lines = out.splitlines()
            for line in lines[:24]:
                print("  │ " + line[:160])
            if len(lines) > 24:
                print(f"  │ …（还有 {len(lines) - 24} 行，已省略）")

        # ── 最终回答 ──────────────────────────────────────
        elif kind == "message_end":
            msg = ev.get("message", {})
            if msg.get("role") != "assistant":
                continue
            c = msg.get("content")
            if isinstance(c, list):
                c = "".join(x.get("text", "") for x in c
                            if isinstance(x, dict) and x.get("type") == "text")
            if (c or "").strip():
                answer = c

    if texts:
        print()
        print("  └" + "─" * 58)
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print("\n  [!] agent 进程没有按时退出，强制结束本次任务。")
        p.kill()
        p.wait()
    print(f"\n  ── 本轮共 {n_tool} 次工具调用 ──")
    return answer


def ask_quiet(prompt, cfg, sid):
    """普通模式：只显示工具执行，不显示思考内容。"""
    provider = (cfg["provider"] or "apigoto").strip()
    model = (cfg["model"] or "deepseek-flash").strip()
    cmd = [NODE, CLI, "-p", "--mode", "json", "--session-id", sid,
           "--provider", provider, "--model", model]
    thinking = (cfg.get("thinking") or "").strip()
    if thinking and thinking.lower() != "off":
        cmd += ["--thinking", thinking]
    cmd.append(prompt)

    env = dict(os.environ, NO_COLOR="1", FORCE_COLOR="0")
    env["PI_CODING_AGENT_DIR"] = AGENT_DIR
    env["PI_SKIP_VERSION_CHECK"] = "1"
    env[re.sub(r"[^A-Z0-9]", "_", provider.upper()) + "_API_KEY"] = cfg["key"]
    if BASH:
        dirs = bash_dirs(BASH)
        env["PATH"] = os.pathsep.join(dirs + [env.get("PATH", "")])
        env["SHELL"] = BASH
    try:
        p = subprocess.Popen(cmd, cwd=STAGE, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace", bufsize=1)
    except (FileNotFoundError, OSError) as e:
        print(f"  [!] 起不来：{e}")
        print(f"      node = {NODE}")
        return ""
    answer = ""
    # 逐行读 stdout。子进程异常退出时迭代器会自然结束，不会抛错。
    for raw in p.stdout:
        raw = raw.strip()
        if not raw.startswith("{"):
            continue
        try:
            ev = json.loads(raw)
        except Exception:
            continue
        kind = ev.get("type")
        if kind == "tool_execution_start":
            name = ev.get("toolName", "")
            print(f"\n  ▸ {TOOL.get(name, name)} {brief(name, ev.get('args', {}))[:64]}")
        elif kind == "tool_execution_end":
            lines = [x.strip() for x in text_of(ev.get("result", {})).splitlines() if x.strip()]
            if lines:
                print(f"    {lines[0][:76]}")
        elif kind == "message_end":
            msg = ev.get("message", {})
            if msg.get("role") != "assistant":
                continue
            c = msg.get("content")
            if isinstance(c, list):
                c = "".join(x.get("text", "") for x in c if isinstance(x, dict))
            if (c or "").strip():
                answer = c
    p.wait()
    return answer


def choose_mode():
    """启动前问一句：要不要进调试模式。

    直接回车或者 EOF（比如管道喂进来的）都当"否"，不会卡住演示。
    """
    print("要进入调试模式吗？")
    print("  是 —— 显示模型的思考过程、每一次工具调用和完整命令")
    print("  否 —— 只看它做了什么，最后给结论")
    try:
        ans = input("输入 Y 进入调试模式，直接回车跳过：").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return ans in ("y", "yes", "是")


def main():
    try:
        return _main()
    except KeyboardInterrupt:
        print("\n\n已中断。")
        return 130
    except Exception as e:
        # 真出了没预料到的错，也不能让窗口一闪就关——把现场留给人看。
        print("\n[!] 程序出错了，但没有直接闪退：")
        print(f"    {type(e).__name__}: {e}")
        print("    把上面这段发给开发者，或者对照 README 的常见问题排查。")
        return 1


def _main():
    if not NODE:
        print("找不到 node.exe。装一个 Node.js，或者把它的目录加到 PATH 里。")
        return 1
    if not BASH:
        print("找不到 bash.exe。装一个 Git for Windows 就行。")
        return 1
    if not os.path.isfile(CLI):
        print(f"找不到 Pi 的 CLI：{CLI}")
        print("先在项目目录里执行一次 npm install。")
        return 1
    cfg = load_cfg()
    if not cfg["key"]:
        print("key.txt 里没有 key。把同目录的「APIKEY配置教程.txt」改名成 key.txt，")
        print("在 key= 后面填上你自己的 API key，保存后重新运行。")
        return 1
    try:
        ensure_agent_dir(cfg, BASH)
    except OSError as e:
        print(f"写配置失败（磁盘满？目录只读？）：{e}")
        return 1

    debug = choose_mode()
    print()
    print("和 agent 对话。输入 quit 退出。")
    print(f"  provider = {cfg['provider'] or 'apigoto'}   model = {cfg['model'] or 'deepseek-flash'}")
    print(f"  模式 = {'调试（显示思考与全部工具细节）' if debug else '普通（只看动作和结论）'}\n")

    sid = f"demo{int(time.time())}"          # 每次启动都是全新对话
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in ("quit", "exit", "q"):
            break
        print()
        try:
            ans = ask_debug(q, cfg, sid) if debug else ask_quiet(q, cfg, sid)
        except Exception as e:
            print(f"\n  [!] 这一轮出错了：{type(e).__name__}: {e}")
            print("  可以继续输入下一句，或输入 quit 退出。")
            ans = ""
        if ans:
            print("\n" + ans.strip() + "\n")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
