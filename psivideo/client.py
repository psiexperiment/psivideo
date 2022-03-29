import asyncio
import json
import subprocess
import time

import websockets


class VideoClient:

    def __init__(self, uri='ws://localhost:33331', launch=True):
        self.launch = launch
        self.uri = uri
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()

    async def connect(self):
        if self.launch:
            process = subprocess.Popen(['psivideo'], stdout=subprocess.PIPE)
        self.ws = await websockets.connect(self.uri, loop=self.loop)
        print(f'Connected to {self.uri}')

    async def disconnect(self):
        await self.ws.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    async def start(self, filename):
        await self.ws.send(json.dumps({'cmd': 'set_filename', 'filename': filename}))
        await self.ws.send(json.dumps({'cmd': 'start'}))
        result = json.loads(await self.ws.recv())
        if result is not None:
            raise ValueError(f'Error starting: {result}')
        result = json.loads(await self.ws.recv())
        if result is not None:
            raise ValueError(f'Error starting: {result}')

    async def get_frames_written(self):
        _, result = await asyncio.gather(
            self.ws.send(json.dumps({'cmd': 'get_frames_written'})),
            self.ws.recv()
        )
        try:
            return json.loads(result)
        except:
            raise ValueError('Error getting frames written: {result}')


class SyncVideoClient(VideoClient):

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.disconnect()

    def disconnect(self):
        self.loop.run_until_complete(super().disconnect())

    def connect(self):
        self.loop.run_until_complete(super().connect())

    def start(self, filename):
        return self.loop.run_until_complete(super().start(filename))

    def get_frames_written(self):
        return self.loop.run_until_complete(super().get_frames_written())
