# Occlusion-Aware Tracking

固定相机、直立瓶子的**二维离线跟踪与遮挡后恢复 Demo**。输入录制视频，输出状态视频、逐帧记录、候选证据和事件；不包含机器人控制、3D 位姿或模型训练。

第一版使用 YOLO11n + Ultralytics ByteTrack，新增人工目标初始化、冻结外观参考、质量/竞争门控、有界标签纹理对齐、连续 5 帧确认和目标重新绑定。完全不可见或证据不足时当前位置为 `UNKNOWN`，不绘制历史框充当当前位置。

## 已测结果

2026-10-03 冻结后录制的三片小规模保留测试，共两个原目标返回机会、一次不同瓶子替换事件：

| 组别 | 正确返回 / 返回机会 | 清楚 T1 固定样本 UNKNOWN |
| --- | --- | --- |
| A：只沿初始化原生 ID | 0/2（两次未返回） | 34/88 |
| B：关闭身份恢复，仅状态/候选 | 0/2（两次未返回） | 34/88 |
| C：冻结外观恢复 | 2/2 | 2/88 |

C 两次返回延迟为 10/4 原帧；一次替换事件的 130 个合格候选帧全部外观拒绝、0 绑定。替换时原目标未返回，返回率与延迟不适用。**2/2 不是通用 100% 准确率，130 帧不是 130 个独立实验。** 原生 ByteTrack 已有短时轨迹保留/关联能力；第一片实际 31 帧无检测超过缓冲 30，本次不证明短于缓冲时限的优势。

[逐片实验表与来源](docs/m3_results.md) · [完整成败与覆盖](docs/m3_holdout_comparison.md) · [00 复核范围](docs/m3_holdout_comparison_00_review.md) · [本地演示入口](docs/local_demo.md)

## 最短运行流程

在项目根目录运行，沿用现有 `.venv`。准备自己的固定相机直立瓶子视频，开头留充分无遮挡画面；瓶盖与标签朝向相机。先完成[依赖/权重准备](docs/run_demo.md#环境与模型)，再执行：

```bash
SOURCE=data/my_bottle.mp4
RUN=outputs/my_bottle_v1
.venv/bin/python scripts/check_env.py
.venv/bin/python scripts/inspect_video.py --source "$SOURCE" --output "$RUN/input"
.venv/bin/python scripts/run_baseline.py --source "$SOURCE" --output "$RUN/baseline" --model weights/yolo11n.pt --device cpu --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/review_baseline.py --output "$RUN/baseline"
```

只看早期无遮挡**原图**确定初始化帧和目标完整框。下面的框仅为坐标格式示例，必须换成自己的 `[左, 上, 右, 下]` 原图像素；帧索引从 0 开始。不要根据后段恢复效果重选初始化。

```bash
INIT_FRAME=0
INIT_BOX=(290 280 510 1040)
.venv/bin/python scripts/run_recovery.py --source "$SOURCE" --baseline "$RUN/baseline" --output "$RUN/C" --init-frame "$INIT_FRAME" --init-box "${INIT_BOX[@]}" --init-iou 0.5 --missing-frames 10 --config configs/recovery_m3_v1.json
.venv/bin/python scripts/review_recovery.py --output "$RUN/C"
```

查看 `$RUN/C/status.mp4`、`frames.jsonl`、`events.jsonl` 和 `references.json`。初始化必须唯一匹配已关联的 bottle 检测；参考不足会报告 `INSUFFICIENT_REFERENCE`。程序接受是外观规则判断，自己的视频没有独立身份评价时不能记作正确恢复。详细[人工初始化、字段和排错](docs/run_demo.md#人工初始化)见运行说明。

**必须显式传入 `configs/recovery_m3_v1.json` 才是实测 C。** CLI 默认仍是旧 `configs/recovery.json`，未启用有界对齐。关闭身份恢复使用同一命令加 `--disable-recovery`，并把输出改为新的 `$RUN/B`；它退回仅候选状态，原始基线保留在 `$RUN/baseline`。

所有输出目录须为空，复跑换新的 `RUN`，保留失败与旧结果。GPU 可用时可将 `--device cpu` 换成 `--device 0`；本机历史 GPU 推理已验证，发布流程的实际验证范围见[复现核查](docs/m4_validation.md)，没有速度对照结论。

## 范围与限制

- C 在整瓶清楚可见的 f210—213 / f280—282 仍等待确认、位置 UNKNOWN，固定样本 f210/f280 保留为失败。
- 三片有拍摄时长偏差；物理操作由拍摄者确认，框/可见性由 Codex 看原图标注，无第二位人类逐帧复核。局部几何不足和保守重现锚点保留。
- 真实双瓶歧义、相同包装替换、困难例、泛化性能和纹理对齐的独立贡献未验证；同包装的不同实体可能误认。分数与 ID 都不是身份概率。
- 全片精确误报率未评价，公平新增开销和端到端速度未验证。固定 88 个清楚 T1 样本不代表全片逐帧评价。
- 视频为 mp4v、名义 FPS 恒定帧率、无音频；保留原帧索引和源时间。读取停止不保证原视频完整性。

## 功能运行与实验复现

Git 包含代码、配置、依赖清单和静态说明；视频、权重、`.venv`、缓存、真值图片与输出留本地。新使用者可按上面的流程运行自己的视频；**精确复现三片数字还需要本地实验包及对应 Git 历史**，公开克隆不含这些输入。包清单、冻结 SHA 与复跑命令见[实验结果说明](docs/m3_results.md#精确实验复现)。

发布核查在只含 Git 文件的独立临时复制目录运行，沿用现有环境和权重，不等于全新机器安装验证。结果证据保存在 `outputs/m4_release_v1/`，说明见[发布验证](docs/m4_validation.md)。

2026-10-03 第一版已通过[00受限验收](docs/m4_acceptance_00.md)，M0—M4交付完成；全新安装与上述性能边界仍未验证或未评价。

## 项目记录与学习

[AGENTS.md](AGENTS.md) 记录协作规则，[SPEC.md](SPEC.md) 记录范围/验收/冻结决策，[STATUS.md](STATUS.md) 记录实际进度。接手必须重读，文件修改不会自动通知其他聊天。

教学与开发历史：[视频 I/O](docs/lesson01.md) · [基线](docs/baseline_m1.md) · [仅候选状态](docs/target_state_m2_step1.md) · [外观恢复](docs/appearance_recovery_m2_step2.md) · [真实开发负例](docs/wrong_bottle_m2_validation.md) · [统一评价](docs/offline_evaluation_m2.md) · [纹理对齐](docs/f180_alignment_development.md) · [三组协议](docs/m3_protocol.md) · [学习记录](docs/learning_log.md)。历史文档中的参数、结果和待办属于当时版本，当前实测以冻结 C 与有效 v2 为准。

仓库：[shuiliufu-design/occlusion-aware-tracking](https://github.com/shuiliufu-design/occlusion-aware-tracking)。

项目提交身份已按账号修正，完整工程历史保留；原实验SHA与当前公开版本的对应关系及本地档案用法见[提交身份与实验档案](docs/git_history_identity.md)。
