  # aiortc_server 
  Kode for strømming av videofead fra RPI til PC.
  
  Inneholder både kode for RPI og PC

  ## RPI kode
  __CameraConfig.ini__\
  Konfigerasjonsfil for kameraene, Brukes til og sette navn og path for kameraene.\
  Er nudvendig ettersom kamera-pathen ikke er konstant fra enhet til enhet.\
  __server.py__\
  Hovedkoden til RPI, tar hånd om STUN, WebRTC og video streaming

  ## PC kode
  __index.html__\
  HTML delen av nettsiden, håndterer den visuelle delen.\
  __client.js__\
  JavaScript delen av nettsiden, håndterer all kode funsjonalitet på nettsiden\
  __start.py__\
  Python kode for og starte opp nettsiden.

  # Bruk
  Nåværende versjon av koden bruker _ngrok_ for forwarding av fetch request hvilket gjør oppstarten noe mer tungvinnt\
  (dettte skal byttes ut i til senere versjoner)

  ### Oppset

  For instalasjon av aiortc på pi må man kjøre 
  ```
  pip install aiohttp aiortc aiohttp_cors
  ```

  ngrok må også settes opp med: \
  (https://ngrok.com/docs/getting-started/)
  ```
  curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok
  ```
  Test at ngrok fungerer med 
  ```
  ngrok -h
  ```
  Legg til bruker credentials fra ngrok.com med 
  ```
  ngrok config add-authtoken <TOKEN>
  ```
 ### Oppstart
  ngrok kan nå startes med 
  ```
  ngrok http 5000
  ```
  Kopier forwarding linken fra terminalen og lim denne inn på linje 130 i client.js. Denne linjen skal da se slik ut:
  `return fetch('ngrokForwardingLink/offer', {`

  Koden på RPI-en kan nå startes ved og kjøre __server.py__ på RPI-en, og nettsiden ved og kjøre __start.py__ på PC-en