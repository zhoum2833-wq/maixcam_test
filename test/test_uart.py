"""
test_uart.py — 串口模块上板测试 (MaixPy v4.12+)

测试 module/uart.py 的 UART 类。

⚠️ 完整收发测试需外接设备，当前只验证"不崩溃"。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
from module.uart import UART

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
    u = UART()
    try:
        u.init()
        check("init 后 is_inited=True", u.is_inited)
    except Exception as e:
        check("init 不抛异常", False, str(e))
    finally:
        u.deinit()
    check("deinit 后 is_inited=False", u.is_inited is False)


def test_send_recv_before_init():
    print("\n--- 2. 边界: 未 init 先 send/recv")
    u = UART()
    try:
        u.send(b"hello")
        check("send 不崩溃", True)
    except Exception as e:
        check("send 不崩溃", False, str(e))
    check("recv 返回 b''", u.recv() == b"", f"实际: {u.recv()}")


def test_send_recv_after_deinit():
    print("\n--- 3. 边界: deinit 后 send/recv")
    u = UART()
    u.init()
    u.deinit()
    try:
        u.send(b"hello")
        check("send 不崩溃", True)
    except Exception as e:
        check("send 不崩溃", False, str(e))
    check("recv 返回 b''", u.recv() == b"")


def test_double_init():
    print("\n--- 4. 边界: 重复 init")
    u = UART()
    u.init()
    try:
        u.init()
        check("不崩溃", True)
    except Exception as e:
        check("不崩溃", False, str(e))
    u.deinit()


def test_send_types():
    print("\n--- 5. send 支持 bytes / str")
    u = UART()
    u.init()
    try:
        u.send(b"\xAA\xBB\x01")
        check("send(bytes)", True)
    except Exception as e:
        check("send(bytes)", False, str(e))
    try:
        u.send("[+012-034*]")
        check("send(str)", True)
    except Exception as e:
        check("send(str)", False, str(e))
    u.deinit()


def test_recv_timeout():
    print("\n--- 6. recv 无数据时返回 b''")
    u = UART()
    u.init()
    try:
        t0 = time.ticks_ms()
    except AttributeError:
        t0 = time.time_ms()
    data = u.recv()
    try:
        ms = time.ticks_diff(time.ticks_ms(), t0)
    except AttributeError:
        ms = time.time_ms() - t0
    check("recv 返回 b''", data == b"", f"实际: {data}")
    print(f"      等待 {ms}ms（应 < 2000ms）")
    check("不长时间阻塞", ms < 2000, f"阻塞 {ms}ms")
    u.deinit()


def test_format_output():
    print("\n--- 7. 协议格式输出 ---")
    u = UART()
    u.init()
    for data, desc in [
        ("[+012-034*]", "正偏差"),
        ("[+999+999*]", "无效信号"),
    ]:
        try:
            u.send(data)
            check(f"send '{desc}'", True)
        except Exception as e:
            check(f"send '{desc}'", False, str(e))
    u.deinit()


if __name__ == "__main__":
    print("=" * 40)
    print(" test_uart.py — UART 模块上板测试")
    print("=" * 40)

    for t in [test_init_default, test_send_recv_before_init,
              test_send_recv_after_deinit, test_double_init,
              test_send_types, test_recv_timeout, test_format_output]:
        try:
            t()
        except Exception as e:
            FAIL += 1
            print(f"  [FAIL] {t.__name__} 异常: {e}")
        try:
            time.sleep_ms(100)
        except AttributeError:
            time.sleep(0.1)

    print(f"\n{'='*40}")
    print(f" 结果: {PASS} PASS / {FAIL} FAIL / {PASS+FAIL} TOTAL")
    if FAIL == 0:
        print(" ✅ 全部通过（功能不崩溃）")
    else:
        print(f" ❌ {FAIL} 项失败")
    print(f"{'='*40}")
