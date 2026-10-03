# 在自己的视频上运行第一版

所有命令在项目根目录执行，使用 Bash。沿用 README 的 `SOURCE`、`RUN`、`INIT_FRAME` 和 `INIT_BOX`；每次复跑换空目录。流程是原视频 → 固定检测/关联 → 早期原图人工初始化 → 冻结 C → 查看输出。人工事件/身份真值只传评价器，不传恢复算法。

## 环境与模型

现机器沿用 `.venv`，不重建、不重装。记录过的环境为 Ubuntu 24.04、Python 3.12.3、RTX 4070 Laptop 8GB；PyTorch 2.8.0+cu128 / torchvision 0.23.0+cu128。GPU 可见性不等于运算验证，历史基线另有矩阵乘法与完整 GPU 推理证据。

核心版本见 `requirements-baseline.txt`：Ultralytics 8.3.221、torch 2.8.0、torchvision 0.23.0、OpenCV 4.12.0.88、NumPy 2.2.6、lap 0.5.12、SciPy 1.18.1、PyYAML 6.0.3。清单固定核心版本，不是全部传递依赖的离线安装包；冻结时的完整安装快照在本地 `outputs/m3_development_preflight_v4/dependencies_snapshot.txt`。

仅新机器或首次克隆且没有可用环境时，按 [PyTorch 官方 2.8 安装说明](https://pytorch.org/get-started/previous-versions/) 选择 CPU 或匹配的 CUDA 构建。下面是同一 CUDA 12.8 构建的准备命令；M4 没有重跑下载安装，也没有验证全新机器安装：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu128
.venv/bin/python -m pip install -r requirements-baseline.txt
.venv/bin/python -m pip check
```

CPU 运行仍可用 CUDA 构建的现有环境。新机器若选择 CPU 构建，改用官方 CPU 索引；功能运行不承诺与 GPU 缓存逐位相同，也不能替代固定 GPU 条件的三片精确实验复现。

权重为 [Ultralytics 官方 YOLO11n 发布文件](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt)。已有权重无需下载；缺少时：

```bash
mkdir -p weights
curl -fL https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt -o weights/yolo11n.pt
sha256sum weights/yolo11n.pt
```

所测 SHA-256：`0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`。核对相同后再运行。脚本不会自动安装依赖，模型路径必须存在。

## 视频与基线

使用固定相机、单个主要直立瓶子，瓶盖/标签尽量正对相机，先留至少 5 秒无遮挡画面，再遮挡和重现/位移。可参照 [拍摄说明](../data/README.md)；自己的功能视频不是自动新增的 M3 测试样本。预训练检测只识别 bottle 类，不识别指定瓶子的物理身份。

执行 README 的读取、基线与核查命令。检查 `$RUN/input/first_frame.jpg` 是否方向和内容正确，`video_info.json` 是否非零帧。基线固定 bottle、imgsz=640、conf=0.1、NMS IoU=0.7；ByteTrack 使用 Ultralytics 8.3.221 包内默认 YAML：高/低/新轨迹阈值 0.25/0.1/0.25、缓冲 30、匹配阈值 0.8、fuse_score=true。源码构造 `frame_rate=30`，实际最大失活缓冲 30 帧，不修改其关联。

原生 ByteTrack 可以在缓冲内保留短时失活轨迹并重新关联；本项目 A 的选择约定只沿初始 ID，不在后段挑新 ID。B 确认丢失后仅候选。C 才增加外观核验与重新绑定，不能把所有重新出现的框计作 C 的贡献。

## 人工初始化

1. 从早期无遮挡原图选目标完整框，记录原帧号、宽高和 `[x1,y1,x2,y2]`。左上角为 `(0,0)`，x 向右、y 向下，坐标用原图像素。不要用缩略图或带算法框画面直接当作原图坐标。
2. 若选 f0，可直接用读取检查的原图 `first_frame.jpg`。需要另一早期帧时，下面的顺序解码片段只保存那一帧原图；把数字替换为已经选定的早期帧：

```bash
.venv/bin/python - "$SOURCE" "$RUN" 0 <<'PY'
import sys
from pathlib import Path
import cv2
source, run, wanted = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
cap = cv2.VideoCapture(source)
try:
    for index in range(wanted + 1):
        ok, frame = cap.read()
        if not ok:
            raise SystemExit('无法读取所选原帧')
    path = run / f'init_raw_{wanted:06d}.png'
    if path.exists():
        raise SystemExit('原图已存在，请保留并换路径')
    if not cv2.imwrite(str(path), frame):
        raise SystemExit('原图保存失败')
    print(path, '原图宽高:', frame.shape[1], frame.shape[0])
finally:
    cap.release()
PY
```

3. 用图像查看器显示原始尺寸，读出目标完整框。README 的 `(290 280 510 1040)` 是 720×1280 开发视频的示例，不通用于自己的视频。填好 `INIT_FRAME` / `INIT_BOX` 再执行 C 命令。
4. 初始化需要与恰好一个已关联 bottle 检测 IoU>=0.5；未匹配时检查方向、缩放、坐标和早期帧的实际检测，不放宽冻结门槛、不用后段效果来挑初始化。没有唯一可用早期检测时保留失败，该视频不能按此入口建立目标。

C 在初始化后因果收集最多 10 个合格参考、等待最多 30 帧、至少 5 个，首次轨迹缺失即停止；冻结后不更新、不从恢复画面补参考。`INSUFFICIENT_REFERENCE` 表示不能自动恢复。配置中的区域针对直立瓶盖/标签，任意物体和不同布局不保证可用。

## 查看、关闭与理解输出

| 文件/字段 | 含义 |
| --- | --- |
| `baseline/annotated.mp4` | 原生跟踪框与未关联检测；不是目标身份真值 |
| `C/status.mp4` | 绿色 T1 框为程序当前观察，候选框/标签为程序证据；不含人工评价框 |
| `C/frames.jsonl` | 原始检测/轨迹、三状态、候选分量/原因/确认计数、当前目标框 |
| `C/events.jsonl` | 状态转换、参考冻结、恢复接受等事件；没有恢复事件也可能正常完成运行 |
| `C/references.json`、`references/` | 冻结参考来源、质量与裁剪，可以检查是否取到指定目标 |
| `C/run_info.json` | 输入/代码/配置校验、准确命令、依赖版本与初始化 |
| `C/review.json`、`evaluation.json` | 结构/视频核查与本次独立身份评价；未传身份记录的接受保持 UNEVALUATED，旧通用待办字段不代表项目当前状态 |

`TRACKING` 是状态决策；缺失未满 10 帧时仍可能是 TRACKING，但 `position_known=false`、当前框为空。达到阈值为 LOST；出现同类候选为 RECOVERY_CANDIDATE。候选 `ACCEPTABLE` 仍需同 ID、空间连续且连续 5 帧通过全部门槛/竞争检查；`RECOVERY_ACCEPTED` 仅表示规则允许重新绑定，不是物理身份概率或人工成功标签。

关闭身份恢复使用新目录，复用同一缓存、原图和初始化：

```bash
.venv/bin/python scripts/run_recovery.py --source "$SOURCE" --baseline "$RUN/baseline" --output "$RUN/B" --init-frame "$INIT_FRAME" --init-box "${INIT_BOX[@]}" --init-iou 0.5 --missing-frames 10 --config configs/recovery_m3_v1.json --disable-recovery
.venv/bin/python scripts/review_recovery.py --output "$RUN/B"
```

关闭分支委托原 TargetState，确认 LOST 后永不自动绑定；关闭的只是身份恢复，仍有指定目标/失效/候选模块。查看原始基线则完全绕过自定义状态/恢复。正式 A/B/C 评价入口见 [精确实验复现](m3_results.md#精确实验复现)，README 的基线视频不是那里的 A 适配器状态视频。

## 常见运行问题

- 路径不存在：先放入自己的视频和权重，再运行；不要用本机私有缓存代替公开流程。
- 输出非空：保存旧目录并换 `RUN`；失败可能留下部分文件，不能覆盖成成功结果。
- CUDA 不可见：功能检查使用 `--device cpu`，本地实际推理设备写入 run_info；未做速度承诺。
- 参考不足/质量暂缓/歧义：查看原图、参考与原因；记录失败，不为演示放宽冻结参数。完全遮挡时 UNKNOWN 是正确的边界表达。
- 播放器不能解码 mp4v：使用本机支持该编码的播放器。OpenCV 重解码验证不等于所有浏览器能播放，视频没有音频。

发布验证、已运行步骤与未验证安装范围见 [M4 验证记录](m4_validation.md)。
