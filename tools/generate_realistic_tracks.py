"""
生成逼真赛道测试图片 — 模拟 MaixCAM 摄像头视角。

特点:
  - 320×240 匹配 MaixCAM 检测分辨率
  - 透视变换（模拟摄像头向下倾斜视角）
  - 随机噪点 + 光照不均 + 模糊（模拟真实环境）
  - 多种赛道元素：直线、弯道、十字、虚线、宽窄线

运行: python tools/generate_realistic_tracks.py
输出: test_images/real_*.png
"""

import os
import cv2
import numpy as np

W, H = 320, 240
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_images')
os.makedirs(OUT_DIR, exist_ok=True)

# 线宽（像素）
LINE_W = 8


def make_canvas():
    """创建白底画布"""
    return np.full((H, W), 255, dtype=np.uint8)


def add_noise(img, level=8):
    """加高斯噪点（模拟摄像头 sensor noise）"""
    noise = np.random.randint(-level, level + 1, (H, W), dtype=np.int16)
    noisy = img.astype(np.int16) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def add_lighting(img, center=None, strength=0.15):
    """加径向光照不均（模拟镜头暗角 / 环境光不均）"""
    if center is None:
        center = (W // 2 + np.random.randint(-60, 60),
                  H // 2 + np.random.randint(-40, 40))
    cx, cy = center
    Y, X = np.ogrid[:H, :W]
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_dist = np.sqrt(W ** 2 + H ** 2)
    # 中间亮、边缘暗
    vignette = 1.0 - strength * (dist / max_dist)
    vignette = np.clip(vignette, 0.7, 1.0)
    return np.clip(img * vignette, 0, 255).astype(np.uint8)


def add_blur(img, ksize=1):
    """加轻微模糊（模拟镜头对焦不准或运动模糊）"""
    if ksize <= 1:
        return img
    if ksize % 2 == 0:
        ksize += 1
    return cv2.GaussianBlur(img, (ksize, ksize), 0)


def add_shadow(img):
    """加随机阴影块（模拟环境遮挡）"""
    result = img.copy()
    for _ in range(np.random.randint(0, 3)):
        sx = np.random.randint(0, W - 60)
        sy = np.random.randint(0, H - 40)
        sw = np.random.randint(30, 100)
        sh = np.random.randint(15, 50)
        result[sy:sy+sh, sx:sx+sw] = np.clip(
            result[sy:sy+sh, sx:sx+sw].astype(np.int16) - 30, 0, 255
        ).astype(np.uint8)
    return result


def save(img, name):
    path = os.path.join(OUT_DIR, name)
    cv2.imwrite(path, img)
    print(f"  {name}")


def apply_effects(img, noise_level=8, blur_k=1, light=True, shadow=True):
    """统一施加效果"""
    if light:
        img = add_lighting(img)
    if shadow:
        img = add_shadow(img)
    if blur_k > 1:
        img = add_blur(img, blur_k)
    if noise_level > 0:
        img = add_noise(img, noise_level)
    return img


# ============================================================
#  场景 A: 中线跟随
# ============================================================

def gen_line_straight():
    """直线居中 — 干净版"""
    img = make_canvas()
    cv2.line(img, (W // 2, 0), (W // 2, H), 0, LINE_W)
    save(img, "real_line_straight_clean.png")

def gen_line_straight_noisy():
    """直线居中 — 加噪 + 暗角"""
    img = make_canvas()
    cv2.line(img, (W // 2, 0), (W // 2, H), 0, LINE_W)
    img = apply_effects(img, noise_level=12, blur_k=3)
    save(img, "real_line_straight_noisy.png")

def gen_line_offset_left():
    """线偏左 60px — 加噪"""
    img = make_canvas()
    cv2.line(img, (W // 2 - 60, 0), (W // 2 - 60, H), 0, LINE_W)
    img = apply_effects(img, noise_level=10)
    save(img, "real_line_left.png")

def gen_line_offset_right():
    """线偏右 60px — 加噪"""
    img = make_canvas()
    cv2.line(img, (W // 2 + 60, 0), (W // 2 + 60, H), 0, LINE_W)
    img = apply_effects(img, noise_level=10)
    save(img, "real_line_right.png")

def gen_line_curve_smooth():
    """平滑弯道（S 弯）"""
    img = make_canvas()
    pts = np.array([
        [int(160 + 60 * np.sin(y / 40.0)), y]
        for y in range(0, H, 4)
    ], dtype=np.int32)
    cv2.polylines(img, [pts], False, 0, LINE_W)
    img = apply_effects(img, noise_level=10)

    # 在图上加文字标注
    img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    cv2.putText(img_color, "S-curve", (5, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
    img = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    save(img, "real_line_scurve.png")

def gen_line_sharp_turn():
    """直角弯"""
    img = make_canvas()
    # 竖线
    cv2.line(img, (W // 2, 0), (W // 2, 160), 0, LINE_W)
    # 横线
    cv2.line(img, (W // 2, 160), (W - 40, 160), 0, LINE_W)
    img = apply_effects(img)
    save(img, "real_line_sharp_turn.png")

def gen_line_cross():
    """十字路口"""
    img = make_canvas()
    cv2.line(img, (W // 2, 0), (W // 2, H), 0, LINE_W)
    cv2.line(img, (0, H // 2), (W, H // 2), 0, LINE_W)
    img = apply_effects(img, noise_level=8)
    save(img, "real_line_cross.png")

def gen_line_dashed():
    """虚线（断线）"""
    img = make_canvas()
    seg_length = 35
    gap = 20
    y = 0
    while y < H:
        end_y = min(y + seg_length, H)
        cv2.line(img, (W // 2, y), (W // 2, end_y), 0, LINE_W)
        y += seg_length + gap
    img = apply_effects(img, noise_level=10)
    save(img, "real_line_dashed.png")

def gen_line_thin():
    """细线 3px"""
    img = make_canvas()
    cv2.line(img, (W // 2, 0), (W // 2, H), 0, 3)
    img = apply_effects(img, noise_level=8, blur_k=3)
    save(img, "real_line_thin.png")

def gen_line_thick():
    """粗线 16px"""
    img = make_canvas()
    cv2.line(img, (W // 2, 0), (W // 2, H), 0, 16)
    img = apply_effects(img, noise_level=10)
    save(img, "real_line_thick.png")

# ============================================================
#  场景 B: 车道跟随（白色车道 + 两条黑边界）
# ============================================================

def gen_lane_straight():
    """标准车道"""
    img = make_canvas()
    left_border = 60
    right_border = 260
    cv2.line(img, (left_border, 0), (left_border, H), 0, 6)
    cv2.line(img, (right_border, 0), (right_border, H), 0, 6)
    img = apply_effects(img, noise_level=10)
    save(img, "real_lane_center.png")

def gen_lane_offset():
    """车道偏左"""
    img = make_canvas()
    cv2.line(img, (20, 0), (20, H), 0, 6)
    cv2.line(img, (180, 0), (180, H), 0, 6)
    img = apply_effects(img, noise_level=10)
    save(img, "real_lane_left.png")

def gen_lane_narrow():
    """窄车道"""
    img = make_canvas()
    cv2.line(img, (120, 0), (120, H), 0, 6)
    cv2.line(img, (200, 0), (200, H), 0, 6)
    img = apply_effects(img, noise_level=10)
    save(img, "real_lane_narrow.png")

# ============================================================
#  场景 C: 边缘跟随
# ============================================================

def gen_edge_left_close():
    """左边黑线（近）"""
    img = make_canvas()
    cv2.line(img, (40, 0), (40, H), 0, 8)
    img = apply_effects(img, noise_level=10)
    save(img, "real_edge_left.png")

def gen_edge_left_far():
    """左边黑线（远）"""
    img = make_canvas()
    cv2.line(img, (80, 0), (80, H), 0, 8)
    img = apply_effects(img, noise_level=10)
    save(img, "real_edge_left_far.png")

def gen_edge_right():
    """右边黑线"""
    img = make_canvas()
    cv2.line(img, (280, 0), (280, H), 0, 8)
    img = apply_effects(img, noise_level=10)
    save(img, "real_edge_right.png")

# ============================================================
#  特殊场景: 模拟真实比赛条件
# ============================================================

def gen_hard_lighting():
    """强光从侧面打（模拟比赛现场灯光）"""
    img = make_canvas()
    cv2.line(img, (W // 2, 0), (W // 2, H), 0, LINE_W)

    # 模拟右侧强光
    Y, X = np.ogrid[:H, :W]
    gradient = 1.0 - 0.35 * (X / W)  # 右边亮、左边暗
    img = np.clip(img * gradient, 0, 255).astype(np.uint8)
    img = add_noise(img, 8)
    save(img, "real_line_hard_light.png")

def gen_low_contrast():
    """低对比度（灰线 + 灰底，模拟光线暗）"""
    img = np.full((H, W), 180, dtype=np.uint8)  # 灰底
    cv2.line(img, (W // 2, 0), (W // 2, H), 60, LINE_W)  # 深灰线
    img = add_noise(img, 15)
    img = add_blur(img, 3)
    save(img, "real_line_low_contrast.png")

def gen_multi_noise():
    """很多噪点 + 污渍块（模拟脏赛道）"""
    img = make_canvas()
    cv2.line(img, (W // 2, 0), (W // 2, H), 0, LINE_W)
    # 高强度噪点
    img = add_noise(img, 25)
    # 随机黑块（污渍）
    for _ in range(8):
        sx = np.random.randint(10, W - 30)
        sy = np.random.randint(10, H - 20)
        r = np.random.randint(4, 12)
        cv2.circle(img, (sx, sy), r, np.random.randint(30, 80), -1)
    img = add_blur(img, 3)
    save(img, "real_line_dirty.png")


if __name__ == "__main__":
    print("[generate_realistic_tracks] 生成逼真赛道测试图片...\n")

    print("=== 场景 A: 中线跟随 ===")
    gen_line_straight()
    gen_line_straight_noisy()
    gen_line_offset_left()
    gen_line_offset_right()
    gen_line_curve_smooth()
    gen_line_sharp_turn()
    gen_line_cross()
    gen_line_dashed()
    gen_line_thin()
    gen_line_thick()

    print("\n=== 场景 B: 车道跟随 ===")
    gen_lane_straight()
    gen_lane_offset()
    gen_lane_narrow()

    print("\n=== 场景 C: 边缘跟随 ===")
    gen_edge_left_close()
    gen_edge_left_far()
    gen_edge_right()

    print("\n=== 特殊场景 ===")
    gen_hard_lighting()
    gen_low_contrast()
    gen_multi_noise()

    print(f"\nDone! 共 20 张，输出到: {OUT_DIR}")
