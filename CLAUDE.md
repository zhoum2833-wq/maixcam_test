# CLAUDE.md — MaixCAM 模块测试工程

## 定位

独立测试工程，用于赛前验证 `maixcam_modules` 中的每个模块。
**测试通过后才提交到模块库，保证模块库始终是"安全版"。**

## 仓库关系

```
maixcam_modules/        → 被测试的模块代码
maixcam_test/           → 你在这里（独立测试工程）
maixcam_vision_temple/  → 视觉工程模板
```

## 测试原则

- 一个测试文件只测一个模块
- 测试脚本命名：`test_模块名.py`
- 测试通过 → 模块代码同步到 `maixcam_modules` 和 `maixcam_vision_temple`
- 测试失败 → 修本工程 → 再测 → 通过后同步

## 同步流程

本工程是模块代码的**测试与验证地**，不是权威来源。
权威来源是 `maixcam_modules/`，模板在 `maixcam_vision_temple/`。

```
改代码 → maixcam_test 测试通过
                ├──→ 同步 module/*.py 到 maixcam_modules/
                └──→ 同步 module/*.py 到 maixcam_vision_temple/module/
```

修改模块代码时，改 `maixcam_test/module/` → 测试通过 → 复制到另外两个库。

## 目录

```
maixcam_test/
├── main.py              ← 开机自启入口
├── config.py            ← 全局配置
├── module/              ← 硬件封装
│   ├── camera.py            摄像头
│   └── uart.py              串口
├── vision/              ← 纯算法
│   ├── line.py              巡线
│   ├── digit.py             数字识别
│   └── rectangle.py         矩形检测
├── algorithm/           ← 通用算法
│   └── pid.py               PID 控制器
├── test/                ← 测试脚本（手动运行）
│   ├── test_camera.py
│   └── test_uart.py
├── model/               ← 模型文件目录
├── docs/                ← 开发参考
│   └── cv_reference.md
├── CLAUDE.md
└── README.md
```

## 运行环境

- 目标硬件：Sipeed MaixCAM Pro
- 系统版本：MaixPy 4.12.5（2026-01 发布）
- 摄像头传感器：GC4653（自动检测，无需手动指定型号）
- 屏幕：2.4" 640×480 电容触摸
- 部署方式：MaixVision WiFi 同步工程 → 运行入口文件

## MaixPy 4.12 API 标准（★ 本工程强制遵守）

MaixPy 4.12 的 API 入口是 `maix.*`，**不是** `media.*`。
网上的参考代码（如 矩形8.3.1.py）多数是旧版 API，不能直接照抄。

| 功能 | ✅ 用这个 (v4.12) | ❌ 不用这个 (旧版) |
|------|-------------------|---------------------|
| 摄像头 | `from maix import camera` → `camera.Camera(w, h, fmt)` | `media.sensor.Sensor` |
| 取图 | `cam.read()` | `sensor.snapshot()` |
| 屏幕 | `from maix import display` → `display.Display().show(img)` | `media.display.Display` / `Display.show_image()` |
| 串口 | `from maix import uart` → `uart.UART(device, baud)` | `machine.UART` / `machine.FPIOA` |
| 主循环 | `while not app.need_exit():` | `while True:` |
| 绘图 | `img.draw_string(x, y, text, color, scale)` | `img.draw_string_advanced(...)` |
| 颜色 | `image.Format.FMT_RGB888` | `Sensor.RGB888` |
| 时间 | `time.time_ms()` / `time.sleep_ms()` | `media.media.MediaManager`（不再需要） |

### 已验证通过的硬件

| 模块 | 状态 | 备注 |
|------|:---:|------|
| Camera (GC4653) | ✅ 2026-07 验证 | 480×320 RGB888 正常采集 |
| UART (WiFi 模式) | ⚠️  | 初始化不报错，收发需外接 MSPM0 验证 |
| Display | ✅ | `disp.show(img)` 自动同步到 MaixVision |
| 工程 import 机制 | ✅ | `sys.path.insert(0, os.path.dirname(__file__))` 正确解析 module/ vision/ |

## 架构规范（★ 强制）

```
main.py  ← 唯一入口，所有业务逻辑、主循环、时序控制全在这里
  │
  ├── module/     ← 只暴露类，不执行任何顶层代码
  ├── vision/     ← 只暴露函数，不执行任何顶层代码
  └── algorithm/  ← 只暴露类/函数，不执行任何顶层代码
```

| 规则 | 说明 |
|------|------|
| ✅ main.py 唯一入口 | 一切业务逻辑、主循环、时序控制全部收拢到 `main.py` |
| ✅ 模块只定义 | `module/` `vision/` `algorithm/` 里**只能有**类和函数定义 |
| ❌ 禁止模块顶层执行 | 模块文件里**禁止** `while True:`、`print()`、`app.need_exit()` 等顶层执行代码 |
| ✅ 模块暴露接口 | 模块对外暴露方法/类，等待 `main.py` 调用 |

```python
# ✅ 正确的模块写法 (vision/xxx.py)
def detect(img):
    ...  # 纯函数，被 main.py 调用
    return result

# ❌ 错误的模块写法
cam = Camera()           # 顶层实例化
while True:              # 顶层死循环
    img = cam.capture()
    print(detect(img))   # 顶层 print
```

## 规范

- 测试脚本独立运行，不依赖其他测试
- 必须验证边界条件（None、超时、格式错误等）
- 测试注释写清楚"期望什么、实际什么"
- 所有 import 使用 `maix.*` API，禁止使用 `media.*` / `machine.*` 旧 API
