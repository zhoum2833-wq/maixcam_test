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
- 测试通过 → 模块代码提交到 `maixcam_modules`
- 测试失败 → 修本工程 → 再测 → 通过后回灌模块库

## 目录

```
maixcam_test/
├── test_camera.py       摄像头测试
├── test_uart.py         串口收发测试
├── test_vision_line.py  巡线算法测试
├── test_vision_digit.py 数字识别测试
├── CLAUDE.md
└── README.md
```

## 规范

- 测试脚本独立运行，不依赖其他测试
- 必须验证边界条件（None、超时、格式错误等）
- 测试注释写清楚"期望什么、实际什么"
