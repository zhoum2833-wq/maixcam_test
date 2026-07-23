"""
vision/rectangle.py — 矩形检测与中心定位 (MaixPy v4.12+)

纯算法层：接收图像 → 检测矩形 → 计算交叉点 → 返回偏差。
不直接访问任何硬件。

API: img.find_rects() (maix.image 内置)
"""

import math
from maix import image
import config


def _find_max_rect(rects):
    """返回面积最大的矩形"""
    if not rects:
        return None
    max_area, max_rect = 0, None
    for r in rects:
        area = r[2] * r[3]  # w * h
        if area > max_area:
            max_area, max_rect = area, r
    return max_rect


def _format_coord(val):
    return f"{val:+04d}"


def detect(img, threshold=None):
    """
    检测图像中的矩形，计算中心交叉点偏差。

    参数:
        img:       maix.image.Image 对象
        threshold: find_rects 阈值（默认使用 config.RECT_THRESHOLD）

    返回:
        dict {'center', 'offset', 'corners', 'area', 'uart'} 或 None
    """
    if threshold is None:
        threshold = config.RECT_THRESHOLD

    # 使用 maix.image 内置的 find_rects
    try:
        rects = img.find_rects(threshold=threshold)
    except Exception:
        return None

    if not rects:
        return None

    # 找最大矩形
    max_rect = _find_max_rect(rects)
    if max_rect is None:
        return None

    x, y, w, h = max_rect[0], max_rect[1], max_rect[2], max_rect[3]
    area = w * h

    # 面积过滤
    img_area = img.width() * img.height()
    if area < config.RECT_AREA_THRESH or area < img_area * 0.005:
        return None

    # 长宽比过滤（太细长的不是目标矩形）
    aspect = max(w, h) / (min(w, h) + 1)
    if aspect > config.RECT_ASPECT_MAX:
        return None

    # 获取角点（左上 → 右上 → 右下 → 左下）
    try:
        corners_raw = max_rect.corners()
        corners = [(int(c[0]), int(c[1])) for c in corners_raw]
    except Exception:
        # 降级: 用外接框的四角
        corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

    # 中心点（从外接框计算）
    center_x = x + w // 2
    center_y = y + h // 2

    # 计算偏差（图像中心为参考点）
    dx = config.IMG_CENTER_X - center_x
    dy = config.IMG_CENTER_Y - center_y

    return {
        'center':  (center_x, center_y),
        'offset':  (dx, dy),
        'corners': corners,
        'area':    area,
        'uart':    f"[{_format_coord(dx)}{_format_coord(dy)}*]",
        'rect':    (x, y, w, h),
    }


def draw_debug(img, result):
    """在图像上绘制检测结果（调试用）"""
    if result is None:
        return

    corners = result['corners']
    center = result['center']
    x, y, w, h = result.get('rect', (0, 0, 0, 0))

    green = image.Color.from_rgb(0, 255, 0)
    red   = image.Color.from_rgb(255, 0, 0)
    blue  = image.Color.from_rgb(0, 0, 255)
    yellow = image.Color.from_rgb(255, 255, 0)

    # 外接框
    img.draw_rect(x, y, w, h, color=green, thickness=2)

    # 角点
    for c in corners:
        img.draw_circle(c[0], c[1], 2, color=blue, thickness=3)

    # 交叉对角线
    if len(corners) == 4:
        img.draw_line(corners[0][0], corners[0][1],
                       corners[2][0], corners[2][1],
                       color=yellow, thickness=1)
        img.draw_line(corners[1][0], corners[1][1],
                       corners[3][0], corners[3][1],
                       color=yellow, thickness=1)

    # 中心点
    img.draw_circle(center[0], center[1], 3, color=red, thickness=4)

    # 坐标信息
    img.draw_string(0, 0,
                     f"({center[0]},{center[1]}) d=({result['offset'][0]},{result['offset'][1]})",
                     color=yellow, scale=1.5)
