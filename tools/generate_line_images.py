"""
生成巡线测试图片 — 白底黑线，模拟比赛赛道。

直接运行: python tools/generate_line_images.py
输出到: test_images/
"""

import os
import numpy as np
from PIL import Image, ImageDraw

W, H = 320, 240  # 匹配 DETECT_W x DETECT_H
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_images')


def make_img():
    """创建白底画布"""
    return Image.new('L', (W, H), color=255)  # 'L' = 灰度, 255=白


def save(img, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    img.save(path)
    print(f"  saved: {path}")


# ============================================================
#  场景 1: 直线居中
# ============================================================
def gen_straight_center():
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(W // 2, 0), (W // 2, H)], fill=0, width=8)
    save(img, "line_straight_center.png")


# ============================================================
#  场景 2: 直线偏左
# ============================================================
def gen_straight_left():
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(100, 0), (100, H)], fill=0, width=8)
    save(img, "line_straight_left.png")


# ============================================================
#  场景 3: 直线偏右
# ============================================================
def gen_straight_right():
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(220, 0), (220, H)], fill=0, width=8)
    save(img, "line_straight_right.png")


# ============================================================
#  场景 4: 斜线（模拟弯道）
# ============================================================
def gen_diagonal():
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(60, 0), (260, H)], fill=0, width=8)
    save(img, "line_diagonal.png")


# ============================================================
#  场景 5: S 形弯道
# ============================================================
def gen_s_curve():
    img = make_img()
    draw = ImageDraw.Draw(img)
    # 用贝塞尔曲线画 S 弯
    points = []
    for t in np.linspace(0, 1, 200):
        # 三次贝塞尔: P0=(160,0) P1=(60,80) P2=(260,160) P3=(160,240)
        x = (1-t)**3 * 160 + 3*(1-t)**2*t * 60 + 3*(1-t)*t**2 * 260 + t**3 * 160
        y = t * H
        points.append((int(x), int(y)))
    draw.line(points, fill=0, width=8)
    save(img, "line_s_curve.png")


# ============================================================
#  场景 6: 十字路口
# ============================================================
def gen_cross():
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(W // 2, 0), (W // 2, H)], fill=0, width=8)
    draw.line([(0, H // 2), (W, H // 2)], fill=0, width=8)
    save(img, "line_cross.png")


# ============================================================
#  场景 7: 细线（3px）
# ============================================================
def gen_thin_line():
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(W // 2, 0), (W // 2, H)], fill=0, width=3)
    save(img, "line_thin.png")


# ============================================================
#  场景 8: 粗线（20px）
# ============================================================
def gen_thick_line():
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(W // 2, 0), (W // 2, H)], fill=0, width=20)
    save(img, "line_thick.png")


# ============================================================
#  场景 9: 断线（模拟不连续线）
# ============================================================
def gen_broken_line():
    img = make_img()
    draw = ImageDraw.Draw(img)
    # 画几段不连续的线
    segments = [(0, 30), (60, 90), (120, 150), (180, 210)]
    for y1, y2 in segments:
        draw.line([(W // 2, y1), (W // 2, y2)], fill=0, width=8)
    save(img, "line_broken.png")


# ============================================================
#  场景 B: 车道跟随（白底 + 两边黑边界）
# ============================================================
def gen_lane_center():
    """白色车道在中间，两边黑线"""
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(60, 0), (60, H)], fill=0, width=6)    # 左黑线
    draw.line([(260, 0), (260, H)], fill=0, width=6)   # 右黑线
    save(img, "lane_center.png")

def gen_lane_left():
    """白色车道偏左"""
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(20, 0), (20, H)], fill=0, width=6)
    draw.line([(180, 0), (180, H)], fill=0, width=6)
    save(img, "lane_left.png")

def gen_lane_right():
    """白色车道偏右"""
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(140, 0), (140, H)], fill=0, width=6)
    draw.line([(300, 0), (300, H)], fill=0, width=6)
    save(img, "lane_right.png")

def gen_lane_curve():
    """弯曲车道"""
    img = make_img()
    draw = ImageDraw.Draw(img)
    # 左边界 S 弯
    pts_l = []
    pts_r = []
    for t in np.linspace(0, 1, 200):
        x_l = (1-t)**3 * 60 + 3*(1-t)**2*t * 10 + 3*(1-t)*t**2 * 100 + t**3 * 100
        x_r = (1-t)**3 * 260 + 3*(1-t)**2*t * 210 + 3*(1-t)*t**2 * 300 + t**3 * 280
        y = t * H
        pts_l.append((int(x_l), int(y)))
        pts_r.append((int(x_r), int(y)))
    draw.line(pts_l, fill=0, width=6)
    draw.line(pts_r, fill=0, width=6)
    save(img, "lane_curve.png")

# ============================================================
#  场景 C: 边缘跟随（一边黑线）
# ============================================================
def gen_edge_left():
    """左边黑线，车沿右边跟着"""
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(40, 0), (40, H)], fill=0, width=8)
    save(img, "edge_left.png")

def gen_edge_right():
    """右边黑线，车沿左边跟着"""
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(280, 0), (280, H)], fill=0, width=8)
    save(img, "edge_right.png")

def gen_edge_left_far():
    """左边黑线距离较远"""
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(80, 0), (80, H)], fill=0, width=8)
    save(img, "edge_left_far.png")

def gen_edge_diagonal():
    """斜的边缘"""
    img = make_img()
    draw = ImageDraw.Draw(img)
    draw.line([(20, 0), (100, H)], fill=0, width=8)
    save(img, "edge_diagonal.png")


if __name__ == "__main__":
    print(f"[generate_line_images] output -> {OUT_DIR}")
    print()

    print("--- 场景 A: 中线跟随 ---")
    gen_straight_center()
    gen_straight_left()
    gen_straight_right()
    gen_diagonal()
    gen_s_curve()
    gen_cross()
    gen_thin_line()
    gen_thick_line()
    gen_broken_line()

    print("\n--- 场景 B: 车道跟随 ---")
    gen_lane_center()
    gen_lane_left()
    gen_lane_right()
    gen_lane_curve()

    print("\n--- 场景 C: 边缘跟随 ---")
    gen_edge_left()
    gen_edge_right()
    gen_edge_left_far()
    gen_edge_diagonal()

    print(f"\nDone! 共生成 17 张测试图片。")
