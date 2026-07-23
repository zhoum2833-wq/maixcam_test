# MaixCAM 模块测试工程

赛前逐个验证 `maixcam_modules` 的正确性。测试通过才推模块库。

## 测试清单

| 模块 | 测试文件 | 状态 |
|------|---------|------|
| camera | test_camera.py | ⬜ |
| uart | test_uart.py | ⬜ |
| vision_line | test_vision_line.py | ⬜ |
| vision_digit | test_vision_digit.py | ⬜ |

## 使用方式

1. 从 `maixcam_vision_temple` 复制工程框架
2. 从 `maixcam_modules` 复制待测模块代码
3. 写 `test_xxx.py` → 运行 → 验证
4. 通过后提交模块代码到 `maixcam_modules`
