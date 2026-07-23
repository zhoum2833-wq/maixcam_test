"""
vision/line_histogram.py — 直方图 + 滑动窗口 + 多项式拟合巡线

参考经典视觉巡线策略，适配 MaixPy v4.12:
  - "直方图": 用底部 ROI + find_blobs 找线的起始位置
  - "滑动窗口": N 个水平条带 ROI，逐层用 find_blobs 跟踪线
  - "多项式拟合": 纯 Python 最小二乘法，拟合 x = A*y^2 + B*y + C

特点:
  - 能看到整条线的走势（不只是底部位置）
  - 输出底部位置 + 斜率 + 曲率，支持预判弯道
  - 分层 find_blobs 速度快（硬件加速）
  - 边界约束防止奇异值
"""

from maix import image as mimg
import config

# ============================================================
#  参数（从 config 读取，带边界约束默认值）
# ============================================================
N_WINDOWS      = max(4, min(15,  getattr(config, 'HIST_N_WINDOWS', 8)))
MARGIN         = max(20, min(150, getattr(config, 'HIST_MARGIN', 60)))
MINPIX         = max(10, min(200, getattr(config, 'HIST_MINPIX', 30)))
BLACK_THRESH   = getattr(config, 'HIST_BLACK_THRESH', [0, 45, -30, 30, -30, 30])
AREA_MIN       = getattr(config, 'HIST_AREA_MIN', 30)
AREA_MAX       = getattr(config, 'HIST_AREA_MAX', 20000)
ASPECT_MIN     = getattr(config, 'HIST_ASPECT_MIN', 1.2)

# 边界约束
MAX_SLOPE      = 2.0     # |dx/dy| 上限，防止奇异值
MAX_CURVATURE  = 0.01    # |d2x/dy2| 上限
MIN_VALID_WIN  = max(2, N_WINDOWS // 3)  # 最少有效窗口数


def _clip(val, lo, hi):
    """边界约束辅助函数。"""
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val


def _polyfit_2d(y_vals, x_vals):
    """
    纯 Python 最小二乘法: 拟合 x = A*y^2 + B*y + C。

    先归一化 y 到 [0,1] 防数值溢出（y 可达 240，y^4 可达 3e9），
    拟合完再反归一化系数。

    参数:
        y_vals, x_vals: 等长 list，至少 3 个点

    返回:
        (A, B, C) 多项式系数（原 y 坐标空间）
        (0, 0, mean_x)  点数不足时退化为均值
    """
    n = len(y_vals)
    if n < 3:
        mx = sum(x_vals) / n if n > 0 else 0.0
        return (0.0, 0.0, mx)

    # ── 归一化 y 到 [0, 1] ──
    y_min = min(y_vals)
    y_max = max(y_vals)
    y_range = y_max - y_min
    if y_range < 1.0:
        y_range = 1.0  # 防止除零（水平线）

    y_norm = [(y - y_min) / y_range for y in y_vals]

    # ── 累加（归一化后 y_norm ∈ [0,1]，y^4 ∈ [0,1]）──
    sy = sy2 = sy3 = sy4 = 0.0
    sx = sxy = sxy2 = 0.0
    for x, yn in zip(x_vals, y_norm):
        yn2 = yn * yn
        sy   += yn
        sy2  += yn2
        sy3  += yn2 * yn
        sy4  += yn2 * yn2
        sx   += x
        sxy  += x * yn
        sxy2 += x * yn2

    # ── 高斯消元解 3×3 ──
    M = [
        [sy4, sy3, sy2, sxy2],
        [sy3, sy2, sy,  sxy],
        [sy2, sy,  float(n), sx],
    ]

    for col in range(3):
        pivot = col
        for row in range(col + 1, 3):
            if abs(M[row][col]) > abs(M[pivot][col]):
                pivot = row
        if abs(M[pivot][col]) < 1e-10:
            # 退化 → 线性拟合
            denom = n * sy2 - sy * sy
            if abs(denom) > 1e-10:
                Bn = (n * sxy - sx * sy) / denom
                Cn = (sx * sy2 - sy * sxy) / denom
                # 反归一化: x = Bn*yn + Cn
                #   yn = (y - y_min) / y_range
                #   x = Bn*(y - y_min)/y_range + Cn
                #     = (Bn/y_range)*y + (Cn - Bn*y_min/y_range)
                B = Bn / y_range
                C = Cn - Bn * y_min / y_range
                return (0.0, B, C)
            return (0.0, 0.0, sx / n)

        M[col], M[pivot] = M[pivot], M[col]

        for row in range(col + 1, 3):
            factor = M[row][col] / M[col][col]
            for j in range(col, 4):
                M[row][j] -= factor * M[col][j]

    # 回代（归一化空间的系数）
    Cn = M[2][3] / M[2][2]
    Bn = (M[1][3] - M[1][2] * Cn) / M[1][1]
    An = (M[0][3] - M[0][1] * Bn - M[0][2] * Cn) / M[0][0]

    # ── 反归一化: yn = (y - y_min) / y_range ──
    #   x = An*yn^2 + Bn*yn + Cn
    #     = An*(y-y_min)^2/y_range^2 + Bn*(y-y_min)/y_range + Cn
    #     = (An/y_range^2)*y^2 + (Bn/y_range - 2*An*y_min/y_range^2)*y
    #       + (An*y_min^2/y_range^2 - Bn*y_min/y_range + Cn)
    A = An / (y_range * y_range)
    B = Bn / y_range - 2.0 * An * y_min / (y_range * y_range)
    C = An * y_min * y_min / (y_range * y_range) - Bn * y_min / y_range + Cn

    return (A, B, C)


def _find_line_in_window(img, rx, ry, rw, rh, cx_guess):
    """
    在单个滑动窗口 ROI 中找黑线 blob。

    返回:
        (cx, cy)  线在窗口中的位置（原图坐标）
        None      未找到
    """
    roi = img.crop(rx, ry, rw, rh)
    blobs = roi.find_blobs(
        [BLACK_THRESH],
        area_threshold=AREA_MIN,
        pixels_threshold=AREA_MIN,
        merge=False,
    )

    if not blobs:
        return None

    # 如果有上一层的猜测位置，优先选靠近猜測位置且像素足够的 blob
    best = None
    best_dist = 99999.0
    for b in blobs:
        area = b.area()
        if area < AREA_MIN or area > AREA_MAX:
            continue
        bh = b.h()
        bw = b.w()
        if bh < 3:
            continue
        aspect = bh / (bw + 1.0)
        if aspect < ASPECT_MIN and area < 150:
            continue

        if area < MINPIX:
            continue

        bx_cx = b.cx() + rx
        dist = abs(bx_cx - cx_guess)
        if dist < best_dist:
            best_dist = dist
            best = b

    if best is None:
        return None

    return (int(best.cx()) + rx, int(best.cy()) + ry)


def track(img):
    """
    直方图 + 滑动窗口 + 多项式拟合，提取线的完整曲线信息。

    参数:
        img: maix.image.Image (建议已透视变换为俯视图)

    返回:
        dict:
            'bottom_x':   线在图像底部 x 坐标（最关键的转向依据）
            'slope':      线在底部的斜率 dx/dy (-1~1, 负=线偏左, 正=线偏右)
            'curve':      二次项系数 A（>0=向右弯, <0=向左弯）
            'fit':        (A, B, C) 多项式系数  x = A*y^2 + B*y + C
            'points':     [(cx,cy), ...]  各窗口检测到的线中心点
            'valid_win': 有效窗口数 / 总窗口数
        None: 未检测到足够多的线点
    """
    img_w = img.width()
    img_h = img.height()

    # ============================================================
    #  1. 直方图法确定线的初始位置（图像底部 1/3 区域）
    # ============================================================
    base_y_start = img_h * 2 // 3
    base_h = img_h - base_y_start
    roi_base = img.crop(0, base_y_start, img_w, base_h)

    # 在底部找所有黑色 blob，作为直方图的"波峰"
    base_blobs = roi_base.find_blobs(
        [BLACK_THRESH],
        area_threshold=AREA_MIN * 3,  # 底部 blob 面积应该更大
        pixels_threshold=AREA_MIN * 2,
        merge=True,
        margin=10,
    )

    if not base_blobs:
        return None

    # 取面积最大的 blob 的质心作为起始位置（模拟直方图的最高峰）
    best_base = max(base_blobs, key=lambda b: b.area())
    if best_base.area() < MINPIX:
        return None

    base_cx = int(best_base.cx())
    base_cy = base_y_start + int(best_base.cy())
    # 换算到原图坐标
    base_x = base_cx
    base_y = base_cy

    # ============================================================
    #  2. 滑动窗口: 从底向上逐层搜索
    # ============================================================
    window_h = img_h // N_WINDOWS
    margin = MARGIN
    points = []

    cx_current = float(base_x)

    for win_idx in range(N_WINDOWS):
        # 窗口从底向上排列: win_idx=0 是最底层
        wy_low = img_h - (win_idx + 1) * window_h
        wy_high = img_h - win_idx * window_h
        wy_mid = (wy_low + wy_high) / 2.0

        # 窗口水平范围（受边界约束）
        wx_low = max(0, int(cx_current - margin))
        wx_high = min(img_w, int(cx_current + margin))
        ww = wx_high - wx_low
        if ww < 10:
            # 窗口太窄，保持上一层的中心
            continue

        pt = _find_line_in_window(img, wx_low, wy_low, ww, wy_high - wy_low, cx_current)

        if pt is not None:
            cx, cy = pt
            cx_current = float(cx)
            points.append((cx, cy))
        # 如果当前窗口没找到线，保持 cx_current 不变（继承上一层位置）

    # ============================================================
    #  3. 边界检查: 有效窗口数是否足够
    # ============================================================
    valid_n = len(points)
    if valid_n < MIN_VALID_WIN:
        return None

    # ============================================================
    #  4. 多项式拟合: x = A*y^2 + B*y + C
    # ============================================================
    y_vals = [p[1] for p in points]
    x_vals = [p[0] for p in points]
    A, B, C = _polyfit_2d(y_vals, x_vals)

    # 边界约束
    A = _clip(A, -MAX_CURVATURE, MAX_CURVATURE)
    B = _clip(B, -MAX_SLOPE, MAX_SLOPE)

    # 计算底部 x 和斜率
    bottom_y = float(img_h)
    bottom_x = A * bottom_y * bottom_y + B * bottom_y + C
    bottom_slope = 2.0 * A * bottom_y + B  # dx/dy at bottom

    # 边界约束
    bottom_x = _clip(bottom_x, 0.0, float(img_w))
    bottom_slope = _clip(bottom_slope, -MAX_SLOPE, MAX_SLOPE)

    return {
        'bottom_x':  int(bottom_x),
        'slope':     round(bottom_slope, 4),
        'curve':     round(A, 6),
        'fit':       (round(A, 6), round(B, 4), round(C, 1)),
        'points':    points,
        'valid_win': f"{valid_n}/{N_WINDOWS}",
    }


def compute_steering(result: dict, img_w: int) -> float:
    """
    综合底部位置和斜率计算转向偏差。

    返回:
        -1000 ~ +1000  （0 = 正中，负 = 偏左，正 = 偏右）
    """
    if result is None:
        return 0.0

    mid = img_w / 2.0
    # 位置偏差（主分量）
    pos_dev = (result['bottom_x'] - mid) / mid * 1000.0
    # 斜率补偿（斜率越大说明弯越急，提前多打一点）
    slope_dev = result['slope'] * 300.0

    return pos_dev + slope_dev


def draw_debug(img, result):
    """在图像上绘制直方图 + 滑动窗口调试信息。"""
    if result is None:
        return

    green   = mimg.Color.from_rgb(0, 255, 0)
    red     = mimg.Color.from_rgb(255, 0, 0)
    yellow  = mimg.Color.from_rgb(255, 255, 0)
    cyan    = mimg.Color.from_rgb(0, 255, 255)
    magenta = mimg.Color.from_rgb(255, 0, 255)
    dark    = mimg.Color.from_rgb(30, 30, 30)

    img_w = img.width()
    img_h = img.height()
    window_h = img_h // N_WINDOWS

    # 画滑动窗口（绿色虚线框）
    for win_idx in range(N_WINDOWS):
        wy_low = img_h - (win_idx + 1) * window_h
        wy_high = img_h - win_idx * window_h
        img.draw_rect(0, wy_low, img_w, window_h, color=dark, thickness=1)

    # 画检测到的线中心点
    for cx, cy in result.get('points', []):
        img.draw_circle(cx, cy, 3, color=cyan, thickness=2)

    # 画拟合曲线
    A, B, C = result['fit']
    last_x = None
    for y in range(0, img_h, 4):
        x = int(A * y * y + B * y + C)
        if 0 <= x < img_w:
            if last_x is not None:
                img.draw_line(last_x, y - 4, x, y, color=green, thickness=1)
            last_x = x

    # 底部位置 + 图像中心参考
    bx = result['bottom_x']
    img_cx = img_w // 2
    img.draw_circle(bx, img_h - 5, 6, color=red, thickness=3)
    img.draw_line(img_cx, img_h, img_cx, 0, color=dark, thickness=1)

    # 信息栏
    dev = compute_steering(result, img_w)
    img.draw_rect(0, 0, img_w, 36, dark, -1)
    img.draw_string(2, 2, f"HIST bx:{bx} dev:{dev:.0f} slope:{result['slope']:.3f}",
                    color=green, scale=1.1)
    img.draw_string(2, 18, f"     curve:{result['curve']:.4f} win:{result['valid_win']}",
                    color=cyan, scale=1.0)
