#pragma once

namespace AppConfig {
constexpr const char *WiFiSsid = "JEJ";
constexpr const char *WiFiPassword = "JEJ031128";

constexpr const char *MqttHost = "931785ba21584ed1825ec9d6dc15ab73.s1.eu.hivemq.cloud";
constexpr unsigned int MqttPort = 8883;
constexpr const char *MqttClientId = "ecowatt-esp32-s3";
constexpr const char *MqttUser = "ecowatt_app";
constexpr const char *MqttPassword = "EcoWatt2026Hack!";

constexpr const char *TelemetryTopic = "ecowatt/medicion";
constexpr const char *StatusTopic = "ecowatt/esp32/status";

constexpr unsigned long TelemetryIntervalMs = 5000;
}
