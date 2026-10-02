# f180 有界标签纹理对齐开发候选

依据 SPEC.md 2026-10-02 的唯一优先任务，增加可关闭的标签纹理整数平移。旧 `configs/recovery.json` 保持原内容/SHA和默认行为；开发配置为 `configs/recovery_f180_dev.json`，新增四项：启用开关、横/纵最大位移比例0.10、最小共同区域0.80。这不是M3冻结。

在64×96标签纹理上，仅搜索包含零位移的±6/±9像素；`shift_xy`表示参考坐标=候选坐标+位移。两边仅取真实共同区域，不填充、不复制边缘、不改变尺度/旋转。共同面积>=80%、两侧std>=5、NCC有限才可比较；无有效证据则暂缓。每个参考取合法最佳NCC，再与该参考的原颜色/形状分量算S，最后按原最高S/门控/竞争规则选择；同ID不免核验。等NCC时按最小曼哈顿位移、dy、dx稳定排序，优先零位移。

原颜色/区域/质量/权重/门槛、NCC>=0.55、S>=0.70、差值0.10、确认5帧、缺失10帧均不改；不读取人工诊断标注或未来帧，不借用历史框，不更新冻结参考。活动轨迹与恢复候选共用 `compare_feature`。每项参考保存零位移NCC、选中位移、共同区域/面积/std、最终NCC/S及模式；分量核查检查合法几何与分数。

原图标注先于实现/运行固定到 `outputs/f180_alignment_dev/diagnosis/visibility_annotations.json`，区间 `[170,196)`：清楚 `[170,181)`、局部不可靠 `[181,187)`、边界不确定 `[187,188)`、全遮挡 `[188,196)`。逐帧PNG/SHA与两张拼图保留，不能按算法失效帧定义真值。清楚帧人工框为目视近似区域，非全片逐帧真值。

候选实现阶段实际运行69项测试通过（原54+新增15），包含合法/超限平移、重叠、共同区域退化/非有限值、关闭保持原数值字段、同一最佳参考、竞争、同ID错误外观、质量暂缓、连续确认/恢复后再丢失。f180单帧因合法对齐通过、f181仍CAP_INSUFFICIENT_COLOR只是分量检查，尚须完整开发回归；完整结果随后记录。

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
