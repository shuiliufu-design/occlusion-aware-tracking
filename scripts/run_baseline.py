"""M1：YOLO11n 检测 + 未修改的 Ultralytics ByteTrack，逐帧保存证据。"""

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import shlex
import sys
import time
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 配置与缓存留在项目内；不在运行时偷偷安装依赖。
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT / ".cache/ultralytics"))
os.environ["YOLO_AUTOINSTALL"] = "false"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(args: argparse.Namespace) -> dict:
    Path(os.environ["YOLO_CONFIG_DIR"]).mkdir(parents=True, exist_ok=True)
    import cv2
    import numpy as np
    import torch
    import yaml
    from ultralytics import YOLO
    from ultralytics.trackers.byte_tracker import BYTETracker
    from ultralytics.utils import ROOT

    if not args.source.is_file():
        raise ValueError(f"视频不存在: {args.source}")
    if not args.model.is_file():
        raise ValueError(f"权重不存在: {args.model}；请按 README 下载官方权重。")
    if args.output.exists() and (
        not args.output.is_dir() or any(args.output.iterdir())
    ):
        raise ValueError(f"输出目录不为空或不是目录，请换路径: {args.output}")

    device = args.device
    if device == "auto":
        device = "0" if torch.cuda.is_available() else "cpu"
    gpu_check = {"cuda_available": torch.cuda.is_available(), "device": device}
    if device != "cpu":
        if not torch.cuda.is_available():
            raise ValueError("CUDA 不可用；如处于受限沙箱，先验证沙箱外 GPU，或显式选 --device cpu。")
        # 不仅检查设备可见性：实际矩阵乘法与取回结果。
        cuda_device = torch.device(f"cuda:{device}")
        ones = torch.ones((32, 32), device=cuda_device)
        value = (ones @ ones)[0, 0].item()
        if value != 32.0:
            raise RuntimeError(f"GPU 运算校验失败: {value}")
        gpu_check.update({"name": torch.cuda.get_device_name(cuda_device),
                          "matrix_multiply_value": value, "compute_verified": True})
    else:
        gpu_check["compute_verified"] = False

    model = YOLO(str(args.model))
    class_ids = [key for key, name in model.names.items() if name == args.class_name]
    if not class_ids:
        raise ValueError(f"模型类别不含 {args.class_name!r}")
    config_path = ROOT / "cfg/trackers/bytetrack.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    config = yaml.safe_load(config_text)
    # 与该版本集成入口一样使用 30；默认缓冲 30 帧，不按观测结果调参。
    tracker = BYTETracker(SimpleNamespace(**config), frame_rate=30)

    cap = cv2.VideoCapture(str(args.source))
    writer = None
    frames_read = 0
    frames_with_detection = 0
    frames_with_track = 0
    id_counts = {}
    inference_seconds = 0.0
    tracking_seconds = 0.0
    try:
        if not cap.isOpened():
            raise ValueError("无法打开视频")
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("无有效名义 FPS，无法确定输出视频帧率")
        declared_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        ok, frame = cap.read()
        if not ok or frame is None:
            raise ValueError("无法解码首帧")
        height, width = frame.shape[:2]
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "bytetrack.yaml").write_text(config_text, encoding="utf-8")
        writer = cv2.VideoWriter(str(args.output / "annotated.mp4"),
                                 cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        if not writer.isOpened():
            raise ValueError("无法创建 mp4v 带框视频")

        started = time.perf_counter()
        with (args.output / "frames.jsonl").open("w", encoding="utf-8") as records:
            while ok and frame is not None:
                if frame.shape[:2] != (height, width):
                    raise ValueError("视频帧尺寸发生变化")
                frame_index = frames_read
                estimated_time = frame_index / fps
                source_time = float(cap.get(cv2.CAP_PROP_POS_MSEC)) / 1000
                # 1. 图像像素 -> 检测。只保留 bottle 类；阈值后的原始框完整保存。
                before_predict = time.perf_counter()
                result = model.predict(frame, imgsz=args.imgsz, conf=args.conf,
                                       iou=args.iou, classes=class_ids,
                                       device=device, verbose=False)[0]
                boxes = result.boxes.cpu().numpy()
                inference_seconds += time.perf_counter() - before_predict
                detections = []
                for index, (xyxy, score, cls) in enumerate(zip(boxes.xyxy, boxes.conf, boxes.cls)):
                    detections.append({"detection_index": index,
                                       "bbox_xyxy": [float(x) for x in xyxy],
                                       "class_id": int(cls), "class_name": model.names[int(cls)],
                                       "detection_score": float(score), "track_id": None})

                # 2. 检测 -> ID。每帧都推进原生跟踪器，空检测帧也不跳过。
                # 8.3.221 返回的索引属于高/低分数子集；映射回完整检测列表。
                # 只整理输出索引，原生关联算法、框、分数与 ID 均不修改。
                high_indices = np.flatnonzero(boxes.conf >= config["track_high_thresh"])
                low_indices = np.flatnonzero((boxes.conf > config["track_low_thresh"]) &
                                             (boxes.conf < config["track_high_thresh"]))
                before_track = time.perf_counter()
                track_rows = tracker.update(boxes, frame)
                tracking_seconds += time.perf_counter() - before_track
                tracks = []
                for row in track_rows:
                    subset_indices = high_indices if row[5] >= config["track_high_thresh"] else low_indices
                    detection_index = int(subset_indices[int(row[7])])
                    track_id = int(row[4])
                    if not math.isclose(detections[detection_index]["detection_score"], float(row[5]), abs_tol=1e-6):
                        raise RuntimeError("跟踪输出无法映射回原始检测；请核对固定版本的 API")
                    detections[detection_index]["track_id"] = track_id
                    tracks.append({"track_id": track_id,
                                   "bbox_xyxy": [float(x) for x in row[:4]],
                                   "detection_index": detection_index,
                                   "class_id": int(row[6]), "class_name": model.names[int(row[6])],
                                   "detection_score": float(row[5])})
                    id_counts[str(track_id)] = id_counts.get(str(track_id), 0) + 1

                record = {"frame_index": frame_index,
                          "timestamp_seconds": estimated_time,
                          "source_pos_msec_seconds": source_time if math.isfinite(source_time) else None,
                          "detections": detections, "tracks": tracks}
                records.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")

                # 3. ID -> 可检查输出。不绘制隐藏目标的预测位置。
                for detection in detections:
                    if detection["track_id"] is not None:
                        continue
                    x1, y1, x2, y2 = [round(x) for x in detection["bbox_xyxy"]]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 190, 255), 2)
                    cv2.putText(frame, f"{args.class_name} unassigned {detection['detection_score']:.2f}",
                                (max(0, x1), max(80, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.55, (0, 190, 255), 2)
                for track in tracks:
                    x1, y1, x2, y2 = [round(x) for x in track["bbox_xyxy"]]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 230, 80), 2)
                    cv2.putText(frame, f"{args.class_name} ID {track['track_id']} det {track['detection_score']:.2f}",
                                (max(0, x1), max(80, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (50, 230, 80), 2)
                cv2.rectangle(frame, (0, 0), (width, 70), (20, 20, 20), -1)
                cv2.putText(frame, f"f{frame_index}  {estimated_time:.2f}s  {args.model.stem} + ByteTrack",
                            (12, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                message = ("NO BOTTLE DETECTION; POSITION UNKNOWN" if not detections
                           else "Green: native track | Yellow: unassigned detection")
                cv2.putText(frame, message, (12, 53), cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (255, 255, 255), 1)
                writer.write(frame)
                if frame_index == 0:
                    if not cv2.imwrite(str(args.output / "first_frame.jpg"), frame):
                        raise ValueError("首帧保存失败")
                frames_read += 1
                frames_with_detection += bool(detections)
                frames_with_track += bool(tracks)
                if frames_read % 100 == 0:
                    print(f"已处理 {frames_read} 帧", flush=True)
                ok, frame = cap.read()
        wall_seconds = time.perf_counter() - started
    finally:
        cap.release()
        if writer is not None:
            writer.release()

    info = {
        "completed": True,
        "command": shlex.join(sys.orig_argv),
        "runner_sha256": sha256(Path(__file__)),
        "source": str(args.source), "source_sha256": sha256(args.source),
        "model": str(args.model), "model_sha256": sha256(args.model),
        "model_origin": ("https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt"
                         if args.model.name == "yolo11n.pt" else None),
        "tracker": "ultralytics.trackers.byte_tracker.BYTETracker",
        "tracker_config_sha256": sha256(config_path),
        "detection_index_mapping": "Ultralytics 8.3.221 track row idx is relative to high/low confidence subset; mapped back to full detections using unchanged YAML thresholds",
        "tracker_config": config, "tracker_constructor_frame_rate": 30,
        "effective_max_time_lost_frames": tracker.max_time_lost,
        "custom_recovery_enabled": False,
        "class_name": args.class_name, "class_ids": class_ids,
        "inference": {"imgsz": args.imgsz, "conf": args.conf, "iou": args.iou, "device": device},
        "gpu_check": gpu_check,
        "versions": {name: importlib.metadata.version(name) for name in
                     ("ultralytics", "torch", "torchvision", "opencv-python", "numpy", "lap", "scipy", "PyYAML")},
        "python": platform.python_version(),
        "width": width, "height": height, "nominal_fps": fps,
        "container_declared_frames": declared_frames, "frames_processed": frames_read,
        "tracker_updates": tracker.frame_id,
        "frames_with_detection": frames_with_detection, "frames_with_track": frames_with_track,
        "track_id_frame_counts": id_counts,
        "timing": {"wall_seconds": wall_seconds, "processing_fps": frames_read / wall_seconds,
                   "predict_seconds": inference_seconds, "tracker_update_seconds": tracking_seconds,
                   "scope": "loop includes first-inference initialization, decode, predict, association, drawing, JSON and video writes; excludes model load, GPU check and final encoder release"},
        "output_video": "annotated.mp4", "video_codec": "mp4v", "records": "frames.jsonl",
        "notes": [
            "frame_index 从 0 开始；timestamp_seconds=frame_index/nominal_fps，是估算时间。",
            "source_pos_msec_seconds 是 OpenCV 解码后报告的时间；输出视频按名义 FPS 恒定帧率写出，无音频。",
            "detections 为 NMS/类别/分数筛选后的原始检测框；tracks 为原生跟踪器的关联与滤波框。",
            "每帧调用原生 BYTETracker.update，包括空检测帧；关联算法与包内 YAML 未修改。",
            "未关联检测 track_id=null；无检测不证明完全遮挡；隐藏时不绘制预测框。",
            "检测分数不等于跟踪可靠性，ID 相同或再次出现框不证明目标身份正确。",
            "bottle 类筛选不识别红盖或指定身份；相似瓶子仍可能误关联。",
            "解码停止可能是正常结束或错误；completed 不表示源视频完整性已证实。",
        ],
    }
    (args.output / "run_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="新的空输出目录")
    parser.add_argument("--model", type=Path, default=Path("weights/yolo11n.pt"))
    parser.add_argument("--class-name", default="bottle")
    parser.add_argument("--device", choices=("auto", "cpu", "0"), default="auto")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.1)
    parser.add_argument("--iou", type=float, default=0.7)
    args = parser.parse_args()
    if args.imgsz <= 0 or not 0 < args.conf < 1 or not 0 < args.iou <= 1:
        parser.error("imgsz 必须为正数，conf 在 (0,1)，iou 在 (0,1]")
    try:
        info = run(args)
    except (ValueError, OSError, RuntimeError, ImportError) as exc:
        parser.exit(1, f"基线运行失败: {exc}\n失败目录可能已有部分输出，请保留并换新目录重跑。\n")
    print(f"完成 {info['frames_processed']} 帧；结果: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
