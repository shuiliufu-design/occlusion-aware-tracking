"""生成有遮挡的几何图形视频，仅用于视频 I/O 自检，不是 AI 评测数据。"""

import argparse
from pathlib import Path

import cv2
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/synthetic_io.avi"))
    args = parser.parse_args()
    if args.output.exists():
        parser.exit(1, "输出文件已存在，请指定另一个 --output 路径。\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    size = (640, 360)
    writer = cv2.VideoWriter(str(args.output), cv2.VideoWriter_fourcc(*"MJPG"), 20, size)
    if not writer.isOpened():
        writer.release()
        parser.exit(1, "MJPG 编码器不可用，无法生成自检视频。\n")
    try:
        for index in range(100):
            frame = np.full((size[1], size[0], 3), 235, dtype=np.uint8)
            x = 80 + index * 4
            cv2.rectangle(frame, (x, 160), (x + 50, 210), (70, 110, 210), -1)
            # 中间的灰色矩形遮挡移动方块。
            cv2.rectangle(frame, (270, 120), (360, 260), (120, 120, 120), -1)
            cv2.putText(frame, f"SYNTHETIC I/O CHECK | frame {index}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 1)
            writer.write(frame)
    finally:
        writer.release()
    print(f"生成自检视频: {args.output} (640x360, 20 FPS, 100 帧)")
    print("这只是几何图形视频，不能证明真实物体检测或跟踪效果。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
