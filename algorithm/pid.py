"""
algorithm/pid.py — PID 控制器

平台无关的纯 Python 实现。
移植自: 25E题开源项目 Algorithm/PID.py
"""


class PID:
    """
    离散 PID 控制器。

    用法:
        pid = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=0)
        output = pid.update(current_value)
    """

    def __init__(self, Kp: float, Ki: float, Kd: float,
                 setpoint: float = 0.0,
                 max_integral: float = 100.0,
                 min_integral: float = -100.0):
        """
        参数:
            Kp:            比例增益
            Ki:            积分增益
            Kd:            微分增益
            setpoint:      目标值（期望值）
            max_integral:  积分上限（防止积分饱和）
            min_integral:  积分下限（防止积分饱和）
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint

        self.prev_error = 0.0
        self.integral = 0.0
        self.output = 0.0

        self.max_integral = max_integral
        self.min_integral = min_integral

    def update(self, current_value: float) -> float:
        """
        输入当前值，返回 PID 控制输出。

        参数:
            current_value: 当前测量值

        返回:
            控制输出值
        """
        # 误差
        error = self.setpoint - current_value

        # 积分项（带限幅）
        self.integral += error
        if self.integral > self.max_integral:
            self.integral = self.max_integral
        elif self.integral < self.min_integral:
            self.integral = self.min_integral

        # 微分项
        derivative = error - self.prev_error

        # PID 输出
        self.output = (self.Kp * error +
                       self.Ki * self.integral +
                       self.Kd * derivative)

        self.prev_error = error
        return self.output

    def reset(self, setpoint: float = None):
        """
        重置 PID 状态。

        参数:
            setpoint: 可选的新目标值
        """
        if setpoint is not None:
            self.setpoint = setpoint
        self.prev_error = 0.0
        self.integral = 0.0
        self.output = 0.0

    def set_setpoint(self, setpoint: float):
        """更新目标值并重置积分项"""
        self.reset(setpoint)
