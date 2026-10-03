# 项目提交身份与实验档案

2026-10-03，用户明确要求整个项目的GitHub提交与贡献者关联到自己的账号。公开身份为 `shuiliufu-design`，提交邮箱为该账号设置页面提供、并与实际GitHub账号ID一致的 `232509668+shuiliufu-design@users.noreply.github.com`。

## 本次修改范围

44条原始提交均沿用了同一误配置身份。逐条重新生成提交，只修正author/committer姓名与邮箱；每个版本的tree、说明、日期及父提交顺序保持。公开仓库包含完整工程历史、代码、配置、依赖说明、测试与项目文档。后续新提交继续使用本项目的正确身份；全局Git配置保持。

用户本次授权修正整段历史，覆盖此前仅正常同步、不改写历史的任务限制。只更新现有仓库main，使用绑定更新前远程SHA的 `--force-with-lease`；远程变化时拒绝覆盖。未删除或重建仓库、未更改模型/阈值/冻结算法或旧输出。贡献者统计由GitHub自动计算，历史更新后可能约24小时刷新，不属于可手工编辑的名单。[GitHub说明](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-a-projects-contributors)

## 原实验版本与公开版本

[版本对应表](git_commit_map.json)记录44条原始实验版本、修正作者后的公开版本及共同tree。表中的原始SHA是实验发生时的真实记录；修正后的SHA用于在当前公开历史中查看对应代码。不得把身份修正写成新实验、改成功率或篡改原运行来源。

冻结清单、静态结果来源与本地运行信息保留原始SHA和文件校验。当前本机Git保留私有引用 `refs/archive/identity-before-20261003`，原始对象仍可供 `git show` / 历史评价核查使用；该引用不推送到GitHub。完整原始Git档案另存本地：

```text
outputs/git_identity_rewrite_v1/original_history.bundle
```

新克隆运行自己的视频，使用[正常主流程](run_demo.md)，不需要原实验档案。**精确复现三片实验**仍需[本地数据/缓存/标注包](m3_results.md#精确实验复现)，身份修正后还需上述私有Git档案。包准备好后，在新的克隆中导入本地引用即可恢复原SHA查找：

```bash
git fetch /absolute/path/original_history.bundle refs/archive/identity-before-20261003:refs/archive/identity-before-20261003
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/m3_common.py --check-freeze configs/m3_freeze_v1.json
```

替换第一行绝对路径为实际本地档案位置；此导入不改变main，不公开档案，不覆盖数据。不能将原始档案引用再次推送到远程；后续发布只正常推送main，避免使用镜像推送。

本地核查与远程结果保存在 `outputs/git_identity_rewrite_v1/`。视频、环境、权重、缓存、原始标注、结果与档案仍按.gitignore留本地。算法/速度/泛化及全新安装的原限制保持。

## 首页侧栏显示待验收（2026-10-03）

远程46条提交author/committer、REST Contributors及真实贡献者图表均已关联本人，图表计46条；用户截图与00浏览器仍看到首页侧栏两个账号。此前只检查接口与初始HTML就宣告显示完成，证据范围不足，现更正为待刷新。当前行为符合GitHub所述历史改写后的统计延迟；尚无办法在本项目代码中强制刷新该服务器侧栏。

历史更新约2026-10-03 19:24（Asia/Shanghai）；建议10月4日19:30后复核已加载的真实侧栏。约24小时是官方估计，不是保证截止时间；若届时仍错误，按上述官方说明由仓库所有者联系GitHub Support。只有首页实际不再列出旧账号才算完成显示验收。
