import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid
import configparser
from subprocess import call
import time

abs_path = os.path.dirname(__file__)

from aiohttp import web
#from av import VideoFrame

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender
import aiohttp_cors

import multiprocessing as mp

from subprocess import Popen, PIPE



if __name__ == "__main__":
    recv_data_queue = mp.Queue()

ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()
relay = MediaRelay()

# Use v4l2-ctl --list-devices to find the camera name and add a unique part of the name to the list below
IR_CAM = "USB_IR"
RGB_CAM = "VIS"
PI_CAM = "service"

# Find the camera device path based on the name
def find_cam(cam):
    cmd = ["/usr/bin/v4l2-ctl", "--list-devices"]
    out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    out, err = out.strip().decode("utf-8"), err.strip().decode("utf-8")
    for l in [i.split("\n\t") for i in out.split("\n\n")]:
        if cam in l[0]:
            return l[1]
    return False

# Reboot the system
async def cmd(request):
    body = await request.text()
    body_json = json.loads(body)
    if body_json["CMD"] == "REBOOT":
        reboot_cmd = ["sudo", "reboot"]
        #call(reboot_cmd, shell=False) # Initiate OS Reboot
        firerover_data["SYS_RESET"] = True



## Function to handle the offer resived from the client
async def offer(request):
    print("offer started")
    #print(request)
    print(type(request))
    body = await request.text()
    body_json = json.loads(body)
    print(body_json)
    
    params = await request.json()
    #print("resived request.json")

    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    options = {"framerate": str(params["video_fps"]), "video_size": str(params["video_resolution"])}
    video_source = str(params["video_source"])
    if video_source == "IR Camera":
        video_source = find_cam(IR_CAM)
    elif video_source == "RGB Camera":
        video_source = find_cam(RGB_CAM)
    elif video_source == "Pi Camera":
        video_source = find_cam(PI_CAM)

    player1 = MediaPlayer(find_cam(PI_CAM), format="v4l2", options=options)
    player2 = MediaPlayer(find_cam(video_source), format="v4l2", options=options)
    #if args.record_to:
        #recorder = MediaRecorder(args.record_to)
    #else:
    recorder = MediaBlackhole()


    ## Setup the data channel
    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            
            try:
                message_json = json.loads(message)
                if message_json["topic"] == "data_request":
                    logging.debug("Data Request Received...")
                    firerover_data_json_str = json.dumps(firerover_data.copy()).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
                    channel.send(f"{firerover_data_json_str}")
                    logging.debug(f"Sending Data: {firerover_data_json_str}")

                elif message_json["topic"] == "data":
                    recv_data_queue.put(message)
                    logging.debug(f"message: {message}")
            except:
                logging.error("Message Recv Error")

            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])
                


    ## Close the connection if ICE fails
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)
        elif pc.connectionState == "connected":
            log_info("connected")

    ## On reciveing media stream
    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)

        if track.kind == "audio":
            pc.addTrack(player1.audio)
            recorder.addTrack(track)
        elif track.kind == "video":
            if args.record_to:
                recorder.addTrack(relay.subscribe(track))

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await recorder.stop()
    @pc.on("ended")
    def on_end():
        print("ended")

    # add media to pc
    log_info("addTrack")
    pc.addTrack(player1.video)
    pc.addTrack(player2.video)
    print("video fps is:",str(params["video_fps"]))
    print("video sorce is:",str(params["video_source"]))
    print("video path is:",str(video_source))
    print("video-resolution is:",str(params["video_resolution"]))

    # handle offer
    log_info("handleOffer")
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    log_info("sendAnswer")
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    #print("\n\n Response \n"+json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})+"\n\n")
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

def start_queues(recv_queue, send_queue, data_manager):
    global recv_data_queue
    recv_data_queue = recv_queue

    global send_data_queue
    send_data_queue = send_queue

    global firerover_data
    firerover_data = data_manager


def start_server():
    parser = argparse.ArgumentParser(
        description="WebRTC audio / video / data-channels demo"
    )
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port for HTTP server (default: 5000)"
    )
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v", action="count")

    global args
    args = parser.parse_args()

    print(f"Args:  {args}")

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    #app.router.add_get("/", index)
    #app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    app.router.add_post("/CMD", cmd)
    cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
        )
    })
    for route in list(app.router.routes()):
        cors.add(route)
    web.run_app(
        app, access_log=None, host=args.host, port=args.port, ssl_context=ssl_context
    )

## For testing
if __name__ == "__main__":
    recv_data_queue = mp.Queue()
    send_data_queue = mp.Queue()
    
    firerover_data_template = {
    "battery_gauge":0,
    "battery_voltage":0,
    "SYS_RESET":False,
    "Server_RESET":False
    }
    firerover_data = mp.Manager().dict(firerover_data_template)
    start_server()
