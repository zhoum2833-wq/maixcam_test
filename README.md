# MaixCAM 视觉测试工程

赛前逐个验证视觉模块的正确性。测试通过才推模块库。

## 性能目标

> 详见 [docs/vision_targets.md](docs/vision_targets.md)

| 指标 | 目标 | 说明 |
|------|:--:|------|
| 帧率 | **80-100Hz** | 外环控制甜点区间 |
| 稳定性 | 持续平稳 | 帧率抖动 > 峰值 |
| 时延 | 尽量低 | 链路延迟决定追踪精度 |

## 测试清单

| 模块 | 测试文件 | 状态 |
|------|---------|:--:|
| camera | test_camera.py | ✅ 7/7 PASS |
| uart | test_uart.py | ✅ 7/7 PASS |
| rectangle | (main.py 实测) | ✅ find_rects 可用 |
| line | test_vision_line.py | ⬜ 待现场实现 |
| digit | test_vision_digit.py | ⬜ 待现场实现 |
| pid | — | ✅ 算法完成，待串联控制回路 |

## 快速开始

### 调试模式（连 MaixVision，有画面）

```python
# main.py 顶部
DEBUG_DRAW   = True   # 画面 + 绘图
SHOW_EVERY_N = 2      # 隔帧推画面，减少 WiFi 开销
```

### 性能测速（不推画面，看真实帧率）

```python
DEBUG_DRAW   = False  # 纯算法 + 串口
```

### 三阶段工作流

| 阶段 | 连接 | 画面 | 目标 |
|------|:--:|:--:|------|
| 1. 线上调试 | MaixVision | ✅ 开 | 调阈值、排查 bug |
| 2. 性能测速 | MaixVision | ❌ 关 | 摸真实帧率上限 |
| 3. 脱机验证 | 独立电源 | — | 最终核验 |

> ⚠️ **不要拿连接 MaixVision 调试时的帧率当作最终性能指标！**
> `disp.show()` 推流 + `print()` + 绘图算子会拉低帧率、增大时延。

## 目录

```
maixcam_test/
├── main.py              ← 唯一入口，调度中枢
├── config.py            ← 全局配置（比赛现场主要改这里）
├── module/              ← 硬件封装（Camera, UART）
├── vision/              ← 纯算法（rectangle, line, digit）
├── algorithm/           ← 通用算法（PID）
├── test/                ← 测试脚本
├── model/               ← 模型文件
├── docs/                ← 参考文档
│   ├── cv_reference.md
│   └── vision_targets.md
├── CLAUDE.md
└── README.md
```

## 架构规范

```
main.py  ← 唯一入口，所有业务逻辑、主循环、时序控制
  ├── module/     ← 只暴露类，不执行顶层代码
  ├── vision/     ← 只暴露函数，不执行顶层代码
  └── algorithm/  ← 只暴露类/函数，不执行顶层代码
```
