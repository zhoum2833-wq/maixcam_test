"""
vision/digit.py — 数字 / 标志识别

纯算法层：接收图像 → 返回识别结果。
依赖 model/ 下的模型文件。
"""

import config


def recognize(img) -> object:
    """
    识别图像中的数字或标志。

    参数:
        img: 摄像头采集的图像对象

    返回:
        result.value        识别的数字 (0=未识别)
        result.confidence   置信度 (0.0 ~ 1.0)
    """
    # TODO: 现场实现
    # 1. 预处理（缩放、灰度化）
    # 2. 加载模型 → model/digit.tflite
    # 3. 推理
    # 4. 返回结果
    return None
