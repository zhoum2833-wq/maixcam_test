"""
vision/perspective.py — 透视变换工具（纯 Python，无 numpy 依赖）

用途: 把前向视角的梯形车道"拉直"成俯视图，使车道线平行且等宽，
      提升直方图定位和滑动窗口跟踪的稳定性。

使用方式:
  1. 赛前标定: 选取图像中车道区域的 4 个角点 → compute_matrix()
  2. 每帧调用: warp(img) → 俯视图
  3. 可逆变换: warp_inv(points) → 把拟合结果投回原图

参考: OpenCV getPerspectiveTransform / warpPerspective 的纯 Python 实现
"""


def _solve_3x3(A, b):
    """高斯消元解 3×3 线性方程组 Ax = b。"""
    n = 3
    M = [[float(A[i][j]) for j in range(n)] + [float(b[i])] for i in range(n)]

    for col in range(n):
        # 选主元
        pivot = col
        for row in range(col + 1, n):
            if abs(M[row][col]) > abs(M[pivot][col]):
                pivot = row
        if abs(M[pivot][col]) < 1e-12:
            return None  # 奇异矩阵
        M[col], M[pivot] = M[pivot], M[col]

        # 消元
        for row in range(col + 1, n):
            factor = M[row][col] / M[col][col]
            for j in range(col, n + 1):
                M[row][j] -= factor * M[col][j]

    # 回代
    x = [0.0, 0.0, 0.0]
    for i in range(n - 1, -1, -1):
        s = M[i][n]
        for j in range(i + 1, n):
            s -= M[i][j] * x[j]
        x[i] = s / M[i][i]
    return x


def compute_matrix(src_pts, dst_pts):
    """
    计算 3×3 透视变换矩阵。

    参数:
        src_pts: [(x0,y0), (x1,y1), (x2,y2), (x3,y3)]  原图四点（左下/左上/右上/右下）
        dst_pts: [(x0,y0), (x1,y1), (x2,y2), (x3,y3)]  目标四点

    返回:
        M: 3×3 透视变换矩阵 list[list[float]]
        Minv: 3×3 逆变换矩阵
    """
    # 构建 8×8 方程组: 每对点提供 2 个方程
    A = [[0.0] * 8 for _ in range(8)]
    b = [0.0] * 8

    for i in range(4):
        sx, sy = src_pts[i][0], src_pts[i][1]
        dx, dy = dst_pts[i][0], dst_pts[i][1]

        A[2 * i]     = [sx, sy, 1, 0, 0, 0, -dx * sx, -dx * sy]
        A[2 * i + 1] = [0, 0, 0, sx, sy, 1, -dy * sx, -dy * sy]
        b[2 * i]     = dx
        b[2 * i + 1] = dy

    h = _solve_3x3(
        [[A[i][j] for j in range(8)] for i in range(8)],
        b
    )
    if h is None:
        raise ValueError("Perspective transform: singular matrix, check source points")

    M = [
        [h[0], h[1], h[2]],
        [h[3], h[4], h[5]],
        [h[6], h[7], 1.0],
    ]

    # 计算逆矩阵
    det = (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
         - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
         + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))
    if abs(det) < 1e-12:
        raise ValueError("Perspective transform: non-invertible matrix")

    inv_det = 1.0 / det
    Minv = [
        [(M[1][1] * M[2][2] - M[1][2] * M[2][1]) * inv_det,
         (M[0][2] * M[2][1] - M[0][1] * M[2][2]) * inv_det,
         (M[0][1] * M[1][2] - M[0][2] * M[1][1]) * inv_det],
        [(M[1][2] * M[2][0] - M[1][0] * M[2][2]) * inv_det,
         (M[0][0] * M[2][2] - M[0][2] * M[2][0]) * inv_det,
         (M[0][2] * M[1][0] - M[0][0] * M[1][2]) * inv_det],
        [(M[1][0] * M[2][1] - M[1][1] * M[2][0]) * inv_det,
         (M[0][1] * M[2][0] - M[0][0] * M[2][1]) * inv_det,
         (M[0][0] * M[1][1] - M[0][1] * M[1][0]) * inv_det],
    ]

    return M, Minv


def _transform_pt(x, y, M):
    """对单点应用 3×3 透视变换。"""
    w = M[2][0] * x + M[2][1] * y + M[2][2]
    if abs(w) < 1e-10:
        return (0.0, 0.0)
    tx = (M[0][0] * x + M[0][1] * y + M[0][2]) / w
    ty = (M[1][0] * x + M[1][1] * y + M[1][2]) / w
    return (tx, ty)


def warp_points(points, M):
    """
    对一组点坐标应用透视变换。

    参数:
        points: [(x0,y0), ...]  原图坐标
        M:      3×3 透视变换矩阵

    返回:
        [(tx0,ty0), ...]  变换后坐标
    """
    result = []
    for x, y in points:
        tx, ty = _transform_pt(x, y, M)
        result.append((tx, ty))
    return result


# ============================================================
#  预置标定: MaixCAM 前向视角 → 俯视图
#  赛后调整 src_pts 即可适配不同安装角度
# ============================================================

# 默认: 320×240，摄像头向下倾斜约 30°
_SRC_DEFAULT = [
    (0,   200),   # 左下 — 近处车道左边界
    (60,   60),   # 左上 — 远处车道左边界
    (260,  60),   # 右上 — 远处车道右边界
    (320, 200),   # 右下 — 近处车道右边界
]

_DST_DEFAULT = [
    (40,   240),   # 左下
    (40,     0),   # 左上
    (280,    0),   # 右上
    (280,  240),   # 右下
]


class Warper:
    """透视变换器 — 赛前标定一次，每帧复用。"""

    def __init__(self, src_pts=None, dst_pts=None, img_w=320, img_h=240):
        self.img_w = img_w
        self.img_h = img_h
        self.src = src_pts or _SRC_DEFAULT
        self.dst = dst_pts or _DST_DEFAULT
        self.M = None
        self.Minv = None
        self.line_width = 0  # 变换后车道实际宽度（像素）

    def calibrate(self):
        """计算变换矩阵（赛前标定一次）。"""
        self.M, self.Minv = compute_matrix(self.src, self.dst)
        # 车道宽度 = dst 左右边界差
        self.line_width = int(self.dst[3][0] - self.dst[0][0])
        return self.M, self.Minv

    def warp_point(self, x, y, inverse=False):
        """对单点做透视变换（inverse=True = 逆向: 俯视图 → 原图）。"""
        M = self.Minv if inverse else self.M
        if M is None:
            self.calibrate()
            M = self.Minv if inverse else self.M
        return _transform_pt(x, y, M)

    def warp_points(self, points, inverse=False):
        """对多点做透视变换。"""
        M = self.Minv if inverse else self.M
        if M is None:
            self.calibrate()
            M = self.Minv if inverse else self.M
        return warp_points(points, M)
