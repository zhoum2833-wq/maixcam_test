"""
maixcam_modules/camera.py — 摄像头硬件封装

纯接口层：初始化、采集、释放。
不包含任何图像处理算法。
"""


class Camera:
    def __init__(self):
        self._inited = False

    def init(self):
        """初始化摄像头"""
        # TODO: MaixPy camera init
        # import sensor
        # sensor.reset()
        # sensor.set_pixformat(sensor.RGB565)
        # sensor.set_framesize(sensor.QVGA)
        self._inited = True

    def capture(self):
        """采集一帧图像，返回 image 对象或 None"""
        # TODO: return sensor.snapshot()
        pass

    def deinit(self):
        """释放摄像头"""
        self._inited = False
