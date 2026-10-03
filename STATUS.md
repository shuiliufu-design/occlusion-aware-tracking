# 项目状态

更新日期：2026-10-03（Asia/Shanghai）。协调聊天：00｜项目总控；第一版M0—M4及GitHub同步已完成，整个项目44条开发历史作者/提交者已修正为shuiliufu-design。线上提交API、Contributors及首页实际核查通过，原始实验Git档案仅本地保留，完整74份工程文件保持。证据outputs/git_identity_rewrite_v1/，冻结/参数/结果与其他聊天未提交讨论保持；本次状态记录正常同步，下一项新范围尚未安排。

## 当前结论

2026-10-03三片独立输入分别341/476/573帧、约11.365/15.864/19.097秒，均720×1280；原件/副本/全部三片开发排除、缓存与前段初始化不变。人工每组两个期待返回及一次零机会替换：C f214相对保守锚点f204延迟10帧（名义0.333278秒/源0.333333秒），C f283相对f279延迟4帧（名义0.133311秒/源0.133289秒）；A/B均未返回。C整瓶可见时仍在f210—213/f280—282等待连续确认，固定样本f210/f280计UNKNOWN。替换片原瓶未再入镜，C完整区域130合格拒绝/0绑定；手持与f442局部完整框未评价。179原标签不改，追加2张原图不扩141固定样本或88清楚T1分母；没有第二位人类逐帧复核。第一/第三片拍摄偏差保持，完整率/速度/困难例限制保留。先前13-21-42原片仍作补充记录。

00已复核确认以上主要实测与来源/补标/失败边界，支持所测范围内的工程改进。第一片实际连续无检测31帧超过缓冲30，不证明短于缓冲的优势；不能将三片结果写成普遍100%恢复或130次独立拒绝实验。05的第一版整理与实际运行核查现已由00验收，M0—M4受限交付完成；全新安装、速度及泛化仍未验证。当前不继续修补外观规则、不新增困难例或速度工程；第一版代码与文档现已同步GitHub，下一项范围由00另行决定。

M0 已验收：02 重新读取两段视频并核对本次首帧，用户明确说明“补拍视频已检查”，作为补拍方向与内容确认。补拍后半段包含背景持续可见的瓶子遮挡与位移。
M1 已实际跑通并通过输出核查：YOLO11n + 未修改的 Ultralytics ByteTrack，补拍视频的 984 帧均处理、记录并重新解码检查一致。有效结果为 `outputs/tabletop_02_baseline_v2/`。
纸板遮挡前 ID 4，长遮挡与位移后输出新 ID 5；保留背景挂包附近误检为瓶子的 ID 3。
M2 第一步已实际运行：复用 v2 与原视频，人工框配置初始化目标，输出 TRACKING / LOST / RECOVERY_CANDIDATE。有效输出为 `outputs/tabletop_02_m2_step1/`，384 条记录与状态视频重解码一致；f703 确认丢失，f845 出现未经身份核验的候选。该步保留为仅候选对照，不执行自动恢复。两段当前都用作开发输入，尚无独立测试集；第二步的受限验收结论见本轮 04 审查。
00 已独立核对本步记录、事件、视频重解码与关键帧预览，M2 第一步达到预定实现要求。用户已反馈本步视频约 3.24 秒位置 UNKNOWN、3.55 秒进入 LOST、8.44 秒出现 UNVERIFIED 候选；03 核对已有记录一致。用户也已明确说明候选可能为其他瓶子或误检，分数/ID 不能单独确认身份，本步观看与理解核对均已完成。
M2 第二步已按 SPEC.md 实现并运行，参数沿用起始值：冻结 f600—609 的 10 个参考，候选多项外观门控、竞争排除与连续 5 帧确认，恢复后继续门控。有效输出 `outputs/tabletop_02_m2_step2_v3/`：f848—852 连续合格，f852 接受并将 T1 关联到新原生 ID；用户确认遮挡期间只移动原瓶子、未替换，独立身份记录支持该开发正例正确接受 1 次。挂包模块负例 2 帧外观拒绝、5 帧质量暂缓、0 绑定；构造等分候选暂缓。23 项测试与视频/证据核查通过，关闭模块退回第一步。这是初次交付时的证据，新增真实不同瓶子验证见下一段；真实双瓶歧义、同包装困难例仍未验证。

用户新提供 `video_2026-10-01_22-41-54.mp4`，确认换成另一只瓶子且原瓶子未再入镜。复制为 `data/tabletop_wrong_bottle_01.mp4`，633 帧读取/固定条件基线/状态视频一致；输出 `outputs/tabletop_wrong_bottle_01_m2_step2/`。人工清楚可见区间 f485—632 的 148 帧都有质量合格候选且全部外观拒绝，0 接受、0 错误当前位置，原像素重算一致；整次含 f484 共149个拒绝候选。关闭模块与原 TargetState 的633帧原字段逐项相同，旧84个输出文件不变，31项测试通过。参数/核心代码与原正例一致。04 已从原像素重算、完整回放状态与核对独立身份记录，确认恢复与拒绝开发证据满足本步验收；本片全镜头遮挡、瓶盖门槛也失败及f180可见目标提前UNKNOWN的限制保留，不推广为可靠性结论。04发现旧关闭run_info的loss_episodes=0错误；03已另存两组修复后关闭v2，各正确记录1次丢失，旧错误报告保留供溯源。

用户已完成真实负例末段约16—21秒的观看，提供f544/18.19秒截图；T1活动ID为空、missing=365、位置UNKNOWN，候选ID2外观拒绝、确认计数0、未绑定。03读取现有记录核对一致；本帧没有T1已绑定绿色框。04 已查看该截图并核对记录与校验，观看反馈保留，不重复要求观看。

03本轮仅修复关闭统计：当前结果 `outputs/tabletop_02_m2_step2_disabled_v2/`、`outputs/tabletop_wrong_bottle_01_m2_disabled_v2/`，确认丢失帧f703/f191，各loss_episodes=1、0尝试/接受。384/633帧的全部记录、事件、视频SHA与旧输出一致；新核查和35项测试通过，旧输出及04审查证据184文件未变。详见 `docs/m2_disabled_statistics_fix.md`、`outputs/m2_disabled_stats_fix/fix_report.json`。

00上一轮已读取04审查与修复证据，独立核对审查JSON校验、新关闭run_info/review校验及逐帧确认丢失集合；两组确实各1次。SPEC.md已写入处理顺序、评价任务验收与M3预定三片/三组协议；当轮并未实施评价修复、f180修正、配置冻结或M3实验。

03随后完成统一评价入口，实际输出 `outputs/m2_evaluation_v1/`：正例开启正确恢复1、关闭未恢复1；负例两组均无返回机会、不计恢复失败，开启148帧合格拒绝属于1个事件、全程149候选另列，关闭外观核验不适用。f180失败与未标注全片误报率分别记FAIL/UNEVALUATED；54项测试通过，历史来源与旧输出保全通过。详见下方本轮交付及 `docs/offline_evaluation_m2.md`。

00在2026-10-02已核对通过该评价交付：从四组384/384/633/633条记录、独立标注与事件重算关键指标，362文件SHA与Git历史代码匹配，重跑当时新增19项评价测试通过。54项全套测试及源视频/状态/负例像素回放为03证据，该轮未重跑。f180原图仍可见；只读有界平移探查支持一种候选修正，当时尚未运行新状态策略。证据 `outputs/m2_evaluation_00_review/`。

03随后按该任务完成开发候选：在先行固定的f170—195原图诊断中，新规则清楚可见UNKNOWN由1/11降至0/11；f181—186局部质量不可靠与f188—195全遮挡仍全部UNKNOWN，f187边界不确定保留未评价。正例仍f852正确恢复1次，负例148帧合格候选仍全拒绝、0绑定/错误位置；旧默认与关闭逐字段/事件/视频SHA回归完全一致，366个旧文件保全。最终结果 `outputs/f180_alignment_dev/comparison_v2.json`、`verification_v2.json`；70项全套和完整原像素/历史状态核查为03实际证据，00本轮复核范围见下方，04尚未重跑此修正。

00在2026-10-03核对通过该修正，采纳新配置作为M3 C组候选；M2受限开发收尾完成，进入M3准备。下一项只补齐三组共同入口并在开发输入预演，重点公平记录原生短时返回与自定义恢复接受；预演核对通过后冻结，再另拍3段独立视频。没有在本轮改变默认配置、工程核心或启动独立测试。

03随后完成共同入口及开发预演v4；00核对通过其共同口径/来源/保全，并另存正式FROZEN清单。其后采集的三段新片完成登记/独立标注后已运行冻结三组，见顶部及本轮交付；上述“不拍新片/待冻结”描述为此前任务状态。冻结与小规模实测均不等于算法泛化验收。

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
| M2 第二步初次开发验证 | 最终 v3 输出/重解码各 384 帧，开发正例尝试/程序接受/有独立依据正确接受各 1；挂包模块负例 2 拒绝、5 暂缓、0 接受；关闭恢复与第一步逐项一致；23 项 unittest 通过；v2 与第一步共 29 个文件校验一致 |
| M2 真实不同瓶子验证 | 新片633帧；人工区间148个合格候选均拒绝，原像素逐帧重算一致，0绑定/错误当前位置；用户替换操作确认独立于分数；新旧固定条件一致，旧84文件保全，31项测试通过。见 `wrong_bottle_validation_v2.json` |
| M2 统一离线评价 | 03提交8975df7的四组评价符合人工分母与范围要求；00独立记录/来源核对、362文件校验及新增19项评价测试通过，f180 FAIL与全片UNEVALUATED保留；54项全套及像素/视频回放属于03运行证据 |
| f180有界纹理对齐开发回归 | 开发配置下f180当前位置通过；固定可见窗1/11 UNKNOWN降为0/11，邻近质量暂缓/全遮挡不回填；正例正确1、负例148合格拒绝且0绑定；旧默认/关闭完全一致、366旧文件保全、70项测试通过。默认未切换、配置未冻结、M3未启动 |
| M3共同入口与正式冻结 | 03版本572de8f六组开发预演及98项测试通过；00独立核对记录、881既有文件/75评价输入SHA、12张原图及28项相关测试通过。正式清单m3_v1核查FROZEN/PASS；开发抽样6/103、全片未评价等历史限制保留 |
| M3 HOLDOUT输入与独立标注 | 三片登记/初始化/原图/时间轴/缓存核查通过，141固定样本+38关键帧，179标签原图逐像素一致；110项全套测试（新增12）通过，1,040旧文件保全。每片公共缓存一次、总1,390帧；输入准备PASS，三组效果NOT_STARTED，速度UNVERIFIED |
| 00 HOLDOUT输入准备复核 | 12项相关测试及全量输入核查再次通过；另重算推理前清单/来源/179图SHA、141网格/机会数、12冻结执行文件/共同规则，抽查18个不同原帧和6幅重合人工框QA。采纳进入三组运行，未重跑模型/三组/全套110项；缺框、保守边界、拍摄偏差及无第二人类复核均保留 |
| M3三片冻结HOLDOUT实测 | 最终v2九组4170行/视频帧；C正确返回2、A/B各未返回2、一次替换130合格拒绝/0绑定；UNKNOWN固定C2/88、A/B34/88。v1/v2状态/事件/视频像素一致；110项测试、1386原旧文件及1529含初轮保全通过，速度UNVERIFIED |
| 00冻结HOLDOUT实测复核 | 28相关测试及新目录评价通过，九组历史回放/视频/负例原像素/181标签图核查；独立复算4170记录主要指标、v1/v2记录/事件/视频SHA、179旧标签、12执行文件及1529旧文件SHA保持。抽查6原PNG，确认接受框和等待失败；M3受限效果交付采纳，下一项M4整理 |
| M4第一版整理与00验收 | 05完成独立目录633帧流程及九演示4170帧核查；00另核对70提交文件、633行三组、重解码1899帧、关闭回放、静态来源/演示链接、12冻结文件与1702旧文件SHA，PASS。沿用已有环境，全新安装未验证；见docs/m4_acceptance_00.md |
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

- 新真实负例：`data/tabletop_wrong_bottle_01.mp4`；读取/原始预览/身份记录 `outputs/tabletop_wrong_bottle_01_input/`；原始模型结果 `outputs/tabletop_wrong_bottle_01_baseline/`；恢复结果 `outputs/tabletop_wrong_bottle_01_m2_step2/`；关闭结果 `outputs/tabletop_wrong_bottle_01_m2_disabled/`。
- 真实负例核查：`scripts/validate_wrong_bottle.py`、`tests/test_wrong_bottle_validation.py`、`docs/wrong_bottle_m2_validation.md`；当前专项报告为 `wrong_bottle_validation_v2.json`，早期报告保留；汇总/关闭等价/旧84文件保全见 `comparison_and_preservation.json`。
- 当前统一离线评价：`scripts/evaluate_offline.py`、`scripts/evaluation_sources.py`、`configs/m2_evaluation.json`、`tests/test_offline_evaluation.py`、`docs/offline_evaluation_m2.md`；结果 `outputs/m2_evaluation_v1/`，旧 `evaluation.json` 不参与新汇总。
- 有界纹理对齐开发配置/复核：`configs/recovery_f180_dev.json`、两份 `configs/m2_evaluation_f180_*.json`、`scripts/review_alignment_development.py`、`tests/test_texture_alignment.py`、`docs/f180_alignment_development.md`；结果 `outputs/f180_alignment_dev/`，最终采用 `comparison_v2.json`、`verification_v2.json` 和两份 `evaluation_*_v2/`；首轮报告也保留。

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

## 第一版同步与提交身份修正完成

05已按 `docs/github_first_version_task.md` 正常同步已验收工程与说明。实际远程main包含00验收c2be7f8，线上README/运行说明/实验表/验收说明与已提交内容一致；证据与准确命令见下方同步记录及 `outputs/github_first_version_sync_v1/`。原历史与本地媒体/资源保持，其他聊天未提交内容保留；本任务自身状态提交亦正常同步。第一版当前范围已完成，下一项范围由00根据用户目标确定，不自动启动新研究。

随后按用户明确授权完成整个项目的历史提交身份修正；上述c2be7f8等原SHA仍是当时真实证据，公开对应版本见docs/git_commit_map.json。本机私有档案及新克隆导入后均能复查原SHA。GitHub所有公开提交author/committer已关联本人账号，Contributors只含shuiliufu-design，首页不含旧身份；该项已完成，不自动启动后续研究。

原拍摄计划与技术目标保留如下供溯源；不是当前补拍要求，实际偏差按SPEC最新决策与输入检查记录报告：

交付：三段分别新录、不剪辑的原视频及各一条拍摄者物理操作确认。固定手机、瓶子直立/标签朝相机、背景始终可见，纸板靠近瓶子只挡目标；每段操作前后分别清楚展示至少5秒。第一段短遮挡约0.3—0.5秒后原位露出同一瓶子；第二段长遮挡约3—4秒期间移动原瓶子约一个瓶身宽度；第三段长遮挡约3—4秒期间取走原瓶子，换成同盖色、标签明显不同的另一瓶子，原瓶子此后不入镜。详见 `docs/m3_holdout_recording.md` 与SPEC当前唯一任务。

验收：三份新文件可解码，早期初始化/操作/后段可检查且附物理确认；保留每项第一条技术可用拍摄，算法失败也作为正式结果，不按效果重拍或筛片。用户提供本地路径即可。三片只是最小对照，不能支持大样本泛化结论。

后续接手先重新读取AGENTS/SPEC/STATUS、正式冻结、实测与00复核及M4任务，保留已登记初始化/标注/一次公共缓存/所有原输出。只整理和验证现有入口，不能看到结果就重选初始化或改变冻结规则；真实双瓶/同包装压力测试仍未验证。

## 待办与交接

1. 第一版代码/文档及历史提交身份修正已完成，线上Contributors已仅显示shuiliufu-design。用户下一项小任务：刷新仓库首页，亲自确认贡献者头像/名称为自己的账号；交付为页面观察，验收为与00的实际API/首页核查一致。研究下一项范围另行确定，原性能边界保留。
2. 本轮 M1 代码、依赖与说明本地提交消息为 `feat: add verified YOLO11n ByteTrack baseline`，用 `git log -1 --oneline` 查看；后续每个可运行里程碑仍检查变更并提交。原视频、权重和输出不加入提交。
3. GitHub 代码与两段视频检查说明均已上传并核对；用户已明确授权公开本次检查记录。视频、模型权重和虚拟环境保留本地。
4. 03—05 在基线可检查后按需进入；01 可结合当前读取脚本学习。

已知问题与限制：旧两组关闭报告错误零计数已另存新v2修复；旧通用evaluation固定PENDING_INPUT/整体验收false已由独立新评价入口替代，原文件保留，不参与新汇总。真实竞争歧义、同包装替换未验证；新背景持续可见的不同瓶子已在130合格区域验证拒绝，但局部完整几何/困难例未评价；同外观实体可能误认；旧默认f180 UNKNOWN失败保留，新开发配置仅在已标注诊断范围改善，未推广为全片零误报；开发负例瓶盖/标签门槛也失败，未隔离纹理贡献；新增搜索开销未做严格速度基准；三片冻结对照已完成，但小样本不支持泛化，全片误报率仍未评价；两片拍摄偏差、局部完整框不足、保守边界及Codex标注无第二人类逐帧复核保留；输出mp4v、无音频。

## 00 项目提交身份修正（2026-10-03）

用户先询问提交作者/贡献者为何不属于自己的账号，并提供Emails设置截图；00核对全局Git作者误配置，已先只修正本项目.git/config，姓名shuiliufu-design、邮箱232509668+shuiliufu-design@users.noreply.github.com。随后用户明确要求整个项目的所有历史提交/贡献者均使用自己身份，并询问Contributors能否修改，授权本次完整历史身份修正。

实际远程/本地起点69a9c3d710bc70b37b16f02a37e4c95f7b376292，只有main、无标签/PR/分叉；GitHub账号API核对login/id与noreply一致，当前权限admin/push。44条历史author/committer均为同一误配置身份，没有其他作者或签名/合并标签。准备的修正版c5d549764232398fb8ffbe468f57b8ccb1afe67a逐条tree/说明/日期/父顺序相同；44版本文件内容也未包含误配置账号名称。

原历史已保存至私有refs/archive/identity-before-20261003及outputs/git_identity_rewrite_v1/original_history.bundle，bundle核查通过；原始工作区与未提交差异亦备份，记录1857旧本地数据/权重/输出SHA。公开docs/git_commit_map.json保留原始/公开SHA及相同tree，不改写原冻结/结果来源。严格实验复查在本机使用原对象；新克隆导入本地档案后恢复原SHA查找，说明docs/git_history_identity.md。

最终实际验证与发布完成：本机及新的临时克隆冻结检查均FROZEN/PASS；45条公开历史author/committer均为正确身份，74份工程文件与提交逐字节一致。新克隆先验证44原始作者提交对象不存在，再导入本地bundle，44原版本tree可复查且main不变；1857旧本地文件SHA与全局配置均保持。没有重新推理模型/重跑算法全套或新装环境，原效果与限制保持。

按精确lease实际更新远程main：69a9c3d → 61d3078fd9d2ab6e7fe727bb3d8b505b6461ae0a。在线核对PASS：该远程SHA与本地一致，45条完整提交的author/committer账号均为shuiliufu-design，9份工程/说明通过GitHub Contents API逐字节一致；Contributors API只返回shuiliufu-design，首页HTTP200且HTML不含旧身份名称。只推送main，私有archive/prepared引用没有公开；未删除重建仓库，没有篡改冻结果或算法。

准确主要命令（根目录；准备脚本/报告在本地证据目录，原输出不可覆盖）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/git_identity_rewrite_v1/prepare_history.py
git update-ref refs/heads/main c5d549764232398fb8ffbe468f57b8ccb1afe67a 69a9c3d710bc70b37b16f02a37e4c95f7b376292
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/git_identity_rewrite_v1/verify_fresh_clone.py
env GIT_TERMINAL_PROMPT=0 git push --force-with-lease=refs/heads/main:69a9c3d710bc70b37b16f02a37e4c95f7b376292 origin refs/heads/main:refs/heads/main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/git_identity_rewrite_v1/check_online.py
```

身份修正公开文档提交61d3078包含版本表/档案说明/自身记录；其他聊天STATUS讨论及learning内容保留且排除。此状态随后正常提交/推送并再次核对最终SHA、所有提交身份及贡献者，最终报告outputs/git_identity_rewrite_v1/final_online_checks.json；不再次改写工程历史。用户本次授权覆盖此前正常同步不改写的限制，任务已完成，下一项只需刷新页面亲自观察，不另开新方法或研究范围。

## 05 已验收第一版GitHub同步（2026-10-03）

接手HEAD及00验收提交 `c2be7f87c32beb88c3a53dfdcef63b964e56de23`。重新读取AGENTS/SPEC/STATUS、00验收说明及GitHub同步任务，核对实际远程、分支、待推送提交与文件。起始远程main实际为 `12736e2f55304b843e146f26d379d5b2503470b8`；获取后确认远程是本地祖先，0个远程独有提交、本地领先34提交，累计64个变化路径。待同步历史包含基线、恢复、评价、正式冻结、三片对照、M4整理579baf3与00验收c2be7f8；72份HEAD文件与全部72条历史路径只有代码/配置/文档及占位文件，不含媒体、模型、环境、缓存、真值包或结果文件。

实际执行正常 `git push origin main`，退出0，远程main从12736e2前进至c2be7f8；随后 `git ls-remote origin refs/heads/main` 实际返回完整验收SHA，与本地当时HEAD一致，包含M4及验收。没有强制推送、重写历史、自动标签或GitHub Release；没有新模型运行/调参/测试/范围扩展。

实际线上核对PASS：用GitHub Contents API读取main的README、docs/run_demo.md、docs/m3_results.md和docs/m4_acceptance_00.md，逐字节与c2be7f8的四份Git文件一致；直接GET四份验收提交页面均HTTP200，页面正文包含相应标题。通用网页读取工具对这四个请求返回Cache miss，已另用上述真实API及公开HTML核对，不把工具索引缓存当成线上证据。本次只同步已验收的代码/文档，本地媒体链接仍需要本地包，不为GitHub缺少本地媒体而上传视频。

仓库：`https://github.com/shuiliufu-design/occlusion-aware-tracking`；分支main。同步证据保存在 `outputs/github_first_version_sync_v1/`：initial_git/initial_diff和两份状态初始副本、pending_commits.json、tracked_content_check.json、push/远程SHA日志、online_accepted_checks.json、四份线上原文/API元数据/HTML，以及最终SHA核对报告。接手1812份旧输入/权重/输出文件SHA保持，冻结12执行文件保持。其他聊天已有及同步期间新增的STATUS讨论26行、learning15行保留且排除本次状态提交，不执行git add .。

项目根目录实际命令（输出留本地，网络和Git元数据写入按本任务授权执行）：

```bash
env GIT_TERMINAL_PROMPT=0 git ls-remote origin refs/heads/main
env GIT_TERMINAL_PROMPT=0 git fetch origin main
git rev-list --left-right --count origin/main...HEAD
git log --reverse --format='%h %s' origin/main..HEAD
git merge-base --is-ancestor origin/main HEAD
env GIT_TERMINAL_PROMPT=0 git push origin main
env GIT_TERMINAL_PROMPT=0 git ls-remote origin refs/heads/main
.venv/bin/python outputs/github_first_version_sync_v1/check_online.py
git diff --check
```

线上脚本实际用 `gh api repos/shuiliufu-design/occlusion-aware-tracking/git/ref/heads/main` 与 `gh api repos/shuiliufu-design/occlusion-aware-tracking/contents/<文件>?ref=main`，另用urllib只读GET验收提交页面。准确请求、SHA与HTTP结果见online_accepted_checks.json；文件占位写法只概述请求，四个实际文件路径由脚本与报告保存。

本状态更新只提交本任务自身差异，随后正常同步状态提交并再次核对最终本地/远程SHA；最终完整提交号和线上STATUS匹配结果保存在 `outputs/github_first_version_sync_v1/final_checks.json` 及任务完成报告。未修改SPEC决策或已验收工程/文档。第一版同步交付完成后，由00决定下一项范围；速度/全片精确率/全新安装/困难例/泛化等原限制保留，没有启动VLA、仿真或世界模型。

## 00 M4验收与第一版完成决策（2026-10-03）

接手HEAD579baf3，重新读取AGENTS/SPEC/STATUS、M4任务、README/运行说明/实验表/演示/05验证、实际执行代码与产物。本轮正式冻结检查FROZEN/PASS，独立临时目录再次运行现有环境检查退出0。核对该目录70份Git文件与579baf3逐字节一致，资源链接符合记录；该提交只修改7份文档。

00另存只读核查 `outputs/m4_release_00_review/independent_check.py` / `acceptance_checks.json`，PASS：新基线/C/B各633行，原缓存/帧号/时间一致，三段各重解码633帧共1899帧；C/B各3事件、0程序接受，关闭633行重放TargetState原字段一致，导出f0原PNG像素一致。静态7来源SHA及三源视频/组别/逐事件返回与延迟、固定UNKNOWN帧匹配有效v2；HTML12链接存在、九演示视频SHA保持；12冻结文件/两依赖清单和1702旧文件重新计算SHA全部不变。已查看三幅程序同帧对照，保留等待/未返回/局部暂缓/拒绝。

05的一次CPU基线+C/B完整633帧与九演示4170帧解码为历史运行证据；00本轮未重推理模型或重复解码九原演示，未重跑110项全套/此前28项算法测试。沿用已有环境与权重，全新安装未验证；速度UNVERIFIED、全片精确误报率UNEVALUATED、真实双瓶/同包装/泛化/纹理独立贡献未验证、拍摄偏差/局部框不足/保守锚点/无第二人类逐帧复核保留，不新增M3样本。

决定：M4验收通过，第一版M0—M4在SPEC明确受限范围完成。README添加验收入口，SPEC确定唯一下一项同步GitHub代码与文档；任务目的/交付/验收见docs/github_first_version_task.md。本轮只更新决策/交接文档并本地提交，未推送、未启动后续研究；其他聊天的STATUS讨论及learning原样保留并排除。

实际命令（当时HEAD579baf3，根目录，旧证据不覆盖）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/m4_release_00_review/independent_check.py
git diff --check
```

另在/tmp/m4-git-files-5sv4mq0p运行 `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/check_env.py` 通过。验收说明docs/m4_acceptance_00.md；进度结论不表示已经同步线上，接手必须重新读取记录。

## 05 M4第一版整理与实际发布核查（2026-10-03）

接手HEAD `5006d96`，重新读取AGENTS/SPEC/STATUS、M4任务、有效v2实测/00复核、冻结清单/协议和实际执行代码/验收/失败证据。接手时其他聊天STATUS讨论与learning有未提交内容，已保存初始副本并原样保留，排除本次提交。没有修改12个冻结执行文件、任何配置/阈值/依赖/权重/检测/状态规则、旧输出或真值。

交付：精简README及单一主流程 `docs/run_demo.md`；有效v2的可追溯静态表 `docs/m3_results.md` / `m3_results.json`；完整九段状态视频和同原帧对照入口 `docs/local_demo.md`；实际核查范围/命令/边界 `docs/m4_validation.md`。媒体与本地演示HTML/图片留在 `outputs/m4_release_v1/demo/`，没有加入Git。主命令显式选 `configs/recovery_m3_v1.json`，原默认保留；关闭仅身份恢复仍退回TargetState候选行为。

本轮先复用开发负例缓存运行/核查冻结C（633帧）；再在只复制Git文件的独立临时目录，沿用现有.venv/权重/一个开发原视频，以可替换的 `data/my_bottle.mp4` 和相对输出路径实际运行：环境检查、读取、仅一次CPU基线推理与核查、C与核查、关闭B与核查、文档中早期原图导出片段，共9个命令全部退出0。独立目录不链接私有缓存/真值。新基线/C/B各633行和非空视频重解码一致，C/B各3条事件；另逐字段重放633行原TargetState，关闭行为一致。示例初始化框来自已查看的f0原图，原图导出像素核对通过；本次CPU发布核查不是新M3实验，不重新报告准确率。没做新环境安装/模型下载/本轮GPU推理；不能称全新机器安装验证。

本轮生成静态表时逐项核对v2来源SHA、三片源SHA、A/B各0/2及34/88、C2/2及2/88、延迟10/4原帧，以及一次替换事件130合格拒绝/0绑定、零返回机会/延迟不适用。重解码全部九段原状态视频共4170帧，查看三张派生程序框对照，保留A/B未返回、C可见UNKNOWN确认空窗与负例局部暂缓/拒绝。没有添加人工评价框到这些演示输出。固定分母、拍摄偏差、保守锚点、局部几何不足、无第二人类逐帧复核、全片精确率UNEVALUATED、速度UNVERIFIED、双瓶/同包装/泛化和纹理独立贡献未验证均保留。

证据：`outputs/m4_release_v1/clean_commands.json` 保存准确命令、实际临时目录、退出码及日志；`clean_directory.json` 保存Git文件/资源访问说明；`clean_run/my_bottle_v1/` 保存读取/新基线/C/B；`cached_C/` 保存缓存核查；`acceptance_checks.json` 保存验收/限制；`demo_media_checks.json` 核对九视频；生成/核查脚本与日志亦留档。12冻结执行文件、配置/依赖清单SHA保持，接手1702个旧本地输入/权重/结果文件SHA保持；新增文档/本地HTML路径和链接经核查。110项全套/00的28项仍为此前证据，本轮未重跑，不新增算法测试。

项目根目录关键实际命令（已有输出不可覆盖；完整相对CLI参数在上述命令JSON与验证文档）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/m4_release_v1/cached_C --init-frame 0 --init-box 290 280 510 1040 --init-iou 0.5 --missing-frames 10 --config configs/recovery_m3_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/review_recovery.py --output outputs/m4_release_v1/cached_C --frames 0 180 485 632
.venv/bin/python /tmp/m4_run_clean.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/m4_release_v1/build_release_artifacts.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/m4_release_v1/verify_release.py
git diff --check
```

临时运行编排脚本亦留档 `outputs/m4_release_v1/run_clean.py`；发布核查不依赖它作为主运行入口。本轮检查变更后仅本地提交，不推送；提交号用 `git log -1 --oneline` 查看。下一项用户小任务：把README、实验表、本地演示及发布核查交00验收；交付为00的M4核对结论，验收为命令/路径/来源与范围相符、失败及未评价项保留。接手00须重新读取记录；同步GitHub与后续研究另决，不再要求拍片或调参。

## 00三片冻结实测复核与M4决策（2026-10-03）

接手HEAD `bd02916`，实测 `e7b028c`、冻结核心 `572de8f`。重新读取AGENTS/SPEC/STATUS、实测/验收/逐事件/失败、v1/v2协议/标注/物理确认及相关执行/评价代码。本轮重跑28三组边界测试通过，在新目录重跑冻结评价，含九组历史回放/视频重解码、130负例原像素及181标签图核查，全部通过；summary/逐事件/人工事件/标签核查四份JSON与03保存评价逐字节相同。没有新模型推理或新开三组实验。

另用本轮只读脚本独立复算4170行的缓存/时间/当前框依据、共同2机会、C f214/f283接受IoU及10/4帧延迟、A/B未返回、固定UNKNOWN 34/88与2/88、492缺席框无错误及130合格区域拒绝。179旧标签逐项不变，仅新增2帧，事件/初始化不改；v1/v2九组记录/事件/视频SHA逐对一致。重算1386和1529保全快照并集共1529文件SHA及12冻结文件当前/历史SHA，通过。03的110项全套为历史证据，本轮未重跑全套；相关28项与评价/审计属于00实际证据。

实际查看6帧原PNG人工框QA（原位f210/214、移位f280/283、替换f442/443），确认两接受帧的原T1/完整框、两清楚可见等待UNKNOWN及局部蓝瓶无完整框边界。不是第二人类逐帧复核，也不是181个框的全量几何人工复核。31帧连续无检测超过30缓冲、C f210—213/f280—282空窗、多个外观门槛共同拒绝不证明纹理独立贡献、一次替换不是130独立事件、拍摄偏差/保守锚点/局部未评价/速度等限制继续保留。

决定：M3受限小规模效果实验交付验收通过，进入M4第一版整理，不继续补阈值或新增困难例/计时/机器人功能。SPEC已写入唯一任务、目的/交付/验收；05或沿用03按 `docs/m4_release_task.md` 接手，完成主流程/README/实测表/本地演示及实际运行核查后交00，M4当前未完成。

实际命令（根目录，已存在输出不可覆盖复跑）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p test_m3_comparison.py -v > /tmp/m3_holdout_comparison_00_tests.log 2>&1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/evaluate_comparison.py --protocol configs/m3_holdout_v2.json --runs outputs/m3_holdout_comparison_v2 --output outputs/m3_holdout_comparison_00_review/evaluation > /tmp/m3_holdout_comparison_00_evaluation.log 2>&1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/m3_holdout_comparison_00_review/independent_check.py
git diff --check
```

证据 `outputs/m3_holdout_comparison_00_review/`，说明 `docs/m3_holdout_comparison_00_review.md`。核心/配置/标签/原输出保持，README只同步00采纳状态与已完成小规模对照；M4完整整理另由下一任务完成。本轮仅决策/任务/进度文档本地提交，不推送，其他聊天已有STATUS讨论与learning改动原样保留并排除。

## 03三片HOLDOUT冻结对照交付（2026-10-03）

重新读取AGENTS/SPEC/STATUS、comparison_task、共同协议/标注/00复核、正式冻结及输入/验收实际记录。起始HEAD3bc338b，其他聊天STATUS/learning未提交修改原样保存并排除。先实际核查正式FROZEN/PASS、三份开发来源排除和现有缓存/标签SHA；核心仍匹配冻结572de8f的12执行文件。没有修改算法、阈值、依赖、权重、YAML或初始化/事件。

初轮按configs/m3_holdout_v1.json完整运行341/476/573帧的A/B/C，保存outputs/m3_holdout_comparison_v1/。共同入口内部完成历史代码回放、记录/事件/状态视频重解码和原像素负例证据核查；初轮C接受f214/f283，但标签只支持返回存在f220/f286，精确延迟/接受身份为UNEVALUATED。实际查看这两帧无算法框原PNG，独立标T1完整框，另存outputs/m3_holdout_annotations_v2/，不改变179原标签/141固定抽样/88清楚T1分母或f204/f279锚点。

v2协议提交e7b028c后复跑冻结离线入口，以新标签SHA绑定最终outputs/m3_holdout_comparison_v2/，仍复用三个缓存；两轮各4170行/视频帧，不是新增独立样本。附加核查逐字段比较缓存/原帧时间/当前位置、v1/v2所有状态和事件完全一致，九对视频4170解码帧像素完全一致；两新增PNG在评价器中逐像素核对。v2实际执行e7b028c，冻结清单SHA0562cedc…与shared_policy不改。

| 片/人工事件 | A | B | C |
| --- | --- | --- | --- |
| return_01，同瓶原位1机会 | 未返回FAIL | 未返回FAIL | f214正确接受/返回PASS；相对f204延迟10帧、名义0.333278秒、源0.333333秒 |
| return_02，同瓶移位1机会 | 未返回FAIL | 未返回FAIL | f283正确接受/返回PASS；相对f279延迟4帧、名义0.133311秒、源0.133289秒 |
| replacement_01，原T1移除0机会 | 返回/延迟/外观核验不适用 | 返回/延迟/外观核验不适用 | 返回/延迟不适用；130合格候选全外观拒绝、0绑定 |

每组共同两个返回机会；A/B各0正确+2未返回，C2正确+0未返回，C两个接受独立身份/当前框核对均正确、错误/未评价接受0。固定清楚T1 UNKNOWN：A/B各14/31+20/37+0/20=34/88；C1/31+1/37+0/20=2/88（f210/f280等待确认）。C连续可见区间f210—213/f280—282仍UNKNOWN，B/C错误确认LOST在人工CLEAR T1区间均0。三组人工缺席25/92/375帧各0错误当前位置；局部已观察框不足第一片f169、第二片f168、负例f195仍未评价（组别见failure_analysis），全片精确率不报零。

原始检测缺失最长31/100/194帧；第一片[172,203)31帧超过ByteTrack30缓冲，不能当作短于缓冲成功样本。两个正例返回原生ID3，初始ID1不再被观察，A不接续新ID、B锁定后仅候选；没有原生重新关联成功样本。C连续5帧核验导致清楚可见时尚有位置空窗，门槛不调。

负例清楚匹配区域[443,573)130帧：实际130检测/130合格候选/130外观拒绝，缺失/低质/歧义/误接受均0仅对该区域成立。整次C133候选=131程序拒绝+2质量暂缓；f390/f391/f442局部完整几何不确定，不混入130分母。A/B不绑定不计外观拒绝通过。130帧外观证据从原像素重算一致；瓶盖/形状通过、标签颜色/纹理/分数同时失败，不能隔离纹理贡献。第一/第三片偏差、小样本、保守锚点、Codex标注无第二人类复核、同包装/双瓶未验证等保留。

实际命令（根目录，现有结果不可覆盖，复跑换空目录）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_comparison.py --protocol configs/m3_holdout_v1.json --output outputs/m3_holdout_comparison_v1 > /tmp/m3_holdout_comparison_v1.log 2>&1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v > /tmp/m3_holdout_comparison_tests.log 2>&1
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python /tmp/m3_add_return_labels.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_comparison.py --protocol configs/m3_holdout_v2.json --output outputs/m3_holdout_comparison_v2 > /tmp/m3_holdout_comparison_v2.log 2>&1
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python outputs/m3_holdout_comparison_v2/verify_run_v2.py --protocol configs/m3_holdout_v2.json --runs outputs/m3_holdout_comparison_v2 --previous outputs/m3_holdout_comparison_v1 > /tmp/m3_holdout_comparison_acceptance_v2.log 2>&1
```

上述成功：110项全套测试（28三组/20离线评价/12标注边界等）实际通过；九组完整历史回放/重解码、原像素/来源校验，1386原受保护文件及v2保护1529文件（含初轮结果/补标输入）SHA保持。首次附加核查误将B已关联轨迹框要求等于检测框而退出1，脚本/日志保留；按冻结组别实际框依据修正附加核查后PASS，没有修改12冻结文件。原辅助disabled_matches_step1=false仅无旧step1路径，单独历史TargetState全帧回放通过；冻结NOT_STARTED/旧辅助开发scope文案留作模板，当前进度见新运行。

交付：docs/m3_holdout_comparison.md；v2的per_event_table.md、group_totals.json、acceptance_checks.json、failure_analysis.json、原图裁剪/附加核查脚本/日志，evaluation的summary/逐事件/人工分母/181标签原像素核查/九组历史来源；三片每组frames.jsonl/events.jsonl/status.mp4/run_info，C参考/配置。原v1及旧审查/开发证据保留，视频/标签PNG/缓存/输出不入Git。实验交付核查PASS不消除表中算法FAIL；速度/端到端开销UNVERIFIED，全片精确误报率UNEVALUATED。下一项交00复核表与失败边界，再决定M4/后续；本轮仅本地提交，不推送。

## 00 HOLDOUT输入准备复核与三组任务决策（2026-10-03）

接手HEAD `97a22a0`，03核查实现 `c0c7503`。重新读取规则、规格/进度、标注说明/报告/协议/物理确认及相关核查/共同入口/评价代码。00本轮以新目录重跑12项标注边界测试及全量输入核查，均退出0：原件/副本/三份开发排除、初始化/时间轴/1,390帧缓存全量重解码、179标签原PNG逐像素、1,040旧文件SHA通过。03全套110项及原缓存推理为历史证据，本轮未重跑全套或模型。

另用本轮只读脚本重算三份源副本、179图/推理前标注清单SHA，核对固定网格35+48+58=141、38附加关键帧、两个返回机会和一个零返回机会、12个执行文件与冻结Git/当前SHA及shared_policy一致。实际查看18个不同原帧的像素裁剪和6幅重合人工框QA，初始化/遮挡/局部重现/末段原瓶与蓝标替代瓶无明显标签矛盾。未对179框全量目视复核，00仍是Codex，不构成第二位人类逐帧复核。

输入准备采纳通过；当前唯一任务安排03运行三片冻结A/B/C及共同评价。清楚T1固定误报分母为88；两个正例f204/f279为保守锚点，邻近不确定/部分框不足保留。替换片T1零返回机会、延迟不适用，[443,573)130帧仅候选匹配区域；手持/局部覆盖另列未评价。首个待评价返回/接受如需补框，另存标签/协议/输出、复跑冻结离线状态入口以满足协议SHA绑定，核对状态/事件/视频像素未变，不改旧运行来源或猜隐藏轮廓。拍摄偏差原样报告，不因结果补拍/筛片。不新增工程计时或困难例，速度继续UNVERIFIED。

实际命令（根目录）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p test_holdout_annotations.py -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_holdout_annotations.py --protocol configs/m3_holdout_v1.json --output outputs/m3_holdout_annotations_00_review/validation
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/m3_holdout_annotations_00_review/independent_check.py
git diff --check
```

证据 `outputs/m3_holdout_annotations_00_review/`，说明 `docs/m3_holdout_annotations_00_review.md`，具体下一任务 `docs/m3_holdout_comparison_task.md`。SPEC已写入采纳/范围/验收；本轮未运行A/B/C或评价效果，工程核心/标签/缓存/阈值/正式冻结未改。只提交本轮决策/任务/进度文档，不推送，其他聊天已有STATUS讨论/learning修改保持并排除。

## 03三片HOLDOUT输入与独立标注交付（2026-10-03）

03重新读取AGENTS、最新SPEC/STATUS、`docs/m3_holdout_annotation_task.md`、正式冻结、共同协议及confirmed登记。起始版本ff48d00，已有其他聊天STATUS/learning修改保留、排除本轮提交。新增核查入口/12项边界测试/协议/说明先提交为 `c0c7503b7076c723c93ce3d0f93f890c4d0ff9f4`，然后实际运行；没有改冻结的12个执行文件、依赖/权重/YAML、算法、阈值或旧SHA。

本聊天用户再次确认“三项物理操作已由我确认”，另存绑定三片SHA的记录；物理身份依据与逐帧原图依据分开。仅看f0/30/60锁定前段f0人工框，随后逐个查看全部固定抽样及连续转折原图，先保存标注/初始化SHA清单再做公共推理。实际标注者为Codex，尚无第二位人工逐帧复核；检测类别/ID/分数均不定义真值。

| HOLDOUT片 | 原帧/固定样本/附加关键帧 | 人工事件与返回依据 |
| --- | --- | --- |
| return_01 | 341 / 35 / 9 | 原位同T1一次机会；f204保守可辨认、f210整瓶清楚 |
| return_02 | 476 / 48 / 13 | 移位同T1一次机会；f279保守可辨认、f280整瓶清楚 |
| replacement_01 | 573 / 58 / 16 | 原T1已取走且不返回，零机会；T2 f388模糊边缘、f389—393局部可辨认、f443整瓶清楚 |

141/141固定样本均有标签；88清楚T1、13清楚T2、36完全不可见、4局部。附加38关键帧不扩大固定分母；11不确定边界及局部几何缺失框均为空。后续首个待评价返回/接受帧若不在网格，仍需追加原图身份/框核对，不可据缺标签报成功、零延迟或全片零误报。替换片手持T2过程保留；[443,573)人工区域用于未来合格候选匹配，不是130帧精确框或已拒绝结论。单区间适配另存并引用推理前标注SHA，核心评价器不改。

第一/第三片原粗检时长偏差完整保留。新原图“开始部分遮挡至整瓶清楚”宽口径分别41/112/248帧（约1.366/3.733/8.265秒），后段131/196/130帧（约4.366/6.532/4.333秒），粗检与新口径并存。视觉遮挡不是连续无检测时长，第一片不能据此证明小于ByteTrack缓冲的能力。

实际命令（根目录，三个缓存各只运行一次；现有输出不可覆盖）：

```bash
.venv/bin/python scripts/run_baseline.py --source data/m3_holdout_return_01.mp4 --output outputs/m3_holdout_cache_v1/holdout_return_01 --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/run_baseline.py --source data/m3_holdout_return_02.mp4 --output outputs/m3_holdout_cache_v1/holdout_return_02 --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/run_baseline.py --source data/m3_holdout_replacement_01.mp4 --output outputs/m3_holdout_cache_v1/holdout_replacement_01 --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
.venv/bin/python scripts/validate_holdout_annotations.py --protocol configs/m3_holdout_v1.json --output outputs/m3_holdout_annotations_v1/validation
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts/validate_holdout_annotations.py tests/test_holdout_annotations.py
```

以上全部成功：三片原始GPU缓存1,390帧，版本/模型/YAML及冻结条件一致；唯一初始化IoU为0.948285/0.899844/0.921554，门槛0.5不改。原视频及缓存完整解码、1390帧时间轴对应；179标签PNG与原视频逐像素一致，141固定样本无遗漏；三个人工事件/两个返回机会正确；正式FROZEN和shared_policy逐项不变，1,040个旧文件SHA一致。110项全套测试通过（既有98+新增12），编译通过。重复核查到同一非空目录按预期退出1，旧报告不覆盖。这些是03本轮实际证据，不借用历史测试或把缓存原生统计算身份结论。

报告 `validation/annotation_checks.json`、`acceptance_checks.json`、`freeze_check.json` 与完整运行/测试日志保存本地；根目录另有事件名义/源时间表、人工框QA、原图拼图、覆盖、推理前清单和准备脚本留档。准备脚本为本轮执行记录，已登记目录不可直接重跑覆盖；核查入口可指定新的空输出目录复跑。视频/权重/缓存/标注PNG/报告仍被Git忽略。

本步输入准备PASS；A/B/C对照与效果评价NOT_STARTED，速度UNVERIFIED。无新的恢复成败、全片误报率或困难例结论；三片有拍摄偏差、小样本和标注覆盖边界均保留。下一项交00核对本轮输入准备，再决定三组任务；本轮仅本地提交，不推送。

## 00用户物理确认与03标注交接（2026-10-03，输入标注前历史）

用户回复中的“三项都正确”确认了上一轮列出的三项：44同一瓶子原位重现，46仅移动原瓶未替换，48取走原瓶换成蓝标瓶且原瓶不再入镜。保存原回复和解释，不将其扩展为逐帧框/可见性/精确事件时刻或算法表现确认。

旧pending登记/检查保留不覆盖，新confirmed目录 `outputs/m3_holdout_input_confirmed_20261003/` 含 `operator_confirmation.json` 和 `input_registry.json`，绑定三片源路径/项目副本/SHA；两次期待返回、一次零返回机会。重新核对三份原片与副本SHA、旧登记SHA及正式冻结SHA，均一致。第一/第三片拍摄偏差仍在新登记中；algorithm_has_run=false/evaluation_status=NOT_STARTED。

已同步SPEC、拍摄说明及本轮用户学习记录；唯一下一任务写入 `docs/m3_holdout_annotation_task.md`，03先完成HOLDOUT输入登记与独立标注，需要公共缓存可固定条件每片推理一次，暂不运行A/B/C对照。具体交付与验收见上方唯一任务及新说明。当前没有运行模型、创建正式逐帧标注/缓存/对照协议或新增算法测试；确认的是物理身份依据。

本轮验证：现有`.venv/bin/python`读取JSON并逐文件重算三份源/副本与冻结SHA，确认新登记3项CONFIRMED、返回机会2、负例1、偏差未改、旧pending登记未改；`git diff --check`。本地提交确认/决策/任务说明，视频及输出保留本地，其他聊天已有VLA讨论/学习记录排除，不推送。没有向03聊天发送消息；给用户可复制的交接提示，接手必须重新读取记录。

## 00三份新视频技术检查与登记（2026-10-03，物理确认前历史）

用户随后提供三份13-58-44/46/48原片。00沿用现有解释器与inspect_video脚本读取全部成功帧；顺序解码每秒原图/遮挡转折附近每0.1秒原图，第一片/第三片完全露出附近又查看逐帧拼图。各片背景持续可见、单主要遮挡事件，抽样未见明显相机位移。未运行任何检测/跟踪/恢复或按结果选择片段，尚无用户物理确认。

| 原文件结尾 | 暂定场景/项目副本 | 解码帧数/名义FPS/估算秒 | 技术拍摄偏差 |
| --- | --- | --- | --- |
| 13-58-44 | 较短遮挡原位重现；data/m3_holdout_return_01.mp4 | 341 / 30.004986166 / 11.365 | 遮挡约1秒长于0.3—0.5目标；完全露出后约4.4秒，少于5秒 |
| 13-58-46 | 遮挡移位；data/m3_holdout_return_02.mp4 | 476 / 30.004916772 / 15.864 | 约3.5秒遮挡、后段约6.3秒；抽样未见明显时长偏差 |
| 13-58-48 | 红标→蓝标替换画面；data/m3_holdout_replacement_01.mp4 | 573 / 30.004904816 / 19.097 | 遮挡约8秒长于3—4目标；完全露出后约4.3秒，少于5秒 |

这些粗略时长只用于输入条件检查，不是正式事件/首次可辨认返回帧真值。第三片约13秒手持蓝标瓶子在遮挡物旁边出现，正式标注须保留这段局部/候选出现过程，不能用最终纸板撤走替代首次可辨认候选时刻。

新源SHA分别 `0e04498b2189f8dac4d697ba3248b5b760f7bee35bb4c1471627a9212e5f59e7`、`6749da6f1cc34d928c293702862bff5421966b9811b1ba8a7c8931c6704e4529`、`e69630d7661ddbac85993d7b75d3ec3d47975a409f096abe0d35246e0b73f952`；三者互异，均不同于冻结清单三份开发来源；项目副本与原文件逐字节SHA一致，原文件未改。

00在任何算法运行前确定输入条件例外：三份保留进入独立登记/标注，不再要求按效果补拍，但结果须称“有拍摄偏差的小规模保留测试”，不得声称严格符合全部原拍摄计划。算法/参数/指标/共同冻结规则未改；不能从第一片约1秒纸板遮挡推定实际连续无检测帧数或证明小于原生缓冲时限的能力。价值是保留首次技术可用拍摄、减少进一步采集工作并如实报告新输入上的成败；不掩盖时长偏差或未知标签。

实际执行命令（项目根目录，三份在独立空输出目录）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/inspect_video.py --source '/home/qiyue/下载/Telegram Desktop/video_2026-10-03_13-58-44.mp4' --output outputs/m3_input_20261003_135844
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/inspect_video.py --source '/home/qiyue/下载/Telegram Desktop/video_2026-10-03_13-58-46.mp4' --output outputs/m3_input_20261003_135846
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/inspect_video.py --source '/home/qiyue/下载/Telegram Desktop/video_2026-10-03_13-58-48.mp4' --output outputs/m3_input_20261003_135848
git diff --check
```

每份目录包含首帧/元信息/原图拼图/provenance/input_review。共同登记 `outputs/m3_holdout_input_batch_20261003/input_registry.json` 保留原路径、副本、SHA、实际观察/偏差、operator_confirmation=PENDING及algorithm_has_run=false。正式冻结SHA0562cedc68e79fcd4a8e2e5dca02c3c3d79917a294154845590bab131a8505ce未变；旧输入/结果保留。未修改工程、未做新增算法测试。

下一项只请用户确认三项物理操作，确认前不宣称正确身份或恢复结果。已通过异步问题请求，独立的读取/登记工作先完成；没有把画面相似或文件名当作物理身份确认。确认后交03先完成HOLDOUT输入登记/独立标注，不立即调参或根据测试结果改方法。本轮只提交输入决策/进度说明，其他聊天未提交讨论/学习记录排除，不推送。

## 00新视频输入检查（2026-10-03，先前混合事件原片）

用户提供原文件 `/home/qiyue/下载/Telegram Desktop/video_2026-10-03_13-21-42.mp4`。00仅检查原视频，没有运行模型/跟踪/恢复、改变冻结规则或根据算法表现选择视频。原文件保留在原路径，SHA256 `b92f42c171633e6dae32ac76c58013032a0545fa1134fd4cfe56af2899f0bd32`，与正式清单中全部三段开发来源SHA不同。

实际沿用现有解释器/脚本成功读取797帧，尺寸720×1280、名义FPS30.004944353、帧数/FPS估算26.562秒；非零帧数不保证源文件完整性。顺序解码另存27个约每秒原图样本、24个转折附近样本的拼图，并查看首帧/两张拼图。抽帧观察约2.5—3.5秒有第一次遮挡，约6.5—10秒遮挡后红标瓶子向右移位，约13—23.5秒再次遮挡后出现蓝标红盖瓶子；这些是画面观察，不是逐帧事件真值或物理身份确认。

拍摄协议检查：同一条包含多次事件，不能当作三份分别新录/每片单次事件的独立输入。尤其约7—9.5秒纸板几乎盖满画面，背景也被大面积遮挡；最初清楚控制段不足5秒，最后重现后约3秒也不足5秒。根据已冻结拍摄条件暂不计正式三片，原片/记录保留，不剪辑成三份或放宽规则；没有根据模型效果要求重拍。

实际运行命令（项目根目录）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/inspect_video.py --source '/home/qiyue/下载/Telegram Desktop/video_2026-10-03_13-21-42.mp4' --output outputs/m3_input_20261003_132142
git diff --check
```

结果 `outputs/m3_input_20261003_132142/` 包含首帧、`video_info.json`、`overview_1s.jpg`、`transition_sheet.jpg`、`input_review.json`。拼图由本轮临时Python顺序读取原帧生成，不是新增算法入口。正式冻结SHA仍为0562cedc68e79fcd4a8e2e5dca02c3c3d79917a294154845590bab131a8505ce，SPEC/核心/配置均未变；尚无HOLDOUT结果。

下一项只让用户先补拍一段短遮挡，以检查纸板靠近瓶子的布置、背景可见与前后5秒控制段，附同瓶未替换确认。输入采集尚未形成新可运行里程碑，本轮只追加进度记录，不提交已有其他聊天的讨论/学习记录，不推送。

## 00三组预演复核与正式冻结（2026-10-03）

接手HEAD `3af410a`，实际预演/评价版本 `572de8fb5196d7873f6e7f41c33f178dc008ed9b`。先读取AGENTS/SPEC/STATUS、M3协议、验收/待冻结清单及相关代码/测试/六组输出；其他聊天已有未提交VLA讨论与学习记录原样保留，不纳入本轮提交。工程核心、默认、阈值和旧输出均未修改。

| 核查范围 | 03已实际运行证据 | 00本轮实际证据 |
| --- | --- | --- |
| 测试/来源 | 全套98项、完整Git来源状态回放/六视频重解码、负例148帧原像素 | 只重跑本轮相关28项，通过；逐执行文件对照572de8f及当前文件SHA。未重跑全套98项、模型或完整状态/输出视频 |
| 三组口径/回归 | A/B/C共用输入/事件、B/C保持采纳行为 | 独立核对六组384/633行、原基线字段和A本帧原生选择映射；B/C记录/事件/视频SHA与先前采纳结果一致 |
| 保全/标注 | 881既有文件与75评价输入保全、12补充原图像素一致 | 实际重算881/75文件SHA；从两段原视频顺序解码，12张补充标注PNG逐像素一致并查看原图拼图 |
| 冻结清单 | 待冻结清单核查PASS | 待冻结与新正式清单均实际核查PASS；新清单状态FROZEN/frozen=true。仅新增正式记录，没有覆盖历史清单/开发协议 |

共同事件口径通过：正例只有1次期待返回，A/B未返回；C首次正确当前位置f852，与人工框IoU约0.8692、从f847延迟5帧。负例期待返回为0，返回/延迟不适用；148帧合格候选拒绝属于1次替换，149全程候选另列，0错误绑定。不得把A/B不绑定写为外观拒绝，也不遗漏原生同ID返回的正确机会。

限制保留：f850三组UNKNOWN；A/B f181缺完整人工框仍UNEVALUATED，另列的156缺席帧0错误不替代它。固定抽样仅6/103，97尚未核对；全片误报率、速度、困难例及纹理独立贡献未验证。独立复核PASS表示入口与开发证据满足冻结条件，不表示上述算法结果均成功或M3独立性能已通过。

本轮实际命令（项目根目录）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p test_m3_comparison.py -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze outputs/m3_development_preflight_v4/freeze_checklist.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/m3_preflight_00_review/checker.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
git diff --check
```

00审查脚本/核对结果/28项测试日志位于 `outputs/m3_preflight_00_review/`；`review.json`明确区分本轮核查与03历史运行。正式清单 `configs/m3_freeze_v1.json`，标识m3_v1，SHA256 `0562cedc68e79fcd4a8e2e5dca02c3c3d79917a294154845590bab131a8505ce`；执行版本572de8f，锁定原清单10项执行文件，并补锁检测/基线核查脚本共12项。C文件与已采纳配置字节一致，依赖/实际安装包、模型/YAML、共同初始化/因果参考/指标/抽样/计时规则保留。

HOLDOUT协议须另存，引用正式清单及SHA，共同规则逐项一致；只新增逐片实际来源、缓存、前段人工初始化、独立标注/事件。清单中的未开始状态是冻结时计划快照，实际测试进度另存。03必须额外核对 `excluded_development_sources` 全部三片SHA；现自动入口只排除两片预演来源。初始化仅看前段，匹配门槛固定0.5，记录后不按后段效果重选；标注不传算法。看过测试后如需改变方法/口径，保存失败、转开发并另拍保留输入。

决策：正式冻结并进入新输入采集，唯一任务为上述三段原片及物理操作确认。尚未收到新片，未执行HOLDOUT或速度试验。本轮只更新决策/说明与正式配置，检查后做本地提交，不推送；其他聊天未提交记录保留。

## 03三组共同入口与冻结准备交付（2026-10-03，冻结前历史）

接手HEAD为 `5bdfe8f`。重新读取规则、SPEC唯一任务、STATUS、评价/对齐说明及00核对证据，核对实际核心/协议/开发输出。接手STATUS及学习日志已有未提交讨论，另存初始副本并保留，不纳入本轮提交。未改M2核心、原默认、检测/跟踪、阈值或参考策略。

新增 `scripts/run_comparison.py`、`evaluate_comparison.py`、`m3_common.py`、`configs/m3_protocol_v1.json`、`tests/test_m3_comparison.py`、`docs/m3_protocol.md`；C另存 `configs/recovery_m3_v1.json` 与采纳配置逐字节一致，SHA `3e66affe0fbac2bf3bb138bb81d515e54c4f37f2489108da182178d6e2989721`。A只读唯一初始化原生ID的本帧检测框；B/C直接复用原核心。三组共用缓存/初始化/区间/源时间，不人工续新ID或输出缺检测预测/历史框；B保留原本帧滤波框与检测映射。

12张补充评价原图先顺序解码并查看拼图，包含新增f850人工框/身份；补充标签在 `outputs/m3_development_annotations_v1/`，旧物理操作确认/身份/事件/诊断不改，评价真值不传算法。三组主返回指标依人工重现时刻后的同一实体与本帧框IoU>=0.5，不要求A/B有RECOVERY_ACCEPTED；原生重关联与C接受另列，旧M2历史指标不重定义。

| 开发事件 | A | B | C |
| --- | --- | --- | --- |
| 正例人工机会1 | 未返回1，延迟不适用 | 未返回1，延迟不适用 | f852正确返回1；5帧延迟 |
| 负例人工机会0 | 返回/延迟不适用 | 返回/延迟不适用 | 返回/延迟不适用，不计恢复失败 |
| 人工148替代瓶子帧 | 匹配检测148；候选/外观机制不适用 | 候选148；外观质量/拒绝不适用 | 合格148，全拒绝，1替换事件；整次149另列 |
| 自定义接受 | 不适用，null | 不适用，null | 正例接受1且人工正确；负例0绑定，0错误/未评价接受 |

C延迟仍从人工f847计5帧，名义0.1721898148秒/源时间0.1899888889秒。本长遮挡片中A/B未接续新ID；短时原生同ID无接受事件仍能正确返回、同ID错实体记错、新ID/未知身份不假成功或零延迟，均由构造边界测试验证，不冒充真实短遮挡结果。固定抽样计划39+64=103，本轮2+4=6已核对，97未核对；正例600/850为清楚T1样本，三组850仍UNKNOWN，C连续确认成本保留。负例清楚T1样本0/170/180有位置，500为T2；后补847/852不进入固定分母。旧11帧可见诊断三组0 UNKNOWN，148替换帧及8全遮挡帧均0错误当前位置，但全片误报率仍UNEVALUATED。负例A/B f181有当前框但缺人工完整框，位置审查为UNEVALUATED/[181]，缺席156帧的0错误/PASS另列；C该帧保持UNKNOWN。

先提交 `a2e1d59` 后跑v1：运行日志误重定向进被保全输入树，pip诊断写日志后保全检查正确拒绝（退出1）；失败目录/日志/原SHA保留，不记主运行成功。日志改到/tmp后v2完整成功；补齐未来正式冻结输入保护、提交 `e614d61` 后v3完整成功。随后发现负例A/B f181有当前框但缺人工完整框，修正汇总未评价状态、提交 `572de8f` 后在最终v4完整成功。v2/v3/v4六组所有记录/事件/视频SHA一致，未改核心/协议/阈值。

最终实际成功命令（项目根目录）：

```bash
.venv/bin/python scripts/run_comparison.py --protocol configs/m3_protocol_v1.json --output outputs/m3_development_preflight_v4 > /tmp/m3_preflight_execution_v4.log 2>&1
.venv/bin/python scripts/m3_common.py --check-freeze outputs/m3_development_preflight_v4/freeze_checklist.json
.venv/bin/python -m unittest discover -s tests -v > /tmp/m3_tests_98.log 2>&1
.venv/bin/python -m compileall -q scripts tests
git diff --check
```

最终v4含两片各A/B/C视频/逐帧/机制事件/来源、 `evaluation/common_manual_events.json`、逐事件/六组summary/抽样缺口、Git回放/负例像素核查、依赖快照、待冻结清单、 `acceptance_checks.json`、测试/执行日志与前后保全。入口开发验收PASS，A/B未返回和f850 UNKNOWN等算法失败/成本仍如实报告。单独评价复跑入口与准确口径见 `docs/m3_protocol.md`；非空运行/评价目录的实际保护均预期退出1，原结果不变。

运行Git快照逐字段回放A384/633、B原TargetState384/633，C记录/参考/分量/事件核对；六视频重解码384/384/384/633/633/633帧。C负例重解码原片633帧、148帧原像素重算；B/C四组记录/事件/视频SHA匹配采纳结果。旧review的disabled_matches_step1=False因未传第一步目录，实际historical_target_state_replayed_frames与完整对照通过，不能误读为B改变。12标注图逐像素一致，原366再次匹配、接手589文件保全、最终入口881既有文件保全。

98项测试实际通过（原70+本轮28），compileall通过；待冻结核查实际PASS但仍PENDING_REVIEW_NOT_FROZEN。清单覆盖实际Git代码/配置/依赖与实际安装包/权重/YAML/缓存/初始化/标注/因果参考/指标/抽样/计时边界。未来HOLDOUT须引用已核对FROZEN清单、匹配共同规则和检测条件、拒绝旧开发视频冒充独立输入；本轮仅测试保护，未创建真实FROZEN记录或执行保留片。B/C增量计时未实施，ms/帧null，预热一次/各3次及排除边界已写协议。

本轮只本地提交、不推送。全片误报率未评价，速度/真实双瓶/同包装/新背景可见负例/纹理独立贡献未验证。下一项用户小任务：把v4验收/共同事件/summary/待冻结清单交00，要求重新读取记录只读核对；交付是核对结论，验收是共同口径与完整清单通过后明确是否冻结。当前不拍片、不启动正式M3。

## 00有界对齐复核与M3准备决策（2026-10-03）

接手HEAD为 `88172f1`。重新读取适用规则、规格、状态、对齐说明、新配置、六组运行及最终v2评价/验收、当前外观核心/评价器和相关测试。先只读审查，随后只更新SPEC/STATUS；其他聊天的VLA讨论/学习记录未提交修改保留，不纳入本次记录提交。

| 核对项 | 03实际交付证据 | 00本轮实际重新核查 |
| --- | --- | --- |
| 测试 | 全套70项通过、compileall通过 | 只重跑有界对齐15项与离线评价20项，共35项通过；未重跑全套70项 |
| 来源/回归 | 六组因果运行、旧/关闭完整状态与视频回放 | 核对六组384/633行记录、原基线字段、事件与旧视频SHA；旧/关闭全部记录等价，Git核心124dbcb/评价bdc3587校验一致；未回放完整状态或解码输出视频 |
| 保全/参数 | 366旧文件保全，原默认/原门槛保留 | 重算366文件SHA与前后清单；旧默认对Git版本一致，新配置只加四项对齐配置，SHA与报告一致；因果参考文件校验未变 |
| f180诊断 | 固定26帧标注、清楚UNKNOWN 1/11→0/11；完整负例原像素重算 | 从原视频解码到f195，26诊断PNG逐像素一致；查看两张原图拼图，核对11清楚/6局部/1不确定/8全遮挡；从早期原裁剪建立分量，独立枚举有限平移重算f180，不调用对齐函数替代审查 |
| 正/负例 | 正例f852正确1/5帧延迟；负例148合格拒绝，0错误绑定 | 从事件、人工身份/框、记录与评价报告核对相同指标；f852人工框IoU约0.8692，f180当前框IoU约0.9459；未重算负例全部148帧原像素 |

独立f180结果：同一最高S参考f5，(-1,+5)、共同区域0.933105、NCC0.793803、S0.799862，与已存分量一致。当前检测框来自f180，未借f179历史框。新首次缺失f181，满10帧f190 LOST；f181—186局部与f188—195全遮挡仍无当前位置，f187不确定不算对错。关闭分支f181仍有原生观察是历史TargetState行为，不能将其写为外观质量通过。

实际命令（项目根目录）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p test_texture_alignment.py -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p test_offline_evaluation.py -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/f180_alignment_00_review/checker.py
git diff --check
```

只读核对源码、PASS结果和测试日志在 `outputs/f180_alignment_00_review/`；首次通过`.venv/bin/python -`执行核对后保存源码。保存脚本首跑因缺工程导入路径退出，补齐路径后实际运行PASS；这是00审查脚本的入口修正，工程实现/输出未变。源码依赖本次实际代码/原始证据版本，后续代码变化应使用对应历史版本。没有运行模型推理、新状态策略、完整03/04审查或正式M3输入。

决策：受限开发修正通过，采纳新配置作为M3 C组候选，原默认及历史输出保留。进入M3准备，唯一任务为03共同A/B/C入口、开发预演与冻结清单；重点补齐A/B原生短时返回无需接受事件的共同评价。当前不记整套实验已冻结，不调阈值、不拍新测试片。本轮文档检查通过后本地提交，不推送。

全片误报率仍UNEVALUATED；真实双瓶/相同包装、背景可见新负例、纹理独立贡献与严格速度未验证。现有两段回归不是独立测试；下一步冻结之后才另拍3段，允许如实报告失败。

## 03有界标签纹理对齐开发回归交付（2026-10-02—03）

接手HEAD为 `92ef257`、工作区干净，重新读取规则、SPEC唯一任务、STATUS、旧评价协议/说明及00原图探查。先从原视频保存f170—195共26帧原图，固定人工诊断 `diagnosis/visibility_annotations.json`，再实现/运行。清楚可见11帧、局部不可靠6帧、不确定边界1帧、全遮挡8帧；f187保留UNEVALUATED，不用算法输出重写真值。旧身份依据来自用户无替换/取走替换确认，新身份副本与正例原f847/f852图再次核对，旧标注不改。

实现候选先提交 `124dbcb`：`appearance_recovery.py`增加可关闭的有界标签纹理平移，活动与候选共用比较；`recovery_f180_dev.json`仅新增开关/位移上限/共同区域四项，原配置SHA和所有原门槛保持不变。零位移、位移、共同区域、两侧std、NCC及同一参考的S/门控均逐参考保存。没有修改检测/跟踪、参考因果冻结、状态转换代码或降低门槛。原默认不带新配置时逐字段行为保持一致。

六组完整因果运行另存 `outputs/f180_alignment_dev/`：旧默认正/负例、新对齐正/负例、新配置关闭正/负例，均从原初始化帧复用原检测缓存和原视频。两份新评价协议共用固定人工事件/诊断与身份依据；每个开启/关闭对严格匹配自己的配置SHA与Git版本，不放松旧版本检查。旧协议和四组有效旧结果均保留。

| 开发验收项 | 实际结果 |
| --- | --- |
| f180清楚可见 | 新规则OBSERVED，当前位置来自本帧检测，与人工框IoU0.945882；旧规则UNKNOWN失败保留 |
| 固定26帧诊断 | 可见UNKNOWN由1/11降至0/11；局部6/6、全遮挡8/8仍UNKNOWN；边界1帧不计成正确/错误 |
| 缺失/质量 | f181瓶盖质量无效仍UNKNOWN，首次缺失从180移至181；连续10帧后f190进入LOST（旧189），未强制固定时间 |
| 正例 | 旧/新开启均f852正确恢复1，0错误/未评价接受；f847至852延迟5帧，名义FPS约0.17219秒/源时间约0.18999秒；关闭仍未恢复1 |
| 真实负例 | 原瓶子无返回机会，延迟不适用；148帧合格候选全拒绝，1次替换事件，全程149候选另列；0绑定、0错误当前位置 |
| 模块夹具 | 挂包2拒绝+5质量暂缓，等分6帧暂缓，均0接受；不作为真实双瓶证据 |
| 默认/关闭/参考回归 | 两组旧默认与旧开启384/633帧全部字段/事件/视频SHA一致；两组新配置关闭与旧关闭v2也一致；参考采样/PNG/NPZ/冻结校验不变 |

f180旧最佳S参考f3的NCC0.480005/S0.737272；新最佳S参考f5同一参考零位移NCC0.465362，经(-1,+5)平移得到NCC0.793803、重叠0.933105、std49.3363/47.4011、S0.799862，所有原门控通过。没有混合不同参考分量，没有借用f179历史框；原像素对全部参考重算与记录一致。关闭组不执行外观质量门控，因此f181仍有原生观察，其局部窗1帧有位置/5帧未知是原TargetState行为，不能写成外观质量通过；全遮挡8帧仍未知，详见 `disabled_diagnostic.json`。

收尾发现并补齐相关评价边界：裁剪合格但无可计算参考的DEFERRED_QUALITY列为INSUFFICIENT_EVIDENCE，不当作拒绝/身份通过。新增1项测试；连同对齐边界15项和原54项，实际70项全套通过。评价修正、比较入口与两份新协议先提交 `bdc3587`，随后在空的新v2目录串行重跑评价，两份指标与首轮完全相同。核心运行版本严格核对 `124dbcb`，评价执行版本 `bdc3587`；旧关闭来源仍为 `a167bba`。不改旧SHA、不覆盖首轮报告，当时核查源码和69项历史验证保留。

本轮成功命令（项目根目录；六组运行的完整命令同时保存在说明及 `run_manifest.json` / 各组run_info）：

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_recovery_fixture.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --recovery-output outputs/f180_alignment_dev/aligned_positive --output outputs/f180_alignment_dev/module_fixture --negative-start 223 --negative-end 230 --negative-box 200 120 455 750
.venv/bin/python scripts/evaluate_offline.py --protocol configs/m2_evaluation_f180_legacy.json --output outputs/f180_alignment_dev/evaluation_legacy_v2
.venv/bin/python scripts/evaluate_offline.py --protocol configs/m2_evaluation_f180_aligned.json --output outputs/f180_alignment_dev/evaluation_aligned_v2
.venv/bin/python scripts/review_alignment_development.py --root outputs/f180_alignment_dev --evaluation-legacy outputs/f180_alignment_dev/evaluation_legacy_v2 --evaluation-aligned outputs/f180_alignment_dev/evaluation_aligned_v2 --report outputs/f180_alignment_dev/comparison_v2.json
.venv/bin/python -m compileall -q scripts tests
git diff --check
```

来源核查使用实际Git历史核心逐字段/视频回放，两份评价各解码384/384/633/633帧，负例每种规则各从原视频重解码633帧、人工148帧逐像素重算；关闭TargetState逐字段回放一致。历史366个输出/配置/协议/原视频文件SHA保全；原检测、状态输入和审查证据不变。诊断标注及原图SHA、逐参考对齐分量、逐诊断帧结果、四组指标、来源与测试日志均可检查。最终验收 `comparison_v2.json` / `verification_v2.json` PASS；完整命令与口径 `docs/f180_alignment_development.md`。本轮没有重跑04/00独立审查。

本任务受限开发验收通过，默认仍旧配置，是否采用新配置及冻结交00决定。最终验证记录提交消息为 `docs: record bounded alignment development regression`，本地提交不推送，输出/视频不入Git。全片误报率UNEVALUATED，困难真实输入/M3/严格速度对照UNVERIFIED；搜索增加NCC比较次数，单段负例其他门槛也失败，不能据此证明纹理独立贡献。下一项用户小任务：把本轮最终报告与说明交00，只读核对后决定采纳/冻结；交付物是00的核对结论，验收为明确配置选择与后续任务，暂不拍新片或启动M3。

## 00统一评价核对与f180开发决策（2026-10-02）

03候选实施进度（历史，完整回归结论见上方）：接手HEAD为92ef257、工作区干净，已重新读取规则/新任务与00证据。原画面 `[170,196)` 标注先固定（清楚11、局部6、不确定1、全遮挡8），另存 `outputs/f180_alignment_dev/diagnosis/`；原输出/配置/协议/视频保全清单已保存。实现可关闭的有界标签纹理平移、开发配置及分量合法性核查，未改旧默认配置/门槛/状态代码；69项测试通过。单帧原像素检查f180合法(-1,+5)对齐NCC0.793803、S0.799862，f181仍瓶盖质量无效；这是候选分量检查，完整因果状态/拒绝回归尚未运行。先本地候选提交记录实现版本，再运行完整回归并追加实际结论；不推送、不冻结、不启动M3。

接手HEAD为 `8975df7`、工作区干净；先只读重新读取规则/规格/状态、`docs/offline_evaluation_m2.md`、`configs/m2_evaluation.json`、summary/acceptance_checks、评价/来源核查代码与19项新增测试。接受该评价工具的受限开发交付，不能把f180 FAIL解释为评价工具失败，也不能把报告PASS解释为算法全片通过。

| 证据 | 03实际运行交付 | 00本轮重新核查 |
| --- | --- | --- |
| 四组统一指标 | 完整评价入口生成summary、逐事件、候选覆盖和来源核查 | 另写只读核对脚本，从384/384/633/633条记录、人工标注与事件重算返回机会/正确/未恢复/候选148与149/关闭不适用，匹配报告；未重跑完整评价入口 |
| 来源与保全 | 历史快照核查，362文件保全，视频/状态回放及负例148帧原像素重算 | 对362个文件重新算SHA；核对协议/评价代码/人工记录校验、四组Git历史代码、公共基线全部原字段、诊断计数；未重跑视频/状态或148帧像素验证 |
| 测试 | 54项全套通过、compileall与非空保护通过 | 只重跑新增19项评价边界测试，全部通过；未重跑54项全套/compileall |
| f180 | 明确原瓶子可见而UNKNOWN，报告FAIL；全片误报率UNEVALUATED | 查看原始f179/f180图与相关框/门控记录，确认纹理对齐敏感；只读提取原视频的冻结早期参考与f179—181分量，作有限平移可行性探查，没有运行新状态策略 |

本轮实际命令：`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p test_offline_evaluation.py -v`；另通过`.venv/bin/python -`执行只读记录核对/分量探查，源码与成功输出另存 `outputs/m2_evaluation_00_review/record_checker.py`、`descriptor_probe.py`、`review.json`及测试日志。保存后实际运行 `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python outputs/m2_evaluation_00_review/record_checker.py`，再次核对通过。核对首次把baseline_sha256清单误当单值，修正审查脚本后通过，这是00读取格式错误，项目输出未改。源码保存便于在相同证据/代码版本复核，后续核心代码变化应使用对应历史快照。

探查实测：f180旧最佳参考f3的NCC0.480005/S0.737272；在不改颜色/门槛、±6/±9平移、重叠>=80%限制下，新探查的同一最佳参考f5，平移(-1,+5)、重叠0.9331、NCC0.793803/S0.799862。f179仍高相关；f181瓶盖颜色无效，不进入对齐比较。最佳参考可变化，未混用分量。只涉及3个开发帧，不能证明整体误报下降、拒绝安全或泛化，当前f180运行输出仍FAIL。

核对通过后只更新SPEC/STATUS、保存本轮审查新证据；不改工程代码/核心参数/旧结果。已安排一项03任务：有界标签纹理平移、固定邻帧诊断、正负例/关闭与旧模式回归，验收详见上方和SPEC。新搜索可能抬高错误候选分数，须保留颜色/质量/竞争/连续门槛并完整回归，不能按单帧探查直接认可。

文档检查为 `git diff --check`；本轮本地提交消息 `docs: accept offline evaluation and scope f180 alignment fix`，不推送。配置未冻结，M3正式测试仍暂缓。

## 03统一离线评价交付（2026-10-02）

接手HEAD为 `a5185df`、工作区干净；重新读取规则、规格、状态、关闭统计修复说明、04审查及fix_report、旧独立身份记录和实际四组输出。执行期间00另追加的路线说明保留。本轮仅新增评价/来源核查入口、开发事件适配、说明和必要测试；检测/跟踪、外观核心、`configs/recovery.json`、状态行为及所有旧输出均未修改。

实现：`scripts/evaluate_offline.py`、`scripts/evaluation_sources.py`、`configs/m2_evaluation.json`、`tests/test_offline_evaluation.py`；口径/复跑说明为 `docs/offline_evaluation_m2.md`，README补新入口。开启/关闭共用独立episode_id与expected_return；不使用算法丢失次数作返回机会分母，不用旧PASS字符串或外观门槛作人工真值。

本轮实际执行（项目根目录）：

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/evaluate_offline.py --protocol configs/m2_evaluation.json --output outputs/m2_evaluation_v1
.venv/bin/python -m compileall -q scripts tests
git diff --check
```

新目录 `outputs/m2_evaluation_v1/` 含 `per_event_results.json`、四组 `summary.json`、`candidate_coverage.jsonl`、协议/命令/输入/代码SHA、历史来源核查与前后保全清单；逐项验收断言保存 `acceptance_checks.json`。另实际重复同一评价命令测试非空保护，按预期退出码1，原结果不变；复跑必须换新空目录。

| 组别 | 人工返回机会 | 正确恢复 | 未恢复 | 错误接受 | 身份/拒绝范围 |
| --- | --- | --- | --- | --- | --- |
| 正例开启v3 | 1 | 1（f852） | 0 | 0 | 人工同一瓶子确认与接受框IoU约0.8692 |
| 正例关闭v2 | 1 | 0 | 1 | 0 | 不绑定；外观核验不适用 |
| 负例开启 | 0 | 0 | 0 | 0 | 人工[485,633)148帧合格候选全部外观拒绝，1次替换事件；全程149候选另列 |
| 负例关闭v2 | 0 | 0 | 0 | 0 | 同区间148帧有候选、不绑定；合格/外观拒绝数量null，不计核验通过 |

正例f847→852延迟5帧，名义FPS0.1721898148秒、源时间0.1899888889秒；其余组延迟不适用。两组负例恢复成功率/延迟NOT_APPLICABLE，原瓶子未再出现不算恢复失败。检测缺失、检测但非候选、质量暂缓、合格外观拒绝分开；开启正例候选2帧质量暂缓、6帧合格外观通过，全程8个候选观察（接受帧也保留候选证据）。缺身份的接受单列UNEVALUATED；真实双瓶/同包装等缺真实输入范围UNVERIFIED。

实际来源与保全核查：旧code_sha与Git对象逐文件匹配（正例3163e39、负例3e557e6、两组关闭a167bba），未修改旧SHA或跳过检查；历史脚本在临时目录核查四组记录/参考/配置/视频，重新解码384/384/633/633帧；两组关闭由当时TargetState回放384/633帧、全部原字段/事件一致，确认丢失各1次（f703/f191）。开启负例重新解码源633帧并重算人工区间148帧原像素外观证据；04已有独立重算证据SHA与统计修复引用一致，另复核04清单185个旧输出。评价前后362个任务输入/代码文件SHA一致；核心、参数、原视频、旧输出及审查证据保全。没有重跑推理或04完整独立审查。

本轮54项unittest实际通过（原35+新增19），compileall与验收断言通过。f180原始图已重新查看：原瓶子仍清楚可辨、检测分数约0.922、纹理NCC约0.480导致UNKNOWN；尽管主状态仍TRACKING，新报告记该可见控制点FAIL。关闭组同一控制点仍给位置。只有这一诊断点有明确控制标注，全片误报率及完整可见/遮挡评价为null/UNEVALUATED；不能据此假报全片零误报。

本任务评价口径验收通过；算法f180失败、全镜头遮挡负例、标签贡献未隔离、真实双瓶/同包装/背景持续可见负例未验证、独立测试/速度对照未验证等边界均保留。配置未冻结，M3未启动。本地提交消息为 `feat: unify offline recovery evaluation with manual events`，不推送；输出/视频继续忽略。下一项用户任务：把本段及新summary交00，要求重新读取记录、核对评价口径交付后安排已确定的f180开发处理；无需新增拍摄或先启动M3。

## 00 M2收尾与M3入口决策（2026-10-02）

- 接手HEAD为 `a167bba`、工作区干净；重新读取AGENTS.md、SPEC.md、STATUS.md、统计修复说明、真实负例说明、04的`acceptance_and_findings.json`/`audit_evidence.json`及两组旧通用evaluation；核对评价与恢复核心相关代码。未修改工程代码、依赖、配置或输出。
- 04审查支持正例正确接受1次和真实不同瓶子合格候选拒绝；总控采纳受限开发验收。通用评价的`unrecovered_events`直接使用算法丢失次数减程序接受，不能判断负例是否应该恢复；固定待输入/验收false字段也不能反映本轮开发证据。先修评价，f180在开发收尾中随后处理。
- 实际用现有`.venv/bin/python`一次性只读核对：04验收JSON的SHA与统计修复报告一致；两组disabled_v2的run_info/review SHA均匹配修复报告；读取384/633行记录，确认丢失帧集合分别为{703}/{191}，run_info均为1，检查退出码0。没有重跑模型、恢复视频、04的全像素审查或35项测试；测试通过数是03历史证据，不是本轮重跑。
- SPEC.md已确定当前只做M3评价准备，正式测试暂缓。预定最小范围为两段原瓶子重现+一段背景可见的不同瓶子替换新视频，三组共享缓存与人工事件；明确初始化原生ID选择、标注、恢复/拒绝/误报分母、时间及增量开销边界，并要求代码/配置/协议在正式测试前冻结。
- 双瓶与同包装真实压力测试继续未验证，不挤入本次单一任务；已使用的三段视频都归开发，不从旧片段切出保留测试。新协议尚未实际执行，当前配置未冻结。
- 本轮仅更新SPEC.md与STATUS.md，验证为只读证据核对及`git diff --check`；本地提交消息为 `docs: prioritize evaluation fixes before M3 holdout`，不推送。接手03必须重新读取新决策，完成评价修复后再交00核对下一步。

## 04 M2 第二步独立审查（2026-10-01）

接手时工作区干净，HEAD 为 `5edd342`。已重新读取 AGENTS.md、SPEC.md、完整状态、两份第二步说明、学习/操作确认、原始基线说明，并核对恢复、关闭与评价代码和实际输出。第一轮只审查：工程代码、配置、依赖、SPEC.md 与旧输出均未修改；没有重跑模型推理或本轮 GPU 验证，没有修复下列问题，没有新增代码提交。

### 本轮实际验证与证据

- 用临时一次性审查脚本顺序解码正例全部984帧、负例全部633帧，调用现有状态核心分别回放384/633帧，全部状态字段、原始检测/轨迹/时间字段、参考采样决策与事件逐项匹配交付。此回放复用了现有核心；另外独立编写分区域特征/分数/门槛计算，重算正例6个可计算候选帧、负例全部149个候选帧，与全部参考比较和最佳同一参考记录逐项相同。
- 两组参考各10个原始因果裁剪，分别为f600—609和f0—9；独立从源视频取裁剪，与冻结PNG像素及NPZ颜色/纹理数组一致。源视频、运行代码、配置校验匹配，参考冻结后不更新，无重现帧补库证据。
- 正例f845/f846低分暂缓，f847外观通过但无原生ID、计数0；f848—852同一原生ID5、连续计数1—5且门槛全过，相邻框IoU为0.986—0.995。f852才给出T1位置，初始原生ID4保留。接受最佳参考f602，瓶盖/标签距离0.479519/0.156482、纹理NCC0.725391、S=0.754278，记录与原像素重算一致。
- 已查看正例原始初始化、遮挡、f845—848和接受帧预览，结合保存的拍摄者“只移动原瓶子，没有替换”确认，支持这一次正确物理身份接受。人工接受框与候选IoU约0.8692；可辨认重现f847的图像依据成立，至f852延迟5帧，名义FPS口径约0.17219秒，源时间口径约0.18999秒。时间标注仍为Codex画面核对，未升级为用户逐帧标注。
- 真实负例专项验证本轮重跑PASS：人工区间f485—632共148帧，每帧均有唯一人工区域匹配检测、质量合格且特征可算，全部外观拒绝，0绑定/确认累计、0错误当前位置、全程0接受。整次含f484为149个候选，不能将148帧当作148次独立实验。已查看原始红白/蓝标签画面、全镜头遮挡帧及用户f544截图，身份依据独立于分数与原生ID；截图SHA匹配、T1 native=None/missing=365/UNKNOWN与记录一致。
- 关闭对照384/633帧均逐项匹配重新调用原TargetState得到的所有原有字段与事件；正例同时匹配既有第一步384帧。全程0恢复接受；未将“关闭第二步”误写为关闭全部状态模块。原M1基线仍单独保存，原生ID与原记录不改写。
- 重新解码两组基线、第一步及四组恢复/关闭视频，共7个视频，帧数分别与984/633/384的对应记录一致，均720×1280。逐帧未知位置规则成立，历史框没有作为当前位置回填。两组固定模型校验、检测/跟踪配置、版本与YAML一致；没有据此声称公平速度对照已通过。
- 重跑挂包/等分候选模块夹具：f224/f225合格外观拒绝2帧，其他5帧低分质量暂缓；构造等分候选6帧均暂缓，0接受。它们仍是“真实裁剪+构造丢失上下文”和构造竞争，不是真实双瓶端到端实验。
- 本轮重新运行31项unittest，全部通过（退出码0）；未新增测试或重跑compileall。单元测试不作为模型效果/真实拒绝率。
- 重新核对历史保全清单：正例v2+第一步29文件、新负例基线15文件、此前旧输出84文件及第一步基线14文件均匹配现存SHA。审查前后快照覆盖原输出与工程脚本/测试/配置共201文件，全部不变。新审查结果单独保存于 `outputs/m2_step2_04_review/`。

本轮准确执行命令（项目根目录，均退出码0）：

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python /tmp/m2_step2_04_audit.py outputs/m2_step2_04_review
.venv/bin/python scripts/validate_wrong_bottle.py --output outputs/tabletop_wrong_bottle_01_m2_step2 --annotations outputs/tabletop_wrong_bottle_01_input/identity_annotations.json --report outputs/m2_step2_04_review/wrong_bottle_validation_04.json
.venv/bin/python scripts/validate_recovery_fixture.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --recovery-output outputs/tabletop_02_m2_step2_v3 --output outputs/m2_step2_04_review/module_fixture_rerun --negative-start 223 --negative-end 230 --negative-box 200 120 455 750
git diff --check
```

临时审查脚本原文保存在 `outputs/m2_step2_04_review/audit_driver.txt`；可用 `.venv/bin/python outputs/m2_step2_04_review/audit_driver.txt outputs/m2_step2_04_review_repeat` 复核（该复跑命令本轮未执行，输出路径须不存在）。主要证据为 `audit_evidence.json`、`acceptance_and_findings.json`、独立逐候选重算JSON、专项报告、审查前后SHA及原始关键帧拼图。审查阶段未调用会覆盖旧报告的原核查入口；专项验证在临时目录执行其通用核查。

### 有证据的问题清单与验收结论

| 级别/性质 | 证据 | 影响与结论 |
| --- | --- | --- |
| P2 新发现：关闭分支丢失汇总错误 | `scripts/run_recovery.py:78` 关闭分支推进TargetState，但`:143`取未推进的RecoveryState.loss_episodes。两组关闭run_info均为0，事件在f703/f191各确认1次丢失，见审查JSON的disabled_comparisons | 逐帧关闭等价成立；汇总次数错误会污染M3指标，需03修复并保留旧输出。本轮未修复，未将该字段判为通过 |
| P2 已记录失败：f180可见目标提前UNKNOWN | 原画面仍可见原瓶子；检测分数0.921734、原生ID1，检测框上界由f179的226.64变为280.06；最佳参考f3的纹理NCC0.480005低于0.55，其他门槛通过 | 检测框和相对纹理区域敏感，可靠观察/失效时序仍有误报边界。说明已准确保留，不能声称准确遮挡起点；本轮没有放宽阈值 |
| P3 已记录报告接口问题 | `scripts/review_recovery.py:51—53`固定真实负例PENDING_INPUT与整体验收false；两组evaluation也保留这些字段，负例unrecovered_events=1 | 通用报告只评价接受，不能作本轮总体进度或拒绝评价；负例原瓶子被取走，不应算恢复失败。专项148帧证据有效，建议后续明确报告范围/汇总入口 |
| 已准确记录的输入/贡献限制 | 原负例f189/f240/f350/f480几乎全镜头被挡；人工148帧瓶盖距离0.623—0.652均高于0.55，标签与纹理也失败 | 支持不同瓶子实际拒绝，但不证明背景持续可见的遮挡负例、不单独证明标签贡献或摆脱瓶盖依赖 |
| 明确未验证 | 真实双瓶歧义、同包装替换、背景持续可见的不同瓶子负例、M3保留测试、公平端到端速度对比 | 构造分支/31项测试不替代这些实验；均继续待验证，不写通过 |

**04结论：满足SPEC.md本步“恢复与拒绝”的受限开发交付验收。**依据为独立身份支持的正例正确接受1次、已知挂包合格裁剪拒绝2帧、真实不同瓶子合格候选区间拒绝148帧，且隐藏位置、ID分离、参考因果冻结、证据保全与逐帧关闭对照成立。新统计问题不推翻这两段的恢复/拒绝证据，但在M3汇总前必须处理。仅限已查看的开发输入，不宣称准确率、通用ReID或独立测试通过；下一项建议见上方，由03修正统计与报告口径。

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

## 03 真实不同瓶子验证交付（2026-10-01）

接手工作区干净，HEAD为 `3163e39`，已重读规则、规格、状态及实际实现。用户新视频原件保留，副本/原件SHA-256一致：`585f9ba9048b672fd39acabdaa8b5164e1a2d45be965d741081e9e8e2322b51f`。用户确认“是，换成了另一只瓶子，原瓶子未再入镜”，另存人工身份记录，不由算法分数生成真值。

- 原始读取与顺序抽帧均633帧，720×1280、29.91038名义FPS、约21.163秒。已查看首帧、逐秒预览、原始重现f480/485/490/495/500、f180与最终状态拼图。
- 固定YOLO11n/ByteTrack原条件首次运行此输入，在原有GPU实际校验和推理通过；模型/版本/推理/跟踪配置与旧v2一致。恢复后处理复用新基线633条记录，不改核心脚本、配置或依赖。
- 初始化原f0人工框 `[290,280,510,1040]`，因果参考f0—9共10个后冻结。f180纹理门控失败清空位置、f189确认LOST、f484候选出现；全程0接受。原瓶子仍可见时的提前UNKNOWN如实保留。
- 人工清楚可见区间f485—632共148帧，以独立人工空间区域匹配蓝标签另一瓶子；每帧都质量合格且特征可算，全部REJECTED_APPEARANCE，0缺检测/质量暂缓、0绑定/错误当前位置。原像素重算质量/最佳参考/门槛逐项相同。含区间前f484的整次候选共149个。
- 代表f500检测分数约0.9303、新原生ID已关联，但标签距离约0.8699、纹理NCC约-0.2142、S约0.3038，拒绝。瓶盖距离约0.6414也未过门槛，所以不单独归因标签模块或声称消除了红盖依赖。
- 新增真实负例核查入口，每次重新核查当前记录与视频，在临时目录保留原核查输出；只凭合格候选实际门槛判断，不信缓存布尔值/拒绝字符串。补8项负例评价测试，与原23项合计31项通过；compileall通过。
- 关闭模块另存633帧，逐帧调用原TargetState比较全部原字段一致；旧正例/第一步/关闭/模块与身份记录共84个文件前后SHA未变，新基线15个文件保全。汇总见 `comparison_and_preservation.json`。
- 通用评价器的真实负例字段仍固定PENDING_INPUT、unrecovered_events=1，仅记录接受/未接受，不能表示本片待输入或负例失败；实际拒绝以专项 `wrong_bottle_validation_v2.json` 为准，原报告保留。
- 真实替代瓶子拒绝PASS与已有正例正确接受1次、挂包模块拒绝2帧共同支持开发恢复/拒绝交付，待00/04复核验收；全镜头遮挡、双瓶/同包装/独立测试等限制保留。没有推断普遍准确率，没有进行速度基准。

准确成功命令（GPU基线沙箱外；其余沙箱内）：

```bash
.venv/bin/python scripts/inspect_video.py --source data/tabletop_wrong_bottle_01.mp4 --output outputs/tabletop_wrong_bottle_01_input
.venv/bin/python scripts/run_baseline.py --source data/tabletop_wrong_bottle_01.mp4 --output outputs/tabletop_wrong_bottle_01_baseline --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/review_baseline.py --output outputs/tabletop_wrong_bottle_01_baseline --frames 0 9 180 190 480 485 500 632
.venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/tabletop_wrong_bottle_01_m2_step2 --init-frame 0 --init-box 290 280 510 1040 --missing-frames 10 --config configs/recovery.json
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_wrong_bottle_01_m2_step2 --frames 0 9 179 180 181 189 480 484 485 500 600 632
.venv/bin/python scripts/validate_wrong_bottle.py --output outputs/tabletop_wrong_bottle_01_m2_step2 --annotations outputs/tabletop_wrong_bottle_01_input/identity_annotations.json --report outputs/tabletop_wrong_bottle_01_m2_step2/wrong_bottle_validation_v2.json
.venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/tabletop_wrong_bottle_01_m2_disabled --init-frame 0 --init-box 290 280 510 1040 --missing-frames 10 --config configs/recovery.json --disable-recovery
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_wrong_bottle_01_m2_disabled --frames 0 181 182 191 484 485 500 632
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts tests
```

本轮只新增验证入口/测试及更新文档，本地提交消息为 `feat: validate real different-bottle rejection`，不推送；视频、原始输出与身份记录继续Git忽略。说明见 `docs/wrong_bottle_m2_validation.md`。用户下一项仅观看末段输出给反馈；后续验收与M3范围由00/04重新读取记录安排。

## 03 收到真实负例观看反馈（2026-10-01）

- 用户补充完整截图并反馈约16—21秒未出现T1已绑定框，上方显示T1 native:None missing:365 position:UNKNOWN，候选标记REJECTED_APPEARANCE native:2 n:0、橙色框存在。原反馈拼写与截图分别保存，不扩写为用户理解或整体验收。
- 实际运行 `.venv/bin/python -` 一次性读取已有 `outputs/tabletop_wrong_bottle_01_m2_step2/frames.jsonl`，核查截图原f544/估算18.19秒：状态RECOVERY_CANDIDATE，活动ID为空、当前框为空、position_known=false、缺少可靠观察365帧（f180—544），候选ID2拒绝、连续计数0、未绑定。退出码0，与截图一致。
- 截图副本、SHA和用户反馈/核对存于 `outputs/tabletop_wrong_bottle_01_feedback/frame_544_user_screenshot.png`、`feedback.json`，新目录保存，不覆盖原运行结果。未重跑模型、状态生成或测试；只核查已有记录并更新三份文档。
- 已解释原目标标签、原生候选ID、连续缺少可靠观察计数与合格确认计数的区别；橙色框仅标出被拒绝候选。用户观看任务完成；下一项为00/04重读记录与输出后复核交付。
- 文档检查为 `git diff --check`，本地提交消息 `docs: record rejected candidate viewing feedback`，不推送。原实现/真实负例提交分别为 `3163e39` / `3e557e6`；图片/反馈JSON继续Git忽略。

## 03 修复04发现的关闭统计（2026-10-01）

接手HEAD为 `5edd342`，STATUS.md已有04未提交的完整审查记录，已读取并完整保留，纳入本轮交接。只修复P2关闭统计，f180提前UNKNOWN与P3评价口径保留未修，不修改SPEC.md、外观模块、检测/跟踪器、阈值、依赖或旧输出。

- 原因：关闭分支实际推进TargetState，却读取未推进的RecoveryState.loss_episodes。改为实际关闭状态的loss_latched汇总；第一步不自动恢复，每次最多1段丢失。LOST/候选切换不重复计数，直接进入候选的确认丢失也计入。
- 核查器新增关闭汇总与逐帧confirmed_lost_frame去重的一致性检查。新增4项微型视频/检测记录回归：状态反复切换、确认后只有候选状态、短缺失重观测、错误零计数被核查拒绝。35项unittest与compileall通过。
- 两组新关闭v2各正确记录1次丢失（f703/f191），0次尝试/接受；重新解码384/633帧。全部逐帧字段、事件与旧输出一致，视频SHA也完全相同；全部原有字段与原TargetState逐帧回放一致。正例另与第一步比对通过。
- 旧运行与04审查输出184文件前后SHA一致。新运行/核查保全原基线/第一步29文件及新输入基线15文件。旧错误run_info不改写，当前关闭统计使用新v2目录。
- 修复证据为 `outputs/m2_disabled_stats_fix/fix_report.json`、`old_outputs_before.json`；说明为 `docs/m2_disabled_statistics_fix.md`。原开启正负例未重跑，沿用04审查证据；代码SHA变化使旧输出的通用核查需使用当时 `5edd342` 版本，不能改写旧SHA绕过检查。

实际成功命令（项目根目录，退出码0，未运行GPU/模型推理）：

```bash
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/tabletop_02_m2_step2_disabled_v2 --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery.json --disable-recovery
.venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/tabletop_wrong_bottle_01_m2_disabled_v2 --init-frame 0 --init-box 290 280 510 1040 --missing-frames 10 --config configs/recovery.json --disable-recovery
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_02_m2_step2_disabled_v2 --frames 600 694 703 845 848
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_wrong_bottle_01_m2_disabled_v2 --frames 0 182 191 484 485 632
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts tests
git diff --check
```

本地提交消息为 `fix: report confirmed loss in disabled recovery runs`，不推送；输出/视频继续Git忽略。下一项是用户交给00结合04受限验收和本次修复，决定M3最小范围及f180/P3的处理顺序，不把未运行事项写为已解决。

## 00 完成效果与后续路线说明（2026-10-02）

- 用户询问第一版完成后的可见效果与后续发展。本轮重读项目规则、规格、状态、M2实现说明与配置，核对恢复代码、正例事件记录、旧负例评价及实际f852恢复截图；未重跑推理、恢复流程或测试。
- 第一版完成目标沿用M0—M4：可复现离线二维Demo，显示目标已观察/位置未知、候选核验、恢复或拒绝，并交付独立小规模对照及失败分析。现有开发正负例不代表独立测试性能；旧负例评价入口的问题仍按当前优先任务修复。
- 后续建议为先建立更充分的评价与身份/可靠性方法对照，再视兴趣与资源选择3D位姿及仿真闭环；动作条件世界模型作为闭环阶段候选。这是发展建议，未新增已批准范围、修改SPEC或启动后续实现。
- 本轮只更新交接说明；无新增可运行里程碑。验证为`git diff --check`。唯一下一项任务仍为03统一离线评价口径，交付与验收继续按SPEC/本文件执行；不额外要求用户拍摄或重复观看。

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
