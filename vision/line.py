"""
vision/line.py — 巡线算法

纯算法层：接收图像 → ROI 中找黑线 → 质心 → 偏差。
不直接访问任何硬件（摄像头、串口）。

核心思路:
  1. 裁剪 ROI 区域（图像底部，线离车最近）
  2. find_blobs 找黑色 blob（merge=False 防污渍粘连）
  3. 面积 + 高宽比过滤，取最佳 blob
  4. 质心 = 线位置 → 计算转向偏差
"""

from maix import image as mimg
import config

# ---- 黑线检测阈值 (LAB) ----
LINE_BLACK_THRESH = getattr(config, 'LINE_BLACK_THRESH', [0, 45, -30, 30, -30, 30])
LINE_AREA_MIN     = getattr(config, 'LINE_AREA_MIN', 80)
LINE_AREA_MAX     = getattr(config, 'LINE_AREA_MAX', 30000)
LINE_ASPECT_MIN   = getattr(config, 'LINE_ASPECT_MIN', 1.5)
LINE_MIN_HEIGHT   = getattr(config, 'LINE_MIN_HEIGHT', 20)


def track(img):
    """
    在图像 ROI 中寻找黑线，返回线中心坐标。

    参数:
        img: maix.image.Image

    返回:
        dict:
            'cx':     线中心 x 坐标（原图坐标）
            'cy':     线中心 y 坐标（原图坐标）
            'area':   线 blob 面积
            'rect':   (x, y, w, h) blob 外接矩形
        None: 未检测到线
    """
    rx, ry, rw, rh = config.LINE_ROI

    # 1. 裁剪 ROI
    roi = img.crop(rx, ry, rw, rh)

    # 2. 找黑色 blob — merge=False 防止线与污渍粘连
    blobs = roi.find_blobs(
        [LINE_BLACK_THRESH],
        area_threshold=LINE_AREA_MIN,
        pixels_threshold=LINE_AREA_MIN,
        merge=False,
    )

    if not blobs:
        return None

    # 3. 面积 + 高宽比评分，选出最像"线"的 blob
    best_score = 0.0
    best_blob = None
    for b in blobs:
        bw = float(b.w())
        bh = float(b.h())
        area = float(b.area())

        if area < LINE_AREA_MIN or area > LINE_AREA_MAX:
            continue
        if bh < LINE_MIN_HEIGHT:
            continue

        aspect = bh / (bw + 1.0)
        if aspect < LINE_ASPECT_MIN:
            continue

        # 评分：面积 × 高宽比
        score = area * aspect
        if score > best_score:
            best_score = score
            best_blob = b

    if best_blob is None:
        return None

    # 4. 质心坐标（ROI → 原图坐标）
    cx = int(best_blob.cx()) + rx
    cy = int(best_blob.cy()) + ry
    x, y, w, h = best_blob.x(), best_blob.y(), best_blob.w(), best_blob.h()

    return {
        'cx':    cx,
        'cy':    cy,
        'area':  int(best_blob.area()),
        'rect':  (x + rx, y + ry, w, h),
    }


def compute_steering(result: dict, img_w: int) -> float:
    """
    从 track() 结果计算转向偏差量。

    返回:
        -1000 ~ +1000  （0 = 线在正中，负 = 偏左，正 = 偏右）
    """
    if result is None:
        return 0.0
    mid = img_w / 2.0
    return (result['cx'] - mid) / mid * 1000.0


def draw_debug(img, result):
    """
    在图像上绘制巡线调试信息。
    """
    if result is None:
        return

    cx, cy = result['cx'], result['cy']
    x, y, w, h = result['rect']

    green   = mimg.Color.from_rgb(0, 255, 0)
    red     = mimg.Color.from_rgb(255, 0, 0)
    yellow  = mimg.Color.from_rgb(255, 255, 0)

    # ROI 框
    rx, ry, rw, rh = config.LINE_ROI
    img.draw_rect(rx, ry, rw, rh, color=yellow, thickness=1)

    # blob 外接矩形
    img.draw_rect(x, y, w, h, color=green, thickness=2)

    # 线中心点 + 十字
    img.draw_circle(cx, cy, 5, color=red, thickness=3)
    img.draw_line(cx - 8, cy, cx + 8, cy, color=red, thickness=2)
    img.draw_line(cx, cy - 8, cx, cy + 8, color=red, thickness=2)

    # 图像中心参考线
    img_cx = img.width() // 2
    img.draw_line(img_cx, ry, img_cx, ry + rh, color=green, thickness=1)

    # 偏差值
    dev = compute_steering(result, img.width())
    img.draw_rect(0, 0, img.width(), 18, mimg.Color.from_rgb(30, 30, 30), -1)
    img.draw_string(2, 2, f"LINE cx:{cx} dev:{dev:.0f} area:{result['area']}",
                    color=green, scale=1.2)
