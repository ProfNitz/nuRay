char test;
#define LED 6

void setup() {
  Serial.begin(115200);
  DDRD = _BV(LED);
}

void loop() {
  if(Serial.available()>0)
  {
    test = Serial.read();
    Serial.print(test);
    if(test=='1')
    {
      PORTD |= _BV(LED);
    }
    else if(test=='0')
    {
      PORTD &= ~_BV(LED);
    }
  }
}
