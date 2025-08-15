import logging
log = logging.getLogger(__name__)

import asyncio
import json
import subprocess
import time
import threading

from websockets.asyncio.client import connect


class VideoClient:

    def __init__(self, launch=False, logging=None, hostname='localhost',
                 port=33331):
        self.launch = launch
        self.logging = logging
        self.hostname = hostname
        self.port = port
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()

    async def connect(self):
        if self.launch:
            args = ['psivideo', '-p', self.port]
            if self.logging is not None:
                args.extend(['--logging', self.logging])
            process = subprocess.Popen(args)
        uri = f'ws://{self.hostname}:{self.port}'
        self.ws = await connect(uri, ping_timeout=None)
        log.info(f'Connected to {uri}')

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.disconnect()

    def disconnect(self):
        with self.lock:
            self.loop.run_until_complete(super().disconnect())

    def connect(self):
        with self.lock:
            self.loop.run_until_complete(super().connect())

    def start(self, filename):
        with self.lock:
            return self.loop.run_until_complete(super().start(filename))

    def stop(self):
        with self.lock:
            return self.loop.run_until_complete(super().stop())

    def get_frames_written(self):
        with self.lock:
            return self.loop.run_until_complete(super().get_frames_written())
    def get_timing(self):
        with self.lock:
            return self.loop.run_until_complete(super().get_timing())
