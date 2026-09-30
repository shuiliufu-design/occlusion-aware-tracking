# Occlusion-Aware Tracking

项目仓库：[shuiliufu-design/occlusion-aware-tracking](https://github.com/shuiliufu-design/occlusion-aware-tracking)。

面向机器人感知的视觉跟踪学习项目：逐步研究遮挡与物体位移后的
跟踪失效判断和目标恢复。第一阶段使用固定相机、单个主要桌面目标。

**当前阶段：两段真实视频已读取，补拍包含目标遮挡与位移；待用户确认预览，下一步运行检测与跟踪基线。**
尚未实现目标检测、跟踪、失效检测、恢复、3D 定位或机器人控制。

## 快速开始

推荐 Python 3.12，在 Ubuntu 上运行。第一课只需要 CPU。

当前项目已有 `.venv`，直接沿用：

```bash
source .venv/bin/activate
python scripts/check_env.py
```

仅新机器或首次克隆后需要创建环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

准备视频，拍摄说明见 [data/README.md](data/README.md)。

```bash
python scripts/inspect_video.py --source data/tabletop_01.mp4 --output outputs/tabletop_01
```

程序逐帧读取视频，保存首帧预览与基本信息。输出目录必须为空。
无真实视频时可先运行合成视频读写自检：

```bash
python scripts/make_sample_video.py
python scripts/inspect_video.py --source data/synthetic_io.avi --output outputs/synthetic_io
```

合成视频仅验证 I/O，不代表模型效果。

## 学习路线

- [ ] 第 1 步：真实视频读取（首段 656 帧、补拍 984 帧已解码并查看抽帧预览；待用户确认预览）
- [ ] 第 2 步：预训练目标检测基线，保存逐帧检测结果
- [ ] 第 3 步：跟踪基线，观察遮挡后的身份丢失与错误关联
- [ ] 第 4 步：失效判断与恢复策略，设置公平对照实验
- [ ] 后续研究：可靠性估计、3D 位姿跟踪与机器人仿真验证

## 文件说明

| 路径 | 作用 |
| --- | --- |
| `AGENTS.md` | 开发规则、环境、验证与交接要求 |
| `SPEC.md` | 第一版范围、验收标准与确定的决策 |
| `STATUS.md` | 实际进度、验证证据、结果路径与下一步 |
| `scripts/check_env.py` | 检查 Python、OpenCV 与 GPU 可见性 |
| `scripts/inspect_video.py` | 读取视频，保存首帧和基本信息 |
| `scripts/make_sample_video.py` | 生成不需下载的 I/O 自检视频 |
| `data/` | 本地输入视频，默认不上传 |
| `outputs/` | 本地生成结果，默认不上传 |
| `docs/lesson01.md` | 第一课讲解与操作步骤 |
| `docs/learning_log.md` | 个人理解、观察与疑问 |

## 复现与结果

`requirements.txt` 固定第一课依赖版本。实验视频、模型文件和输出不进入 Git。
真实视频的检测与跟踪尚未评测，当前没有准确率或恢复性能结论。
后续将补充数据来源、评测协议、对照实验及实际结果。

## 参考

- [OpenCV 视频入门](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html)
- [Ultralytics 跟踪文档](https://docs.ultralytics.com/modes/track/)，候选后续基线，目前未集成
- [FoundationPose](https://github.com/NVlabs/FoundationPose)，候选后续 3D 基线，目前未集成
