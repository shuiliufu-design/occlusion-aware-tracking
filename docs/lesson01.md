# 第一课：让程序读懂视频的基本结构

今天的完成标准：环境检查通过；程序读取视频并保存首帧和信息文件。
这是数据流程验证，不代表 AI 检测、跟踪或恢复已经完成。

## 1. 为什么创建虚拟环境

`.venv` 是这个项目独立的 Python 和依赖目录。激活后，`python`
会指向它，避免不同项目的依赖混在一起。
`python -m pip` 的含义是“用当前 Python 对应的 pip 安装”。

在项目根目录执行（本会话已创建 `.venv`，你无需重复创建）：

```bash
source .venv/bin/activate
python scripts/check_env.py
```

换电脑或从 GitHub 克隆后，先执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell 的激活命令为 `.venv\Scripts\Activate.ps1`。
今天推荐使用 Ubuntu，不需要配置 CUDA。

## 2. 视频不是一张图

视频是一系列随时间排列的图像，每张图叫一帧。
FPS 是每秒帧数，分辨率是每帧的宽度和高度。
`frame.shape` 的顺序是 `(高度, 宽度, 通道数)`，不是宽度在前。
普通彩色帧有三个通道，OpenCV 默认按 BGR 排列。

在 `scripts/inspect_video.py` 中，先理解这三行：

```python
cap = cv2.VideoCapture(str(source))
ok, frame = cap.read()
height, width, channels = frame.shape
```

第一行打开视频；第二行读取一帧，`ok` 表示是否成功；第三行取图像尺寸。
之后用循环不断 `read()`，直到无法继续读取，并通过 `release()` 释放资源。
这个流程来自 [OpenCV 官方视频入门教程](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html)。

## 3. 用自己的视频运行

拍摄方法见 `data/README.md`。把视频放到 `data/tabletop_01.mp4` 后执行：

```bash
python scripts/inspect_video.py --source data/tabletop_01.mp4 --output outputs/tabletop_01
```

输出：`first_frame.jpg` 是首帧，`video_info.json` 保存尺寸、帧率和解码帧数。
为避免覆盖旧结果，输出目录必须为空；重复实验时换一个目录名。
时长只是估算，手机的可变帧率以及解码问题可能导致偏差。

没有真实视频时，也可验证读写流程：

```bash
python scripts/make_sample_video.py
python scripts/inspect_video.py --source data/synthetic_io.avi --output outputs/synthetic_io
```

这是自检用图形视频，不能拿它作为 AI 模型效果展示或研究结论。

## 4. 你需要亲自确认的三件事

- 首帧预览是否与视频开头一致？
- 输出宽高是否符合视频的实际方向？
- 能否解释 `ok`、`frame.shape` 和 FPS 分别是什么意思？

把观察写进 `docs/learning_log.md`，下一课再加入预训练目标检测。

## 5. Git 与 GitHub

Git 在本地记录代码版本；GitHub 保存远程仓库。
`.gitignore` 定义哪些本地文件不进入版本管理。用 `git status` 查看待提交内容。

当前已准备好适合上传的源文件，已有首次本地提交。
用户已创建 [GitHub 项目仓库](https://github.com/shuiliufu-design/occlusion-aware-tracking)，
origin 已配置；首次推送仍需执行并验证。视频和 `.venv` 默认不上传。

以下是新项目创建空仓库的方法（当前项目已完成这一步）：

1. 登录 GitHub，打开 [新建仓库页面](https://github.com/new)。
2. Owner 选择自己的账号，Repository name 填 `occlusion-aware-tracking`。
3. Description 可填 `Learning reliable visual tracking under occlusion for robot perception.`。
4. 希望直接展示作品可选 Public；希望先自己开发可选 Private。
5. 不初始化 README、`.gitignore` 或 License；本地已经有项目文件。
6. 点击 Create repository，然后把生成的仓库链接发到当前对话。

这符合 [GitHub 官方创建说明](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)：
上传已有本地项目时不要预先填充远程文件，以避免产生两套初始历史。
下一步再确认提交内容、设置远程地址并上传，不需要在聊天中提供密码或 token。

本项目已经配置远程地址，之后可以用 `git remote -v` 查看。
`git commit` 将选定变更保存为本地版本，`git push` 将提交上传到远程。
当本地 main 分支准备好时，首次上传使用 `git push -u origin main`；
`-u` 建立本地与远程分支的对应关系，以后可使用 `git push`。

第一阶段无需选择开源许可证；如希望允许他人复用，之后再选择适合的许可证。
引入模型或第三方代码后，应保留出处并核对其许可证。

## 本会话完成的验证

2026-09-30：Python 3.12.3、OpenCV 4.12.0、NumPy 2.2.6 的读写流程已运行。
合成视频的 100 帧全部读出，尺寸为 640×360，名义帧率为 20 FPS，
估算时长为 5 秒；首帧图片尺寸与生成参数一致。
缺失输入和已有非空输出目录均给出了错误提示。
已确认 `.venv`、输入视频和生成结果被 `.gitignore` 排除。
真实视频尚未提供，AI 模型和 GPU 尚未验证。
