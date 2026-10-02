# f180 有界标签纹理对齐开发候选

依据 SPEC.md 2026-10-02 的唯一优先任务，增加可关闭的标签纹理整数平移。旧 `configs/recovery.json` 保持原内容/SHA和默认行为；开发配置为 `configs/recovery_f180_dev.json`，新增四项：启用开关、横/纵最大位移比例0.10、最小共同区域0.80。这不是M3冻结。

在64×96标签纹理上，仅搜索包含零位移的±6/±9像素；`shift_xy`表示参考坐标=候选坐标+位移。两边仅取真实共同区域，不填充、不复制边缘、不改变尺度/旋转。共同面积>=80%、两侧std>=5、NCC有限才可比较；无有效证据则暂缓。每个参考取合法最佳NCC，再与该参考的原颜色/形状分量算S，最后按原最高S/门控/竞争规则选择；同ID不免核验。等NCC时按最小曼哈顿位移、dy、dx稳定排序，优先零位移。

原颜色/区域/质量/权重/门槛、NCC>=0.55、S>=0.70、差值0.10、确认5帧、缺失10帧均不改；不读取人工诊断标注或未来帧，不借用历史框，不更新冻结参考。活动轨迹与恢复候选共用 `compare_feature`。每项参考保存零位移NCC、选中位移、共同区域/面积/std、最终NCC/S及模式；分量核查检查合法几何与分数。

原图标注先于实现/运行固定到 `outputs/f180_alignment_dev/diagnosis/visibility_annotations.json`，区间 `[170,196)`：清楚 `[170,181)`、局部不可靠 `[181,187)`、边界不确定 `[187,188)`、全遮挡 `[188,196)`。逐帧PNG/SHA与两张拼图保留，不能按算法失效帧定义真值。清楚帧人工框为目视近似区域，非全片逐帧真值。

候选实现阶段（历史）实际运行69项测试通过（原54+新增15），包含合法/超限平移、重叠、共同区域退化/非有限值、关闭保持原数值字段、同一最佳参考、竞争、同ID错误外观、质量暂缓、连续确认/恢复后再丢失。当时f180单帧因合法对齐通过、f181仍CAP_INSUFFICIENT_COLOR仅为分量检查；完整因果回归及最终70项测试结果见下文。

从各片原始初始化顺序运行，沿用固定检测缓存：

```bash
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/f180_alignment_dev/legacy_positive --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery.json
.venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/f180_alignment_dev/legacy_negative --init-frame 0 --init-box 290 280 510 1040 --missing-frames 10 --config configs/recovery.json
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/f180_alignment_dev/aligned_positive --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery_f180_dev.json
.venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/f180_alignment_dev/aligned_negative --init-frame 0 --init-box 290 280 510 1040 --missing-frames 10 --config configs/recovery_f180_dev.json
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/f180_alignment_dev/aligned_disabled_positive --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery_f180_dev.json --disable-recovery
.venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/f180_alignment_dev/aligned_disabled_negative --init-frame 0 --init-box 290 280 510 1040 --missing-frames 10 --config configs/recovery_f180_dev.json --disable-recovery
```

复跑换新空输出，保留全部旧输出/标注/协议及原配置。搜索会抬高分数，必须同时通过真实负例148帧拒绝、挂包/等分夹具、隐藏位置与默认/关闭回归后才可接受；目前M3未启动、配置未冻结。

## 完整开发回归（2026-10-02—03）

候选实现先保存本地提交 `124dbcb`；六次上述运行随后实际成功，输出/协议的代码SHA均与该提交内容匹配。旧/新规则分别用严格共同开关输入校验评价，原人工事件/返回机会不改变；新诊断标注与身份副本另存，原记录/协议未改。

```bash
.venv/bin/python scripts/validate_recovery_fixture.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --recovery-output outputs/f180_alignment_dev/aligned_positive --output outputs/f180_alignment_dev/module_fixture --negative-start 223 --negative-end 230 --negative-box 200 120 455 750
.venv/bin/python scripts/evaluate_offline.py --protocol configs/m2_evaluation_f180_legacy.json --output outputs/f180_alignment_dev/evaluation_legacy
.venv/bin/python scripts/evaluate_offline.py --protocol configs/m2_evaluation_f180_aligned.json --output outputs/f180_alignment_dev/evaluation_aligned
.venv/bin/python scripts/review_alignment_development.py --root outputs/f180_alignment_dev
.venv/bin/python outputs/f180_alignment_dev/disabled_diagnostic_check.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts tests
```

上述实际执行均成功；单元测试在候选提交前已实际运行69项，完整视频回归后未无故重复。诊断/身份/协议生成采用项目根目录的一次性Python，产物保存明确边界、来源/标注SHA与原图；评价复跑须另存新协议/根目录及空输出。比较核查若comparison.json已存在会拒绝覆盖，不把旧PASS当新验证。关闭诊断脚本源码也保留在本地输出供复核。

| 开启第2步的检查 | 旧规则 | 开启有界对齐 |
| --- | --- | --- |
| 清楚可见 `[170,181)` | UNKNOWN 1/11（f180） | UNKNOWN 0/11 |
| 局部不可靠 `[181,187)` | 6帧均UNKNOWN | 6帧均UNKNOWN，f181瓶盖质量无效，不进入对齐 |
| 边界 `[187,188)` | 位置未知 | 位置未知；物理边界不确定，不计可见/隐藏成功率 |
| 全遮挡 `[188,196)` | 8帧均UNKNOWN | 8帧均UNKNOWN，0当前位置 |
| 首次缺失 / LOST | f180 / f189 | f181 / f190，缺失10帧；未硬凑旧事件时刻 |
| 正例返回 | 正确接受f852，错误/未评价接受0 | 相同；从人工f847延迟5帧，名义FPS0.1721898148秒、源时间0.1899888889秒 |
| 人工替代瓶子 `[485,633)` | 148合格拒绝，1次事件 | 148合格拒绝，1次事件；0接受/绑定/错误当前位置，全程149候选另列 |
| 挂包 / 等分夹具 | 2拒绝+5质量暂缓 / 6帧等分暂缓 | 相同，0接受；不升级为真实双瓶证据 |

f180旧最佳S参考f3：NCC0.480005、S0.737272。新最佳S参考f5：同一参考零位移NCC0.465362，经位移(-1,+5)后0.793803，共同区域0.933105、两侧std49.3363/47.4011，S0.799862，全部原门槛通过。参考可以改变，未混合不同参考分量；当前框直接来自f180检测，与本轮人工T1框IoU0.945882，未借用f179历史框。原图分量逐参考重算与状态证据完全相同。已经查看f180/f181状态图与正例原始f847/f852；新接受时刻未改变，独立身份/框另存副本并再次核对。

关闭第2步依旧退回原TargetState，四组汇总中的外观质量/身份核验NOT_APPLICABLE。它在f181原生轨迹仍在时保留位置，局部诊断6帧中1帧有位置、5帧未知；8帧全遮挡仍全部未知。该行为与旧关闭逐字段/事件/视频SHA一致，不能写成关闭组通过了外观质量暂缓。详见单列的disabled_diagnostic.json。

两组旧默认重跑384/633帧与旧开启逐字段/事件/视频SHA完全一致；两组新配置关闭384/633帧与旧关闭v2也完全一致。冻结参考的采样、PNG/NPZ与记录校验均不变。旧/新评价各重新解码4组状态视频，使用对应Git快照核查记录；负例各从原视频重新解码633帧并重算人工区间148帧的质量与最佳参考/对齐分量。原有366个输出/原视频/原配置/旧协议文件SHA保全。没有重跑检测或更换跟踪器。

收尾补齐“裁剪质量合格但无可计算比较”的评价边界：DEFERRED_QUALITY且best_reference为空时列为INSUFFICIENT_EVIDENCE，不把它写成拒绝或合格外观通过。返回机会、身份/IoU口径均不变。该兼容修正、比较入口和协议先提交 `bdc3587`；随后在新的v2评价目录串行复跑，不覆盖第一轮。最终70项测试通过（原54+对齐安全15+评价边界1），日志tests_final.log；compileall通过。首轮comparison.json及当时核查源码review_checker_v1.py、69项验证记录均保留，最终交接使用comparison_v2.json/verification_v2.json与两组evaluation_*_v2目录。

```bash
.venv/bin/python scripts/evaluate_offline.py --protocol configs/m2_evaluation_f180_legacy.json --output outputs/f180_alignment_dev/evaluation_legacy_v2
.venv/bin/python scripts/evaluate_offline.py --protocol configs/m2_evaluation_f180_aligned.json --output outputs/f180_alignment_dev/evaluation_aligned_v2
.venv/bin/python scripts/review_alignment_development.py --root outputs/f180_alignment_dev --evaluation-legacy outputs/f180_alignment_dev/evaluation_legacy_v2 --evaluation-aligned outputs/f180_alignment_dev/evaluation_aligned_v2 --report outputs/f180_alignment_dev/comparison_v2.json
```

交付根目录 `outputs/f180_alignment_dev/`：

- `comparison_v2.json`：最终逐项验收、旧/新指标、参考/配置/代码与保全结果；首轮comparison.json保留。
- `diagnosis/visibility_annotations.json`、原图及拼图：先行固定的26帧人工诊断，边界不确定保留。
- `diagnostic_by_frame.jsonl`、`alignment_components.jsonl`：逐诊断帧与旧/新全程逐参考分量。
- `legacy_positive/`、`legacy_negative/`、`aligned_positive/`、`aligned_negative/`、两组`aligned_disabled_*/`：视频、记录、事件、参考与运行来源。
- `evaluation_legacy_v2/`、`evaluation_aligned_v2/`：相同人工事件/诊断下的最终四组评价、历史来源和像素核查；首轮目录保留。
- `annotations/`、`review_images/`、`module_fixture/`、`disabled_diagnostic.json`、`verification_v2.json`及前后保全清单。

本次受限开发修正验收通过；旧默认策略继续保留，是否采用新配置及最终冻结由00根据证据决定。搜索会改变分数分布、增加每参考NCC比较次数，本轮未作严格速度基准。全片误报率仍UNEVALUATED；单段负例中瓶盖/标签也失败，未隔离纹理贡献。背景持续可见的负例、真实双瓶/同包装替换及M3独立测试仍UNVERIFIED，配置未冻结，M3未启动。
