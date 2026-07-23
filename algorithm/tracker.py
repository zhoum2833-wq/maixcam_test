"""
algorithm/tracker.py — 轻量多目标帧间跟踪器

帧间欧式距离匹配 + 速度估算 + 短暂丢失预测。
纯 Python，不依赖 numpy，适配 MaixCAM Pro。

核心逻辑:
  1. 当前帧检测 → 与现有 track 做最近邻匹配（距离阈值）
  2. 匹配成功 → 更新位置 + 速度估计
  3. 匹配失败（短暂丢失）→ 用上一帧速度预测当前位置
  4. 连续丢失超过 max_miss 帧 → 彻底删除 track
  5. 新出现且连续命中 ≥ min_hits → 确认新 track

效果:
  - 单帧漏检（运动模糊/瞬间遮挡）→ tracker 预测位置，控制系统不震荡
  - 新目标需要连中 min_hits 帧才确认 → 抑制孤立误检
  - 计算量极低（O(n*m) 贪婪匹配），不拖累帧率

用法:
    tracker = BallTracker(max_move=60, max_miss=2, min_hits=2)
    tracks = tracker.update(detections)
    for t in tracks:
        cx, cy = t['center']
        print(f"ID:{t['id']} pos:{cx},{cy} missed:{t['missed']}")
"""


class BallTracker:
    def __init__(self, max_move: int = 60, max_miss: int = 2,
                 min_hits: int = 2, dt: float = 1.0 / 40):
        """
        参数:
            max_move: 帧间最大移动距离 (px)。只匹配在此范围内的检测。
                      取决于: 小车最大速度 × 帧间隔 × 成像比例。
                      例: 车速 1m/s, 40fps, 球距 30cm → ~25px/帧，设 60 安全。
            max_miss: 最大连续丢失帧数。超出后删除 track。
                      设为 2 表示容忍 1-2 帧短暂遮挡/模糊。
            min_hits: 最少连续命中次数。新 track 需要连中此数才标记 confirmed=True。
                      设为 2 可滤除单帧孤立误检。
            dt:       帧间隔 (s)，用于速度估算。默认 1/40 ≈ 25ms。
        """
        self.max_move = max_move
        self.max_miss = max_miss
        self.min_hits = min_hits
        self.dt = dt

        self._tracks = []          # 活跃 track 列表
        self._next_id = 0          # 自增 ID

    def update(self, detections: list) -> list:
        """
        输入当前帧的全部检测结果，返回所有活跃 track（含预测）。

        参数:
            detections: [{center: (cx,cy), ...}, ...]
                        支持 ball.detect() 返回的 balls 列表中的每个 dict。

        返回:
            tracks: [{id, center, predicted, missed, hits, confirmed, raw}, ...]
                id:        整数，唯一且稳定（同一目标 ID 不变）
                center:    (cx, cy) 当前最佳位置（可能是预测值）
                predicted: bool, True 表示当前位置是预测得出的
                missed:    int, 连续丢失帧数（0 = 当前帧匹配成功）
                hits:      int, 累计命中次数
                confirmed: bool, hits >= min_hits 时为 True
                raw:       原始检测 dict 引用（predicted=False 时有值）
        """
        # 提取待匹配的中心坐标列表
        det_centers = [d['center'] for d in detections]
        det_matched = [False] * len(detections)

        # ---- 1. 对每个 track 做预测 + 匹配 ----
        for track in self._tracks:
            # 用速度估算预测当前位置（丢失帧时用，匹配成功后修正）
            px = track['cx'] + track['vx'] * self.dt
            py = track['cy'] + track['vy'] * self.dt
            track['pred_cx'] = int(px)
            track['pred_cy'] = int(py)
            track['matched'] = False

        # ---- 2. 贪婪最近邻匹配 ----
        # 对每个未匹配的 track，找最近的未匹配 detection
        for track in self._tracks:
            best_idx = -1
            best_dist = self.max_move + 1

            px, py = track['pred_cx'], track['pred_cy']
            for i, (dcx, dcy) in enumerate(det_centers):
                if det_matched[i]:
                    continue
                dx = dcx - px
                dy = dcy - py
                dist_sq = dx * dx + dy * dy
                if dist_sq < best_dist * best_dist:
                    best_dist = int(dist_sq ** 0.5)
                    best_idx = i

            if best_idx >= 0 and best_dist <= self.max_move:
                # 匹配成功
                dcx, dcy = det_centers[best_idx]
                det_matched[best_idx] = True
                track['matched'] = True

                # 更新速度估计（简单差分）
                track['vx'] = (dcx - track['cx']) / self.dt if track['hits'] > 0 else 0
                track['vy'] = (dcy - track['cy']) / self.dt if track['hits'] > 0 else 0

                # 更新位置
                track['cx'] = dcx
                track['cy'] = dcy
                track['missed'] = 0
                track['hits'] += 1
                track['predicted'] = False
                track['raw'] = detections[best_idx]

                if track['hits'] >= self.min_hits:
                    track['confirmed'] = True
            else:
                # 未匹配 → 使用预测位置
                track['cx'] = track['pred_cx']
                track['cy'] = track['pred_cy']
                track['missed'] += 1
                track['matched'] = False
                track['predicted'] = True
                track['raw'] = None

        # ---- 3. 删除连续丢失过多的 track ----
        self._tracks = [t for t in self._tracks if t['missed'] <= self.max_miss]

        # ---- 4. 未匹配的 detection → 新 track（tentative） ----
        for i, matched in enumerate(det_matched):
            if not matched:
                dcx, dcy = det_centers[i]
                self._tracks.append({
                    'id':        self._next_id,
                    'cx':        dcx,
                    'cy':        dcy,
                    'vx':        0,
                    'vy':        0,
                    'missed':    0,
                    'hits':      1,
                    'confirmed': False,
                    'predicted': False,
                    'matched':   True,
                    'raw':       detections[i],
                })
                self._next_id += 1

        # ---- 5. 返回活跃 track（统一输出格式） ----
        result = []
        for t in self._tracks:
            result.append({
                'id':        t['id'],
                'center':    (t['cx'], t['cy']),
                'predicted': t['predicted'],
                'missed':    t['missed'],
                'hits':      t['hits'],
                'confirmed': t['confirmed'],
                'raw':       t.get('raw'),
            })

        # 按 ID 排序，保证输出稳定
        result.sort(key=lambda t: t['id'])
        return result

    def reset(self):
        """清空所有 track（切换模式/重置场景时调用）"""
        self._tracks.clear()
        self._next_id = 0

    @property
    def track_count(self) -> int:
        """当前活跃 track 数"""
        return len(self._tracks)

    @property
    def confirmed_count(self) -> int:
        """已确认的 track 数（hits >= min_hits）"""
        return sum(1 for t in self._tracks if t['confirmed'])
