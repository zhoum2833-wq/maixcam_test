"""
PC 端巡线验证 — 用 OpenCV 模拟 MaixPy find_blobs 行为。

在 PC 上运行，验证生成的测试图片是否合理，以及检测逻辑是否正确。
运行: python tools/verify_line_on_pc.py
"""

import os
import cv2
import numpy as np
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 复用 config 中的 ROI 参数
import config

TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_images')
ROI = config.LINE_ROI  # (x, y, w, h)


def find_black_line(img_gray):
    """
    模拟 find_blobs 行为: 在 ROI 内找黑色区域，返回最大 blob 的质心。
    """
    x, y, w, h = ROI
    roi = img_gray[y:y+h, x:x+w]

    # 二值化：像素 < 128 视为黑线
    _, binary = cv2.threshold(roi, 128, 255, cv2.THRESH_BINARY_INV)

    # 找连通域
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    if num_labels <= 1:
        return None, roi, binary

    # 去掉背景 (label 0)，找面积最大的
    areas = stats[1:, cv2.CC_STAT_AREA]
    best_idx = np.argmax(areas) + 1
    best_area = areas[best_idx - 1]

    if best_area < config.LINE_AREA_MIN:
        return None, roi, binary

    cx, cy = centroids[best_idx]
    # 换算到原图坐标
    cx_global = int(cx) + x
    cy_global = int(cy) + y

    return (cx_global, cy_global), roi, binary


def draw_result(img_color, result):
    """在彩色图上画检测结果"""
    x, y, w, h = ROI

    # ROI 框 (黄)
    cv2.rectangle(img_color, (x, y), (x + w, y + h), (0, 255, 255), 1)

    if result is None:
        cv2.putText(img_color, "NO LINE", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return

    cx, cy = result

    # 线中心点 (红)
    cv2.circle(img_color, (cx, cy), 5, (0, 0, 255), 2)
    cv2.line(img_color, (cx - 10, cy), (cx + 10, cy), (0, 0, 255), 2)
    cv2.line(img_color, (cx, cy - 10), (cx, cy + 10), (0, 0, 255), 2)

    # 图像中心参考线 (绿)
    img_cx = img_color.shape[1] // 2
    cv2.line(img_color, (img_cx, cy - 15), (img_cx, cy + 15), (0, 255, 0), 1)

    # 偏差值
    dev = (cx - img_cx) / img_cx * 1000.0
    cv2.putText(img_color, f"cx={cx} dev={dev:.0f}", (cx + 15, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


def main():
    print(f"[verify_line] test_images dir: {TEST_DIR}")
    print(f"[verify_line] ROI: {ROI}")

    files = sorted([f for f in os.listdir(TEST_DIR) if f.endswith('.png')])

    for fname in files:
        fpath = os.path.join(TEST_DIR, fname)
        img = cv2.imread(fpath)
        if img is None:
            print(f"  [SKIP] cannot read: {fname}")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        result, roi_binary, binary = find_black_line(gray)

        if result:
            cx, cy = result
            dev = (cx - gray.shape[1] / 2) / (gray.shape[1] / 2) * 1000.0
            print(f"  {fname:30s} → line at ({cx:3d},{cy:3d})  dev={dev:+.0f}")
        else:
            print(f"  {fname:30s} → NO LINE DETECTED")

        # 画结果
        result_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        draw_result(result_img, result)

        # 保存结果图片
        out_name = fname.replace('.png', '_result.png')
        out_path = os.path.join(TEST_DIR, out_name)
        cv2.imwrite(out_path, result_img)
        bin_name = fname.replace('.png', '_binary.png')
        bin_path = os.path.join(TEST_DIR, bin_name)
        cv2.imwrite(bin_path, binary)
    print("[verify_line] Done!")


if __name__ == "__main__":
    main()
