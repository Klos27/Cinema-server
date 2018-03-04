#define LEDPIN 9 // Analog output pin that the LED is attached to
#define LEDRELAY 8  // for LED PowerSupply
volatile int _brightVal;  // Brightness value ( 0 to 255 )
char _cmd[100];  // buffer for Serial
int _cmdIndex;   // Serial index
  
void setup() {
  pinMode(LEDPIN, OUTPUT);
  pinMode(LEDRELAY, OUTPUT);
  Serial.begin(115200);
  _brightVal = 128;
  _cmdIndex = 0;
  analogWrite(LEDPIN, _brightVal);
  digitalWrite(LEDRELAY, HIGH); // turnOff Led
}

void loop() {
}

//-------------------------------------------------------------------- Serial FUNCTIONS
//-------------------------------------------------------------------- BTRead
void SeRead(){  // read from Serial UART (Serial)
  char c = (char)Serial.read();
    
    if(c=='\n') {
      _cmd[_cmdIndex] = 0;
     // Serial.println(_cmd); // only for debugging! Takes a lot of ATmega Power!
      _cmdIndex = 0; // reset the _cmdIndex
      exeCmd();  // execute the command
     
    } else {      
      _cmd[_cmdIndex] = c;
      if(_cmdIndex<99) _cmdIndex++;
    }
}
//-------------------------------------------------------------------- BTRead END
//-------------------------------------------------------------------- serialEvent ( SERIAL INTERRUPT HANDLER )
void serialEvent(){  // SERIAL INTERRUPT HANDLER
       SeRead();
}
//-------------------------------------------------------------------- serialEvent ( SERIAL INTERRUPT HANDLER ) END
//-------------------------------------------------------------------- Serial cmdStartsWith
boolean cmdStartsWith(char *st) { // Check if BT cmd starts with
  for(int i=0; ; i++) {
    if(st[i]==0) return true;
    if(_cmd[i]==0) return false;
    if(_cmd[i]!=st[i]) return false;;
  }
  return false;
}
//-------------------------------------------------------------------- Serial cmdStartsWith END
//-------------------------------------------------------------------- Execute Serial Command
void exeCmd() {
  // Serial.println(_cmd);
   if( cmdStartsWith("LED ") ) { 
      _brightVal = atoi(_cmd+4);
      if(_brightVal >0 && _brightVal <=255)
         digitalWrite(LEDRELAY, LOW);
         analogWrite(LEDPIN, _brightVal);
      if(_brightVal == 0){
        digitalWrite(LEDRELAY, HIGH);
        analogWrite(LEDPIN, _brightVal);
      }
   }
   else if(cmdStartsWith("REL ")){
      if(atoi(_cmd+4) == 1)
        digitalWrite(LEDRELAY, LOW);
      else if(atoi(_cmd+4) == 0)
        digitalWrite(LEDRELAY, HIGH);
   }
}

