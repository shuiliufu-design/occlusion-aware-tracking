# 项目状态

更新日期：2026-09-30（Asia/Shanghai）。协调聊天：00｜项目总控；当前执行聊天：02｜环境与跟踪基线。

## 当前结论

处于 M0：环境与合成视频 I/O 已有验证，真实桌面视频尚未放入项目。
检测、跟踪、失效判断、恢复与对照实验均未实现。下一项技术任务只有“准备真实桌面视频并完成读取检查”。

## 已完成与证据

| 内容 | 状态与依据 |
| --- | --- |
| 项目结构与环境 | 已有 `.venv`、`requirements.txt`、README、教学文档、视频读取/合成脚本 |
| 02 接手环境检查 | 再次运行 `.venv/bin/python scripts/check_env.py`，退出码 0；Python 3.12.3、OpenCV 4.12.0（opencv-python 4.12.0.88）、NumPy 2.2.6，解释器位于项目 `.venv`；沿用原环境，未安装新依赖 |
| 用户本机环境 | `docs/learning_log.md` 记录用户本机检查通过；交接背景为 Ubuntu 24.04、RTX 4070 Laptop 8GB，记录中显存 8188 MiB、驱动 580.178.04 |
| GPU 验证边界 | 本次受限会话无法查询 NVIDIA GPU；不推翻用户本机记录。PyTorch GPU 运算仍未验证 |
| 合成视频 I/O | 02 实际重跑读取检查，退出码 0；新结果 `outputs/synthetic_io_02_check/video_info.json` 记录 640×360、20 FPS、100 帧、估算 5 秒。既有结果保留；此前读写与错误路径检查见 `docs/lesson01.md`，02 未重跑错误路径检查 |
| 交接文件 | 00 已建立 `AGENTS.md`、`SPEC.md`、`STATUS.md` 并同步 README；02 接手时已重新读取并核对代码与实际输入 |
| Git | 02 将已核查的环境与视频 I/O 脚本、说明及交接记录纳入首次本地提交（`chore: initialize video I/O baseline and project handoff`）；用 `git log -1 --oneline` 查看提交。`git remote -v` 无输出，未配置远程，未上传 |

合成结果只证明 I/O，不证明目标检测、跟踪或恢复效果。

## 现有文件与结果

- 环境检查：`scripts/check_env.py`。
- 视频读取：`scripts/inspect_video.py`。
- 合成视频生成：`scripts/make_sample_video.py`。
- 本地合成输入：`data/synthetic_io.avi`。
- 既有结果：`outputs/synthetic_io/first_frame.jpg`、`outputs/synthetic_io/video_info.json`。
- 02 本次结果：`outputs/synthetic_io_02_check/first_frame.jpg`、`outputs/synthetic_io_02_check/video_info.json`。
- 拍摄说明：`data/README.md`；学习理解继续写入 `docs/learning_log.md`。
- 本次检查 `data/`，没有真实桌面视频；未检查项目以外的个人视频目录。

02 本次实际运行命令（项目根目录）：

```bash
.venv/bin/python scripts/check_env.py
.venv/bin/python scripts/inspect_video.py --source data/synthetic_io.avi --output outputs/synthetic_io_02_check
```

工程代码未修改；真实视频缺失，因此未运行真实视频检查，也未加入检测或跟踪模型。

## 下一项任务：真实视频读取检查

目的：确认后续检测与跟踪使用的真实输入可以解码，并包含无遮挡、遮挡和遮挡期间位移的过程。

用户准备一段约 15—25 秒的固定相机桌面视频：前几秒目标可见，遮挡约 2 秒后显露，再遮挡并移动目标，最后保持可见。
优先使用杯子或瓶子、720p/1080p、约 30 FPS、H.264 MP4，放为 `data/tabletop_01.mp4`。

输入到位后在项目根目录执行（以下尚未运行）：

```bash
.venv/bin/python scripts/inspect_video.py --source data/tabletop_01.mp4 --output outputs/tabletop_01
```

交付：`outputs/tabletop_01/first_frame.jpg`、`outputs/tabletop_01/video_info.json`。
验收：命令成功、解码帧数大于零、宽高/FPS 已记录；用户确认首帧方向与视频内容正确。
输出目录必须为空；如已有结果，使用新目录名并在此记录实际路径。估算时长和读取停止不能单独证明视频完整性。

## 待办与交接

1. 完成真实视频读取检查并更新本文件，再由 02 推进轻量检测与跟踪基线。
2. 后续每个可运行里程碑完成后检查变更并提交 Git；当前环境与合成 I/O 已纳入首次本地提交。
3. GitHub 远程待用户提供或确认仓库地址后配置，不阻塞当前视频任务。
4. 03—05 在基线可检查后按需进入；01 可结合当前读取脚本学习。

未解决问题：缺少真实输入；GPU 运算未验证；基线方案与评测规则尚未确定。
