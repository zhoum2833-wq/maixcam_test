"""
vision/rectangle.py — 矩形检测与中心定位

纯算法层：接收图像 → 检测矩形 → 计算交叉点 → 返回偏差。
不直接访问任何硬件。

参考:
  - 25E题 矩形8.3.1.py: cv_lite 矩形检测 + 对角线交叉点 + UART 格式
  - 开源项目 Algorithm/CenterGet.py: 轮廓评分逻辑
"""

import math
import config


def _find_max_rect(rects):
    """从矩形列表中找面积最大的"""
    if not rects:
        return None
    max_size = 0
    max_rect = None
    for r in rects:
        area = r[2] * r[3]
        if area > max_size:
            max_size = area
            max_rect = r
    return max_rect


def _are_parallel(theta1_deg, theta2_deg, tolerance=30):
    """判断两条线段是否平行 (角度差 ≈ 0° 或 180°)"""
    diff = abs(theta1_deg - theta2_deg)
    if diff > 180:
        diff -= 180
    return math.isclose(diff, 0, abs_tol=tolerance) or \
           math.isclose(diff, 180, abs_tol=tolerance)


def _are_vertical(theta1_deg, theta2_deg, tolerance=30):
    """判断两条线段是否垂直 (角度差 ≈ 90°)"""
    diff = abs(theta1_deg - theta2_deg)
    if diff > 180:
        diff -= 180
    return math.isclose(diff, 90, abs_tol=tolerance)


def _find_intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    """计算两条线段的交点（直线 AB × 直线 CD）"""
    def det(A, B):
        return A[0] * B[1] - A[1] * B[0]

    AB = (x2 - x1, y2 - y1)
    CD = (x4 - x3, y4 - y3)
    denom = det(AB, CD)

    if denom == 0:
        return None  # 平行

    AC = (x3 - x1, y3 - y1)
    t = det(AC, CD) / denom
    ix = x1 + t * AB[0]
    iy = y1 + t * AB[1]
    return int(ix), int(iy)


def _format_coord(val):
    """格式化为 ±000 的 4 位带符号字符串，如 -123→"-123", 12→"+012" """
    return f"{val:+04d}"


def detect(img, image_shape: list = None):
    """
    检测图像中的矩形，计算中心交叉点偏差。

    参数:
        img:         传感器 snapshot 对象
        image_shape: [height, width], 默认 [320, 480]

    返回:
        dict 或 None:
        {
            'center':      (cx, cy),        # 矩形对角线交叉点坐标
            'offset':      (dx, dy),        # 相对于图像中心的偏差
            'corners':     [(x1,y1), ...],  # 四个顶点坐标
            'area':        float,           # 矩形面积
            'uart':        str,             # 格式化串口输出: "[+012-034*]"
        }
        未检测到 → None
    """
    if image_shape is None:
        image_shape = [config.CAM_HEIGHT, config.CAM_WIDTH]

    # 1. 获取 numpy 引用
    try:
        img_np = img.to_numpy_ref()
    except Exception:
        return None

    # 2. cv_lite 矩形检测
    try:
        import cv_lite
        rects = cv_lite.rgb888_find_rectangles_with_corners(
            image_shape, img_np,
            config.RECT_CANNY_LO, config.RECT_CANNY_HI,
            config.RECT_EPSILON,
            config.RECT_AREA_MIN,
            config.RECT_MAX_ANGLE,
            config.RECT_GAUSS_SIZE
        )
    except Exception:
        return None

    if not rects:
        return None

    # 3. 取最大矩形
    max_rect = _find_max_rect(rects)
    if max_rect is None:
        return None

    # 4. 提取四个顶点坐标
    # rects 格式: [x, y, w, h, x0, y0, x1, y1, x2, y2, x3, y3]
    corners = []
    for i in range(4):
        cx = max_rect[2 * i + 4]
        cy = max_rect[2 * i + 5]
        corners.append((cx, cy))

    # 5. 计算边长
    def dist(i, j):
        return math.sqrt((corners[j][0] - corners[i][0]) ** 2 +
                         (corners[j][1] - corners[i][1]) ** 2)

    len_ab = dist(0, 1)  # 上边
    len_cd = dist(2, 3)  # 下边
    len_ad = dist(0, 3)  # 左边
    len_bc = dist(1, 2)  # 右边

    area = max_rect[2] * max_rect[3]

    # 6. 矩形验证
    # 对边差值
    err_h = abs(len_ab - len_cd)
    err_v = abs(len_ad - len_bc)

    if not (area > config.RECT_AREA_THRESH and
            err_h < config.RECT_LEN_THRESH and
            err_v < config.RECT_LEN_THRESH and
            len_ab > config.RECT_MIN_EDGE and
            len_cd > config.RECT_MIN_EDGE and
            len_ad > config.RECT_MIN_EDGE and
            len_bc > config.RECT_MIN_EDGE):
        return None

    # 计算每条边的角度
    theta_ab = math.degrees(math.atan2(corners[1][1] - corners[0][1],
                                       corners[1][0] - corners[0][0]))
    theta_cd = math.degrees(math.atan2(corners[3][1] - corners[2][1],
                                       corners[3][0] - corners[2][0]))
    theta_ad = math.degrees(math.atan2(corners[3][1] - corners[0][1],
                                       corners[3][0] - corners[0][0]))
    theta_bc = math.degrees(math.atan2(corners[2][1] - corners[1][1],
                                       corners[2][0] - corners[1][0]))

    is_parallel = (_are_parallel(theta_ab, theta_cd) and
                   _are_parallel(theta_ad, theta_bc))
    is_vertical = _are_vertical(theta_ab, theta_ad)

    if not (is_parallel and is_vertical):
        return None

    # 7. 对角线交叉点（矩形中心）
    center = _find_intersection(corners[0][0], corners[0][1],
                                 corners[2][0], corners[2][1],
                                 corners[1][0], corners[1][1],
                                 corners[3][0], corners[3][1])
    if center is None:
        return None

    # 8. 计算偏差
    dx = config.IMG_CENTER_X - center[0]
    dy = config.IMG_CENTER_Y - center[1]

    # 9. 生成 UART 格式
    uart_str = f"[{_format_coord(dx)}{_format_coord(dy)}*]"

    return {
        'center':  center,
        'offset':  (dx, dy),
        'corners': corners,
        'area':    area,
        'uart':    uart_str,
    }


def draw_debug(img, result: dict):
    """
    在图像上绘制检测结果（调试用）。

    参数:
        img:    图像对象
        result: detect() 的返回值
    """
    if result is None:
        return

    corners = result['corners']
    center = result['center']

    # 绘制矩形边框和顶点
    for i in range(4):
        j = (i + 1) % 4
        img.draw_line(corners[i][0], corners[i][1],
                       corners[j][0], corners[j][1],
                       color=(0, 255, 0), thickness=3)
        img.draw_circle(corners[i][0], corners[i][1], 2,
                         color=(0, 0, 255), fill=True, thickness=3)

    # 绘制中心交叉点
    img.draw_circle(center[0], center[1], 3,
                     color=(255, 0, 0), thickness=4)

    # 绘制坐标文字
    img.draw_string_advanced(0, 0, 30,
                              f"(x={center[0]},y={center[1]})",
                              color=(255, 255, 0), scale=3)
