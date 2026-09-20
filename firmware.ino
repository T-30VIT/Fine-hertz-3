/*
  SUPER SIMPLE HEART MONITOR
  ---------------------------
  What it does:
    - Reads the heart sensor.
    - Checks it fast or slow, depending on a "speed level" (0-3)
      that the computer tells us to use.
    - Sends the heart rate to the computer.
    - If the heart rate looks dangerous, switches to fast checking
      by itself.

  Wiring:
    AD8232 OUTPUT -> A0
    AD8232 LO+    -> Pin 2
    AD8232 GND    -> GND
    AD8232 3.3V   -> 3.3V
*/

int sensorPin  = A0;
int leadOffPin = 2;

// speed level: 0 = slow, 1 = medium, 2 = fast, 3 = urgent
int speedLevel = 2;

// how often to check the sensor, in milliseconds, for each speed level
int checkDelay[4]  = {1000, 40, 10, 4};

// how often to send data to the computer, in milliseconds
int sendDelay[4] = {10000, 2000, 1000, 250};

unsigned long lastCheck = 0;
unsigned long lastSend  = 0;

int beatThreshold  = 600;
unsigned long lastBeatTime = 0;
int heartRate = 0;

void setup() {
  Serial.begin(115200);
  pinMode(leadOffPin, INPUT);
  Serial.println("Ready");
}

void loop() {
  checkForNewSpeedLevel();

  unsigned long now = millis();

  if (now - lastCheck >= checkDelay[speedLevel]) {
    lastCheck = now;
    readSensorAndUpdateHeartRate();
  }

  if (now - lastSend >= sendDelay[speedLevel]) {
    lastSend = now;
    sendDataToComputer();
  }
}

void readSensorAndUpdateHeartRate() {
  int value = analogRead(sensorPin);

  // Print the raw value on its own line so Arduino's built-in
  // Serial Plotter (Tools -> Serial Plotter) can graph it live.
  Serial.println(value);

  // Did the signal just spike up? That means one heartbeat happened.
  if (value > beatThreshold) {
    unsigned long now = millis();
    if (lastBeatTime != 0) {
      unsigned long gap = now - lastBeatTime;
      if (gap > 250 && gap < 2000) {
        heartRate = 60000 / gap;   // turn the time gap into beats per minute
      }
    }
    lastBeatTime = now;
  }

  // Safety rule: if heart rate is dangerous, speed up right now.
  // The computer does not need to tell us this -- we act on our own.
  bool tooFast = heartRate > 140;
  bool tooSlow = heartRate > 0 && heartRate < 40;
  if ((tooFast || tooSlow) && speedLevel < 2) {
    speedLevel = 2;
    Serial.println("Dangerous heart rate, switching to fast checking");
  }
}

void sendDataToComputer() {
  bool leadIsOff = digitalRead(leadOffPin) == HIGH;

  Serial.print("DATA,");
  Serial.print(heartRate);
  Serial.print(",");
  Serial.print(leadIsOff ? 1 : 0);
  Serial.print(",");
  Serial.println(speedLevel);
}

// Listens for a single digit (0-3) from the computer telling us
// what speed level to use.
void checkForNewSpeedLevel() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c >= '0' && c <= '3') {
      speedLevel = c - '0';
    }
  }
}
