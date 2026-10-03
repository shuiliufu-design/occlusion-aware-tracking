# M3 三片冻结 HOLDOUT 对照

2026-10-03，按00采纳的输入准备和 `docs/m3_holdout_comparison_task.md` 实际完成三片A/B/C。实验交付核查PASS；A/B各两次未返回，C两次正确返回、一次替换事件的130个合格候选拒绝。C仍有连续确认期间的可见UNKNOWN。结论限于有拍摄偏差的三片小规模保留测试；全片精确误报率未评价，速度未验证。

最终结果 `outputs/m3_holdout_comparison_v2/`，最终协议 `configs/m3_holdout_v2.json`。初轮 `outputs/m3_holdout_comparison_v1/`、v1标签/协议、全部开发证据保留。没有重新推理或修改冻结算法/阈值/初始化/参考规则/人工事件。

## 共同输入与独立分母

三片341/476/573帧，三个既有YOLO11n+ByteTrack缓存各只推理过一次，共1,390帧。本轮只顺序读取原像素与缓存；每轮九组共4,170条记录/视频帧，仍是三段独立视频和三个人工事件。每组分母为两个期待T1返回事件；替换事件取走T1且不再出现，零返回机会，不计恢复失败/零延迟。

A只沿初始化原生ID；B沿冻结的TargetState，确认丢失后仅候选；C使用冻结的有界对齐外观恢复。A/C当前框来自本帧检测，B保持原TargetState的已关联轨迹框且有本帧检测映射；各组按自己实际当前框与同一原图人工框IoU>=0.5评价。原生ID或检测分数不证明物理身份。

物理操作由用户确认；框/可见性为Codex原图标注，无第二位人类逐帧复核。人工f204/f279是保守可辨认锚点，附近不确定/局部框不足保留，不声称精确最早可辨认时刻。每10原帧固定样本141，其中清楚T1为31+37+20=88；接受关键帧不扩这个分母。

## 实际逐事件结果

| 事件 | A原始选择 | B状态/候选 | C身份恢复 |
| --- | --- | --- | --- |
| return_01，同瓶原位一次返回机会 | 未返回FAIL | 未返回FAIL | f214正确返回PASS，自定义接受；相对f204延迟10帧，名义0.333278秒、源时间0.333333秒 |
| return_02，同瓶移位一次返回机会 | 未返回FAIL | 未返回FAIL | f283正确返回PASS，自定义接受；相对f279延迟4帧，名义0.133311秒、源时间0.133289秒 |
| replacement_01，T1已移除不返回 | 返回/延迟不适用；没有外观核验 | 返回/延迟不适用；没有外观核验 | 返回/延迟不适用；130合格候选全部外观拒绝PASS，0绑定 |

| 组 | 正确返回/人工机会 | 未返回 | 清楚T1固定样本UNKNOWN | 已核对自定义正确/错误/未评价接受 |
| --- | --- | --- | --- | --- |
| A | 0/2 | 2 | 34/88（38.636%） | 不适用 |
| B | 0/2 | 2 | 34/88（38.636%） | 不适用 |
| C | 2/2 | 0 | 2/88（2.273%） | 2 / 0 / 0 |

逐片UNKNOWN为A/B 14/31、20/37、0/20；C 1/31、1/37、0/20。B/C在人工CLEAR T1区间内错误确认LOST事件各0，但仍保留返回后的UNKNOWN空窗。三组在人工目标缺席的25/92/375帧（各组合计492）均0错误当前位置；已审计框中没有错误框。局部已观察框不足：第一片f169 A/B/C、第二片f168 A/B/C、替换片f195 A/B仍UNEVALUATED，不能据局部和非网格帧缺标签宣称全片正确率或零误报。

替换片清楚区间[443,573)是130帧人工候选匹配区域，非130帧精确框。C该区域130匹配检测、130合格候选、130外观拒绝；检测缺失、质量暂缓、歧义、误接受各0，仅适用于此区域。B的130候选均未经身份核验，A没有恢复候选机制；两组不绑定不能算外观拒绝通过。

整次C候选133：131程序外观拒绝、2质量暂缓。f390/f391低检测分数暂缓；f442程序拒绝；这些手持/局部候选的完整几何匹配仍未评价，不混入130合格拒绝分母。f389—393/f442局部T2过程保留，一次替换事件不按候选帧数扩大成133个事件。旧开发148/149分母不用于新HOLDOUT。

## 失败与限制

两个正例返回瓶子的原生ID均为3，初始化ID1不再报告。A按冻结约定不接续新ID，B已确认丢失后仅报告候选，因此两组未返回。第一片实际无瓶子检测[172,203)连续31帧（另f170单帧缺失），超过冻结缓冲30；第二片[178,278)连续100帧。不能以第一片约1秒纸板遮挡宣称小于缓冲的原生恢复能力，本轮也没有原生重新关联成功样本。

C第一片f203—206/f208质量暂缓、f207/f209外观门槛未通过；f210—214连续合格计数1—5，f214才报告位置。人工整瓶清楚f210后，f210—213仍UNKNOWN，其中固定样本f210计入误报分子。第二片f279—283连续合格1—5，f280—282整瓶可见仍UNKNOWN，固定样本f280计入。阈值保持，空窗如实作为剩余失败；不把恢复PASS写成全程无误报。

清楚负例的瓶盖/形状门槛通过，标签颜色、纹理和排序分数门槛失败。例如f443瓶盖距离0.493、标签距离0.978、对齐NCC0.094、排序分数0.378；均与冻结阈值核对，原像素重算一致。多个门槛同时拒绝，不能单独证明纹理或对齐的贡献。相同包装实体、真实双瓶、困难例和泛化性能未验证。

第一片原粗检约1秒遮挡/4.4秒后段、第三片约8秒遮挡/4.3秒后段的拍摄偏差保留。宽口径部分遮挡至整瓶清楚分别41/112/248帧，后段131/196/130帧；不能称严格满足原拍摄时长。三片没有按算法结果补拍、筛片或改初始化。

## 接受帧补标与版本绑定

初轮v1已有已核对返回f220/f286，但更早C输出f214/f283没有独立完整框；初轮精确延迟与接受身份因此UNEVALUATED，旧结果保留。实际查看这两帧无算法框原PNG后，依物理操作确认及红盖/红白绿标签/完整瓶身补T1框，另存 `outputs/m3_holdout_annotations_v2/`。仅状态输出用于选择要核对的帧，不用于定义身份或框；追加2帧为EVENT_KEYFRAME，不进入固定分母。

v2保存179原标签完全不变、两个附加标签及SHA/来源，协议SHA为 `9dbebca61b8b3d5f42fff09425828d5fd243409dcbaaec67c126fd7a4bae308c`。冻结清单SHA仍 `0562cedc68e79fcd4a8e2e5dca02c3c3d79917a294154845590bab131a8505ce`；全部shared_policy逐项不变。按任务授权，以v2协议复跑一次九组离线入口以绑定新标签，仍复用既有缓存。4,170条记录/事件与4,170个视频解码帧像素逐项和v1相同；补标改善评价覆盖，没有改变算法行为。

初轮运行HEAD `3bc338b`，v2运行HEAD `e7b028c`；12个执行文件仍匹配冻结Git版本 `572de8f`，不改旧SHA绕过历史版本检查。冻结模板NOT_STARTED和部分原辅助报告“开发scope”文字保留为历史模板；实际HOLDOUT完成状态以本轮run_manifest、评价与验收为准。B辅助报告 `disabled_matches_step1=false` 表示未提供旧step1目录，单独Git历史TargetState全帧回放均通过。

## 实际运行与核查

项目根目录实际命令；现有目录均非空，复跑需新的空目录。速度仍UNVERIFIED，未实施计时，不以整轮墙钟或历史推理FPS代替公平开销。

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_comparison.py --protocol configs/m3_holdout_v1.json --output outputs/m3_holdout_comparison_v1 > /tmp/m3_holdout_comparison_v1.log 2>&1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v > /tmp/m3_holdout_comparison_tests.log 2>&1
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python /tmp/m3_add_return_labels.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_comparison.py --protocol configs/m3_holdout_v2.json --output outputs/m3_holdout_comparison_v2 > /tmp/m3_holdout_comparison_v2.log 2>&1
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python outputs/m3_holdout_comparison_v2/verify_run_v2.py --protocol configs/m3_holdout_v2.json --runs outputs/m3_holdout_comparison_v2 --previous outputs/m3_holdout_comparison_v1 > /tmp/m3_holdout_comparison_acceptance_v2.log 2>&1
```

补标脚本留档 `outputs/m3_holdout_annotations_v2/prepare_supplement.py`，已登记目录不能直接重跑覆盖。附加核查脚本/日志保留本地。首次附加核查误要求B框等于检测框而退出1；原脚本 `verify_run.py`、`acceptance_initial.log` 保留，更正为按冻结组别核对后 `verify_run_v2.py` 全部通过，没有修改被冻结的实现。

两轮共同入口均退出0，内部从记录Git版本完整回放九组、重新解码九段状态视频，负例130帧外观证据原像素重算。110项全套测试实际通过（含28项三组、20项离线评价、12项标注边界），沿用环境。附加核查检查4170行缓存/时间轴/当前位置依据、共同条件/分母、所有旧标签不变、视频逐像素一致、12个冻结文件及共享规则。初轮1,386个受保护旧文件SHA保持；v2保护1,529个文件（含完整v1结果、补标输入），均保持。验收PASS表示实验交付完整性，表中FAIL仍是算法失败。

结果入口：`per_event_table.md`（九组逐事件表）、`group_totals.json`（每组两机会汇总）、`acceptance_checks.json`（实际验收）、`failure_analysis.json`（失败/未评价/偏差）、`raw_failure_review.png`（本轮实际查看原图裁剪）。`evaluation/`含summary、per_event_results、共同人工事件、181标签PNG原像素校验及九组历史来源核查。各片A/B/C目录含frames.jsonl、events.jsonl、status.mp4、run_info.json；C另含冻结参考和配置。视频/缓存/标签PNG/报告均保留本地，Git只提交协议与说明。

下一项给用户：把本说明、逐事件表和验收/失败报告交00，要求重新读取并核对实际成败、来源、补标与覆盖边界，再决定M4整理或后续处理。本轮没有调参、开困难例、补拍或推送。
