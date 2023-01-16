import weatherhat
import asyncio
import random
import json
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import socket
from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
import netifaces as ni

localIP = ni.ifaddresses('eth0')[AF_INET][0]['addr']

updateSpeed = 0.5

sensor = weatherhat.WeatherHAT()
sensor.temperature_offset = -10 # fix that this is the right amount



def getLocalIP():
    #hostname = socket.gethostname()
    local_ip = socket.gethostbyname('weatherstation.local')
    #print(local_ip)
    return(local_ip)

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # send the contents of index.html
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            with open('index.html', 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)

async def sensor_handler(websocket, path):
    while True:
        # get a random sensor reading
        #reading = random.random()
        sensor.update(interval=updateSpeed)
        readings = {'currentIP':localIP,
                    'temperature':sensor.temperature,
                    'lux':sensor.lux,
                    'pressure':sensor.pressure,
                    'humidity':sensor.humidity,
                    'relative_humidity':sensor.relative_humidity,
                    'dewpoint':sensor.dewpoint,
                    'rain':sensor.rain,
                    'rain_total':sensor.rain_total,
                    'updated_wind_rain':sensor.updated_wind_rain,
                    'wind_direction':sensor.wind_direction,
                    'wind_speed':sensor.wind_speed}

        #print(readings)
	# send the reading over the websocket
        await websocket.send(json.dumps(readings))

        # wait 1 second before getting the next reading
        await asyncio.sleep(updateSpeed)

        # also dump json to a file
        json_tosave = json.dumps(readings)
        with open("readings/readings.json", "w") as outfile:
            outfile.write(json_tosave)

async def handler(websocket, path):
    if path == '/sensor':
        await sensor_handler(websocket, path)

async def main():
    # start the HTTP server
    server = HTTPServer(('0.0.0.0', 8000), RequestHandler)
    print("Listening on http://weatherstation.local:8000/")
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # start the WebSocket server
    ws_server = await websockets.serve(handler, '0.0.0.0', 8001)
    print("Listening on ws://localhost:8001/sensor")

    # wait until the servers are closed
    await ws_server.wait_closed()
    server.shutdown()

asyncio.run(main())
