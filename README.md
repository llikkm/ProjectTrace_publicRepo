# SRDP 投影交互笔

探索基于二维激光雷达与笔尖接触检测的投影交互。ESP32-S3 采集笔端输入，电脑端计划使用 Python 完成定位和绘图。

## 当前进度

仓库目前包含 LSM6DS3TR-C 六轴 IMU 的 Arduino 采集示例。雷达接入、接触检测及 Python 画布仍处于规划阶段。源码已保留，本次仓库整理未执行编译或硬件测试。

## 目录

```text
IMU_Test_261104/
  IMU_Test_261104.ino   IMU 寄存器读写与串口输出
docs/
  DEVELOPMENT.md       开发环境、接线和运行说明
  GIT_WORKFLOW.md      提交与同步步骤
```

Arduino 草图文件夹和其中的 `.ino` 文件保持同名，可直接用 Arduino IDE 打开。

## 快速开始

1. 安装 Arduino IDE 2.x 和 Espressif 的 `esp32` 开发板包。
2. 打开 `IMU_Test_261104/IMU_Test_261104.ino`，按实际硬件选择 ESP32-S3 开发板和串口。
3. 按[开发环境说明](docs/DEVELOPMENT.md)核对接线，手动编译、上传。
4. 以 115200 波特率打开串口监视器，观察初始化消息和六轴数据。

## 公开范围

公开仓库保存源码及经过整理的开发说明。本地申报资料、参考视频和原始交接记录通过 `.gitignore` 排除。新增文件时，先按[提交说明](docs/GIT_WORKFLOW.md)检查暂存内容。

## 参考

- [Arduino-ESP32 安装说明](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html)
- [Arduino-ESP32 I²C API](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2c.html)
- [ST LSM6DS3TR-C 产品资料](https://www.st.com/en/mems-and-sensors/lsm6ds3tr-c.html)
