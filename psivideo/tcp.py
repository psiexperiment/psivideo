import logging
log = logging.getLogger(__name__)

import asyncio
from functools import partial
import json

from threading import Thread
import websockets


async def handle_connection(video, websocket):
    async for mesg in websocket:
        try:
            result = video.dispatch(**json.loads(mesg))
            await websocket.send(json.dumps(result))
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except Exception as e:
            await websocket.send(json.dumps(str(e)))


async def run_server(video, loop):
    cb = partial(handle_connection, video)
    async with websockets.serve(cb, video.hostname, video.port, loop=loop):
        while True:
            await asyncio.sleep(0.1)
            if video.stop.is_set():
                break


def start_server(video, loop):
    loop.run_until_complete(run_server(video, loop))


def video_tcp(video):
    loop = asyncio.new_event_loop()
    cb = partial(start_server, video, loop)
    thread = Thread(target=cb)
    thread.start()
    print(f'Websocket server listening on ws://{video.hostname}:{video.port}')
    thread.join()
    print('Websocket server shutting down')
