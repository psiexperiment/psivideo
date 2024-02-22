import cv2
import time


def video_capture_profile(*args):
    from line_profiler import LineProfiler
    lp = LineProfiler()
    lp_wrapper = lp(_video_capture)
    lp_wrapper(*args)
    lp.print_stats()


def _video_capture(video, log_cb):
    '''
    Function to execute in a process that captures video.
    '''
    log = log_cb()
    log.info('Setting up capture')

    stream = cv2.VideoCapture(video.ctx.source)
    stream.set(cv2.CAP_PROP_FPS, 30.0)
    stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M','J','P','G'))

    # Read in some attributes that will be needed later
    video.ctx.fps = stream.get(cv2.CAP_PROP_FPS)
    video.ctx.image_width = stream.get(cv2.CAP_PROP_FRAME_WIDTH)
    video.ctx.image_height = stream.get(cv2.CAP_PROP_FRAME_HEIGHT)

    log.info(f'Actual FPS {video.ctx.fps}')

    # For some reason, first capture is very slow. Let's just grab and discard
    # the frame to get it out of the way.
    stream.read()

    # We need to track the actual capture time since the rate is a bit
    # variable. The video muxer we use can handle variable framerates. t0 is
    # time since the beginning of the video.
    t0 = stream.get(cv2.CAP_PROP_POS_MSEC) * 1e-3
    n_frames = 0

    # Notify the parent thread/process that capture is ready to go. This
    # prevents any other operations from beginning until capture is up and
    # running.
    log.info('Starting capture loop')
    video.capture_started.set()

    while True:
        try:
            # CAP_PROP_POS_MSEC is more accurate than time.time()
            grabbed, frame = stream.read()
            capture_ts = stream.get(cv2.CAP_PROP_POS_MSEC) * 1e-3 - t0
            if not grabbed:
                # Something is wrong with the video camera interface
                break
            if video.stop.is_set():
                # Time to stop the video
                break

            n_frames += 1
            video.queue.put_nowait((capture_ts, frame))
            video.ctx.capture_ts = capture_ts
        except Exception as e:
            # Notify other threads that it's time to stop.
            log.error(str(e))
            video.stop.set()
            raise

    stream.release()
    fps = n_frames / capture_ts
    log.info(f'Captured {n_frames} frames. Estimated capture rate was {fps:.0f} FPS')


# This allows us to switch between the line_profiler and regular version of video_capture
video_capture = _video_capture
