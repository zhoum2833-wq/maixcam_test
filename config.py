"""
config.py — 全局配置 (MaixPy v4.12+)

比赛现场主要改这个文件。
"""

# ---- 串口 (与 MSPM0 通信) ----
UART_DEVICE       = "/dev/ttyS1"     # UART 设备路径 (S0=USB-C, S1/S2=GPIO)
UART_BAUDRATE     = 115200
UART_RX_BUF       = 256

# ---- 摄像头 ----
CAM_WIDTH         = 480
CAM_HEIGHT        = 320
CAM_PIXFMT        = "RGB888"          # RGB888 / RGB565 / GRAYSCALE

# ---- 屏幕 ----
DISP_WIDTH        = 640               # MaixCAM Pro: 2.4" 640x480
DISP_HEIGHT       = 480

# ---- 矩形检测 (find_blobs 路线) ----
RECT_BLACK_THRESH  = [0, 15, -20, 20, -20, 20]   # LAB 黑色（备用）
RECT_WHITE_THRESH  = [60, 100, -30, 30, -30, 30] # LAB 白色（主检测目标，放宽A/B）
RECT_AREA_MIN      = 500                          # 最小黑色 blob 面积
RECT_AREA_MAX      = 55000                        # 最大黑色 blob 面积
RECT_WHITE_RATIO   = 0.70                         # 框内白色面积/框面积 > 此值
RECT_ASPECT_MIN    = 0.55                         # 最小宽高比
RECT_ASPECT_MAX    = 1.8                          # 最大宽高比
RECT_MERGE_MARGIN  = 15                           # merge 合并距离

# ---- 图像中心参考点 ----
IMG_CENTER_X      = 240               # CAM_WIDTH / 2
IMG_CENTER_Y      = 160               # CAM_HEIGHT / 2

# ============================================================
#  场景 A: 中线跟随 (vision/line.py)
#  白底 + 中间一条黑线，车跨在线上走
# ============================================================
LINE_ROI          = (0, 140, 320, 100)    # ROI: x, y, w, h（图像底部区域）
LINE_BLACK_THRESH = [0, 45, -30, 30, -30, 30]  # LAB 黑色阈值
LINE_AREA_MIN     = 80                    # 最小黑线面积
LINE_AREA_MAX     = 28000                 # 最大黑线面积
LINE_ASPECT_MIN   = 1.5                   # 最小高/宽比（小于此值不是线，是污渍）
LINE_MIN_HEIGHT   = 20                    # blob 最低高度（太矮不是线）

# ============================================================
#  场景 B: 车道跟随 (vision/lane.py)
#  白底车道 + 两边黑色边界，车在白色车道中间走
# ============================================================
LANE_ROI          = (0, 100, 320, 140)    # ROI: x, y, w, h（比中线 ROI 更大）
LANE_WHITE_THRESH = [60, 100, -30, 30, -30, 30]  # LAB 白色阈值
LANE_AREA_MIN     = 400                   # 最小白色车道面积
LANE_AREA_MAX     = 50000                 # 最大白色车道面积
LANE_MERGE_MARGIN = 15                    # blob 合并距离

# ============================================================
#  场景 C: 边缘跟随 (vision/edge.py)
#  沿一条黑线/边界的某一侧走，保持固定距离
# ============================================================
EDGE_SIDE         = 'left'                # 'left' 跟左边  /  'right' 跟右边
EDGE_ROI          = (0, 80, 80, 160)      # ROI: 窄条，只看左侧（跟 right 时改为右侧）
EDGE_BLACK_THRESH = [0, 40, -20, 20, -20, 20]  # LAB 黑色阈值（稍严）
EDGE_AREA_MIN     = 80                    # 最小面积
EDGE_AREA_MAX     = 25000                 # 最大面积
EDGE_ASPECT_MIN   = 1.5                   # 最小高/宽比
EDGE_MIN_HEIGHT   = 20                    # 最低高度
EDGE_REF_X        = 40                    # 目标：线边缘应该保持在这个 x 位置

# ============================================================
#  场景 E: 钢球检测 (vision/ball.py)
#  YOLOv5s 深度学习模型 → 直接检测钢球
#  模型: model/ball.model/model_295152.mud (cvimodel, 320×320)
#  数据集: 2910 张, mAP 0.745, 标签: ball
# ============================================================
BALL_MODEL_PATH     = "model/ball.model/model_295152.mud"
BALL_CONF_THRESH    = 0.45                           # 置信度阈值
BALL_IOU_THRESH     = 0.45                           # NMS IoU 阈值
BALL_SIZE_TOLERANCE = 0.30                           # 多目标尺寸容差（±30%，用于软过滤离群框）

# ---- 识别 ----
DIGIT_CONF_MIN    = 0.6
MODEL_PATH        = "model/digit.tflite"

# ============================================================
#  场景 D: 直方图 + 滑动窗口 + 多项式拟合 (vision/line_histogram.py)
#  完整的曲线提取: 底部位置 + 斜率 + 曲率
# ============================================================
HIST_N_WINDOWS    = 8                     # 滑动窗口数量 (4~15)
HIST_MARGIN       = 60                    # 窗口搜索半宽 (20~150 px)
HIST_MINPIX       = 30                    # 窗口内最小有效像素 (10~200)
HIST_BLACK_THRESH = [0, 45, -30, 30, -30, 30]  # LAB 黑色阈值
HIST_AREA_MIN     = 30                    # blob 最小面积
HIST_AREA_MAX     = 20000                 # blob 最大面积
HIST_ASPECT_MIN   = 1.2                   # blob 最小高宽比

# ============================================================
#  透视变换 (vision/perspective.py)
#  摄像头前向视角 → 俯视图的 4 个标定点
#  赛后根据实际安装角度重新选取
# ============================================================
PERSP_SRC_PTS = [                        # 原图中的梯形四点（左下/左上/右上/右下）
    (0,   200),
    (60,   60),
    (260,  60),
    (320, 200),
]
PERSP_DST_PTS = [                        # 目标矩形四点
    (40,   240),
    (40,     0),
    (280,    0),
    (280,  240),
]
