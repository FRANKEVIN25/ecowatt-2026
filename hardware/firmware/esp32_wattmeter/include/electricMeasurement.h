#pragma once
#include <Arduino.h>
#include <EmonLib.h>
const double ADC_A_VOLTS = 5.0 / 1023.0;
//conversion_factor_modify
const double VOLTS_A_VRMS = 220 / 0.38; // diferencia entre voltaje maximo y el offset es el 0.38
const int16_t CENTRO_ADC = 512;         // verificar eso con el prototipo en fisico
const int16_t HISTERESIS = 0;
const int16_t UMBRAL_ALTO = CENTRO_ADC + HISTERESIS; // 542
const int16_t UMBRAL_BAJO = CENTRO_ADC - HISTERESIS; // 482
const double dephase_offset = -17.8; // en grados, se puede ajustar para compensar desfase fijo del circuito

struct Measurement
{
    EnergyMonitor emon;
    double vrms; // 8 bytes cada uno
    double frequency;
    double irms;
    double dephase;
    void voltageFrequencyMeasurement(uint8_t clocks);
    void currentMeasurement(uint8_t clocks);
    void allMeasurements(uint8_t clocks);
    void allMeasurementsSimulation(uint8_t clocks);
    void MeasurementSetup();
    void Measurementer_library();
};
