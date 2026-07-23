"""
module/camera.py — 摄像头硬件封装 (MaixPy v4.12+)

纯接口层：初始化、采集、释放。
API: maix.camera + maix.image
"""

from maix import camera, image


class Camera:
    def __init__(self):
        self._cam = None
        self._inited = False

    def init(self, width: int = 480, height: int = 320,
             pixformat: str = "RGB888", fps: int = 80):
        """
        初始化摄像头。

        参数:
            width, height: 分辨率（默认 480x320）
            pixformat:     "RGB888" / "RGB565" / "GRAYSCALE"
            fps:           帧率 (30/60/80, GC4653 ≤720p 支持 80fps)
        """
        fmt_map = {
            "RGB888": image.Format.FMT_RGB888,
            "RGB565": image.Format.FMT_RGB565,
            "GRAYSCALE": image.Format.FMT_GRAYSCALE,
        }
        fmt = fmt_map.get(pixformat, image.Format.FMT_RGB888)
        self._cam = camera.Camera(width, height, fmt, fps=fps)
        self._inited = True

    def capture(self):
        """
        采集一帧图像。

        返回:
            maix.image.Image 对象，失败返回 None
        """
        if not self._inited or self._cam is None:
            return None
        try:
            return self._cam.read()
        except Exception:
            return None

    def deinit(self):
        """释放摄像头"""
        self._cam = None
        self._inited = False

    @property
    def is_inited(self) -> bool:
        return self._inited
