# M3 HOLDOUT 输入与独立标注

本文件保留输入准备阶段记录。随后已完成的三片冻结A/B/C实测、两个接受帧补标与失败结果见 `docs/m3_holdout_comparison.md`；原v1标注与报告不变。

2026-10-03，本轮仅完成三片输入准备。来源为已确认登记 `outputs/m3_holdout_input_confirmed_20261003/input_registry.json`，用户在本聊天再次确认三项物理操作。正式冻结仍为 `configs/m3_freeze_v1.json`，SHA `0562cedc68e79fcd4a8e2e5dca02c3c3d79917a294154845590bab131a8505ce`；12个冻结执行文件、算法、阈值和全部 shared_policy 不变。没有运行 A/B/C 对照、恢复效果评价或速度测量。

## 独立依据与输入

身份依据来自用户的物理操作确认，并绑定三片原文件/项目副本/SHA。T1只在每片内表示最初指定瓶子；蓝标替代瓶子为T2，在冻结评价字段中编码为 OTHER_BOTTLE。检测类别、置信度、原生ID和外观分数不定义物理身份。

框、可见性和时刻由Codex直接查看原像素标注，尚非用户逐帧标注，也没有第二位人工复核者。先只看前段f0/30/60，锁定f0人工初始化；再查看全部固定抽样与转折原图，保存标注清单，之后才运行公共缓存。标签不传给算法。公共缓存之后的区域适配只从已经固定的原图标签取值，没有查看恢复输出或据算法成败改标注。

| 输入 | 原帧数 | f0人工初始化框 xyxy | 唯一初始化IoU | 人工机会 |
| --- | --- | --- | --- | --- |
| holdout_return_01 | 341 | [148,474,252,824] | 0.948285 | 原瓶原位返回1次 |
| holdout_return_02 | 476 | [148,474,245,826] | 0.899844 | 仅移位原瓶返回1次 |
| holdout_replacement_01 | 573 | [235,492,327,792] | 0.921554 | 原瓶已取走不再出现，0次 |

初始化匹配固定0.5，框没有在看到后段或缓存之后重选。匹配到的native ID只是初始化映射证据，不是物理身份证明。处理区间分别[0,341)、[0,476)、[0,573)，保留原视频帧索引；没有剪辑、补帧或省略困难区间。三片原文件/副本逐字节SHA一致，彼此互异，排除冻结清单全部三份开发来源。

## 帧标注与时长偏差

以下边界是保守的原图目视判断，不是检测/状态边界。区间一律左闭右开，nominal 时间为原帧号/各片名义FPS，源时间另外保存在 timeline 和标签中。局部身份可辨认不意味着完整框已可评价；完整几何不足时框为空，不能强行计正确返回或零延迟。

| 输入 | 开始部分遮挡 | 保守可辨认原目标返回 | 后段整瓶清楚 | 其他物体局部过程 |
| --- | --- | --- | --- | --- |
| return_01 | f169 | f204，红白主标签部分与瓶身下部可辨认 | f210 | f175、f201—203为不确定边界 |
| return_02 | f168 | f279，红盖、红白标签和瓶身可辨认 | f280 | f182、f275—278为不确定边界 |
| replacement_01 | f195 | 无原目标返回，延迟不适用 | T2 f443 | f388先见边缘模糊蓝瓶，f389—393手持T2可辨认但完整框不确定，f394再次隐藏；f442再局部可辨认 |

替换片不能用f443最后完整露出代替首次T2可辨认f389。原瓶在幕后的精确取走时刻无法从画面得知，保持未评价；零返回机会由用户确认。T1从f198起无可报告的当前观察（先被遮挡，后已移除），不能猜幕后位置。

拍摄偏差原样保留：第一片00粗检约1秒遮挡、后段约4.4秒，超过0.3—0.5秒目标且不足5秒后段；第三片粗检约8秒遮挡、后段约4.3秒，超过3—4秒目标且不足5秒后段。新标注使用更宽的“开始部分遮挡到整瓶清楚”口径，分别41/112/248原帧，约1.366/3.733/8.265秒；完全清楚后段分别131/196/130原帧，约4.366/6.532/4.333秒。粗检值与新口径均保存，不改写为严格符合原拍摄计划。第一片不能证明小于ByteTrack缓冲时限的能力；视觉遮挡时长不等同连续无检测时长。

## 覆盖与评价边界

固定抽样从每片初始化f0起每10原帧：35+48+58=141，全部已目视核对并保存原PNG/标签。另有38个不在固定网格的事件关键帧，总计179张有标签原图；追加帧不扩大固定分母。全部转折连续原图/拼图也保留，未添加精确框的原帧仍不能当作框真值。

固定样本中88帧清楚T1、13帧清楚T2、36帧完全不可见、4帧局部（T1 f170；第二片f170/f180；T2 f390）。局部和11个附加不确定边界帧均不猜完整框。静止段各固定样本逐个核对后可采用同一目视近似框；没有用检测框、自动插值或隐藏轮廓补框。区间身份/可见标签与逐帧精确框分开保存。

负例的冻结评价器原本接受一个连续人工匹配区域，因此另存 `physical_identity_for_evaluator.json`，引用推理前身份/标签SHA。完整静止T2覆盖为[443,573)，130原帧，区域取f443原图人工框；它是候选匹配区域，不是130个逐帧精确框。手持/局部几何未知区间另列，不能称已经拒绝或没有候选。未来该区间内的实际合格候选分母、检测缺失、质量暂缓和外观拒绝只能由三组运行后评价；当前没有任何相关成败计数。

后续各组首个待评价返回/接受帧可能不在网格内，届时仍须追加原图身份/框核对，以报告精确延迟；不能把缺标签当作成功或零误报。完整固定样本覆盖也不等于全片每帧精确标注，当前全片误报率及算法效果均未评价。

## 公共缓存与核查

沿用原环境。每片仅实际运行一次固定YOLO11n+原始ByteTrack：imgsz640、conf0.1、NMS IoU0.7、bottle、GPU0、包内默认YAML/缓冲30；依赖/模型/YAML与冻结来源核对。原始缓存推理1390帧，不是A/B/C恢复对照；没有据检测结果筛片/调参或观看带框片用于标注。

项目根目录实际缓存命令（输出目录需为空，本轮已存在；复跑须另存并按任务授权决定，不能覆盖或反复推理）：

```bash
.venv/bin/python scripts/run_baseline.py --source data/m3_holdout_return_01.mp4 --output outputs/m3_holdout_cache_v1/holdout_return_01 --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/run_baseline.py --source data/m3_holdout_return_02.mp4 --output outputs/m3_holdout_cache_v1/holdout_return_02 --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/run_baseline.py --source data/m3_holdout_replacement_01.mp4 --output outputs/m3_holdout_cache_v1/holdout_replacement_01 --model weights/yolo11n.pt --device 0 --imgsz 640 --conf 0.1 --iou 0.7
```

核查入口只检查正式清单、三份原件/副本/开发排除、初始化、缓存、标注原PNG逐像素、时间轴/框/覆盖/事件与旧文件保全；不调用任何组的step或恢复运行。原始缓存核查器在临时只读链接上检查所有记录和重解码视频，不改已登记缓存，也不把其轨迹统计作身份真值。

```bash
.venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
.venv/bin/python scripts/validate_holdout_annotations.py --protocol configs/m3_holdout_v1.json --output outputs/m3_holdout_annotations_v1/validation
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts/validate_holdout_annotations.py tests/test_holdout_annotations.py
```

复核需另一个空输出目录；拒绝覆盖已有核查报告。正式HOLDOUT协议为 `configs/m3_holdout_v1.json`：stage=HOLDOUT、freeze_status=FROZEN，全部shared_policy逐项与正式清单一致。冻结的independent_test_design未开始字段保留为当时计划快照，本轮实际准备进度写在额外字段和STATUS中，不改冻结内容。

本地包 `outputs/m3_holdout_annotations_v1/` 包含：推理前标注清单、最新输入登记、初始化/身份/固定与关键帧标签/可见区间/人工事件/覆盖、原图与拼图、时间轴、旧文件保全及核查报告。旧pending/confirmed登记、正式冻结、开发输出均保留；视频、权重、缓存、PNG与报告仍被Git忽略。

实际核查版本 `c0c7503b7076c723c93ce3d0f93f890c4d0ff9f4`：输入准备PASS。三片原视频/缓存完整解码与1,390帧时间轴对应，179张标签PNG逐像素一致；141/141固定样本、三个人工事件/两个期待返回机会核查通过。正式FROZEN、全部shared_policy与12个冻结执行文件不变，1,040个既有文件SHA一致。110项全套测试（既有98+新增12）及编译通过；重复核查到已存在目录按预期退出1，旧报告不覆盖。算法对照/效果NOT_STARTED，速度UNVERIFIED。

详细证据在 `validation/annotation_checks.json`、`acceptance_checks.json`、`freeze_check.json`、测试/运行日志；根目录另存 `event_time_table.json`（名义/源时间并列）、`manual_box_QA.png` 与 `preparation_tools/`（本轮实际准备脚本留档）。准备脚本写入的本轮目录已存在，不可直接重跑覆盖；复核使用上述核查入口并指定新的空目录。

下一项只交00核对标注覆盖、来源/协议和不确定项；本轮不将输入就绪写成M3算法验收，不启动三组效果或速度测试。
