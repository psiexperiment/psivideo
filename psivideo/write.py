from fractions import Fraction
import queue

import av


def video_write(ctx, write_queue, recording, stop, log_cb):
    log = log_cb()
    log.info('Setting up write')

    while True:
        if recording.wait(0.1):
            break
        if stop.is_set():
            return

    frames_written = 0
    total_frames_dropped = 0
    prior_pts = -1
    fps = ctx.fps
    # Ok, it's time to start writing video!
    try:
        log.info(f'Recording to {ctx.output_filename}')
        container = av.open(ctx.output_filename, mode='w')
        stream = container.add_stream('mpeg4', rate=fps)
        stream.width, stream.height = ctx.image_width, ctx.image_height

        while True:
            try:
                ts, frame = write_queue.get(timeout=1)
                if ctx.write_t0 is None:
                    ctx.write_t0 = ts
                ts -= ctx.write_t0
                frame = av.VideoFrame.from_ndarray(frame[..., ::-1], format='rgb24')

                current_pts = int(round(ts * fps))
                if (current_pts - prior_pts) != 1:
                    frames_dropped = current_pts - prior_pts - 1
                    log.warning(f'Dropped {frames_dropped} frames before frame {current_pts}.')
                    total_frames_dropped += frames_dropped
                for pts in range(prior_pts, current_pts):
                    frames_written += 1
                    frame.pts = pts + 1
                    for packet in stream.encode(frame):
                        container.mux(packet)
                prior_pts = current_pts

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

    log.info(f'{total_frames_dropped} dropped frames.')
    log.info(f'Wrote {frames_written} frames.')
