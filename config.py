"""
config.py — 全局配置

比赛现场主要改这个文件。
"""

# ---- 串口 ----
UART_PORT         = "/dev/ttyS1"     # 与 MSPM0 通信的串口
UART_BAUDRATE     = 115200
UART_RX_BUF       = 256

# ---- 摄像头 ----
CAM_RESOLUTION    = (320, 240)        # QQVGA
CAM_FPS           = 60
CAM_ROTATE        = 0                 # 旋转角度 (0 / 90 / 180 / 270)

# ---- 巡线 ----
LINE_ROI          = (0, 120, 320, 80) # 巡线 ROI (x, y, w, h)
LINE_THRESH_BW    = 128               # 二值化阈值
LINE_MIN_WIDTH    = 3                 # 最小线宽

# ---- 识别 ----
DIGIT_CONF_MIN    = 0.6               # 数字识别最低置信度
MODEL_PATH        = "model/digit.tflite"
