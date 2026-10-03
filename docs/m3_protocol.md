# M3 三组共同入口与冻结准备

2026-10-03 更新：正式冻结 `configs/m3_freeze_v1.json`（m3_v1，核心版本572de8f）保持。00复核新输入准备后，03已实际完成三片HOLDOUT A/B/C；最终 `configs/m3_holdout_v2.json` / `outputs/m3_holdout_comparison_v2/`，初轮v1保留。C两个正确返回和一次130合格候选拒绝，A/B各两次未返回；固定UNKNOWN与拍摄偏差、未评价项如实保留，速度未验证。实测/失败与补标版本绑定见 `docs/m3_holdout_comparison.md`，原标注见 `docs/m3_holdout_annotations.md`。本文件下方保留开发记录，原 `configs/m3_protocol_v1.json` 与预演待冻结清单仍是历史状态；它们不是正式测试输出。

正式冻结核查：

```bash
.venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
```

独立测试使用另存的HOLDOUT协议，引用正式清单及SHA，保持全部 `shared_policy` 字段一致；新增每片来源、一次公共缓存、前段初始化与独立标注。接手03额外检查正式清单的全部三段 `excluded_development_sources`，初始化IoU固定0.5。计时规则已锁定但未实施，仍不报速度。开发f850等待、A/B f181缺框及覆盖缺口保留。00审查范围与证据见STATUS及 `outputs/m3_preflight_00_review/`。

## 03交付时的开发记录（历史）

依据 SPEC.md 2026-10-03 决策，目前只在已有两段开发视频预演。协议为 `configs/m3_protocol_v1.json`，状态 `PENDING_REVIEW_NOT_FROZEN`；不是独立测试或已冻结实验。C 配置 `configs/recovery_m3_v1.json` 与00采纳的 `recovery_f180_dev.json` 逐字节一致，原默认配置保留。

## 共同运行与复跑

在项目根目录，沿用 `.venv`，无需新依赖、GPU或重跑检测：

```bash
.venv/bin/python scripts/run_comparison.py --protocol configs/m3_protocol_v1.json --output outputs/m3_development_preflight_v4
.venv/bin/python scripts/m3_common.py --check-freeze outputs/m3_development_preflight_v4/freeze_checklist.json
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q scripts tests
```

复跑换新的空目录。运行先核对输入/配置SHA和实际执行代码的Git版本，再顺序运行每片A/B/C、评价、准备冻结清单。每组分别顺序解码同一原视频与复用同一公共缓存；没有推理或速度对照结论。代码须先本地提交再实际运行，不能以更新旧SHA跳过版本核查。

单独复跑评价（用新空目录）：

```bash
.venv/bin/python scripts/evaluate_comparison.py --protocol configs/m3_protocol_v1.json --runs outputs/m3_development_preflight_v4 --output outputs/m3_development_evaluation_recheck_v1
```

| 组别 | 运行机制 | 不适用项 |
| --- | --- | --- |
| A 原始 ByteTrack | 初始化框唯一匹配已关联检测，此后只选择该原生ID，输出本帧实际检测框；跟踪器与缓存不改 | M2状态、外观核验、自定义接受均为空/不适用；观察间断诊断不是LOST |
| B 状态与候选 | 原 `TargetState`；短时缺失后同ID可继续，连续10帧确认丢失后仅候选、不接续新ID | 外观质量/身份拒绝/自定义接受不适用 |
| C 身份恢复 | 已验证 `RecoveryState` 和选定对齐配置；冻结因果参考、外观/竞争/连续5帧确认 | 程序接受与人工正确物理身份仍分别评价 |

A当前框是原始检测框；B保留原生本帧滤波轨迹框与检测映射，C保留原检测框。B的表示是已验证行为，不在入口中替换；三组均不使用缺检测时的预测/历史框作当前位置。图像、帧号、源时间、初始选择、缺失阈值及处理区间共用。协议通过来源与逐字段回放核查这条约定。

## 共用人工事件与返回评价

开发正例共用旧纸板事件，拍摄者确认只移动原瓶子、未替换；可辨认重现仍为f847。负例共用一次替换事件，拍摄者确认取走原瓶子且未再入镜；原目标返回机会为0。每组分别评价相同事件，不把三组当成三倍独立样本。人工事件表另存 `evaluation/common_manual_events.json`。

三组主指标从人工可辨认时刻起检查**实际输出的当前框**：本帧人工身份为T1且框IoU>=0.5才是正确返回。A/B不必产生 `RECOVERY_ACCEPTED`；原生ID短时重关联可以计成功。A/B不能因新ID、瓶子类别或分数而自动接续。相同原生ID对应错误实体仍记错。C自定义接受、原生重关联和连续观察分别报告，不把原生能力记作新增恢复贡献。

无返回机会时成功率/延迟不适用；缺身份/框时未评价，不填0延迟。如果后来有独立正确框，可确认返回存在，但更早输出缺标注时精确首次返回延迟仍未评价。完全没有当前框且人工期待返回，才可明确计未返回。旧M2基于接受事件的历史指标保持原定义，新M3入口不重写旧报告。

## 标注覆盖与拒绝分母

新增原图核对保存于 `outputs/m3_development_annotations_v1/`；12帧PNG/校验与身份/框依据在标签文件中。正例补看f850，现有f847/f852重新看原画面；负例初始化/诊断/替代瓶子关键帧也查看。框为目视近似，尚非用户逐帧复核。

正式抽样计划从初始化起每10原帧固定抽样。此次预演只核对其中少量帧，其余列为未核对；追加返回/接受/拒绝关键帧不混入固定抽样分母。旧11帧可见诊断控制另列，旧8帧全遮挡与负例148帧原目标缺席也单列。全片误报率继续UNEVALUATED，不用少量样本假报全片零误报。

负例合格拒绝仍以人工 `[485,633)` 的148帧空间区域匹配为依据，属于一次替换事件；整次149个候选另列。检测缺失、检测但非恢复候选、质量暂缓、证据不足、合格外观拒绝/歧义分开；A没有M2候选机制，B有候选但未作外观核验，二者不获得外观拒绝PASS。

## 冻结清单与独立测试入口

`freeze_checklist.json` 保存实际代码Git提交与执行文件SHA、协议/恢复配置全部参数、原配置与采纳来源、requirements/实际安装依赖、Python/OpenCV/平台、权重SHA、YOLO参数、ByteTrack YAML/参数/版本、两片缓存/源校验、初始化、事件/标注及评价器。还记录参考因果冻结、抽样/指标与计时边界。核查命令只证明清单未变化，状态仍待00复核；当前不记已经冻结。

B/C新增处理计时计划包含参考建库，排除推理、解码、绘图/编码及评价；每片独立状态预热一次再各测3次，报告逐次、中位数、硬件与起止。本轮未实施，ms/帧为null、速度UNVERIFIED，不与历史A推理FPS相比较。

00核对开发预演后再冻结最终执行版本，之后另拍3段独立片：两段原瓶子返回（改变遮挡长度/位移），一段不同标签替换且原瓶子不返回。固定相机、背景可见、纸板只挡瓶子，前段足够初始化；不按检测或恢复成功挑片。每片早期人工初始化框/帧是输入，不依据后段结果重选。身份/可见/遮挡/可辨认返回及固定抽样框独立于算法，uncertain与覆盖缺口保留；每片只产生一次公共缓存，三组复用。测试后不调参；需修正则保留失败，将该片转开发并另拍保留片。

同一入口已经支持后续 `HOLDOUT` 输入：须引用经00复核记录为 `FROZEN` 的清单及SHA，代码/实际安装依赖/共同规则必须匹配，检测缓存的参数、模型、YAML与版本须匹配冻结条件。只允许另填每片来源、早期初始化和独立人工标注；旧开发视频不能换名当保留测试。这些保护有构造边界测试，本轮没有创建真实FROZEN清单或运行HOLDOUT输入。当前协议仍为开发预演。

真实双瓶/同包装、背景持续可见新负例、纹理独立贡献、全片误报率与严格速度仍未验证/未评价。

## 实际开发预演（2026-10-03）

首次提交 `a2e1d59` 保存共同入口/配置/协议。首轮 `outputs/m3_development_preflight_v1/` 已生成六组和评价，但调用者把正在写的日志放入被保全的输出树；pip诊断写日志后保全检查正确拒绝（退出1）。保留失败目录、日志及原SHA，没有把该次主运行记为成功。随后日志改先写 `/tmp`，`v2/` 完整成功；再补齐正式冻结输入保护，提交 `e614d61` 并另存 `v3/` 完整成功。收尾发现负例A/B f181有当前框却缺人工完整框，汇总应记未评价；提交评价统计修正 `572de8f` 后在最终 `v4/` 完整成功。各版算法/阈值均未修改，v2/v3/v4六组全部记录/事件/视频SHA一致。

最终实际运行命令（日志先写临时路径，完成后复制到新结果目录；不要预先向被保全输入树中的文件重定向）：

```bash
.venv/bin/python scripts/run_comparison.py --protocol configs/m3_protocol_v1.json --output outputs/m3_development_preflight_v4 > /tmp/m3_preflight_execution_v4.log 2>&1
.venv/bin/python scripts/m3_common.py --check-freeze outputs/m3_development_preflight_v4/freeze_checklist.json
.venv/bin/python -m unittest discover -s tests -v > /tmp/m3_tests_98.log 2>&1
.venv/bin/python -m compileall -q scripts tests
git diff --check
```

| 开发事件 | A 原始原生ID | B 状态与候选 | C 身份恢复 |
| --- | --- | --- | --- |
| 原瓶子返回，人工机会1 | 未返回1；无延迟 | 未返回1；无延迟 | 正确返回1，f852；5帧延迟 |
| 不同瓶子替换，人工机会0 | 返回/延迟不适用 | 返回/延迟不适用 | 返回/延迟不适用 |
| 替代瓶子人工148帧 | 148帧有匹配检测；无M2候选/外观机制 | 148帧候选；外观核验不适用 | 148帧合格候选均外观拒绝；一次替换事件 |
| 自定义接受 | 不适用，null | 不适用，null | 正例1次人工正确；负例0次，0错误/未评价接受 |

两片共2个人工事件，其中期待返回机会只有1，不能累加三组制造更多独立样本。正例5帧延迟仍从人工f847计算：名义FPS0.1721898148秒，源时间0.1899888889秒。A/B初始原生ID消失后没有接续新ID；当前长遮挡片中未成功返回。短时同ID、无接受事件仍能正确返回的口径，由小规模构造记录验证，未声称已有真实短遮挡效果结果。

固定抽样计划正例39帧/负例64帧，共103；本轮分别核对2/4帧，共6，未核对97帧。正例两帧清楚T1样本为600/850，三组均在850 UNKNOWN；C的连续确认等待成本保留，不假报零误报。负例清楚T1固定样本0/170/180均有位置；500为T2，不充当可见T1分母。后补847/852等关键帧不扩大固定抽样。旧11帧诊断控制三组均0 UNKNOWN，但只能说明该诊断范围；原目标缺席的148替换帧与8全遮挡帧均0错误当前位置，全片仍未评价。负例A/B在f181有当前框，但原图诊断只有部分可见且没有可核对完整人工框，因此位置审查列UNEVALUATED/[181]；不能借缺席范围156帧通过掩盖该项缺口。C该帧没有当前位置，仍保持UNKNOWN。

最终来源核查使用 `572de8f` 对应Git快照：A只读选择逐字段回放384/633帧，B原TargetState逐字段回放384/633帧，C记录/参考/分量/事件核查；六个视频各重解码384/384/384/633/633/633帧。C负例重新解码原视频633帧并从原像素重算148帧；B/C四组记录、事件与视频SHA全部匹配先前采纳的开发结果。旧核查器的 `disabled_matches_step1=False` 因本入口没有传入第一步目录，不表示回放失败；新来源证据中的 `historical_target_state_replayed_frames` 与逐字段/事件对照才是B等价依据。12张补充标注原图逐像素匹配源视频，原身份确认与旧事件/诊断SHA未改。

98项测试通过（原70+三组评价/冻结保护28）；compileall、共同输入/代码/配置核查与非空运行/评价保护均通过。原366文件再次匹配，接手保全清单589文件未变，最终主入口保全881个既有文件；实际清单可检查，不改旧SHA。新配置与采纳配置逐字节相同，M2四个核心/旧评价文件SHA保留。

最终结果 `outputs/m3_development_preflight_v4/`：

- `positive/`、`negative/` 下各有 `A/ B/ C/`：视频、完整逐帧记录、机制事件、运行来源；B/C另含冻结参考/配置。
- `evaluation/common_manual_events.json`、`per_event_results.json`、`summary.json`：共同事件与六组评价；人工返回、候选/拒绝、固定抽样缺口和机制不适用分别报告。
- `evaluation/source_checks/`、`annotation_checks.json`：Git历史回放、负例像素重算与原图核查。
- `freeze_checklist.json`、`dependencies_snapshot.txt`：最终执行版本与待冻结清单，实际核查PASS，仍 `PENDING_REVIEW_NOT_FROZEN`。
- `acceptance_checks.json`、`run_manifest.json`、`tests_final.log`、`execution.log`、前后保全清单：本轮交付证据。

共同入口与开发预演验收通过；A/B在本长遮挡开发事件的未返回、C f850未知和覆盖缺口保留为结果，不将工具验收升级为全片算法通过。下一步仅交00只读核对三组口径/待冻结清单，核对通过后才正式冻结、另拍3段独立片。本轮未冻结、未拍片、未执行HOLDOUT、未推送。
