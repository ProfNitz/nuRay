#include <stdio.h>
#include <stdlib.h>
#include <EEPROM.h>

#define MAX_PAYLOAD_LEN 4
#define MAX_PACK_LEN (MAX_PAYLOAD_LEN+3)
#define STOPFLAG 0xff
#define STARTFLAG 0xff
#define BUF_SIZE 256
#define LED1 5
#define LED2 6
#define LED3 7
#define PARAM_COUNTF 30
#define PARAM_COUNT16 30
#define PARAM_COUNT8 30

uint8_t buf[BUF_SIZE]; 
uint8_t *p;
uint8_t pack[MAX_PACK_LEN];
uint8_t idx,k,i,x,sizeB,newidx,sum;
uint8_t len, teststartflag;
uint16_t cmd;
uint8_t dtype;
uint8_t recByte;
int setidx;
int active = 1;
int EEPROMidx = 0;


typedef struct {
  float paramf[PARAM_COUNTF];
  int16_t param16[PARAM_COUNT16];
  uint8_t param8[PARAM_COUNT8];
} PSET;

PSET paramset[2];

void init_pwm(void)
{ 
TCCR0A = _BV(COM0A1) + _BV(WGM00) + _BV(WGM01); // S. 139f., Tab. 19-5/-9
TCCR0B = _BV(CS00) + _BV(CS01); // Datenblatt S. 142, Tab. 19-10
OCR0A = 0; // Tastgrad
}

uint8_t checksum(uint8_t *buf, uint8_t len){
  uint16_t res=0;
  uint8_t k;
  for (k=0;k<len;res+=buf[k++]);
  return (uint8_t)(res&0xff);
}

void setup() {
  Serial.begin(115200);
  idx = 0;
  DDRD = _BV(LED1) + _BV(LED2) + _BV(LED3);
  init_pwm();
  paramset[1].param8[1] = 121;
  paramset[0].param8[1] = 5;
  paramset[1].paramf[2] = 12.25;
  paramset[0].paramf[2] = 5;  
  paramset[1].param8[3] = 255;
  paramset[0].param8[3] = 5;
}

/*void sendSet() {
  Serial.write(active);
}*/
int negidx (int oldidx,int back)
{
  sum = (oldidx-back);
  return sum;
}
void loop() {
  //sendSet();
  if(Serial.available()>0){
    while(Serial.available()>0){
      recByte = Serial.read();
      idx = idx%BUF_SIZE;
      //Serial.println(recByte);
      buf[idx]=recByte;
      //Serial.println(buf[idx]);  
      if((buf[idx]) == STOPFLAG){
        //Serial.println("stopflag erkannt!");
        len = buf[(uint8_t)idx-1]&0x0f;
        //Serial.write(len);
        teststartflag = buf[(uint8_t)negidx(idx,(3+len))];
        //Serial.println(teststartflag);
        if ((buf[negidx(idx,(3+len))]==STARTFLAG)&&(len<=MAX_PACK_LEN)){
          //Serial.write(len);
          for (k=negidx(idx,(2+len)),p=pack,i=0;i<len+1;*(p++)=buf[k++],i++);
          //Serial.println(pack[0]);
          if (checksum(pack,len)==buf[(uint8_t)negidx(idx,2)]){
            //Serial.write(len);
            //Serial.println(checksum(pack,len));
            //Serial.println(buf[(uint8_t)(idx-2)]);

             int subidx = (*(uint16_t*)&pack[0])>>4;
             dtype= (buf[negidx(idx,1)])&0xf0;
             switch (dtype){
              case 48:
              if((((*(uint8_t*)&pack[0])&_BV(2))>>2)==1)
              { 
                setidx = 1;
              }
              else 
              {
              setidx = 0;
              }
              if((((*(uint8_t*)&pack[0])&_BV(3))>>3)==1)
              { 
                paramset[setidx].paramf[subidx] = *(float*)&pack[2];idx++;
              }
              if(((*(uint8_t*)&pack[0])&_BV(3))==0)
              {
                byte *b = (byte*)&paramset[setidx].paramf[subidx];
                Serial.write(b,4);
                //PORTD |= _BV(LED3);
                //Serial.print(paramset[setidx].paramf[subidx],2);
                //Serial.print("\n");
                //Serial.write(paramset[setidx].paramf[subidx],4);
                idx++;
              }
              break;
              case 32:
              if((((*(uint8_t*)&pack[0])&_BV(2))>>2)==1)
              { 
                setidx = 1;
              }
              else 
              {
              setidx = 0;
              }
              if((((*(uint8_t*)&pack[0])&_BV(3))>>3)==1)
              { 
                paramset[setidx].param16[subidx] = *(int16_t*)&pack[2];idx++;
              }
              if(((*(uint8_t*)&pack[0])&_BV(3))==0)
              {
                //Serial.print(paramset[setidx].param16[subidx]);
                //Serial.print("\n");
                //Serial.write(paramset[setidx].param16[subidx],2);
                byte *b = (byte*)&paramset[setidx].param16[subidx];
                Serial.write(b,2);
                idx++;

              }
              break;
              case 16:
              if((((*(uint8_t*)&pack[0])&_BV(2))>>2)==1)
              { 
                setidx = 1;
              }
              else 
              {
              setidx = 0;
              } 
              if((((*(uint8_t*)&pack[0])&_BV(3))>>3)==1)
              { 
                paramset[setidx].param8[subidx] = *(uint8_t*)&pack[2];idx++;
              }
              if(((*(uint8_t*)&pack[0])&_BV(3))==0)
              {
                byte *b = (byte*)&paramset[setidx].param8[subidx];
                Serial.write(b,1);
                idx++;
                //PORTD |= _BV(LED3);
              }
              break;
              case 240:
              if((((*(uint8_t*)&pack[0])&_BV(2))>>2)==1)
              {
                if((((*(uint8_t*)&pack[0])&_BV(3))>>3)==1)
                { 
                  active = *(uint8_t*)&pack[2]; idx++;
                }
                if(((*(uint8_t*)&pack[0])&_BV(3))==0)
                {
                  Serial.write(active);
                  idx++;
                }
              }
              break;
             }
           }
           else{
            //Serial.println("akein gültiges paket wegen checksum!");
            idx++;
           }
        }
        else{
          //Serial.println("bkein gültiges paket!");
          idx++;
        }
      }
      else{
        idx++;
      }
    }
  }
   
  if(paramset[active].param8[1] == 121){
    PORTD |= _BV(LED1);
  }
  else{
    PORTD &= ~_BV(LED1);
  }
  if(paramset[active].paramf[2] == 12.25){
    PORTD |= _BV(LED3);
  }
  else{
    PORTD &= ~_BV(LED3);
  }
  OCR0A = paramset[active].param8[3];
}
