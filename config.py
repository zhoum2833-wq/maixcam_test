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

# ---- 矩形检测 (img.find_rects) ----
RECT_THRESHOLD    = 12000            # find_rects 阈值（越大越严格，默认 10000）
RECT_AREA_THRESH  = 2000             # 最小面积（像素）
RECT_ASPECT_MAX   = 5.0              # 最大长宽比（超过视为噪声）

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
