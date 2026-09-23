import logging
from logging.handlers import QueueHandler, QueueListener

log = logging.getLogger(__name__)

from datetime import datetime
from fractions import Fraction
from functools import partial
import importlib
import multiprocessing as mp
from pathlib import Path
from threading import Event, Lock, Thread
import time

import cv2

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
    frame_size : {None, string}
        If provided, size will be defined in the format WxH, e.g., "320x240".
        Otherwise, the default size of the camera will be used.
    timebase : fractions.Fraction
        Unit of the PTS. To get the time of the frame relative to video start,
        multiply PTS by timebase.
    '''

    def __init__(self, source=0, hostname='localhost', port=33331,
                 frame_size=None, writer='cv2'):
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

        if frame_size is None:
            self.ctx.requested_image_width = -1
            self.ctx.requested_image_height = -1
        else:
            width, height = frame_size.split('x')
            self.ctx.requested_image_width = int(width)
            self.ctx.requested_image_height = int(height)

        # Thread synchronization
        self.new_frame = mp.Event()

        self.overlay_text = ''
        self.bar_height = 50

        # Folder that snapshots are saved to. Set by the client (e.g.,
        # psiexperiment) once it knows where the experiment data are saved.
        self.data_folder = None
        self.last_snapshot_time = None

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
                # Once we have the image height, expand it by the bar height.
                self.ctx.image_height += self.bar_height

    def join(self):
        self._threads['capture'].join()

    def process_frame(self, ts, frame):
        frame = cv2.copyMakeBorder(frame, self.bar_height, 0, 0, 0,
                                   cv2.BORDER_CONSTANT, value=(0, 0, 0))
        if self.overlay_text:
            cv2.putText(frame, self.overlay_text, (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
                        cv2.LINE_AA)

        if self.recording.is_set() and self.ctx.write_t0 is not None:
            # Calculate elapsed time in seconds for this specific frame
            elapsed = ts - self.ctx.write_t0

            # Ensure we don't briefly display a negative number due to slight thread delays
            if elapsed >= 0:
                # Convert total seconds to Hours, Minutes, Seconds
                hours, remainder = divmod(elapsed, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                width = frame.shape[1]
                cv2.putText(frame, time_str, (width - 135, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return ts, frame

    def save_snapshot(self, prefix='snapshot'):
        if self.data_folder is None:
            log.warning('No data folder set. Snapshot not saved.')
            return None
        if self.current_frame is None:
            return None
        # Drop the overlay bar so the snapshot contains only the camera image.
        frame = self.current_frame[self.bar_height:]
        folder = Path(self.data_folder)
        folder.mkdir(parents=True, exist_ok=True)
        filename = folder / f'{prefix}_{datetime.now():%Y%m%d-%H%M%S-%f}.png'
        # cv2.imwrite silently fails on non-ASCII paths on Windows, so encode
        # in memory and write the bytes ourselves.
        ok, buffer = cv2.imencode('.png', frame)
        if not ok:
            raise IOError('Unable to encode snapshot')
        filename.write_bytes(buffer.tobytes())
        self.last_snapshot_time = time.monotonic()
        log.info(f'Saved snapshot to {filename}')
        return filename

    @property
    def ts(self):
        return self.ctx.capture_ts - self.ctx.write_t0

    @property
    def frames_written(self):
        return self.ts * self.ctx.fps

    def dispatch(self, cmd, **kwargs):
        return getattr(self, f'handle_{cmd}')(**kwargs)

    def handle_is_recording(self):
        return self.recording.is_set()

    def handle_start(self, filename, force=True):
        if self.recording.is_set():
            if force:
                log.info('Recording already running. Stopping current recording.')
                self.handle_stop()
            else:
                raise IOError('Recording already started.')
        self.ctx.output_filename = filename
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

    def handle_show_text(self, text):
        self.overlay_text = text

    def handle_clear_text(self):
        self.overlay_text = ''

    def handle_set_data_folder(self, path):
        self.data_folder = path

    def handle_snapshot(self, prefix='snapshot'):
        filename = self.save_snapshot(prefix)
        return None if filename is None else str(filename)
