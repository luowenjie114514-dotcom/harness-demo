# 来源说明 / NOTICE

## 本项目修改自 Pi

Harness 驱动的 Agent（《人工智能通识》课程综合设计 · 小组作业）
在 Pi 的基础上构建。

**上游项目**：Pi（pi-coding-agent）
**仓库**：https://github.com/earendil-works/pi
**包名**：@earendil-works/pi-coding-agent
**许可证**：MIT License

本项目**没有修改 Pi 的源码**，只是调用它的 CLI 接口
（`node node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js`），
在它外面加了一层中文对话外壳、调试模式、可移植运行时和演示数据。

Pi 的 MIT 许可证全文见 `node_modules/@earendil-works/pi-coding-agent/LICENSE`
（发行包中位置相同）。

---

## DeepSeek 参与开发

本项目在开发过程中使用 DeepSeek 模型辅助，范围包括：

- 代码实现与重构（`chat.py` 的调试模式、shell 解析修复、provider 配置生成）
- 问题排查（WSL bash 误用、Git Bash shim 机制、GitHub API 空仓库限制）
- 文档撰写（README、演示稿指导、素材指导、原理图规格）

人类成员负责：需求定义、方案决策、实机验证、内容审核与最终定稿。

论文/答辩引用时请如实说明 AI 参与的边界。

---

## 第三方组件

| 组件 | 用途 | 许可证 |
|---|---|---|
| Pi / pi-coding-agent | agent 循环与工具系统 | MIT |
| Node.js | 运行时 | MIT |
| Git for Windows（PortableGit） | Git Bash 与 coreutils | GPL-2.0 |
| Python（embeddable） | 脚本运行时 | PSF License |
| openai / @anthropic-ai / @google 等 SDK | 模型调用（Pi 的依赖） | 各自许可证 |

发行包 `harness-demo-portable.zip` 内含上述运行时的完整副本，
各自的许可证文件保留在对应目录下。