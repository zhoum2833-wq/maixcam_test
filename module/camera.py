"""
module/camera.py — 摄像头硬件封装 (MaixPy v4.12+)

纯接口层：初始化、ISP 配置、采集、释放。
API: maix.camera + maix.image

ISP 锁定（运动场景核心）:
  - 关闭 AEC/AWB → 防止运动时画面亮度漂移
  - 短曝光 (<1ms) → 消除运动模糊，代价是画面变暗（需要补光灯）
  - 固定增益 → 配合曝光锁定画面亮度
"""

from maix import camera, image
import config


class Camera:
    def __init__(self):
        self._cam = None
        self._inited = False

    def init(self, width: int = 480, height: int = 320,
             pixformat: str = "RGB888", fps: int = 80):
        """
        初始化摄像头 + 应用 ISP 锁定配置。

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

        # 应用 ISP 锁定配置
        self._apply_isp_config()

    def _apply_isp_config(self):
        """
        锁定曝光/增益/白平衡，消除运动场景亮度漂移。

        仅当 config.CAM_ISP_LOCK = True 时生效。
        调试阶段保持 False（自动曝光），比赛现场 + 补光灯再打开。
        """
        if self._cam is None:
            return
        if not getattr(config, 'CAM_ISP_LOCK', False):
            return  # 调试模式: 保持默认自动曝光

        aec = getattr(config, 'CAM_AEC_ENABLE', False)
        awb = getattr(config, 'CAM_AWB_ENABLE', False)
        exposure_us = getattr(config, 'CAM_EXPOSURE_US', 800)
        analog_gain = getattr(config, 'CAM_ANALOG_GAIN', 1.0)

        # --- AEC 模式 ---
        # maix.camera.AeMode: Auto=0 / Manual=1 (v4.12)
        try:
            mode = camera.AeMode.Auto if aec else camera.AeMode.Manual
            self._cam.exp_mode(mode)
        except Exception:
            pass

        # --- AWB 模式 ---
        # maix.camera.AwbMode: Auto=0 / Manual=1 (v4.12)
        try:
            mode = camera.AwbMode.Auto if awb else camera.AwbMode.Manual
            self._cam.awb_mode(mode)
        except Exception:
            pass

        # --- 手动曝光 (µs)，同时切到 Manual AE ---
        try:
            self._cam.exposure(exposure_us)
        except Exception:
            pass

        # --- 手动增益 ---
        try:
            self._cam.gain(int(analog_gain * 100))  # API 接受整数
        except Exception:
            pass

        # --- 亮度 / 对比度 / 饱和度 ---
        try:
            self._cam.luma(getattr(config, 'CAM_LUMA', 50))
        except Exception:
            pass
        try:
            self._cam.constrast(getattr(config, 'CAM_CONTRAST', 50))
        except Exception:
            pass
        try:
            self._cam.saturation(getattr(config, 'CAM_SATURATION', 50))
        except Exception:
            pass

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
