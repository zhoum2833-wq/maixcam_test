"""
vision/ball.py — 钢球检测（YOLOv5s 深度学习模型）

管线: YOLOv5s (320×320) → NMS → 尺寸软过滤 → 多目标输出

模型: model/ball.model/model_295152.mud (cvimodel, MaixCAM Pro 专用)
数据集: 2910 张钢球图片, 140 轮最佳 mAP 0.745, 标注框限制 10
标签: ball（单类）

多目标策略:
  - 模型原生支持多目标（标注框限制 10），不做硬裁剪
  - 统计所有检出框的中位面积，偏离 ±30% 以上的框标记 filtered=True
  - 不删除离群框（可能是有遮挡/粘连的球），只降低优先级
  - primary 选「未被过滤 + 置信度最高」的球

用法:
    result = ball.detect(img)
    → {'balls': [...], 'primary': {...}, 'count': 3, 'count_raw': 4, ...}
"""

from maix import image as mimg
import config

_DETECTOR = None


def _get_detector():
    """懒加载 YOLOv5 检测器（遵守架构规范：模块不执行顶层代码）"""
    global _DETECTOR
    if _DETECTOR is None:
        from maix import nn
        model_path = getattr(config, 'BALL_MODEL_PATH',
                             'model/ball.model/model_295152.mud')
        _DETECTOR = nn.YOLOv5(model=model_path)
    return _DETECTOR


def _obj_to_dict(obj, img_cx, img_cy):
    """将 YOLO 检测对象转为统一 dict"""
    cx = int(obj.x + obj.w / 2)
    cy = int(obj.y + obj.h / 2)
    return {
        'center': (cx, cy),
        'offset': (img_cx - cx, img_cy - cy),
        'radius': max(obj.w, obj.h) // 2,
        'area':   obj.w * obj.h,
        'score':  round(obj.score, 3),
        'rect':   (obj.x, obj.y, obj.w, obj.h),
        'w':      obj.w,
        'h':      obj.h,
        'filtered': False,
    }


def _median_area(balls):
    """计算 balls 的中位面积"""
    if not balls:
        return 0
    areas = sorted(b['area'] for b in balls)
    n = len(areas)
    if n % 2 == 1:
        return areas[n // 2]
    return (areas[n // 2 - 1] + areas[n // 2]) // 2


def _apply_size_filter(balls, tolerance):
    """
    尺寸软过滤: 不删除，只标记 filtered=True。

    偏离中位面积 ±tolerance 以上的框标记为 filtered，
    可能是反光误检或粘连合并框。
    保留但不参与 primary 竞争。
    """
    if len(balls) < 3:
        # 只有 1-2 个目标时不滤波，信息太少
        return balls

    med = _median_area(balls)
    if med <= 0:
        return balls

    lo = med * (1.0 - tolerance)
    hi = med * (1.0 + tolerance)

    for b in balls:
        if b['area'] < lo or b['area'] > hi:
            b['filtered'] = True

    return balls


def detect(img):
    """
    使用 YOLOv5s 检测图像中的钢球（多目标）。

    返回:
        {
            'balls':   [{...}, ...],    # 全部检测结果（含 filtered 标记）
            'count':   int,             # 未过滤的有效数量
            'count_raw': int,           # 原始检出总数
            'primary': {...},           # 首选目标（用于 UART / 跟踪）
            'median_area': int,         # 中位面积（调试用）
            # 兼容旧版单目标接口:
            'center':  (cx, cy),
            'offset':  (dx, dy),
            'radius':  int,
            'score':   float,
            'rect':    (x, y, w, h),
        }
        未检测到返回 None
    """
    detector = _get_detector()
    conf_th = getattr(config, 'BALL_CONF_THRESH', 0.45)
    iou_th  = getattr(config, 'BALL_IOU_THRESH', 0.45)
    size_tol = getattr(config, 'BALL_SIZE_TOLERANCE', 0.30)

    objs = detector.detect(img, conf_th=conf_th, iou_th=iou_th)

    if not objs:
        return None

    w_img, h_img = img.width(), img.height()
    img_cx, img_cy = w_img // 2, h_img // 2

    # 全部转换为统一格式
    balls = [_obj_to_dict(obj, img_cx, img_cy) for obj in objs]

    # 按置信度降序
    balls.sort(key=lambda b: b['score'], reverse=True)

    # 尺寸软过滤（不删除，只标记）
    balls = _apply_size_filter(balls, size_tol)

    count_raw = len(balls)
    count = sum(1 for b in balls if not b['filtered'])

    # primary 选: 未过滤 + 最高分；如果全部被过滤则取最高分
    valid_balls = [b for b in balls if not b['filtered']] or balls
    primary = max(valid_balls, key=lambda b: b['score'])

    return {
        'balls':       balls,
        'count':       count,
        'count_raw':   count_raw,
        'primary':     primary,
        'median_area': _median_area(balls),
        # 兼容旧版单目标字段（main.py uart_send_coord 依赖）
        'center':      primary['center'],
        'offset':      primary['offset'],
        'radius':      primary['radius'],
        'score':       primary['score'],
        'area':        primary['area'],
        'rect':        primary['rect'],
    }


def draw_debug(img, result):
    """在图像上绘制所有检测结果（调试用，仅 DEBUG_DRAW=True 时调用）"""
    if result is None:
        return

    green   = mimg.Color.from_rgb(0, 255, 0)
    red     = mimg.Color.from_rgb(255, 0, 0)
    yellow  = mimg.Color.from_rgb(255, 255, 0)
    magenta = mimg.Color.from_rgb(255, 0, 255)   # filtered 框用
    white   = mimg.Color.from_rgb(255, 255, 255)

    balls = result.get('balls', [])
    if not balls and result.get('center'):
        # 兼容旧格式（单目标 dict）
        balls = [result]

    for b in balls:
        center = b['center']
        radius = b.get('radius', 10)
        x, y, w, h = b.get('rect', (0, 0, 0, 0))
        score  = b.get('score', 0.0)
        filtered = b.get('filtered', False)

        # 被过滤的框用洋红色 + 虚线风格（细线）
        rect_color = magenta if filtered else yellow
        circ_color = magenta if filtered else green
        thickness  = 1 if filtered else 2

        # 外接圆
        img.draw_circle(center[0], center[1], radius, color=circ_color, thickness=thickness)
        # 边界框
        img.draw_rect(x, y, w, h, color=rect_color, thickness=thickness)
        # 圆心十字
        img.draw_circle(center[0], center[1], 2, color=red, thickness=2)

        # 标签
        flag = "?" if filtered else ""
        img.draw_string(x, max(y - 12, 0), f"ball{flag} {score:.2f}",
                        color=rect_color, scale=1.0)

    # 左上角统计信息
    count = result.get('count', len(balls))
    count_raw = result.get('count_raw', len(balls))
    n_filtered = count_raw - count
    med_area = result.get('median_area', 0)

    status = f"balls:{count}"
    if n_filtered > 0:
        status += f" (flt:{n_filtered})"
    img.draw_string(0, 0, status, color=white, scale=1.2)

    primary = result.get('primary')
    if primary:
        img.draw_string(0, 16,
                        f"P:{primary['center'][0]},{primary['center'][1]} "
                        f"r={primary['radius']}",
                        color=white, scale=1.0)
