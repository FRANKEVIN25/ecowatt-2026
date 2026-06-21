#pragma once

#include <Arduino.h>
#include <AsyncMqttClient.h>
#include <WiFi.h>

class MqttService {
public:
  void begin();
  void loop();
  bool isConnected() const;
  bool publishTelemetry(float voltage, float current, float power);
  bool publishMessage(const char *topic, const String &payload, bool retain = false, uint8_t qos = 0);

private:
  void connectToWifi();
  void connectToMqtt();

  void handleMqttConnect(bool sessionPresent);
  void handleMqttDisconnect(AsyncMqttClientDisconnectReason reason);
  void handleMqttPublish(uint16_t packetId);

  AsyncMqttClient mqttClient;
  bool wifiReady = false;
  bool mqttReconnectPending = false;
  unsigned long lastWifiCheckMs = 0;
  unsigned long lastWifiReconnectAttemptMs = 0;
  unsigned long lastMqttReconnectAttemptMs = 0;
};
