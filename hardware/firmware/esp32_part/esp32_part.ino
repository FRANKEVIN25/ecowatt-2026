#include <Arduino.h>

#include "AppConfig.h"
#include "MqttService.h"

MqttService mqttService;
unsigned long lastTelemetryMs = 0;

void setup() {
  Serial.begin(115200);
  delay(2000);

  mqttService.begin();
}

void loop() {
  mqttService.loop();

  const unsigned long now = millis();

  if (now - lastTelemetryMs >= AppConfig::TelemetryIntervalMs) {
    lastTelemetryMs = now;

    const float voltage = 220.5;
    const float current = 1.25;
    const float power = voltage * current;
    const float phi = 0.0;
    const float fp = 0.95;
    const float kwh = 0.0;

    mqttService.publishTelemetry(voltage, current, power, phi, fp, kwh);
  }
}