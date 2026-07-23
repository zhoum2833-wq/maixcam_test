"""
test/test_ball_pc.py — 钢球检测算法 PC 端验证

两条路线对照：
  A. Hough Circles  — 能处理球挨在一起的情况（本测试图适用）
  B. Blobs + 圆形度  — MaixPy 移植路线（find_blobs 替代方案）

用法:
    python test/test_ball_pc.py <图片路径>
    python test/test_ball_pc.py <图片路径> --method hough     (默认)
    python test/test_ball_pc.py <图片路径> --method blobs
"""

import cv2
import numpy as np
import sys
import math
import os

# ============================================================
#  检测参数
# ============================================================
# --- Hough Circles ---
HOUGH_DP         = 1.2      # 累加器分辨率（>1 降低分辨率加速）
HOUGH_MIN_DIST   = 35       # 球心最小间距
HOUGH_PARAM1     = 50       # Canny 高阈值
HOUGH_PARAM2     = 38       # 累加器阈值（调高=更严格=更少假阳性）
HOUGH_MIN_R      = 28       # 最小半径
HOUGH_MAX_R      = 65       # 最大半径

# --- Blobs + 圆形度 ---
BLUR_KSIZE       = 5        # 高斯核大小
THRESH_VALUE     = 240      # 灰度阈值：低于此值为前景
AREA_MIN         = 200      # 最小面积
AREA_MAX         = 50000    # 最大面积
CIRCULARITY_MIN  = 0.70     # 圆形度下限（1.0 = 完美圆）


# ============================================================
#  路线 A: Hough Circles（PC 端推荐）
# ============================================================
def detect_balls_hough(img_bgr, debug_dir=None):
    """Hough 圆检测 — 可处理粘连圆"""
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (BLUR_KSIZE, BLUR_KSIZE), 0)

    if debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "A01_gray.jpg"), gray)
        cv2.imwrite(os.path.join(debug_dir, "A02_blurred.jpg"), blurred)

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT,
        dp=HOUGH_DP,
        minDist=HOUGH_MIN_DIST,
        param1=HOUGH_PARAM1,
        param2=HOUGH_PARAM2,
        minRadius=HOUGH_MIN_R,
        maxRadius=HOUGH_MAX_R,
    )

    if circles is None:
        return []

    circles = np.uint16(np.around(circles))
    balls = []
    for c in circles[0]:
        cx, cy, r = int(c[0]), int(c[1]), int(c[2])
        # 用轮廓验证圆形度
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (cx, cy), r, 255, -1)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            area = cv2.contourArea(cnts[0])
            peri = cv2.arcLength(cnts[0], True)
            circ = (4.0 * math.pi * area) / (peri * peri) if peri > 0 else 0
        else:
            circ = 0.0
        balls.append((cx, cy, r, round(circ, 3)))

    balls.sort(key=lambda b: b[2] * b[2], reverse=True)
    return balls


# ============================================================
#  路线 B: Blobs + 圆形度过滤（MaixPy 移植目标）
# ============================================================
def detect_balls_blobs(img_bgr, debug_dir=None):
    """二值化 → 轮廓 → 圆形度过滤 → MaixPy find_blobs 等价实现"""
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (BLUR_KSIZE, BLUR_KSIZE), 0)
    _, binary = cv2.threshold(blurred, THRESH_VALUE, 255, cv2.THRESH_BINARY_INV)

    if debug_dir:
        cv2.imwrite(os.path.join(debug_dir, "B01_gray.jpg"), gray)
        cv2.imwrite(os.path.join(debug_dir, "B02_binary.jpg"), binary)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    balls = []
    debug_cnt = np.zeros((h, w, 3), dtype=np.uint8) if debug_dir else None

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if not (AREA_MIN < area < AREA_MAX):
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter < 1.0:
            continue

        circularity = (4.0 * math.pi * area) / (perimeter * perimeter)
        if circularity < CIRCULARITY_MIN:
            continue

        (cx, cy), radius = cv2.minEnclosingCircle(cnt)
        balls.append((int(cx), int(cy), int(radius), round(circularity, 3)))

        if debug_cnt is not None:
            cv2.drawContours(debug_cnt, [cnt], -1,
                             (np.random.randint(50, 255),
                              np.random.randint(50, 255),
                              np.random.randint(50, 255)), 2)

    if debug_dir and debug_cnt is not None:
        cv2.imwrite(os.path.join(debug_dir, "B03_contours.jpg"), debug_cnt)

    balls.sort(key=lambda b: b[2] * b[2], reverse=True)
    return balls


# ============================================================
#  绘制
# ============================================================
def draw_results(img_bgr, balls, method_name=""):
    out = img_bgr.copy()
    for i, (cx, cy, r, circ) in enumerate(balls):
        cv2.circle(out, (cx, cy), r, (0, 255, 0), 2)
        cv2.circle(out, (cx, cy), 3, (0, 0, 255), -1)
        label = f"#{i} r={r} c={circ:.2f}"
        cv2.putText(out, label, (cx + r + 5, cy - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    cv2.putText(out, f"[{method_name}] Found: {len(balls)} balls", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    return out


# ============================================================
#  Main
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("用法: python test/test_ball_pc.py <图片路径> [--method hough|blobs]")
        sys.exit(1)

    img_path = sys.argv[1]
    method = "hough"
    i = 2
    while i < len(sys.argv):
        a = sys.argv[i]
        if a.startswith("--method="):
            method = a.split("=")[1]
        elif a in ("--method", "-m"):
            if i + 1 < len(sys.argv):
                method = sys.argv[i + 1]
                i += 1
        i += 1

    if not os.path.exists(img_path):
        print(f"[ERROR] 文件不存在: {img_path}")
        sys.exit(1)

    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        print(f"[ERROR] 无法读取图片")
        sys.exit(1)

    h, w = img_bgr.shape[:2]
    print(f"[INFO] 图片: {w}×{h}  |  方法: {method}")

    debug_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(debug_dir, exist_ok=True)

    if method == "hough":
        balls = detect_balls_hough(img_bgr, debug_dir=debug_dir)
    else:
        balls = detect_balls_blobs(img_bgr, debug_dir=debug_dir)

    print(f"\n[RESULT] 检测到 {len(balls)} 个钢球:")
    print(f"{'#':<4} {'cx':<6} {'cy':<6} {'radius':<8} {'circularity':<12}")
    print("-" * 40)
    for i, (cx, cy, r, circ) in enumerate(balls):
        print(f"{i:<4} {cx:<6} {cy:<6} {r:<8} {circ:<12}")

    result_img = draw_results(img_bgr, balls, method_name=method)
    out_path = os.path.join(debug_dir, f"{method}_result.jpg")
    cv2.imwrite(out_path, result_img)
    print(f"\n[INFO] 结果: {out_path}")


if __name__ == "__main__":
    main()
