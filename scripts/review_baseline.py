"""核对基线逐帧记录与带框视频；生成供人工观察的预览，不计算身份准确率。"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path

import cv2
import numpy as np


def ranges(indices: list[int], fps: float) -> list[dict]:
    groups = []
    for index in indices:
        if groups and index == groups[-1][1] + 1:
            groups[-1][1] = index
        else:
            groups.append([index, index])
    return [{"first_frame": a, "last_frame": b, "frames": b - a + 1,
             "start_seconds_estimated": a / fps,
             "end_seconds_estimated_exclusive": (b + 1) / fps} for a, b in groups]


def review(output: Path, selected_frames: list[int]) -> dict:
    info = json.loads((output / "run_info.json").read_text())
    rows = [json.loads(line) for line in (output / "frames.jsonl").read_text().splitlines()]
    fps = info["nominal_fps"]
    if not rows or len(rows) != info["frames_processed"] or len(rows) != info["tracker_updates"]:
        raise ValueError("逐帧记录、处理帧数与跟踪器更新次数不一致")
    if any(index < 0 or index >= len(rows) for index in selected_frames):
        raise ValueError("选取的预览帧超出记录范围")
    id_frames = {}
    no_detection, no_track = [], []
    counts = Counter()
    previous_source_time = None
    source_time_monotonic = True
    for index, row in enumerate(rows):
        if row["frame_index"] != index or not math.isclose(row["timestamp_seconds"], index / fps):
            raise ValueError(f"帧索引或估算时间错误: {index}")
        source_time = row["source_pos_msec_seconds"]
        if source_time is not None:
            if previous_source_time is not None and source_time < previous_source_time:
                source_time_monotonic = False
            previous_source_time = source_time
        detections = row["detections"]
        tracks = row["tracks"]
        if not detections:
            no_detection.append(index)
        if not tracks:
            no_track.append(index)
        for d_index, detection in enumerate(detections):
            if detection["detection_index"] != d_index:
                raise ValueError(f"检测索引错误: {index}")
            box = detection["bbox_xyxy"]
            if len(box) != 4 or not all(math.isfinite(v) for v in box) or box[2] < box[0] or box[3] < box[1]:
                raise ValueError(f"检测框无效: {index}")
            if not 0 <= detection["detection_score"] <= 1:
                raise ValueError(f"检测分数无效: {index}")
        seen_ids, assigned_indices = set(), set()
        for track in tracks:
            track_id, d_index = track["track_id"], track["detection_index"]
            if track_id in seen_ids or d_index in assigned_indices or not 0 <= d_index < len(detections):
                raise ValueError(f"轨迹重复或关联索引无效: {index}")
            detection = detections[d_index]
            if detection["track_id"] != track_id or track["class_id"] != detection["class_id"]:
                raise ValueError(f"轨迹与检测记录不一致: {index}")
            if not math.isclose(track["detection_score"], detection["detection_score"], abs_tol=1e-6):
                raise ValueError(f"轨迹分数与检测分数不一致: {index}")
            seen_ids.add(track_id)
            assigned_indices.add(d_index)
            id_frames.setdefault(str(track_id), []).append(index)
            counts[str(track_id)] += 1
        if any(d["track_id"] is not None and d["detection_index"] not in assigned_indices for d in detections):
            raise ValueError(f"检测关联缺少轨迹: {index}")
    if dict(counts) != info["track_id_frame_counts"]:
        raise ValueError("ID 统计与运行信息不一致")
    if len(rows) - len(no_detection) != info["frames_with_detection"] or len(rows) - len(no_track) != info["frames_with_track"]:
        raise ValueError("检测/轨迹帧统计不一致")

    cap = cv2.VideoCapture(str(output / "annotated.mp4"))
    if not cap.isOpened():
        raise ValueError("带框视频无法打开")
    samples = []
    decoded = 0
    next_sample = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if decoded >= len(rows):
                raise ValueError("带框视频帧数超过逐帧记录")
            if frame.shape[:2] != (info["height"], info["width"]):
                raise ValueError("带框视频尺寸错误")
            if decoded in selected_frames:
                if not cv2.imwrite(str(output / f"frame_{decoded:06d}.jpg"), frame):
                    raise ValueError("单帧预览保存失败")
            if decoded >= next_sample:
                tile = np.full((320, 180, 3), 245, np.uint8)
                thumb = cv2.resize(frame, (180, 300))
                tile[:300] = thumb
                ids = [str(t["track_id"]) for t in rows[decoded]["tracks"]]
                cv2.putText(tile, f"{decoded / fps:.1f}s f{decoded} ID:{','.join(ids) or '-'}",
                            (2, 315), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (20, 20, 20), 1)
                samples.append(tile)
                next_sample = round(len(samples) * fps)
            decoded += 1
    finally:
        cap.release()
    if decoded != len(rows):
        raise ValueError(f"带框视频解码 {decoded} 帧，记录 {len(rows)} 帧")
    columns = 6
    sheet = np.full((math.ceil(len(samples) / columns) * 320, columns * 180, 3), 245, np.uint8)
    for index, tile in enumerate(samples):
        y, x = (index // columns) * 320, (index % columns) * 180
        sheet[y:y + 320, x:x + 180] = tile
    if not cv2.imwrite(str(output / "contact_sheet.jpg"), sheet):
        raise ValueError("预览保存失败")
    result = {"record_checks_passed": True, "records": len(rows), "output_decoded_frames": decoded,
              "source_time_monotonic": source_time_monotonic,
              "last_source_pos_seconds": previous_source_time,
              "selected_preview_frames": selected_frames,
              "track_id_segments": {key: ranges(value, fps) for key, value in id_frames.items()},
              "no_detection_ranges": ranges(no_detection, fps), "no_track_ranges": ranges(no_track, fps),
              "notes": ["区间由逐帧检测/关联输出计算，不是遮挡标注。",
                        "时间采用帧索引/名义 FPS；ID 连续与否不构成身份正确或恢复成功的证明。"]}
    (output / "review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames", type=int, nargs="*", default=[])
    args = parser.parse_args()
    result = review(args.output, args.frames)
    print(json.dumps(result, ensure_ascii=False, indent=2))
