#include "MqttService.h"

#include <ArduinoJson.h>
#include <WiFi.h>

#include "AppConfig.h"

void MqttService::begin()
{
  WiFi.mode(WIFI_STA);

  mqttClient.onConnect([this](bool sessionPresent)
                       { handleMqttConnect(sessionPresent); });

  mqttClient.onDisconnect([this](AsyncMqttClientDisconnectReason reason)
                          { handleMqttDisconnect(reason); });

  mqttClient.onPublish([this](uint16_t packetId)
                       { handleMqttPublish(packetId); });

  mqttClient.setServer(AppConfig::MqttHost, AppConfig::MqttPort);
  mqttClient.setClientId(AppConfig::MqttClientId);

  if (strlen(AppConfig::MqttUser) > 0)
  {
    mqttClient.setCredentials(AppConfig::MqttUser, AppConfig::MqttPassword);
  }

  connectToWifi();
}

void MqttService::loop()
{
  const unsigned long now = millis();

  if (now - lastWifiCheckMs < 1000)
  {
    return;
  }

  lastWifiCheckMs = now;
  const bool connected = WiFi.status() == WL_CONNECTED;

  if (connected && !wifiReady)
  {
    wifiReady = true;
    Serial.print("WiFi conectado. IP: ");
    Serial.println(WiFi.localIP());
    connectToMqtt();
    return;
  }

  if (!connected && wifiReady)
  {
    wifiReady = false;
    mqttReconnectPending = false;
    Serial.println("WiFi desconectado");
  }

  if (!connected && now - lastWifiReconnectAttemptMs >= 5000)
  {
    connectToWifi();
  }

  if (connected && mqttReconnectPending && now - lastMqttReconnectAttemptMs >= 2000)
  {
    connectToMqtt();
  }
}

bool MqttService::isConnected() const
{
  return mqttClient.connected();
}

bool MqttService::publishTelemetry(float voltage, float current, float power)
{
  JsonDocument doc;
  doc["voltage"] = voltage;
  doc["current"] = current;
  doc["power"] = power;
  doc["uptime_ms"] = millis();

  String payload;
  serializeJson(doc, payload);

  return publishMessage(AppConfig::TelemetryTopic, payload);
}

bool MqttService::publishMessage(const char *topic, const String &payload, bool retain, uint8_t qos)
{
  if (!mqttClient.connected())
  {
    Serial.println("MQTT no conectado, publicacion omitida");
    return false;
  }

  const uint16_t packetId = mqttClient.publish(topic, qos, retain, payload.c_str());
  return packetId > 0 || qos == 0;
}

void MqttService::connectToWifi()
{
  lastWifiReconnectAttemptMs = millis();
  Serial.print("Conectando a WiFi: ");
  Serial.println(AppConfig::WiFiSsid);
  WiFi.begin(AppConfig::WiFiSsid, AppConfig::WiFiPassword);
}

void MqttService::connectToMqtt()
{
  if (!wifiReady)
  {
    return;
  }

  Serial.print("Conectando a MQTT: ");
  Serial.print(AppConfig::MqttHost);
  Serial.print(":");
  Serial.println(AppConfig::MqttPort);
  lastMqttReconnectAttemptMs = millis();
  mqttReconnectPending = false;
  mqttClient.connect();
}

void MqttService::handleMqttConnect(bool sessionPresent)
{
  Serial.print("MQTT conectado. Sesion previa: ");
  Serial.println(sessionPresent ? "si" : "no");
  publishMessage(AppConfig::StatusTopic, "{\"status\":\"online\"}", true);
}

void MqttService::handleMqttDisconnect(AsyncMqttClientDisconnectReason reason)
{
  Serial.print("MQTT desconectado. Motivo: ");
  Serial.println(static_cast<int>(reason));

  if (wifiReady)
  {
    mqttReconnectPending = true;
    lastMqttReconnectAttemptMs = millis();
  }
}

void MqttService::handleMqttPublish(uint16_t packetId)
{
  Serial.print("MQTT publicado. Packet ID: ");
  Serial.println(packetId);
}
