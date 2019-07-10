#include mRay.h
#include mRay_intern.h



/*two param sets and a pointer to the active one*/
params_struct_type mR_params[2];
params_struct_type *mR_ptr_params;

/*one set of signals and a pointer thereon*/
signals_struct_type mR_signals;
signals_struct_type *mR_ptr_signals


/*used to switch active param set*/
void choose_paramset(int set){
  mR_ptr_params=&(mR_params[set])
}


/*find start of input stream*/
int try_synch_with_input(int reset){
  static int synched=0;
  static int cnt=0;
  if (reset){
    synched=0;
    cnt=0;
  }
  else {
    while (!synched && Serial.available()){
      if (Serial.read()==255 cnt++;
      else cnt=0;
      if (cnt==4) synched=1;
    }
  }
  return synched;
}


int mR_init(){
  /*set pointers to structs of params and signals*/
  mR_ptr_signals = &mR_signals;
  choose_paramset(0)
}

int mR_communicate(){
  if (try_synch_with_input(0)){
    read_params();
  }
}

void read_params{
  static uint16_t idx=0;
  byte *p;
  uint8_t len,k;
  p=(byte*)&idx;
  
  /*allow to read several params at once*/
  /*but what's the limit, time?, a number set by the user?*/
  
  if (!idx && Serial.available()>=2){
    p[0]=Serial.read();p[1]=Serial.read();
  }
  
  /*set address and length according to idx*/
  switch (idx){
    /*nuRay: Add variable list for reading here*/
    default:
      /*something went wrong, try resynch*/
      idx=0;
      try_synch_with_input(1);/*reset -> resynch next time*/
  }
  if (idx && Serial.available()>=len){
    for (k=0;k<len;p[k++]=Serial.read());
    idx=0;
  }
}