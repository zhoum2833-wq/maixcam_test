"""
vision/rectangle.py — 矩形检测与中心定位 (MaixPy v4.12+)

纯算法层：接收图像 → 检测矩形 → 计算交叉点 → 返回偏差。
不直接访问任何硬件。
"""

import math
import config


def _find_max_rect(rects):
    if not rects:
        return None
    max_size, max_rect = 0, None
    for r in rects:
        area = r[2] * r[3]
        if area > max_size:
            max_size, max_rect = area, r
    return max_rect


def _are_parallel(t1, t2, tol=30):
    d = abs(t1 - t2)
    if d > 180:
        d -= 180
    return math.isclose(d, 0, abs_tol=tol) or math.isclose(d, 180, abs_tol=tol)


def _are_vertical(t1, t2, tol=30):
    d = abs(t1 - t2)
    if d > 180:
        d -= 180
    return math.isclose(d, 90, abs_tol=tol)


def _find_intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    def det(A, B):
        return A[0] * B[1] - A[1] * B[0]
    AB = (x2 - x1, y2 - y1)
    CD = (x4 - x3, y4 - y3)
    d = det(AB, CD)
    if d == 0:
        return None
    AC = (x3 - x1, y3 - y1)
    t = det(AC, CD) / d
    return int(x1 + t * AB[0]), int(y1 + t * AB[1])


def _format_coord(val):
    return f"{val:+04d}"


def detect(img, image_shape=None):
    """
    检测图像中的矩形，计算中心交叉点偏差。

    返回:
        dict {'center', 'offset', 'corners', 'area', 'uart'} 或 None
    """
    if image_shape is None:
        image_shape = [config.CAM_HEIGHT, config.CAM_WIDTH]

    # 获取 numpy 引用 (MaixPy v4: to_numpy_ref or tobytes)
    try:
        img_np = img.to_numpy_ref()
    except AttributeError:
        try:
            img_np = img.tobytes()
        except Exception:
            return None

    # cv_lite 矩形检测
    try:
        import cv_lite
        rects = cv_lite.rgb888_find_rectangles_with_corners(
            image_shape, img_np,
            config.RECT_CANNY_LO, config.RECT_CANNY_HI,
            config.RECT_EPSILON, config.RECT_AREA_MIN,
            config.RECT_MAX_ANGLE, config.RECT_GAUSS_SIZE)
    except Exception:
        return None

    if not rects:
        return None

    max_rect = _find_max_rect(rects)
    if max_rect is None:
        return None

    corners = [(max_rect[2 * i + 4], max_rect[2 * i + 5]) for i in range(4)]

    def dist(i, j):
        return math.sqrt((corners[j][0] - corners[i][0]) ** 2 +
                         (corners[j][1] - corners[i][1]) ** 2)

    len_ab, len_cd = dist(0, 1), dist(2, 3)
    len_ad, len_bc = dist(0, 3), dist(1, 2)
    area = max_rect[2] * max_rect[3]

    err_h = abs(len_ab - len_cd)
    err_v = abs(len_ad - len_bc)
    ok = (area > config.RECT_AREA_THRESH and
          err_h < config.RECT_LEN_THRESH and
          err_v < config.RECT_LEN_THRESH and
          all(d > config.RECT_MIN_EDGE for d in [len_ab, len_cd, len_ad, len_bc]))
    if not ok:
        return None

    theta_ab = math.degrees(math.atan2(corners[1][1] - corners[0][1],
                                       corners[1][0] - corners[0][0]))
    theta_cd = math.degrees(math.atan2(corners[3][1] - corners[2][1],
                                       corners[3][0] - corners[2][0]))
    theta_ad = math.degrees(math.atan2(corners[3][1] - corners[0][1],
                                       corners[3][0] - corners[0][0]))
    theta_bc = math.degrees(math.atan2(corners[2][1] - corners[1][1],
                                       corners[2][0] - corners[1][0]))

    if not (_are_parallel(theta_ab, theta_cd) and
            _are_parallel(theta_ad, theta_bc) and
            _are_vertical(theta_ab, theta_ad)):
        return None

    center = _find_intersection(corners[0][0], corners[0][1],
                                 corners[2][0], corners[2][1],
                                 corners[1][0], corners[1][1],
                                 corners[3][0], corners[3][1])
    if center is None:
        return None

    dx = config.IMG_CENTER_X - center[0]
    dy = config.IMG_CENTER_Y - center[1]

    return {
        'center':  center,
        'offset':  (dx, dy),
        'corners': corners,
        'area':    area,
        'uart':    f"[{_format_coord(dx)}{_format_coord(dy)}*]",
    }


def draw_debug(img, result):
    """在图像上绘制检测结果（调试用）"""
    if result is None:
        return
    corners = result['corners']
    center = result['center']

    for i in range(4):
        j = (i + 1) % 4
        img.draw_line(corners[i][0], corners[i][1],
                       corners[j][0], corners[j][1],
                       color=(0, 255, 0), thickness=3)
        img.draw_circle(corners[i][0], corners[i][1], 2,
                         color=(0, 0, 255), thickness=3)

    img.draw_circle(center[0], center[1], 3,
                     color=(255, 0, 0), thickness=4)
    img.draw_string(0, 0,
                     f"(x={center[0]},y={center[1]})",
                     color=(255, 255, 0), scale=2)
