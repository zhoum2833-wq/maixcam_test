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
from maix import display, app, image


_cam = camera.Camera()
_uart = uart.UART(device=config.UART_DEVICE,
                   baudrate=config.UART_BAUDRATE)
_disp = None
_frame_count = 0


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
        print(f"[UART] send_coord err: {e}")


def send_none():
    try:
        _uart.send("[+999+999*]")
    except Exception as e:
        print(f"[UART] send_none err: {e}")


def send_result(cmd: int, val1: int = 0, val2: int = 0):
    frame = bytes([0xAA, 0xBB, cmd & 0xFF, val1 & 0xFF, val2 & 0xFF])
    try:
        _uart.send(frame)
    except Exception as e:
        print(f"[UART] send_result err: {e}")


def task_rectangle():
    """矩形检测任务"""
    global _frame_count
    img = _cam.capture()
    if img is None:
        print("[RECT] capture None")
        return

    _frame_count += 1
    w, h = img.width(), img.height()

    result = rectangle.detect(img)

    if result:
        send_coord(*result['offset'])
        rectangle.draw_debug(img, result)
        if _frame_count % 30 == 1:
            print(f"[RECT] #{_frame_count} center={result['center']} offset={result['offset']}")
    else:
        send_none()
        # 没检测到时画十字参考线
        red = image.Color.from_rgb(255, 0, 0)
        blue = image.Color.from_rgb(0, 0, 255)
        cx, cy = config.IMG_CENTER_X, config.IMG_CENTER_Y
        img.draw_line(cx - 20, cy, cx + 20, cy, color=blue, thickness=2)
        img.draw_line(cx, cy - 20, cx, cy + 20, color=blue, thickness=2)
        img.draw_string(5, 5, f"NO RECT #{_frame_count}",
                        color=red, scale=1.5)
        if _frame_count % 30 == 1:
            print(f"[RECT] #{_frame_count} no rect w={w} h={h}")

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
    print("[MaixCAM] === vision start ===")

    # 摄像头
    _cam.init(width=config.CAM_WIDTH,
              height=config.CAM_HEIGHT,
              pixformat=config.CAM_PIXFMT)
    print(f"[MaixCAM] camera: {config.CAM_WIDTH}x{config.CAM_HEIGHT} {config.CAM_PIXFMT}")

    # 串口 (出错不阻塞)
    try:
        _uart.init()
        print(f"[MaixCAM] uart: {config.UART_DEVICE}@{config.UART_BAUDRATE}")
    except Exception as e:
        print(f"[MaixCAM] uart init fail (ignore): {e}")

    # 测试一帧
    test_img = _cam.capture()
    if test_img:
        print(f"[MaixCAM] test frame: {test_img.width()}x{test_img.height()}")
        # 测试 find_rects
        try:
            test_rects = test_img.find_rects(threshold=config.RECT_THRESHOLD)
            print(f"[MaixCAM] find_rects: {len(test_rects) if test_rects else 0} rects")
        except Exception as e:
            print(f"[MaixCAM] find_rects err: {e}")
    else:
        print("[MaixCAM] test frame None!")

    print("[MaixCAM] loop start")

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
