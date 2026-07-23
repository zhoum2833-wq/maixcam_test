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

# ---- 矩形检测 (cv_lite 参数) ----
RECT_CANNY_LO     = 50
RECT_CANNY_HI     = 150
RECT_EPSILON      = 0.04
RECT_AREA_MIN     = 0.001
RECT_MAX_ANGLE    = 0.5
RECT_GAUSS_SIZE   = 5
RECT_AREA_THRESH  = 2000
RECT_LEN_THRESH   = 120
RECT_MIN_EDGE     = 30

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
