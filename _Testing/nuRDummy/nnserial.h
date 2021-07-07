#ifndef __NNSERIAL__
#define __NNSERIAL

#include <stdint.h>
#include <windows.h>


typedef struct{
  HANDLE hCom;
} nnserial_private;

typedef struct{
  nnserial_private pr;
  int (*available)(void*);
  uint8_t (*read)(void*,uint8_t*);
  void (*close)();
} class_nnserial;

void class_nnserial_cnstr(class_nnserial *obj, char* port);


#endif // __NNSERIAL__
