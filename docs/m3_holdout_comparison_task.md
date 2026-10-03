# 03 当前任务：三片 HOLDOUT 冻结对照

00已复核通过输入准备。唯一任务：实际运行三片A/B/C、核对共同事件评价、保留失败与未评价项。目的为检查现有恢复与拒绝在新输入上的成败，不要求C必须优于A/B。速度、困难例和新方法不在本轮开发范围。

## 接手必读

项目根目录 `/home/qiyue/文档/ChatGPT/AI个人项目`。重新读取：

- AGENTS.md、SPEC.md、STATUS.md。
- docs/m3_protocol.md、docs/m3_holdout_annotations.md、docs/m3_holdout_annotations_00_review.md。
- configs/m3_freeze_v1.json、configs/m3_holdout_v1.json、configs/recovery_m3_v1.json。
- outputs/m3_holdout_annotations_v1/validation/acceptance_checks.json。
- outputs/m3_holdout_annotations_00_review/validation/annotation_checks.json、independent_check.json及当前源文件/标注/缓存。

以SPEC最新决策为准。正式冻结m3_v1/12个执行文件与共同规则保持。三个缓存已经各推理一次，总1,390帧；直接复用，不重跑YOLO/ByteTrack，不重建环境。

## 执行与交付

1. 检查当前Git与来源，保留其他聊天未提交记录。先核对正式冻结和三份开发来源排除；锁定的前段f0框、处理区间、真值/缓存不按后段效果重选。
2. 用现有共同入口逐片运行A/B/C。A选择初始原生ID；B关闭身份恢复；C用已冻结的有界对齐配置。相同341/476/573帧、原像素、缓存、初始化和人工事件；三组共4,170条状态记录/视频帧，不是九个独立视频样本。
3. 入口自动生成初轮评价；随后核对三组共同输入、来源/代码、逐帧/事件、九段状态视频重解码及关键失败原图。保存适用的既有评价/三组边界测试结果，旧文件运行前后校验保持。不得只凭退出0或测试数量宣称方法有效。
4. 保存运行命令/日志/来源、九组状态视频/逐帧/事件、评价summary、验收核查JSON、逐片逐事件表与失败/限制说明。推荐新目录 `outputs/m3_holdout_comparison_v1/`，说明 `docs/m3_holdout_comparison.md`。目录非空则换新后缀，保留部分失败输出。

根目录建议命令（本任务尚未执行）：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_comparison.py --protocol configs/m3_holdout_v1.json --output outputs/m3_holdout_comparison_v1 > /tmp/m3_holdout_comparison_v1.log 2>&1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p test_m3_comparison.py -v
```

运行期间日志放 `/tmp/`，不要持续写入已被保全快照保护的outputs旧文件；命令结束后可复制日志到本轮新输出。入口不会重新检测，但会顺序读取原像素、运行冻结状态和评价。

## 评价与验收

- 每组共同分母为两个T1期待返回事件（原位/移位各一次），以及一次T1不返回的替换事件。分母来自人工事件，不能改为算法丢失次数、候选帧数或成功片段数。
- 按人工物理身份与本帧当前位置框IoU>=0.5核对；A/B原生连续/重新关联也可正确返回，不要求有自定义接受事件。C程序接受须另核对物理身份，不能把新ID或接受日志直接计成功。逐片列正确/未返回/未评价、错误绑定/错误当前位置、返回机制和延迟状态。
- 返回锚点为保守f204/f279，邻近UNCERTAIN保留。恢复延迟主报原帧差/名义FPS并列源时间；缺首个观察框则精确延迟UNEVALUATED，不给零。替换事件返回率/延迟NOT_APPLICABLE，不能记恢复失败。
- 清楚T1固定样本分母31/37/20，共88；报告各组UNKNOWN误报数/已评价分母及B/C错误LOST事件。141是全部固定样本，179含关键帧，均不能替代88。追加评价关键帧不扩大固定分母，全片精确误报率仍未评价。
- 替换片T2在f389—393/f442局部出现，f443起清楚。[443,573)匹配区域非130帧精确框；按实际检测、质量合格与人工区域匹配报告检测不足/低质暂缓/外观拒绝/歧义暂缓/误接受。合格候选分母以实际结果为准，手持/局部覆盖另列未评价；一次替换事件与候选帧计数分开。A/B无外观核验，不把永不绑定计为身份拒绝通过。
- 记录实际连续无检测长度与原生行为，不能用第一片约1秒视觉遮挡证明小于ByteTrack缓冲的能力。报告第一/第三片拍摄偏差、标注者Codex和无第二人类逐帧复核；三片仅为有偏差的小规模保留测试。
- 不开发增量计时，本轮速度UNVERIFIED；不能用历史缓存推理FPS或整轮墙钟时间代替冻结的公平计算开销。困难例、纹理独立贡献和泛化性能均未验证。
- 正式冻结、共享条件、来源、帧/事件/视频及旧文件保全核查通过，即使算法失败也可满足实验交付。冻结模板内NOT_STARTED仍是计划快照；实际是否完成写入新运行和STATUS，不能为了进度改锁定模板。

## 缺标注时如何处理

对各组首个待评价返回/接受帧，仅用原像素与既有物理操作确认补独立身份/完整框，另存原PNG/SHA、标注v2；标为追加关键帧，不混入固定抽样。状态输出只决定需要核对哪一帧，不决定真值。部分/不确定几何不能猜完整框；若仍不足，保留UNEVALUATED，可说明已核对的返回帧，不冒充精确首次恢复。

保持v1标签/协议/运行。只补标签也会改变协议SHA，而现评价入口要求运行绑定同一协议；此时另存HOLDOUT v2协议及新的空结果目录，复跑冻结离线三组以绑定新标签，仍不重新检测、不改初始化/参考/配置/事件。核对v1/v2逐帧状态、事件一致，状态视频像素一致；run_info的新协议SHA/时间可不同，不能改写旧run_info或冒称原运行用过新标签。若不需要补标签，不增加复跑。

如执行/评价入口出现真实阻塞，保留部分输出与可复现错误，报告00；不得修改冻结代码/口径绕过后再将结果写为原冻结测试。

完成后更新STATUS、检查变更并做本地Git提交，不推送；不纳入其他聊天未提交记录。把实际表/验收/失败说明交00核对，再决定M4整理或后续处理。边做边解释一次状态接受与物理恢复判定的区别，不额外要求用户重新拍片或重复已完成的输入确认。
