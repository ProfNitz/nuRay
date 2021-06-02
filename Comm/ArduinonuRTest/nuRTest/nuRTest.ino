#include <stdio.h>
#include <stdlib.h>

#define MAX_PAYLOAD_LEN 4
#define MAX_PACK_LEN (MAX_PAYLOAD_LEN+3)
#define STOPFLAG 0xff
#define STARTFLAG 0xff
#define BUF_SIZE 256
#define LED1 5
#define LED2 6
uint8_t buf[BUF_SIZE]; 
uint8_t *p;
uint8_t pack[MAX_PACK_LEN];
uint8_t idx,k,i,x,sizeB;
uint8_t len, teststartflag;
uint16_t cmd;
uint8_t dtype;
uint8_t recByte;
int setidx;

typedef struct {
  float paramf[30];
  int16_t param16[30];
  uint8_t param8[30];
} PSET;

PSET paramset[2];

uint8_t checksum(uint8_t *buf, uint8_t len){
  uint16_t res=0;
  uint8_t k;
  for (k=0;k<len;res+=buf[k++]);
  return (uint8_t)(res&0xff);
}

void setup() {
  Serial.begin(115200);
  idx = 0;
  DDRD = _BV(LED1) + _BV(LED2);
}

void loop() {
  if(Serial.available()>0){
    while(Serial.available()>0){
      recByte = Serial.read();
      //Serial.println(recByte);
      buf[idx]=recByte;
      //Serial.println(buf[idx]);  
      if((buf[idx]) == STOPFLAG){
        Serial.println("stopflag erkannt!");
        len = buf[(uint8_t)idx-1]&0x0f;
        //Serial.println(len);
        teststartflag = buf[(uint8_t)idx-(3+len)];
        //Serial.println(teststartflag);
        if ((buf[idx-(3+len)]==STARTFLAG)&&(len<=MAX_PACK_LEN)){
          for (k=idx-(2+len),p=pack,i=0;i<len+1;*(p++)=buf[k++],i++);
          //Serial.println(pack[0]);
          if (checksum(pack,len)==buf[(uint8_t)(idx-2)]){
            //Serial.println(checksum(pack,len));
            //Serial.println(buf[(uint8_t)(idx-2)]);
             if(((*(uint8_t*)&pack[0])&0x0f)==0){ 
              setidx = 0;
             }
             else {
              setidx = 1;
             }
             int subidx = (*(uint16_t*)&pack[0])>>4;
             dtype= (buf[idx-1])&0xf0;
             switch (dtype){
              case 48:
              paramset[setidx].paramf[subidx] = *(float*)&pack[2];idx++;break;

              case 32:
              paramset[setidx].param16[subidx] = *(int16_t*)&pack[2];idx++;break;

              case 16: 
              paramset[setidx].param8[subidx] = *(uint8_t*)&pack[2];idx++;break;
             }
           }
           else{
            Serial.println("kein gültiges paket wegen checksum!");
            idx++;
           }
        }
        else{
          Serial.println("kein gültiges paket!");
          idx++;
        }
      }
      else{
        idx++;
      }
    }
  }
  if(paramset[1].param8[1] == 121){
    PORTD = _BV(LED1);
  }
  if(paramset[1].paramf[2] == 123.76){
    PORTD = _BV(LED2);
  }
}
