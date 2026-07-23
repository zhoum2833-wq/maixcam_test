"""
用逼真测试图片验证三场景巡线模块。
"""

import os, sys, cv2, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import config

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_images')


def find_black_in_roi(gray, roi, area_min=80, area_max=50000):
    """模拟 line.py / edge.py 的 find_blobs 行为"""
    x, y, w, h = roi
    roi_img = gray[y:y+h, x:x+w]
    _, binary = cv2.threshold(roi_img, 128, 255, cv2.THRESH_BINARY_INV)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)
    if n <= 1:
        return None
    best_i = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
    area = stats[best_i, cv2.CC_STAT_AREA]
    if area < area_min or area > area_max:
        return None
    cx_r, cy_r = centroids[best_i]
    bx, by = stats[best_i, cv2.CC_STAT_LEFT], stats[best_i, cv2.CC_STAT_TOP]
    bw, bh = stats[best_i, cv2.CC_STAT_WIDTH], stats[best_i, cv2.CC_STAT_HEIGHT]
    return int(cx_r)+x, int(cy_r)+y, int(area), (bx+x, by+y, bw, bh)


def find_white_in_roi(gray, roi, area_min=400, area_max=80000):
    """模拟 lane.py 的 find_blobs 行为"""
    x, y, w, h = roi
    roi_img = gray[y:y+h, x:x+w]
    _, binary = cv2.threshold(roi_img, 200, 255, cv2.THRESH_BINARY)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)
    if n <= 1:
        return None
    best_i = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
    area = stats[best_i, cv2.CC_STAT_AREA]
    if area < area_min or area > area_max:
        return None
    cx_r, cy_r = centroids[best_i]
    bx, by = stats[best_i, cv2.CC_STAT_LEFT], stats[best_i, cv2.CC_STAT_TOP]
    bw, bh = stats[best_i, cv2.CC_STAT_WIDTH], stats[best_i, cv2.CC_STAT_HEIGHT]
    return int(cx_r)+x, int(cy_r)+y, int(area), (bx+x, by+y, bw, bh), bx+x, bx+bw+x


def test_scene(label, files, roi, finder, extra=""):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  ROI: {roi}  {extra}")
    print(f"{'='*60}")
    ok = 0
    fail = 0
    for fname in sorted(files):
        fpath = os.path.join(TEST_DIR, fname)
        gray = cv2.imread(fpath, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            continue
        result = finder(gray, roi)
        if result:
            ok += 1
            if len(result) == 4:
                cx, cy, area, rect = result
                dev = (cx - W//2) / (W//2) * 1000
                print(f"  {fname:38s} cx={cx:3d} area={area:5d} dev={dev:+6.0f}")
            elif len(result) == 6:
                cx, cy, area, rect, left, right = result
                dev = (cx - W//2) / (W//2) * 1000
                w_lane = right - left
                print(f"  {fname:38s} cx={cx:3d} w={w_lane:3d} L={left:3d} R={right:3d} dev={dev:+6.0f}")
        else:
            fail += 1
            print(f"  {fname:38s} [FAIL] NOT FOUND")
    print(f"  ---> 通过:{ok}  未检出:{fail}")
    return ok, fail


W, H = 320, 240

# 场景 A: 中线跟随
line_files = [f for f in os.listdir(TEST_DIR) if f.startswith('real_line_')]
test_scene("场景 A: 中线跟随 (vision/line.py)", line_files, config.LINE_ROI, find_black_in_roi)

# 场景 B: 车道跟随
lane_files = [f for f in os.listdir(TEST_DIR) if f.startswith('real_lane_')]
test_scene("场景 B: 车道跟随 (vision/lane.py)", lane_files, config.LANE_ROI, find_white_in_roi)

# 场景 C: 边缘跟随
edge_files = [f for f in os.listdir(TEST_DIR) if f.startswith('real_edge_')]
test_scene("场景 C: 边缘跟随 (vision/edge.py)  side=left ref=40",
          edge_files, config.EDGE_ROI, find_black_in_roi,
          extra=f"ref_x={config.EDGE_REF_X}")

print(f"\n{'='*60}")
print("  全部验证完成！")
print(f"{'='*60}")
