#include "electricMeasurement.h"

void Measurement::voltageFrequencyMeasurement(uint8_t clocks)
{
    uint16_t count = 0;
    int16_t adcValue = 0;
    bool positive_flank = true;
    uint32_t begin_time = 0;
    uint32_t elapsed_time = 16666;
    double frequency_aux = 0.0;
    double sum_frequency_aux = 0.0;
    double sum_vrms = 0.0;
    double vrms = 0.0;
    uint32_t sample_count = 0;
    uint16_t max_val = 0;
    bool begin_measurement = false;
    double voltaje_inst = 0.0;
    uint32_t tiempo_actual;
    double vrms_ciclo_actual;
    double vrms_promedio;

    while (count < clocks)
    {
        adcValue = analogRead(36);
        if (adcValue > max_val)
            max_val = adcValue;

        if (!begin_measurement)
        {
            if (adcValue >= 512 && !positive_flank)
            {
                begin_measurement = true;
                positive_flank = true;
                begin_time = micros();
            }
            else if (adcValue < 512)
            {
                positive_flank = false;
            }
            continue;
        }

        voltaje_inst = (double)(adcValue - 512) * ADC_A_VOLTS;
        sum_vrms += voltaje_inst * voltaje_inst;
        sample_count++;

        if (adcValue >= UMBRAL_ALTO && !positive_flank)
        {
            positive_flank = true;
            tiempo_actual = micros();
            elapsed_time = tiempo_actual - begin_time;
            begin_time = tiempo_actual;

            if (elapsed_time > 0)
            {
                frequency_aux = 1000000.0 / elapsed_time;
                sum_frequency_aux += frequency_aux;

                if (sample_count > 0)
                {
                    vrms_ciclo_actual = sqrt(sum_vrms / sample_count);
                    vrms += vrms_ciclo_actual;
                }

                sum_vrms = 0.0;
                sample_count = 0;
                count++;

                if (count == clocks)
                {
                    this->frequency = sum_frequency_aux / clocks;
                    vrms_promedio = vrms / clocks;
                    this->vrms = vrms_promedio * VOLTS_A_VRMS;

                    Serial.print("Frecuencia Promedio (Hz) despues de ");
                    Serial.print(clocks);
                    Serial.print(" ciclos: ");
                    Serial.println(this->frequency, 2);
                    Serial.print("VOLTAJE  (VRMS): ");
                    Serial.println(this->vrms, 4);
                    Serial.println("--------------------------------------------------");
                }
            }
        }
        else if (adcValue < UMBRAL_BAJO && positive_flank)
        {
            positive_flank = false;
        }
    }
}

void Measurement::currentMeasurement(uint8_t clocks)
{
    uint16_t count = 0;
    int16_t adcValue = 0;
    bool positive_flank = true;
    uint32_t begin_time = 0;
    uint32_t elapsed_time = 16666;
    double frequency_aux = 0.0;
    double sum_frequency_aux = 0.0;
    double sum_irms = 0.0;
    double irms = 0.0;
    uint32_t sample_count = 0;
    uint16_t max_val = 0;
    bool begin_measurement = false;
    double i_inst = 0.0;
    uint32_t tiempo_actual;
    double irms_ciclo_actual;
    double irms_mean;

    while (count < clocks)
    {
        adcValue = analogRead(39);
        if (adcValue > max_val)
            max_val = adcValue;

        if (!begin_measurement)
        {
            if (adcValue >= 512 && !positive_flank)
            {
                begin_measurement = true;
                positive_flank = true;
                begin_time = micros();
            }
            else if (adcValue < 512)
            {
                positive_flank = false;
            }
            continue;
        }

        i_inst = ((double)(adcValue)*ADC_A_VOLTS - 2.5) / 0.2;
        sum_irms += i_inst * i_inst;
        sample_count++;

        if (adcValue >= UMBRAL_ALTO && !positive_flank)
        {
            positive_flank = true;
            tiempo_actual = micros();
            elapsed_time = tiempo_actual - begin_time;
            begin_time = tiempo_actual;

            if (elapsed_time > 0)
            {
                frequency_aux = 1000000.0 / elapsed_time;
                sum_frequency_aux += frequency_aux;

                if (sample_count > 0)
                {
                    irms_ciclo_actual = sqrt(sum_irms / sample_count);
                    irms += irms_ciclo_actual;
                }

                sum_irms = 0.0;
                sample_count = 0;
                count++;

                if (count == clocks)
                {
                    this->frequency = sum_frequency_aux / clocks;
                    irms_mean = irms / clocks;
                    this->irms = irms_mean;

                    Serial.print("CORRIENTE (IRMS): ");
                    Serial.println(this->irms, 4);
                    Serial.println("--------------------------------------------------");
                }
            }
        }
        else if (adcValue < UMBRAL_BAJO && positive_flank)
        {
            positive_flank = false;
        }
    }
}

void Measurement::allMeasurements(uint8_t clocks)
{
    uint16_t count = 0;
    bool v_positive_flank = true;
    bool i_positive_flank = true;

    uint32_t v_begin_time = 0;
    uint32_t v_begin_time_all = 0;
    uint32_t i_begin_time = 0;

    double sum_frequency_aux = 0.0;
    double sum_vrms = 0.0;
    double sum_irms = 0.0;
    double sum_potencia_activa = 0.0;

    uint32_t cycle_samples = 0;
    uint32_t total_samples = 0;

    bool begin_measurement_voltage = false;
    bool begin_measurement_current = false;
    bool desfase_calculado = false;
    int32_t desfase_inicial_us = 0;

    double vrms_acumulado = 0.0;
    double irms_acumulado = 0.0;

    while (count < clocks)
    {
        int16_t adcValueVoltage = analogRead(36);
        int16_t adcValueCurrent = analogRead(39);

        // FASE DE SINCRONIZACIÓN INICIAL ÚNICA (Solo mide el primer flanco de cada una)
        if (!begin_measurement_voltage)
        {
            if (adcValueVoltage >= 512 && !v_positive_flank)
            {
                begin_measurement_voltage = true;
                v_positive_flank = true;
                v_begin_time_all = micros(); // Tiempo del primer flanco de voltaje
                v_begin_time = v_begin_time_all;
            }
            else if (adcValueVoltage < 512)
            {
                v_positive_flank = false;
            }
            // No hacemos 'continue' para permitir que la corriente se sincronice concurrentemente
        }

        if (!begin_measurement_current && count <= clocks / 2)
        {
            if (adcValueCurrent >= 512 && !i_positive_flank)
            {
                begin_measurement_current = true;
                i_positive_flank = true;
                i_begin_time = micros(); // Tiempo del primer flanco de corriente
            }
            else if (adcValueCurrent < 512)
            {
                i_positive_flank = false;
            }
        }

        // Si alguna de las dos señales no ha tenido su primer flanco, esperamos sin acumular datos RMS
        if (!begin_measurement_voltage || !begin_measurement_current)
        {
            continue;
        }

        // CÁLCULO DEL DESFASE INICIAL (Se ejecuta UNA SOLA VEZ en la historia de la función)

        // ACUMULACIÓN DE VALORES INSTANTÁNEOS (Corrección de fórmula unificada)
        double v_inst = (double)(adcValueVoltage - 512) * ADC_A_VOLTS;
        sum_vrms += v_inst * v_inst;

        double i_inst = ((double)(adcValueCurrent)*ADC_A_VOLTS - 2.5) / 0.2;
        sum_irms += i_inst * i_inst;

        sum_potencia_activa += (v_inst * i_inst);
        cycle_samples++;
        total_samples++;

        // DETECCIÓN DE FIN DE CICLO (Únicamente basado en Voltaje)
        if (adcValueVoltage >= UMBRAL_ALTO && !v_positive_flank)
        {
            v_positive_flank = true;
            uint32_t tiempo_actual = micros();
            uint32_t elapsed_time = tiempo_actual - v_begin_time;

            if (elapsed_time > 0)
            {
                sum_frequency_aux += (1000000.0 / elapsed_time);

                if (cycle_samples > 0)
                {
                    vrms_acumulado += sqrt(sum_vrms / cycle_samples);
                    irms_acumulado += sqrt(sum_irms / cycle_samples);
                }

                // REINICIO DE VARIABLES PARA EL SIGUIENTE CICLO
                sum_vrms = 0.0;
                sum_irms = 0.0;
                cycle_samples = 0;

                v_begin_time = tiempo_actual;
                count++;

                // PROCESAMIENTO FINAL AL COMPLETAR LOS CICLOS REQUERIDOS
                if (count == clocks)
                {
                    this->frequency = sum_frequency_aux / clocks;
                    this->vrms = (vrms_acumulado / clocks) * VOLTS_A_VRMS;
                    this->irms = irms_acumulado / clocks;

                    double potencia_activa = (sum_potencia_activa / total_samples) * VOLTS_A_VRMS;
                    double potencia_aparente = this->vrms * this->irms;

                    // Procesamos el único desfase guardado al inicio

                    int32_t delta_tiempo = (int32_t)(i_begin_time - v_begin_time_all);

                    double periodo_promedio_us = 1000000.0 / this->frequency;
                    while (delta_tiempo > (int32_t)(periodo_promedio_us / 2))
                    {
                        delta_tiempo -= periodo_promedio_us;
                    }
                    while (delta_tiempo < -(int32_t)(periodo_promedio_us / 2))
                    {
                        delta_tiempo += periodo_promedio_us;
                    }
                    double desfase_final_us = (double)delta_tiempo;

                    // Factor de potencia calculado por ese desfase de tiempo inicial

                    // Filtro de vacío para corrientes despreciables (Menores a 5mA)

                    // desfase_final_us -= 32.0; // Compensación fija por retraso de lecturas del ADC

                    double desfase_grados = (desfase_final_us * 360.0) / periodo_promedio_us;
                    double fp = cos(desfase_grados * (PI / 180.0));

                    // if (this->irms < 0.005)
                    // {
                    //     this->irms = 0.0;
                    //     potencia_activa = 0.0;
                    //     desfase_final_us = 0.0;
                    //     desfase_grados = 0.0;
                    //     fp = 1.0;
                    // }

                    // IMPRESIÓN DE RESULTADOS
                    Serial.println("============ MEDICIÓN ELÉCTRICA COMBINADA (Primer Flanco) ============");
                    Serial.print("Frecuencia Red: ");
                    Serial.print(this->frequency, 2);
                    Serial.println(" Hz");
                    Serial.print("Voltaje (VRMS): ");
                    Serial.print(this->vrms, 4);
                    Serial.println(" V");
                    Serial.print("Corriente (IRMS): ");
                    Serial.print(this->irms, 4);
                    Serial.println(" A");
                    Serial.print("Potencia Activa: ");
                    Serial.print(potencia_activa, 2);
                    Serial.println(" W");
                    Serial.print("Factor de Potencia: ");
                    Serial.println(fp, 4);
                    Serial.print("Desfase (Tiempo): ");
                    Serial.print(desfase_final_us, 1);
                    Serial.println(" us");
                    Serial.print("Desfase (Grados): ");
                    Serial.print(desfase_grados, 2);
                    Serial.println("°");

                    if (desfase_grados > 0.5)
                        Serial.println("Tipo de Carga: CAPACITIVA (Corriente Adelantada)");
                    else if (desfase_grados < -0.5)
                        Serial.println("Tipo de Carga: INDUCTIVA (Corriente Retrasada)");
                    else
                        Serial.println("Tipo de Carga: RESISTIVA PURA");
                    Serial.println("=====================================================================");
                }
            }
        }
        else if (adcValueVoltage < UMBRAL_BAJO && v_positive_flank)
        {
            v_positive_flank = false;
        }
    }
}

void Measurement::allMeasurementsSimulation(uint8_t clocks)
{
    uint8_t count = 0;

    bool v_positive_flank = true;
    bool i_positive_flank = true;

    bool begin_measurement_voltage = false;
    bool begin_measurement_current = false;

    bool i_edge_detected_this_cycle = false;

    uint32_t total_samples = 0;
    uint32_t cycle_samples = 0;

    double sum_frequency = 0.0;
    double sum_vrms = 0.0;
    double sum_irms = 0.0;
    double sum_power = 0.0;
    double sum_phase_us = 0.0;

    double vrms_accum = 0.0;
    double irms_accum = 0.0;

    uint32_t v_cross_time = 0;
    uint32_t i_cross_time = 0;

    //---------------------------------
    // Variables para interpolación
    //---------------------------------
    int16_t prevV = analogRead(36); //A0
    int16_t prevI = analogRead(39); //A1

    uint32_t prevTime = micros();

    //---------------------------------
    // Filtro IIR
    //--------------------------------
    float vf = prevV;
    float ifilt = prevI;

    const float ALPHA = 0.15f;

    //---------------------------------
    // Arduino UNO:
    // ~104 us entre lecturas ADC
    //---------------------------------
    const float ADC_DELAY_US = 104.0f;

    while (count < clocks)
    {
        int16_t rawV = analogRead(36);
        int16_t rawI = analogRead(39);

        uint32_t now = micros();

        //---------------------------------
        // FILTRO
        //---------------------------------
        vf = vf + ALPHA * ((float)rawV - vf);
        ifilt = ifilt + ALPHA * ((float)rawI - ifilt);

        int16_t adcValueVoltage = (int16_t)vf;
        int16_t adcValueCurrent = (int16_t)ifilt;

        //---------------------------------
        // SINCRONIZACIÓN INICIAL VOLTAJE
        //---------------------------------
        if (!begin_measurement_voltage)
        {
            if (adcValueVoltage >= 512 && !v_positive_flank)
            {
                float frac =
                    (512.0f - prevV) /
                    ((float)adcValueVoltage - prevV);

                v_cross_time =
                    prevTime +
                    (uint32_t)((now - prevTime) * frac);

                begin_measurement_voltage = true;
                v_positive_flank = true;
            }
            else if (adcValueVoltage < 512)
            {
                v_positive_flank = false;
            }
        }

        //---------------------------------
        // CRUCE CORRIENTE
        //---------------------------------
        if (begin_measurement_voltage)
        {
            if (adcValueCurrent >= UMBRAL_ALTO &&
                !i_positive_flank)
            {
                i_positive_flank = true;

                if (!i_edge_detected_this_cycle)
                {
                    float frac =
                        (512.0f - prevI) /
                        ((float)adcValueCurrent - prevI);

                    i_cross_time =
                        prevTime +
                        (uint32_t)((now - prevTime) * frac);

                    // compensar lectura secuencial ADC
                    i_cross_time -= (uint32_t)ADC_DELAY_US;

                    i_edge_detected_this_cycle = true;
                    begin_measurement_current = true;
                }
            }
            else if (adcValueCurrent < UMBRAL_BAJO)
            {
                i_positive_flank = false;
            }
        }

        //---------------------------------
        // ESPERAR SINCRONIZACIÓN
        //---------------------------------
        if (!begin_measurement_voltage ||
            !begin_measurement_current)
        {
            prevV = adcValueVoltage;
            prevI = adcValueCurrent;
            prevTime = now;
            continue;
        }

        //---------------------------------
        // VALORES INSTANTÁNEOS
        //---------------------------------
        double v_inst =
            ((double)rawV - 512.0) *
            ADC_A_VOLTS;

        double i_inst =
            (((double)rawI * ADC_A_VOLTS) - 2.5) /
            0.185; // ACS712 5A

        sum_vrms += v_inst * v_inst;
        sum_irms += i_inst * i_inst;

        sum_power += v_inst * i_inst;

        cycle_samples++;
        total_samples++;

        //---------------------------------
        // FIN DE CICLO DE VOLTAJE
        //---------------------------------
        if (adcValueVoltage >= UMBRAL_ALTO &&
            !v_positive_flank)
        {
            v_positive_flank = true;

            float frac =
                (512.0f - prevV) /
                ((float)adcValueVoltage - prevV);

            uint32_t current_cross =
                prevTime +
                (uint32_t)((now - prevTime) * frac);

            uint32_t elapsed =
                current_cross - v_cross_time;

            if (elapsed > 1000)
            {
                double freq =
                    1000000.0 /
                    (double)elapsed;

                sum_frequency += freq;

                if (cycle_samples > 0)
                {
                    vrms_accum +=
                        sqrt(sum_vrms /
                             cycle_samples);

                    irms_accum +=
                        sqrt(sum_irms /
                             cycle_samples);
                }

                //---------------------------------
                // DESFASE
                //---------------------------------
                if (i_edge_detected_this_cycle)
                {
                    int32_t delta =
                        (int32_t)v_cross_time -
                        (int32_t)i_cross_time;

                    double T = elapsed;

                    while (delta > T / 2)
                        delta -= T;

                    while (delta < -T / 2)
                        delta += T;

                    sum_phase_us += delta;
                }

                //---------------------------------
                // RESET CICLO
                //---------------------------------
                sum_vrms = 0;
                sum_irms = 0;
                cycle_samples = 0;

                i_edge_detected_this_cycle = false;

                v_cross_time = current_cross;

                count++;
            }

            //---------------------------------
            // RESULTADOS FINALES
            //---------------------------------
            if (count == clocks)
            {
                this->frequency =
                    sum_frequency / clocks;

                this->vrms =
                    (vrms_accum / clocks) *
                    VOLTS_A_VRMS;

                this->irms =
                    irms_accum / clocks;

                double power =
                    (sum_power /
                     total_samples) *
                    VOLTS_A_VRMS;

                double phase_us =
                    sum_phase_us /
                    clocks;

                double T =
                    1000000.0 /
                    this->frequency;

                double phase_deg =
                    (phase_us * 360.0) /
                    T;
                phase_deg -= dephase_offset; // Compensación por desfase fijo del circuito a ver

                double fp =
                    cos(phase_deg *
                        DEG_TO_RAD);

                if (this->irms < 0.010)
                {
                    this->irms = 0;
                    power = 0;
                    phase_us = 0;
                    phase_deg = 0;
                    fp = 1.0;
                }

                Serial.println();
                Serial.println(F("========= RESULTADOS ========="));

                Serial.print(F("Frecuencia: "));
                Serial.print(this->frequency, 3);
                Serial.println(F(" Hz"));

                Serial.print(F("VRMS: "));
                Serial.print(this->vrms, 3);
                Serial.println(F(" V"));

                Serial.print(F("IRMS: "));
                Serial.print(this->irms, 4);
                Serial.println(F(" A"));

                Serial.print(F("Potencia: "));
                Serial.print(power, 2);
                Serial.println(F(" W"));

                Serial.print(F("FP: "));
                Serial.println(fp, 4);

                Serial.print(F("Desfase us: "));
                Serial.println(phase_us, 1);

                Serial.print(F("Desfase grados: "));
                Serial.println(phase_deg, 2);

                if (phase_deg > 0.5)
                    Serial.println(F("CAPACITIVA"));
                else if (phase_deg < -0.5)
                    Serial.println(F("INDUCTIVA"));
                else
                    Serial.println(F("RESISTIVA"));

                Serial.println(F("=============================="));
            }
        }
        else if (adcValueVoltage < UMBRAL_BAJO &&
                 v_positive_flank)
        {
            v_positive_flank = false;
        }

        prevV = adcValueVoltage;
        prevI = adcValueCurrent;
        prevTime = now;
    }
}
void Measurement::Measurementer_library()
{
    this->emon.calcVI(20, 2000);

    Serial.print("Vrms: ");
    Serial.println(this->emon.Vrms);

    Serial.print("Irms: ");
    Serial.println(this->emon.Irms);

    Serial.print("Power: ");
    Serial.println(this->emon.realPower);

    Serial.print("PF: ");
    Serial.println(this->emon.powerFactor);

float pf = this->emon.powerFactor;

// seguridad numérica
if (pf > 1) pf = 1;
if (pf < -1) pf = -1;

float angle = acos(pf) * 180.0 / PI;

Serial.println(angle);}

void Measurement::MeasurementSetup()
{
    this->emon.voltage(36, 530, -8); //572 y -1.5 simulaion Configura el pin de voltaje y el factor de calibración
    this->emon.current(39, 12);   //5.405 Configura el pin de corriente y el factor de calibración para ACS712 5A
}
