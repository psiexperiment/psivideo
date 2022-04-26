import logging
log = logging.getLogger(__name__)

import asyncio
import json
import subprocess
import time

import websockets


class VideoClient:

    def __init__(self, uri='ws://localhost:33331', launch=True, logging=None):
        self.launch = launch
        self.uri = uri
        self.logging = logging
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()

    async def connect(self):
        if self.launch:
            args = ['psivideo']
            if self.logging is not None:
                args.extend(['--logging', self.logging])
            process = subprocess.Popen(args)
        self.ws = await websockets.connect(self.uri, loop=self.loop)
        log.info(f'Connected to {self.uri}')

    async def disconnect(self):
        log.info('Closing websocket')
        await self.ws.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    async def dispatch(self, cmd, **kwargs):
        log.info(f'Dispatching {cmd} with kwargs {kwargs}')
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

    async def get_timing(self):
        return await self.dispatch('get_timing')


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
        log.info('Starting')
        return self.loop.run_until_complete(super().start(filename))

    def stop(self):
        return self.loop.run_until_complete(super().stop())

    def get_frames_written(self):
        return self.loop.run_until_complete(super().get_frames_written())

    def get_timing(self):
        return self.loop.run_until_complete(super().get_timing())
