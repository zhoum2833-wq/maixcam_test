"""
maixcam_modules/uart.py — 串口通信模块

发送结果包给 MSPM0，接收 MSPM0 指令。
参考: 25E题 矩形8.3.1.py 的 UART+FPIOA 初始化
"""

from machine import UART as mUART
from machine import FPIOA


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

    def __init__(self, uart_id: int = 2, baudrate: int = 115200,
                 tx_pin: int = 11, rx_pin: int = 12):
        """
        参数:
            uart_id:   串口编号 (2 = UART2)
            baudrate:  波特率
            tx_pin:    FPIOA 发送引脚
            rx_pin:    FPIOA 接收引脚
        """
        self._uart_id = uart_id
        self._baudrate = baudrate
        self._tx_pin = tx_pin
        self._rx_pin = rx_pin
        self._uart = None
        self._inited = False

    def init(self):
        """
        初始化串口: FPIOA 引脚映射 → 创建 UART 对象。

        MaixCAM 默认: PIN11→UART2_TXD, PIN12→UART2_RXD
        """
        # 1. FPIOA 引脚功能映射
        fpioa = FPIOA()
        fpioa.set_function(self._tx_pin, fpioa.UART2_TXD)
        fpioa.set_function(self._rx_pin, fpioa.UART2_RXD)

        # 2. 创建 UART 对象
        # UART2 = index 2, UART1 = index 1
        uart_index = getattr(mUART, f'UART{self._uart_id}', mUART.UART2)
        self._uart = mUART(uart_index,
                           baudrate=self._baudrate,
                           bits=mUART.EIGHTBITS,
                           parity=mUART.PARITY_NONE,
                           stop=mUART.STOPBITS_ONE)
        self._inited = True

    def send(self, data):
        """
        发送数据。

        参数:
            data: bytes 或 str（str 会自动 encode 为 utf-8）
        """
        if not self._inited or self._uart is None:
            return
        if isinstance(data, str):
            data = data.encode('utf-8')
        self._uart.write(data)

    def recv(self, n: int) -> bytes:
        """
        接收指定字节数。

        参数:
            n: 期望接收的字节数

        返回:
            bytes，超时或无数据时返回 b''
        """
        if not self._inited or self._uart is None:
            return b''
        data = self._uart.read(n)
        return data if data else b''

    def deinit(self):
        """释放串口资源"""
        if self._uart is not None:
            self._uart.deinit()
            self._uart = None
        self._inited = False

    @property
    def is_inited(self) -> bool:
        return self._inited
