"""
test_camera.py — 摄像头模块上板测试 (MaixPy v4.12+)

测试 module/camera.py 的 Camera 类。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
from module.camera import Camera

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")


def test_init_default():
    print("\n--- 1. 默认参数初始化 ---")
    cam = Camera()
    cam.init()
    check("init 后 is_inited=True", cam.is_inited)
    cam.deinit()
    check("deinit 后 is_inited=False", cam.is_inited is False)


def test_capture():
    print("\n--- 2. 采集图像 ---")
    cam = Camera()
    cam.init()
    img = cam.capture()
    check("capture() 返回非 None", img is not None)
    if img is not None and hasattr(img, 'width'):
        print(f"      分辨率: {img.width()}x{img.height()}")
    cam.deinit()


def test_capture_before_init():
    print("\n--- 3. 边界: 未 init 先 capture → None")
    cam = Camera()
    check("返回 None", cam.capture() is None)


def test_capture_after_deinit():
    print("\n--- 4. 边界: deinit 后 capture → None")
    cam = Camera()
    cam.init()
    cam.deinit()
    check("返回 None", cam.capture() is None)


def test_double_init():
    print("\n--- 5. 边界: 重复 init 不崩溃")
    cam = Camera()
    cam.init()
    try:
        cam.init()
        check("不崩溃", True)
    except Exception as e:
        check("不崩溃", False, str(e))
    cam.deinit()


def test_fps():
    print("\n--- 6. FPS 测试 ---")
    cam = Camera()
    cam.init()
    n = 30
    try:
        t0 = time.ticks_ms()
    except AttributeError:
        t0 = time.time_ms()
    for i in range(n):
        if cam.capture() is None:
            check(f"第{i}帧为 None", False)
            break
    try:
        ms = time.ticks_diff(time.ticks_ms(), t0)
    except AttributeError:
        ms = (time.time_ms() - t0)
    cam.deinit()
    if ms > 0:
        fps = n * 1000 / ms
        print(f"      {n}帧 / {ms}ms = {fps:.1f} FPS")
        check("FPS > 10", fps > 10, f"实际 {fps:.1f}")


def test_gc():
    print("\n--- 7. 边界: deinit + GC 不崩溃")
    cam = Camera()
    cam.init()
    cam.deinit()
    del cam
    try:
        import gc
        gc.collect()
    except Exception:
        pass
    check("不崩溃", True)


if __name__ == "__main__":
    print("=" * 40)
    print(" test_camera.py — Camera 模块上板测试")
    print("=" * 40)

    for t in [test_init_default, test_capture, test_capture_before_init,
              test_capture_after_deinit, test_double_init, test_fps, test_gc]:
        try:
            t()
        except Exception as e:
            FAIL += 1
            print(f"  [FAIL] {t.__name__} 异常: {e}")
        try:
            time.sleep_ms(200)
        except AttributeError:
            time.sleep(0.2)

    print(f"\n{'='*40}")
    print(f" 结果: {PASS} PASS / {FAIL} FAIL / {PASS+FAIL} TOTAL")
    print(f" {'✅ 全部通过' if FAIL == 0 else f'❌ {FAIL}项失败'}")
    print(f"{'='*40}")
