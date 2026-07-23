"""
module/uart.py — 串口通信模块 (MaixPy v4.12+)

发送结果包给 MSPM0，接收 MSPM0 指令。
API: maix.uart
"""

from maix import uart


class UART:
    """
    MaixCAM 串口通信封装。

    用法:
        uart = UART()
        uart.init()
        uart.send(b'hello')
        data = uart.recv(10)
        uart.deinit()
    """

    def __init__(self, device: str = "/dev/ttyS1", baudrate: int = 115200):
        """
        参数:
            device:   串口设备路径 (/dev/ttyS0, /dev/ttyS1, ...)
            baudrate: 波特率
        """
        self._device = device
        self._baudrate = baudrate
        self._uart = None
        self._inited = False

    def init(self):
        """初始化串口"""
        self._uart = uart.UART(self._device, self._baudrate)
        self._inited = True

    def send(self, data):
        """
        发送数据。

        参数:
            data: bytes 或 str
        """
        if not self._inited or self._uart is None:
            return
        if isinstance(data, str):
            self._uart.write_str(data)
        else:
            self._uart.write(data)

    def recv(self, n: int = 0) -> bytes:
        """
        接收数据。

        参数:
            n: 期望接收字节数（0 或省略 = 返回缓冲区内所有数据）

        返回:
            bytes，无数据时返回 b''
        """
        if not self._inited or self._uart is None:
            return b''
        try:
            data = self._uart.read(timeout=50)
            return data if data else b''
        except Exception:
            return b''

    def deinit(self):
        """释放串口"""
        self._uart = None
        self._inited = False

    @property
    def is_inited(self) -> bool:
        return self._inited
