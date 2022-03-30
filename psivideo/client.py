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

    async def dispatch(self, cmd, **kwargs):
        await self.ws.send(json.dumps((cmd, kwargs)))
        error, result = json.loads(await self.ws.recv())
        if error is not None:
            raise ValueError(f'Error running {cmd}: {error}')
        return result

    async def start(self, filename):
        await self.dispatch('set_filename', filename=str(filename))
        await self.dispatch('start')

    async def stop(self):
        return await self.dispatch('stop')

    async def get_frames_written(self):
        return await self.dispatch('get_frames_written')


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

    def stop(self):
        return self.loop.run_until_complete(super().stop())

    def get_frames_written(self):
        return self.loop.run_until_complete(super().get_frames_written())
