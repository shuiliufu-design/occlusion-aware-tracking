# 项目状态

更新日期：2026-10-01（Asia/Shanghai）。协调聊天：00｜项目总控；02 已交付 M1；03 已交付 M2 第一步，第二步代码与已有输入验证完成，真实错误瓶子验证待补，第二步为部分完成。接手聊天需重新读取记录与实际输出。

## 当前结论

M0 已验收：02 重新读取两段视频并核对本次首帧，用户明确说明“补拍视频已检查”，作为补拍方向与内容确认。补拍后半段包含背景持续可见的瓶子遮挡与位移。
M1 已实际跑通并通过输出核查：YOLO11n + 未修改的 Ultralytics ByteTrack，补拍视频的 984 帧均处理、记录并重新解码检查一致。有效结果为 `outputs/tabletop_02_baseline_v2/`。
纸板遮挡前 ID 4，长遮挡与位移后输出新 ID 5；保留背景挂包附近误检为瓶子的 ID 3。
M2 第一步已实际运行：复用 v2 与原视频，人工框配置初始化目标，输出 TRACKING / LOST / RECOVERY_CANDIDATE。有效输出为 `outputs/tabletop_02_m2_step1/`，384 条记录与状态视频重解码一致；f703 确认丢失，f845 出现未经身份核验的候选。该步保留为仅候选对照，不执行自动恢复。两段当前都用作开发输入，尚无独立测试集；M2 尚未全部验收。
00 已独立核对本步记录、事件、视频重解码与关键帧预览，M2 第一步达到预定实现要求。用户已反馈本步视频约 3.24 秒位置 UNKNOWN、3.55 秒进入 LOST、8.44 秒出现 UNVERIFIED 候选；03 核对已有记录一致。用户也已明确说明候选可能为其他瓶子或误检，分数/ID 不能单独确认身份，本步观看与理解核对均已完成。
M2 第二步已按 SPEC.md 实现并运行，参数沿用起始值：冻结 f600—609 的 10 个参考，候选多项外观门控、竞争排除与连续 5 帧确认，恢复后继续门控。有效输出 `outputs/tabletop_02_m2_step2_v3/`：f848—852 连续合格，f852 接受并将 T1 关联到新原生 ID；用户确认遮挡期间只移动原瓶子、未替换，独立身份记录支持该开发正例正确接受 1 次。挂包模块负例 2 帧外观拒绝、5 帧质量暂缓、0 绑定；构造等分候选暂缓。23 项测试与视频/证据核查通过，关闭模块退回第一步。真实错误瓶子、真实双瓶歧义、同包装困难例仍待输入，不能验收完整恢复/拒绝能力。

## 已完成与证据

| 内容 | 状态与依据 |
| --- | --- |
| 项目结构与环境 | 已有 `.venv`、`requirements.txt`、README、教学文档、视频读取/合成脚本 |
| 02 环境检查 | 本轮再次运行 `.venv/bin/python scripts/check_env.py`，退出码 0；Python 3.12.3、OpenCV 4.12.0（opencv-python 4.12.0.88）、NumPy 2.2.6，解释器位于项目 `.venv`；沿用原环境 |
| 用户本机环境 | `docs/learning_log.md` 记录用户本机检查通过；交接背景为 Ubuntu 24.04、RTX 4070 Laptop 8GB，记录中显存 8188 MiB、驱动 580.178.04 |
| GPU 验证边界 | 沙箱内 CUDA 不可见；02 在沙箱外验证现有 torch 2.8.0+cu128 的 CUDA 矩阵乘法（32×32 全一矩阵，结果 32），并在 RTX 4070 Laptop 上跑完模型推理，实际 GPU 运算已验证 |
| 合成视频 I/O | 02 实际重跑读取检查，退出码 0；新结果 `outputs/synthetic_io_02_check/video_info.json` 记录 640×360、20 FPS、100 帧、估算 5 秒。既有结果保留；此前读写与错误路径检查见 `docs/lesson01.md`，02 未重跑错误路径检查 |
| 真实视频 I/O | 02 重新运行原脚本，退出码 0；新结果 `outputs/tabletop_01_02_check/`：720×1280、名义约 28.7545 FPS、656 帧、估算 22.814 秒，与旧记录一致；已查看本次首帧 |
| 补拍视频 I/O | 02 重新运行原脚本，退出码 0；新结果 `outputs/tabletop_02_02_check/`：720×1280、984 帧、名义约 29.0377 FPS、估算 33.887 秒；本次首帧与既有抽帧预览已查看；用户说明补拍已检查 |
| M1 基线与核查 | `scripts/run_baseline.py` 实际处理 984 帧；`scripts/review_baseline.py` 核对记录/ID 映射/统计与视频重解码，退出码 0；有效输出为 v2。已查看带框首帧、每秒预览及 f227/f845/f848 |
| M2 第一步与核查 | `scripts/run_target_state.py` 复用原始记录、顺序解码 984 帧并输出 f600—983 共 384 帧；`review_target_state.py` 核查记录/阈值/事件/候选/视频，退出码 0；8 项 unittest 通过；v2 全部 14 个文件运行前后校验一致 |
| M2 第二步部分交付 | 最终 v3 输出/重解码各 384 帧，开发正例尝试/程序接受/有独立依据正确接受各 1；挂包模块负例 2 拒绝、5 暂缓、0 接受；关闭恢复与第一步逐项一致；23 项 unittest 通过；v2 与第一步共 29 个文件校验一致 |
| 基线依赖 | 接手时已有 torch 2.8.0+cu128、torchvision 0.23.0+cu128 和权重；本次补充 ultralytics 8.3.221、lap 0.5.12 等依赖，未重建环境或更换 OpenCV/NumPy；`pip check` 通过，固定核心版本见 `requirements-baseline.txt` |
| 交接文件 | 00 已建立 `AGENTS.md`、`SPEC.md`、`STATUS.md` 并同步 README；02 接手时已重新读取并核对代码与实际输入 |
| Git | 已有公开仓库与两段视频检查记录同步历史见下方；02 本轮按里程碑进行本地提交，不执行推送。视频、权重、环境、缓存与输出被忽略，保留本地 |

合成结果只证明 I/O，不证明目标检测、跟踪或恢复效果。

## 现有文件与结果

- 环境检查：`scripts/check_env.py`。
- 视频读取：`scripts/inspect_video.py`。
- 合成视频生成：`scripts/make_sample_video.py`。
- 本地合成输入：`data/synthetic_io.avi`。
- 既有结果：`outputs/synthetic_io/first_frame.jpg`、`outputs/synthetic_io/video_info.json`。
- 02 本次结果：`outputs/synthetic_io_02_check/first_frame.jpg`、`outputs/synthetic_io_02_check/video_info.json`。
- 拍摄说明：`data/README.md`；学习理解继续写入 `docs/learning_log.md`。
- 真实输入：`data/tabletop_01.mp4`；结果：`outputs/tabletop_01/first_frame.jpg`、`video_info.json`、`contact_sheet.jpg`。历史接手记录中的输入缺失描述保留为当时状态。
- 补拍输入：`data/tabletop_02.mp4`；结果：`outputs/tabletop_02/first_frame.jpg`、`video_info.json`、`contact_sheet.jpg`。
- 02 重新读取结果：`outputs/tabletop_01_02_check/`、`outputs/tabletop_02_02_check/`，各含 `first_frame.jpg` 与 `video_info.json`，旧结果保留。
- 可用基线：`outputs/tabletop_02_baseline_v2/annotated.mp4`、`frames.jsonl`、`run_info.json`、`bytetrack.yaml`、`first_frame.jpg`、`contact_sheet.jpg`、`review.json`、关键帧 `frame_*.jpg`。
- 基线实现与说明：`scripts/run_baseline.py`、`scripts/review_baseline.py`、`requirements-baseline.txt`、`docs/baseline_m1.md`；README 已补运行入口。
- M2 第一步实现与说明：`scripts/run_target_state.py`、`scripts/review_target_state.py`、`tests/test_target_state.py`、`docs/target_state_m2_step1.md`；结果 `outputs/tabletop_02_m2_step1/` 含 `status.mp4`、`frames.jsonl`、`events.jsonl`、`run_info.json`、`review.json`、关键帧/预览及 `baseline_preservation.json`。
- M2 第二步实现：`scripts/appearance_recovery.py`、`scripts/run_recovery.py`、`scripts/review_recovery.py`、`scripts/validate_recovery_fixture.py`、`configs/recovery.json`、`tests/test_appearance_recovery.py`；说明 `docs/appearance_recovery_m2_step2.md`。
- M2 第二步有效结果：`outputs/tabletop_02_m2_step2_v3/`（状态视频、逐帧/事件、参考 PNG/NPZ、配置/校验、核查/身份评价）；关闭结果 `outputs/tabletop_02_m2_step2_disabled/`；模块验证 `outputs/m2_step2_module_validation_v2/`；独立身份记录 `outputs/m2_step2_identity_review/identity_annotations.json`。早期运行结果保留，最终核查以 v3 为准。

02 首次接手实际运行命令（历史；当时真实输入缺失）：

```bash
.venv/bin/python scripts/check_env.py
.venv/bin/python scripts/inspect_video.py --source data/synthetic_io.avi --output outputs/synthetic_io_02_check
```

当时工程代码未修改、真实输入缺失；本轮新增基线与运行结果见下一节。

## 02 本轮 M0/M1 交付（2026-09-30）

已重新读取规则/规格/状态，检查现有脚本、输入与旧输出。接手时 `.gitignore` 的缓存忽略项和未提交的 `run_baseline.py` 已存在，本轮核对后沿用并修正输出索引映射；未创建另一套项目或环境。

本次实际运行的成功命令（项目根目录）：

```bash
.venv/bin/python scripts/check_env.py
.venv/bin/python scripts/inspect_video.py --source data/tabletop_01.mp4 --output outputs/tabletop_01_02_check
.venv/bin/python scripts/inspect_video.py --source data/tabletop_02.mp4 --output outputs/tabletop_02_02_check
.venv/bin/python -m pip install ultralytics==8.3.221 lap==0.5.12 --index-url https://pypi.tuna.tsinghua.edu.cn/simple --timeout 60 --cache-dir .cache/pip
curl -fL --retry 2 --connect-timeout 10 https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt -o weights/yolo11n_official_verify.pt
sha256sum weights/yolo11n.pt weights/yolo11n_official_verify.pt
.venv/bin/python -c 'import torch; print("torch", torch.__version__, "cuda", torch.cuda.is_available()); x=torch.ones((32,32),device="cuda:0"); print("GPU",torch.cuda.get_device_name(0),"matmul",(x@x)[0,0].item())'
.venv/bin/python scripts/run_baseline.py --source data/tabletop_02.mp4 --output outputs/tabletop_02_baseline_v2 --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/review_baseline.py --output outputs/tabletop_02_baseline_v2 --frames 227 693 694 844 845 847 848
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q scripts
```

沙箱内网络解析失败；沙箱外官方 PyPI 下载又超时，最终用清华镜像安装相同固定版本成功。下载/GPU 命令在沙箱外执行；环境检查和读取/输出核查在沙箱内成功。
第一轮基线命令同上但 `--output outputs/tabletop_02_baseline`；实际跑完 984 帧，核查却在 f227 失败：分数子集索引误用为完整检测索引。第一轮保留但不作基线；只修正记录映射后重新运行 v2，原 ByteTrack 与 YAML 未改，验证通过。

实际观察：默认缓冲 30 帧；纸板段 f694—844 连续 151 帧无瓶子检测（估算 23.90—29.10 秒），此前 ID 4，f848 起 ID 5（约 29.20 秒）。f223—229 的 ID 3 是挂包附近误检，已查看 f227。详细证据、版本、算法能力与限制见 `docs/baseline_m1.md`。
650 帧有检测、643 帧有轨迹；本次循环计时约 10.30 秒、95.53 FPS，包含解码/首次推理初始化/关联/绘制/记录/写视频，排除模型加载、GPU 校验与最终编码释放。未做严谨速度基准或身份准确率评价。
M0/M1 交付完成；没有添加恢复策略。尚无测试集与身份/事件标注，ID 变化不能单独作为身份判定或恢复评价。
另实际执行以下错误路径命令，均按预期退出码 1：非空输出拒绝覆盖、缺失输入拒绝运行，旧结果保持原状。

```bash
.venv/bin/python scripts/run_baseline.py --device cpu --source data/tabletop_02.mp4 --output outputs/tabletop_02_baseline_v2
.venv/bin/python scripts/run_baseline.py --device cpu --source data/not_present.mp4 --output outputs/baseline_missing_input_check
```

## 下一项任务：拍摄实际错误瓶子的负例

用户已反馈观看视频、未发现问题（2026-10-01），已记录于 `docs/learning_log.md`。此前讲解了“无框”和新轨迹 ID 的含义；用户理解不由 Codex 代填，后续结合 03 的代码继续学习。
M2 第一步现已完成，用户对状态视频的三处观察已保存至 `docs/learning_log.md`。这些是状态视频的播放器时间，原视频帧号仍保留在逐帧记录中。
用户已用自己的话正确说明候选与身份确认的区别，原话见 `docs/learning_log.md`。
下一项用户任务只有拍摄 `data/tabletop_wrong_bottle_01.mp4`，约 15—20 秒：固定相机和光照，原红盖瓶子清楚可见约 5 秒；纸板只遮住瓶子、背景持续可见；遮挡期间取走原瓶子，换上同样红盖但标签明显不同的瓶子；移开纸板，让替代瓶子清楚可见至少 5 秒，原瓶子不再入镜。附一句说明替换操作。
目的：检验不只凭红色瓶盖接受身份；交付为视频与操作说明；拍摄验收为瓶盖与标签清楚、镜头不被遮住。输入到位后由 03 检查读取并沿用固定检测条件，确认替代瓶子确实形成质量合格候选，再核查拒绝。没有检测到假瓶子不能算外观拒绝通过。
真实不同瓶子拒绝有人工依据后，才能验收本步恢复/拒绝交付；实际双瓶歧义与同包装困难例仍保留待验证。04 可先审查当前代码/输出。接手需重读记录，不把外观启发式称为确定物理身份。

## 待办与交接

1. 用户已完成第一步观看与理解，第二步已完成已有输入的实现/验证；下一项为补拍实际错误瓶子。03/04 接手前必须重新读取记录，原始对照使用 v2，第一轮无效基线不可用于实验。
2. 本轮 M1 代码、依赖与说明本地提交消息为 `feat: add verified YOLO11n ByteTrack baseline`，用 `git log -1 --oneline` 查看；后续每个可运行里程碑仍检查变更并提交。原视频、权重和输出不加入提交。
3. GitHub 代码与两段视频检查说明均已上传并核对；用户已明确授权公开本次检查记录。视频、模型权重和虚拟环境保留本地。
4. 03—05 在基线可检查后按需进入；01 可结合当前读取脚本学习。

未解决问题：实际错误瓶子、真实竞争歧义、同包装替换尚未验证；同外观实体可能误认；质量门槛可能把真实目标暂时判为不可靠；阈值未调优、尚无独立保留测试；可辨认重现帧为 Codex 画面核对，尚非用户逐帧时间标注；输出为 mp4v、无音频，未进行端到端速度对比。

## 03 本轮 M2 第一步交付（2026-10-01）

已重新读取 AGENTS.md、SPEC.md、完整状态与 `docs/baseline_m1.md`，核对 M1 实现、v2 配置/核查和全部记录。接手时工作区干净，HEAD 为 `a7029b5`。本轮沿用现有环境和依赖，不运行模型，不修改原始 M1 脚本或 SPEC.md。更新记录前重新读取并保留了学习聊天新增的“用户已观看基线”反馈。

查看原视频 f600 后，以配置 `--init-frame 600 --init-box 180 450 305 870` 指定红盖瓶子；不是用户已确认的真值标注。人工框与检测框 IoU 约 0.8896，唯一匹配原生轨迹；ID 4/5 和遮挡帧号均未硬编码在状态逻辑中。
连续缺失阈值为可配置的 10 帧，按名义 FPS 估算约 0.3444 秒，尚未调优。达到阈值前保留 TRACKING 决策及 `pending_loss` 标志，但无观察时立即清空当前框；确认丢失后锁定，所有同类检测（即使是原 ID）均仅作未核验候选，不再自动回 TRACKING。

实际成功运行命令（项目根目录，退出码均 0）：

```bash
.venv/bin/python scripts/run_target_state.py --baseline outputs/tabletop_02_baseline_v2 --source data/tabletop_02.mp4 --output outputs/tabletop_02_m2_step1 --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --init-iou 0.5
.venv/bin/python scripts/review_target_state.py --output outputs/tabletop_02_m2_step1 --frames 600 693 694 702 703 844 845 848
.venv/bin/python -m unittest discover -s tests -v
```

- 顺序解码原视频全部 984 帧；保存 f600—983 共 384 帧，原帧号、估算时间、源时间及检测/轨迹均保留。状态视频从 f600 开始，播放器 0 秒对应原 f600。
- TRACKING=103 帧（f600—693 有观察，f694—702 是 9 帧缺失宽限期）；LOST=142（f703—844）；RECOVERY_CANDIDATE=139（f845—983）。事件为 f600 初始化、f703 确认丢失、f845 候选出现。f845 候选没有轨迹 ID，f848 的 ID 5 仍未绑定；所有候选均 `identity_check.performed=false`，`bound_to_target=false`，没有恢复成功结论。
- 记录、缺失阈值、空位置、候选与状态事件、384 帧视频重解码均核查通过。已查看原始初始化帧和 f600/f693/f694/f702/f703/f844/f845/f848 状态预览。
- 8 项状态逻辑 unittest 通过，涵盖阈值边界、宽限期位置未知、其他 ID 不重置缺失、短缺失原生连续性、确认丢失后同 ID 不绑定、未关联/多候选、无效/歧义初始化及任意初始 ID。这些合成输入不是模型效果证据。
- 经 subprocess 实际执行非空输出、人工框不匹配、原视频与基线校验不符的三条错误路径，均退出码 1；无效初始化/错误源视频未创建输出目录。准确命令见 `docs/target_state_m2_step1.md`。
- v2 的全部 14 个文件运行前后 SHA-256 一致，记录保存在新增输出的 `baseline_preservation.json`。关闭新增模块直接使用原始 v2 视频/记录；原始基线入口仍可运行。本轮无身份标注、对照评测、GPU 推理或速度基准。
- 本轮本地提交消息为 `feat: add target loss states and unverified recovery candidates`；用 `git log -1 --oneline` 查看完成后的哈希。不执行远程推送；视频、输出与环境保持 Git 忽略。

详细状态规则、字段、配置、准确命令、实际结果与限制见 `docs/target_state_m2_step1.md`。下一项用户任务见上方：观看状态视频并记录对候选和身份恢复区别的理解。

## 00 M2 第一步交付核对（2026-10-01）

- 已读取规则、规格、当前状态、M2 文档、实现与测试代码，查看状态关键帧拼图。接手时工作区干净，03 本地提交为 `5d5f6fd`。
- 使用一次性 Python 检查逐项比对全部 384 条记录与 v2 原字段，验证原帧号/输出帧号连续、无本帧观察时当前框为空、所有候选 UNVERIFIED 且未核验/未绑定、所有 recovery_confirmed 为 false；事件核对为 f600 初始化、f703 LOST、f845 RECOVERY_CANDIDATE。实际重新解码状态视频得到 384 帧，全部为 720×1280，检查退出码 0。
- 另计算 v2 现存 14 个文件的 SHA-256，与保存的运行前后校验逐项一致，退出码 0。未重跑检测、状态生成或 03 已通过的 8 项测试；本轮为独立输出核对，不修改工程代码。
- f694—702 的 9 帧缺失宽限期仍保留 TRACKING 决策，但 pending_loss=true、position_known=false、当前框为空；该行为符合本步已记录的延迟失效规则，不代表目标仍可见。
- M2 第一步达到预定实现要求，尚无身份恢复结论。用户下一步观看状态视频约 3—9 秒，说明黄框代表待核验候选；身份匹配规则及拒绝错误候选的验证由总控随后确定，继续在 03 实现第二步。

## 03 收到 M2 第一步观看反馈（2026-10-01）

- 用户实际反馈：播放器约 3.24 秒目标框消失、位置 UNKNOWN；约 3.55 秒缺失达到 10 帧并进入 LOST；约 8.44 秒出现黄色 UNVERIFIED 候选。
- 本次使用现有 `.venv/bin/python` 一次性读取 `outputs/tabletop_02_m2_step1/run_info.json` 与 `frames.jsonl`，以 `output_frame_index / nominal_fps` 核对 f694/f703/f845，结果分别约 3.237/3.547/8.437 秒，退出码 0。f694 为 1 帧缺失的宽限期，f703 为 10 帧确认丢失，f845 候选未经核验；用户观察与记录一致。
- 已将本人观察保存到 `docs/learning_log.md`，更新当前待办；未代填用户的理解、身份标注或恢复结论。本轮只修改两份记录，未修改工程代码、依赖、规格或运行输出，不重跑已通过的模型/状态/测试。
- 文档检查命令为 `git diff --check`；本轮交接记录保存为本地提交 `docs: record user M2 state video observations`，不推送远程。原 M2 实现提交为 `5d5f6fd`。
- 下一项用户任务见上方：说明为何未核验候选不能算恢复成功；身份依据与第二步实现范围仍由 00 确定。

## 03 完成候选概念核对（2026-10-01）

- 用户本人说明黄色框只表示瓶子候选，可能是其他瓶子或误检，检测分数高或有跟踪 ID 不能单独确认原目标身份；原话已写入 `docs/learning_log.md`，本步理解核对完成。
- 实际执行 `rg -n 'identity_check|bound_to_target|recovery_confirmed' scripts/run_target_state.py` 并读取 `outputs/tabletop_02_m2_step1/events.jsonl`，核对代码与候选事件仍为未核验、未绑定、未确认恢复。本轮仅核对现有证据，没有重跑模型、状态生成或测试，没有新增结果或性能结论。
- 只更新两份项目记录，执行 `git diff --check`；本地提交消息为 `docs: record understanding of unverified candidates`。不修改工程代码、依赖或规格，不推送远程。
- 下一项用户任务：交由 00 确定第二步身份依据、恢复条件与拒绝错误候选的验证方式，写入 SPEC.md 后由 03 接续实现。

## 00 M2 第二步技术决策（2026-10-01）

- 已读取规则、规格、当前状态、学习记录、M2 文档及 TargetState 核心代码；接手时工作区干净。未修改工程代码、依赖或原始基线。
- 一次性 OpenCV 脚本顺序读取原视频，查看 f227 误检区域与 f600/f620/f670/f845/f848/f880/f950 的检测裁剪，保存 `outputs/m2_step2_planning/appearance_crops.jpg`。可见瓶盖与标签较稳定，f845 仅局部瓶身，挂包外观不同。
- 另做单参考 f600 与选定开发帧的 H-S 分区域直方图/标签灰度相关度探查，结果为 `outputs/m2_step2_planning/descriptor_probe.json`。f848 瓶盖/标签距离约 0.511/0.192、纹理相关约 0.646；f227 约 1.000/0.840/-0.010；f845 约 0.825/0.638/-0.133。命令退出码 0。这只支持起始设计的可行性，不是完整恢复运行、阈值调优或身份性能验证。
- 核对 OpenCV 4.12 官方直方图比较/模板匹配文档，接口出处写入 SPEC.md；区域、分数、门槛与恢复条件为项目设计。
- SPEC.md 已明确参考库只用初始化后的早期合格观察、冻结不污染；候选须有颜色/纹理证据、足够质量、竞争差值与连续5帧确认，才恢复项目目标关联。模板不足、局部/低质候选和歧义均暂缓；外观明显不符拒绝。原生 ID 只作候选跨帧串联依据。
- 验证要求覆盖已有正例、挂包真实裁剪的模块负例、不同瓶子实际负例、歧义暂缓、相同包装困难例和状态回归；真实负例未提供，不能称拒绝能力已验证。包装相同的另一实体可能误认，明确保留失败边界。
- 本轮只更新 SPEC.md 与本交接，做文档检查/本地提交，不推送远程。下一项为 03 按新规格实现第二步，已有输入可先开发；完整验收须补齐实际不同瓶子负例及人工依据。

## 03 本轮 M2 第二步部分交付（2026-10-01）

接手重读规则、规格、状态、第一步实现/测试/结果及规划裁剪。工作区接手时干净，HEAD 为 `4c7a2d6`。本轮新增外观模块、运行/核查/夹具入口、JSON 配置与测试；沿用现有 OpenCV/NumPy，不安装依赖、不重跑模型，不修改 M1/第一步脚本或 SPEC.md。

最终实际成功命令（项目根目录，退出码均 0）：

```bash
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/tabletop_02_m2_step2_v3 --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery.json
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_02_m2_step2_v3 --annotations outputs/m2_step2_identity_review/identity_annotations.json --frames 600 609 691 692 701 845 847 848 851 852 900 983
.venv/bin/python scripts/validate_recovery_fixture.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --recovery-output outputs/tabletop_02_m2_step2_v3 --output outputs/m2_step2_module_validation_v2 --negative-start 223 --negative-end 230 --negative-box 200 120 455 750
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/tabletop_02_m2_step2_disabled --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery.json --disable-recovery
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_02_m2_step2_disabled --frames 600 694 703 845 848
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts tests
```

- 原视频顺序解码 984 帧，第二步输出 f600—983 共 384 帧；视频重解码、原基线字段、冻结参考、连续计数/门槛、绑定事件与位置字段核查通过。已查看原始重现 f845/f846/f847、参考裁剪、接受帧和最终状态预览。原生 ID 不改写，项目 UID 与初始/活动 ID 分开。
- 参数沿用 SPEC.md 起始值，无调优。参考 f600—609 收满 10 个并冻结，不采候选/恢复后画面；轨迹仍在的低质帧跳过，首次轨迹缺失/确认丢失停止建库，不足 5 个不恢复。所有质量合格竞争候选参与排序，最佳 S 的同一参考须通过全部门槛。
- f692 检测分数低于 0.5，清空当前框、位置 UNKNOWN；f701 达连续 10 帧不可靠/缺失并 LOST；f845/f846 暂缓，f847 外观合格但无 ID、计数 0；f848—852 连续 5 帧合格，f852 RECOVERY_ACCEPTED，T1 关联到当前原生 ID。接受后继续门控，参考不更新。
- 1 次丢失、1 次连续确认尝试、1 次程序接受。用户在本聊天明确确认“是，遮挡期间只移动了原瓶子，没有替换”；另存独立物理身份/关键帧记录，结合画面核对计为此开发正例正确接受 1、错误接受 0、未评价接受 0、未恢复事件 0。未推断泛化性能。
- 可辨认重现帧为 Codex 查看原画面后保守指定 f847（红盖/完整标签清楚），尚非用户逐帧时间标注；至 f852 延迟 5 帧，名义 FPS 口径约 0.172 秒，源时间口径约 0.190 秒。不是以首次检测/ID/LOST 事件代替重现标注。
- 挂包模块夹具使用 f223—229 的真实框/像素/分数与构造 LOST 上下文，记录原帧号映射，不冒充端到端错误瓶子实验。f224/f225 质量合格且外观拒绝；其余 5 帧低分质量暂缓，均无绑定。重复参考裁剪构造的两项等分候选连续 6 帧均暂缓，非真实双瓶实验。参考校验保持不变。
- 23 项 unittest（第一步 8 + 新 15）通过，覆盖因果/冻结/不足参考、最佳参考与失败竞争候选、门槛边界、同 ID 高分错外观、无 ID/短确认/ID切换/空间跳变、歧义/重复 ID、退化模板、恢复后再次丢失；相同图像代表另一实体的构造测试明确外观无法区分的边界，未称为真实困难例。
- 关闭模块输出 384 帧，与第一步全部原有字段逐项一致，0 接受。v2 与第一步共 29 个文件运行前后及核查时 SHA-256 一致。早期第二步运行目录及模块夹具保留，最终数据/代码校验使用 v3 和模块验证 v2。
- 本轮本地提交消息为 `feat: add frozen appearance recovery with validation evidence`；视频、参考、标注、报告等运行输出按 Git 忽略留本地，不推送远程。准确配置、输出字段、结果与限制见 `docs/appearance_recovery_m2_step2.md`。

本步为部分完成：缺少真实不同瓶子合格候选的拒绝验证，真实双瓶歧义/同包装替换与 M3 独立测试仍未运行。用户下一项只有拍摄上方不同标签瓶子的替换负例，不把未运行项目写为通过。

## 历史交接记录

以下各段保留当时的输入、Git 与实现状态；它们不表示当前进度，当前结论与本轮交付见上方。

## 05 接手检查（2026-09-30）

- 已读取 `AGENTS.md`、`SPEC.md`、本文件、README、拍摄说明、学习记录、依赖与忽略规则，以及全部三个现有脚本。05 负责根据实际交付整理运行说明、演示、实验结果和已知限制。
- 实际执行 `rg --files --hidden --no-ignore data outputs docs scripts`，并读取三组已有 `video_info.json`：项目中只有 `data/synthetic_io.avi` 和合成 I/O 结果，均记录 640×360、名义 20 FPS、100 帧、估算 5 秒。没有真实桌面视频、带跟踪框视频、逐帧检测/跟踪结果或恢复实验。本次只核对已有结果，没有重跑环境检查、视频读取或查看首帧图像。
- 实际执行 `git status --short`、`git log -3 --oneline`、`git remote -v`、`git diff -- STATUS.md`：最新提交为 `bb7cc53`，未配置远程；接手时本文件已有其他聊天的未提交记录，已保留。
- 当前 M4 尚不具备完成条件。现有 README 与实现能力一致；最终整理应依据 M1—M3 的实际输出补齐运行命令、模型与跟踪器配置、演示视频、身份判定依据、对照结果和失败案例，区分原始基线、新增工程模块与待验证想法。整理前须重新读取项目记录并核对输出。
- 本次仅更新交接记录，未修改工程代码、依赖、规格或 README；未生成新的运行结果，没有新增可运行里程碑，未创建 Git 提交。
- 下一项用户任务：按 `data/README.md` 拍摄并放入 `data/tabletop_01.mp4`。目的为提供真实检测与跟踪输入；交付为约 15—25 秒的固定相机桌面视频；内容验收为目标初始可见，包含遮挡、重现及遮挡期间位移。随后由 02 运行读取检查，保存首帧与视频信息，再推进基线。

## 03 接手检查（2026-09-30）

- 已读取适用的 `AGENTS.md`、`SPEC.md`、本文件、README、拍摄说明、学习记录，以及现有环境检查与视频读取代码。
- 实际执行 `rg --files --hidden --no-ignore data outputs` 核对本地输入与结果：只有合成视频及两组 I/O 输出，没有真实桌面视频，也没有检测、跟踪或恢复输出。
- 实际读取两份合成 `video_info.json`，均记录 640×360、20 FPS、100 帧、估算 5 秒；本次仅核对已有结果，没有重跑视频读取或环境检查。
- 实际执行 `git status --short`、`git log -1 --oneline`、`git remote -v`：检查时工作区干净，最新提交为 `bb7cc53 chore: initialize video I/O baseline and project handoff`，没有配置远程。
- 本次只更新交接状态，未修改工程代码、安装依赖或选择模型；没有产生新的运行结果或可运行里程碑。
- 下一项用户任务仍是按 `data/README.md` 准备真实视频并放为 `data/tabletop_01.mp4`。随后由 02 完成读取检查和 M1 基线，交付准确命令、带框视频、逐帧结果及原始跟踪器能力说明。
- 03 开始实现前需重新读取项目记录并核对基线输出，再确定目标身份依据和失效/恢复条件；实现需保留关闭新增模块的方式，完全不可见时明确位置不确定。

## 04 首轮独立审查（2026-09-30）

已重新读取项目规则、规格、状态、README、教学与学习记录，并核对全部现有脚本和本地输入/输出。工程代码未修改，未安装依赖，未确定新技术方案。

实际执行命令（项目根目录）：

```bash
rg --files -uu -g '!.venv/**' -g '!.git/**'
git status --short
git log -5 --oneline
git diff -- STATUS.md
git remote -v
.venv/bin/python scripts/check_env.py
.venv/bin/python scripts/inspect_video.py --source data/synthetic_io.avi --output outputs/synthetic_io_04_review
```

- 环境检查与合成视频读取均退出码 0；沿用项目 `.venv`，Python 3.12.3、OpenCV 4.12.0（发行包 4.12.0.88）、NumPy 2.2.6。本会话仍无法查询 GPU；PyTorch GPU 运算未验证。
- 新结果：`outputs/synthetic_io_04_review/video_info.json`、`outputs/synthetic_io_04_review/first_frame.jpg`。实测成功解码 100 帧，640×360、名义 20 FPS、估算 5 秒，与两组既有 JSON 一致；已查看新首帧，内容符合生成脚本中的方块与遮挡矩形。旧结果保留，未重跑历史错误路径检查。
- 接手时 `STATUS.md` 已有 03 的未提交记录；本次保留。当前最新本地提交仍为 `bb7cc53`，远程查询无输出。本次为审查与记录更新，没有新增可运行里程碑，未创建提交。

审查发现与证据边界：

| 事项 | 可复核证据 | 结论与下一步 |
| --- | --- | --- |
| 真实输入缺失 | 项目 `data/` 只有合成视频和说明 | M0 尚未验收；用户先准备 `data/tabletop_01.mp4`，由 02 检查读取 |
| 方法实现与结果缺失 | 现有三个脚本只检查环境、生成合成视频和读取视频；输出只有首帧与视频信息 | 尚不能审查身份错误、失效状态或恢复表现；等 M1/M2 实际交付后再审查 |
| 对照实验依据缺失 | 尚无开发/测试划分、人工标注、模型/跟踪器配置和逐帧方法结果 | 目前无性能结论；在评测前补齐身份与事件依据、指标定义及公平对照条件 |

现有 I/O 输出与文档对能力边界的表述一致。本轮没有确认需要修复的工程缺陷；这不代表尚未实现的跟踪或恢复模块通过审查。

下一项用户任务仍只有准备真实桌面视频，拍摄要求见 `data/README.md`。交付为 `data/tabletop_01.mp4`；验收为固定相机、约 15—25 秒，能看清目标初始外观，包含遮挡、重现及遮挡期间位移。随后由 02 完成读取与基线，本聊天再审查其实际输出；接手前必须重新读取项目记录。

## 00 下一项任务确认（2026-09-30）

重新读取项目规则、规格与状态，并检查 README、学习记录、`data/`、`outputs/` 和 Git 状态。
三个交接文件及首次本地提交已存在，沿用其他聊天的工作；真实视频仍未提供，远程仍未配置。
本次仅追加状态记录，保留已有未提交记录；没有修改工程代码或产生新的运行结果。
用户当前只需拍摄并放入 `data/tabletop_01.mp4`。文件到位后由 02 完成 M0 读取验收，再推进 M1；GitHub 地址可随后补充。

## 00 GitHub 首次上传准备（2026-09-30）

用户截图提供新建公开空仓库：`https://github.com/shuiliufu-design/occlusion-aware-tracking`。
已配置准确的 HTTPS origin；`git ls-remote` 退出码 0，未返回远程引用，确认仓库为空。
GitHub 连接器可读取仓库元数据，但返回 `push: false`；命令行上传权限须另行验证。
已检查所有 Git 跟踪文件，只有代码、文档、依赖清单与目录占位文件；没有视频、模型权重或 `.venv`。
保留并纳入已有聊天的交接记录。下一步提交文档、使用 main 分支，并尝试常规推送，不使用强制推送。

首次推送实测：已将分支改名 main，并完成文档提交 `c2491da`。
执行 `env GIT_TERMINAL_PROMPT=0 git push -u origin main`，退出码 128，
提示无法读取 HTTPS GitHub 用户名；本会话缺少可用命令行认证，尚未上传任何提交。
下一步由用户在本机完成 GitHub CLI 登录；无需在聊天中提供密码、token 或验证码。
认证完成后重试 `git push -u origin main`，再比较远程 main 与本地 HEAD。

## 00 GitHub 首次上传完成（2026-09-30）

用户完成 GitHub CLI 登录后，联网执行 `gh auth status --hostname github.com`，确认账号为 `shuiliufu-design`，HTTPS 认证有效。
执行 `env GIT_TERMINAL_PROMPT=0 git push -u origin main`，退出码 0，远程 main 创建成功，本地 main 已跟踪 origin/main。
执行 `git ls-remote origin refs/heads/main` 与 `git rev-parse HEAD`，均返回 `f51130e4cd8f899e896615bac58423e010e80c87`，确认首次上传内容与本地提交一致。
随后更新本文件与第一课 GitHub 说明，并提交、推送说明更新。工程代码与依赖未修改，无需重跑已有 I/O 检查。
下一项任务：用户准备 `data/tabletop_01.mp4`，由 02 完成真实视频读取验收，再推进跟踪基线。

## 00 首段真实视频检查（2026-09-30）

- 用户提供 `video_2026-09-30_21-59-11.mp4`；复制为 `data/tabletop_01.mp4`，原文件保留。两份文件 SHA-256 均为 `2b620011fa6b79619d1faadde76400e23a798e1f88872e4e8bf938808bb3db5c`。
- 实际执行 `.venv/bin/python scripts/inspect_video.py --source data/tabletop_01.mp4 --output outputs/tabletop_01`，退出码 0；成功解码 656 帧，720×1280，名义 28.7544977606 FPS，估算 22.814 秒。沿用既有环境与工程代码，未安装新依赖。
- 另用一次性 OpenCV 脚本顺序解码，每约一秒按帧索引/名义 FPS 抽取一帧，生成 23 张缩略图组成的 `outputs/tabletop_01/contact_sheet.jpg`。已查看首帧和该预览：竖屏方向正常，目标为红盖瓶子；约 6—7 秒、14—17 秒几乎整幅画面被遮住，约 18 秒后瓶子出现在更远的新位置。上述时间是抽帧估算，不能当作事件标注或模型效果。
- 保留首段用于基线开发及画面中断样例。M0 的脚本读取部分已通过，用户对首帧和内容的确认仍待补充；主要目标遮挡场景还需补拍。
- `git check-ignore` 已确认视频及全部检查输出被忽略，仅提交说明更新。视频读取停止仍可能为正常结尾或解码失败，未做完整性保证。
- 下一项用户任务：按 `data/README.md` 补拍 `data/tabletop_02.mp4`，手/纸板靠近瓶子、只遮住目标，背景保持可见。由 02 重新读取本记录，检查补拍并推进 M1；无需重新初始化 Git 或环境。
- 本次检查说明已保存为本地提交 `ef017c1`，尚未同步到 GitHub。自动审批拒绝了 `git push`：说明中含私人视频派生的尺寸、时序观察和校验信息，公开这些记录需要用户明确同意。当前远程仍是上次已验证的 `380841e`；视频和输出没有加入 Git。等待用户选择公开检查记录或只保留本地，再决定同步方式。

## 00 补拍视频检查（2026-09-30）

- 用户提供 `video_2026-09-30_22-10-01.mp4` 并说明补拍了靠近瓶子的遮挡及遮挡期间位移。复制为 `data/tabletop_02.mp4`，原文件与首段均保留；原件/副本 SHA-256 一致，为 `5a6ca2cfcc5089cd1099815cf2bb0fa05468d9deae212cfb9821833a970fcaa5`。
- 实际执行 `.venv/bin/python scripts/inspect_video.py --source data/tabletop_02.mp4 --output outputs/tabletop_02`，退出码 0，720×1280、984 帧、名义 29.0377221520 FPS、估算 33.887 秒。未修改工程代码或依赖。
- 一次性 OpenCV 脚本顺序解码并按帧索引/名义 FPS 每约一秒抽帧，保存 34 张缩略图组成的 `outputs/tabletop_02/contact_sheet.jpg`，已查看。约 6—7 秒与 14—17 秒仍是镜头遮挡；约 18 秒后视角与目标位置变化，后半段约 24—29 秒纸板挡住瓶子，周围背景可见；约 30 秒后红盖瓶子在新位置重现。时间为抽帧估算，尚无精确事件标注或身份评价。
- 后半段符合目标遮挡与位移的开发场景，约 34 秒的总长度可以使用，无需为长度或竖屏再次补拍。用户对生成预览的确认仍待补充，但基线开发不依赖追加拍摄。
- `git check-ignore` 确认视频及全部输出被忽略。说明仅本地保存；用户尚未回答上一条公开检查记录的授权问题，本轮不尝试推送。
- 下一项任务交给 02：重读 AGENTS.md、SPEC.md、STATUS.md 和实际输入，在补拍视频上实现并运行 M1 原始检测/跟踪基线，解释输入→检测→关联→带框视频/逐帧记录的数据流。

## 00 再次请求同步（2026-09-30）

用户回复“我要上传到github上”。已检查工作区干净、origin 正确、待推送三个提交只改动六份 Markdown 文档，视频与预览未跟踪。
尝试 `env GIT_TERMINAL_PROMPT=0 git push origin main`，自动审批在执行前再次拒绝：其认为上传项目的表述尚未明确授权公开私人视频派生的尺寸、遮挡时序与校验信息。
没有实际推送或绕过拒绝；待用户明确同意公开这两段视频的上述检查记录后再推送。原始视频、预览和环境继续保留本地。

## 00 视频检查记录公开同步完成（2026-09-30）

用户明确回复：“同意将两段视频的检查记录，包括尺寸、遮挡时间观察和校验信息，公开到 GitHub”。本次授权覆盖这两段检查记录，不包含原视频或预览文件。
实际执行 `env GIT_TERMINAL_PROMPT=0 git push origin main`，退出码 0，将远程从 `380841e` 更新至 `813a522`。
随后 `git ls-remote origin refs/heads/main` 与 `git rev-parse HEAD` 均返回 `813a52250dfe669d89251cb3ffd320d94829e2c4`，确认待上传的四个文档提交已同步。
本次仅更新同步完成状态并继续提交/推送；工程代码与依赖未修改，无需重跑视频检查。下一项技术任务仍是由 02 使用补拍视频推进 M1 基线。

## 00 M1 核对与 M2 第一步安排（2026-10-01）

- 已读取规则、规格、完整状态、M1 说明、学习记录与 run_baseline.py；实际读取 v2 run_info.json 和全部 984 行 frames.jsonl，抽查 f223/f227/f693/f694/f844/f845/f847/f848。
- 记录与 02 报告一致：f693 有 ID 4，f694/f844 空检测，f845 有检测但无关联 ID，f848 有 ID 5；f227 有主瓶子 ID 2 与挂包区域误检 ID 3。本轮没有重跑模型、视频核查或查看关键帧图片，因此身份/误检的视觉判断沿用 02 已查看画面的记录。
- 本地工作区接手时干净，M1 提交 `948f8c7` 尚未推送；本轮只更新总控决策与交接文件，不修改工程代码或同步远程。
- 下一步已写入 SPEC.md：03 先做人工指定目标、连续缺失判断与恢复候选输出。初始化帧/框、缺失阈值均可配置并记录，不硬编码本视频 ID 或事件时间；保持检测/ByteTrack 条件与 v2 对照一致。
- 第一步验收：状态视频能展示指定瓶子消失后的丢失与重现后的候选；隐藏时当前位置未知，检测分数与身份证据分开保存，未经检查的候选不会自动获认原目标。该步骤完成不代表 M2 全部验收，身份匹配与恢复留给第二步。

## 00 用户基线观看反馈（2026-10-01）

用户本人说明已观看视频、未发现问题。已记录原话，未将该反馈扩写为正式身份标注、恢复成功或无误检结论。
本次仅更新学习与交接记录，没有重跑基线或修改工程代码；下一项任务仍由 03 按 SPEC.md 完成 M2 第一步。
