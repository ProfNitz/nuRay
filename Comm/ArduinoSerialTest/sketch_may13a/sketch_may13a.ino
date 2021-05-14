#define LED1 5
#define LED2 6
const int BUF_SIZE = 2;
char buf[BUF_SIZE];
#include <avr/io.h>

void init_pwm(void)
{ 
TCCR0A = _BV(COM0A1) + _BV(WGM00) + _BV(WGM01); // S. 139f., Tab. 19-5/-9
TCCR0B = _BV(CS00) + _BV(CS01); // Datenblatt S. 142, Tab. 19-10
OCR0A = 0; // Tastgrad
}

void setup() {
  Serial.begin(115200);
  DDRD = _BV(LED1) + _BV(LED2);
  init_pwm();
}

void loop() {
  if(Serial.available()>0)
  {
    Serial.readBytes(buf,BUF_SIZE);
    
    switch(buf[0]){
      case 'a':
      switch(buf[1]){
        case 0:
        PORTD &= ~_BV(LED1);
        break;
        case 1:
        PORTD |= _BV(LED1);
        break;
      }
      break;

      case 'b':
      OCR0A = buf[1];
      break;
      }
      
    }
}
