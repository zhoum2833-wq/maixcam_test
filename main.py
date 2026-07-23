"""
main.py — 视觉板调度中枢

采集图像 → 运行视觉算法 → 把结果通过串口发给 MSPM0

调用链路:
    main.py
      ├── module.camera → 获取图像
      ├── vision.line   → 巡线偏差
      ├── vision.digit  → 数字识别
      └── module.uart   → 发送结果包给 MSPM0
"""

import config
from module import camera, uart
from vision import line, digit


def send_result(cmd: int, val1: int = 0, val2: int = 0):
    """发送结果包给 MSPM0（协议见 smart_car_docs/protocol_uart.md）"""
    # TODO: 按协议打包发送
    frame = bytes([0xAA, 0xBB, cmd & 0xFF, val1 & 0xFF, val2 & 0xFF])
    uart.send(frame)


def main():
    """主循环 — TODO: 现场填空"""
    camera.init()
    uart.init()

    print("[MaixCAM] vision ready")

    while True:
        # 1. 读摄像头
        img = camera.capture()
        if img is None:
            continue

        # 2. 运行视觉算法
        # TODO: 根据赛题选择算法
        # lr = line.track(img)          # 巡线 → (left, right)
        # d  = digit.recognize(img)      # 数字识别
        # if d:
        #     send_result(0x10, d.value)

        # 3. 发送给 MSPM0
        # send_result(0x01, lr[0], lr[1])

        pass


if __name__ == "__main__":
    main()
