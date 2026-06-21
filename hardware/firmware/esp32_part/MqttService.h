
#pragma once

#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>

class MqttService {
public:
  void begin();
  void loop();
  bool isConnected();
  bool publishTelemetry(float voltage, float current, float power, float phi = 0.0, float fp = 0.0, float kwh = 0.0);
  bool publishMessage(const char *topic, const String &payload, bool retain = false);

private:
  void connectToWifi();
  void connectToMqtt();

  WiFiClientSecure secureClient;
  PubSubClient mqttClient;

  bool wifiReady = false;
  unsigned long lastWifiCheckMs = 0;
  unsigned long lastWifiReconnectAttemptMs = 0;
  unsigned long lastMqttReconnectAttemptMs = 0;
};