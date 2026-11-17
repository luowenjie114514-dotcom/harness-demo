# Harness 驱动的 Agent：设计实现与能力提升

> **《人工智能通识》课程综合设计 · 算法实践类 · 小组作业**
>
> 同一个模型权重，只换外面那层壳，它能做的事从"给你建议"变成"把活干完"。
> 本项目把这个"壳"（harness）拆开、实现出来，并做对比验证。

一个用来演示 **Agent = Model + Harness** 的最小装置。

同一句"帮我把这个文件夹整理一下"，走网页对话框只能得到一段建议，走这里能真的把文件搬完。区别不在模型，在模型外面那层壳。

技术上它是：**一个 Python 对话外壳 + 一个真实的开源 agent（Pi）+ 一个隔离的待整理区**。

---

## 来源与说明

**本项目修改自 [Pi](https://github.com/earendil-works/pi)**（`@earendil-works/pi-coding-agent`，MIT 协议）。

原项目的 agent 循环、工具系统、事件流都由 Pi 提供；本项目在它外面加了一层中文对话外壳、调试模式、可移植运行时打包和演示数据。

**开发过程中使用了 DeepSeek 参与开发**：代码实现、排错（WSL bash 误用、Git Bash shim 问题、provider 配置生成）、文档撰写均有 AI 辅助。具体做了哪些事，见下节。

> 谢绝把 AI 的产出当成自己的独立成果。这一节就是写清楚边界。

### 我们实际做了什么

| 工作 | 说明 |
|---|---|
| `chat.py` 对话外壳 | 340 行 → 450 行，驱动 Pi 的 `--mode json` 事件流，翻译成人能看的输出 |
| 调试模式 | 新增。启动时 Y/N 选择，把思考过程、工具调用、完整命令和返回内容全部摊开 |
| shell 解析修复 | 原版 `shutil.which("bash")` 会选中 WSL 启动器，导致每条命令都失败。改成候选收集 + 剔除 WSL + 实跑验证 |
| provider 配置生成 | 按 `key.txt` 动态生成 `.pi-agent/models.json`，解决换机器就报 `Unknown provider` 的问题 |
| 可移植打包 | 把 node / Git Bash / Python 塞进 `runtime/`，286 MB 整套拷走即用，目标机不需要装任何东西 |
| 演示数据 | `make_mess.py` 生成 45 个文件，内含假 PDF、0 字节残留、同名冲突等刻意的坑 |
| 行为约束 | `stage/AGENTS.md` 五条规矩，让 agent 不删文件、不覆盖、前后数数、看内容不看后缀 |
| 文档 | 演示稿指导、素材指导、原理图规格、本 README |

### 上游依赖

- **Pi** — https://github.com/earendil-works/pi ，MIT License
- 本仓库不修改 Pi 的源码，只调用它的 CLI

---

## 本仓库包含什么

| 类型 | 文件 |
|---|---|
| 核心实现 | `chat.py`（对话外壳与调试模式）、`make_mess.py`、`clear.py`、`folder_agent.py`（12 行 harness 内核） |
| 启动脚本 | `1_make.cmd`、`2_clear.cmd`、`3_chat.cmd` |
| Agent 规矩 | `stage/AGENTS.md`（五条行为约束） |
| 文档 | `README.md`、`HTML演示稿指导.md`、`素材指导.md`、`原理图规格.md` |
| 演示页 | `slides.html` |

**不包含**（`.gitignore` 已排除，需自行准备）：

- `key.txt` —— API 凭证，用 `APIKEY配置教程.txt` 改名后填自己的 key
- `runtime/` —— 内置的 node / Git Bash / Python（172 MB）
- `node_modules/` —— Pi 及其依赖（110 MB）
- `stage/workspace/` —— 演示用乱文件，双击 `1_make.cmd` 可重新生成

> 完整可运行包（含运行时，286 MB）请向组内索取，不要直接塞进 Git 仓库。

---

## 三十秒上手

```
第 1 步  填 key        打开 key.txt，在 key= 后面填上你的 API key，保存
第 2 步  双击 1_make.cmd   铺 45 个乱文件到待整理区
第 3 步  双击 3_chat.cmd   出现 > 提示符，输入：这个文件夹有点乱，根据用途分类
```

然后看着它一条条执行、最后给你报告。输入 `quit` 退出。

**不需要装任何东西。** node、Git Bash、Python 都在 `runtime/` 里带着，整个文件夹拷到任何 Windows 机器上都能跑（见 [换一台电脑用](#换一台电脑用)）。

---

## 使用说明

### 三个脚本分别干什么

| 双击 | 作用 | 副作用 |
|---|---|---|
| `1_make.cmd` | 在 `stage/workspace/` 里铺 45 个文件 + 2 个子目录，约 0.5 秒 | **会先清空**待整理区再重建 |
| `2_clear.cmd` | 清空待整理区，问你 `y/N` | 只删 `stage/workspace/` 里面的东西，别处不动 |
| `3_chat.cmd` | 进入对话，等你的指令 | 只读写 `stage/workspace/`（Pi 的工作目录是 `stage/`） |

一般流程就是 **1 → 3 → 用完 2 清场 → 下次再 1**。

### 调试模式

双击 `3_chat.cmd` 后，程序先问一句：

```
要进入调试模式吗？
  是 —— 显示模型的思考过程、每一次工具调用和完整命令
  否 —— 只看它做了什么，最后给结论
输入 Y 进入调试模式，直接回车跳过：
```

**输入 `Y` 进调试模式**，会看到：

```
  ┌─ 思考 ──────────────────────────────────────────
  │ 用户要统计文件数。先看看 workspace 里有什么。
  └────────────────────────────────────────────────

  ▸ [1] 调用 执行 (bash)
  │ $ find workspace -type f | wc -l
  ◂ [1] 完成 · 878 ms
  │ 45

  ┌─ 回复 ──────────────────────────────────────────
  │ 45
  └────────────────────────────────────────────────
  ── 本轮共 1 次工具调用 ──
```

调试模式强制打开 `thinking`，演示"它在想什么"时用这个。
**直接回车**进普通模式，只显示工具动作和最终结论，适合正式展示。

### 界面怎么读（普通模式）

```
> 这个文件夹有点乱，根据用途分类

  ▸ 执行 find . -type f | wc -l && mkdir -p 图片 课程资料
    45

  ▸ 执行 head -c 4 发票2024.pdf | xxd
    00000000: 8950 4e47                                .PNG

整理完成。移动 40 个，45 → 45 对得上……
```

- **`▸ 执行 …`** —— agent 要调工具了，后面是它实际执行的命令（`cd` 前缀被我省掉了，因为每轮都在 `stage/` 里）
- **缩进那一行** —— 工具返回的第一行，用来确认它真的跑成功了
- **没有箭头的一大段** —— agent 最后说的话，原样给你，不加旁白

一次任务通常会调十几次工具，中间那些光标闪动就是它在想。

### 可以直接下的指令

`stage/AGENTS.md` 只规定了五条**行为规矩**（不许删、不许覆盖、前后数数、看内容不看后缀、最后报告），具体做什么完全由你现说。

已验证能跑通的：

| 指令 | 实际发生的事 |
|---|---|
| `这个文件夹有点乱，根据用途分类` | 移 40~43 个，建 8~11 个目录，揪出后缀造假的文件 |
| `按科目分类，分不清的放"待确认"` | 按课程归类，模糊的单独隔离 |
| `给所有 pdf 的文件名加上最后修改日期前缀` | 改成 `20261113_xxx.pdf`，**拒改**那个假 pdf |
| `找出重复的文件` | 用 `md5sum` 比对，报出同哈希的组 |
| `统计一下有几个文件、总共多大` | 只读不写 |

想加新任务不用改代码，直接说就行。

### 退出与重置

- 输入 `quit` / `exit` / `q` 退出，或按 `Ctrl+C`
- 每次启动都是**全新对话**（session id 带时间戳），不会记得上一轮说过什么
- 想恢复干净环境：`2_clear.cmd` 清空 → `1_make.cmd` 重建

### 填 key

打开 `key.txt`（记事本就行），是这样的：

```
# 把下面的 key 换成你自己的，然后保存。这个文件不要发给别人。
provider=apigoto
model=deepseek-flash
key=
thinking=minimal
base_url=https://api.apigoto.com/v1
```

在 `key=` 后面填上你的 key 就完事。五个字段的含义见 [换 provider 和 key](#换-provider-和-key)。

---

## 目录结构

```
harness-demo/
├── 1_make.cmd          双击：铺 45 个乱文件到待整理区
├── 2_clear.cmd         双击：清空待整理区（问 y/N）
├── 3_chat.cmd          双击：进入对话
├── chat.py             对话外壳（核心，见下）
├── make_mess.py        生成演示数据
├── clear.py            清空待整理区
├── folder_agent.py     另写的 12 行 harness，用来"拆开看内核"（可选）
├── key.txt             API 凭证（key= 填你自己的）
├── APIKEY配置教程.txt  改名成 key.txt 后使用，字段说明都在里面
├── runtime/            ← 随包携带的运行时（172MB）
│   ├── node/node.exe           83MB
│   ├── git/usr/bin/bash.exe    68MB，裁剪版 Git Bash
│   └── python/python.exe       21MB，embeddable 版
├── .pi-agent/          ← Pi 的配置目录，chat.py 自动生成
│   ├── models.json     ← provider 定义（apigoto 就在这里）
│   ├── settings.json   ← shellPath，指向包内这台 bash
│   └── sessions/       每次对话的记录
├── stage/              ← Pi 的工作目录
│   ├── AGENTS.md       ← Pi 每轮自动读的规矩，共 5 条
│   └── workspace/      ← 待整理区，所有操作都在这里面
├── node_modules/       Pi 及其依赖（110MB）
├── package.json
└── README.md
```

整个文件夹 286 MB。`runtime/` 和 `.pi-agent/` 都是**可以随时删的派生目录**：删了 `runtime/` 就退回用系统装的 node/git/python，删了 `.pi-agent/` 下次启动会重新生成。

---

## 换一台电脑用

### 最省事的方式

用 `harness-demo-portable.zip`（106 MB）。解压出来是一个 `harness-demo/` 文件夹，进去填好 `key.txt`，双击 `3_chat.cmd`。

目标机 **不需要装 node / Git / Python**，`runtime/` 里都带着。

### 或者整个文件夹直接拷

一样能跑。注意事项：

- 拷到 U 盘/网盘时确认 `runtime/node/node.exe`（83 MB）没被同步工具跳过
- 路径里**可以有中文和空格**，脚本都用 `%~dp0` 自己定位
- 路径**不要超过 240 个字符**，Windows 老 API 有长度限制，node_modules 里有些深层路径比较长

### 换 provider 和 key

只改 `key.txt` 这五行，重新双击 `3_chat.cmd` 就生效：

```
provider=apigoto
model=deepseek-flash
key=sk-你的key
thinking=minimal
base_url=https://api.apigoto.com/v1
```

| 字段 | 说明 |
|---|---|
| `provider` | 供应商名字，自己起也行。改了它，`base_url` 必须一起改 |
| `model` | 模型 id，写供应商文档里那个名字 |
| `key` | API key，**唯一必填项** |
| `thinking` | `off` / `minimal` / `low` / `medium` / `high` / `xhigh` / `max`；留空或 `off` 就不带这个参数 |
| `base_url` | OpenAI 兼容接口地址，一般以 `/v1` 结尾 |

`chat.py` 会按这几行**重新生成** `.pi-agent/models.json`，所以你不用手改 Pi 的配置文件，也不用担心换机器后 provider 找不到。

换一家的例子：

```
provider=myprov
model=some-model
key=sk-xxxx
thinking=
base_url=https://api.example.com/v1
```

只要对方是 OpenAI 兼容协议（`POST /chat/completions`），这样就能直接用。内置的 `deepseek` / `openai` / `anthropic` 等也可以写进 `provider=`，但那样需要它们各自的官方 key。

### 分发给别人之前

1. 清空 `key.txt` 的 `key=` 那一行，或直接删掉这个文件（`APIKEY配置教程.txt` 留着就够了）
2. 想减小体积可以删 `stage/workspace/` 里的东西，反正 `1_make.cmd` 会重建
3. `.gitignore` 已经排除了 `key.txt`、`runtime/`、`.pi-agent/`、`node_modules/`

---

## chat.py 干了什么

不是自己实现 agent，而是**驱动 Pi**，把它的执行过程翻译成人能看的样子。

```
用户输入
  → Popen(node, cli.js, -p, --mode json, --session-id, prompt)
  → 逐行读 stdout（每行一个 JSON 事件）
  → tool_execution_start  → 打印 "▸ 执行 <命令>"
  → tool_execution_end    → 打印结果第一行
  → message_end(assistant)→ 记下最终回答
  → 进程退出后打印回答
```

启动时它会做三件准备工作：

1. 找 node —— 先看 `runtime\node\node.exe`，再退回系统 PATH
2. 找 bash —— 先看 `runtime\git\usr\bin\bash.exe`，再退回 PATH 和各种安装位置，**每一个都要实跑 `echo __BASH_OK__` 验证**
3. 生成 `.pi-agent/{models.json,settings.json}` —— 把 `key.txt` 的 provider 写成 provider 定义，把找到的 bash 写进 `shellPath`

每次对话都带 `PI_CODING_AGENT_DIR=<包内 .pi-agent>`，所以不碰目标机原来的 `~/.pi`。

### Pi 的事件类型

`--mode json` 输出 NDJSON，一行一个事件：

| type | 含义 |
|---|---|
| `session` | 会话开始，带 cwd |
| `agent_start` / `agent_end` | 整轮开始/结束 |
| `turn_start` / `turn_end` | 单次"想-做"循环 |
| `message_start` / `message_update` / `message_end` | 消息流式更新 |
| `tool_execution_start` | 要调工具，含 `toolName` 和 `args` |
| `tool_execution_end` | 工具返回，含 `result.structuredContent.output` |

`message_end` 里 `message.content` 可能是字符串，也可能是 `[{type:text,text}]` 数组，两种都要处理。

### 关键参数

```
-p                    非交互，跑完退出
--mode json           结构化事件流
--session-id <id>     同一 id 内保持上下文
--provider <名字>      来自 key.txt 的 provider=
--model <模型>         来自 key.txt 的 model=
--thinking <档位>      来自 key.txt 的 thinking=（off 或留空则不带）
--api-key <key>       也可不用，chat.py 是走环境变量传的
```

---

## 环境依赖

正常情况下**什么都不用装**，`runtime/` 里带着 node、Git Bash、Python。

万一 `runtime/` 被删了，脚本也会自己去系统里找：

| 依赖 | 查找顺序 |
|---|---|
| `node.exe` | `runtime\node\` → PATH → `~\.workbuddy\binaries\node\versions\*\` → `C:\Program Files\nodejs\` → nvm/scoop |
| `bash.exe` | `runtime\git\` → PATH → `~\.workbuddy\binaries\PortableGit\versions\*\bin\` → `C:\Program Files\Git\bin\` |
| `python.exe` | `.cmd` 里先看 `runtime\python\`，没有再退回 `python` |

`bash.exe` 找到之后还要**实跑一句 `bash -c "echo __BASH_OK__"` 验证**，跑不通的（典型就是 WSL 启动器）直接跳过换下一个。光看文件存在不算数，见坑 1。

`runtime\git` 是 PortableGit 裁剪过的版本，只留了 `usr/` 和 `etc/`（68 MB，原版 130 MB）。**不能只留 `bin/bash.exe`**——那个 47 KB 的文件其实是 `git.exe` 的 shim，删掉 `mingw64/` 之后它会报 `Top-level not found`。正确做法是用 `usr\bin\bash.exe`，并且把 `usr\bin` 放进 PATH，否则 `find` / `wc` / `md5sum` 全都找不到（`chat.py` 的 `bash_dirs()` 会自动做这件事）。

---

## 常见问题

**启动就报 `key.txt 里没有 key`**
→ 打开 `key.txt`，把 `key=` 后面填上。这行空着就会被拦下来。

**报 `找不到 node.exe` / `找不到 bash.exe`**
→ 说明 `runtime/` 被删了，系统里也没有。把 `runtime/` 恢复回来，或装 Node.js + Git for Windows。

**agent 一执行 bash 就报 `execvpe(/bin/bash) failed`**
→ 它用上了 WSL 的启动器（`C:\Windows\System32\bash.exe`）。删掉 `.pi-agent/` 让它重新生成 `settings.json`；还不行就是 `find_bash()` 没找到可用 bash，见坑 1。

**报 `Unknown provider "apigoto"`**
→ `.pi-agent/models.json` 没生成或内容不对。删掉 `.pi-agent/` 重新启动即可。

**agent 说 `file: command not found`**
→ 正常。裁剪版 Git Bash 没有 `file`，它会自己退回 `od` / `xxd` 看魔数。想第一轮就顺，可以在 `stage/AGENTS.md` 里直接提示用 `xxd`。

**中文显示成乱码**
→ 三个 `.cmd` 里都有 `chcp 65001`。如果还是乱，检查终端字体，或改用 Windows Terminal。

**每轮都很慢**
→ 慢在模型推理，不在本地。可以把 `thinking=` 设成 `off` 或 `minimal` 提速。

**杀毒软件把执行拖得很慢**
→ 把整个文件夹加进白名单，见坑 6。

**整理完想重来**
→ `2_clear.cmd` 清空，`1_make.cmd` 重建，两条命令回到初始状态。

---

## 八个坑（都踩过，别再踩）

### 1. Windows 上 Pi 会去用 WSL 的 bash

`shell.js` 的解析顺序是：`settings.json` 的 `shellPath` → `%ProgramFiles%\Git\bin\bash.exe` → **PATH 里第一个 `bash.exe`**。

这台机器 PATH 里第一个是 `C:\Windows\System32\bash.exe`，那只是 WSL 启动器，WSL 装不起来，于是每次 `bash` 调用都报 `execvpe(/bin/bash) failed`。

**修法**：`chat.py` 启动时把 Git Bash 的绝对路径写进 `.pi-agent/settings.json` 的 `shellPath`（第 1 优先级，一写就生效）。这个目录是包内的，靠 `PI_CODING_AGENT_DIR` 指过去。

**但光写还不够** —— 早先的 `find_bash()` 是 `p = shutil.which("bash"); if p: return p`，`which` 在这台机器上返回的正是 `C:\WINDOWS\system32\bash.EXE`，于是它把 WSL 启动器当成答案写进了 `shellPath`，glob 回退分支一次都没跑到。表现和"没修"一模一样，还更隐蔽：settings.json 里明明有值。

现在的顺序是：把 PATH 命中的和 glob 命中的候选**全部收集起来**，先剔除 `System32\bash.exe` / `Sysnative\bash.exe` / `WindowsApps\bash.exe` 这几个 WSL 启动器，再对剩下的逐个 `subprocess.run` 跑一句 `echo __BASH_OK__`，第一个真的跑通的才算数（`chat.py` 的 `is_wsl_bash()` 和 `bash_works()`）。被跳过的候选一律不写进 `settings.json`，找不到就明确报"找不到 bash.exe，装个 Git for Windows"，不再静默写一个坏路径。

### 2. `.cmd` 文件必须纯 ASCII

cmd.exe 按系统代码页解析批处理文件，UTF-8 存的中文会全乱，导致 `echo` 变成一堆乱码命令、`cd` 失效、脚本去 `C:\Windows\System32` 找 python 文件。

**修法**：三个 `.cmd` 里一个非 ASCII 字节都没有，中文全放在 `.py` 里。

### 3. Pi 在管道里会卡住等 stdin

不加 `< /dev/null` 或 `stdin=subprocess.DEVNULL`，`-p` 模式会一直等输入，看起来像卡死。

**修法**：`Popen(..., stdin=subprocess.DEVNULL)`。

### 4. 空 session 会让演示"记得上一轮"

如果复用固定 session id，第二次演示时 agent 会说"我上次已经整理过了"。

**修法**：`sid = f"demo{int(time.time())}"`，每次启动换一个。

### 5. `mv` 会静默覆盖同名文件

Pi 用 `mv` 移动文件时，如果目标目录已存在同名文件，**直接覆盖，不报错，原文件消失**。这个问题真实发生过一次，丢了一个 `实验报告.pdf`。

**修法**：`stage/AGENTS.md` 第 2 条明确写"用 `mv -n`，永远不要覆盖"。

### 6. 杀毒软件会让生成文件变得极慢

早期生成 187 个几十 MB 的文件要 44 秒，其中大部分时间花在实时扫描上。

**修法**：文件压到 340KB 以内，45 个文件 0.5 秒。

### 7. 换个文件夹就报 `Unknown provider`

`apigoto` 不是 Pi 的内置 provider，它只存在于 `~/.pi/agent/models.json`。原版 `chat.py` 每次都在 `ask()` 里硬编码 `--provider apigoto`，却从来没管过这个文件存不存在。于是**把这个文件夹拷到别的机器、或者换一个 Windows 用户，第一条消息就报**：

```
Error: Unknown provider "apigoto". Use --list-models to see available providers/models.
```

同时 `key.txt` 里那行 `provider=` 是死的：`load_key()` 只读 `key=`，另外两行写得再对也没人看。

**修法**：
- `chat.py` 现在用 `load_cfg()` 把 `provider` / `model` / `key` / `thinking` / `base_url` 全部读出来
- 每次启动按这几行**重新生成** `.pi-agent/models.json`，provider 名、模型 id、base_url 都跟着 `key.txt` 走
- `PI_CODING_AGENT_DIR` 指向包内 `.pi-agent`，Pi 不去碰 `~/.pi`

于是"换 provider"变成真的改一行就生效，拷到别的机器也不会因为缺 models.json 而崩。

### 8. `key.txt` 用记事本存会带 BOM

Windows 记事本存 UTF-8 默认加 BOM（`EF BB BF`）。第一行被读成 `\ufeff# 把下面的...`，虽然当前不影响 `provider=` 的解析（它在第二行），但改一下顺序就会踩。

**修法**：`load_cfg()` 用 `encoding="utf-8-sig"` 读，有没有 BOM 都能正确解析。

---

## AGENTS.md：这是整个演示的核心

`stage/AGENTS.md` 会被 Pi 自动加载进每一轮的系统提示。五条规矩：

1. 不许删除任何文件，只能移动
2. 移动前检查同名，有就停下报告，用 `mv -n`
3. 动手前后各数一遍文件总数，对不上就停
4. 后缀不等于内容，归类前先看文件本体
5. 最后报告：移了多少、现在多少、哪几个没动、为什么

**第 4 条是演示的高光**：只写了这一句，agent 就真的去逐个校验文件魔数（`%PDF` / `49 46` / `MZ` / `ftypmp42` / `ID3`），然后揪出那个后缀是 `.pdf`、内容其实是 PNG 的"发票"。

改这五条，agent 的行为会立刻变。这是最容易做对比实验的地方——把第 4 条删掉，它就会老老实实按后缀分类，把 PNG 当成 PDF 塞进"文档"。

---

## 演示数据里埋了什么

`make_mess.py` 生成 45 个文件、2 个子目录，其中四个是刻意的：

| 文件 | 埋的东西 |
|---|---|
| `发票2024.pdf` | 内容是一张合法的 1024×768 PNG，只有后缀是 pdf |
| `~$课件.docx` | 0 字节，Word 的锁文件残留 |
| `备份_旧版.bak` | 内容是 gzip 数据流，但已损坏，解不开 |
| `课程资料/实验报告.pdf` | 与根目录 `实验报告.pdf` 同名但内容不同（同大小、不同 MD5） |

另外所有 `.png` 用的是同一份字节，MD5 完全相同，agent 可能会主动指出"这 7 张图内容一致"。

---

## 已知限制

- 生成的 `.docx` / `.xlsx` / `.pptx` / `.zip` **只有 `PK` 文件头，不是有效的 ZIP**。agent 如果去解压会发现解不开，可能据此把它们放进"待确认"。要修就得用 `zipfile` 生成真实容器。
- `key.txt` 是明文凭证，**不要提交、不要外发**。仓库里那份 `key=` 是空的。
- 依赖 `api.apigoto.com` 这个中转服务。换官方 API 只需要改 `key.txt` 的三行，不用改代码。
- **Git Bash 里没有 `file` 命令**（PortableGit 的 `usr\bin` 下不含 `file.exe`）。agent 会先试 `file`、失败后自己退回 `od` / `xxd` 读魔数——实测能退回来，但第一轮会多花一两次调用。
- `runtime/git` 是裁剪版（68 MB）。`git` 命令本身用不了（删了 `mingw64/`），只有 bash + coreutils。演示够用；要真用 git 请装完整版 Git for Windows（130 MB）。
- 只在 Windows 上验证过。`chat.py` 里 `find_node` / `find_bash` 的路径都是 Windows 写法，换 macOS/Linux 要改。

---

## 想改的话

**换模型 / 换供应商**：改 `key.txt` 那五行，重新双击 `3_chat.cmd`。不用改代码，也不用动 Pi 的配置文件。

**换任务**：不用改代码，直接在对话里下别的指令。

**改规矩**：编辑 `stage/AGENTS.md`，下一轮立刻生效。

**改演示数据**：编辑 `make_mess.py`，然后 `2_clear.cmd` + `1_make.cmd` 重建。

**要看 agent 原始输出**：把 `chat.py` 的 `--mode json` 去掉，直接跑：

```
set PI_CODING_AGENT_DIR=%~dp0.pi-agent
runtime\node\node.exe node_modules\@earendil-works\pi-coding-agent\dist\bundle\cli.js --provider apigoto --model deepseek-flash "你的话"
```

**要拆开看内核**：`python folder_agent.py`，12 行 Python 复现同一套循环，不调模型，跑得很快，用来说明"harness 的本质就是工具 + 循环 + 回传 + 核对"。

**要讲这堂课**：`HTML演示稿指导.md` 教怎么做演示稿（风格选择 + 八页内容 + 技术要点），`素材指导.md` 教怎么录对比视频、怎么整理数据图表。`slides.html` 是早期做的示例页面，仅供参考。
