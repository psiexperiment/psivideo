import queue


class Recording:
    '''
    Saves the frames for one recording, filling in dropped frames so that the
    frame number reflects the time since the recording started.
    '''

    def __init__(self, ctx, session, t0, writer_class, log):
        _, filename = session
        self.ctx = ctx
        self.session = session
        self.t0 = t0
        self.fps = int(ctx.fps)
        self.log = log
        self.frames_written = 0
        self.frames_dropped = 0
        self.prior_pts = -1
        self.writer = writer_class(filename, self.fps, ctx.image_width,
                                   ctx.image_height, log)
        ctx.write_t0 = t0

    def write(self, ts, frame):
        current_pts = int(round((ts - self.t0) * self.fps))
        if current_pts <= self.prior_pts:
            self.log.info('Skipping write')
            return
        elif (current_pts - self.prior_pts) > 1:
            frames_dropped = current_pts - self.prior_pts - 1
            self.log.warning(f'Dropped {frames_dropped} frames before frame {current_pts}.')
            self.frames_dropped += frames_dropped
        for pts in range(self.prior_pts + 1, current_pts + 1):
            self.writer.write(pts, frame)
            self.frames_written += 1
        self.prior_pts = current_pts

    def close(self):
        self.ctx.write_t0 = None
        self.writer.close()
        self.log.info(f'{self.frames_dropped} dropped frames.')
        self.log.info(f'Wrote {self.frames_written} frames.')


def video_write(ctx, write_queue, stop, log_cb, writer_class):
    '''
    Save frames from `write_queue` until `stop` is set.

    Each item in the queue is either `(session, ts, frame)`, where `session`
    identifies the recording the frame belongs to, or `None`, which marks the
    end of a recording. A new file is started whenever the session changes, so
    back-to-back recordings are split correctly even when frames never stop
    arriving.
    '''
    log = log_cb()
    recording = None
    try:
        while True:
            try:
                item = write_queue.get(timeout=0.1)
            except queue.Empty:
                if stop.is_set():
                    break
                continue

            if item is None:
                if recording is not None:
                    recording.close()
                    recording = None
                continue

            session, ts, frame = item
            if recording is not None and recording.session != session:
                recording.close()
                recording = None
            if recording is None:
                recording = Recording(ctx, session, ts, writer_class, log)
            recording.write(ts, frame)
    except Exception as e:
        log.error(str(e))
        stop.set()
        raise
    finally:
        if recording is not None:
            recording.close()
