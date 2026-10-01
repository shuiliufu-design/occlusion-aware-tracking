# M2 关闭分支统计修复

2026-10-01，04独立审查确认恢复/拒绝满足受限开发验收，同时发现两组关闭报告丢失次数错误。03本轮只修正该统计并增加核查/回归测试，保留04未提交的审查记录、旧输出及其他未修问题。

关闭运行实际推进原 `TargetState`，却从未推进的 `RecoveryState` 读取 `loss_episodes`，导致旧报告为0。修复改为从实际关闭状态的 `loss_latched` 统计：第一步确认丢失后不自动恢复，因此每次关闭运行最多1段丢失；LOST与RECOVERY_CANDIDATE之间来回切换不重复计数。开启分支仍使用原恢复状态机计数，检测、状态行为和外观参数不变。
通用核查新增关闭报告与逐帧 `confirmed_lost_frame` 的一致性检查，错误汇总直接失败。

| 输入 | 修复后关闭输出 | 丢失次数 | 确认帧 | 与旧输出比较 |
| --- | --- | --- | --- | --- |
| tabletop_02 | `outputs/tabletop_02_m2_step2_disabled_v2/` | 1（旧报告0） | f703 | 384条记录、全部事件与视频SHA完全一致 |
| wrong_bottle_01 | `outputs/tabletop_wrong_bottle_01_m2_disabled_v2/` | 1（旧报告0） | f191 | 633条记录、全部事件与视频SHA完全一致 |

两组都0次尝试、0次接受，全部原有字段与逐帧调用原TargetState一致。新视频重新解码分别384/633帧。旧运行与04审查证据184个文件前后SHA一致；既有两组基线/第一步的29/15文件也由新运行与核查保全。
统计修复证据为 `outputs/m2_disabled_stats_fix/fix_report.json`、`old_outputs_before.json`；旧输出继续保存原错误报告，用于问题溯源，当前关闭统计以新v2目录为准。

本轮实际成功命令（项目根目录，全部在现有环境中）：

```bash
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/tabletop_02_m2_step2_disabled_v2 --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery.json --disable-recovery
.venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/tabletop_wrong_bottle_01_m2_disabled_v2 --init-frame 0 --init-box 290 280 510 1040 --missing-frames 10 --config configs/recovery.json --disable-recovery
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_02_m2_step2_disabled_v2 --frames 600 694 703 845 848
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_wrong_bottle_01_m2_disabled_v2 --frames 0 182 191 484 485 632
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts tests
git diff --check
```

35项测试通过（原31+新4）：微型视频+已知检测记录覆盖丢失/候选反复切换只计1段、确认帧直接为候选而未出现LOST仍计1段、短缺失后重观测计0段，以及核查器拒绝旧的错误零汇总。测试不作为模型效果证据。
本轮没有重跑模型推理或开启恢复的正负例；开启行为和外观模块未改，沿用04已经独立核查的历史证据。旧输出记录的代码SHA对应当时提交 `5edd342`；当前脚本因报告修复而改变，新通用核查对旧输出会提示代码不同，历史核查应使用当时版本，不能改旧SHA绕过来源检查。

仍未修复：P2 f180可见原目标提前UNKNOWN、P3通用evaluation固定PENDING_INPUT/整体false的范围问题。真实双瓶歧义、同包装替换、背景持续可见的不同瓶子负例、M3保留测试和速度对照仍未验证。本轮不把这项报告修复写成解决上述问题。
下一项：用户将04受限验收与03修复结果交给00，重新读取SPEC/STATUS和实际证据，确定是否进入M3、先处理哪些剩余问题及最小实验范围；决策由00写入SPEC.md。
