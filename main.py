"""
main.py — 视觉板调度中枢

采集图像 → 运行视觉算法 → 把结果通过串口发给 MSPM0

调用链路:
    main.py
      ├── module.camera    → 获取图像
      ├── vision.rectangle → 矩形检测 + 中心定位
      ├── vision.line      → 巡线偏差
      ├── vision.digit     → 数字识别
      └── module.uart      → 发送结果包给 MSPM0

参考: 25E题 矩形8.3.1.py 主循环 / 开源项目 main.py 任务调度
"""

import time
import config
from module import camera, uart
from vision import rectangle, line, digit


# ---- 全局设备 ----
_cam = camera.Camera()
_uart = uart.UART(uart_id=config.UART_ID,
                   baudrate=config.UART_BAUDRATE,
                   tx_pin=config.UART_TX_PIN,
                   rx_pin=config.UART_RX_PIN)


def send_coord(offset_x: int, offset_y: int):
    """
    发送坐标偏差到 MSPM0。
    格式: [+xxxx+yyyy*] （参考 矩形8.3.1.py L308-313）
    """
    msg = f"[{offset_x:+04d}{offset_y:+04d}*]"
    _uart.send(msg)


def send_none():
    """未检测到目标时发送无效坐标"""
    _uart.send("[+999+999*]")


def send_result(cmd: int, val1: int = 0, val2: int = 0):
    """发送结果包给 MSPM0（协议见 smart_car_docs/protocol_uart.md）"""
    frame = bytes([0xAA, 0xBB, cmd & 0xFF, val1 & 0xFF, val2 & 0xFF])
    _uart.send(frame)


def task_rectangle():
    """
    矩形检测任务 — 赛题"矩形中心定位"。
    检测图像中的矩形，计算中心偏差，通过串口发送。
    """
    img = _cam.capture()
    if img is None:
        return

    result = rectangle.detect(img)
    if result:
        dx, dy = result['offset']
        send_coord(dx, dy)

        # 调试: 绘制结果到屏幕
        rectangle.draw_debug(img, result)
    else:
        send_none()

    from media.display import Display
    Display.show_image(img)


def task_line():
    """巡线任务"""
    img = _cam.capture()
    if img is None:
        return

    left_x, right_x = line.track(img)
    send_result(0x01, left_x, right_x)


def task_digit():
    """数字识别任务"""
    img = _cam.capture()
    if img is None:
        return

    result = digit.recognize(img)
    if result:
        send_result(0x10, result.value)


def main():
    """主循环"""
    _cam.init(width=config.CAM_WIDTH,
              height=config.CAM_HEIGHT,
              pixformat=config.CAM_PIXFMT,
              disp_width=config.DISP_WIDTH,
              disp_height=config.DISP_HEIGHT,
              fps=config.CAM_FPS,
              to_ide=config.CAM_TO_IDE)
    _uart.init()

    print("[MaixCAM] vision ready")

    fps_clock = time.clock()

    try:
        while True:
            fps_clock.tick()

            # TODO: 赛时根据按键/指令选择任务
            # 当前默认: 矩形检测
            task_rectangle()

            print(f"fps: {fps_clock.fps():.1f}")

    except KeyboardInterrupt:
        print("[MaixCAM] user stop")
    finally:
        _cam.deinit()
        _uart.deinit()
        print("[MaixCAM] deinit done")


if __name__ == "__main__":
    main()
