"""逐帧读取本地视频，保存首帧和基本信息；尚不进行 AI 检测或跟踪。"""

import argparse
import json
import math
from pathlib import Path

import cv2


def inspect_video(source: Path, output: Path) -> dict:
    if not source.is_file():
        raise ValueError(f"视频文件不存在: {source}")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"输出目录不为空，请换一个 --output 路径: {output}")

    # VideoCapture 打开视频；read 每次解码一帧，返回成功标志和像素数组。
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        cap.release()
        raise ValueError("无法打开视频；请确认是可播放的 MP4/AVI/MOV 文件。")

    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if not math.isfinite(fps) or fps <= 0:
            fps = None
        ok, frame = cap.read()
        if not ok or frame is None:
            raise ValueError("无法解码第一帧；可尝试将手机视频导出为 H.264 MP4。")

        # frame.shape 是 (高度, 宽度, 通道数)，OpenCV 的彩色通道顺序为 BGR。
        height, width, channels = frame.shape
        output.mkdir(parents=True, exist_ok=True)
        preview = output / "first_frame.jpg"
        if not cv2.imwrite(str(preview), frame):
            raise ValueError("保存首帧失败，请检查输出目录权限。")

        # 实际数出成功解码的帧，不将容器里声明的帧数当作实测值。
        frames_read = 1
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames_read += 1
    finally:
        # 即使中间报错，也应释放文件资源。
        cap.release()

    info = {
        "input_filename": source.name,
        "width": width,
        "height": height,
        "channels": channels,
        "nominal_fps": fps,
        "frames_read": frames_read,
        "estimated_duration_seconds": round(frames_read / fps, 3) if fps else None,
        "preview": preview.name,
        "opencv_version": cv2.__version__,
        "notes": [
            "时长按成功解码帧数和名义帧率估算；可变帧率视频可能有偏差。",
            "读取停止可能是正常结尾或解码失败；本步骤不保证视频完整性。",
            "此结果仅验证视频读取，不包含检测、跟踪或恢复能力。",
        ],
    }
    (output / "video_info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="本地视频路径")
    parser.add_argument("--output", type=Path, default=Path("outputs/lesson01"),
                        help="空的输出目录，默认 outputs/lesson01")
    args = parser.parse_args()
    try:
        info = inspect_video(args.source, args.output)
    except (ValueError, OSError, cv2.error) as exc:
        parser.exit(1, f"视频检查失败: {exc}\n")
    print(json.dumps(info, ensure_ascii=False, indent=2))
    print(f"首帧预览: {args.output / 'first_frame.jpg'}")
    print(f"视频信息: {args.output / 'video_info.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
