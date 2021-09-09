// including the SoftwareSerial library will allow us to 
// use the digital pin no. 2,3 as Rx, Tx.
#include <SoftwareSerial.h>
// set the Rx ==> Pin 2; Tx ==> Pin 3.
SoftwareSerial esp8266(2, 3);
// set the software and hardware serial communication speed(baud rate)
#define serialCommunicationSpeed 9600

#include <FastLED.h> // for controlling RGB LED
#define NUM_LEDS 1 // one LED
#define DIG_PIN 6 // at digital pin 6
CRGB leds[NUM_LEDS]; // declare the leds

// define a constant named "DEBUG" and it's value true; used later
#define DEBUG true

// assign a variable referring to the pin.

int fanPin = 11;
int bulbPin = 10;

void setup()
{
  // set inbuilt LED in output mode.
  pinMode(LED_BUILTIN, OUTPUT);

  // turn the red LED on at the beginning of the program.
  digitalWrite(LED_BUILTIN, LOW);

  // begin the Hardware serial communication (0, 1) at speed 9600.
  Serial.begin(serialCommunicationSpeed);
  delay(10000);
  // begin the software serial communication (2, 3) at speed 9600.
  esp8266.begin(serialCommunicationSpeed);

  // call this user-defined function "InitWifiModule()" to 
  // initialize a communication between the ESP8266 and 
  // access point (Home Router or even your mobile hotspot) ie WiFi.
  InitWifiModule();

  delay (1000);
  FastLED.addLeds<WS2811, DIG_PIN, GRB>(leds, NUM_LEDS);

  pinMode(fanPin, OUTPUT);
  pinMode(bulbPin, OUTPUT);


  // after finishing the initialization successfully, turn off the red LED (just an indicator).
  digitalWrite(LED_BUILTIN, HIGH);
}

void fan()
{
  // Advance the cursor to the "pin=" part in the request header to read the 
  // incoming bytes after the "pin=" part which is the pinNumber and it's state.
  esp8266.find("pin=");
  // read the first Byte from the Arduino input buffer ie hundreds digit
  // 1 from '110 or 111' becomes 10
  int pinNumber = (esp8266.read() - 48) * 10;
  // read the second Byte from the Arduino input buffer
  // 10 + 1 becomes 11 pin number
  pinNumber = pinNumber + (esp8266.read() - 48);
  // read the third byte from the Arduino input buffer.
  // 1 or 0 ie ON or OFF
  int statusLed = (esp8266.read() - 48);

  // then turn the LED at "pinNumber" on or off depending on the "statusLed" variable value.
  digitalWrite(pinNumber, statusLed);

  // print the "pinNumber" value on the serial monitor for debugging purposes.
  Serial.print(pinNumber);
  // print some spaces on the serial monitor to make it more readable.
  Serial.print("      ");
  // print the "statusLed" value on the serial monitor for debugging purposes.
  Serial.println(statusLed);
}

void bulb()
{
  // Advance the cursor to the "pin=" part in the request header to read the 
  // incoming bytes after the "pin=" part which is the pinNumber and it's state.
  esp8266.find("pin=");
  // read the first Byte from the Arduino input buffer ie hundreds digit
  // 1 from '110 or 111' becomes 10
  int pinNumber = (esp8266.read() - 48) * 10;
  // read the second Byte from the Arduino input buffer
  // 10 + 1 becomes 11 pin number
  pinNumber = pinNumber + (esp8266.read() - 48);
 // read the third byte from the Arduino input buffer.
 // 1 or 0 ie ON or OFF
  int statusLed = (esp8266.read() - 48);

  // then turn the LED at "pinNumber" on or off depending on the "statusLed" variable value.
  digitalWrite(pinNumber, statusLed);


  // print the "pinNumber" value on the serial monitor for debugging purposes.
  Serial.print(pinNumber);
  // print some spaces on the serial monitor to make it more readable.
  Serial.print("      ");
  // print the "statusLed" value on the serial monitor for debugging purposes.
  Serial.println(statusLed);
}

void rgbLED()
{
  // similarly find rgb values
  esp8266.find("red=");
  int redValue = (esp8266.read() - 48) * 100;
  redValue += (esp8266.read() - 48) * 10;
  redValue += esp8266.read() - 48;

  esp8266.find("green=");
  int greenValue = (esp8266.read() - 48) * 100;
  greenValue += (esp8266.read() - 48) * 10;
  greenValue += esp8266.read() - 48;
  esp8266.find("blue=");

  int blueValue = (esp8266.read() - 48) * 100;
  blueValue += (esp8266.read() - 48) * 10;
  blueValue += esp8266.read() - 48;

  Serial.println(redValue);
  Serial.println(greenValue);
  Serial.println(blueValue);

  leds[0] = CRGB(redValue, greenValue, blueValue);// show the color
  FastLED.show();
}

void loop()
{
  // check if there's any data received and stored in the serial receive buffer, 
  if (esp8266.available())
  {
    // search for the "+IPD," string in the incoming data. if it exists the ".find()" returns true and if not it returns false.
    if (esp8266.find("+IPD,"))
    {
      //wait 2 second to fill up the buffer with the data.
      delay(2000);

      // Subtract 48 because the read() function returns the ASCII decimal value 48. make it 0
      int connectionId = esp8266.read() - 48;

      // print the "connectionId" value on the serial monitor for debugging purposes.
      Serial.println(connectionId);

      // call the appropriate device functions 
      if (esp8266.find("device="))
      {
        int deviceValue = esp8266.read() - 48;
        if (deviceValue == 0)
        {
          fan();
        }
        else if (deviceValue == 1)
        {
          rgbLED();
        }
        else if (deviceValue == 2)
        {
          bulb();
        }
      }

      // close the TCP/IP connection.
      String closeCommand = "AT+CIPCLOSE=";
      // append the "connectionId" value to the string.
      closeCommand += connectionId;
      // append the "\r\n" to the string. it simulates the keyboard enter press.
      closeCommand += "\r\n";
      // then send this command to the ESP8266 module to excute it.
      sendData(closeCommand, 1000, DEBUG);

    }
  }
}


/* sendData
  this fn regulates how the AT Commands will be sent to the ESP8266.

  Parameters: - command - the AT Command to send
              - timeout - the time to wait for a response
              - debug   - print to Serial window?(true = yes, false = no)

  Returns: The response from the esp8266 (if there is a reponse)
*/
String sendData(String command, const int timeout, boolean debug)
{
  // initialize a String variable named "response". we will use it later.
  String response = "";

  // send the AT command to the esp8266 (from ARDUINO to ESP8266).
  esp8266.print(command);

  // get the operating time at this specific moment and save it inside the "time" variable.
  long int time = millis();
  // excute only within 1 second.
  while ( (time + timeout) > millis())
  {
    // check if any response came from the ESP8266 and saved in the Arduino input buffer
    while (esp8266.available())
    {
      // if yes, read the next character from the input buffer and 
      // save it in the "response" String variable.
      char c = esp8266.read();
      // append the next character to the response variable. 
      // at the end we will get a string(array of characters) contains the response.
      response += c;
    }
  }
  // print the response on the Serial monitor.
  if (debug)
  {
    Serial.print(response);
  }
  // return the String response.
  return response;
}


/* InitWifiModule
  this function initialises the wifi module by 
  sending the AT commands to ESP8266 via sendData() function.

  Parameters: void

  Returns: void
*/
void InitWifiModule()
{
  //reset the ESP8266 module.
  sendData("AT+RST\r\n", 2000, DEBUG);
  delay(3000);

  //connect to the WiFi network.
  sendData("AT+CWJAP=\"WiFi SSID\",\"WiFi Password\"\r\n", 2000, DEBUG);
  delay (2000);
  //set the ESP8266 WiFi mode to station mode.(conncect to an existing wifi)
  sendData("AT+CWMODE=1\r\n", 1500, DEBUG);
  delay (1500);
  //Show IP Address, and the MAC Address.
  sendData("AT+CIFSR\r\n", 1500, DEBUG);
  delay (1500);
  //Multiple conections.
  sendData("AT+CIPMUX=1\r\n", 1500, DEBUG);
  delay (1500);

  //start the communication at port 80, 
  // port 80 used to communicate with the web servers through the http requests.
  sendData("AT+CIPSERVER=1,80\r\n", 1500, DEBUG);
  delay (1500);
}
