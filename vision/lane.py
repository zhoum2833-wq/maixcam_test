"""
vision/lane.py — 车道跟随（白底车道 + 两边黑边界）

场景: 白色车道被两条黑线夹在中间，车在车道里走。

核心思路:
  1. 裁剪底部 ROI
  2. find_blobs 找白色区域 → 白色区域 = 车道
  3. 车道中心 = 白色 blob 质心
  4. 计算偏差（车道中心 vs 图像中心）
  + 额外输出车道左右边界，方便精细控制
"""

from maix import image as mimg
import config

LANE_WHITE_THRESH = getattr(config, 'LANE_WHITE_THRESH', [60, 100, -30, 30, -30, 30])
LANE_AREA_MIN     = getattr(config, 'LANE_AREA_MIN', 400)
LANE_AREA_MAX     = getattr(config, 'LANE_AREA_MAX', 50000)
LANE_MERGE_MARGIN = getattr(config, 'LANE_MERGE_MARGIN', 15)


def track(img):
    """
    在图像 ROI 中寻找白色车道，返回车道中心及边界。

    参数:
        img: maix.image.Image

    返回:
        dict:
            'cx':       车道中心 x 坐标
            'cy':       车道中心 y 坐标
            'left':     车道左边界 x（黑线内侧）
            'right':    车道右边界 x（黑线内侧）
            'width':    车道宽度（像素）
            'area':     白色区域面积
            'rect':     (x, y, w, h) blob 外接矩形
        None: 未检测到车道
    """
    rx, ry, rw, rh = config.LANE_ROI

    # 1. 裁剪 ROI
    roi = img.crop(rx, ry, rw, rh)

    # 2. 在 ROI 中找白色 blob（白色 = 车道本身）
    blobs = roi.find_blobs(
        [LANE_WHITE_THRESH],
        area_threshold=LANE_AREA_MIN,
        pixels_threshold=LANE_AREA_MIN,
        merge=True,
        margin=LANE_MERGE_MARGIN,
    )

    if not blobs:
        return None

    # 3. 取面积最大的白色 blob（主车道，忽略边角碎片）
    best = max(blobs, key=lambda b: b.area())
    area = best.area()

    if not (LANE_AREA_MIN < area < LANE_AREA_MAX):
        return None

    # 4. 计算车道信息（ROI 坐标 → 原图坐标）
    cx = int(best.cx()) + rx
    cy = int(best.cy()) + ry
    bx, by, bw, bh = best.x(), best.y(), best.w(), best.h()

    # 车道左右边界
    left_edge  = bx + rx          # 白色区域左边界
    right_edge = bx + bw + rx     # 白色区域右边界
    lane_width = bw

    return {
        'cx':    cx,
        'cy':    cy,
        'left':  left_edge,
        'right': right_edge,
        'width': lane_width,
        'area':  int(area),
        'rect':  (bx + rx, by + ry, bw, bh),
    }


def compute_steering(result: dict, img_w: int) -> float:
    """
    从车道中心计算转向偏差。

    返回:
        -1000 ~ +1000  （0 = 车在车道正中，负 = 偏左，正 = 偏右）
    """
    if result is None:
        return 0.0
    mid = img_w / 2.0
    return (result['cx'] - mid) / mid * 1000.0


def draw_debug(img, result):
    """在图像上绘制车道检测调试信息。"""
    if result is None:
        return

    cx, cy = result['cx'], result['cy']
    left, right = result['left'], result['right']
    x, y, w, h = result['rect']

    green   = mimg.Color.from_rgb(0, 255, 0)
    red     = mimg.Color.from_rgb(255, 0, 0)
    yellow  = mimg.Color.from_rgb(255, 255, 0)
    cyan    = mimg.Color.from_rgb(0, 255, 255)
    dark    = mimg.Color.from_rgb(30, 30, 30)

    # ROI 框
    rx, ry, rw, rh = config.LANE_ROI
    img.draw_rect(rx, ry, rw, rh, color=yellow, thickness=1)

    # 车道 blob 外接矩形
    img.draw_rect(x, y, w, h, color=green, thickness=2)

    # 左右边界线
    bot_y = ry + rh
    img.draw_line(left, ry, left, bot_y, color=cyan, thickness=2)   # 左边界
    img.draw_line(right, ry, right, bot_y, color=cyan, thickness=2) # 右边界

    # 车道中心点
    img.draw_circle(cx, cy, 5, color=red, thickness=3)
    img.draw_line(cx - 10, cy, cx + 10, cy, color=red, thickness=2)
    img.draw_line(cx, cy - 10, cx, cy + 10, color=red, thickness=2)

    # 图像中心参考线
    img_cx = img.width() // 2
    img.draw_line(img_cx, ry, img_cx, bot_y, color=green, thickness=1)

    # 信息栏
    dev = compute_steering(result, img.width())
    img.draw_rect(0, 0, img.width(), 18, dark, -1)
    img.draw_string(2, 2,
                    f"LANE cx:{cx} dev:{dev:.0f} w:{result['width']} L:{left} R:{right}",
                    color=green, scale=1.2)
