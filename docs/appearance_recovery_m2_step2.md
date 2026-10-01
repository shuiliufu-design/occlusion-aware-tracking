# M2 第二步：冻结外观参考与恢复关联

2026-10-01，03 按 SPEC.md 实现第二步。现有开发正例与挂包模块负例已实际验证，真实错误瓶子视频缺失，第二步仍为部分完成。
有效输出为 `outputs/tabletop_02_m2_step2_v3/`。早期运行 `tabletop_02_m2_step2/` 和 `tabletop_02_m2_step2_v2/` 保留为开发记录；修正建库对低质量观察的跳过规则及差值边界后使用新目录运行，最终核查以 v3 为准。

## 数据流与身份含义

`原视频像素 + v2 原检测/轨迹 → 因果参考库 → 外观/质量证据 → 竞争比较 → 连续确认 → T1 与活动原生 ID 的关联`。
YOLO11n、ByteTrack、原生 ID 与原检测结果均未修改，也没有新增依赖或重跑推理。

初始化仍由原帧号、人工瓶子框、唯一 IoU 匹配确定。项目标识 `target_uid` 默认 T1，与初始/活动原生 ID 分开；原生 ID 用于串联候选，不能单独决定身份。
`recovery_confirmed=true` 只在程序接受的当前帧出现，含义为按外观规则接受；`verification_basis=appearance_heuristic`。物理身份判断另存于 `evaluation.json`，不将外观分数当作身份概率。

## 参考与候选规则

所有起始参数保存在 `configs/recovery.json`，本轮未调整 SPEC.md 的颜色、纹理、分数与确认阈值。
使用原始检测框裁剪，左/上 floor、右/下 ceil；相对瓶盖和标签区域同样 floor/ceil。标签灰度缩放采用 INTER_AREA，统一 64×96。
H-S 为 16×16、H 范围 [0,180)、S 范围 [0,256)，颜色掩码 S/V 均至少 40；有效颜色不足或灰度标准差不足时暂缓。

从初始化后的最早合格观察采样，目标 10、最少 5、等待至多 30 帧。轨迹仍在但质量不合格的帧只记录原因并跳过；首次选定轨迹缺失即停止，确认丢失时也冻结。达到最少数量后，新增参考还需与已有参考一致；不一致时冻结现有库。
不足最少样本报告 INSUFFICIENT_REFERENCE，不使用重现画面补齐。建库初期由人工初始化和原生连续性支撑，随后冻结，自动恢复的画面也不更新。
本次参考为 f600—609 的 10 个原始裁剪，全部合格，f609 冻结；记录与裁剪校验一致。参考 SHA-256 为 `d12ca74ec566f48bddd62c37e0b2ae6886e8103bb16dd0c52a88ca1a98bdd876`。

每个候选先与全部参考计算 S，选最高 S，再对这一份参考检查全部颜色、纹理、形状与分数条件；不拼接不同参考的有利分量，也不退而挑选低分但过门槛的参考。
所有质量合格、分数可计算的同类候选参与竞争，含某项门槛失败的候选。最高分未过门槛则不改选其他候选；与次佳差值不足 0.10 时暂缓。差值比较只容忍 1e-12 的浮点舍入误差，未放宽业务阈值。
候选身份判定保存 ACCEPTABLE / REJECTED_APPEARANCE / DEFERRED_QUALITY / AMBIGUOUS、原因、全部参考比较、最高分参考、质量、差值及连续计数。

只有已关联且 ID 唯一的最高分候选，连续 5 帧通过全部条件、相邻框 IoU 至少 0.3，才接受。无 ID、消失、ID 改变、空间跳变、门槛失败或竞争歧义都会阻断/重置确认。
接受后继续对活动检测做同样外观与质量检查；不可靠时立即清空当前位置，再按连续缺失规则丢失。候选区域和历史框都不作为原目标的已确认当前位置。

## 准确运行命令

项目根目录执行，复跑必须换新输出目录：

```bash
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/tabletop_02_m2_step2_v3 --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery.json
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_02_m2_step2_v3 --annotations outputs/m2_step2_identity_review/identity_annotations.json --frames 600 609 691 692 701 845 847 848 851 852 900 983
.venv/bin/python scripts/validate_recovery_fixture.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --recovery-output outputs/tabletop_02_m2_step2_v3 --output outputs/m2_step2_module_validation_v2 --negative-start 223 --negative-end 230 --negative-box 200 120 455 750
.venv/bin/python scripts/run_recovery.py --source data/tabletop_02.mp4 --baseline outputs/tabletop_02_baseline_v2 --step1-output outputs/tabletop_02_m2_step1 --output outputs/tabletop_02_m2_step2_disabled --init-frame 600 --init-box 180 450 305 870 --missing-frames 10 --config configs/recovery.json --disable-recovery
.venv/bin/python scripts/review_recovery.py --output outputs/tabletop_02_m2_step2_disabled --frames 600 694 703 845 848
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts tests
```

`identity_annotations.json` 为本次本地身份记录，不在 Git 中。新的输入需另建含视频校验、目标身份、关键帧人工框、可辨认重现帧、标注者和确认依据的记录，不能复用本视频标注或以算法门槛生成真值。缺少标注时可省略 `--annotations`，接受只计为 UNEVALUATED。

## 本次正例结果

984 帧原视频顺序解码，保存原 f600—983 的 384 帧；输出视频重解码为同样 384 帧、720×1280。

| 原帧 | 实际行为 | 状态视频播放器估算时间 |
| --- | --- | --- |
| f600—609 | 收集并冻结 10 个参考 | 从 0 秒开始 |
| f692 | 原生 ID 仍输出，但检测分数低于 0.5；当前目标框清空，位置 UNKNOWN | 约 3.17 秒 |
| f701 | 第 10 个不可靠/缺失观察，进入 LOST | 约 3.48 秒 |
| f845—846 | 局部/低分候选质量暂缓 | 从约 8.44 秒起 |
| f847 | 外观通过，但没有已关联原生 ID，确认计数 0 | 约 8.51 秒 |
| f848—851 | 同一候选连续合格，计数 1—4，原目标位置仍未知 | 从约 8.54 秒起 |
| f852 | 第 5 帧合格，RECOVERY_ACCEPTED；T1 关联到新原生 ID，并从本帧给出位置 | 约 8.68 秒 |

TRACKING=233 帧（包括 f692—700 的 9 帧宽限期），LOST=144，RECOVERY_CANDIDATE=7。1 次丢失事件、1 次连续确认尝试、1 次程序接受。
接受帧最佳参考 f602；瓶盖距离约 0.4795、标签距离约 0.1565、纹理 NCC 约 0.7254、高宽比相对值约 0.9888、S 约 0.7543；全部门槛通过。当前仅一个候选，免除差值要求，绝对门槛仍执行。

物理身份依据：用户（拍摄者）明确确认“是，遮挡期间只移动了原瓶子，没有替换”；Codex 查看原始 f600/f845/f846/f847 与接受帧画面，另写关键帧框/身份记录。接受结果计为该开发片段正确接受 1、错误接受 0、未评价接受 0、未恢复事件 0。
可辨认重现帧保守选为 f847（红盖和完整标签清楚显露），由 Codex 画面核对，尚非用户逐帧时间标注。f852 的恢复延迟为 5 帧，按帧号/名义 FPS 约 0.172 秒，按记录源时间约 0.190 秒。注明该时间口径，不以首个检测或新 ID 帧代替可辨认重现依据。
这是一段已查看开发正例，不是准确率或泛化性能结论。

## 模块负例、关闭对照与状态检查

挂包负例使用 v2 f223—229 的真实检测框、像素、分数；人工框区域 `[200,120,455,750]` 用于唯一选择挂包误检，不按 ID 写死。
该段早于初始化，明确构造 LOST 模块上下文，并记录真实原帧号到夹具逻辑帧号的映射。没有改分数，也不冒充本纸板段端到端负例。

- f224/f225 原检测分数约 0.509/0.518，特征可计算，均为 REJECTED_APPEARANCE。瓶盖距离均 1.0、标签距离约 0.805/0.811、纹理 NCC 约 -0.004/-0.035；形状通过而外观不通过，未绑定。
- 其余 5 帧原检测分数不足，均为 DEFERRED_QUALITY；不将这些帧计为外观拒绝。
- 同一真实参考裁剪构造两个等分、已关联候选，连续 6 帧都因竞争差值不足暂缓，0 接受。该构造例不能算真实双瓶歧义验证。
- 参考在上述候选中保持不变，报告为 `outputs/m2_step2_module_validation_v2/module_validation.json`、`ambiguity_fixture.json` 及挂包裁剪 PNG。

关闭恢复另跑 384 帧，通过与第一步所有原有字段逐项比较：TRACKING=103、LOST=142、RECOVERY_CANDIDATE=139，0 接受，回到仅候选行为。
v2 与第一步共 29 个文件在运行前后及核查时校验一致，`preservation.json` 保留全部 SHA-256；原 M1/第一步脚本未修改。
最终 23 项 unittest（原第一步 8 项 + 新 15 项）通过，涵盖因果采样/低质跳过/窗口截止、不足参考、最佳参考统一门控、失败竞争候选不剔除、差值/颜色/纹理/形状边界、同 ID 高分错误外观、无 ID、候选切换/消失/空间跳变、短确认、歧义/重复 ID、退化图像、恢复后再次丢失与冻结参考。
相同图像代表另一实体的构造测试也会接受，用来明确这些特征无法区分相同外观实体的边界，不能将该测试写成真实困难例结果。

输出主目录另含 `status.mp4`、`frames.jsonl`、`events.jsonl`、`run_info.json`、`references.json`、参考 PNG/特征 NPZ、`review.json`、`evaluation.json` 与关键帧预览。每个候选的全部分量、质量、差值、确认计数与理由可检查，参考和配置有校验。

## 待验证与下一项拍摄任务

真实错误瓶子、真实双瓶歧义、相同包装替换均未提供；独立保留测试及端到端速度对比也未运行。阈值未调整、未冻结为 M3 测试配置，不能声称通用 ReID 或普遍拒绝能力。
本步仍为部分完成：真实不同瓶子必须确实产生质量合格候选并被拒绝，才满足 SPEC.md 的“恢复与拒绝”验收。没有检测到假瓶子不能算外观拒绝通过。

用户现在只需拍一段实际不同瓶子的负例，保存为 `data/tabletop_wrong_bottle_01.mp4`：固定相机与光照，原红盖瓶子先清楚可见约 5 秒；纸板只遮住瓶子，背景保持可见；遮挡期间取走原瓶子，换成同样红盖但标签明显不同的瓶子；移开纸板，让替代瓶子清楚可见至少 5 秒，原瓶子不再入镜。总长约 15—20 秒，并简短说明替换操作。
目的：检查不只依赖红色瓶盖的身份拒绝。交付为视频与操作说明；拍摄验收为替代瓶子的瓶盖、标签清楚、镜头不被遮住。后续由 03 检查视频读取，复用固定检测条件运行，确认替代瓶子确实形成质量合格候选，再评价拒绝；不提前填写结果。
