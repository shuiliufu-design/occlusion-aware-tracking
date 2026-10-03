# M4 发布流程核查

2026-10-03，起始 HEAD `5006d96`。本轮完成第一版 README、自己的视频主流程、有效 v2 静态实验表和本地演示入口；等待 00 验收整理交付。只改文档，没有改 12 个冻结执行文件、配置/阈值、依赖、模型、原生跟踪器、初始化协议或评价真值。只做本地提交，不推送。

## 实际运行范围

先在项目中复用开发负例的历史检测缓存核对显式冻结 C，再在独立临时复制目录从开发原视频实际生成新基线，运行 C 和关闭身份恢复的 B。所有新结果保存在 `outputs/m4_release_v1/`，旧实验不覆盖。

独立目录用 Git 文件复制形成（本次发布文档随后同步）；只链接现有 `.venv`、官方权重和一个开发输入 `tabletop_wrong_bottle_01.mp4`，以 `data/my_bottle.mp4` 作为可替换输入名。没有链接旧缓存或真值包，输出链接到新的 `outputs/m4_release_v1/clean_run/`。目录位置与清单记录在 `clean_directory.json`；所有 CLI 使用相对项目路径。

| 实际步骤 | 结果与证据 |
| --- | --- |
| 正式冻结检查 | PASS，12 执行文件与配置/依赖清单保持冻结 SHA；日志 `logs/freeze_before.log` / `freeze_after.log` |
| 已有开发缓存 → 显式冻结 C → 恢复核查 | 退出 0；633 行/视频帧，参考冻结、0 程序接受；`cached_C/` 与 `logs/cached_C*.log` |
| 独立目录环境检查 / 读取 | 退出 0；沿用既有环境，读取 633 帧，720×1280，首帧和视频信息非空 |
| 独立目录新基线 / 基线核查 | 仅一次 CPU 推理，退出 0；633 行/视频帧；`clean_run/my_bottle_v1/baseline/` |
| 早期原图导出片段 | 直接执行 `run_demo.md` 的原图片段，退出 0；导出 f0 PNG 与顺序解码原像素完全相同；人工初始化框采用已查看 f0 的开发示例 `[290,280,510,1040]`，未看后段重选 |
| 独立目录 C / 恢复核查 | 退出 0；633 行/视频帧，3 条事件、0 程序接受；`clean_run/my_bottle_v1/C/` |
| 独立目录关闭 B / 核查 | 退出 0；633 行/视频帧，3 条事件；另对所有 633 行重放原 TargetState，原字段逐项一致；`clean_run/my_bottle_v1/B/` |
| 三片九段原演示视频 | 全部重解码，共 4,170 帧，来源 SHA 保持；`demo_media_checks.json` |
| 演示对照图 | 查看三张同原帧 A/B/C 对照；保留 C 清楚可见等待、A/B 未返回、局部质量暂缓和清楚负例拒绝；只含程序框 |
| 静态结果 / 链接 / 保全 | 数字和来源对有效 v2 逐项核对；本地相对路径、文档链接/锚点检查；接手 1,702 个旧本地输入/结果/权重文件 SHA 不变 |

完整命令、工作目录、退出码和日志保存在 `clean_commands.json`；验收及边界为 `acceptance_checks.json`。`build_release_artifacts.py` 留档静态表/同帧图/九视频重解码，`verify_release.py` 留档原图片段运行、字段回放、来源/冻结/保全核查。页面入口 `demo/index.html`，Git 说明入口 [本地演示](local_demo.md)。

## 实际命令

缓存核查在项目根目录执行：

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/run_recovery.py --source data/tabletop_wrong_bottle_01.mp4 --baseline outputs/tabletop_wrong_bottle_01_baseline --output outputs/m4_release_v1/cached_C --init-frame 0 --init-box 290 280 510 1040 --init-iou 0.5 --missing-frames 10 --config configs/recovery_m3_v1.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/review_recovery.py --output outputs/m4_release_v1/cached_C --frames 0 180 485 632
```

下面在独立复制目录执行，命令与 README 主流程一致；现有结果非空，复跑必须换输出路径。该 CPU 发布核查设置 `PYTHONDONTWRITEBYTECODE=1`、`OMP_NUM_THREADS=4`、`OPENBLAS_NUM_THREADS=4`，只限制运行线程，不改算法或阈值。

```bash
.venv/bin/python scripts/check_env.py
.venv/bin/python scripts/inspect_video.py --source data/my_bottle.mp4 --output outputs/my_bottle_v1/input
.venv/bin/python scripts/run_baseline.py --source data/my_bottle.mp4 --output outputs/my_bottle_v1/baseline --model weights/yolo11n.pt --device cpu --imgsz 640 --conf 0.1 --iou 0.7
.venv/bin/python scripts/review_baseline.py --output outputs/my_bottle_v1/baseline
.venv/bin/python scripts/run_recovery.py --source data/my_bottle.mp4 --baseline outputs/my_bottle_v1/baseline --output outputs/my_bottle_v1/C --init-frame 0 --init-box 290 280 510 1040 --init-iou 0.5 --missing-frames 10 --config configs/recovery_m3_v1.json
.venv/bin/python scripts/review_recovery.py --output outputs/my_bottle_v1/C
.venv/bin/python scripts/run_recovery.py --source data/my_bottle.mp4 --baseline outputs/my_bottle_v1/baseline --output outputs/my_bottle_v1/B --init-frame 0 --init-box 290 280 510 1040 --init-iou 0.5 --missing-frames 10 --config configs/recovery_m3_v1.json --disable-recovery
.venv/bin/python scripts/review_recovery.py --output outputs/my_bottle_v1/B
```

原图导出片段和根目录生成/核查也实际执行，详见日志。上述使用一个开发负例，0 接受不意味着普遍正确拒绝；没有给发布运行传身份标注，不另报恢复准确率或 M3 成败。旧通用 `evaluation.json` 的 `unrecovered_events` / `PENDING_INPUT` / `m2_step2_fully_accepted=false` 属于该辅助报告，不能替代已通过的独立 M3 评价，也不能把零返回机会替换算成一次恢复失败。

## 证据边界与交接

- 没有新装环境、重新下载权重、运行新机器安装或本轮 GPU 推理；不是完整干净安装验证。CPU 新缓存用于发布流程，不替代原 GPU M3 公共缓存，也不保证 CPU/GPU 逐位结果相同。
- 没有新 M3 样本、重新运行九组三片实验、改真值/分母或新增算法。03 的 110 项全套与 00 的 28 项/冻结评价仍是各自历史证据，本轮没有重跑这些测试并据为本轮结论。
- 速度仍未验证，全片精确误报率未评价；C 2/88 UNKNOWN、A/B 未返回、局部几何不足、保守锚点、拍摄偏差、无第二人类逐帧复核、双瓶/同包装/泛化与纹理独立贡献限制均保留。
- 九段视频/三张派生图的 OpenCV 解码与目视检查不等于所有浏览器/播放器兼容性测试。本地 HTML 提供图片和完整视频链接，未声称浏览器可内嵌播放 mp4v。
- 接手时已有其他聊天的 STATUS 讨论和学习记录；保存初始副本，提交只纳入 M4 自己的状态差异，其他未提交内容保持并排除。媒体、权重、环境和 outputs 不入 Git。

下一项交 00：重新读取项目记录，核对 [README](../README.md)、[运行说明](run_demo.md)、[实验表](m3_results.md)、[本地演示](local_demo.md) 和本地 `acceptance_checks.json`，判断第一版整理是否达到 M4 验收。GitHub 同步与后续研究另由用户/00决定，本轮不推送。
