"""
maixcam_modules/uart.py — 串口通信模块

发送结果包给 MSPM0，接收 MSPM0 指令。
协议定义见 smart_car_docs/protocol_uart.md。
"""


class UART:
    def __init__(self, port: int, baudrate: int = 115200):
        self._port = port
        self._baudrate = baudrate
        self._inited = False

    def init(self):
        """初始化串口"""
        # TODO: MaixPy UART init
        # from machine import UART as mUART
        # self._uart = mUART(self._port, self._baudrate)
        self._inited = True

    def send(self, data: bytes):
        """发送字节数据"""
        # self._uart.write(data)
        pass

    def recv(self, n: int) -> bytes:
        """接收 n 字节"""
        # return self._uart.read(n)
        return b''
