//it's noting here
COTURN = true;

// get DOM elements
var dataChannelLog = document.getElementById('data-channel'),
    iceConnectionLog = document.getElementById('ice-connection-state'),
    iceGatheringLog = document.getElementById('ice-gathering-state'),
    signalingLog = document.getElementById('signaling-state');

// Global variables
var old_controller_data = null;
var controller_connected = false;

var battery_low = false;

var steering_offset = 0;
var speed_multiplier = 50;

var video_array = [];
var video_array_index = 0;

var video1 = null;
var video2 = null;
var video_display = 1;
var cam_hidden = false;

var timestamp_sent = 0;
var timestamp_received = 0;

// update values from sliders
document.getElementById('steering-offset-slider').addEventListener('change', function() {
    ofset_value = document.getElementById('steering-offset-slider').value;
    value_element = document.getElementById('steering-offset-value');
    value_element.innerHTML = ofset_value;
});
document.getElementById('speed-factor-slider').addEventListener('input', function() {
    speed_multiplier = document.getElementById('speed-factor-slider').value;
    value_element = document.getElementById('speed-factor-value');
    value_element.innerHTML = speed_multiplier;
});

// update coturn value
document.getElementById('COTURN').addEventListener('change', function() {
    //console.log('coTURN is: ', this.checked);
    if(this.checked) {
        COTURN = true;
    }
    else {
        COTURN = false;
    }
});

// Gamepad controller
const gamepadInfo = document.getElementById("gamepad-info");

window.addEventListener("gamepadconnected", (e) => {
    const gp = navigator.getGamepads()[e.gamepad.index];
    console.log("Gamepad connected");
    //console.log(`It has ${gp.buttons.length} buttons and ${gp.axes.length} axes.`);
    console.log(gp);
    //gamepadInfo.textContent = "Gamepad connected";
    controller_connected = true;
    a = document.getElementById("ControllerConnection");
    a.style.color = "green";
  
    readController();
  });

window.addEventListener("gamepaddisconnected", (e) => {
    //gamepadInfo.textContent = "Waiting for gamepad";
    controller_connected = false;
    a = document.getElementById("ControllerConnection");
    a.style.color = "red";
  });

// Read controller data
async function readController() {
    //console.log("read controller");
    const gamepads = navigator.getGamepads();
    if (!gamepads) {
      return;
    }
    if(!controller_connected) {
        return;
    }
  
    const gp = gamepads[0];
    // JSON from controller data
    gamepad_data = {
        topic: "data",
        timestamp: getCurrentTimestamp(),
        values: {
        buttons: {
            A: gp.buttons[0].pressed,
            B: gp.buttons[1].pressed,
            X: gp.buttons[2].pressed,
            Y: gp.buttons[3].pressed,
            D_PAD_UP: gp.buttons[12].pressed,
            D_PAD_DOWN: gp.buttons[13].pressed,
            D_PAD_LEFT: gp.buttons[14].pressed,
            D_PAD_RIGHT: gp.buttons[15].pressed,
            LB: gp.buttons[4].pressed,
            RB: gp.buttons[5].pressed,
            left_stick_button: gp.buttons[10].pressed,
            right_stick_button: gp.buttons[11].pressed,},
        left_trigger: gp.buttons[6].value, 
        right_trigger: gp.buttons[7].value, 
        l_thumb_y: gp.axes[1], 
        l_thumb_x: gp.axes[0],
        r_thumb_y: gp.axes[3],
        r_thumb_x: gp.axes[2],
        speed_multiplier: speed_multiplier,
        steering_offset: steering_offset,}}
    //console.log(gamepad_data.values.speed_multiplier);

    // Update steering offset and visualis when D-pad is used
    if(gamepad_data.values.buttons.D_PAD_RIGHT) {
        if(steering_offset < 15){
            steering_offset += 1;
            document.getElementById('steering-offset-slider').value = steering_offset;
            value_element = document.getElementById('steering-offset-value');
            value_element.innerHTML = steering_offset;

            //console.log("ofst is: ",steering_offset);
        }
    }
    if(gamepad_data.values.buttons.D_PAD_LEFT) {
        if(steering_offset > -15){
            steering_offset -= 1;
            document.getElementById('steering-offset-slider').value = steering_offset;
            value_element = document.getElementById('steering-offset-value');
            value_element.innerHTML = steering_offset;
            //console.log("ofst is: ",steering_offset);
        }
    }

    // Update speed multiplier and visualis when buttons are used
    if(gamepad_data.values.buttons.A) {
        speed_multiplier = 20;
        document.getElementById('speed-factor-slider').value = speed_multiplier;
        value_element = document.getElementById('speed-factor-value');
        value_element.innerHTML = speed_multiplier;
    }
    if(gamepad_data.values.buttons.X) {
        speed_multiplier = 60;
        document.getElementById('speed-factor-slider').value = speed_multiplier;
        value_element = document.getElementById('speed-factor-value');
        value_element.innerHTML = speed_multiplier;
    }
    if(gamepad_data.values.buttons.Y) {
        speed_multiplier = 100;
        document.getElementById('speed-factor-slider').value = speed_multiplier;
        value_element = document.getElementById('speed-factor-value');
        value_element.innerHTML = speed_multiplier;
    }

    return gamepad_data;
}

// Change camera position in UI
function changeCam(){
    if(video_display == 1){
        document.getElementById('video2').srcObject = video1
        document.getElementById('video1').srcObject = video2
        video_display = 2;
    }
    else{
        document.getElementById('video1').srcObject = video1
        document.getElementById('video2').srcObject = video2
        video_display = 1;
    }
}
// Show secondary camera
function showCam(){
    document.getElementById('video2').style.display = 'block';
    document.getElementById('show-cam').style.display = 'block';
    document.getElementById('hide-cam').style.display = 'none';
}
// Hide secondary camera
function hideCam(){
    document.getElementById('video2').style.display = 'none';
    document.getElementById('show-cam').style.display = 'none';
    document.getElementById('hide-cam').style.display = 'block';
}


// Update voltage indicator
function chargebattery(voltage) {
    var a;
    a = document.getElementById("charging");
    v = document.getElementById("voltage");
    v.innerHTML = voltage;
    if (voltage > 12) {
        a.innerHTML = "&#xf240;";
        a.style.color = "green";
    } else if (voltage > 10.3) {
        a.innerHTML = "&#xf242;";
        a.style.color = "yellow";
    } else {
        a.innerHTML = "&#xf243;";
        a.style.color = "red";
        if(!battery_low){
            alert("Battery is low, please charge the battery");
            battery_low = true;
        }
    }
  }

// Read local file and return JSON
function readTextFile(file)
{   var phrasedText;
    var rawFile = new XMLHttpRequest();
    rawFile.open("GET", file, false);
    rawFile.onreadystatechange = function ()
    {
        if(rawFile.readyState === 4)
        {
            if(rawFile.status === 200 || rawFile.status == 0)
            {
                var allText = rawFile.responseText;
                phrasedText = JSON.parse(allText);
                
            }
        }
    }
    rawFile.send(null);
    return phrasedText;
}

function getCurrentTimestamp () {
    return Date.now()
}


// peer connection
var pc = null;

// data channel
var dc = null, dcInterval = null;

async function createPeerConnection() {
    console.log("createPeerConnection");
    var config = {
        //sdpSemantics: 'unified-plan',
        iceTransportPolicy: 'relay',
        iceCandidatePoolSize: 0,
        rtcpMuxPolicy: 'negotiate',
    };
    
    if(COTURN==true) {
        console.log("COTURN");
        config.iceServers = [
            {
                urls: 'stun:188.113.112.68:3478'
            },
            {
                username: 'turnuser',
                credential: 'turnTBRT',
                urls: 'turn:188.113.112.68:3478'
            }];
        console.log(config.iceServers);
    }
    else {
        config.iceServers = ice_options;
        var ice_options = readTextFile("./ice_servers.txt");
        console.log("ice_options", ice_options);
    }

    console.log("using ICE", config.iceServers);

    pc = new RTCPeerConnection(config);

    // register some listeners to help debugging
    pc.addEventListener('icegatheringstatechange', function() {
        iceGatheringLog.textContent += ' -> ' + pc.iceGatheringState;
    }, false);
    iceGatheringLog.textContent = pc.iceGatheringState;

    pc.addEventListener('iceconnectionstatechange', function() {
        iceConnectionLog.textContent += ' -> ' + pc.iceConnectionState;
    }, false);
    iceConnectionLog.textContent = pc.iceConnectionState;

    pc.addEventListener('signalingstatechange', function() {
        signalingLog.textContent += ' -> ' + pc.signalingState;
    }, false);
    signalingLog.textContent = pc.signalingState;

    // connect audio / video 
    console.log("listening for tracks");
    pc.addEventListener('track', function(evt) {
        console.log(evt);
        if (evt.track.kind == 'video'){
            if(video_array_index == 0){
                console.log("got video track1");
                console.log(evt.streams[0]);
                video1 = new MediaStream([event.track]);
                document.getElementById('video1').srcObject = video1;
                video_array_index++;
            }
            else if ( video_array_index == 1){
                console.log("got video track2");
                console.log(evt.streams[0]);
                video2 = new MediaStream([event.track]);
                document.getElementById('video2').srcObject = video2;
                video_array_index++;
            }
            else{
                console.log("no more video tracks");
            }
            console.log("started video");
        }
        else
            document.getElementById('audio').srcObject = evt.streams[0];
    });

    return pc;
}

function negotiate() {
    console.log("negotiate");
    // add media tracks transcivers
    pc.addTransceiver('video', {direction: 'recvonly'});
    pc.addTransceiver('video', {direction: 'recvonly'});
    pc.addTransceiver('audio', {direction: 'recvonly'});
    return pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(offer);
    }).then(function() {
        // wait for ICE gathering to complete
        console.log("Waiting for ICE gathering to complete");
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } 
            else {
                function checkState() {
                    console.log("checkState");
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function() {
        console.log("creatng offer");
        console.log( pc.localDescription);
        var offer = pc.localDescription;
        // Force H264 codec to be used
        var codec = "H264/90000";
        offer.sdp = sdpFilterCodec('video', codec, offer.sdp);
        
        /* 
        * Send offer to the server to be forwarded to the callee
        *
        * This uses pagekite for forwarding to the callee 
        * The pagekite acount used is private and neads to be changed for future use.
        * When changing the pagekite account, pagekite.py neads to be run manually on the pi 
        * to log in to the new account.
        */
        console.log("Sending offer");
        return fetch('https://firerover.pagekite.me/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
                video_fps: document.getElementById('video-fps').value,
                video_source: document.getElementById('video-source').value,
                video_resolution: document.getElementById('video-resolution').value
            }),
            headers: {
                'Content-Type': 'application/json',
                //'Authorization': 'Basic ' + encode(username + ":" + password)
            },
            method: 'POST',
            //mode: "no-cors",
            cache: "no-cache",
            redirect: "follow",
            credentials: "omit"
        });
    }).then(function(response) {
        console.log("response");
        console.log(response);
        if (!response.ok) {
            console.log("Network response was not OK");
          }
        try {
            return response.json();
          } catch (error) {
            console.log("error parsing input");
          }
        //return response.json();
        console.log("response.json");
    }).then(function(answer) {
        console.log("answer");
        console.log("answer-sdp");
        return pc.setRemoteDescription(answer);
    }).catch(function(e) {
        alert(e);
    });
}

// Send a command to the rover to restart the pi, used to reboot if ICE fails 
async function restart_rover() {
    const url = 'https://firerover.pagekite.me/CMD';
    const response = await fetch(url, {
        body: JSON.stringify({
            CMD:"REBOOT"
        }),
        headers: {
            'Content-Type': 'application/json',
        },
        method: 'POST',
        mode: "no-cors",
        cache: "no-cache",
        redirect: "follow",
        credentials: "omit"
    });
    const text = await response.text();
    console.log('Restart FireRover');
    console.log(text);
}

// Start the connection to the rover
async function start() {
    if(controller_connected == false){
        alert("Controller not connected");
        return;
    }
    console.log("start");
    console.log("Creating peer connection");
    pc = await createPeerConnection();

    var time_start = null;

    function current_stamp() {
        if (time_start === null) {
            time_start = new Date().getTime();
            return 0;
        } else {
            return new Date().getTime() - time_start;
        }
    }

    // Setup data channel
    var parameters = JSON.parse('{"ordered": false}');
    console.log("Creating data channel");
    console.log("parameters", parameters);
    dc = pc.createDataChannel('chat', parameters);
    console.log("data channel", dc);
    dc.onclose = function() {
        clearInterval(dcInterval);
        clearInterval(get_data);
        //dataChannelLog.textContent += '- close\n';
    };
    dc.onopen = function() {
        //dataChannelLog.textContent += '- open\n';
        dcInterval = setInterval(function() {
            try
            {   
                // Send controller data to rover
                readController()
                .then(res => {
                    //console.log(res.data);
                    if(res != old_controller_data){
                        //dataChannelLog.textContent += '> ' + JSON.stringify(res) + '\n';
                        dc.send(JSON.stringify(res));
                        //console.log("sent data");
                        old_controller_data = res;
                    }
                //console.log("sent data");
                })

                
            }
            catch (e)
            {
                console.log("Error", e);
            }
        }, 25);
        get_data = setInterval(function() {
            try
            {
                // Request data from rover this is used to get the ping and battery voltage
                data_request = {
                topic: "data_request",
                timestamp: getCurrentTimestamp(),
                values: {}
                }
                timestamp_sent = current_stamp();
                dc.send(JSON.stringify(data_request));
                //console.log("data_request");    
            }
            catch (e)
            {
                console.log("Error", e);
            }
        }, 1000);
    };
    dc.onmessage = function(evt) {

        // Retuned data from rover
        timestamp_received = current_stamp();
        var RTT = timestamp_received - timestamp_sent;
        var ping = Math.round(RTT/2);
        //console.log("RTT", RTT);
        r = document.getElementById("Ping");
        r.innerHTML = ping;

        JSON.parse(evt.data, (key, value) => {
            //console.log(key, value); 
            if(key == "battery_voltage"){
                chargebattery(value)
                //console.log("voltage received");  
            }
        });

        //firerover_data = JSON.parse(evt.data);
        //console.log(firerover_data.battery_gauge);

        if (evt.data.substring(0, 4) === 'pong') {
            var elapsed_ms = current_stamp() - parseInt(evt.data.substring(5), 10);
            dataChannelLog.textContent += ' RTT ' + elapsed_ms + ' ms\n';
        }
    };

    var constraints = {
        audio: false,
        video: false
    };

    var resolution = document.getElementById('video-resolution').value;
    if (resolution) {
        resolution = resolution.split('x');
        constraints.video = {
            width: parseInt(resolution[0], 0),
            height: parseInt(resolution[1], 0)
        };
    } else {
        constraints.video = true;
    }
    negotiate();
    document.getElementById('stop').style.display = 'inline-block';
}

// Stop the connection to the rover
function stop() {
    document.getElementById('stop').style.display = 'none';
    document.getElementById('start').style.display = 'inline-block';
    video_array_index = 0;

    // close data channel
    if (dc) {
        dc.close();
    }

    // close transceivers
    if (pc.getTransceivers) {
        pc.getTransceivers().forEach(function(transceiver) {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }
    // close peer connection
    setTimeout(function() {
        pc.close();
    }, 500);
}

// Filter out codecs that are not supported 
function sdpFilterCodec(kind, codec, realSdp) {
    console.log("sdpFilterCodec");
    var allowed = []
    var rtxRegex = new RegExp('a=fmtp:(\\d+) apt=(\\d+)\r$');
    var codecRegex = new RegExp('a=rtpmap:([0-9]+) ' + escapeRegExp(codec))
    var videoRegex = new RegExp('(m=' + kind + ' .*?)( ([0-9]+))*\\s*$')
    
    var lines = realSdp.split('\n');

    var isKind = false;
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].startsWith('m=' + kind + ' ')) {
            isKind = true;
        } else if (lines[i].startsWith('m=')) {
            isKind = false;
        }

        if (isKind) {
            var match = lines[i].match(codecRegex);
            if (match) {
                allowed.push(parseInt(match[1]));
            }

            match = lines[i].match(rtxRegex);
            if (match && allowed.includes(parseInt(match[2]))) {
                allowed.push(parseInt(match[1]));
            }
        }
    }

    var skipRegex = 'a=(fmtp|rtcp-fb|rtpmap):([0-9]+)';
    var sdp = '';

    isKind = false;
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].startsWith('m=' + kind + ' ')) {
            isKind = true;
        } else if (lines[i].startsWith('m=')) {
            isKind = false;
        }

        if (isKind) {
            var skipMatch = lines[i].match(skipRegex);
            if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
                continue;
            } else if (lines[i].match(videoRegex)) {
                sdp += lines[i].replace(videoRegex, '$1 ' + allowed.join(' ')) + '\n';
            } else {
                sdp += lines[i] + '\n';
            }
        } else {
            sdp += lines[i] + '\n';
        }
    }

    return sdp;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}