"""
test/test_ball.py — 钢球 YOLOv5s 模型测试脚本

用法（在 MaixCAM Pro 上）:
    cd /root/maixcam_test
    python test/test_ball.py

测试内容:
    1. 模型加载（.cvimodel 通过 .mud 加载）
    2. 单张图片推理
    3. 连续帧 FPS 摸底
    4. 串口输出验证

注意: 此脚本只在 MaixCAM Pro 硬件上运行，PC 端无法执行。
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from maix import camera, display, image, nn, app
import config


# ============================================================
#  测试配置
# ============================================================
MODEL_PATH   = "model/ball.model/model_295152.mud"
TEST_ROUNDS  = 100          # FPS 测试帧数
CONF_THRESH  = 0.45
IOU_THRESH   = 0.45
# ============================================================


def test_model_load():
    """测试 1: 模型加载"""
    print("\n" + "=" * 50)
    print("[TEST 1] 模型加载")
    print("=" * 50)

    import os as _os
    if not _os.path.exists(MODEL_PATH):
        # 尝试 MaixHub 默认路径
        alt_path = "/root/models/maixhub/295152/model_295152.mud"
        print(f"  ❌ 模型文件不存在: {MODEL_PATH}")
        print(f"     尝试备用路径: {alt_path}")
        if _os.path.exists(alt_path):
            model_path = alt_path
        else:
            print(f"  ❌ 备用路径也不存在！请先部署模型文件。")
            return None
    else:
        model_path = MODEL_PATH
        print(f"  ✅ 模型文件存在: {model_path}")

    try:
        t0 = time.time()
        detector = nn.YOLOv5(model=model_path)
        dt = (time.time() - t0) * 1000
        print(f"  ✅ 模型加载成功 ({dt:.0f}ms)")
        print(f"     labels: {detector.labels}")
        print(f"     input:  {detector.input_width()}×{detector.input_height()} "
              f"fmt={detector.input_format()}")
        return detector
    except Exception as e:
        print(f"  ❌ 模型加载失败: {e}")
        return None


def test_single_image(detector, img):
    """测试 2: 单张推理"""
    print("\n" + "=" * 50)
    print("[TEST 2] 单张推理")
    print("=" * 50)

    if img is None:
        print("  ❌ 图像为空，跳过")
        return

    print(f"  image: {img.width()}×{img.height()} fmt={img.format()}")

    try:
        t0 = time.time()
        objs = detector.detect(img, conf_th=CONF_THRESH, iou_th=IOU_THRESH)
        dt = (time.time() - t0) * 1000

        print(f"  推理耗时: {dt:.1f}ms")
        print(f"  检测结果: {len(objs)} 个目标")

        for i, obj in enumerate(objs):
            label = detector.labels[obj.class_id] if detector.labels else f"cls_{obj.class_id}"
            print(f"    [{i}] {label}: score={obj.score:.3f} "
                  f"bbox=({obj.x},{obj.y},{obj.w},{obj.h}) "
                  f"center=({int(obj.x+obj.w/2)},{int(obj.y+obj.h/2)})")
        return objs
    except Exception as e:
        print(f"  ❌ 推理失败: {e}")
        return None


def test_fps(detector, cam):
    """测试 3: 连续帧 FPS（关画面、关串口）"""
    print("\n" + "=" * 50)
    print(f"[TEST 3] 连续 {TEST_ROUNDS} 帧 FPS 摸底")
    print("=" * 50)
    print("  (不推画面、不发串口，纯算法测速)")

    # 预热
    for _ in range(10):
        img = cam.read()
        if img:
            detector.detect(img, conf_th=CONF_THRESH, iou_th=IOU_THRESH)

    # 正式测试
    t0 = time.time()
    n_detected = 0
    for i in range(TEST_ROUNDS):
        img = cam.read()
        if img is None:
            continue
        objs = detector.detect(img, conf_th=CONF_THRESH, iou_th=IOU_THRESH)
        if objs:
            n_detected += 1

    dt = time.time() - t0
    fps = TEST_ROUNDS / dt
    avg_ms = dt / TEST_ROUNDS * 1000

    print(f"  总耗时: {dt:.2f}s")
    print(f"  平均 FPS: {fps:.1f}")
    print(f"  平均每帧: {avg_ms:.1f}ms")
    print(f"  检出率:   {n_detected}/{TEST_ROUNDS} ({100*n_detected/TEST_ROUNDS:.0f}%)")

    return fps


def main():
    print("=" * 50)
    print("  钢球 YOLOv5s 模型测试")
    print(f"  模型: {MODEL_PATH}")
    print(f"  阈值: conf={CONF_THRESH} iou={IOU_THRESH}")
    print("=" * 50)

    # -- 测试 1: 加载模型 --
    detector = test_model_load()
    if detector is None:
        print("\n❌ 模型加载失败，终止测试。")
        return

    # -- 测试 2: 单张推理（摄像头实时取一帧） --
    cam = camera.Camera(
        detector.input_width(),
        detector.input_height(),
        detector.input_format()
    )
    print(f"\n  摄像头: {detector.input_width()}×{detector.input_height()}")

    img = cam.read()
    objs = test_single_image(detector, img)

    # -- 测试 3: FPS --
    fps = test_fps(detector, cam)

    # -- 测试 4: 带绘图的推理（手动确认画面） --
    print("\n" + "=" * 50)
    print("[TEST 4] 带绘图预览（10 帧，观察 MaixVision 画面）")
    print("=" * 50)

    disp = display.Display()
    red = image.Color.from_rgb(255, 0, 0)
    yellow = image.Color.from_rgb(255, 255, 0)

    for i in range(10):
        img = cam.read()
        if img is None:
            continue
        objs = detector.detect(img, conf_th=CONF_THRESH, iou_th=IOU_THRESH)

        for obj in objs:
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=yellow, thickness=2)
            cx, cy = int(obj.x + obj.w / 2), int(obj.y + obj.h / 2)
            img.draw_circle(cx, cy, 3, color=red, thickness=3)
            label = f"{detector.labels[obj.class_id]}: {obj.score:.2f}"
            img.draw_string(obj.x, max(obj.y - 14, 0), label, color=yellow, scale=1.2)

        img.draw_string(5, 5, f"FPS:{fps:.0f} frame:{i+1}/10", color=red, scale=1.5)
        disp.show(img)
        time.sleep(0.1)

    cam.deinit()
    print("\n✅ 全部测试完成")
    print(f"   模型 FPS: {fps:.0f}")
    print(f"   如果 FPS < 30，考虑缩小摄像头分辨率或降低 conf_th")


if __name__ == "__main__":
    main()
