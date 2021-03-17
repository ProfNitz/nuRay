#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

#include "nnserial.h"

#define MAX_PAYLOAD_LEN 4
#define MAX_PACK_LEN (MAX_PAYLOAD_LEN+3) /* cmd(2) + payload (maxlen) + check_sum(1)*/
#define STOPFLAG 0xff
#define STARTFLAG 0xff

// start cmd cmd payload chk len stop
// len = 2 (cmd) + sizeof(payload)(1,2,4) + 1 (chk)


typedef struct {
  HANDLE evStop;
} WORK_PARAMS;

uint8_t checksum(uint8_t *buf, uint8_t len){
	uint16_t res=0;
	uint8_t k;
	for (k=0;k<len-1;res+=buf[k++]);/* len-1 .. calc checksum without checksum ;o) */
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
				len=buf[(uint8_t)(idx-2)];

				/* check length of package */
				/* distance start-->stop vs. len and len vs. MAX_LEN*/
				if ((buf[(uint8_t)(idx-(3+len))]==STARTFLAG)&&(len<=MAX_PACK_LEN)){
					/*copy buf to pack*/
					for (k=idx-(2+len),p=pack,i=0;i<len;*(p++)=buf[k++],i++);
					/* check the checksum */
					if (checksum(pack,len)==buf[(uint8_t)(idx-3)]){
            printf("------------------ recv: %d: ",cmd=*(uint16_t*)pack);
            switch (cmd){
						case 12:printf("%g",*(float*)&pack[2]);break;
						case 10:printf("%d",*(int16_t*)&pack[2]);break;
						case 14:printf("%d",*(uint8_t*)&pack[2]);break;
						default:
							printf("unknown data: ");
	            for (k=2;k<len-1;printf("0x%x ",pack[k++]));
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
