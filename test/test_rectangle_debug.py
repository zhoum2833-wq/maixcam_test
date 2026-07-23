"""
test_rectangle_debug.py — 矩形检测逐步诊断 (自包含，不依赖项目导入)

直接复制到 MaixVision 运行即可。
"""

from maix import camera, display, image, app
import time

# ---- 本地配置 ----
CAM_WIDTH = 480
CAM_HEIGHT = 320
CAM_PIXFMT = "RGB888"
IMG_CENTER_X = 240
IMG_CENTER_Y = 160

RECT_CANNY_LO = 50
RECT_CANNY_HI = 150
RECT_EPSILON = 0.04
RECT_AREA_MIN = 0.001
RECT_MAX_ANGLE = 0.5
RECT_GAUSS_SIZE = 5

cam = None
disp = None

print("[1] 初始化摄像头...")
cam = camera.Camera(CAM_WIDTH, CAM_HEIGHT, image.Format.FMT_RGB888)
print(f"    OK — {CAM_WIDTH}x{CAM_HEIGHT} {CAM_PIXFMT}")

print("[2] 采集一帧...")
img = cam.read()
print(f"    返回类型: {type(img)}")
if img is None:
    print("    ❌ img 为 None！")
    exit()
print(f"    分辨率: {img.width()}x{img.height()}")
print(f"    格式: {img.format()}")

# --- 测试 to_numpy_ref ---
print("[3] 测试 img.to_numpy_ref()...")
has_numpy_ref = False
try:
    img_np = img.to_numpy_ref()
    print(f"    类型: {type(img_np)}, shape: {img_np.shape}, dtype: {img_np.dtype}")
    has_numpy_ref = True
except AttributeError:
    print("    ❌ to_numpy_ref() 不存在")
except Exception as e:
    print(f"    ❌ 异常: {e}")

# --- 测试 tobytes ---
print("[4] 测试 img.tobytes()...")
try:
    raw = img.tobytes()
    print(f"    类型: {type(raw)}, len: {len(raw)}")
except Exception as e:
    print(f"    ❌ 异常: {e}")

# --- 测试 cv_lite 导入 ---
print("[5] 测试 import cv_lite...")
try:
    import cv_lite
    print(f"    OK — cv_lite 模块存在")
    funcs = [f for f in dir(cv_lite) if 'rect' in f.lower()]
    print(f"    矩形相关函数: {funcs}")
except Exception as e:
    print(f"    ❌ cv_lite 导入失败: {e}")
    exit()

# --- 测试矩形检测 [H, W] ---
if has_numpy_ref:
    print("[6] cv_lite 矩形检测 [H, W]...")
    shape_hw = [img.height(), img.width()]
    print(f"    image_shape = {shape_hw}")
    try:
        rects = cv_lite.rgb888_find_rectangles_with_corners(
            shape_hw, img_np,
            RECT_CANNY_LO, RECT_CANNY_HI,
            RECT_EPSILON, RECT_AREA_MIN,
            RECT_MAX_ANGLE, RECT_GAUSS_SIZE)
        print(f"    返回: {len(rects) if rects else 0} 个矩形")
        if rects:
            for i, r in enumerate(rects[:3]):
                print(f"    [{i}] x={r[0]}, y={r[1]}, w={r[2]}, h={r[3]}, area={r[2]*r[3]}")
    except Exception as e:
        print(f"    ❌ 异常: {e}")

# --- 测试 [W, H] ---
if has_numpy_ref:
    print("[7] cv_lite 矩形检测 [W, H]...")
    shape_wh = [img.width(), img.height()]
    print(f"    image_shape = {shape_wh}")
    try:
        rects2 = cv_lite.rgb888_find_rectangles_with_corners(
            shape_wh, img_np,
            RECT_CANNY_LO, RECT_CANNY_HI,
            RECT_EPSILON, RECT_AREA_MIN,
            RECT_MAX_ANGLE, RECT_GAUSS_SIZE)
        print(f"    返回: {len(rects2) if rects2 else 0} 个矩形")
        if rects2:
            print("    ✅ [W, H] 顺序正确！")
    except Exception as e:
        print(f"    ❌ 异常: {e}")

# --- 放松参数 ---
if has_numpy_ref:
    print("[8] 放松参数测试 [H, W]...")
    try:
        rects3 = cv_lite.rgb888_find_rectangles_with_corners(
            [img.height(), img.width()], img_np,
            30, 200, 0.02, 0.0001, 10.0, 3)
        print(f"    返回: {len(rects3) if rects3 else 0} 个矩形")
        if rects3:
            print("    ✅ 放松参数后检测到了！")
    except Exception as e:
        print(f"    ❌ 异常: {e}")

# --- 显示 ---
print("[9] 显示画面...")
disp = display.Display()
cx, cy = IMG_CENTER_X, IMG_CENTER_Y
img.draw_line(cx - 30, cy, cx + 30, cy, color=(255, 0, 0), thickness=2)
img.draw_line(cx, cy - 30, cx, cy + 30, color=(255, 0, 0), thickness=2)
img.draw_string(10, 10, "DEBUG - check console", color=(0, 255, 0), scale=2)
img.draw_string(10, 40, f"shape:{img.width()}x{img.height()}", color=(0, 255, 0), scale=2)
disp.show(img)
print("    OK — 屏幕应有十字准星")

print("\n[10] 保持 5 秒...")
for _ in range(50):
    if app.need_exit():
        break
    time.sleep_ms(100)

if cam:
    cam = None
print("诊断完成。")
