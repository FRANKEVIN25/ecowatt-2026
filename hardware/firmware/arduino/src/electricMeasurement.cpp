#include "electricMeasurement.h"

void Measurement::voltageFrequencyMeasurement(uint8_t clocks)
{
    uint16_t count = 0;
    int16_t adcValue = 0;
    bool positive_flank = true;
    uint32_t begin_time = 0;
    uint32_t elapsed_time = 16666; // Inicializado en un ciclo estándar de 60Hz

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
        adcValue = analogRead(A0);

        if (adcValue > max_val)
            max_val = adcValue;

        if (!begin_measurement)
        {
            if (adcValue >= 512 && !positive_flank)
            {
                begin_measurement = true;
                positive_flank = true;
                begin_time = micros(); // Sincronización inicial en microsegundos
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
            tiempo_actual = micros(); // Todo unificado en microsegundos
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

                uint32_t samples = sample_count;

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

                    // Serial.print("Muestras promedio por ciclo: ");
                    // Serial.println(samples);

                    // Serial.print("VRMS en ADC: ");
                    // Serial.println(vrms_promedio, 4);

                    Serial.print("VOLTAJE  (VRMS): ");
                    Serial.println(this->vrms, 4);

                    // Serial.print("Valor Maximo ADC registrado: ");
                    // Serial.println(max_val);
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
/**
 * @def currentMeasurement:
 * Según el datasheet del ACS712 la ecuación del voltaje respecto a la corriente es:
 * @return V_out = Vcc/2 + 0.2*I (para el modelo de 5A)
 */
void Measurement::currentMeasurement(uint8_t clocks)
{
    uint16_t count = 0;
    int16_t adcValue = 0;
    bool positive_flank = true;
    uint32_t begin_time = 0;
    uint32_t elapsed_time = 16666; // Inicializado en un ciclo estándar de 60Hz

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
        adcValue = analogRead(A1);

        if (adcValue > max_val)
            max_val = adcValue;

        if (!begin_measurement)
        {
            if (adcValue >= 512 && !positive_flank)
            {
                begin_measurement = true;
                positive_flank = true;
                begin_time = micros(); // Sincronización inicial en microsegundos
            }
            else if (adcValue < 512)
            {
                positive_flank = false;
            }
            continue;
        }
        // conversion_factor_modify
        i_inst = ((double)(adcValue)*ADC_A_VOLTS - 2.5) / 0.2; // Offset de 2.5V para el modelo de 5A originalmente
        // era 0.185
        sum_irms += i_inst * i_inst;
        sample_count++;

        if (adcValue >= UMBRAL_ALTO && !positive_flank)
        {
            positive_flank = true;
            tiempo_actual = micros(); // Todo unificado en microsegundos
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

                uint32_t samples = sample_count;

                sum_irms = 0.0;
                sample_count = 0;

                count++;

                if (count == clocks)
                {
                    this->frequency = sum_frequency_aux / clocks;
                    irms_mean = irms / clocks;
                    this->irms = irms_mean;

                    // Serial.print("Muestras promedio por ciclo: ");
                    // Serial.println(samples);

                    // Serial.print("VRMS en ADC: ");
                    // Serial.println(vrms_promedio, 4);

                    Serial.print("CORRIENTE (IRMS): ");
                    Serial.println(this->irms, 4);

                    // Serial.print("Valor Maximo ADC registrado: ");
                    // Serial.println(max_val);
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
    int16_t adcValue = 0;
    bool v_positive_flank = true;
    bool i_positive_flank = true;
    uint32_t v_begin_time = 0;
    uint32_t i_begin_time = 0;
    uint32_t elapsed_time = 16666; // Inicializado en un ciclo estándar de 60Hz

    double frequency_aux = 0.0;
    double sum_frequency_aux = 0.0;
    double sum_irms = 0.0;
    double irms = 0.0;

    uint32_t v_sample_count = 0;
    uint32_t i_sample_count = 0;
    uint16_t max_val = 0;
    bool begin_measurement = false;
    double i_inst = 0.0;
    uint32_t tiempo_actual;
    double irms_ciclo_actual;
    double irms_mean;
    double voltaje_inst = 0.0;
    double sum_vrms = 0.0;
    double vrms = 0.0;
    double vrms_ciclo_actual;
    double sum_phase_delay_us = 0.0;
    double vrms_mean;

    while (count < clocks)
    {
        int16_t adcValueVoltage = analogRead(A0);
        int16_t adcValueCurrent = analogRead(A1);

        if (!begin_measurement)
        {
            if (adcValueVoltage >= 512 && !v_positive_flank)
            {
                begin_measurement = true;
                v_positive_flank = true;
                v_begin_time = micros();
            }
            else if (adcValueVoltage < 512)
            {
                v_positive_flank = false;
            }
            continue;
        }

        double v_inst = (double)(adcValueVoltage - 512) * ADC_A_VOLTS;
        sum_vrms += v_inst * v_inst;
        v_sample_count++;

        double i_inst = (double)(adcValueCurrent * ADC_A_VOLTS - 2.5) / 0.2;
        sum_irms += i_inst * i_inst;
        i_sample_count++;

        if (adcValueCurrent >= UMBRAL_ALTO && !i_positive_flank)
        {
            i_positive_flank = true;
            i_begin_time = micros(); 
        }
        else if (adcValueCurrent < UMBRAL_BAJO && i_positive_flank)
        {
            i_positive_flank = false;
        }
        if (adcValueVoltage >= UMBRAL_ALTO && !v_positive_flank)
        {
            v_positive_flank = true;
            uint32_t tiempo_actual = micros();
            uint32_t elapsed_time = tiempo_actual - v_begin_time;
            v_begin_time = tiempo_actual;

            if (elapsed_time > 0)
            {
                sum_frequency_aux += (1000000.0 / elapsed_time);

                
                int32_t delay_us = (int32_t)(i_begin_time - tiempo_actual);

                while (delay_us > (int32_t)elapsed_time)
                    delay_us -= elapsed_time;
                while (delay_us < -(int32_t)elapsed_time)
                    delay_us += elapsed_time;
                sum_phase_delay_us += delay_us;

                if (v_sample_count > 0)
                    vrms += sqrt(sum_vrms / v_sample_count);
                if (i_sample_count > 0)
                    irms += sqrt(sum_irms / i_sample_count);

                sum_vrms = 0.0;
                v_sample_count = 0;
                sum_irms = 0.0;
                i_sample_count = 0;
                count++;

                if (count == clocks)
                {
                    this->frequency = sum_frequency_aux / clocks;
                    double vrms_mean = vrms / clocks;
                    double irms_mean = irms / clocks;

                    this->vrms = vrms_mean * VOLTS_A_VRMS;
                    this->irms = irms_mean;

                    double avg_delay_us = sum_phase_delay_us / clocks;
                    double periodo_promedio_us = 1000000.0 / this->frequency;
                    double desfase_grados = (avg_delay_us / periodo_promedio_us) * 360.0;

                    if (desfase_grados > 180.0)
                        desfase_grados -= 360.0;
                    if (desfase_grados < -180.0)
                        desfase_grados += 360.0;

                    Serial.println("============ MEDICIÓN ELÉCTRICA COMBINADA ============");
                    Serial.print("Frecuencia Red: ");
                    Serial.print(this->frequency, 2);
                    Serial.println(" Hz");
                    Serial.print("Voltaje (VRMS): ");
                    Serial.print(this->vrms, 4);
                    Serial.println(" V");
                    Serial.print("Corriente (IRMS): ");
                    Serial.print(this->irms, 4);
                    Serial.println(" A");
                    Serial.print("Desfase Eléctrico: ");
                    Serial.print(desfase_grados, 2);
                    Serial.println("°");

                   
                }
            }
        }
        else if (adcValueVoltage < UMBRAL_BAJO && v_positive_flank)
        {
            v_positive_flank = false;
        }
    }
}