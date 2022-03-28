import logging
log = logging.getLogger(__name__)

import asyncio
from functools import partial
import json

import websockets


async def handle_connection(video, websocket):
    async for mesg in websocket:
        try:
            result = video.dispatch(**json.loads(mesg))
            print(mesg, result)
            await websocket.send(json.dumps(result))
        except Exception as e:
            await websocket.send(json.dumps(str(e)))


def video_tcp(video):
    loop = asyncio.new_event_loop()
    cb = partial(handle_connection, video)
    server = websockets.serve(cb, video.hostname, video.port, loop=loop)
    loop.run_until_complete(server)
    print(f'Websocket server listening on ws://{video.hostname}:{video.port}')
    loop.run_forever()
