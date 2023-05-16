
import configparser
import time
import serial

ser = serial.Serial("/dev/ttyUSB2", 115200)

config5G = configparser.ConfigParser() # Config til 5G

config5G.read("/Users/syver/Documents/NTNU/Skole/Config_Test.ini") # Her skrives path til config-filen

PIN = config5G["DEFAULT"]["SIM_PIN"] #Henter ut variablen SIM_PIN
PUK = config5G["DEFAULT"]["SIM_PUK"] #Henter ut variablen SIM_PUK

def ExecuteCommand(Command):
    ser.write((Command+'\r\n').encode())

def ReadResponse(PerferredResponse):
    RecievedString = ''
    while True:
        if ser.inWaiting() > 0:
            BitsWaiting = ser.inWaiting()
            time.sleep(0.1)
            NewBitsWaiting = ser.inWaiting - BitsWaiting
            if not NewBitsWaiting:
                RecievedString = ser.read(ser.inWaiting()).decode()
                if PerferredResponse == RecievedString:
                    return 1
                else:
                    return RecievedString

def UnlockSIM(PIN, PUK):
    ExecuteCommand('cpin?')
    UnlockStatus = ReadResponse("OK")
    if UnlockStatus == "+CPIN: PIN":
        ExecuteCommand("AT+CPIN="+PIN)
    if UnlockStatus == "+CPIN: PUK":
        ExecuteCommand("AT+CPIN="+PUK)


#Denne funksjonen er skrevet av WaveShare. 
""" 
def send_at(command, back, timeout):
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if back not in rec_buff.decode():
        print(command + ' ERROR')
        print(command + ' back:\t' + rec_buff.decode())
        return 0
    else:
        print(rec_buff.decode())
        return 1
"""



#Alt nedenfor er testing og skal ikke være med i fullført kode
"""
print(PIN)
print(PUK)

AT_Command_Pin = "AT+CPIN="+PIN                         #AT-Kommando lås opp PIN
AT_Command_PUK = "AT+CPIN="+PUK
AT_Command_Initialize = "AT+CUSBCFG=USBID,1E0E,9011"    #AT-kommando Initialiser mobilnett

print(AT_Command_Pin)
print(AT_Command_PUK)
print(AT_Command_Initialize)
"""

ExecuteCommand("AT+CUSBCFG=USBID,1E0E,9011")
time.sleep(30)
UnlockSIM(PIN, PUK)
time.sleep(5)
ser.close()