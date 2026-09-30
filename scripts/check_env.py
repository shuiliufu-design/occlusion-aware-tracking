"""第一课：确认正在使用哪个 Python、OpenCV 是否可用，以及 GPU 的可见性。"""

import importlib.metadata
import platform
import shutil
import subprocess
import sys


def main() -> int:
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"解释器: {sys.executable}")
    print(f"虚拟环境: {'是' if sys.prefix != sys.base_prefix else '否'}")
    if sys.version_info < (3, 10):
        print("请使用 Python 3.10 或更新版本。")
        return 1

    try:
        import cv2
        import numpy
    except ImportError as exc:
        print(f"依赖尚不可用: {exc}")
        print("请在虚拟环境中执行 python -m pip install -r requirements.txt")
        return 1
    print(f"OpenCV: {cv2.__version__}")
    print(f"NumPy: {numpy.__version__}")

    # OpenCV 的几个发行包共用 cv2，不能在一个环境中重复安装。
    installed = []
    for package in (
        "opencv-python", "opencv-python-headless",
        "opencv-contrib-python", "opencv-contrib-python-headless",
    ):
        try:
            installed.append(f"{package}=={importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            pass
    print(f"OpenCV 发行包: {', '.join(installed)}")
    if len(installed) > 1:
        print("发现多个 OpenCV 发行包；请在干净的虚拟环境中重新安装依赖。")
        return 1

    # 今天不需要 GPU。查询失败并不等于物理电脑没有显卡。
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            result = subprocess.run(
                [nvidia_smi, "--query-gpu=name,memory.total,driver_version",
                 "--format=csv,noheader"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                print(f"NVIDIA GPU: {result.stdout.strip()}")
            else:
                print("本会话无法查询 NVIDIA GPU，今天继续使用 CPU。")
        except (OSError, subprocess.TimeoutExpired):
            print("NVIDIA 查询未完成，今天继续使用 CPU。")
    else:
        print("未找到 nvidia-smi，今天继续使用 CPU。")
    print("第一课环境检查通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
