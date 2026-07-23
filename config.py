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

# ---- 巡线 ----
LINE_ROI          = (0, 120, 320, 80)
LINE_THRESH_BW    = 128
LINE_MIN_WIDTH    = 3

# ---- 识别 ----
DIGIT_CONF_MIN    = 0.6
MODEL_PATH        = "model/digit.tflite"
