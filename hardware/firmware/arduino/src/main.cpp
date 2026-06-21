#include <Arduino.h>
#include <electricMeasurement.h>
#include <ArduinoJson.h>
#include <SoftwareSerial.h>
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
SoftwareSerial Serial2(10,11);

Measurement measurement;
JsonDocument json;
double data[5] = {0, 0, 0, 0, 0};
void setup()
{
    Serial.begin(115200);
    Serial2.begin(115200);

    delay(100); // Estabilización para Proteus
    sbi(ADCSRA, ADPS2);
    cbi(ADCSRA, ADPS1);
    cbi(ADCSRA, ADPS0);
    measurement.MeasurementSetup();
}

void loop()
{
    // measurement.voltageFrequencyMeasurement(200);
    // measurement.currentMeasurement(200);
    //  measurement.allMeasurementsSimulation(400);
    measurement.Measurementer_library();
    data[0] = measurement.emon.Vrms;
    data[1] = measurement.emon.Irms;
    data[2] = measurement.emon.powerFactor;
    data[3] = measurement.emon.realPower;
    data[4] = measurement.dephase;

    Serial2.print((uint8_t) data);
}
