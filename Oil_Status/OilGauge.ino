#include <Arduino.h>
#include <TM1637Display.h>
#include <math.h>
// Module connection pins (Digital Pins)
#define CLKR 3
#define DIOR 2

#define CLKL 10
#define DIOL 9


int offset = 105; // zero pressure calibrate
int fullScale = 922; // max pressure calibrate
float pressure; // final pressure

TM1637Display displayR(CLKR, DIOR);
TM1637Display displayL(CLKL, DIOL);

// value to determine the size of the readings array.
const int numReadings = 5;

int readings[numReadings];      // the readings from the analog input
int readIndex = 0;              // the index of the current reading
int total = 0;                  // the running total
int average = 0;                // the average

int inputPin = A0;

void setup()
{
  Serial.begin(9600);
    // initialize all the readings to 0:
    for (int thisReading = 0; thisReading < numReadings; thisReading++) {
    readings[thisReading] = 0;
  }
}

double Thermister(int RawADC) {  //Function to perform the fancy math of the Steinhart-Hart equation
 double Temp;
 Temp = log(((10240000/RawADC) - 10000));
 Temp = 1 / (0.001129148 + (0.000234125 + (0.0000000876741 * Temp * Temp ))* Temp );
 Temp = Temp - 273.15;              // Convert Kelvin to Celsius
 Temp = (Temp * 9.0)/ 5.0 + 32.0; // Celsius to Fahrenheit - comment out this line if you need Celsius
 return Temp;
}


void loop()
{
  int tempVal=analogRead(7);      //Read the analog port 0 and store the value in val
  double temp=Thermister(tempVal);   //Runs the fancy math on the raw analog value
  // Serial.print ("Oil Temperature: "); // Change this if monitoring another type of fluid
  // Serial.println(temp);   //Print the value to the serial port
  
  // float pressure = (analogRead(A0) - offset) * 6.89476  / (fullScale - offset); // pressure conversion
  
   // subtract the last reading:
  total = total - readings[readIndex];
  // read from the sensor:
  readings[readIndex] = analogRead(inputPin);
  // add the reading to the total:
  total = total + readings[readIndex];
  // advance to the next position in the array:
  readIndex = readIndex + 1;

  // if we're at the end of the array...
  if (readIndex >= numReadings) {
    // ...wrap around to the beginning:
    readIndex = 0;
  }

  

  // calculate the average:
  average = total / numReadings;
  
  float pressure = (average - offset) * 6.89476  / (fullScale - offset); // pressure conversion

  
  
  int psi =int(pressure*14.5038);
  Serial.print("Oil Pressure: ");
  Serial.println(pressure);
  // Serial.println(int(pressure*14.5038));

  displayR.setBrightness(0x0f); 
  displayR.showNumberDec(temp); 

  displayL.setBrightness(0x0f);
  displayL.showNumberDec(psi*.66 ) ; 

  delay(100);
}
