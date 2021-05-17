#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#include "nnserial.h"

#define MAX_PAYLOAD_LEN 4
#define MAX_PACK_LEN (MAX_PAYLOAD_LEN+3) /* cmd(2) + payload (maxlen) + check_sum(1)*/
#define STOPFLAG 0xff
#define STARTFLAG 0xff

// start cmd cmd payload chk len stop
// len = 2 (cmd) + sizeof(payload)(1,2,4)
  typedef struct {
  float paramf[30];
  int16_t param16[30];
  uint8_t param8[30];
} PSET;

PSET paramset[2];

typedef struct {
  HANDLE evStop;
} WORK_PARAMS;

uint8_t checksum(uint8_t *buf, uint8_t len){
	uint16_t res=0;
	uint8_t k;
	for (k=0;k<len;res+=buf[k++]);
	return (uint8_t)(res&0xff);
}

DWORD WINAPI Work(LPVOID params) {
  class_nnserial Serial;
  uint8_t buf[256]; /* receive buffer, used as a ring buffer by letting idx overflow/underflow (observe typecasts when indexing!!)*/
  uint8_t *p;
  uint8_t pack[MAX_PACK_LEN];
  uint8_t idx,k,i;
  uint8_t len;
  uint16_t cmd;
  uint8_t dtype;
  int setidx;


  class_nnserial_cnstr(&Serial,"COM9");
  idx = 0;
  //check for Stop Signal (timeout 0); sent by main when user hits <enter>
  while (WaitForSingleObject(((WORK_PARAMS*)params)->evStop,0) == WAIT_TIMEOUT) {
		/*read one byte*/
    if (Serial.read(&Serial,&buf[idx])){
    	/* increment pointer into buffer */
			idx++;
			/* print the byte just read */
			printf("0x%x ",buf[(uint8_t)(idx-1)]);

			/* if the last byte is a STOPFLAG, we might have a package here */
			if (buf[(uint8_t)(idx-1)]==STOPFLAG){
				printf("\nreceived STOPFLAG: lets check if that is a valid package\n");
				/* retrieve the len of the package from the corresponding byte (see protocoll spec) */
				len=buf[(uint8_t)(idx-2)]&0x0f;
				printf("\nlen ist: %d\n",len);

				/* check length of package */
				/* distance start-->stop vs. len and len vs. MAX_LEN*/
				if ((buf[(uint8_t)(idx-(4+len))]==STARTFLAG)&&(len<=MAX_PACK_LEN)){
					/*copy buf to pack*/
					for (k=idx-(3+len),p=pack,i=0;i<len+1;*(p++)=buf[k++],i++);
					/* check the checksum */
					if (checksum(pack,len)==buf[(uint8_t)(idx-3)]){
            /* we have a valid package */
            if(((*(uint8_t*)&pack[0])&0x0f)==0)
            {
                printf("\n setidx ist null\n");
                setidx = 0;
            }
            else
            {
                printf("\n setidx ist eins\n");
                setidx = 1;
            }
            int subidx = (*(uint16_t*)&pack[0])>>4;

            printf("------------------ recv: %d: ",dtype= (buf[(uint8_t)(idx-2)])&0xf0);
            switch (dtype){
						case 48: /*printf("%g",*(float*)&pack[2]);break;*/
                                 paramset[setidx].paramf[subidx] = *(float*)&pack[2];
                                 printf("%g ", paramset[setidx].paramf[subidx]);
                                 printf("\nparameter %d has been changed\n",subidx);break;


						case 32: /*printf("%d",*(int16_t*)&pack[2]);break;*/
                                 paramset[setidx].param16[subidx] = *(int16_t*)&pack[2];
                                 printf("%d ", paramset[setidx].param16[subidx]);
                                 printf("\nparameter %d has been changed\n",subidx);break;


						case 16: /*printf("%d",*(uint8_t*)&pack[2]);break;*/
						         paramset[setidx].param8[subidx] = *(uint8_t*)&pack[2];
						         printf("%d ", paramset[setidx].param8[subidx]);
						         printf("\nparameter %d has been changed\n",subidx);break;

						default:
							printf("unknown data: ");
	            for (k=2;k<len;printf("0x%x ",pack[k++]));
            }

            printf("\nidx: %d\n",idx);
					}
				}
			}
    }//received one byte
  }//infinite while loop
  Serial.close(&Serial);
  return 0;
}


int main() {

  WORK_PARAMS wp;
  HANDLE my_working_thread;
  char line[100];


  wp.evStop = CreateEvent(NULL, TRUE, FALSE, NULL);

  my_working_thread = CreateThread(
                        NULL,                   // default security attributes
                        0,                      // use default stack size
                        Work,                   // thread function name
                        (LPVOID)&wp,            // argument to thread function
                        0,                      // use default creation flags
                        NULL);                  // returns the thread identifier

  gets(line);//wait for user to hit enter

  //stop working thread
  SetEvent(wp.evStop);
  //wait for thread to really stop
  WaitForSingleObject(my_working_thread,INFINITE);
  printf("Stop\n");
  return 0;
}
