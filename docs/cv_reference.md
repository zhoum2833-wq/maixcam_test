# CV 算法选型参考（视觉端详细版）

适用平台：MaixCAM Pro / MaixPy  


## 一、决策总则

```
能用传统 CV → 绝对不用 YOLO
传统 CV 搞不定 → 才上 YOLO
高频（每帧）→ 传统 CV 巡线
低频（5-10 帧一次）→ YOLO 识别
```

| 维度 | 传统 CV | YOLO |
|------|---------|------|
| 延迟 | < 5ms | 30-50ms（NPU 推理） |
| 确定性 | 100%（同输入同输出） | 概率性（可能漏检） |
| 光照敏感 | ⚠️ 敏感（需现场调参） | ✅ 鲁棒 |
| 角度/形变 | ❌ 容忍度低 | ✅ 鲁棒 |
| 调参成本 | 低（改几个数字） | 高（重新采集→训练→量化→验证） |
| 语义能力 | 无（只认颜色/形状） | 有（能区分"车"和"人"） |


## 二、滤波：什么时候用什么

### 2.1 高斯滤波 `img.gaussian(kernel_size)`

```
什么时候用：
  ✅ Canny 边缘检测前（必做！去噪后再找边缘）
  ✅ 图像整体噪点多时（灯光闪烁、传感器噪点）
  ❌ 需要保留边缘锐度的场景

参数：
  kernel_size: 奇数值，比赛环境用 3 或 5
  越大越模糊，越小越保留细节
```

```python
# MaixPy
img.gaussian(3)  # 3x3 高斯核，最常用
```

### 2.2 均值滤波 `img.mean(kernel_size)`

```
什么时候用：
  ⚠️  几乎不用。效果不如高斯（高斯给近像素更高权重）
  唯一场景：噪点均匀分布、没有明显中心区域时
```

### 2.3 中值滤波

```
什么时候用：
  ✅ 椒盐噪点（个别像素异常亮/暗）
  ⚠️  MaixPy 不一定有 median 实现，优先用高斯替代
```

### 决策口诀

```
椒盐噪点 → 中值滤波
其他一切 → 高斯滤波(3)
```

---

## 三、二值化：什么时候用

### 核心原则
**二值化是巡线的第一步**——把赛道线从背景分离出来。

```python
# MaixPy
img.binary([threshold])          # 固定阈值
# 或
img.binary([(L_H, U_H), ...])    # 多阈值（彩色二值化）
```

```
什么时候用：
  ✅ 黑白赛道线 → 单阈值即可
  ✅ 彩色赛道线 → 先 HSV 滤色，再二值化
  ✅ 巡线 ROI 区域内使用（减少计算量）
  ❌ 背景颜色和线颜色接近时（改用边缘检测）

阈值怎么调：
  比赛现场最需要改的参数之一
  按键 ±5 动态调整（参考 config.py 中 RECT_CANNY_LO/HI 的按键调节模式）
```

---

## 四、边缘检测：什么时候用什么

### 4.1 Canny 边缘检测

```
什么时候用：
  ✅ 形状检测（矩形、圆形、十字）——找轮廓前必须做
  ✅ 复杂背景下需要提取边缘
  ✅ cv_lite.rgb888_find_rectangles 内部已包含 Canny

参数（config.py 中）：
  RECT_CANNY_LO  = 50   低阈值（低于此值不是边缘）
  RECT_CANNY_HI  = 150  高阈值（高于此值一定是边缘）
  两阈值之间：与高阈值边缘相连才保留

调参口诀：
  噪点多 → 提高 LO、HI
  边缘断 → 降低 LO
```

### 4.2 Sobel 算子

```
什么时候用：
  ⚠️  基本不需要单独调
  Canny 已包含 Sobel 梯度计算，且效果更好
  唯一场景：只需要知道边缘方向（水平/垂直）时
```

### 决策口诀

```
日常 → Canny（cv_lite 内置）
需要边缘方向信息 → Sobel
```

---

## 五、颜色检测（HSV 分割）

### 这可能是除巡线外最常用的传统 CV 技术

```
什么时候用：
  ✅ 红色/黄色/蓝色/绿色路标
  ✅ 纯色障碍物/标志物
  ✅ 背景颜色相对单一

什么时候不用：
  ❌ 颜色和背景接近
  ❌ 光照剧烈变化（场地灯光有颜色）
  ❌ 需要区分类别（"红车"和"红球"分不开）
```

```python
# MaixPy 多阈值二值化（HSV 空间）
# 红色的 HSV 范围（一般需要两组，红色在 HSV 中跨 0°）
red_low  = [(0, 50, 50),   (160, 50, 50)]
red_high = [(10, 255, 255), (180, 255, 255)]

img.binary([red_low[0] + red_high[0], red_low[1] + red_high[1]])

# 然后对二值化结果找轮廓 → 外接矩形 → 定位
```

### 现场调参最关键的参数

```python
# config.py 中建议加：
COLOR_H_LOW  = 100   # 色调下限 (0-180)
COLOR_H_HIGH = 140   # 色调上限
COLOR_S_MIN  = 50    # 饱和度下限（太低=白色）
COLOR_V_MIN  = 50    # 明度下限（太低=黑色）
```

---

## 六、形态学操作（腐蚀 / 膨胀）

### 原文没提，但电赛巡线很关键

```
什么时候用：
  ✅ 二值化后有小噪点（白色小点）→ 腐蚀（erode）把噪点吃掉
  ✅ 二值化后线段有断裂 → 膨胀（dilate）把断口补上
  ✅ 两个目标粘连 → 腐蚀把它们分开
  ✅ 开运算（先腐蚀再膨胀）= 去噪点 + 不改变目标大小
  ✅ 闭运算（先膨胀再腐蚀）= 补断线 + 不改变目标大小
```

```python
# OpenCV 写法（MaixPy 可能有差异，需验证）
# 腐蚀
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
eroded = cv2.erode(binary_img, kernel)

# 膨胀
dilated = cv2.dilate(binary_img, kernel)

# 开运算（去噪点）
opened = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel)

# 闭运算（补断线）
closed = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel)
```

### 决策口诀

```
噪点多 → 开运算（先腐蚀再膨胀）
线断了 → 闭运算（先膨胀再腐蚀）
目标粘连 → 腐蚀
线太细 → 膨胀
核大小 → 3x3 起步，5x5 效果更强但会模糊细节
```

---

## 七、几何变换

### 7.1 透视变换（摄像头斜拍转正）

```
什么时候用：
  ✅ 摄像头斜向下拍赛道 → 转成俯视图
  ✅ 矩形偏斜需要校正 → 四点映射
  ✅ 巡线前做一次，后续处理更简单

方法：
  在赛道上放置 4 个已知坐标的参考点
  或直接用赛道边界作为 4 个点做映射
```

```python
# OpenCV
import cv2
import numpy as np

# 原图四个点（赛道 ROI 四个角）
src_pts = np.float32([[x1,y1], [x2,y2], [x3,y3], [x4,y4]])
# 目标四个点（俯视图矩形）
dst_pts = np.float32([[0,0], [320,0], [0,240], [320,240]])

M = cv2.getPerspectiveTransform(src_pts, dst_pts)
warped = cv2.warpPerspective(img, M, (320, 240))
```

### 7.2 ROI 裁剪

```
什么时候用：
  ✅ 只看图像下半部分（赛道在下方）
  ✅ 巡线只关心 ROI 区域，减少计算量
```

```python
# MaixPy
roi = img.crop(x=0, y=120, w=320, h=80)  # 只看中间一条
```

### 7.3 缩放

```
什么时候用：
  ✅ YOLO 需要指定输入尺寸（224x224 或 320x320）
  ✅ 减少计算量时缩小图像
```

---

## 八、形状检测：什么时候用什么

### 6.1 矩形检测 `cv_lite.rgb888_find_rectangles_with_corners`

```
什么时候用：
  ✅ 赛题需要找矩形框（已实现于 vision/rectangle.py）
  ✅ 对形变容忍度高（弯曲的矩形也能检测）

原理：
  Canny 边缘 → 四边形拟合 → 对边平行 + 邻边垂直 → 对角线交叉点

参考：
  vision/rectangle.py — 已实现完整流程
  config.py — 参数：RECT_CANNY_LO/HI, RECT_AREA_THRESH 等
```

### 6.2 圆形检测

```
什么时候用：
  ✅ 赛题需要找圆形路标 / 圆形障碍物
  ⚠️  MaixPy 没有 HoughCircles

替代方案：
  轮廓检测 → 计算面积/周长比
  理想圆：area / (perimeter²) ≈ 1 / (4π) ≈ 0.0796
  越接近这个值，越像圆
```

```python
# 圆形判定（轮廓级）
perimeter = contour_length
area = contour_area
ratio = area / (perimeter * perimeter)
# 圆 ≈ 0.0796，正方形 ≈ 0.0625
# 阈值可设在 0.07 ~ 0.09
```

### 6.3 十字形检测

```
什么时候用：
  ✅ 赛题需要找十字路口标志

方法：
  轮廓检测 → 多边形近似 → 判断顶点数=12（十字的凸包）
  或：水平/垂直方向投影 → 找对称中心
```

---

---

## 九、轮廓分析

### 形状检测的基础——找到二值图中的连通区域

```
什么时候用：
  ✅ 二值化/边缘检测后，需要找"有几个目标、每个在哪"
  ✅ 色块定位：HSV 分割 → 找轮廓 → 外接矩形 → 坐标
  ✅ 圆形判定：找轮廓 → 面积/周长比
  ✅ 形状分类：找轮廓 → 多边形近似 → 顶点数

核心流程：
  二值化 → 找轮廓 → 过滤（面积/比例） → 外接矩形/多边形拟合 → 输出
```

```python
# OpenCV 示例（MaixPy 需验证对应 API）
import cv2

# 找轮廓
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < 500:            # 过滤太小
        continue

    # 外接矩形（无旋转）
    x, y, w, h = cv2.boundingRect(cnt)   # → 目标位置

    # 外接矩形（带旋转角度）
    rect = cv2.minAreaRect(cnt)          # → 带方向信息

    # 多边形近似 → 判断形状
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
    vertices = len(approx)   # 3=三角形, 4=四边形, 8+=圆

    # 面积/周长比 → 判断圆形
    ratio = area / (peri * peri)
    # 圆 ≈ 0.08, 正方形 ≈ 0.06
```

### 决策口诀

```
找位置 → 外接矩形 boundingRect
找方向 → 最小外接矩形 minAreaRect
判断形状 → 多边形近似 approxPolyDP
判断圆形 → 面积周长比
```

---

## 十、特征提取（SIFT / ORB）

### ⚠️ 声明：MaixPy 不支持 SIFT 和 ORB

```
原因：
  MaixPy 不是完整 OpenCV，没有 cv2.SIFT_create() / cv2.ORB_create()
  这些算法需要大量数学库和内存，MCU 级别设备不支持

替代方案：
  传统 CV：颜色/形状/模板匹配
  AI：YOLO 检测（算力允许时）
```

---

## 十一、模板匹配 vs YOLO

| 维度 | 模板匹配 | YOLO |
|------|---------|------|
| 旋转不变 | ❌ 图歪了就废 | ✅ |
| 缩放不变 | ❌ 图大了小了就废 | ✅ |
| 光照不变 | ❌ | ✅ |
| 计算量 | 低 | 高（NPU 推理） |
| 适用场景 | 固定视角、固定距离 | 任意角度/距离 |

```
什么时候用模板匹配：
  ✅ 摄像头固定、目标距离固定、角度固定
  ✅ 数字/字符（固定字体）
  ❌ 小车移动中拍摄（距离变化大）

什么时候用 YOLO：
  ✅ 数字/字符识别（距离、角度不确定）
  ✅ 多类别需要区分语义
  ✅ 模板匹配完全搞不定时
```

---

## 十二、主循环架构（高低频搭配）

```python
# main.py 的核心结构
fps_clock = time.clock()
frame_count = 0

while True:
    fps_clock.tick()
    img = camera.capture()
    if img is None:
        continue

    # ===== 高频：每帧执行 =====
    # 巡线（传统 CV，< 5ms）
    left_x, right_x = line.track(img)
    uart.send_steering(left_x, right_x)

    # ===== 低频：每 N 帧执行 =====
    frame_count += 1
    if frame_count % 8 == 0:
        # YOLO 检测标志物/数字（30-50ms）
        result = yolo.detect(img)
        if result:
            uart.send_action(result.class_id)

    print(f"fps: {fps_clock.fps():.1f}")
```

### 帧率预期

| 模式 | FPS | 说明 |
|------|-----|------|
| 纯传统 CV（巡线） | 60-100 | 不阻塞，几乎无延迟 |
| 传统 CV + YOLO（8帧一次） | 50-90 | 每 8 帧有一次 YOLO 阻塞 |
| 纯 YOLO | 15-30 | NPU 推理耗时，完全不推荐 |

---

## 十三、现场调参优先级

| 优先级 | 参数 | 影响 |
|--------|------|------|
| 1 | 二值化阈值 `LINE_THRESH_BW` | 线能不能从背景分出来 |
| 2 | HSV 颜色阈值 | 色块能不能找到 |
| 3 | ROI 区域 `LINE_ROI` | 巡线范围对不对 |
| 4 | 矩形面积阈值 `RECT_AREA_THRESH` | 过滤假矩形 |
| 5 | Canny 高低阈值 | 边缘检测质量 |

**建议：** 按键动态调参（参考 矩形8.3.1.py 的 INC_KEY/DEC_KEY），不要每次重新下载代码。

---

## 附录：MaixPy 图像处理 API 速查

| 操作 | MaixPy API | 对应 OpenCV |
|------|-----------|------------|
| 高斯滤波 | `img.gaussian(k)` | `cv2.GaussianBlur` |
| 均值滤波 | `img.mean(k)` | `cv2.blur` |
| 固定二值化 | `img.binary([thresh])` | `cv2.threshold` |
| 多阈值二值化 | `img.binary([(lo,hi),...])` | `cv2.inRange` |
| Sobel 梯度 | `img.sobel()` | `cv2.Sobel` |
| ROI 裁剪 | `img.crop(x,y,w,h)` | `img[y:y+h, x:x+w]` |
| 矩形检测 | `cv_lite.rgb888_find_rectangles_with_corners(...)` | 无直接对应 |
| 画线 | `img.draw_line(x1,y1,x2,y2)` | `cv2.line` |
| 画圆 | `img.draw_circle(x,y,r)` | `cv2.circle` |
| 画文字 | `img.draw_string_advanced(x,y,size,text)` | `cv2.putText` |
