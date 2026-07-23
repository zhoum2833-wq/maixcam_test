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
    _uart.send(f"[{dx:+04d}{dy:+04d}*]")


def send_none():
    _uart.send("[+999+999*]")


def send_result(cmd: int, val1: int = 0, val2: int = 0):
    frame = bytes([0xAA, 0xBB, cmd & 0xFF, val1 & 0xFF, val2 & 0xFF])
    _uart.send(frame)


def task_rectangle():
    """矩形检测任务"""
    img = _cam.capture()
    if img is None:
        return
    result = rectangle.detect(img)
    if result:
        send_coord(*result['offset'])
        rectangle.draw_debug(img, result)
    else:
        send_none()
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
    _cam.init(width=config.CAM_WIDTH,
              height=config.CAM_HEIGHT,
              pixformat=config.CAM_PIXFMT)
    _uart.init()
    print("[MaixCAM] vision ready")

    try:
        while not app.need_exit():
            task_rectangle()
    except KeyboardInterrupt:
        print("[MaixCAM] user stop")
    except Exception as e:
        print(f"[MaixCAM] error: {e}")
    finally:
        _cam.deinit()
        _uart.deinit()
        print("[MaixCAM] deinit done")


if __name__ == "__main__":
    main()
