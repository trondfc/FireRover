# FireRover
GitHub repo for FireRover platformen.

Utviklet som en bacheloroppgave hos [NTNU](https://www.ntnu.no/) i sammarbeid med [SINTEF](https://www.sintef.no/) og [TBRT](https://tbrt.no/)

Plattformen skal være en fjernstyrt bil, styrt over mobilnett og utstyrt med kameraer og sensorer. Denne skal kunne brukes av brannvesenet på oppdrag for å sende inn for å skaffe seg oversikt i situasjoner hvor det ikke er trygt å sende inn mennesker, som ved brann i et annlegsområde med gassflasker. 

Plattformen er konstruert rundt en Raspberry pi med tilleggsmoduler for mobilnettilkobling, PWM-styring og mer.

Koden til plattformen er laget for WebRTC-tilkobling mellom enhetene, og baserer seg på [aiortc biblioteket](https://github.com/aiortc/aiortc).

For detaljert infromasjon om systemet, se bacheloroppgaven *Utvikling og realisering av
5G-basert, fjernstyrt kjøretøy for
brann- og redningstjenesten* på ntnu open. 

## Setup
### Raspberry
Enable legacy kamera og I2C på Raspberry pien med sudo raspi-config

Last ned github repoet til Raspberry pien og gå inn i mappen.
```
cd FireRover
```
Installer nødvendige python-biblioteker med 
```
pip install -r Code/rover_requirements.txt
```

kopier `FireRover.service` og `PowerButtons.service` til `/lib/systemd/system/` og enable servicene med `sudo systemctl enable FireRover.service` og tilsvarende for PowerButtons

For å sette opp pien til å prioritere nettverk fra 5G HATen:
```
sudo nano /etc/dhcpcd.conf
```
her må det legges til instillinger for wlan0 og usb0
```
interface wlan0
metric 300

interface usb0
metric 200
```

Aiortc biblioteket bennytter seg av en utdatert h264 encoder på Raspberry pi. Derfor må det gjøres forandringer til biblioteket. Dette gjøres enklest ved å kjøre kommandoen:
```
sudo cp Code/h264.py /home/pi/.local/lib/python3.9/site-packages/aiortc/codecs/h264.py
```
Denne erstatter filen for h264-encoding med en oppdatert fil.

Restart raspberry pien med `sudo reboot`. Om alt fungerte vil bilen komme med tre raske pip ved oppstart.

### PC
Last ned github repoet

Installer Python3 på PCen om den ikke har det

Kjør `download_packages.bat` for å installere nødvendige python-biblioteker

Kjør `main.bat` for å starte programmet
