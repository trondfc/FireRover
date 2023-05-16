# Oppsett av ServoHat

Hentet fra: 
https://www.adafruit.com/product/2327


## RPi Oppsett
Update the local package database to find new versions.

```
sudo apt-get update 
``` 

 Upgrade all installed packages to the newest version.

```
sudo apt-get upgrade
``` 

Install, pip3, the python package installer for python3.

```
sudo apt-get install python3-pip
``` 

Allows for the creation of custom python packages.

```
sudo pip3 install --upgrade setuptools

```

## Installer ServoHat og Konfigurer RPi periferienheter


Used to execute Linux shell commands in python
```
sudo pip3 install --upgrade adafruit-python-shell

```

Downloads the raspi-blinka.py autoconfiguration script
```
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py

```

Automatically installs a number of packages and enables the RPi I2C, SPI, SSH, Serial and Camera.
```
sudo python3 raspi-blinka.py

```

Test script to verify that the RPi interfaces have been configured.
```
python3 blinkatest.py
```
