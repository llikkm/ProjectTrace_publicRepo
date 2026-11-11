
#include <Wire.h>

#define SDA_PIN 8
#define SCL_PIN 9
#define IMU_ADDR 0x6A

// 陀螺仪静态零偏，单位：°/s
float gyroBiasX = -1.4343;
float gyroBiasY = -1.8020;
float gyroBiasZ = -0.0069;

// 写入一个寄存器
bool writeReg(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

// 连续读取寄存器
bool readRegs(uint8_t reg, uint8_t *data, uint8_t len) {
  Wire.beginTransmission(IMU_ADDR);
  Wire.write(reg);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  if (Wire.requestFrom((uint8_t)IMU_ADDR, len, true) != len) {
    return false;
  }

  for (uint8_t i = 0; i < len; i++) {
    data[i] = Wire.read();
  }
  return true;
}

// 两个字节转换为有符号16位数据
int16_t toInt16(uint8_t low, uint8_t high) {
  return (int16_t)((uint16_t)high << 8 | low);
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);

  Serial.println("LSM6DS3TR-C Test");

  uint8_t id;

  if (!readRegs(0x0F, &id, 1)) {
    Serial.println("WHO_AM_I read failed!");
    while (1) delay(1000);
  }

  Serial.print("WHO_AM_I = 0x");
  Serial.println(id, HEX);

  if (id != 0x6A) {
    Serial.println("Unexpected sensor ID!");
    while (1) delay(1000);
  }

  // BDU=1，寄存器地址自动递增
  bool ok = writeReg(0x12, 0x44);

  // 加速度计：104Hz，±2g
  ok &= writeReg(0x10, 0x40);

  // 陀螺仪：104Hz，±250 dps
  ok &= writeReg(0x11, 0x40);

  if (!ok) {
    Serial.println("IMU configuration failed!");
    while (1) delay(1000);
  }

  delay(100);
  Serial.println("IMU initialized!");
}

void loop() {
  uint8_t data[12];

  // 从 0x22 开始读取陀螺仪和加速度计
  if (!readRegs(0x22, data, 12)) {
    Serial.println("Read failed!");
    delay(100);
    return;
  }

  int16_t gx_raw = toInt16(data[0], data[1]);
  int16_t gy_raw = toInt16(data[2], data[3]);
  int16_t gz_raw = toInt16(data[4], data[5]);

  int16_t ax_raw = toInt16(data[6], data[7]);
  int16_t ay_raw = toInt16(data[8], data[9]);
  int16_t az_raw = toInt16(data[10], data[11]);




  // ±250dps：8.75 mdps/LSB
  float gx = gx_raw * 0.00875f;
  float gy = gy_raw * 0.00875f;
  float gz = gz_raw * 0.00875f;

  // ±2g：0.061 mg/LSB
  float ax = ax_raw * 0.000061f;
  float ay = ay_raw * 0.000061f;
  float az = az_raw * 0.000061f;


  
  // 陀螺仪零偏修正
  gx -= gyroBiasX;
  gy -= gyroBiasY;
  gz -= gyroBiasZ;





  Serial.printf(
    "AX:%.3f AY:%.3f AZ:%.3f "
    "GX:%.3f GY:%.3f GZ:%.3f\n",
    ax, ay, az, gx, gy, gz);

  delay(50);
}
