void setup() {
  Serial.begin(9600, SERIAL_8N1);
  // EN PROTEUS FUNCIONA A 8 MHZ → Asumir que el delay tarda dos veces más
  // ADC-6 → REFERENCE
  // ADC-7 → READ
}

void loop() {
  uint16_t counter = 0;
  float rms = 0;
  int8_t buffer[256] = {};

  // Obtener 256 muestras cada 1 milisegundo
  while(counter < 256){
    int8_t input = (analogRead(A7)>>2) - (analogRead(A6)>>2);
    buffer[counter] = input;
    counter ++;
    delayMicroseconds(280);
  }

  // Calcular voltaje RMS
  counter = 0;
  while(counter < 256){
    rms = rms + buffer[counter]*buffer[counter];
    counter ++;
  }
  rms = 5*sqrt(rms/256)/256;

  int8_t output[64] = {};
  bool state = false;
  counter = 0;

  while(counter < 256){
    if(buffer[counter]>1 and not state){
      output[counter] = 1;
      state = true;
    }else if(buffer[counter]<-1 and state){
      output[counter] = -1;
      state = false;
    }else if(state){
      output[counter] = 1;
    }else if(not state){
      output[counter] = -1;
    }
    counter ++;
  }

  state = false;
  uint8_t semicycle[32] = {};
  uint8_t on_state = 0;
  uint8_t off_state = 0;
  uint8_t b = 0;
  counter = 0;

  while(counter < 256){
    if(buffer[counter]>1 and not state){
      semicycle[b] = off_state;
      b ++;
      off_state = 0;
      on_state ++;
      state = true;
    }else if(buffer[counter]<-1 and state){
      semicycle[b] = on_state;
      b ++;
      on_state = 0;
      off_state ++;
      state = false;
    }else if(state){
      on_state ++;
    }else if(not state){
      off_state ++;
    }
    counter ++;
  }

  float a = 0;
  counter = 1;
  while(counter < (b-1)){
    a = a + semicycle[counter];
    counter ++;
  }
  a = 1000 / (2 * a / (b - 2));

  Serial.print("Voltaje RMS: ");
  Serial.print(rms);
  Serial.println();
  Serial.print("Frecuencia: ");
  Serial.print(a);
  Serial.println();


  delay(1000);
}