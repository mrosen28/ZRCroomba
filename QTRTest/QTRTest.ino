#include <QTRSensors.h>
#define NUMBEROFSENSORS 8
#define EMITTER_PIN 11
#define TIMEOUT 2500
#define BAUDRATE 115200
//#define DEBUG //DEBUG: No Calibration, Autosend Reading on One Line
              //Non-DEBUG: Calibrate, Wait for Connection Byte in Setup, Send Data upon Request
unsigned int sensorReading[NUMBEROFSENSORS];
QTRSensorsRC qtr((unsigned char[]){3, 4, 5, 6, 7, 8, 9, 10}, NUMBEROFSENSORS, TIMEOUT, EMITTER_PIN);
void setup()
{
  pinMode(13, OUTPUT);
  digitalWrite(13, HIGH);
  Serial.begin(BAUDRATE);

  #ifndef DEBUG
    for (int i = 0; i < 400; i++)
      qtr.calibrate();//reads all sensors 10 times at 2500 us per read (i.e. ~25 ms per call)
  #else
    Serial.print("DEBUG Mode: Skipping QTR Calibration.");
  #endif

   while (!Serial.available())
   {
    delay(10);
    Serial.write("0");
   }
   
  digitalWrite(13,LOW);
}
void loop()
{
  #ifndef DEBUG
  while(!Serial.available());
  while(Serial.available()){
    Serial.read();
  }
  #endif
  unsigned char out = 0;
  qtr.read(sensorReading);
  for (auto r:sensorReading)
  {
    out *= 2;
    out += r > 1000;
  }
  #ifdef DEBUG //Print Out Entire Sensor Reading on New Line
  for(int i=0;i<8;i++)
    Serial.print(bitRead(out,7-i));
  Serial.println();
  delay(50);
  #else
  Serial.write(out);
  #endif
}
