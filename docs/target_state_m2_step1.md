# M2 第一步：指定目标、丢失判断与恢复候选

2026-10-01，03 实际复用 `outputs/tabletop_02_baseline_v2/` 和原视频，完成后半段纸板遮挡的状态输出。
本步不执行身份匹配或恢复绑定，不表示 M2 全部验收。没有新增依赖、重跑检测或修改 ByteTrack。

## 输入与初始化

`scripts/run_target_state.py` 接收原视频、基线目录、原视频初始化帧、人工框与缺失阈值。
框为原图像素坐标 `[左, 上, 右, 下]`。初始化必须唯一匹配一项已关联的 bottle 检测，IoU 不低于 `--init-iou`；未匹配、多个匹配或检测尚无轨迹 ID 时拒绝运行。并非挑选分数最高的任意瓶子。

本次 03 查看原视频第 600 帧后，将红盖瓶子框指定为 `[180, 450, 305, 870]`；这是本次演示的可修改配置，不是用户已确认的人工真值标注。
与 v2 检测框 IoU 为约 0.8896，匹配到原生 ID 4。ID 来自记录，不作为脚本常量。
`--missing-frames 10` 在名义 29.0377 FPS 下约为 0.3444 秒，是演示阈值，尚未调优或证明最优。阈值按处理帧计数，不按源时间差计数。

输入视频 SHA-256 必须与基线一致；记录帧索引必须连续，数量与基线处理/更新帧数一致。
视频从头顺序解码以保留帧对应关系；只输出初始化帧至 `--end-frame`（不含该帧，默认至结尾），不使用 seek 截取实际运行输入。

## 三种状态如何转换

| 条件 | 状态与输出 |
| --- | --- |
| 初始化成功，或确认丢失前原生初始轨迹仍有输出 | `TRACKING`；当前目标框来自该轨迹，缺失计数清零 |
| 初始轨迹缺失但尚未达到阈值 | 保留 `TRACKING` 决策，`pending_loss=true`；本帧无目标观察，当前框为空、位置 UNKNOWN；历史框只保留在记录中 |
| 连续缺失达到阈值，且无同类检测 | `LOST`；丢失锁定，当前目标位置未知 |
| 丢失锁定后出现同类检测 | `RECOVERY_CANDIDATE`；所有候选均 UNVERIFIED、不绑定原目标，当前目标框仍为空 |
| 候选再次消失 | `RECOVERY_CANDIDATE → LOST`；仍处于丢失锁定 |

“连续缺失”指人工初始化后，原生初始轨迹未被接受为本帧目标观察的连续帧数，不是全画面无检测帧数。其他 ID 不能替代目标或清零计数。
达到阈值前，相同 ID 短暂消失又出现，仍按 ByteTrack 的连续跟踪输出处理；这不是新增身份恢复能力，也不证明没有错误关联。
达到阈值后，即使初始 ID 再次出现，也只作为候选；本步没有从 LOST/RECOVERY_CANDIDATE 自动回 TRACKING 的路径。

同类别只是候选筛选条件，候选可能是别的瓶子或误检。候选记录保存检测框、检测索引、类别、检测分数、原生 ID（允许空），以及 `identity_check.performed=false`、`status=UNVERIFIED`、`bound_to_target=false`。
检测分数不代表身份概率或跟踪可靠性。没有输出框也不能单独证明实际完全遮挡。

## 实际运行与结果

从项目根目录运行，复跑须使用新的空输出目录：

```bash
.venv/bin/python scripts/run_target_state.py --baseline outputs/tabletop_02_baseline_v2 --source data/tabletop_02.mp4 --output outputs/tabletop_02_m2_step1 --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --init-iou 0.5
.venv/bin/python scripts/review_target_state.py --output outputs/tabletop_02_m2_step1 --frames 600 693 694 702 703 844 845 848
.venv/bin/python -m unittest discover -s tests -v
```

原视频全部顺序解码 984 帧，输出 f600—983 的 384 帧。状态记录与输出视频重解码数量一致，720×1280；原检测、轨迹、原帧索引与两种时间字段完整保留且与 v2 相同。
视频从 f600 开始，播放器的 0 秒对应原帧 f600；`output_frame_index` 从 0 计数，主 `frame_index` 仍是原视频帧号。

| 原帧区间（含端点） | 状态 | 实际证据 |
| --- | --- | --- |
| f600—693 | TRACKING，有本帧目标观察 | 人工初始化引用的原生轨迹持续输出，共 94 帧 |
| f694—702 | TRACKING，缺失宽限期 | 连续缺失 1—9 帧；当前框立即清空、位置未知 |
| f703—844 | LOST | f703 为第 10 个缺失帧；142 帧丢失状态 |
| f845—983 | RECOVERY_CANDIDATE | 139 帧候选；f845 原生 ID 为空、检测分数约 0.154；f848 获得 ID 5，但仍不绑定原目标 |

状态计数：TRACKING=103（含 9 帧宽限期）、LOST=142、RECOVERY_CANDIDATE=139。
状态事件 3 条：f600 初始化（null→TRACKING）、f703 TRACKING→LOST、f845 LOST→RECOVERY_CANDIDATE。
f703/f845 的主估算时间约为 24.210/29.100 秒，源时间字段约为 24.478/29.221 秒；这些是记录时间，不是人工遮挡或重现标注。

输出目录 `outputs/tabletop_02_m2_step1/`：

- `status.mp4`：绿框为本帧指定轨迹观察，黄框为 UNVERIFIED 候选；不绘制历史框或隐藏目标预测框。mp4v、名义恒定帧率、无音频。
- `frames.jsonl`：完整原基线证据，以及状态、缺失计数、丢失起始/确认帧、当前位置、历史观察和候选。
- `events.jsonl`：初始化与状态转换；保留触发帧的时间、缺失与候选证据。
- `run_info.json`：准确命令、初始化匹配、全部可配置参数、原输入/基线校验、继承的模型与 ByteTrack 条件、状态统计。
- `review.json`、`frame_*.jpg`、`contact_sheet.jpg`：数据/事件/视频核查和关键帧预览。
- `baseline_preservation.json`：本次运行前后 v2 全部 14 个文件的校验值与一致性结果。

## 验证与边界

8 项 unittest 通过：缺失阈值边界、宽限期位置未知、其他 ID 不重置缺失、原生短缺失连续性、确认丢失后同 ID 仍只是候选、未关联/多候选不绑定、初始化歧义拒绝、任意初始 ID/输入不变/不连续帧拒绝及无效参数。
这些合成记录只验证状态逻辑，不作为模型或恢复效果证据。

真实结果核查通过：原基线字段逐项一致、缺失计数与阈值正确、无观察时当前框为空、候选未绑定、事件与状态变化一致、384 条记录与视频重解码一致。
已查看原始初始化帧与八帧状态预览（f600/f693/f694/f702/f703/f844/f845/f848）。
另经 subprocess 实际检查非空输出、未匹配人工框、错误源视频三条错误路径，均按预期退出码 1；两个无效输入路径没有创建输出目录。
错误路径实际命令：

```bash
.venv/bin/python scripts/run_target_state.py --baseline outputs/tabletop_02_baseline_v2 --init-frame 600 --init-box 180 450 305 870 --source data/tabletop_02.mp4 --output outputs/tabletop_02_m2_step1
.venv/bin/python scripts/run_target_state.py --baseline outputs/tabletop_02_baseline_v2 --init-frame 600 --init-box 180 450 305 870 --source data/tabletop_02.mp4 --output outputs/m2_invalid_init_check --init-box 0 0 100 100
.venv/bin/python scripts/run_target_state.py --baseline outputs/tabletop_02_baseline_v2 --init-frame 600 --init-box 180 450 305 870 --source data/tabletop_01.mp4 --output outputs/m2_wrong_source_check
```

保留原始对照：v2 的 14 个文件运行前后 SHA-256 全部一致，M1 两个脚本均未修改。关闭新增模块即直接使用 `outputs/tabletop_02_baseline_v2/annotated.mp4` 与 `frames.jsonl`；重跑原始检测/跟踪沿用 README 的 `run_baseline.py` 命令并更换输出目录。不需要为了关闭后处理重跑模型。

新增贡献仅是指定目标、缺失状态判断、候选证据与视频/事件输出。原生检测、关联、短时丢失后同 ID 输出属于 M1/ByteTrack。
本次复用已有检测计算，是离线后处理验证；没有执行端到端速度对比、身份/遮挡标注、错误恢复指标或独立测试。
已知限制：TRACKING 只表示原生连续性假设，仍可能跟错；候选仅按类别筛选，误检或相似目标也会入选；阈值敏感性尚未评价。当前保持全部候选未绑定，无法宣称恢复成功。

下一项用户任务：观看状态视频，确认瓶子消失时无当前位置框、纸板移开后黄框标为 UNVERIFIED，并在 `docs/learning_log.md` 记录观察及一个疑问。交付为简短观察；验收为能区分“候选出现”和“原目标身份已恢复”。之后由 00 确定 M2 第二步的身份证据与判定规则。
