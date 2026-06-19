#pragma once
#include <Arduino.h>

const double ADC_A_VOLTS = 5.0 / 1023.0;
//conversion_factor_modify
const double VOLTS_A_VRMS = 220 / 0.38; // diferencia entre voltaje maximo y el offset es el 0.38
const int16_t CENTRO_ADC = 512;         // verificar eso con el prototipo en fisico
const int16_t HISTERESIS = 30;
const int16_t UMBRAL_ALTO = CENTRO_ADC + HISTERESIS; // 542
const int16_t UMBRAL_BAJO = CENTRO_ADC - HISTERESIS; // 482

struct Measurement
{
    double vrms; // 8 bytes cada uno
    double frequency;
    double irms;
    double dephase;
    double dephase_offset;

    void voltageFrequencyMeasurement(uint8_t clocks);
    void currentMeasurement(uint8_t clocks);
    void allMeasurements(uint8_t clocks);
};
