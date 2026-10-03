# 第一版本地演示入口

先打开本地 [演示索引](../outputs/m4_release_v1/demo/index.html)，或用下面九段完整视频。页面用同步原帧对照图保留确认等待、未返回和负例，没有只剪成功片段。视频为 mp4v，无音频；用本机支持该格式的播放器打开，浏览器未必支持此编码。

| 物理操作（拍摄者已确认） | A 初始原生 ID | B 仅状态/候选 | C 外观恢复 |
| --- | --- | --- | --- |
| 同一瓶子原位重现 | [完整 A](../outputs/m3_holdout_comparison_v2/holdout_return_01/A/status.mp4) | [完整 B](../outputs/m3_holdout_comparison_v2/holdout_return_01/B/status.mp4) | [完整 C](../outputs/m3_holdout_comparison_v2/holdout_return_01/C/status.mp4) |
| 遮挡期间只移动原瓶子、未替换 | [完整 A](../outputs/m3_holdout_comparison_v2/holdout_return_02/A/status.mp4) | [完整 B](../outputs/m3_holdout_comparison_v2/holdout_return_02/B/status.mp4) | [完整 C](../outputs/m3_holdout_comparison_v2/holdout_return_02/C/status.mp4) |
| 取走原 T1、换蓝标 T2，T1 此后未入镜 | [完整 A](../outputs/m3_holdout_comparison_v2/holdout_replacement_01/A/status.mp4) | [完整 B](../outputs/m3_holdout_comparison_v2/holdout_replacement_01/B/status.mp4) | [完整 C](../outputs/m3_holdout_comparison_v2/holdout_replacement_01/C/status.mp4) |

每片三组均从原 f0 开始，分别 341/476/573 帧、名义 FPS 约 30.005。输出视频保持整片原帧顺序，按名义 FPS 恒定帧率写出；源视频可能有帧时差，精确定位看 `frames.jsonl` 的 `frame_index`、`timestamp_seconds`、`source_pos_msec_seconds`，不要以播放器四舍五入的秒数代替事件原帧。并排截图取同一原帧，不代表已做速度比较。

## 一次完整讲解

1. 展示初始化：人工只选择早期无遮挡原图中的 T1；原生 ID 是关联编号，T1 是项目目标标识。C 用初始化后原像素因果建库并冻结，人工评价真值不参与候选选择。
2. 原位片：看遮挡前、遮挡时 UNKNOWN、重现后 A/B 未返回；在 [f210 / f214 三组对照](../outputs/m4_release_v1/demo/holdout_return_01.jpg) 中，C f210 清楚可见仍 UNKNOWN，连续确认到 f214 才接受。第一片 31 帧无检测超过原生缓冲 30，不宣传短于缓冲优势。
3. 移位片：看同一瓶子在新位置出现；[f280 / f283 对照](../outputs/m4_release_v1/demo/holdout_return_02.jpg) 保留 C 等待和两组未返回。C f283 绑定新 native ID3，不把它改名为旧 ID1；正确物理身份另由操作与原图标注评价。
4. 替换片：T1 被取走，局部手持 T2 的 f391 质量暂缓且完整几何未评价；[f391 / f443 / f572 对照](../outputs/m4_release_v1/demo/holdout_replacement_01.jpg) 保留完整过程。C 清楚区间拒绝候选，T1 当前位置始终 UNKNOWN。A/B 没有外观拒绝机制，它们不绑定不算同等拒绝验证。
5. 展示 [实测表与限制](m3_results.md)：两个返回机会、一个替换事件；C 2/88 UNKNOWN 留作失败，130 合格候选帧不是 130 次实验。速度、全片精确率、双瓶/同包装/泛化仍未验证或未评价。

视频和对照图只有**程序输出框/文字**，没有人工真值框。绿色 T1 表示当前程序观察；候选标签可能 ACCEPTABLE、REJECTED_APPEARANCE、DEFERRED_QUALITY 或 UNVERIFIED；程序接受不等于已经通过人工评价。`outputs/m3_holdout_annotations_*/` 中的原图与标签用于评价，不是这些演示框的来源。

九段视频、派生对照图与页面留本地，不在 Git。没有本地包时按 [README 主流程](../README.md#最短运行流程) 在自己的视频上生成演示，不能把这九个链接写成公开可下载资源。M4 重解码核对九段共 4,170 帧并检查链接，证据为 `outputs/m4_release_v1/demo_media_checks.json`；不重新推理或改原状态输出。
