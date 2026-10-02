# Occlusion-Aware Tracking

项目仓库：[shuiliufu-design/occlusion-aware-tracking](https://github.com/shuiliufu-design/occlusion-aware-tracking)。

面向机器人感知的视觉跟踪学习项目：逐步研究遮挡与物体位移后的
跟踪失效判断和目标恢复。第一阶段使用固定相机、单个主要桌面目标。

**当前阶段：00 已采纳有界纹理对齐；03 已完成 A/B/C 共同入口、两片开发预演与冻结准备，待 00 核对后正式冻结。旧默认保留，M3 独立测试未启动。**
真实双瓶歧义、同包装替换和独立对照评价尚未验证；3D 定位与机器人控制尚未实现。

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

## M2 第一步：目标丢失与候选报告

复用 v2 检测/跟踪记录及原视频，不需要 GPU 或新依赖。初始化帧与人工框为原视频帧号及原图 xyxy 像素坐标；本次配置来自对 f600 红盖瓶子的画面查看，不是正式真值标注。

```bash
.venv/bin/python scripts/run_target_state.py --baseline outputs/tabletop_02_baseline_v2 --source data/tabletop_02.mp4 --output outputs/tabletop_02_m2_step1 --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --init-iou 0.5
.venv/bin/python scripts/review_target_state.py --output outputs/tabletop_02_m2_step1 --frames 600 693 694 702 703 844 845 848
.venv/bin/python -m unittest discover -s tests -v
```

复跑请换新输出目录。`--end-frame` 可指定原视频结束帧（不含该帧），默认到结尾。初始化只接受与人工框唯一匹配的已关联瓶子，未硬编码 ID 或遮挡时间。

输出 `status.mp4`、`frames.jsonl`、`events.jsonl` 与配置/核查 JSON。视频从初始化帧开始；记录保留原帧索引和时间，另存从 0 开始的 `output_frame_index`。
本次输出 384 帧并通过重解码核查，f703 进入 LOST，f845 报告 RECOVERY_CANDIDATE；8 项状态逻辑检查通过。

连续缺失达到可配置阈值前保持 TRACKING 决策，但无本帧目标观察时立即清空当前框、显示位置未知。确认丢失后所有同类检测只作 UNVERIFIED 候选，包含原 ID 再现的情况，不自动回 TRACKING。
关闭新增模块时直接查看原始 v2 视频/记录；M1 入口与全部输出保持原状。详细数据字段、阈值、状态转换与限制见 [M2 第一步说明](docs/target_state_m2_step1.md)。

## M2 第二步：冻结外观参考与恢复关联

复用同一 v2 记录与原视频，参考只从初始化后的合格观察建立并冻结。候选通过瓶盖/标签颜色、标签纹理、形状、竞争差值与连续 5 帧确认后，才将原项目目标 `T1` 关联到当前原生 ID；原生 ID 不改写。参数见 `configs/recovery.json`。

```bash
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/tabletop_02_m2_step2_v3 --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery.json
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_02_m2_step2_v3 --annotations outputs/m2_step2_identity_review/identity_annotations.json --frames 600 609 691 692 701 845 847 848 851 852 900 983
```

重复运行须换新目录。身份记录仅本地保存；缺少独立记录时省略 `--annotations`，程序接受保留为未评价。新增 `--disable-recovery` 并换新输出目录可退回第一步仅候选行为。
本次有效结果为 `outputs/tabletop_02_m2_step2_v3/`，384 帧核查通过；f848—852 连续通过后接受，物理身份依据来自用户无替换的操作确认与独立画面核对。
23 项状态/门控测试通过；挂包真实裁剪中 2 帧外观拒绝、5 帧质量暂缓，0 绑定。v2 与第一步共 29 个文件保持不变。

新视频 `data/tabletop_wrong_bottle_01.mp4` 的真实不同瓶子验证已运行：633 帧读取/基线/状态视频核查一致；人工清楚可见区间 f485—632 的 148 帧均有合格候选并外观拒绝，0 绑定。用户确认换成另一只瓶子，原瓶子未再入镜。原视频像素逐帧重算一致；当前共 31 项测试通过，旧 84 个输出文件保持不变。

```bash
.venv/bin/python scripts/validate_wrong_bottle.py --output outputs/tabletop_wrong_bottle_01_m2_step2 --annotations outputs/tabletop_wrong_bottle_01_input/identity_annotations.json --report outputs/tabletop_wrong_bottle_01_m2_step2/wrong_bottle_validation_v2.json
```

复跑报告也须换新路径。新视频在遮挡时挡住整个镜头；瓶盖门槛也失败，未隔离标签模块贡献；f180 原瓶子仍可见时，检测框变化导致纹理门控提前清空位置。保留这些限制，不将单段负例零误绑定推广为准确率。真实双瓶歧义、同包装替换均待验证。准确命令与证据见 [真实负例说明](docs/wrong_bottle_m2_validation.md)；初次实现记录见 [M2 第二步说明](docs/appearance_recovery_m2_step2.md)。

04 发现旧关闭报告的 `loss_episodes=0` 汇总错误，03 已修复。当前关闭结果为 `outputs/tabletop_02_m2_step2_disabled_v2/`、`outputs/tabletop_wrong_bottle_01_m2_disabled_v2/`，各正确记录1次丢失；384/633帧记录、事件、视频与旧结果完全一致。统计修复时35项测试通过，旧184个输出文件保全。修复命令与证据见 [关闭统计修复](docs/m2_disabled_statistics_fix.md)。历史运行输出的代码校验对应当时提交。

统一评价现在使用独立人工返回/替换事件，旧通用评价保留但不参与新汇总：正例开启正确恢复1次，关闭未恢复1次；两组负例原目标无返回机会，不能算恢复失败。开启负例人工区间148个合格拒绝帧属于一次替换事件，全程149候选另列；关闭组外观核验不适用。f180可见却UNKNOWN继续作为失败证据，全片误报率未评价。54项测试通过，准确口径、标注覆盖与历史来源核查见 [统一离线评价](docs/offline_evaluation_m2.md)。

```bash
.venv/bin/python scripts/evaluate_offline.py --protocol configs/m2_evaluation.json --output outputs/m2_evaluation_v1
```

复跑换空的新目录。结果位于 `outputs/m2_evaluation_v1/summary.json` 与 `per_event_results.json`；本次没有修改恢复行为、冻结配置或启动M3。

f180开发修正另提供 `configs/recovery_f180_dev.json`：在标签纹理真实共同区域上搜索最多±6/±9像素，原门槛不变，旧默认配置仍保留。诊断窗清楚可见UNKNOWN从1/11降为0/11，开启第2步的f181与8帧全遮挡仍UNKNOWN；正例仍f852正确接受，负例148帧合格候选仍拒绝。70项测试通过。准确命令、旧/新规则与关闭对照及限制见 [有界纹理对齐开发回归](docs/f180_alignment_development.md)，最终报告 `outputs/f180_alignment_dev/comparison_v2.json`；00已采纳该配置，三组协议待核对冻结；M3独立测试未启动。

## 学习路线

M3 共同入口与开发预演说明见 [M3协议](docs/m3_protocol.md)。当前只跑已有开发输入，复跑必须换新的空目录：

```bash
.venv/bin/python scripts/run_comparison.py --protocol configs/m3_protocol_v1.json --output outputs/m3_development_preflight_v4
.venv/bin/python scripts/m3_common.py --check-freeze outputs/m3_development_preflight_v4/freeze_checklist.json
```

最终六组结果和评价在 `outputs/m3_development_preflight_v4/`。正例A/B未返回，C在f852正确返回；负例无返回机会，C148帧合格候选均拒绝。98项测试通过。冻结清单仍待00核对，固定抽样只核对6/103帧；f850三组均UNKNOWN，负例A/B f181缺少人工完整框，位置核对未评价。全片误报率和速度仍未评价/验证。

- [x] 第 1 步：真实视频读取（首段 656 帧、补拍 984 帧；用户已确认补拍检查完成）
- [x] 第 2 步：预训练目标检测基线，保存逐帧检测结果
- [x] 第 3 步：跟踪基线，观察遮挡后的 ID 变化与误检轨迹
- [x] 第 4a 步：指定目标、连续缺失判断与未经身份核验的恢复候选
- [x] 第 4b 步：04确认受限开发恢复/拒绝验收，03修复关闭统计；困难例仍未验证
- [x] 第 4c 步：00采纳f180对齐；03完成三组共同入口/开发预演/冻结准备
- [ ] 第 5 步：00核对三组交付并冻结，再另拍3段独立视频进行M3最小对照
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
| `scripts/run_target_state.py` | 复用基线，输出目标状态、候选与事件 |
| `scripts/review_target_state.py` | 核查 M2 状态记录、候选、事件及视频 |
| `tests/test_target_state.py` | 状态边界与未经身份核验不得绑定的回归检查 |
| `scripts/appearance_recovery.py` | 冻结外观参考、候选门控与连续确认状态 |
| `scripts/run_recovery.py` | 保存第二步视频、参考、事件与配置，支持关闭恢复 |
| `scripts/review_recovery.py` | 核对恢复证据、视频、原始输出保全与独立身份评价 |
| `scripts/validate_recovery_fixture.py` | 挂包真实裁剪与构造 LOST/等分候选的模块验证 |
| `scripts/validate_wrong_bottle.py` | 用人工身份区间核查真实瓶子拒绝，逐帧重算原像素证据 |
| `scripts/evaluate_offline.py` | 以共用人工事件统一开启/关闭的返回、拒绝与误报评价 |
| `scripts/evaluation_sources.py` | 严格核对历史Git代码SHA，在临时目录复核旧结果 |
| `configs/m2_evaluation.json` | 当前两段开发视频的独立事件/标注适配与来源清单 |
| `tests/test_offline_evaluation.py` | 无返回机会、缺标注接受、覆盖/区间与来源边界测试 |
| `scripts/review_alignment_development.py` | 固定诊断窗、旧/新评价、默认/关闭回归与保全比较 |
| `scripts/run_comparison.py` | 同一缓存/初始化运行A/B/C并调用共同人工事件评价 |
| `scripts/evaluate_comparison.py` | 以人工身份/本帧框评价三组正确返回，不依赖A/B接受事件 |
| `scripts/m3_common.py` | 共同输入、待冻结清单核查与正式输入冻结保护 |
| `configs/m3_protocol_v1.json` | 现有开发片预演、未来三片设计及共同指标/抽样/计时口径 |
| `configs/recovery_m3_v1.json` | 与00采纳对齐配置逐字节一致的C配置副本 |
| `tests/test_m3_comparison.py` | 三组选择/返回、物理身份、未知标注与冻结保护28项边界测试 |
| `configs/recovery_f180_dev.json` | 可关闭的有界标签纹理平移开发配置，原门槛保持不变 |
| `tests/test_texture_alignment.py` | 平移/共同区域/退化与对齐开启后的状态安全测试 |
| `configs/recovery.json` | 外观/质量/竞争/确认参数，沿用 SPEC.md 起始值 |
| `tests/test_appearance_recovery.py` | 外观与身份门控、参考冻结和再次丢失回归检查 |
| `requirements-baseline.txt` | M1 核心依赖版本，包含原视频 I/O 依赖 |
| `docs/baseline_m1.md` | 原始基线能力、实际观察与失败案例 |
| `docs/target_state_m2_step1.md` | 目标初始化、状态规则、实际结果与限制 |
| `docs/appearance_recovery_m2_step2.md` | 第二步规则、实际验证、身份依据与待补负例 |
| `docs/offline_evaluation_m2.md` | 统一评价口径、准确命令、四组开发结果与未评价范围 |
| `docs/f180_alignment_development.md` | 有界标签纹理对齐、开发回归、准确命令与能力边界 |
| `docs/m3_protocol.md` | 三组共同入口、开发预演结果、标注缺口及冻结/正式输入约定 |
| `data/` | 本地输入视频，默认不上传 |
| `outputs/` | 本地生成结果，默认不上传 |
| `docs/lesson01.md` | 第一课讲解与操作步骤 |
| `docs/learning_log.md` | 个人理解、观察与疑问 |

## 复现与结果

`requirements.txt` 固定第一课依赖版本。实验视频、模型文件和输出不进入 Git。
真实视频已运行原始检测与跟踪，并有受限开发身份/事件依据和四组评价；尚无独立保留测试或泛化性能结论。
后续由00按SPEC.md核对三组共同口径与清单并正式冻结，再另拍独立输入完成小规模对照。

## 参考

- [OpenCV 视频入门](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html)
- [Ultralytics 跟踪文档](https://docs.ultralytics.com/modes/track/)，本次固定 Ultralytics 8.3.221 的 ByteTrack 实现
- [FoundationPose](https://github.com/NVlabs/FoundationPose)，候选后续 3D 基线，目前未集成
