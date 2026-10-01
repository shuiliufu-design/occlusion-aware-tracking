# M2 第二步：真实不同瓶子的开发负例

2026-10-01，03 沿用冻结外观规则检查用户新视频。该片段的真实不同瓶子拒绝验证通过；连同已确认的开发正例与挂包模块负例，恢复/拒绝交付已有开发证据，待 00/04 复核验收。未修改 SPEC.md、检测/恢复核心、阈值、依赖或旧输出。

## 输入与独立身份依据

用户提供 `video_2026-10-01_22-41-54.mp4`，原件保留，复制为 `data/tabletop_wrong_bottle_01.mp4`。原件/副本 SHA-256 一致：`585f9ba9048b672fd39acabdaa8b5164e1a2d45be965d741081e9e8e2322b51f`。
既有读取入口与另一次顺序解码均读出 633 帧、720×1280、名义约 29.91038 FPS、估算 21.163 秒。读取停止不等于视频完整性保证。

用户明确确认：“是，换成了另一只瓶子，原瓶子未再入镜”。查看原始 f0、逐秒预览和 f480/485/490/495/500，原目标为红白标签瓶子，替代物为红盖蓝标签瓶子。身份依据不是检测 ID、外观分数或程序结果。
人工初始化为原 f0、框 `[290,280,510,1040]`；人工评价区间保守从原 f485 到 f632，替代瓶子完整且清楚可见。固定机位人工区域 `[180,325,415,1045]` 用 IoU>=0.5 匹配评价候选；此区域不传入恢复算法，不是逐帧精确标注，不以第一检测/ID时刻生成真值。
独立记录为 `outputs/tabletop_wrong_bottle_01_input/identity_annotations.json`，含校验、用户确认、标注者、关键帧框、区间、依据及限制。

## 固定条件与实际状态

新视频首次运行 YOLO11n + 原 ByteTrack，模型校验、包版本、bottle 类、imgsz=640、conf=0.1、NMS IoU=0.7、默认跟踪配置与原 v2 一致，现有 GPU 矩阵乘法和推理通过。新恢复输出直接复用这 633 条检测记录；`configs/recovery.json` 与上一正例完全一致，不调参。
仅用新视频 f0—9 的 10 个因果参考，f9 冻结；参考 digest 为 `cdccdc35bf74525eacf7781f1fdcf2ecd8e6d9a2a938c02be5c25a5effee337a`。没有使用旧视频参考或替代瓶子图像补库。

| 原帧/估算时间 | 实际行为 |
| --- | --- |
| f0—179 | 原瓶子可靠观察，原生 ID 1 |
| f180 / 6.02 秒 | 原瓶子仍可见，但检测框上界变化使最佳参考纹理 NCC 约 0.480 <0.55，位置清空为 UNKNOWN |
| f181 | 检测仅剩部分瓶身，瓶盖颜色特征无效；不能继续作为可靠观察 |
| f189 / 6.32 秒 | 连续 10 帧不可靠/缺失，进入 LOST |
| f484 / 16.18 秒 | 替代瓶子检测形成候选，尚无原生 ID；外观拒绝 |
| f485—632 / 16.22—21.13 秒 | 原 ByteTrack 给出新 ID 2，合格候选持续外观拒绝；T1 位置始终未知 |

633 条记录与状态视频重新解码一致。TRACKING=189（含9帧宽限）、LOST=295、RECOVERY_CANDIDATE=149。整次 149 个候选全部 REJECTED_APPEARANCE；人工清楚可见区间内为 148 个，不能混用两个分母。
丢失事件 1、连续确认尝试 0、程序接受 0、区间错误当前框 0；原目标被移除，预期不恢复。通用核查中的 `unrecovered_events=1` 不作为本负例的恢复失败；没有恢复延迟可计算。

## 真正拒绝，而非没有检测

人工区间 148 帧全有唯一匹配检测、有效质量和可计算外观证据，没有缺检测/质量暂缓。逐帧重新解码原视频，重建 lossless 冻结参考并重算质量、最佳同一参考和门控，与运行记录完全一致。
例如 f500：原检测分数约 0.9303，新原生 ID 已分配；瓶盖距离约 0.6414、标签距离约 0.8699、纹理 NCC 约 -0.2142、S 约 0.3038。形状通过，颜色/纹理/分数失败，连续确认始终 0，不绑定。

人工区间最佳参考证据范围：瓶盖距离 0.623—0.652、标签距离 0.868—0.896、纹理 NCC -0.245—-0.158、S 0.292—0.315。瓶盖门槛也在 148 帧失败，所以本片支持真实不同瓶子拒绝，不能单独证明标签模块的贡献或拒绝完全不依赖瓶盖。

新增 `scripts/validate_wrong_bottle.py` 补足通用接受评价的边界：每次重新核查当前记录/视频/校验，临时写核查结果以保留已有输出；只信实际质量和门槛证据，不信旧 review 布尔值或拒绝字符串。人工区间、候选证据、逐帧像素重算、绑定/错误位置检查写入 `wrong_bottle_validation_v2.json`。早期 `wrong_bottle_validation.json` 保留，最终使用 v2；核心运行无需重跑。
原 `evaluation.json` 的真实负例字段为固定 PENDING_INPUT，且不支持拒绝区间评价，作为通用接受评价保留；本片结论以专项报告为准，不将旧通用字段改写为完整验收。

## 准确命令与输出

在项目根目录运行；全部实际命令成功，复跑输出/报告均须换新路径：

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

基线 GPU 命令沙箱外运行；读取、恢复后处理、核查与测试在沙箱内成功。全部沿用原环境。
新状态输出含 `status.mp4`、`frames.jsonl`、`events.jsonl`、冻结 PNG/NPZ/来源、run_info/校验、预览、通用核查及专项报告；视频与标注等按 Git 忽略留本地。
关闭输出 633 帧，状态为 TRACKING=191、LOST=293、RECOVERY_CANDIDATE=149，0 接受。另用一次性 Python 对每条基线调用原 TargetState，与关闭结果的全部原有字段比较一致，报告为 `comparison_and_preservation.json`。本片没有单独运行第一步输出，所以通用核查的 disabled_matches_step1=false 表示未提供该输出，直接等价检查见专项报告。
对先前正例 v2/第一步/第二步/关闭、模块夹具及身份记录共 84 个文件做前后 SHA-256，全部未变；清单在输入检查目录 `previous_outputs_before.json`。新基线的 15 个文件也由运行/核查保全。
31 项 unittest 通过：原 23 + 8 项负例评价边界，覆盖无检测、低质、合格拒绝、合格待接受、错误位置/接受、人工区域不匹配、确认计数、区间不完整/缺身份依据、拒绝字符串与门槛矛盾。这些测试不计为真实拒绝率。

## 限制与交接

本片遮挡的是整个镜头，不能验证背景持续可见的不同瓶子遮挡负例。f180 可见原瓶子提前 UNKNOWN 是检测框与相对纹理区域敏感性的实际失败记录；未放宽阈值掩盖它。真实双瓶竞争、同包装替换、M3 独立保留测试和速度对照仍未运行。
已有正例正确接受 1、挂包合格裁剪拒绝 2、此真实不同瓶子区间拒绝 148，支持有限的开发恢复/拒绝交付；不将单段零错误推成准确率，不声称通用 ReID。00/04 重新读取记录与实际输出后复核验收。
用户下一项只有观看新状态视频末段约16—21秒，核对拒绝框存在时 T1 是否仍为 UNKNOWN、没有 T1 绿色已绑定框，并给出观看反馈；不代填学习理解。
