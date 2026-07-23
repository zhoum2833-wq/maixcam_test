"""
vision/rectangle.py — 矩形检测与中心定位 (find_blobs 白纸法, 极简)

管线: find_blobs(白) → 面积+宽高比过滤 → blob质心 → 输出
"""

from maix import image as mimg
import config


# ============================================================
#  检测参数
# ============================================================
WHITE_THRESH  = getattr(config, 'RECT_WHITE_THRESH', [60, 100, -30, 30, -30, 30])
AREA_MIN      = getattr(config, 'RECT_AREA_MIN', 500)
AREA_MAX      = getattr(config, 'RECT_AREA_MAX', 55000)
ASPECT_MIN    = getattr(config, 'RECT_ASPECT_MIN', 0.55)
ASPECT_MAX    = getattr(config, 'RECT_ASPECT_MAX', 1.8)
MERGE_MARGIN  = getattr(config, 'RECT_MERGE_MARGIN', 15)


def _format_coord(val):
    return f"{val:+04d}"


def detect(img):
    """
    白纸法: find_blobs → 质心 = 矩形中心
    """
    w, h = img.width(), img.height()
    img_cx, img_cy = w // 2, h // 2

    # 找白色块
    whites = img.find_blobs(
        [WHITE_THRESH],
        area_threshold=AREA_MIN,
        pixels_threshold=AREA_MIN,
        merge=True,
        margin=MERGE_MARGIN,
    )
    if not whites:
        return None

    best = max(whites, key=lambda b: b.area())
    area = best.area()
    if not (AREA_MIN < area < AREA_MAX):
        return None

    bw, bh = best.w(), best.h()
    aspect = bw / (bh + 0.01)
    if not (ASPECT_MIN <= aspect <= ASPECT_MAX):
        return None

    # 质心 = 矩形几何中心
    center = (int(best.cx()), int(best.cy()))
    dx = img_cx - center[0]
    dy = img_cy - center[1]

    return {
        'center':  center,
        'offset':  (dx, dy),
        'area':    area,
        'rect':    (best.x(), best.y(), bw, bh),
        'corners': [(best.x(), best.y()),
                     (best.x() + bw, best.y()),
                     (best.x() + bw, best.y() + bh),
                     (best.x(), best.y() + bh)],
    }


def draw_debug(img, result):
    """在图像上绘制检测结果（调试用）"""
    if result is None:
        return

    green  = mimg.Color.from_rgb(0, 255, 0)
    red    = mimg.Color.from_rgb(255, 0, 0)
    yellow = mimg.Color.from_rgb(255, 255, 0)

    center = result['center']
    x, y, w, h = result.get('rect', (0, 0, 0, 0))

    img.draw_rect(x, y, w, h, color=green, thickness=2)
    img.draw_circle(center[0], center[1], 4, color=red, thickness=4)

    # 十字准星
    img.draw_line(center[0] - 10, center[1], center[0] + 10, center[1],
                   color=red, thickness=2)
    img.draw_line(center[0], center[1] - 10, center[0], center[1] + 10,
                   color=red, thickness=2)

    img.draw_string(0, 0, f"({center[0]},{center[1]})", color=yellow, scale=1.5)
