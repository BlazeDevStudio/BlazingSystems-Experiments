// Independent baseline Arduino Uno blink for Arduino IDE compatibility.
void setup() { pinMode(13, OUTPUT); }
void loop() { digitalWrite(13, HIGH); delay(1000UL); digitalWrite(13, LOW); delay(1000UL); }
