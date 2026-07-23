"""
vision/line.py — 巡线算法

纯算法层：接收图像 → 计算线位置偏差。
不直接访问任何硬件（摄像头、串口）。
"""

import config


def track(img) -> tuple:
    """
    巡线：二值化 + 寻找黑线。

    参数:
        img: 摄像头采集的图像对象

    返回:
        (left_x, right_x)  左右线在图像中的 x 坐标
        (0, 0)             未检测到线
    """
    # TODO: 现场实现
    # 1. 裁剪 ROI 区域
    # roi = img.crop(config.LINE_ROI)
    # 2. 二值化
    # roi.binary([config.LINE_THRESH_BW])
    # 3. 找线（连通域 / 边缘检测 / 线性回归）
    # 4. 返回左右线中点坐标
    return (0, 0)


def compute_steering(left: int, right: int, img_w: int) -> float:
    """
    从左右线坐标计算转向偏差。

    返回:
        -1000 ~ +1000   (0=正中, 负=偏左, 正=偏右)
    """
    if left == 0 and right == 0:
        return 0.0
    center = (left + right) / 2.0
    mid = img_w / 2.0
    return (center - mid) / mid * 1000.0
