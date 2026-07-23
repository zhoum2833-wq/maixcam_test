"""
config.py — 全局配置

比赛现场主要改这个文件。
参考: 25E题 矩形8.3.1.py 的可调参数 / 开源项目 configs.py
"""

# ---- 串口 (UART2 → MSPM0) ----
UART_ID           = 2                 # UART2 与 MSPM0 通信
UART_BAUDRATE     = 115200
UART_TX_PIN       = 11                # FPIOA 映射: PIN11 → UART2_TXD
UART_RX_PIN       = 12                # FPIOA 映射: PIN12 → UART2_RXD
UART_RX_BUF       = 256

# ---- 摄像头 ----
CAM_WIDTH         = 480               # 传感器宽度
CAM_HEIGHT        = 320               # 传感器高度
CAM_PIXFMT        = "RGB888"          # 像素格式 (RGB565 / RGB888)
CAM_FPS           = 100               # 显示帧率
CAM_TO_IDE        = True              # True=输出到 IDE 屏幕, False=LCD 本地显示

# ---- 屏幕 ----
DISP_WIDTH        = 800               # 屏幕宽度 (16 对齐)
DISP_HEIGHT       = 480               # 屏幕高度

# ---- 矩形检测 (cv_lite 参数, 参考 矩形8.3.1.py) ----
RECT_CANNY_LO     = 50                # Canny 边缘检测低阈值
RECT_CANNY_HI     = 150               # Canny 边缘检测高阈值
RECT_EPSILON      = 0.04              # 多边形拟合精度（比例）
RECT_AREA_MIN     = 0.001             # 最小面积比例（0~1）
RECT_MAX_ANGLE    = 0.5               # 最大角余弦（越小越接近矩形）
RECT_GAUSS_SIZE   = 5                 # 高斯模糊核大小（奇数）
RECT_AREA_THRESH  = 2000              # 矩形面积阈值（小于此值忽略）
RECT_LEN_THRESH   = 120               # 对边差值阈值
RECT_MIN_EDGE     = 30                # 最短边长

# ---- 图像中心参考点 ----
IMG_CENTER_X      = 240               # CAM_WIDTH / 2
IMG_CENTER_Y      = 160               # CAM_HEIGHT / 2

# ---- 激光笔 ----
LASER_PIN         = 17                # 激光笔 GPIO 引脚

# ---- 巡线 ----
LINE_ROI          = (0, 120, 320, 80) # 巡线 ROI (x, y, w, h)
LINE_THRESH_BW    = 128               # 二值化阈值
LINE_MIN_WIDTH    = 3                 # 最小线宽

# ---- 识别 ----
DIGIT_CONF_MIN    = 0.6               # 数字识别最低置信度
MODEL_PATH        = "model/digit.tflite"
