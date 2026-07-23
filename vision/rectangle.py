"""
vision/rectangle.py — 矩形检测与中心定位 (find_blobs 路线)

管线: find_blobs(黑, merge) → 取顶点 → 角度检查 → 框内白块面积比 → 输出

性能: find_blobs 在 MaixCAM 上 320×240 约 7ms, 适合高频跟踪。
"""

import math
from maix import image as mimg
import config


# ---- 诊断计数器 ----
_diag_n = 0

# ============================================================
#  检测参数
# ============================================================
BLACK_THRESH  = getattr(config, 'RECT_BLACK_THRESH', [0, 35, -25, 25, -25, 25])
WHITE_THRESH  = getattr(config, 'RECT_WHITE_THRESH', [70, 100, -25, 25, -25, 25])
AREA_MIN      = getattr(config, 'RECT_AREA_MIN', 500)
AREA_MAX      = getattr(config, 'RECT_AREA_MAX', 55000)
WHITE_RATIO   = getattr(config, 'RECT_WHITE_RATIO', 0.70)   # 白面积/框面积 > 此值
ASPECT_MIN    = getattr(config, 'RECT_ASPECT_MIN', 0.55)
ASPECT_MAX    = getattr(config, 'RECT_ASPECT_MAX', 1.8)
MERGE_MARGIN  = getattr(config, 'RECT_MERGE_MARGIN', 15)
ANGLE_TOL     = 30               # 角度宽松度 (±30°)


def compute_angle(p1, p2, p3):
    """p2 处的内角 (度)"""
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = math.sqrt(v1[0]**2 + v1[1]**2) + 1e-8
    n2 = math.sqrt(v2[0]**2 + v2[1]**2) + 1e-8
    cos_a = max(-1, min(1, dot / (n1 * n2)))
    return math.degrees(math.acos(cos_a))


def intersection(p1, p2, p3, p4):
    """线段 p1-p2 与 p3-p4 的交点"""
    x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-8:
        return None
    px = ((x1*y2 - y1*x2) * (x3 - x4) - (x1 - x2) * (x3*y4 - y3*x4)) / d
    py = ((x1*y2 - y1*x2) * (y3 - y4) - (y1 - y2) * (x3*y4 - y3*x4)) / d
    return (int(px), int(py))


def _format_coord(val):
    return f"{val:+04d}"


def detect(img):
    """
    find_blobs 矩形检测 — 白纸法
    """
    global _diag_n
    import time as _time
    w, h = img.width(), img.height()
    img_cx, img_cy = w // 2, h // 2

    _diag_n += 1
    t0 = _time.time()

    # 1. 找白色块
    whites = img.find_blobs(
        [WHITE_THRESH],
        area_threshold=AREA_MIN,
        pixels_threshold=AREA_MIN,
        merge=True,
        margin=MERGE_MARGIN,
    )
    t1 = _time.time()

    if not whites:
        if _diag_n % 30 == 0:
            print(f"[RECT] 无白色blob")
        return None

    # 选最大
    best = max(whites, key=lambda b: b.area())
    area_best = best.area()
    if not (AREA_MIN < area_best < AREA_MAX):
        if _diag_n % 30 == 0:
            print(f"[RECT] 面积{area_best} 超范围")
        return None

    bx, by, bw, bh = best.x(), best.y(), best.w(), best.h()
    t2 = _time.time()

    # 宽高比
    aspect = bw / (bh + 0.01)
    if not (ASPECT_MIN <= aspect <= ASPECT_MAX):
        return None

    # 取顶点
    try:
        corners_raw = best.mini_corners()
        if len(corners_raw) < 4:
            return None
        pts = [(int(c[0]), int(c[1])) for c in corners_raw[:4]]
    except Exception:
        return None
    t3 = _time.time()

    # 角度检查
    for i in range(4):
        angle = compute_angle(pts[(i - 1) % 4], pts[i], pts[(i + 1) % 4])
        if not (90 - ANGLE_TOL <= angle <= 90 + ANGLE_TOL):
            return None

    # 填充率
    fill_ratio = area_best / (bw * bh) if bw * bh > 0 else 0
    t4 = _time.time()

    # 中心
    center = intersection(pts[0], pts[2], pts[1], pts[3])
    if center is None:
        center = (int(best.cx()), int(best.cy()))

    dx = img_cx - center[0]
    dy = img_cy - center[1]

    if _diag_n % 30 == 0:
        dt1 = (t1 - t0) * 1000
        dt2 = (t2 - t1) * 1000
        dt3 = (t3 - t2) * 1000
        dt4 = (t4 - t3) * 1000
        dt_total = (t4 - t0) * 1000
        print(f"[RECT] detect:{dt_total:.0f}ms | blob:{dt1:.0f} filter:{dt2:.0f} corners:{dt3:.0f} angle:{dt4:.0f}")

    return {
        'center':  center,
        'offset':  (dx, dy),
        'corners': pts,
        'area':    area_best,
        'rect':    (bx, by, bw, bh),
    }


def draw_debug(img, result):
    """在图像上绘制检测结果"""
    if result is None:
        return

    green  = mimg.Color.from_rgb(0, 255, 0)
    red    = mimg.Color.from_rgb(255, 0, 0)
    blue   = mimg.Color.from_rgb(0, 0, 255)
    yellow = mimg.Color.from_rgb(255, 255, 0)

    corners = result['corners']
    center  = result['center']
    x, y, w, h = result.get('rect', (0, 0, 0, 0))

    img.draw_rect(x, y, w, h, color=green, thickness=2)

    for i in range(4):
        j = (i + 1) % 4
        img.draw_line(corners[i][0], corners[i][1],
                       corners[j][0], corners[j][1],
                       color=yellow, thickness=1)
        img.draw_circle(corners[i][0], corners[i][1], 2,
                         color=blue, thickness=3)

    if len(corners) == 4:
        img.draw_line(corners[0][0], corners[0][1],
                       corners[2][0], corners[2][1],
                       color=yellow, thickness=1)
        img.draw_line(corners[1][0], corners[1][1],
                       corners[3][0], corners[3][1],
                       color=yellow, thickness=1)

    img.draw_circle(center[0], center[1], 3, color=red, thickness=4)
    img.draw_string(0, 0, f"({center[0]},{center[1]})", color=yellow, scale=1.5)
