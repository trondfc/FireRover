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

# Account SID and Auth Token from twilio.com neads to be added
# to get_ice() function. This will allow the server to generate
# a new set of ICE servers every time the server is started.
# Twilios security dont allow uploading of the SID and Auth Token
# to a public github repo, and will immediatly change the SID 
# and Auth Token if done so.
# The SID and Auth Token can be found on the twilio dashboard.
# https://www.twilio.com/console

def get_ice():
    account_sid = ""
    auth_token = ""
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
 