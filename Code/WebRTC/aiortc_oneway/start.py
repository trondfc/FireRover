from http.server import HTTPServer, SimpleHTTPRequestHandler, test
import sys
from twilio.rest import Client
import json

hostName = "localhost"
serverPort = 8000

class CORSRequestHandler (SimpleHTTPRequestHandler):
    def end_headers (self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

def start_client():
    f = open("ice_servers.txt", "w")
    f.write(str(get_ice()))
    f.close()
    print("server starting as http://localhost:8000/")
    test(CORSRequestHandler, HTTPServer, port=8000)

def get_ice():
    account_sid = "AC3f41fff3e0e8db7d9f5ff32494b3dd86"
    auth_token = "5255cc68862bf23bb36e3ae5a20d7495"
    client = Client(account_sid, auth_token)
    token = client.tokens.create()
    ice = token.ice_servers
    prased_ice = json.dumps(ice)
    return prased_ice

if __name__ == '__main__':


    f = open("ice_servers.txt", "w")
    f.write(str(get_ice()))
    f.close()
    print("server starting as http://localhost:8000/")
    test(CORSRequestHandler, HTTPServer, port=8000)
 