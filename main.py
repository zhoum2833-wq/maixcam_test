"""
main.py — 视觉板调度中枢 (MaixPy v4.12+)

开机自启入口。采集图像 → 运行视觉算法 → 通过串口发给 MSPM0。

===== 调试模式 vs 生产模式 =====
  DEBUG_DRAW = True   → 画框、画线、FPS 叠加、隔帧推画面（调试用）
  DEBUG_DRAW = False  → 不画任何东西，不推画面，只跑算法 + 串口（测真实帧率用）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import time
import config
from module import camera, uart
from vision import rectangle, line, digit
from maix import display, app, image


# ============================================================
#  调试开关（比赛前设为 False）
# ============================================================
DEBUG_DRAW   = False   # 关画面，测裸算法帧率
SHOW_EVERY_N = 2        # 隔 N 帧推一次画面到 MaixVision
PRINT_EVERY_N = 30      # 隔 N 帧打印一次 FPS + 分段计时
# ============================================================

# ============================================================
#  性能参数
# ============================================================
DETECT_W, DETECT_H = 320, 240   # 原生分辨率，cam.read() 只要 1ms
UART_THRESH = 5                  # 坐标变化超过此像素才发送，减少串口阻塞
# ============================================================


_cam = camera.Camera()
_uart = uart.UART(device=config.UART_DEVICE,
                   baudrate=config.UART_BAUDRATE)
_disp = None
_n = 0
_t0 = 0.0
_fps = 0.0

# 上一次发送的坐标（用于 UART 去重）
_last_tx, _last_ty = 999, 999

# 预创建颜色对象（避免每帧重复创建）
_RED   = image.Color.from_rgb(255, 0, 0)
_GREEN = image.Color.from_rgb(0, 255, 0)
_BLUE  = image.Color.from_rgb(0, 0, 255)
_YELLOW = image.Color.from_rgb(255, 255, 0)


def _get_disp():
    global _disp
    if _disp is None:
        _disp = display.Display()
    return _disp


def uart_send_coord(dx: int, dy: int):
    """坐标变化超过阈值才发送，减少串口阻塞"""
    global _last_tx, _last_ty
    if abs(dx - _last_tx) >= UART_THRESH or abs(dy - _last_ty) >= UART_THRESH:
        _last_tx, _last_ty = dx, dy
        try:
            _uart.send(f"[{dx:+04d}{dy:+04d}*]")
        except Exception as e:
            print(f"[UART] send err: {e}")


def uart_send_none():
    """丢目标时只发一次，不重复发送"""
    global _last_tx, _last_ty
    if (_last_tx, _last_ty) == (999, 999):
        return  # 已经发过 none 了
    _last_tx, _last_ty = 999, 999
    try:
        _uart.send("[+999+999*]")
    except Exception as e:
        print(f"[UART] send err: {e}")


def task_rectangle(img):
    """矩形检测 — 只做检测 + 串口，绘图由主循环控制"""
    global _n
    _n += 1

    result = rectangle.detect(img)

    if result:
        uart_send_coord(*result['offset'])
    else:
        uart_send_none()

    return result


def main():
    global _t0, _fps, _last_tx, _last_ty

    print("[MaixCAM] === vision start ===")
    print(f"[MaixCAM] DEBUG_DRAW={DEBUG_DRAW} SHOW_EVERY_N={SHOW_EVERY_N}")
    print(f"[MaixCAM] detect: {DETECT_W}x{DETECT_H}  uart_thresh:{UART_THRESH}px")

    _cam.init(width=DETECT_W, height=DETECT_H, pixformat=config.CAM_PIXFMT)

    try:
        _uart.init()
        print(f"[MaixCAM] uart: {config.UART_DEVICE}@{config.UART_BAUDRATE}")
    except Exception as e:
        print(f"[MaixCAM] uart init fail (ignore): {e}")

    # 预热
    for _ in range(10):
        _cam.capture()
        time.sleep(0.02)

    _t0 = time.time()
    print("[MaixCAM] loop start")

    # 图像中心参考点（跟随检测分辨率）
    img_cx = DETECT_W // 2
    img_cy = DETECT_H // 2

    try:
        while not app.need_exit():
            t0 = time.time()
            img = _cam.capture()
            t_cap = time.time()
            if img is None:
                continue

            result = task_rectangle(img)
            t_detect = time.time()

            if DEBUG_DRAW:
                if result:
                    rectangle.draw_debug(img, result)
                else:
                    img.draw_line(img_cx - 20, img_cy, img_cx + 20, img_cy, color=_BLUE, thickness=2)
                    img.draw_line(img_cx, img_cy - 20, img_cx, img_cy + 20, color=_BLUE, thickness=2)
                    img.draw_string(5, 5, f"NO RECT #{_n}", color=_RED, scale=1.5)

                img.draw_string(img.width() - 80, 5, f"FPS:{_fps:.0f}",
                                color=_GREEN, scale=1.5)

                if _n % SHOW_EVERY_N == 0:
                    _get_disp().show(img)
            t_draw = time.time()

            # 分段计时打印
            if _n % PRINT_EVERY_N == 0:
                t1 = time.time()
                _fps = PRINT_EVERY_N / (t1 - _t0 + 0.001)
                _t0 = t1
                dt_cap    = (t_cap    - t0)      * 1000
                dt_detect = (t_detect - t_cap)    * 1000
                dt_draw   = (t_draw   - t_detect) * 1000
                dt_total  = (t_draw   - t0)       * 1000
                print(f"[FPS] {_fps:.1f}  total:{dt_total:.1f}ms | cap:{dt_cap:.1f} detect:{dt_detect:.1f} draw:{dt_draw:.1f}")

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
