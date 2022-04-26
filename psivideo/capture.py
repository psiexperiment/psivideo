import cv2
import time


def video_capture_profile(*args):
    from line_profiler import LineProfiler
    lp = LineProfiler()
    lp_wrapper = lp(_video_capture)
    lp_wrapper(*args)
    lp.print_stats()


def _video_capture(source, queue, capture_started, stop, log_cb):
    '''
    Function to execute in a thread that captures video. Basic tests suggest
    threading is enough and we do not need to go to multiprocessing for speed.
    '''
    log = log_cb()
    log.info('Setting up capture')

    stream = cv2.VideoCapture(source)
    stream.set(cv2.CAP_PROP_BUFFERSIZE, 0)

    # For some reason, first capture is very slow. Let's just grab and discard
    # the frame to get it out of the way.
    stream.read()

    # We need to track the actual capture time since the rate is a bit
    # variable. The video muxer we use can handle variable framerates. t0 is
    # time since the beginning of the video. t1 is the time of the current
    # frame. t2 is used to track the approximate frame rate.
    t1 = t0 = time.time()
    n_frames = 0

    log.info('Starting capture loop')
    capture_started.set()

    prev_capture_ts = None
    while True:
        try:
            # We can use the stream.read method which combines grab and
            # retrieve, but this approach (splitting the two) should yield more
            # accurate acquisition timestamps.
            grabbed = stream.grab()
            t2 = time.time()
            if not grabbed:
                # Something is wrong with the video camera interface
                break

            _, frame = stream.retrieve()
            if stop.is_set():
                # Time to stop the video
                break

            n_frames += 1
            capture_ts = t2-t0
            queue.put_nowait((capture_ts, frame))

            if prev_capture_ts is not None:
                log.info(f'Capture delta {(capture_ts - prev_capture_ts) * 1e3:.0f} msec')
            prev_capture_ts = capture_ts

            #if (n_frames % 500) == 0:
            #    fps = 500 / (t2-t1)
            #    t1 = t2
            #    log.info(f'Estimated FPS: {fps:.0f}')

        except Exception as e:
            # Notify other threads that it's time to stop.
            log.error(str(e))
            stop.set()
            raise

    fps = n_frames / (t2-t0)
    log.info(f'Captured {n_frames} frames. Estimated capture rate was {fps:.0f} FPS')


video_capture = video_capture_profile
