#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <DHT.h>

MAX30105 particleSensor;

// -------- Heart Variables --------
long lastBeat = 0;
float beatsPerMinute;
bool fingerPresent = false;

// -------- LM35 --------
#define LM35_PIN A0

// -------- DHT11 --------
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

void setup()
{
  Serial.begin(9600);

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD))
  {
    Serial.println("MAX30102 not found");
    while (1);
  }

  dht.begin();   // initialize DHT11

  Serial.println("Place finger on sensor...");

  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x1F);
  particleSensor.setPulseAmplitudeGreen(0);
}

void loop()
{
  long irValue = particleSensor.getIR();

  // -------- LM35 Temperature (Body Temp) --------
  int lm35Value = analogRead(LM35_PIN);
  float voltage = lm35Value * (5.0 / 1023.0);
  float bodyTemp = voltage * 100.0;

  // -------- DHT11 Readings --------
  float humidity = dht.readHumidity();
  float atmTemp = dht.readTemperature();  // Atmospheric temperature

  if (irValue > 20000)
  {
    if (!fingerPresent)
    {
      Serial.println("Finger detected");
      fingerPresent = true;
    }

    // -------- ORIGINAL HEART LOGIC (UNCHANGED) --------
    if (checkForBeat(irValue) == true)
    {
      long delta = millis() - lastBeat;
      lastBeat = millis();

      beatsPerMinute = 60 / (delta / 1000.0);

      if (beatsPerMinute < 255 && beatsPerMinute > 20)
      {
        Serial.print("Heart Rate: ");
        Serial.print(beatsPerMinute);
        Serial.print(" BPM | Body Temp: ");
        Serial.print(bodyTemp);
        Serial.print(" °C | Atmos Temp: ");
        Serial.print(atmTemp);
        Serial.print(" °C | Humidity: ");
        Serial.print(humidity);
        Serial.println(" %");
      }
    }
  }
  else
  {
    if (fingerPresent)
    {
      Serial.println("No finger detected");
      fingerPresent = false;
    }
  }
}
