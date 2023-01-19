import cv2
import time


def video_capture_profile(*args):
    from line_profiler import LineProfiler
    lp = LineProfiler()
    lp_wrapper = lp(_video_capture)
    lp_wrapper(*args)
    lp.print_stats()


def _video_capture(ctx, queue, capture_started, stop, log_cb):
    '''
    Function to execute in a thread that captures video. Basic tests suggest
    threading is enough and we do not need to go to multiprocessing for speed.
    '''
    log = log_cb()
    log.info('Setting up capture')

    stream = cv2.VideoCapture(ctx.source)
    stream.set(cv2.CAP_PROP_FPS, 30.0)
    stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M','J','P','G'))
    stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    # Read in some attributes that will be needed later
    ctx.fps = stream.get(cv2.CAP_PROP_FPS)
    ctx.image_width = stream.get(cv2.CAP_PROP_FRAME_WIDTH)
    ctx.image_height = stream.get(cv2.CAP_PROP_FRAME_HEIGHT)

    log.info(f'Actual FPS {ctx.fps}')

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
    capture_started.set()

    while True:
        try:
            # CAP_PROP_POS_MSEC is more accurate than time.time()
            grabbed, frame = stream.read()
            capture_ts = stream.get(cv2.CAP_PROP_POS_MSEC) * 1e-3 - t0
            if not grabbed:
                # Something is wrong with the video camera interface
                break
            if stop.is_set():
                # Time to stop the video
                break

            n_frames += 1
            queue.put_nowait((capture_ts, frame))
            ctx.capture_ts = capture_ts
        except Exception as e:
            # Notify other threads that it's time to stop.
            log.error(str(e))
            stop.set()
            raise

    stream.release()
    fps = n_frames / capture_ts
    log.info(f'Captured {n_frames} frames. Estimated capture rate was {fps:.0f} FPS')


# This allows us to switch between the line_profiler and regula version of video_capture
video_capture = _video_capture
