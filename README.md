# Harness 驱动的 Agent：设计实现与能力提升

> **《人工智能通识》课程综合设计 · 算法实践类 · 小组作业**
>
> 同一个模型权重，只换外面那层壳，它能做的事从"给你建议"变成"把活干完"。
> 本项目把这个"壳"（harness）拆开、实现出来，并做对比验证。

一个用来演示 **Agent = Model + Harness** 的最小装置。

技术上它是：**一个 Python 对话外壳 + 一个真实的开源 agent（Pi）+ 一个隔离的待整理区**。

---

## 来源与说明

**本项目修改自 [Pi](https://github.com/earendil-works/pi)**（`@earendil-works/pi-coding-agent`，MIT 协议）。

原项目的 agent 循环、工具系统、事件流都由 Pi 提供；本项目在它外面加了一层中文对话外壳、调试模式、可移植运行时打包和演示数据。

**开发过程中使用了 DeepSeek 参与开发**：代码实现、排错（WSL bash 误用、Git Bash shim 问题、provider 配置生成）、文档撰写均有 AI 辅助。具体做了哪些事，见下节。


### 工作内容

| 工作 | 说明 |
|---|---|
| `chat.py` 对话外壳 | 驱动 Pi 的 `--mode json` 事件流，翻译输出 |
| 调试模式 | 启动时 Y/N 选择，把思考过程、工具调用、完整命令和返回内容全部摊开 |
| shell 解析修复 | 原版 WSL 启动器改成候选收集  |
| provider 配置生成 | 按 `key.txt` 动态生成 `.pi-agent/models.json`，解决 `Unknown provider` 的问题 |
| 可移植打包 | 把 node / Git Bash / Python 塞进 `runtime/`，286 MB 整套拷走即用 |
| 演示数据 | `make_mess.py` 生成 45 个文件，内含假 PDF、0 字节残留、同名冲突等杂乱脏文件 |
| 行为约束 | `stage/AGENTS.md` 规范 agent 行为|
| 文档 | 演示稿指导、素材指导、原理图规格、本 README |

### 上游依赖

- **Pi** — https://github.com/earendil-works/pi ，MIT License
- 本仓库不修改 Pi 的源码，只调用它的 CLI

---

## 本仓库包含

| 类型 | 文件 |
|---|---|
| 核心实现 | `chat.py`（对话外壳与调试模式）、`make_mess.py`、`clear.py`、`folder_agent.py`（12 行 harness 内核） |
| 启动脚本 | `1_make.cmd`、`2_clear.cmd`、`3_chat.cmd` |
| Agent 规矩 | `stage/AGENTS.md`（五条行为约束） |
| 文档 | `README.md`、`HTML演示稿指导.md`、`素材指导.md`、`原理图规格.md` |
| 演示页 | `slides.html` |

**不包含**（`.gitignore` 已排除，需自行准备）：

- `key.txt` —— API 凭证
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

**不需要装任何东西。** node、Git Bash、Python 都在 `runtime/` 里带着，整个文件夹拷到任何 Windows 机器上都能跑（见 [换一台电脑用](#更换设备)）。

---

## 使用说明

### 三个脚本分别干什么

| 双击 | 作用 | 
|---|---|
| `1_make.cmd` | 在 `stage/workspace/` 里铺 45 个文件 + 2 个子目录，约 0.5 秒 |
| `2_clear.cmd` | 清空待整理区，问你 `y/N` |
| `3_chat.cmd` | 进入对话，等你的指令 |

一般流程： **1 → 3 → 用完 2 清场 → 下次再 1**。

### 调试模式

双击 `3_chat.cmd` 后进入调试确认：

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

### 界面阅读（普通模式）

```
> 这个文件夹有点乱，根据用途分类

  ▸ 执行 find . -type f | wc -l && mkdir -p 图片 课程资料
    45

  ▸ 执行 head -c 4 发票2024.pdf | xxd
    00000000: 8950 4e47                                .PNG

整理完成。移动 40 个，45 → 45 对得上……
```

- **`▸ 执行 …`** —— agent 调用工具
- **缩进那一行** —— 工具返回，反馈运行成功
- **没有箭头的一大段** —— agent 对用户输出


### 指令参考

`stage/AGENTS.md` 只规定了五条**行为规矩**（不许删、不许覆盖、前后数数、看内容不看后缀、最后报告）

已验证能跑通的：

| 指令 | 实际发生的事 |
|---|---|
| `这个文件夹有点乱，根据用途分类` | 移 40~43 个，建 8~11 个目录，揪出后缀造假的文件 |
| `按科目分类，分不清的放"待确认"` | 按课程归类，模糊的单独隔离 |
| `给所有 pdf 的文件名加上最后修改日期前缀` | 改成 `20261113_xxx.pdf`，**拒改**那个假 pdf |
| `找出重复的文件` | 用 `md5sum` 比对，报出同哈希的组 |
| `统计一下有几个文件、总共多大` | 只读不写 |

### 退出与重置

- 输入 `quit` / `exit` / `q` 退出，或 `Ctrl+C`
- 每次启动都是**全新对话**（session id 带时间戳），不记录记忆
- 想恢复干净环境：`2_clear.cmd` 清空 → `1_make.cmd` 重建

### 填 key

打开 `key.txt`（记事本就行），是这样的：

```
# 把下面的 key 换成你自己的，然后保存。这个文件不要发给别人。
provider=name
model=modelid
key=**-*****
thinking=minimal
base_url=http(s)://ip/v1
```

在 `key=` 后面填上 key。五个字段的含义见 [换 provider 和 key](#更换-provider-和-key)。

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
├── key.txt.example     key.txt 的样板，字段说明都在里面
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

## 更换设备

### 一般使用的方式

用 `harness-demo-portable.zip`（106 MB）。解压出来是一个 `harness-demo/` 文件夹，进去填好 `key.txt`，双击 `3_chat.cmd`。

目标机 **不需要装 node / Git / Python**，`runtime/` 。

### 整个文件夹拷贝

注意事项：

- 拷到 U 盘/网盘时确认 `runtime/node/node.exe`（83 MB）没被同步工具跳过
- 路径里**可以有中文和空格**，脚本都用 `%~dp0` 自己定位
- 路径**不要超过 240 个字符**，Windows 老 API 有长度限制

### 更换 provider 和 key

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

`runtime\git` 是 PortableGit 裁剪过的版本

---

## 常见问题

**启动就报 `key.txt 里没有 key`**
→ 打开 `key.txt`，把 `key=` 后面填上。这行空着就会被拦下来。

**报 `找不到 node.exe` / `找不到 bash.exe`**
→ 说明 `runtime/` 被删了，系统里也没有。把 `runtime/` 恢复回来，或装 Node.js + Git for Windows。

**agent 一执行 bash 就报 `execvpe(/bin/bash) failed`**
→ 它用上了 WSL 的启动器（`C:\Windows\System32\bash.exe`）。删掉 `.pi-agent/` 让它重新生成 `settings.json`；还不行就是 `find_bash()` 没找到可用 bash，见坑 1。

**agent 说 `file: command not found`**
→ 正常。裁剪版 Git Bash 没有 `file`，它会自己退回 `od` / `xxd` 看魔数。想第一轮就顺，可以在 `stage/AGENTS.md` 里直接提示用 `xxd`。

**中文显示成乱码**
→ 三个 `.cmd` 里都有 `chcp 65001`。如果还是乱，检查终端字体，或改用 Windows Terminal。

**每轮都很慢**
→ 慢在模型推理，不在本地。可以把 `thinking=` 设成 `off` 或 `minimal` 提速。

**整理完想重来**
→ `2_clear.cmd` 清空，`1_make.cmd` 重建，两条命令回到初始状态。

---

## 已知限制

- 生成的 `.docx` / `.xlsx` / `.pptx` / `.zip` **只有 `PK` 文件头，不是有效的 ZIP**。agent 如果去解压会发现解不开，可能据此把它们放进"待确认"。可能需要 `zipfile` 生成真实容器。
- `key.txt` 是明文凭证，**不要提交、不要外发**。
- **Git Bash 里没有 `file` 命令**（PortableGit 的 `usr\bin` 下不含 `file.exe`）。agent 会先试 `file`、失败后自己退回 `od` / `xxd` 读魔数——实测能退回来，但第一轮会多花一两次调用。
- `runtime/git` 是裁剪版（68 MB）。`git` 命令本身用不了（删了 `mingw64/`），只有 bash + coreutils。演示够用；要真用 git 请装完整版 Git for Windows（130 MB）。
- 只在 Windows 上验证过。`chat.py` 里 `find_node` / `find_bash` 的路径都是 Windows 写法，换 macOS/Linux 要改。

---

## 修改方式

**换模型 / 换供应商**：改 `key.txt` ，重新双击 `3_chat.cmd`。

**换任务**：直接在对话里下别的指令。

**改规矩**：编辑 `stage/AGENTS.md`，下一轮立刻生效。

**改演示数据**：编辑 `make_mess.py`，然后 `2_clear.cmd` + `1_make.cmd` 重建。

**要看 agent 原始输出**：把 `chat.py` 的 `--mode json` 去掉，直接跑：

```
set PI_CODING_AGENT_DIR=%~dp0.pi-agent
runtime\node\node.exe node_modules\@earendil-works\pi-coding-agent\dist\bundle\cli.js --provider apigoto --model deepseek-flash "你的话"
```

**拆解内核**：`python folder_agent.py`，12 行 Python 复现同一套循环，不调模型，跑得很快，用来说明"harness 的本质就是工具 + 循环 + 回传 + 核对"。

**要讲这堂课**：`HTML演示稿指导.md` 教怎么做演示稿（风格选择 + 八页内容 + 技术要点），`素材指导.md` 教怎么录对比视频、怎么整理数据图表。`slides.html` 是早期做的示例页面，仅供参考。
