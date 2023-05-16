# utdatert
se Code/WebRTC/aiortc_server/README.md for forenklet versjon av nåverende instalasjon
# Oppset av WebRTC
Instalasjonsveildning for oppset av WebRTC med uv4l på RPI

Fremgangsmåte hentet fra:\
* https://github.com/PietroAvolio/uv4l-webrtc-raspberry-pi#readme
* https://pramod-atre.medium.com/live-streaming-video-audio-on-raspberry-pi-using-usb-camera-and-microphone-d19ece13eff0
* https://raspberrypi.stackexchange.com/questions/63930/remove-uv4l-software-by-http-linux-project-org-watermark

## Oppset av RPI
Kjør :
```
sudo rpi-update
``` 
om det ikke er gjort tidligre for og forsikre at RPI OS er up to date

Enable legacy kamera ved å gå kjøre
 ```
 sudo raspi-config
 ```
  å gå til **Interface Options > Legacy Camera**. Enable kameraet og reboot for at endringene skal ta effekt

## installasjon 
Kjør kommandoene :
```
curl https://www.linux-projects.org/listing/uv4l_repo/lpkey.asc | sudo apt-key add -
```

og
```
sudo nano /etc/apt/sources.list
```
Legg til linjen
```
deb https://www.linux-projects.org/listing/uv4l_repo/raspbian/stretch stretch main
```

Videre må programmvaren oppdateres og instaleres
```
sudo apt-get update
```
```
sudo apt-get upgrade
```

```
sudo apt-get install uv4l uv4l-raspicam uv4l-server uv4l-webrtc uv4l-raspicam-extras
```
```
sudo apt-get install uv4l uv4l-server uv4l-uvc uv4l-server uv4l-webrtc uv4l-xmpp-bridge
```

reboot for at endringene skal ta effekt

## Config
Åpne filen 
```
/etc/uv4l/uv4l-raspicam.conf
```
 og endre disse linjene:\

`encoding = h264`
`server-option = --enable-webrtc-audio = no`
`server-option = --webrtc-receive-audio = no`
`server-option = --enable-webrtc-audio = no`
`server-option = --webrtc-receive-audio = no`
`server-option = --webrtc-enable-hw-codec=yes`


## wannmerke
For og fjerne vannmerket fra videostrømen må man endre på hvilken driver som brukes\
Gå til : 
``` 
sudo nano /etc/systemd/system/uv4l_raspicam.service
```
 Endre linjen med 
 `ExecStart=...` til\
`ExecStart=/usr/bin/uv4l -f -k --sched-fifo --mem-lock --config-file=/etc/uv4l/uv4l-raspicam.conf --external-driver --device-name=video0 --server-option=--editable-config-file=/etc/uv4l/uv4l-raspicam.conf
`

Systemet må deretter reloade
```
sudo systemctl daemon-reload
```
```
sudo service uv4l_raspicam restart
```
For og se status kan man kjøre: 
```
sudo service uv4l_raspicam status
```

Etter restart av servicefilen skal videostrømen være tilgjengelig.

## Bruk

Standar er videostrømmen tilgjengelig på `RPI_IP:8080` og kan opnes i nettleser på `http://firerover4:8080/stream/webrtc`

Om det er gjort forandringer i config filen kan porten som benyttes være anderledes. Den nye portadressen kan da finnes ved og se på den loggede dataen med 
```
sudo service uv4l_raspicam status
```

Om der er behov for og avslutte strømingen kan dette gjøres med `sudo service uv4l_raspicam stop` eller `sudo pkill uv4l`