#include <Arduino.h>
int16_t adcValue = 0;
void cambiarCanalADC(uint8_t pin);
bool positive_flank = true;
uint32_t begin_time = 0;
uint32_t elapsed_time = 5000;
double frequency_aux = 0.0;
double sum_frequency_aux = 0.0;
double sum_vrms = 0.0;
double vrms = 0.0;
double frequency = 0.0;
uint8_t times = 200;
uint8_t count = 0;
uint32_t sample_count = 0;
uint16_t max_val=0;
const double ADC_A_VOLTS = 5.0 / 1023.0;
const double VOLTS_A_VRMS = 220 / 1.0142;
void setup()
{
    Serial.begin(115200);
    delay(100);                                                                       // Estabilización para Proteus
    ADCSRA = (1 << ADEN) | (1 << ADATE) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); // 125KHz

    ADMUX = (1 << REFS0); // Usa el voltaje de referencia de 5V y selecciona A0 (0000)

    ADCSRB = 0; // Configura el trigger como "Modo Libre"

    ADCSRA |= (1 << ADSC);

    DDRB |= (1 << DDB0);
    PORTB |= (1 << PORTB0);
}

void loop()
{
    // cambiarCanalADC(0);
    if (!(ADCSRA & (1 << ADSC))) // desbloquea la conversion adc
    {
        ADCSRA |= (1 << ADSC);
    }
    adcValue = ADC;
    double voltaje_inst = (double)(adcValue - 512) * ADC_A_VOLTS; // Convertir el valor ADC a voltaje
    sum_vrms += voltaje_inst * voltaje_inst;                      // Acumular el cuadrado del voltaje para RMS
    sample_count++;

    if (adcValue >= 512 && !positive_flank)
    {
        positive_flank = true; // Ya subió, bloqueamos este IF hasta que vuelva a bajar
        uint32_t tiempo_actual = millis();
        elapsed_time = tiempo_actual - begin_time; // Tiempo que duró EL CICLO COMPLETO
        begin_time = tiempo_actual;                // Reiniciamos el cronómetro para el siguiente ciclo

        // Evitamos el crash de división por cero por si acaso
        if (elapsed_time > 0)
        {
            // 1000.0 ms porque estamos midiendo el periodo completo (T)
            frequency_aux = 1000.0 / elapsed_time;
            sum_frequency_aux += frequency_aux;

            if (sample_count > 0)
            {
                double vrms_ciclo_actual = sqrt(sum_vrms / sample_count);
                vrms += vrms_ciclo_actual; // Acumulamos el RMS real calculado
            }

            count++;
            if (count == times)
            {
                // 1. Promediar la frecuencia acumulada
                frequency = sum_frequency_aux / times;
                Serial.print("Frecuencia Promedio (Hz) despues de ");
                Serial.print((int)times);
                Serial.print(" mediciones: ");
                Serial.println(frequency);

                // 2. Promediar el VRMS acumulado (¡Sin recalcular raíces de variables en cero!)
                double vrms_promedio = vrms / times;
                Serial.print("VRMS despues de ");
                Serial.print((uint32_t)sample_count);
                Serial.print(" mediciones: ");
                Serial.println(vrms_promedio, 4);
                Serial.print("Valor Maximo VRMS: ");
                Serial.println(vrms_promedio * VOLTS_A_VRMS, 4);
                Serial.println("--------------------------------------------------");   
                // 3. Reinicio limpio de todos los acumuladores generales
                count = 0;
                sum_frequency_aux = 0.0;
                sum_vrms = 0.0;
                sample_count = 0;
                vrms = 0.0;
                vrms_promedio = 0.0; // Dejar listo el acumulador de RMS para la siguiente tanda de 200
            }
        }
    }
    // Si la señal cae por debajo de 512, habilitamos la siguiente medición de subida
    else if (adcValue < 512 && positive_flank)
    {
        positive_flank = false;
    }
    // if(adcValue > max_val){
    //     max_val = adcValue;
    // }
}

/**
 * @brief Cambia el canal del ADC a un pin específico (A0 a A5) sin afectar la referencia de voltaje ni el modo de operación.
 */
void cambiarCanalADC(uint8_t pin)
{
    // Desactivar temporalmente el ADC
    ADCSRA &= ~(1 << ADEN);

    // Limpiar los bits MUX viejos en ADMUX (bits 0, 1, 2 y 3)
    // Dejamos intactos los bits de referencia de voltaje
    ADMUX &= ~((1 << MUX3) | (1 << MUX2) | (1 << MUX1) | (1 << MUX0));

    // Configurar los nuevos bits MUX según el pin deseado (A0 a A5)
    // El pin A0 es 0, A1 es 1, A2 es 2, etc.
    ADMUX |= (pin & 0x07);

    // Volver a encender el ADC e iniciar la nueva conversión automática
    ADCSRA |= (1 << ADEN) | (1 << ADSC);
}