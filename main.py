"""
main.py — 视觉板调度中枢 (MaixPy v4.12+)

开机自启入口。采集图像 → 运行视觉算法 → 通过串口发给 MSPM0。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import config
from module import camera, uart
from vision import rectangle, line, digit
from maix import display, app
import time


_cam = camera.Camera()
_uart = uart.UART(device=config.UART_DEVICE,
                   baudrate=config.UART_BAUDRATE)
_disp = None


def _get_disp():
    global _disp
    if _disp is None:
        _disp = display.Display()
    return _disp


def send_coord(dx: int, dy: int):
    """发送坐标偏差 [+xxxx+yyyy*]"""
    try:
        _uart.send(f"[{dx:+04d}{dy:+04d}*]")
    except Exception as e:
        print(f"[UART] send_coord 异常: {e}")


def send_none():
    try:
        _uart.send("[+999+999*]")
    except Exception as e:
        print(f"[UART] send_none 异常: {e}")


def send_result(cmd: int, val1: int = 0, val2: int = 0):
    frame = bytes([0xAA, 0xBB, cmd & 0xFF, val1 & 0xFF, val2 & 0xFF])
    try:
        _uart.send(frame)
    except Exception as e:
        print(f"[UART] send_result 异常: {e}")


def task_rectangle():
    """矩形检测任务"""
    img = _cam.capture()
    if img is None:
        print("[RECT] capture 返回 None")
        return

    # 先画个标记确认代码在跑
    img.draw_string(5, 5, f"RUN {time.time_ms() % 10000}",
                    color=(255, 255, 0), scale=1.5)

    # 诊断: 图像信息
    w, h = img.width(), img.height()
    fmt = img.format()

    # 诊断: 测试 to_numpy_ref
    try:
        img_np = img.to_numpy_ref()
        np_ok = True
    except Exception as e:
        np_ok = False
        print(f"[RECT] to_numpy_ref 异常: {e}")

    # 诊断: 检测
    result = rectangle.detect(img)

    if result:
        print(f"[RECT] ✅ 检测到 — center={result['center']} offset={result['offset']}")
        send_coord(*result['offset'])
        rectangle.draw_debug(img, result)
    else:
        print(f"[RECT] ❌ 未检测到 — w={w} h={h} fmt={fmt} np_ok={np_ok}")
        # 画十字准星 + 信息
        cx, cy = config.IMG_CENTER_X, config.IMG_CENTER_Y
        img.draw_line(cx - 20, cy, cx + 20, cy, color=(0, 0, 255), thickness=2)
        img.draw_line(cx, cy - 20, cx, cy + 20, color=(0, 0, 255), thickness=2)
        img.draw_string(5, 25, f"NO RECT {w}x{h}",
                        color=(255, 0, 0), scale=1.5)

    _get_disp().show(img)


def task_line():
    """巡线任务"""
    img = _cam.capture()
    if img is None:
        return
    lx, rx = line.track(img)
    send_result(0x01, lx, rx)


def task_digit():
    """数字识别任务"""
    img = _cam.capture()
    if img is None:
        return
    r = digit.recognize(img)
    if r:
        send_result(0x10, r.value)


def main():
    print("[MaixCAM] === 矩形检测诊断模式 ===")

    # 摄像头
    _cam.init(width=config.CAM_WIDTH,
              height=config.CAM_HEIGHT,
              pixformat=config.CAM_PIXFMT)
    print(f"[MaixCAM] camera init: {config.CAM_WIDTH}x{config.CAM_HEIGHT} {config.CAM_PIXFMT}")

    # 串口 (出错不阻塞)
    try:
        _uart.init()
        print(f"[MaixCAM] uart init: {config.UART_DEVICE}@{config.UART_BAUDRATE}")
    except Exception as e:
        print(f"[MaixCAM] uart init 失败 (忽略): {e}")

    # 诊断: cv_lite 导入
    try:
        import cv_lite
        print(f"[MaixCAM] cv_lite 可用")
    except Exception as e:
        print(f"[MaixCAM] cv_lite 不可用: {e}")

    # 测试一帧
    test_img = _cam.capture()
    if test_img:
        print(f"[MaixCAM] 测试帧: {test_img.width()}x{test_img.height()} fmt={test_img.format()}")
        try:
            np_ref = test_img.to_numpy_ref()
            print(f"[MaixCAM] to_numpy_ref: shape={np_ref.shape} dtype={np_ref.dtype}")
        except Exception as e:
            print(f"[MaixCAM] to_numpy_ref 失败: {e}")
            try:
                raw = test_img.tobytes()
                print(f"[MaixCAM] tobytes: len={len(raw)} type={type(raw)}")
            except Exception as e2:
                print(f"[MaixCAM] tobytes 也失败: {e2}")
    else:
        print("[MaixCAM] ❌ 测试帧为 None")

    print("[MaixCAM] 进入主循环...")

    try:
        while not app.need_exit():
            task_rectangle()
    except KeyboardInterrupt:
        print("[MaixCAM] user stop")
    except Exception as e:
        print(f"[MaixCAM] error: {e}")
        import sys as _sys
        _sys.print_exception(e)
    finally:
        _cam.deinit()
        _uart.deinit()
        print("[MaixCAM] deinit done")


if __name__ == "__main__":
    main()
