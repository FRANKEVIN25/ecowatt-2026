#include <Arduino.h>
#include <electricMeasurement.h>

#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif

Measurement measurement;
void setup()
{
    Serial.begin(115200);
    delay(100); // Estabilización para Proteus
    // sbi(ADCSRA, ADPS2);
    // cbi(ADCSRA, ADPS1);
    // cbi(ADCSRA, ADPS0);
    measurement.MeasurementSetup();
}

void loop()
{
    //    measurement.voltageFrequencyMeasurement(200);
    //    measurement.currentMeasurement(200);
    // measurement.allMeasurementsSimulation(400);
    measurement.Measurementer_library();
}
