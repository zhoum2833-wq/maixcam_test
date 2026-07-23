"""
vision/edge.py — 边缘跟随（沿一边黑线走）

场景: 车沿着一条黑线/黑色边界的某一侧行驶，保持固定距离。
      类似参考 maxicam.py 的 boundary_detect。

核心思路:
  1. 在画面一侧裁剪窄 ROI（左或右，由 EDGE_SIDE 决定）
  2. find_blobs 找黑色 blob → 就是边缘/黑线
  3. 高宽比 + 面积评分，过滤非线噪点
  4. 取 blob 的质心/边缘位置 → 与参考位置比较 → 偏差
"""

from maix import image as mimg
import config

EDGE_SIDE         = getattr(config, 'EDGE_SIDE', 'left')  # 'left' or 'right'
EDGE_BLACK_THRESH = getattr(config, 'EDGE_BLACK_THRESH', [0, 40, -20, 20, -20, 20])
EDGE_AREA_MIN     = getattr(config, 'EDGE_AREA_MIN', 80)
EDGE_AREA_MAX     = getattr(config, 'EDGE_AREA_MAX', 25000)
EDGE_ASPECT_MIN   = getattr(config, 'EDGE_ASPECT_MIN', 1.5)
EDGE_MIN_HEIGHT   = getattr(config, 'EDGE_MIN_HEIGHT', 20)
EDGE_REF_X        = getattr(config, 'EDGE_REF_X', 40)       # 目标：线应该在这个 x 位置


def track(img):
    """
    在画面一侧找黑线边缘，返回其位置。

    参数:
        img: maix.image.Image

    返回:
        dict:
            'cx':     黑线边缘质心 x 坐标
            'cy':     黑线边缘质心 y 坐标
            'side':   'left' 或 'right'（当前跟踪的边）
            'ref_x':  目标参考 x 位置
            'area':   blob 面积
            'rect':   (x, y, w, h) blob 外接矩形
        None: 未检测到边缘
    """
    rx, ry, rw, rh = config.EDGE_ROI

    # 1. 裁剪 ROI
    roi = img.crop(rx, ry, rw, rh)

    # 2. 找黑色 blob（merge=False 防污渍粘连）
    blobs = roi.find_blobs(
        [EDGE_BLACK_THRESH],
        area_threshold=EDGE_AREA_MIN,
        pixels_threshold=EDGE_AREA_MIN,
        merge=False,
    )

    if not blobs:
        return None

    # 3. 面积 + 高宽比评分，选最像"线"的 blob
    best_score = 0.0
    best_blob = None
    for b in blobs:
        bw = float(b.w())
        bh = float(b.h())
        area = float(b.area())

        if area < EDGE_AREA_MIN or area > EDGE_AREA_MAX:
            continue
        if bh < EDGE_MIN_HEIGHT:
            continue

        aspect = bh / (bw + 1.0)
        if aspect < EDGE_ASPECT_MIN:
            continue

        score = area * aspect
        if score > best_score:
            best_score = score
            best_blob = b

    if best_blob is None:
        return None

    # 4. 质心坐标（ROI → 原图）
    cx = int(best_blob.cx()) + rx
    cy = int(best_blob.cy()) + ry
    x, y, w, h = best_blob.x(), best_blob.y(), best_blob.w(), best_blob.h()

    return {
        'cx':    cx,
        'cy':    cy,
        'side':  EDGE_SIDE,
        'ref_x': EDGE_REF_X,
        'area':  int(best_blob.area()),
        'rect':  (x + rx, y + ry, w, h),
    }


def compute_steering(result: dict, img_w: int) -> float:
    """
    从边缘位置计算转向偏差。

    逻辑:
      EDGE_SIDE='left'  → 线在左边，线太近说明车偏右，该往左打
      EDGE_SIDE='right' → 线在右边，线太远说明车偏左，该往右打

    返回:
        -1000 ~ +1000  （0 = 距离正好，负 = 左打，正 = 右打）
    """
    if result is None:
        return 0.0

    edge_x = result['cx']
    ref_x  = result['ref_x']

    if result['side'] == 'left':
        # 左边跟线：线太近(x小) → 车偏右 → 正偏差(往左打)
        deviation = (ref_x - edge_x) / ref_x * 1000.0
    else:
        # 右边跟线：线太近(x大) → 车偏左 → 负偏差(往右打)
        deviation = (edge_x - ref_x) / (img_w - ref_x) * 1000.0 * (-1)

    return deviation


def draw_debug(img, result):
    """在图像上绘制边缘跟随调试信息。"""
    if result is None:
        return

    cx, cy = result['cx'], result['cy']
    x, y, w, h = result['rect']
    ref_x = result['ref_x']

    green   = mimg.Color.from_rgb(0, 255, 0)
    red     = mimg.Color.from_rgb(255, 0, 0)
    yellow  = mimg.Color.from_rgb(255, 255, 0)
    cyan    = mimg.Color.from_rgb(0, 255, 255)
    magenta = mimg.Color.from_rgb(255, 0, 255)
    dark    = mimg.Color.from_rgb(30, 30, 30)

    # ROI 框
    rx, ry, rw, rh = config.EDGE_ROI
    img.draw_rect(rx, ry, rw, rh, color=yellow, thickness=1)

    # blob 外接矩形
    img.draw_rect(x, y, w, h, color=green, thickness=2)

    # 边缘质心
    img.draw_circle(cx, cy, 5, color=red, thickness=3)
    img.draw_line(cx - 8, cy, cx + 8, cy, color=red, thickness=2)
    img.draw_line(cx, cy - 8, cx, cy + 8, color=red, thickness=2)

    # 参考位置线（目标应该保持的距离）
    bot_y = ry + rh
    img.draw_line(ref_x, ry, ref_x, bot_y, color=magenta, thickness=2)

    # 实际 vs 参考的差距
    img.draw_line(cx, bot_y - 10, ref_x, bot_y - 10, color=cyan, thickness=1)

    # 信息栏
    dev = compute_steering(result, img.width())
    img.draw_rect(0, 0, img.width(), 18, dark, -1)
    img.draw_string(2, 2,
                    f"EDGE:{result['side']} cx:{cx} ref:{ref_x} dev:{dev:.0f}",
                    color=green, scale=1.2)
