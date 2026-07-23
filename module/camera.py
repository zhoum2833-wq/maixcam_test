"""
maixcam_modules/camera.py — 摄像头硬件封装

纯接口层：初始化、采集、释放。
不包含任何图像处理算法。

参考: 25E题 矩形8.3.1.py 的 camera_init / camera_deinit / capture 流程
"""

from media.sensor import Sensor
from media.display import Display
from media.media import MediaManager


class Camera:
    def __init__(self):
        self._sensor = None
        self._inited = False

    def init(self, width: int = 480, height: int = 320,
             pixformat: str = "RGB888",
             disp_width: int = 800, disp_height: int = 480,
             fps: int = 100, to_ide: bool = True):
        """
        初始化摄像头、屏幕和媒体管理器。

        参数:
            width, height:  传感器分辨率（默认 480x320）
            pixformat:      像素格式 "RGB565" / "RGB888"
            disp_width, disp_height: 屏幕分辨率
            fps:            显示帧率
            to_ide:         是否输出到 IDE 屏幕
        """
        # 1. 传感器
        self._sensor = Sensor()
        self._sensor.reset()
        self._sensor.set_framesize(width=width, height=height)

        fmt = Sensor.RGB888 if pixformat == "RGB888" else Sensor.RGB565
        self._sensor.set_pixformat(fmt)

        # 2. 屏幕 (to_ide=True 时输出到 IDE 显示)
        Display.init(Display.ST7701, width=disp_width, height=disp_height,
                     fps=fps, to_ide=to_ide)

        # 3. 媒体管理器 + 启动传感器
        MediaManager.init()
        self._sensor.run()
        self._inited = True

    def capture(self):
        """
        采集一帧图像。

        返回:
            image 对象，失败返回 None
        """
        if not self._inited or self._sensor is None:
            return None
        try:
            return self._sensor.snapshot()
        except Exception:
            return None

    def deinit(self):
        """
        释放摄像头、屏幕和媒体管理器。
        顺序: 停止传感器 → 释放屏幕 → 释放媒体管理器
        """
        if self._sensor is not None:
            self._sensor.stop()
            self._sensor = None
        Display.deinit()
        MediaManager.deinit()
        self._inited = False

    @property
    def is_inited(self) -> bool:
        return self._inited
