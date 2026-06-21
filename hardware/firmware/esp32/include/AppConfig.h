#pragma once

namespace AppConfig {
constexpr const char *WiFiSsid = "TU_WIFI";
constexpr const char *WiFiPassword = "TU_PASSWORD";

constexpr const char *MqttHost = "broker.hivemq.com";
constexpr unsigned int MqttPort = 1883;
constexpr const char *MqttClientId = "ecowatt-esp32-s3";
constexpr const char *MqttUser = "";
constexpr const char *MqttPassword = "";

constexpr const char *TelemetryTopic = "ecowatt/esp32/telemetry";
constexpr const char *StatusTopic = "ecowatt/esp32/status";

constexpr unsigned long TelemetryIntervalMs = 5000;
}
