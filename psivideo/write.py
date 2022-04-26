from fractions import Fraction
import queue

import av


def video_write(ctx, write_queue, recording, stop, time_base, log_cb):
    log = log_cb()
    log.info('Setting up write')

    while True:
        if recording.wait(0.1):
            break
        if stop.is_set():
            return

    prior_pts = 0
    # Ok, it's time to start writing video!
    try:
        log.info(f'Recording to {ctx.output_filename}')
        container = av.open(ctx.output_filename, mode='w')
        stream = container.add_stream('mpeg4', rate=24)
        stream.width, stream.height = 640, 480
        stream.codec_context.time_base = time_base
        log.info(f'Time base is {stream.codec_context.time_base}')

        while True:
            try:
                ts, frame = write_queue.get(timeout=1)
                if ctx.write_t0 is None:
                    ctx.write_t0 = ts
                ts -= ctx.write_t0
                ctx.frames_written += 1
                frame = av.VideoFrame.from_ndarray(frame[..., ::-1], format='rgb24')
                frame.pts = int(round(ts / stream.codec_context.time_base))
                #log.debug(f'PTS is {frame.pts} (ts={ts:.3f}), DELTA={frame.pts-prior_pts}')
                prior_pts = frame.pts
                for packet in stream.encode(frame):
                    container.mux(packet)
            except queue.Empty:
                log.error('Queue is empty!')
                if stop.is_set():
                    break
    except Exception as e:
        log.error(str(e))
        stop.set()
        raise
    finally:
        try:
            # If the error occured when creating the container, it won't exist!
            container.close()
        except:
            pass

    print(f'Wrote {ctx.frames_written} frames.')
