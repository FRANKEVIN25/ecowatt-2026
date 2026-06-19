#include <Arduino.h>
#include <electricMeasurement.h>
Measurement measurement;
void setup()
{
    Serial.begin(115200);
    delay(100); // Estabilización para Proteus
    

}

void loop()
{
//    measurement.voltageFrequencyMeasurement(200);
//    measurement.currentMeasurement(200);
    measurement.allMeasurements(200);
    
}
