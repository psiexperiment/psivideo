from fractions import Fraction
import queue

import cv2


def video_write(video, log_cb):
    log = log_cb()
    log.info('Setting up write')

    frames_written = 0
    total_frames_dropped = 0
    prior_pts = -1
    fps = int(video.ctx.fps)
    frame_size = int(video.ctx.image_width), int(video.ctx.image_height)
    # Ok, it's time to start writing video!
    try:
        log.info(f'Recording to {video.ctx.output_filename} with fps {fps} and frame size {frame_size}')

        out = cv2.VideoWriter(video.ctx.output_filename,
                              cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                              fps,
                              frame_size)

        while True:
            try:
                ts, frame = video.write_queue.get(timeout=1)
                if video.ctx.write_t0 is None:
                    video.ctx.write_t0 = ts
                ts -= video.ctx.write_t0

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
                    out.write(frame)
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
            out.release()
        except:
            pass

    log.info(f'{total_frames_dropped} dropped frames.')
    log.info(f'Wrote {frames_written} frames.')
