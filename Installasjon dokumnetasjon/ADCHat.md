# Oppsett av ADCHat

ADCHat bruker en Waveshare Current/Power monitor Hat til å lese effekt, strøm og spennign på 4 ADC kanaler. Den Kan også brukes til å beregne den gjennværende batterikapasiteten til en 3S LiPo batteri ved å måle speningen å batteriet.

https://www.waveshare.com/wiki/Current/Power_Monitor_HAT

## Oppsett av Pi
Hvis man ikke allerede har gjort det, så må burde man oppdatere og oppgradere pakkene på PIen. Dette kan gjøres med

```
sudo apt-get update 
``` 

```
sudo apt-get upgrade
``` 


I2C bus må aktiveres på RPi. Dette kan gjøres med kommandoen:

```
sudo raspi-config nonint do_i2c 0
```

For å  teste om I2C er aktivert kan man bruke en konsollkommando for å detektere alle enheter på I2C bussen.

```
sudo i2cdetect -y 1
```
Hvis alt er gjort riktig burde den detektere fire enheter på addressene 0x40, 0x41, 0x42 og 0x43.


## Installasjon

ADCHat bruker smbus 2biblioteket til å gjennomføre I2C kommunikasjon med INA219 sensorene.
smbus2 kan installeres ved å bruke kommandoen:
```
pip3 install smbus2
```
Dokumentasjon og eksempler kan finnes på pypi:
https://pypi.org/project/smbus2/



