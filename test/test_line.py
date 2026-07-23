"""
test/test_line.py — 巡线模块测试（MaixCAM 上运行）

用白底黑线测试图片验证 vision/line.py 的检测能力。

运行方式:
  MaixVision 连接 MaixCAM → 运行此文件

测试图片放在 test_images/ 目录下，部署时会一起同步到板子上。
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from maix import image, display, app
from vision import line

# 测试图片列表 — (文件名, 期望结果描述, 期望偏差方向)
TEST_CASES = [
    ("line_straight_center.png",  "直线居中",  "≈ 0"),
    ("line_straight_left.png",    "直线偏左",  "< 0"),
    ("line_straight_right.png",   "直线偏右",  "> 0"),
    ("line_diagonal.png",         "斜线弯道",  "≈ 0"),
    ("line_s_curve.png",          "S 形弯道",  "—"),
    ("line_cross.png",            "十字路口",  "—"),
    ("line_thin.png",             "细线(3px)", "≈ 0"),
    ("line_thick.png",            "粗线(20px)","≈ 0"),
    ("line_broken.png",           "断线",      "—"),
]

TEST_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_images')


def run_test(img_path, description, expected):
    """对一张图片运行巡线检测"""
    print(f"\n{'='*50}")
    print(f"  Test: {description}")
    print(f"  File: {os.path.basename(img_path)}")
    print(f"  Expected deviation: {expected}")

    # 加载图片
    try:
        img = image.open(img_path)
    except Exception as e:
        print(f"  [FAIL] 无法加载图片: {e}")
        return False

    if img is None:
        print(f"  [FAIL] 图片为 None")
        return False

    print(f"  Image: {img.width()}x{img.height()}")

    # 运行巡线
    t0 = time.time()
    result = line.track(img)
    dt = (time.time() - t0) * 1000

    if result is None:
        print(f"  result: None (未检测到线)")
        print(f"  time: {dt:.1f}ms")
        # 对 "断线" 场景，未检测到是可以接受的
        return True

    cx, cy = result
    dev = line.compute_steering(cx, img.width())
    print(f"  result: ({cx}, {cy})  deviation: {dev:.1f}")
    print(f"  time: {dt:.1f}ms")

    # 画调试信息
    line.draw_debug(img, result)
    img.draw_string(5, 5, f"{description}", color=image.Color.from_rgb(0, 255, 0), scale=1.2)
    img.draw_string(5, 22, f"dev:{dev:.0f}", color=image.Color.from_rgb(255, 255, 0), scale=1.2)

    return img, dev


def main():
    print("[test_line] === 巡线模块测试 ===")
    print(f"[test_line] 测试图片目录: {TEST_DIR}")
    print(f"[test_line] 共 {len(TEST_CASES)} 个测试用例")

    disp = display.Display()
    passed = 0
    failed = 0

    for filename, desc, expected in TEST_CASES:
        if app.need_exit():
            break

        img_path = os.path.join(TEST_DIR, filename)

        if not os.path.exists(img_path):
            print(f"\n  [SKIP] 文件不存在: {img_path}")
            continue

        result = run_test(img_path, desc, expected)
        if result is False:
            failed += 1
            continue

        passed += 1
        if isinstance(result, tuple):
            img, dev = result
            disp.show(img)
            time.sleep(1.5)  # 每张图停 1.5 秒方便观察

    print(f"\n{'='*50}")
    print(f"[test_line] Done! passed:{passed} failed:{failed}")
    print(f"[test_line] 检查 MaixVision 画面确认检测效果")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[test_line] user stop")
    except Exception as e:
        print(f"[test_line] error: {e}")
