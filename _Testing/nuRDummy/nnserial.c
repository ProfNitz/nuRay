#include <stdio.h>
#include "nnserial.h"


int class_nnserial_available(class_nnserial *obj){
  return 0;
}

uint8_t class_nnserial_read(class_nnserial *obj, uint8_t *buf){
  static uint8_t cnt;
  DWORD nb;
  ReadFile(obj->pr.hCom,buf,1,&nb,NULL);
  //printf("%03d, %d, %d\n",cnt++,nb,*buf);
  return nb;
}

void class_nnserial_close(class_nnserial *obj){
	CloseHandle(obj->pr.hCom);
}

void class_nnserial_cnstr(class_nnserial *obj, char* port){
  DCB paramsCom;
  COMMTIMEOUTS ct;

  /* register member functions */
  obj->available=class_nnserial_available;
  obj->read = class_nnserial_read;
  obj->close = class_nnserial_close;

  obj->pr.hCom = CreateFile(port,          // for COM1—COM9 only
                   GENERIC_READ | GENERIC_WRITE, //Read/Write
                   0,               // No Sharing
                   NULL,            // No Security
                   OPEN_EXISTING,   // Open existing port only
                   0,               // Non Overlapped I/O
                   NULL);
  if (obj->pr.hCom == INVALID_HANDLE_VALUE)
    printf("error when opening serial port\r\n");
  else
    printf("serial port successfully opend\r\n");

  // Set Parameters
  GetCommState(obj->pr.hCom, &paramsCom);

  paramsCom.BaudRate = CBR_115200;
  paramsCom.Parity = NOPARITY;
  paramsCom.StopBits = 0;
  paramsCom.ByteSize = 8;
  paramsCom.fDtrControl = DTR_CONTROL_DISABLE;

  SetCommState(obj->pr.hCom, &paramsCom);

  ct.ReadIntervalTimeout = 0;
  ct.ReadTotalTimeoutConstant = 1000; /* ms */
  ct.ReadTotalTimeoutMultiplier = 0;
  ct.WriteTotalTimeoutConstant = 0;
  ct.WriteTotalTimeoutMultiplier = 100;


  SetCommTimeouts(obj->pr.hCom,&ct);

  PurgeComm(obj->pr.hCom,PURGE_RXCLEAR | PURGE_TXCLEAR);

}


