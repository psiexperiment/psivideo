from threading import Event, Lock, Thread
import queue

from .capture import video_capture
from .display import video_display
from .tcp import video_tcp
from .write import video_write


class Video:

    def __init__(self, source=0, hostname='localhost', port=33331, filename=None):
        vars(self).update(locals())
        self.current_frame = None
        self.output_filename = 'test/test.avi'
        self.frames_captured = 0
        self.frames_written = 0
        self.frames_discarded = 0
        self.write_start = None

        # Thread synchronization
        self.write_queue = queue.Queue()
        self.stop = Event()
        self.new_frame = Event()
        self.recording = Event()

    def start(self):
        self._threads = {
            'capture': Thread(target=video_capture, args=(self,)),
            'display': Thread(target=video_display, args=(self,)),
            'write': Thread(target=video_write, args=(self,)),
            'tcp': Thread(target=video_tcp, args=(self,), daemon=True),
        }
        for thread in self._threads.values():
            thread.start()

    def join(self):
        self._threads['capture'].join()

    def dispatch(self, cmd, **kwargs):
        return getattr(self, f'handle_{cmd}')(**kwargs)

    def handle_set_filename(self, filename):
        if self.recording.is_set():
            raise IOError('Recording already started. Cannot set filename.')
        self.output_filename = filename

    def handle_start(self):
        if self.recording.is_set():
            raise IOError('Recording already started.')
        self.recording.set()
        self.write_start = self.frames_captured

    def handle_get_frames_written(self):
        if not self.recording.is_set():
            raise IOError('Recording has not started')
        return self.frames_captured - self.write_start
