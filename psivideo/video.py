import logging
from logging.handlers import QueueHandler, QueueListener

log = logging.getLogger(__name__)

from fractions import Fraction
from functools import partial
import importlib
import multiprocessing as mp
from threading import Event, Lock, Thread

from .capture import video_capture
from .display import video_display
from .tcp import video_tcp
from .process import video_process
from .write import video_write


def configure_worker_logging(queue):
    handler = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    return root


def logging_thread(queue):
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


class Video:
    '''
    Parameters
    ----------
    source : int
        Source index (as seen by opencv) of acquisition device
    hostname : string
        IP address or hostname for server to listen on
    port : number
        Port for server to listen on
    timebase : fractions.Fraction
        Unit of the PTS. To get the time of the frame relative to video start,
        multiply PTS by timebase.
    '''

    def __init__(self, source=0, hostname='localhost', port=33331, writer='cv2'):
        # TODO: Don't use indexing for source. Should always point to correct
        # camera even if inputs are swapped.
        vars(self).update(locals())
        self.current_frame = None
        self.frames_discarded = 0

        # Process synchronization
        self.process_queue = mp.Queue(-1)   # Capture function puts frames/timestamp here.
        self.capture_started = mp.Event()   # Set when capture begins
        self.stop = mp.Event()              # All processes/threads can request stop.
        self.recording = mp.Event()         # Indicates whether we are saving video.
        self.write_queue = mp.Queue(-1)     # Process function puts frames/timestamp here.

        # This manages a set of variables that are shared globally
        self.mgr = mp.Manager()
        self.ctx = self.mgr.Namespace()
        self.ctx.source = source
        self.ctx.output_filename = None
        self.ctx.write_t0 = None

        # Thread synchronization
        self.new_frame = mp.Event()

        module = importlib.import_module(f'psivideo.write_{writer}')
        self.write_cb = getattr(module, 'video_write')
        self.log_queue = mp.Queue(-1)

    def start(self):
        log_cb = partial(configure_worker_logging, self.log_queue)
        capture_args = (self.ctx, self.process_queue, self.capture_started, self.stop, log_cb)
        write_args = (self.ctx, self.write_queue, self.recording, self.stop, log_cb, self.write_cb)

        self._threads = {
            'capture': mp.Process(target=video_capture, name='capture', args=capture_args),
            'process': Thread(target=video_process, args=(self,)),
            'display': Thread(target=video_display, args=(self,)),
            'write': mp.Process(target=video_write, name='write', args=write_args),
            'tcp': Thread(target=video_tcp, args=(self,)),
            'log': Thread(target=logging_thread, args=(self.log_queue,), daemon=True),
        }
        for name, thread in self._threads.items():
            log.info(f'Starting {thread}')
            thread.start()
            if name == 'capture':
                self.capture_started.wait()

    def join(self):
        self._threads['capture'].join()

    def process_frame(self, ts, frame):
        # Passthrough, but this method makes it easy for users to subclass and
        # write their own custom processing functions. Deeplabcut anyone?
        return ts, frame

    @property
    def ts(self):
        return self.ctx.capture_ts - self.ctx.write_t0

    @property
    def frames_written(self):
        return self.ts * self.ctx.fps

    def dispatch(self, cmd, **kwargs):
        return getattr(self, f'handle_{cmd}')(**kwargs)

    def handle_set_filename(self, filename):
        if self.recording.is_set():
            raise IOError('Recording already started. Cannot set filename.')
        self.ctx.output_filename = filename

    def handle_start(self, force=True):
        if self.recording.is_set():
            if force:
                log.info('Recording already running. Stopping current recording.')
                self.handle_stop()
            else:
                raise IOError('Recording already started.')
        self.recording.set()

    def handle_get_frames_written(self):
        if not self.recording.is_set():
            raise IOError('Recording has not started')
        return self.frames_written

    def handle_get_timing(self):
        if not self.recording.is_set():
            raise IOError('Recording has not started')
        ts = self.ts
        return {
            'frame_number': ts * self.ctx.fps,
            'timestamp': ts
        }

    def handle_stop(self):
        self.recording.clear()

    def handle_shutdown(self):
        self.stop()
        self.join()
