"""
PC 端三场景巡线验证 — 用 OpenCV 模拟 MaixPy find_blobs。
一次运行覆盖: 中线跟随 / 车道跟随 / 边缘跟随。
"""

import os
import cv2
import numpy as np
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import config

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_images')


def find_black_in_roi(gray, roi):
    """在 ROI 内找黑色 blob，返回 (cx, cy, area, rect) 或 None。"""
    x, y, w, h = roi
    roi_img = gray[y:y+h, x:x+w]
    _, binary = cv2.threshold(roi_img, 128, 255, cv2.THRESH_BINARY_INV)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        return None, binary
    areas = stats[1:, cv2.CC_STAT_AREA]
    best_idx = np.argmax(areas) + 1
    best_area = areas[best_idx - 1]
    cx_r, cy_r = centroids[best_idx]
    bx, by = stats[best_idx, cv2.CC_STAT_LEFT], stats[best_idx, cv2.CC_STAT_TOP]
    bw, bh = stats[best_idx, cv2.CC_STAT_WIDTH], stats[best_idx, cv2.CC_STAT_HEIGHT]
    return (int(cx_r) + x, int(cy_r) + y, int(best_area), (bx + x, by + y, bw, bh)), binary


def find_white_in_roi(gray, roi):
    """在 ROI 内找白色 blob，返回 (cx, cy, area, rect, left, right) 或 None。"""
    x, y, w, h = roi
    roi_img = gray[y:y+h, x:x+w]
    _, binary = cv2.threshold(roi_img, 200, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels <= 1:
        return None, binary
    areas = stats[1:, cv2.CC_STAT_AREA]
    best_idx = np.argmax(areas) + 1
    best_area = areas[best_idx - 1]
    cx_r, cy_r = centroids[best_idx]
    bx, by = stats[best_idx, cv2.CC_STAT_LEFT], stats[best_idx, cv2.CC_STAT_TOP]
    bw, bh = stats[best_idx, cv2.CC_STAT_WIDTH], stats[best_idx, cv2.CC_STAT_HEIGHT]
    left = bx + x
    right = bx + bw + x
    return (int(cx_r) + x, int(cy_r) + y, int(best_area), (bx + x, by + y, bw, bh), left, right), binary


def draw_line_result(img, result, roi):
    """画中线跟随结果"""
    x, y, w, h = roi
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255), 1)
    if result:
        cx, cy, area, rect = result
        rx, ry, rw, rh = rect
        cv2.rectangle(img, (rx, ry), (rw, rh), (0, 255, 0), 2)
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), 2)
        img_cx = img.shape[1] // 2
        cv2.line(img, (img_cx, y), (img_cx, y+h), (0, 255, 0), 1)
        dev = (cx - img_cx) / img_cx * 1000
        cv2.putText(img, f"LINE cx:{cx} dev:{dev:.0f}", (2, 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


def draw_lane_result(img, result, roi):
    """画车道跟随结果"""
    x, y, w, h = roi
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255), 1)
    if result:
        cx, cy, area, rect, left, right = result
        rx, ry, rw, rh = rect
        cv2.rectangle(img, (rx, ry), (rw, rh), (0, 255, 0), 2)
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), 2)
        bot_y = y + h
        cv2.line(img, (left, y), (left, bot_y), (255, 255, 0), 2)
        cv2.line(img, (right, y), (right, bot_y), (255, 255, 0), 2)
        img_cx = img.shape[1] // 2
        cv2.line(img, (img_cx, y), (img_cx, bot_y), (0, 255, 0), 1)
        dev = (cx - img_cx) / img_cx * 1000
        lane_w = right - left
        cv2.putText(img, f"LANE cx:{cx} w:{lane_w} dev:{dev:.0f}", (2, 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


def draw_edge_result(img, result, roi, ref_x):
    """画边缘跟随结果"""
    x, y, w, h = roi
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255), 1)
    if result:
        cx, cy, area, rect = result
        rx, ry, rw, rh = rect
        cv2.rectangle(img, (rx, ry), (rw, rh), (0, 255, 0), 2)
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), 2)
        bot_y = y + h
        cv2.line(img, (ref_x, y), (ref_x, bot_y), (255, 0, 255), 2)
        gap = ref_x - cx
        cv2.putText(img, f"EDGE cx:{cx} ref:{ref_x} gap:{gap}", (2, 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


def main():
    print("=" * 65)
    print("  三场景巡线 PC 验证")
    print("=" * 65)

    # ---- 场景 A: 中线跟随 ----
    print("\n=== 场景 A: 中线跟随 (vision/line.py) ===")
    print(f"    ROI: {config.LINE_ROI}")
    line_files = sorted([f for f in os.listdir(TEST_DIR)
                         if f.startswith('line_') and not f.endswith('_result.png') and not f.endswith('_binary.png')])
    for fname in line_files:
        fpath = os.path.join(TEST_DIR, fname)
        gray = cv2.imread(fpath, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            print(f"  [SKIP] {fname}")
            continue
        result, _ = find_black_in_roi(gray, config.LINE_ROI)
        if result:
            cx, cy, area, rect = result
            dev = (cx - gray.shape[1]/2) / (gray.shape[1]/2) * 1000
            print(f"  {fname:32s} → cx={cx:3d} area={area:4d} dev={dev:+6.0f}")
        else:
            print(f"  {fname:32s} → NO LINE")
        img_color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        draw_line_result(img_color, result, config.LINE_ROI)
        cv2.imwrite(os.path.join(TEST_DIR, fname.replace('.png', '_line_result.png')), img_color)

    # ---- 场景 B: 车道跟随 ----
    print("\n=== 场景 B: 车道跟随 (vision/lane.py) ===")
    print(f"    ROI: {config.LANE_ROI}")
    lane_files = sorted([f for f in os.listdir(TEST_DIR) if f.startswith('lane_')])
    for fname in lane_files:
        fpath = os.path.join(TEST_DIR, fname)
        gray = cv2.imread(fpath, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            print(f"  [SKIP] {fname}")
            continue
        result, _ = find_white_in_roi(gray, config.LANE_ROI)
        if result:
            cx, cy, area, rect, left, right = result
            dev = (cx - gray.shape[1]/2) / (gray.shape[1]/2) * 1000
            lane_w = right - left
            print(f"  {fname:32s} → cx={cx:3d} w={lane_w:3d} L={left:3d} R={right:3d} dev={dev:+6.0f}")
        else:
            print(f"  {fname:32s} → NO LANE")
        img_color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        draw_lane_result(img_color, result, config.LANE_ROI)
        cv2.imwrite(os.path.join(TEST_DIR, fname.replace('.png', '_lane_result.png')), img_color)

    # ---- 场景 C: 边缘跟随 ----
    print("\n=== 场景 C: 边缘跟随 (vision/edge.py) ===")
    print(f"    ROI: {config.EDGE_ROI}  side: {config.EDGE_SIDE}  ref_x: {config.EDGE_REF_X}")
    edge_files = sorted([f for f in os.listdir(TEST_DIR) if f.startswith('edge_')])
    for fname in edge_files:
        fpath = os.path.join(TEST_DIR, fname)
        gray = cv2.imread(fpath, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            print(f"  [SKIP] {fname}")
            continue
        result, _ = find_black_in_roi(gray, config.EDGE_ROI)
        if result:
            cx, cy, area, rect = result
            gap = config.EDGE_REF_X - cx
            print(f"  {fname:32s} → cx={cx:3d} ref={config.EDGE_REF_X} gap={gap:+4d}")
        else:
            print(f"  {fname:32s} → NO EDGE")
        img_color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        draw_edge_result(img_color, result, config.EDGE_ROI, config.EDGE_REF_X)
        cv2.imwrite(os.path.join(TEST_DIR, fname.replace('.png', '_edge_result.png')), img_color)

    print("\n" + "=" * 65)
    print("  验证完成！结果图片已保存到 test_images/")
    print("=" * 65)


if __name__ == "__main__":
    main()
