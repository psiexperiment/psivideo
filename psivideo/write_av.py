from fractions import Fraction
import queue

import av


def video_write(video, log_cb):
    log = log_cb()
    log.info('Setting up write')

    frames_written = 0
    total_frames_dropped = 0
    prior_pts = -1
    fps = video.ctx.fps

    # Ok, it's time to start writing video!
    try:
        log.info(f'Recording to {video.ctx.output_filename}')
        container = av.open(video.ctx.output_filename, mode='w')
        stream = container.add_stream('mpeg4', rate=fps)
        stream.width, stream.height = video.ctx.image_width, video.ctx.image_height

        # Ok, we're ready to start recording
        while True:
            try:
                ts, frame = video.write_queue.get(timeout=1)
                if video.ctx.write_t0 is None:
                    video.ctx.write_t0 = ts
                ts -= video.ctx.write_t0
                frame = av.VideoFrame.from_ndarray(frame[..., ::-1], format='rgb24')

                current_pts = int(round(ts * fps))
                if current_pts == prior_pts:
                    log.info('Skipping write')
                    continue
                elif (current_pts - prior_pts) > 1:
                    frames_dropped = current_pts - prior_pts - 1
                    log.warning(f'Dropped {frames_dropped} frames before frame {current_pts}.')
                    total_frames_dropped += frames_dropped
                for pts in range(prior_pts, current_pts):
                    frames_written += 1
                    frame.pts = pts + 1
                    container.mux(stream.encode(frame))
                prior_pts = current_pts

            except queue.Empty:
                log.error('Queue is empty!')
                if video.stop.is_set():
                    break
    except BrokenPipeError:
        pass
    except Exception as e:
        log.error(str(e))
        video.stop.set()
        raise
    finally:
        try:
            # If the error occured when creating the container, it won't exist!
            container.close()
        except:
            pass

    log.info(f'{total_frames_dropped} dropped frames.')
    log.info(f'Wrote {frames_written} frames.')
