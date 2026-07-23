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
    """在图像上绘制所有检测结果 + track 信息（调试用，仅 DEBUG_DRAW=True 时调用）

    性能优化:
      - O(1) track 查找（用 id() 字典，不用 O(n²) 距离匹配）
      - 外接圆改为细线（减少光栅化开销）
      - 标签精简到 3 字符（减少字体渲染）
      - 纯预测 track 用 set 查找（避免 O(n²) 扫描）
    """
    if result is None:
        return

    green   = mimg.Color.from_rgb(0, 255, 0)
    red     = mimg.Color.from_rgb(255, 0, 0)
    yellow  = mimg.Color.from_rgb(255, 255, 0)
    magenta = mimg.Color.from_rgb(255, 0, 255)
    cyan    = mimg.Color.from_rgb(0, 255, 255)
    orange  = mimg.Color.from_rgb(255, 165, 0)
    grey    = mimg.Color.from_rgb(128, 128, 128)
    white   = mimg.Color.from_rgb(255, 255, 255)

    balls = result.get('balls', [])
    if not balls and result.get('center'):
        balls = [result]

    # O(1) 查找: 用 detection 对象 id 直接映射到 track
    det_to_track = result.get('_det_to_track', {})

    # 收集已匹配的检测中心（用于纯预测 track 的快速去重）
    matched_centers = set()

    for b in balls:
        center = b['center']
        x, y, w, h = b.get('rect', (0, 0, 0, 0))
        score  = b.get('score', 0.0)
        filtered = b.get('filtered', False)

        match_track = det_to_track.get(id(b))
        if match_track:
            matched_centers.add(match_track['center'])

        # 颜色: filtered > track 状态 > 默认
        if filtered:
            rect_color = magenta
            thickness  = 1
        elif match_track:
            if match_track['predicted']:
                rect_color = orange
            elif not match_track['confirmed']:
                rect_color = grey
            else:
                rect_color = cyan
            thickness = 2
        else:
            rect_color = yellow
            thickness = 2

        # 只画边界框 + 圆心十字（外接圆太贵，砍掉）
        img.draw_rect(x, y, w, h, color=rect_color, thickness=thickness)
        img.draw_circle(center[0], center[1], 2, color=red, thickness=2)

        # 精简标签: 只显示 track ID（1 字符）+ 过滤标记
        parts = []
        if filtered:
            parts.append("?")
        if match_track:
            parts.append(str(match_track['id']))
        if match_track and match_track['predicted']:
            parts.append("P")
        label = "".join(parts) if parts else None
        if label:
            img.draw_string(x, max(y - 12, 0), label, color=rect_color, scale=1.0)

    # 纯预测 track（无匹配检测）→ 小十字标记
    tracks = result.get('tracks', [])
    if tracks:
        for t in tracks:
            if t['predicted'] and t['confirmed']:
                if t['center'] not in matched_centers:
                    cx, cy = t['center']
                    img.draw_line(cx - 4, cy, cx + 4, cy, color=orange, thickness=1)
                    img.draw_line(cx, cy - 4, cx, cy + 4, color=orange, thickness=1)

    # 左上角统计
    count = result.get('count', len(balls))
    count_raw = result.get('count_raw', len(balls))
    n_filtered = count_raw - count
    track_cnt = result.get('track_count', len(tracks))
    track_conf = result.get('track_confirmed', 0)

    status = f"balls:{count} trk:{track_conf}/{track_cnt}"
    if n_filtered > 0:
        status += f" flt:{n_filtered}"
    img.draw_string(0, 0, status, color=white, scale=1.2)
