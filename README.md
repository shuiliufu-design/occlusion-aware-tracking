# Occlusion-Aware Tracking

项目仓库：[shuiliufu-design/occlusion-aware-tracking](https://github.com/shuiliufu-design/occlusion-aware-tracking)。

面向机器人感知的视觉跟踪学习项目：逐步研究遮挡与物体位移后的
跟踪失效判断和目标恢复。第一阶段使用固定相机、单个主要桌面目标。

**当前阶段：M0 读取验收通过；YOLO11n + 原始 ByteTrack 已在补拍视频上跑通，并保存逐帧结果。**
尚未添加失效判断与恢复策略，也未实现 3D 定位或机器人控制。

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

## M1 原始检测与跟踪基线

沿用已有 `.venv`。基线核心依赖固定在 `requirements-baseline.txt`；仅缺少时安装，已有可用环境无需重建：

```bash
.venv/bin/python -m pip install -r requirements-baseline.txt
```

本机实测 PyTorch 2.8.0+cu128、torchvision 0.23.0+cu128，RTX 4070 Laptop 上矩阵乘法与完整模型推理均通过。
新机器如需同一 CUDA 构建，可先按 [PyTorch 2.8 官方安装说明](https://pytorch.org/get-started/previous-versions/) 安装：

```bash
.venv/bin/python -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu128
.venv/bin/python -m pip install -r requirements-baseline.txt
```

权重来自 [官方 YOLO11n 发布文件](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt)，保存为 `weights/yolo11n.pt`。
已有文件已与官方重新下载件核对 SHA-256 一致，无需重复下载。缺少时创建 `weights/` 后执行：

```bash
curl -fL https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt -o weights/yolo11n.pt
```

本次实际运行（输出目录不可覆盖；复跑请改为新的目录）：

```bash
.venv/bin/python scripts/run_baseline.py --source data/tabletop_02.mp4 --output outputs/tabletop_02_baseline_v2 --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/review_baseline.py --output outputs/tabletop_02_baseline_v2 --frames 227 693 694 844 845 847 848
```

无可用 GPU 时显式使用 `--device cpu`；其速度尚未实测。受限会话可能隐藏 GPU，本次 GPU 检查和基线运行在沙箱外完成。

| 输出 | 用途 |
| --- | --- |
| `annotated.mp4` | 720×1280 的 mp4v 带框视频，无音频；绿框是原生轨迹，黄框是未关联检测 |
| `frames.jsonl` | 每帧一行 JSON，包括空检测帧；帧索引、时间、所有筛选后检测与关联轨迹 |
| `run_info.json` | 命令、输入/权重校验、核心版本、检测参数、GPU 运算与计时范围 |
| `bytetrack.yaml` | 未修改的包内默认跟踪配置副本 |
| `first_frame.jpg`、`contact_sheet.jpg` | 带框首帧、约每秒抽帧预览 |
| `review.json`、`frame_*.jpg` | 记录/输出视频一致性核查、ID 区间及关键帧预览 |

数据流为 `OpenCV 视频帧 → YOLO11n bottle 检测 → BYTETracker.update → 轨迹 ID → 视频与 JSONL`。
检测框 `bbox_xyxy` 是原始图像像素坐标 `[左, 上, 右, 下]`；轨迹框经过原生滤波，可能与检测框不同。
`track_id=null` 表示检测尚未获得可输出的轨迹。主时间为 `frame_index/nominal_fps` 的估算值；同时保存 OpenCV 报告的源时间，输出视频按名义 FPS 恒定帧率写出。

本次 984 帧均处理并重新解码检查通过。纸板遮挡前 ID 4，重现后 ID 5；还保留了挂包附近误检为瓶子的 ID 3。
详细证据和边界见 [基线说明](docs/baseline_m1.md)。没有新增恢复模块；检测分数、相同 ID 或再次出现框都不能证明目标身份正确。

## 学习路线

- [x] 第 1 步：真实视频读取（首段 656 帧、补拍 984 帧；用户已确认补拍检查完成）
- [x] 第 2 步：预训练目标检测基线，保存逐帧检测结果
- [x] 第 3 步：跟踪基线，观察遮挡后的 ID 变化与误检轨迹
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
| `scripts/run_baseline.py` | 固定版本 YOLO11n + ByteTrack，保存带框视频与逐帧记录 |
| `scripts/review_baseline.py` | 核查逐帧关联记录与输出视频，生成预览 |
| `requirements-baseline.txt` | M1 核心依赖版本，包含原视频 I/O 依赖 |
| `docs/baseline_m1.md` | 原始基线能力、实际观察与失败案例 |
| `data/` | 本地输入视频，默认不上传 |
| `outputs/` | 本地生成结果，默认不上传 |
| `docs/lesson01.md` | 第一课讲解与操作步骤 |
| `docs/learning_log.md` | 个人理解、观察与疑问 |

## 复现与结果

`requirements.txt` 固定第一课依赖版本。实验视频、模型文件和输出不进入 Git。
真实视频已运行原始检测与跟踪；尚无独立测试集及身份/事件标注，当前没有准确率或恢复性能结论。
后续将补充数据来源、评测协议、对照实验及实际结果。

## 参考

- [OpenCV 视频入门](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html)
- [Ultralytics 跟踪文档](https://docs.ultralytics.com/modes/track/)，本次固定 Ultralytics 8.3.221 的 ByteTrack 实现
- [FoundationPose](https://github.com/NVlabs/FoundationPose)，候选后续 3D 基线，目前未集成
