#include <Arduino.h>

#include "AppConfig.h"
#include "MqttService.h"

MqttService mqttService;
unsigned long lastTelemetryMs = 0;

void setup() {
  Serial.begin(115200);
  delay(200);

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

    mqttService.publishTelemetry(voltage, current, power);
  }
}
