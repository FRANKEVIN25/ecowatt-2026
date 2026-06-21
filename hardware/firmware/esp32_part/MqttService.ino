#include "MqttService.h"

#include <ArduinoJson.h>
#include <WiFi.h>

#include "AppConfig.h"

void MqttService::begin()
{
  WiFi.mode(WIFI_STA);

  secureClient.setInsecure();
  mqttClient.setClient(secureClient);
  mqttClient.setServer(AppConfig::MqttHost, AppConfig::MqttPort);
  mqttClient.setBufferSize(512);

  connectToWifi();
}

void MqttService::loop()
{
  const unsigned long now = millis();

  if (wifiReady) {
    mqttClient.loop();
  }

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
    Serial.println("WiFi desconectado");
  }

  if (!connected && now - lastWifiReconnectAttemptMs >= 5000)
  {
    connectToWifi();
  }

  if (connected && !mqttClient.connected() && now - lastMqttReconnectAttemptMs >= 3000)
  {
    connectToMqtt();
  }
}

bool MqttService::isConnected()
{
  return mqttClient.connected();
}

bool MqttService::publishTelemetry(float voltage, float current, float power, float phi, float fp, float kwh)
{
  JsonDocument doc;
  doc["V"] = voltage;
  doc["I"] = current;
  doc["P"] = power;
  doc["phi"] = phi;
  doc["fp"] = fp;
  doc["kWh"] = kwh;
  doc["cuarto"] = "principal";

  String payload;
  serializeJson(doc, payload);

  return publishMessage(AppConfig::TelemetryTopic, payload);
}

bool MqttService::publishMessage(const char *topic, const String &payload, bool retain)
{
  if (!mqttClient.connected())
  {
    Serial.println("MQTT no conectado, publicacion omitida");
    return false;
  }

  return mqttClient.publish(topic, payload.c_str(), retain);
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

  const bool ok = mqttClient.connect(
      AppConfig::MqttClientId,
      AppConfig::MqttUser,
      AppConfig::MqttPassword
  );

  if (ok) {
    Serial.println("MQTT conectado");
    mqttClient.publish(AppConfig::StatusTopic, "{\"status\":\"online\"}", true);
  } else {
    Serial.print("MQTT fallo, rc=");
    Serial.println(mqttClient.state());
  }
}